"""
WhatsApp watcher for monitoring WhatsApp Web.

This module implements WhatsApp monitoring using Playwright browser automation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from .base_watcher import BaseWatcher
from ..utils import get_logger, serialize_frontmatter, write_file

# Playwright imports (will be installed via pip)
try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WhatsAppWatcher(BaseWatcher):
    """
    Watcher for WhatsApp Web using Playwright browser automation.

    Monitors WhatsApp Web for unread messages and creates action files.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file

        Raises:
            ImportError: If Playwright not installed
            ValueError: If WhatsApp session not configured
        """
        super().__init__(vault_path, config_path, "whatsapp")

        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        # Load environment variables
        env_path = self.vault_path / "silver" / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Get WhatsApp session path
        self.session_path = Path(os.getenv(
            "WHATSAPP_SESSION_PATH",
            str(self.vault_path / "silver" / "config" / "whatsapp_session")
        ))

        # Browser settings
        self.headless = self.config["whatsapp"].get("headless", True)
        self.timeout = self.config["whatsapp"].get("timeout", 30) * 1000  # Convert to ms

        # Keyword filtering settings
        keyword_config = self.config["whatsapp"].get("keyword_filter", {})
        self.keyword_filter_enabled = keyword_config.get("enabled", False)
        self.keywords = keyword_config.get("keywords", [])
        self.case_sensitive = keyword_config.get("case_sensitive", False)

        if self.keyword_filter_enabled:
            self.logger.info(f"Keyword filtering enabled with {len(self.keywords)} keywords")
        else:
            self.logger.info("Keyword filtering disabled - processing all messages")

        # Selectors (from Agent Skill reference)
        self.SELECTORS = {
            "chat_list": 'div[aria-label="Chat list"]',
            "chat_item": 'div[role="listitem"]',
            "unread_indicator": '[aria-label*="unread"]',  # Lowercase! Matches "unread messages", "1 unread message", etc.
            "chat_name": 'span[title]',
            "message_container": 'div[data-testid="conversation-panel-messages"]',
            "message": 'div[data-testid="msg-container"]',
            "message_text": 'span.selectable-text.copyable-text',
            "message_time": 'span[data-testid="msg-time"]',
            "qr_code": 'canvas[aria-label="Scan this QR code to link a device!"]',
            "login_success": 'div[data-testid="default-user"]',
        }

        # Track processed messages to avoid re-processing
        # Store as set of (chat_name, message_text, timestamp) tuples
        self.processed_messages = set()

        self.logger.info("WhatsApp watcher initialized successfully")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check WhatsApp Web for unread messages.

        Returns:
            List of message dictionaries

        Raises:
            Exception: If browser automation fails
        """
        messages = []

        with sync_playwright() as p:
            try:
                # Launch browser with persistent context (session)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Increased timeout for slow connections
                page.goto('https://web.whatsapp.com', wait_until='load', timeout=90000)

                # Wait a moment for page to stabilize
                page.wait_for_timeout(2000)

                # Check if logged in
                if not self._is_logged_in(page):
                    self.logger.warning("⚠️  WhatsApp session expired")
                    self.logger.warning("   To fix: python3 silver/scripts/setup_whatsapp.py")
                    browser.close()
                    return []

                # Wait for chat list to load with extended timeout (5 minutes for large chat histories)
                page.wait_for_selector(self.SELECTORS["chat_list"], timeout=300000)
                self.logger.debug("Chat list loaded")

                # CRITICAL: Wait for chats to sync from server (especially with 133+ messages)
                # WhatsApp Web loads UI fast but chat data syncs slowly
                sync_wait = 30  # 30 seconds for large message histories
                self.logger.info(f"⏳ Waiting {sync_wait}s for chats to sync from server...")
                page.wait_for_timeout(sync_wait * 1000)
                self.logger.info("✅ Chat sync complete")

                # Get unread chats
                unread_chats = self._get_unread_chats(page)
                self.logger.info(f"Found {len(unread_chats)} unread chats")

                # Filter chats by keywords BEFORE opening them (efficiency!)
                chats_to_process = []
                for chat_info in unread_chats:
                    chat_name = chat_info['name']
                    preview_text = chat_info['preview']

                    # Check if preview contains keywords
                    if self._contains_keywords(preview_text):
                        self.logger.info(f"✅ Chat '{chat_name}' contains keywords - will process")
                        chats_to_process.append(chat_info)
                    else:
                        self.logger.info(f"⏭️  Chat '{chat_name}' has no keywords - skipping")

                self.logger.info(f"Filtered to {len(chats_to_process)} chats with keywords (from {len(unread_chats)} total)")

                # Process each filtered chat
                max_results = self.config["whatsapp"]["max_results"]
                for i, chat_info in enumerate(chats_to_process[:max_results]):
                    try:
                        chat_messages = self._process_chat_by_name(page, chat_info['name'])
                        messages.extend(chat_messages)
                    except Exception as e:
                        self.logger.error(f"Failed to process chat {i}: {e}")

                browser.close()
                return messages

            except PlaywrightTimeout as e:
                self.logger.error(f"WhatsApp Web timeout: {e}")
                return []
            except Exception as e:
                self.logger.error(f"WhatsApp automation error: {e}")
                raise

    def _is_logged_in(self, page: Page) -> bool:
        """
        Check if WhatsApp Web is logged in.

        Args:
            page: Playwright page object

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check for QR code (not logged in)
            # Use multiple possible QR code selectors
            qr_selectors = [
                'canvas[aria-label="Scan me!"]',
                'canvas[aria-label="Scan this QR code to link a device!"]',
                self.SELECTORS["qr_code"]
            ]

            for selector in qr_selectors:
                try:
                    qr_code = page.locator(selector)
                    if qr_code.is_visible(timeout=3000):
                        self.logger.warning("QR code detected - not logged in")
                        return False
                except PlaywrightTimeout:
                    # QR code not visible with this selector, try next
                    continue

            # If no QR code found, check for chat list (indicates logged in)
            # This is more reliable than checking for specific user elements
            try:
                page.wait_for_selector(self.SELECTORS["chat_list"], timeout=60000)
                self.logger.debug("Login verified - chat list loaded")
                return True
            except PlaywrightTimeout:
                self.logger.warning("Chat list not found - login status unclear")
                return False

        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False

    def _get_unread_chats(self, page: Page) -> List[Dict[str, str]]:
        """
        Get list of unread chats with their names and preview text.

        Args:
            page: Playwright page object

        Returns:
            List of dictionaries with 'name' and 'preview' keys
        """
        try:
            # Find unread indicators first
            unread_indicators = page.query_selector_all(self.SELECTORS["unread_indicator"])
            self.logger.info(f"Found {len(unread_indicators)} unread indicators")

            unread_chats = []
            seen_names = set()  # Avoid duplicates

            for indicator in unread_indicators:
                # Find the parent chat element to extract name and preview
                chat_element = None

                # Try to find the chat container
                try:
                    chat_element = indicator.evaluate_handle(
                        'element => element.closest(\'div[role="listitem"]\')'
                    ).as_element()
                except:
                    pass

                if not chat_element:
                    try:
                        chat_element = indicator.evaluate_handle(
                            'element => element.closest(\'div[tabindex="-1"]\')'
                        ).as_element()
                    except:
                        pass

                if chat_element:
                    # Get chat name
                    name_element = chat_element.query_selector(self.SELECTORS["chat_name"])
                    chat_name = name_element.get_attribute('title') if name_element else None

                    if chat_name and chat_name not in seen_names:
                        # Get message preview
                        preview_text = self._get_chat_preview(chat_element)

                        unread_chats.append({
                            'name': chat_name,
                            'preview': preview_text
                        })
                        seen_names.add(chat_name)

            self.logger.info(f"Found {len(unread_chats)} unique unread chats")
            return unread_chats

        except Exception as e:
            self.logger.error(f"Failed to get unread chats: {e}")
            return []

    def _get_chat_preview(self, chat_element: Any) -> str:
        """
        Get message preview text from chat list (without opening the chat).

        Args:
            chat_element: Chat element from the chat list

        Returns:
            Preview text from the chat list
        """
        try:
            # WhatsApp shows message preview in the chat list
            # Try multiple selectors to find the preview text
            preview_selectors = [
                'span.selectable-text',  # Common text selector
                'span[title]',           # Sometimes has full text in title
                'div[dir="ltr"] span',   # Text direction wrapper
                'span',                  # Fallback to any span
            ]

            preview_text = ""

            for selector in preview_selectors:
                elements = chat_element.query_selector_all(selector)
                for elem in elements:
                    text = elem.inner_text() if elem else ""
                    if text and len(text) > len(preview_text):
                        preview_text = text

            # Also check title attributes which might have full text
            title_elements = chat_element.query_selector_all('[title]')
            for elem in title_elements:
                title = elem.get_attribute('title') if elem else ""
                if title and len(title) > len(preview_text):
                    preview_text = title

            self.logger.debug(f"Chat preview: {preview_text[:50]}...")
            return preview_text

        except Exception as e:
            self.logger.error(f"Failed to get chat preview: {e}")
            return ""

    def _process_chat(self, page: Page, chat_element: Any) -> List[Dict[str, Any]]:
        """
        Process a single chat and extract messages.

        Args:
            page: Playwright page object
            chat_element: Chat element to process

        Returns:
            List of message dictionaries
        """
        messages = []

        try:
            # Get chat name
            name_element = chat_element.query_selector(self.SELECTORS["chat_name"])
            chat_name = name_element.get_attribute('title') if name_element else "Unknown"

            self.logger.info(f"Opening chat: {chat_name}")

            # Click to open chat
            chat_element.click()

            # Wait longer for chat to load (especially for large group chats)
            self.logger.debug(f"Waiting for chat to load...")
            page.wait_for_timeout(3000)  # Increased from 1s to 3s

            # Wait for message container with longer timeout
            self.logger.debug(f"Waiting for message container...")
            page.wait_for_selector(self.SELECTORS["message_container"], timeout=15000)  # Increased from 5s to 15s

            # Get all messages in chat
            message_elements = page.query_selector_all(self.SELECTORS["message"])
            self.logger.debug(f"Found {len(message_elements)} messages in chat")

            # Process recent messages (last 5)
            for msg_element in message_elements[-5:]:
                try:
                    message_data = self._extract_message_data(msg_element, chat_name)
                    if message_data:
                        messages.append(message_data)
                except Exception as e:
                    self.logger.error(f"Failed to extract message: {e}")

            self.logger.info(f"✅ Processed {len(messages)} message(s) from {chat_name}")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to process chat: {e}")
            return []

    def _process_chat_by_name(self, page: Page, chat_name: str) -> List[Dict[str, Any]]:
        """
        Process a chat by searching for it by name (more reliable than DOM elements).

        Args:
            page: Playwright page object
            chat_name: Name of the chat to open

        Returns:
            List of message dictionaries
        """
        messages = []

        try:
            self.logger.info(f"Opening chat: {chat_name}")

            # Try multiple approaches to find and click the chat
            chat_clicked = False

            # Approach 1: Find by title attribute
            chat_selector = f'span[title="{chat_name}"]'
            chat_title_element = page.query_selector(chat_selector)

            if chat_title_element:
                self.logger.info(f"Found chat by title selector")
                # Get the parent chat item (the clickable div)
                chat_item = chat_title_element.evaluate_handle(
                    'element => element.closest(\'div[role="listitem"]\')'
                ).as_element()

                if chat_item:
                    self.logger.info(f"Found parent chat item, clicking...")
                    chat_item.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    chat_item.click()
                    chat_clicked = True
                else:
                    # Fallback: click the title element directly
                    self.logger.info(f"Parent not found, clicking title directly...")
                    chat_title_element.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    chat_title_element.click()
                    chat_clicked = True

            # Approach 2: Search by text content if title approach failed
            if not chat_clicked:
                self.logger.warning(f"Title selector failed, trying text search...")
                # Use XPath to find by text content
                xpath_selector = f'//span[@title="{chat_name}"]'
                chat_element = page.query_selector(f'xpath={xpath_selector}')

                if chat_element:
                    self.logger.info(f"Found chat by XPath, clicking...")
                    chat_element.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)
                    chat_element.click()
                    chat_clicked = True

            if not chat_clicked:
                self.logger.error(f"Could not find or click chat: {chat_name}")
                return []

            # Wait for chat to load (increased from 3s to 5s)
            self.logger.info(f"Waiting for chat to load...")
            page.wait_for_timeout(5000)

            # Check if we're actually in a chat by looking for the message input
            message_input = page.query_selector('div[contenteditable="true"][data-tab="10"]')
            if not message_input:
                self.logger.error(f"Chat didn't open - message input not found")
                return []

            self.logger.info(f"Chat opened successfully!")

            # Wait for message container with multiple fallback selectors
            self.logger.info(f"Waiting for message container...")
            try:
                page.wait_for_selector(self.SELECTORS["message_container"], timeout=15000)
            except Exception as e:
                # Try alternative selector
                self.logger.warning(f"Primary selector failed, trying alternative...")
                try:
                    page.wait_for_selector('div[role="application"]', timeout=10000)
                except Exception as e2:
                    # Last resort: just proceed if we have the message input
                    self.logger.warning(f"Both selectors failed, but chat is open - proceeding...")
                    pass

            # Get all messages in chat - try multiple selectors
            self.logger.info(f"Searching for messages...")

            # Try primary selector
            message_elements = page.query_selector_all(self.SELECTORS["message"])
            self.logger.info(f"Primary selector found {len(message_elements)} messages")

            # If no messages found, try alternative selectors
            if len(message_elements) == 0:
                self.logger.warning(f"No messages with primary selector, trying alternatives...")

                # Alternative 1: Any div with message-in or message-out class
                message_elements = page.query_selector_all('div.message-in, div.message-out')
                self.logger.info(f"Alternative 1 (message-in/out) found {len(message_elements)} messages")

                # Alternative 2: Look for copyable text spans (actual message content)
                if len(message_elements) == 0:
                    message_elements = page.query_selector_all('span.selectable-text.copyable-text')
                    self.logger.info(f"Alternative 2 (copyable-text) found {len(message_elements)} messages")

                # Alternative 3: Look for any div in the conversation panel
                if len(message_elements) == 0:
                    # Get the conversation panel first
                    conv_panel = page.query_selector('div[data-testid="conversation-panel-body"]')
                    if conv_panel:
                        message_elements = conv_panel.query_selector_all('div[class*="message"]')
                        self.logger.info(f"Alternative 3 (conversation panel) found {len(message_elements)} messages")

            if len(message_elements) == 0:
                self.logger.error(f"Could not find any messages in chat with any selector")
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"/tmp/whatsapp_debug_{chat_name.replace(' ', '_')}.png"
                    page.screenshot(path=screenshot_path)
                    self.logger.info(f"Debug screenshot saved to: {screenshot_path}")
                except:
                    pass
                return []

            # Process recent messages (last 10 instead of 5 to catch older messages)
            num_to_process = min(10, len(message_elements))
            self.logger.info(f"Processing last {num_to_process} messages out of {len(message_elements)} total...")
            for msg_element in message_elements[-num_to_process:]:
                try:
                    message_data = self._extract_message_data(msg_element, chat_name)
                    if message_data:
                        messages.append(message_data)
                except Exception as e:
                    self.logger.error(f"Failed to extract message: {e}")

            self.logger.info(f"✅ Processed {len(messages)} message(s) from {chat_name}")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to process chat '{chat_name}': {e}")
            return []

    def _contains_keywords(self, text: str) -> bool:
        """
        Check if message text contains any of the configured keywords.

        Args:
            text: Message text to check

        Returns:
            True if text contains any keyword, False otherwise
        """
        if not self.keyword_filter_enabled:
            return True  # No filtering, process all messages

        if not text:
            return False

        # Prepare text for comparison
        search_text = text if self.case_sensitive else text.lower()

        # Check each keyword
        for keyword in self.keywords:
            search_keyword = keyword if self.case_sensitive else keyword.lower()
            if search_keyword in search_text:
                self.logger.debug(f"Message contains keyword: '{keyword}'")
                return True

        return False

    def _extract_message_data(self, message_element: Any, chat_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract message data from message element.

        Args:
            message_element: Message element
            chat_name: Name of the chat

        Returns:
            Message dictionary or None if already processed or filtered out
        """
        try:
            # Extract message text - try multiple selectors
            text_element = message_element.query_selector(self.SELECTORS["message_text"])
            if not text_element:
                # Try alternative: get all text from the message element
                message_text = message_element.inner_text()
            else:
                message_text = text_element.inner_text()

            # Log the extracted text for debugging
            self.logger.info(f"Extracted text: '{message_text[:100]}...' (length: {len(message_text)})")

            # Extract timestamp
            time_element = message_element.query_selector(self.SELECTORS["message_time"])
            time_str = time_element.inner_text() if time_element else ""

            # Create unique identifier for this message
            message_id = (chat_name, message_text, time_str)

            # Skip if already processed
            if message_id in self.processed_messages:
                self.logger.debug(f"Skipping already processed message from {chat_name}")
                return None

            # Check keyword filter
            if not self._contains_keywords(message_text):
                self.logger.info(f"Skipping message from {chat_name} - no priority keywords found")
                # Mark as processed so we don't check it again
                self.processed_messages.add(message_id)
                return None

            # Mark as processed
            self.processed_messages.add(message_id)

            # Parse timestamp (format: "10:30 AM")
            timestamp = self._parse_timestamp(time_str)

            return {
                "sender": chat_name,
                "subject": f"WhatsApp message from {chat_name}",
                "body": message_text,
                "timestamp": timestamp,
                "metadata": {
                    "chat_name": chat_name,
                    "time_display": time_str,
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to extract message data: {e}")
            return None

    def _parse_timestamp(self, time_str: str) -> str:
        """
        Parse WhatsApp timestamp to ISO format.

        Args:
            time_str: Time string (e.g., "10:30 AM")

        Returns:
            ISO format timestamp
        """
        try:
            # WhatsApp shows time in format "HH:MM AM/PM"
            # Assume today's date
            today = datetime.now().date()
            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
            dt = datetime.combine(today, time_obj)
            return dt.isoformat()
        except Exception as e:
            self.logger.error(f"Failed to parse timestamp '{time_str}': {e}")
            return datetime.now().isoformat()

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create markdown action file for WhatsApp message.

        Args:
            item: Message data dictionary

        Returns:
            Path to created action file

        Raises:
            IOError: If file cannot be created
        """
        # Generate unique filename
        message_id = self._generate_message_id(item)
        filename = f"{message_id}.md"
        file_path = self.output_folder / filename

        # Create frontmatter
        frontmatter = {
            "id": message_id,
            "source": "whatsapp",
            "channel": "messaging",
            "sender": item["sender"],
            "subject": item["subject"],
            "timestamp": item["timestamp"],
            "status": "pending",
            "priority": "normal",
            "chat_name": item["metadata"]["chat_name"],
        }

        # Create body
        body = f"""# Message from {item['sender']}

**Chat**: {item['metadata']['chat_name']}

**Received**: {datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %I:%M %p')}

## Content

{item['body']}

## Suggested Actions

- [ ] Reply to sender
- [ ] Add to task list
- [ ] File in appropriate folder
- [ ] Mark as done

## Metadata

- **Source**: whatsapp
- **Channel**: messaging
- **Chat Name**: {item['metadata']['chat_name']}
- **Time Display**: {item['metadata']['time_display']}
"""

        # Serialize and write file
        content = serialize_frontmatter(frontmatter, body)
        write_file(file_path, content)

        self.logger.info(f"Created action file: {file_path}")
        return file_path


def main():
    """Main entry point for WhatsApp watcher."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path from environment or use default
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )
    config_path = f"{vault_path}/silver/config/watcher_config.yaml"

    try:
        # Initialize watcher
        watcher = WhatsAppWatcher(vault_path, config_path)

        # Run check
        watcher.run()

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

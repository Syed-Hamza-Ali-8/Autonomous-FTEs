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

        # Selectors (from Agent Skill reference)
        self.SELECTORS = {
            "chat_list": 'div[aria-label="Chat list"]',
            "chat_item": 'div[role="listitem"]',
            "unread_indicator": 'span[data-icon="unread-count"]',
            "chat_name": 'span[title]',
            "message_container": 'div[data-testid="conversation-panel-messages"]',
            "message": 'div[data-testid="msg-container"]',
            "message_text": 'span.selectable-text.copyable-text',
            "message_time": 'span[data-testid="msg-time"]',
            "qr_code": 'canvas[aria-label="Scan this QR code to link a device!"]',
            "login_success": 'div[data-testid="default-user"]',
        }

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
                page.goto('https://web.whatsapp.com', timeout=self.timeout)

                # Check if logged in
                if not self._is_logged_in(page):
                    self.logger.error("WhatsApp session expired. Please re-scan QR code.")
                    browser.close()
                    return []

                # Wait for chat list to load
                page.wait_for_selector(self.SELECTORS["chat_list"], timeout=self.timeout)
                self.logger.debug("Chat list loaded")

                # Get unread chats
                unread_chats = self._get_unread_chats(page)
                self.logger.info(f"Found {len(unread_chats)} unread chats")

                # Process each unread chat
                max_results = self.config["whatsapp"]["max_results"]
                for i, chat in enumerate(unread_chats[:max_results]):
                    try:
                        chat_messages = self._process_chat(page, chat)
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
            qr_code = page.query_selector(self.SELECTORS["qr_code"])
            if qr_code:
                self.logger.warning("QR code detected - not logged in")
                return False

            # Check for login success indicator
            page.wait_for_selector(self.SELECTORS["login_success"], timeout=10000)
            self.logger.debug("Login verified")
            return True

        except PlaywrightTimeout:
            self.logger.warning("Login verification timeout")
            return False

    def _get_unread_chats(self, page: Page) -> List[Any]:
        """
        Get list of unread chats.

        Args:
            page: Playwright page object

        Returns:
            List of unread chat elements
        """
        try:
            # Find all chat items with unread indicator
            chat_items = page.query_selector_all(self.SELECTORS["chat_item"])
            unread_chats = []

            for chat in chat_items:
                # Check if chat has unread indicator
                unread_indicator = chat.query_selector(self.SELECTORS["unread_indicator"])
                if unread_indicator:
                    unread_chats.append(chat)

            return unread_chats

        except Exception as e:
            self.logger.error(f"Failed to get unread chats: {e}")
            return []

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

            self.logger.debug(f"Processing chat: {chat_name}")

            # Click to open chat
            chat_element.click()
            page.wait_for_timeout(1000)  # Wait for chat to load

            # Wait for message container
            page.wait_for_selector(self.SELECTORS["message_container"], timeout=5000)

            # Get all messages in chat
            message_elements = page.query_selector_all(self.SELECTORS["message"])

            # Process recent messages (last 5)
            for msg_element in message_elements[-5:]:
                try:
                    message_data = self._extract_message_data(msg_element, chat_name)
                    if message_data:
                        messages.append(message_data)
                except Exception as e:
                    self.logger.error(f"Failed to extract message: {e}")

            return messages

        except Exception as e:
            self.logger.error(f"Failed to process chat: {e}")
            return []

    def _extract_message_data(self, message_element: Any, chat_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract message data from message element.

        Args:
            message_element: Message element
            chat_name: Name of the chat

        Returns:
            Message dictionary or None
        """
        try:
            # Extract message text
            text_element = message_element.query_selector(self.SELECTORS["message_text"])
            message_text = text_element.inner_text() if text_element else ""

            # Extract timestamp
            time_element = message_element.query_selector(self.SELECTORS["message_time"])
            time_str = time_element.inner_text() if time_element else ""

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

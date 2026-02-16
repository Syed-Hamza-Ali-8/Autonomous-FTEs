"""
WhatsApp Sender for sending messages via WhatsApp Web.

This module provides WhatsApp Web automation for sending messages
using Playwright browser automation.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import logging
import time

from ..utils import get_logger

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WhatsAppSender:
    """
    Sends WhatsApp messages via WhatsApp Web automation.

    Uses Playwright to automate WhatsApp Web for sending messages
    with session persistence and error handling.
    """

    def __init__(self, vault_path: str):
        """
        Initialize WhatsAppSender.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error(
                "Playwright not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )
            raise ImportError("Playwright not available")

        # Session path for persistent login
        self.session_path = self.vault_path / "silver" / "config" / "whatsapp_session"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.headless = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"
        self.timeout = int(os.getenv("WHATSAPP_TIMEOUT", "90000"))  # 90 seconds (increased from 30s)

        self.logger.info("WhatsAppSender initialized")

    def send_message(
        self,
        to: str,
        message: str,
        wait_for_delivery: bool = True
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via WhatsApp Web.

        Args:
            to: Recipient phone number or contact name
            message: Message text to send
            wait_for_delivery: Whether to wait for delivery confirmation

        Returns:
            Result dictionary with:
            - success: bool
            - message_id: str (if successful)
            - error: str (if failed)

        Raises:
            ValueError: If required fields are missing
        """
        try:
            # Validate required fields
            if not to:
                raise ValueError("Recipient is required")
            if not message:
                raise ValueError("Message text is required")

            self.logger.info(f"Sending WhatsApp message to: {to}")

            # Launch browser and send message
            with sync_playwright() as p:
                # Launch persistent context (maintains login session)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=self.headless,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                    ]
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to WhatsApp Web with increased timeout
                page.goto('https://web.whatsapp.com', wait_until='load', timeout=self.timeout)

                # Wait a moment for page to stabilize
                page.wait_for_timeout(2000)

                # Wait for WhatsApp to load
                self._wait_for_whatsapp_ready(page)

                # Search for contact
                self._search_contact(page, to)

                # Send message
                self._send_message_text(page, message)

                # Wait for delivery if requested
                if wait_for_delivery:
                    delivered = self._wait_for_delivery(page)
                    if not delivered:
                        self.logger.warning("Could not confirm message delivery")

                # Keep browser open for visual confirmation
                verification_wait = 20
                self.logger.info(f"✅ Message sent! Keeping browser open for {verification_wait}s so you can verify...")
                time.sleep(verification_wait)

                # Close browser
                browser.close()

                self.logger.info(f"WhatsApp message sent successfully to: {to}")

                return {
                    "success": True,
                    "message_id": f"whatsapp_{int(time.time())}",
                    "recipient": to,
                }

        except PlaywrightTimeout as e:
            error_msg = f"WhatsApp Web timeout: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

        except Exception as e:
            error_msg = f"Failed to send WhatsApp message: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    def _wait_for_whatsapp_ready(self, page) -> None:
        """
        Wait for WhatsApp Web to be ready.

        Args:
            page: Playwright page object

        Raises:
            TimeoutError: If WhatsApp doesn't load in time
        """
        try:
            # Check if QR code is present (not logged in)
            qr_code = page.locator('canvas[aria-label="Scan me!"]')

            # Wait a bit to see if QR code appears
            try:
                if qr_code.is_visible(timeout=5000):
                    self.logger.error("⚠️  WhatsApp Web session expired")
                    self.logger.error("   To fix: python3 silver/scripts/setup_whatsapp.py")
                    raise ValueError("WhatsApp Web not logged in - session expired")
            except PlaywrightTimeout:
                # QR code not visible - good, we're logged in
                pass

            # Wait for chat list to load (logged in) with extended timeout (5 minutes for large chat histories)
            self.logger.info("Waiting for WhatsApp Web to load...")
            page.wait_for_selector('div[aria-label="Chat list"]', timeout=300000)
            self.logger.info("✅ WhatsApp Web loaded successfully")

        except PlaywrightTimeout as e:
            self.logger.error(f"⏱️  Timeout waiting for WhatsApp Web: {e}")
            self.logger.error("   This usually means:")
            self.logger.error("   1. Session expired - run: python3 silver/scripts/setup_whatsapp.py")
            self.logger.error("   2. Slow internet connection")
            self.logger.error("   3. WhatsApp Web is down")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load WhatsApp Web: {e}")
            raise

    def _search_contact(self, page, contact: str) -> None:
        """
        Search for a contact in WhatsApp Web.

        Args:
            page: Playwright page object
            contact: Contact name or phone number

        Raises:
            ValueError: If contact not found
        """
        try:
            # Click search box
            search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
            search_box.click()
            time.sleep(1)  # Increased from 0.5s

            # Type contact name/number
            search_box.fill(contact)
            self.logger.info(f"Typed contact name: {contact}")

            # Wait longer for search results to appear (increased from 1s to 3s)
            time.sleep(3)

            # Try to find the contact in search results
            # Use a more flexible selector that waits for any search result
            self.logger.info(f"Waiting for search results...")

            # Wait for search results to appear
            page.wait_for_selector('div[aria-label="Search results."]', timeout=10000)
            self.logger.info(f"Search results appeared")

            # Click on first result with the contact name
            first_result = page.locator(f'span[title="{contact}"]').first

            # Wait for the result to be visible
            if not first_result.is_visible(timeout=10000):
                self.logger.error(f"Contact '{contact}' not found in search results")
                # Take a screenshot for debugging
                try:
                    screenshot_path = f"/tmp/whatsapp_search_failed_{contact.replace(' ', '_')}.png"
                    page.screenshot(path=screenshot_path)
                    self.logger.info(f"Debug screenshot saved: {screenshot_path}")
                except:
                    pass
                raise ValueError(f"Contact not found: {contact}")

            self.logger.info(f"Found contact in search results, clicking...")
            first_result.click()

            # CRITICAL: Wait for chat to fully load before sending
            self.logger.info(f"Contact selected: {contact}, waiting for chat to load...")
            self._wait_for_chat_ready(page)

            self.logger.info(f"Contact found and chat ready: {contact}")

        except Exception as e:
            self.logger.error(f"Failed to search contact: {e}")
            raise

    def _wait_for_chat_ready(self, page, timeout: int = 60) -> None:
        """
        Wait for chat to fully load before sending messages.

        This is CRITICAL to ensure messages are delivered immediately.
        WhatsApp Web syncs chat history when opening a chat, which can take
        10-60 seconds for large chats. If we send during sync, the message
        gets queued and won't be delivered until sync completes.

        Args:
            page: Playwright page object
            timeout: Maximum wait time in seconds

        Raises:
            TimeoutError: If chat doesn't load in time
        """
        try:
            self.logger.info("Waiting for chat to fully load (this may take 15-60 seconds)...")

            # Strategy 1: Wait for message input box to be ready
            # This indicates the chat UI is loaded
            message_box = page.locator('div[contenteditable="true"][data-tab="10"]')
            message_box.wait_for(state="visible", timeout=timeout * 1000)
            self.logger.info("✅ Message input box visible")

            # Strategy 2: MINIMUM WAIT TIME (15 seconds)
            # WhatsApp Web needs time to sync messages even if no loading indicators are visible
            # This is the most reliable approach for ensuring messages are delivered
            min_wait = 15
            self.logger.info(f"⏳ Waiting minimum {min_wait} seconds for chat sync...")
            time.sleep(min_wait)
            self.logger.info(f"✅ Minimum wait complete ({min_wait}s)")

            # Strategy 3: Check for loading indicators and wait if present
            # WhatsApp shows a progress bar or spinner while loading messages
            loading_selectors = [
                'div[role="progressbar"]',  # Progress bar
                'span[data-icon="status-time"]',  # Clock icon (loading)
                'div.progress-container',  # Progress container
                'span[data-icon="msg-time"]',  # Message time (appears when syncing)
            ]

            max_additional_wait = 45  # Maximum 45 additional seconds (total 60s with min_wait)
            start_time = time.time()

            while time.time() - start_time < max_additional_wait:
                # Check if any loading indicators are present
                loading = False
                for selector in loading_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            loading = True
                            self.logger.info(f"🔄 Loading indicator detected: {selector} (count: {count})")
                            break
                    except:
                        pass

                if not loading:
                    # No loading indicators - chat is ready
                    self.logger.info("✅ No loading indicators detected")
                    break

                # Still loading - wait and check again
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0 and elapsed > 0:  # Log every 10 seconds
                    self.logger.info(f"Chat still loading messages... ({elapsed}s elapsed)")
                time.sleep(1)

            # Strategy 4: Additional safety wait
            # Even after loading indicators disappear, give WhatsApp a moment to stabilize
            safety_wait = 5
            self.logger.info(f"⏳ Safety wait ({safety_wait}s) to ensure chat is stable...")
            time.sleep(safety_wait)

            # Verify message box is still ready
            if not message_box.is_visible():
                raise ValueError("Message input box disappeared after loading")

            total_elapsed = min_wait + int(time.time() - start_time) + safety_wait
            self.logger.info(f"✅ Chat fully loaded and ready to send (total wait: {total_elapsed}s)")

        except PlaywrightTimeout as e:
            self.logger.error(f"Timeout waiting for chat to load: {e}")
            self.logger.error("Chat may still be syncing messages. Message might be delayed.")
            raise
        except Exception as e:
            self.logger.error(f"Error waiting for chat: {e}")
            raise

    def _send_message_text(self, page, message: str) -> None:
        """
        Send message text in WhatsApp Web.

        Args:
            page: Playwright page object
            message: Message text to send

        Raises:
            ValueError: If message box not found
        """
        try:
            # Find message input box
            message_box = page.locator('div[contenteditable="true"][data-tab="10"]')
            if not message_box.is_visible(timeout=5000):
                raise ValueError("Message input box not found")

            # Type message
            message_box.fill(message)
            time.sleep(0.5)

            # Press Enter to send
            message_box.press('Enter')
            time.sleep(0.5)

            self.logger.info("Message sent")

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    def _wait_for_delivery(self, page, timeout: int = 10) -> bool:
        """
        Wait for message delivery confirmation.

        Args:
            page: Playwright page object
            timeout: Timeout in seconds

        Returns:
            True if delivery confirmed, False otherwise
        """
        try:
            # Wait for double checkmark (delivered)
            # WhatsApp uses different icons for sent/delivered/read
            # This is a simplified check
            time.sleep(2)  # Give time for delivery

            # Check for checkmarks in last message
            checkmarks = page.locator('span[data-icon="msg-dblcheck"]')
            if checkmarks.count() > 0:
                self.logger.info("Message delivery confirmed")
                return True

            self.logger.warning("Could not confirm delivery")
            return False

        except Exception as e:
            self.logger.warning(f"Failed to check delivery status: {e}")
            return False

    def verify_session(self) -> bool:
        """
        Verify that WhatsApp Web session is active.

        Returns:
            True if session is active, False otherwise
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=True,
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://web.whatsapp.com', timeout=self.timeout)

                # Check if logged in
                qr_code = page.locator('canvas[aria-label="Scan me!"]')
                is_logged_in = not qr_code.is_visible(timeout=5000)

                browser.close()

                return is_logged_in

        except Exception as e:
            self.logger.error(f"Failed to verify session: {e}")
            return False

    def get_recent_messages(self, contact: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages from a contact.

        Args:
            contact: Contact name or phone number
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """
        try:
            messages = []

            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=True,
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://web.whatsapp.com', timeout=self.timeout)

                # Wait for WhatsApp to load
                self._wait_for_whatsapp_ready(page)

                # Search for contact
                self._search_contact(page, contact)

                # Get messages
                message_elements = page.locator('div[class*="message"]').all()[:limit]

                for elem in message_elements:
                    try:
                        text = elem.inner_text()
                        messages.append({
                            'text': text,
                            'contact': contact,
                        })
                    except:
                        continue

                browser.close()

            return messages

        except Exception as e:
            self.logger.error(f"Failed to get recent messages: {e}")
            return []


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize sender
        sender = WhatsAppSender(vault_path)

        # Verify session
        print("Verifying WhatsApp Web session...")
        is_logged_in = sender.verify_session()

        if not is_logged_in:
            print("❌ WhatsApp Web not logged in")
            print("   Run: python silver/scripts/setup_whatsapp.py")
            sys.exit(1)

        print("✅ WhatsApp Web session active")

        # Test: Send test message
        print("\nSending test message...")
        print("Note: This will send a real WhatsApp message!")
        print()

        # Get recipient from user
        to = input("Enter recipient name or phone number: ").strip()
        if not to:
            print("❌ No recipient provided")
            sys.exit(1)

        # Send test message
        result = sender.send_message(
            to=to,
            message="Test message from AI Employee Vault Silver tier. "
                   "If you received this, WhatsApp sending is working correctly!",
            wait_for_delivery=True
        )

        if result['success']:
            print(f"\n✅ Message sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Recipient: {result['recipient']}")
        else:
            print(f"\n❌ Failed to send message: {result['error']}")

        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

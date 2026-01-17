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
        self.timeout = int(os.getenv("WHATSAPP_TIMEOUT", "30000"))  # 30 seconds

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

                # Navigate to WhatsApp Web
                page.goto('https://web.whatsapp.com', timeout=self.timeout)

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
            if qr_code.is_visible(timeout=5000):
                self.logger.error(
                    "WhatsApp Web not logged in. Please scan QR code. "
                    "Run: python silver/scripts/setup_whatsapp.py"
                )
                raise ValueError("WhatsApp Web not logged in")

            # Wait for chat list to load (logged in)
            page.wait_for_selector('div[aria-label="Chat list"]', timeout=self.timeout)
            self.logger.info("WhatsApp Web loaded successfully")

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
            time.sleep(0.5)

            # Type contact name/number
            search_box.fill(contact)
            time.sleep(1)

            # Click on first result
            first_result = page.locator(f'span[title="{contact}"]').first
            if not first_result.is_visible(timeout=5000):
                raise ValueError(f"Contact not found: {contact}")

            first_result.click()
            time.sleep(0.5)

            self.logger.info(f"Contact found and selected: {contact}")

        except Exception as e:
            self.logger.error(f"Failed to search contact: {e}")
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

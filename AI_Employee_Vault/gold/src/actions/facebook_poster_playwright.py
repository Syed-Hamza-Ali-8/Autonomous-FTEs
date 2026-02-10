"""
Facebook poster using Playwright browser automation.

This module implements Facebook posting using Playwright with visible browser
(headless=False) so you can watch the posting happen in real-time.

Similar to Silver Tier LinkedIn posting.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class FacebookPosterPlaywright:
    """
    Poster for Facebook using Playwright browser automation.

    Posts content to Facebook with visible browser window.
    """

    def __init__(self, vault_path: str):
        """
        Initialize Facebook poster.

        Args:
            vault_path: Path to the Obsidian vault root

        Raises:
            ImportError: If Playwright not installed
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        self.vault_path = Path(vault_path)

        # Load environment variables
        env_path = self.vault_path / "gold" / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Facebook session path
        self.session_path = os.getenv(
            "FACEBOOK_SESSION_PATH",
            str(self.vault_path / "gold" / "config" / "facebook_session")
        )

        print(f"✅ Facebook poster initialized (session: {self.session_path})")

    def post_update(self, content: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an update to Facebook.

        Args:
            content: Text content to post
            image_path: Optional path to image to attach

        Returns:
            Dict with success status and post details
        """
        print("🚀 Posting to Facebook...")

        try:
            with sync_playwright() as p:
                # Launch browser with persistent session (VISIBLE BROWSER)
                print("🌐 Opening browser...")
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=False,  # SHOW BROWSER - you can watch it post!
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.new_page()

                # Navigate to Facebook
                print("📱 Navigating to Facebook...")
                page.goto("https://www.facebook.com/", wait_until="load", timeout=90000)

                # Check if logged in
                if "login" in page.url.lower():
                    print("❌ Facebook session expired. Please re-login.")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Session expired",
                        "message": "Run: python gold/scripts/setup_facebook.py"
                    }

                # Wait for page to fully load
                page.wait_for_timeout(3000)

                # Close any promotional modals
                print("🧹 Closing promotional modals...")
                try:
                    for i in range(3):
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                except:
                    pass

                page.wait_for_timeout(2000)

                # Click "What's on your mind?" to open post composer
                print("🖱️  Looking for post composer...")

                composer_selectors = [
                    '[role="button"][aria-label*="Create a post"]',
                    '[role="button"]:has-text("What\'s on your mind")',
                    'div[role="button"]:has-text("What\'s on your mind")',
                    '[aria-label*="Create a post"]',
                    'span:has-text("What\'s on your mind")',
                ]

                composer_clicked = False
                for selector in composer_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first
                            if button.is_visible():
                                button.click(timeout=5000)
                                print(f"✅ Clicked composer using: {selector}")
                                composer_clicked = True
                                break
                    except Exception as e:
                        print(f"   Selector {selector} failed: {e}")
                        continue

                if not composer_clicked:
                    print("❌ Could not find post composer")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Composer not found",
                        "message": "Could not find Facebook post composer"
                    }

                # Wait for composer modal to open
                print("⏳ Waiting for composer modal...")
                page.wait_for_timeout(3000)

                # Find the text input area
                print("📝 Looking for text input...")

                textbox_selectors = [
                    '[role="textbox"][contenteditable="true"]',
                    'div[contenteditable="true"][role="textbox"]',
                    '[aria-label*="What\'s on your mind"]',
                    'div[contenteditable="true"]',
                ]

                textbox_found = False
                for selector in textbox_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000, state="visible")
                        print(f"✅ Found textbox using: {selector}")
                        textbox_found = True
                        break
                    except:
                        continue

                if not textbox_found:
                    print("❌ Could not find text input")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Textbox not found",
                        "message": "Could not find text input area"
                    }

                # Type content
                print("⌨️  Typing content...")
                editor = page.locator('[role="textbox"][contenteditable="true"]').first
                editor.click()
                page.wait_for_timeout(500)

                # Type the content
                editor.type(content, delay=50)

                print(f"✅ Typed {len(content)} characters")

                # Wait for content to be processed
                page.wait_for_timeout(2000)

                # Click "Post" button
                print("🔍 Looking for Post button...")

                post_button_selectors = [
                    '[role="button"][aria-label="Post"]:not([aria-disabled="true"])',
                    'div[role="button"]:has-text("Post"):not([aria-disabled="true"])',
                    '[aria-label="Post"]:not([aria-disabled="true"])',
                    'div[role="button"]:has-text("Post")',
                ]

                post_clicked = False
                for selector in post_button_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first
                            if button.is_visible():
                                button.wait_for(state="visible", timeout=5000)
                                button.click(timeout=5000)
                                print(f"✅ Clicked Post button using: {selector}")
                                post_clicked = True
                                break
                    except Exception as e:
                        print(f"   Selector {selector} failed: {e}")
                        continue

                if not post_clicked:
                    print("❌ Could not find or click Post button")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Post button not found",
                        "message": "Could not find or click the Post button"
                    }

                # Wait for post to be submitted
                print("⏳ Waiting for post to be submitted...")
                page.wait_for_timeout(5000)

                # Verify modal closed
                modal_count = page.locator('[role="dialog"]').count()
                print(f"📊 Modal count after posting: {modal_count}")

                if modal_count > 0:
                    # Close remaining modals
                    print("🧹 Closing remaining modals...")
                    for i in range(3):
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)

                browser.close()

                print("✅ Successfully posted to Facebook!")
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(content),
                    "platform": "facebook"
                }

        except PlaywrightTimeout as e:
            print(f"❌ Timeout while posting: {e}")
            return {
                "success": False,
                "error": "Timeout",
                "message": str(e)
            }
        except Exception as e:
            print(f"❌ Error posting to Facebook: {e}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }


def main():
    """Test Facebook poster."""
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    poster = FacebookPosterPlaywright(vault_path)

    # Test content
    content = """🚀 Testing Gold Tier Facebook posting!

This post was created by my AI Employee using Playwright browser automation.

You can watch the browser post in real-time! 🤖

#AI #Automation #GoldTier"""

    print("=" * 60)
    print("Facebook Poster Test")
    print("=" * 60)
    print()
    print("Content to post:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    print()

    response = input("Post this to Facebook? (yes/no): ")

    if response.lower() == "yes":
        result = poster.post_update(content)

        if result["success"]:
            print()
            print("=" * 60)
            print("✅ SUCCESS!")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print(f"❌ FAILED: {result.get('error')}")
            print(f"   {result.get('message')}")
            print("=" * 60)
    else:
        print("Post cancelled.")


if __name__ == "__main__":
    main()

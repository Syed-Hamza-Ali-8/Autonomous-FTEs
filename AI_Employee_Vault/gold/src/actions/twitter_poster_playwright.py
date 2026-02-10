"""
Twitter/X poster using Playwright browser automation.

This module implements Twitter posting using Playwright with visible browser
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


class TwitterPosterPlaywright:
    """
    Poster for Twitter/X using Playwright browser automation.

    Posts content to Twitter with visible browser window.
    """

    def __init__(self, vault_path: str):
        """
        Initialize Twitter poster.

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

        # Twitter session path
        self.session_path = os.getenv(
            "TWITTER_SESSION_PATH",
            str(self.vault_path / "gold" / "config" / "twitter_session")
        )

        print(f"✅ Twitter poster initialized (session: {self.session_path})")

    def post_update(self, content: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Post a tweet to Twitter/X.

        Args:
            content: Text content to post
            image_path: Optional path to image to attach

        Returns:
            Dict with success status and post details
        """
        print("🚀 Posting to Twitter/X...")

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

                # Navigate to Twitter
                print("🐦 Navigating to Twitter/X...")
                page.goto("https://twitter.com/home", wait_until="load", timeout=90000)

                # Check if logged in
                if "login" in page.url.lower() or page.url == "https://twitter.com/":
                    print("❌ Twitter session expired. Please re-login.")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Session expired",
                        "message": "Run: python gold/scripts/setup_twitter.py"
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

                # Find the tweet compose box
                print("🖱️  Looking for tweet compose box...")

                # Twitter has a prominent "What's happening?" textbox on the home page
                textbox_selectors = [
                    '[data-testid="tweetTextarea_0"]',
                    '[role="textbox"][aria-label*="Tweet"]',
                    '[role="textbox"][data-testid*="tweet"]',
                    'div[role="textbox"][contenteditable="true"]',
                    '[aria-label*="What is happening"]',
                ]

                textbox_found = False
                for selector in textbox_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            textbox = page.locator(selector).first
                            if textbox.is_visible():
                                print(f"✅ Found textbox using: {selector}")
                                textbox_found = True

                                # Click to focus
                                textbox.click()
                                page.wait_for_timeout(500)

                                # Type content
                                print("⌨️  Typing content...")
                                textbox.type(content, delay=50)
                                print(f"✅ Typed {len(content)} characters")
                                break
                    except Exception as e:
                        print(f"   Selector {selector} failed: {e}")
                        continue

                if not textbox_found:
                    print("❌ Could not find tweet compose box")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Textbox not found",
                        "message": "Could not find tweet compose box"
                    }

                # Wait for content to be processed
                page.wait_for_timeout(2000)

                # Click "Post" or "Tweet" button
                print("🔍 Looking for Post button...")

                post_button_selectors = [
                    '[data-testid="tweetButtonInline"]',
                    '[data-testid="tweetButton"]',
                    'div[role="button"][data-testid*="tweet"]',
                    '[role="button"]:has-text("Post")',
                    '[role="button"]:has-text("Tweet")',
                    'button:has-text("Post")',
                    'button:has-text("Tweet")',
                ]

                post_clicked = False
                for selector in post_button_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first
                            if button.is_visible() and not button.is_disabled():
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

                # Wait for tweet to be submitted
                print("⏳ Waiting for tweet to be submitted...")
                page.wait_for_timeout(5000)

                # Verify tweet was posted (textbox should be cleared)
                try:
                    textbox = page.locator('[data-testid="tweetTextarea_0"]').first
                    text_content = textbox.inner_text()
                    if not text_content or len(text_content.strip()) == 0:
                        print("✅ Textbox cleared - tweet posted successfully!")
                except:
                    pass

                browser.close()

                print("✅ Successfully posted to Twitter/X!")
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(content),
                    "platform": "twitter"
                }

        except PlaywrightTimeout as e:
            print(f"❌ Timeout while posting: {e}")
            return {
                "success": False,
                "error": "Timeout",
                "message": str(e)
            }
        except Exception as e:
            print(f"❌ Error posting to Twitter: {e}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }


def main():
    """Test Twitter poster."""
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    poster = TwitterPosterPlaywright(vault_path)

    # Test content
    content = """🚀 Testing Gold Tier Twitter posting!

This tweet was created by my AI Employee using Playwright browser automation.

You can watch the browser post in real-time! 🤖

#AI #Automation #GoldTier"""

    print("=" * 60)
    print("Twitter Poster Test")
    print("=" * 60)
    print()
    print("Content to post:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    print()

    response = input("Post this to Twitter? (yes/no): ")

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

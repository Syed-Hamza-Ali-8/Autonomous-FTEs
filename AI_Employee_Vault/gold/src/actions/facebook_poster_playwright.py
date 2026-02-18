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
import glob
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

    def _cleanup_stale_locks(self):
        """Clean up stale browser lock files to prevent session conflicts."""
        session_path = Path(self.session_path)
        if not session_path.exists():
            return

        print("   🧹 Cleaning up stale browser lock files...")

        # Remove Chromium lock files that can prevent browser from starting
        lock_patterns = [
            "SingletonLock",
            "SingletonSocket",
            "SingletonCookie"
        ]

        cleaned_count = 0
        for pattern in lock_patterns:
            # Check root directory
            lock_file = session_path / pattern
            if lock_file.exists():
                try:
                    lock_file.unlink()
                    print(f"      ✓ Removed: {pattern}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"      ✗ Could not remove {pattern}: {e}")

            # Check subdirectories
            for lock_file in session_path.glob(f"**/{pattern}"):
                try:
                    lock_file.unlink()
                    print(f"      ✓ Removed: {lock_file.relative_to(session_path)}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"      ✗ Could not remove {lock_file.name}: {e}")

        if cleaned_count == 0:
            print("      ✓ No stale locks found")
        else:
            print(f"      ✓ Cleaned up {cleaned_count} lock file(s)")

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

        # Clean up any stale lock files before opening browser
        self._cleanup_stale_locks()

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

                # Wait a bit for the Post button to become enabled
                page.wait_for_timeout(2000)

                # Try Ctrl+Enter first (Facebook's universal submit shortcut)
                print("   Trying Ctrl+Enter keyboard shortcut...")
                try:
                    page.keyboard.press("Control+Enter")
                    page.wait_for_timeout(3000)

                    # Check if modal closed (success)
                    modal_count = page.locator('[role="dialog"]').count()
                    if modal_count == 0:
                        print("✅ Ctrl+Enter worked! Post submitted.")
                        post_clicked = True
                    else:
                        print(f"   Ctrl+Enter didn't work (modal count: {modal_count}), trying button click...")
                        post_clicked = False
                except Exception as e:
                    print(f"   Ctrl+Enter failed: {e}")
                    post_clicked = False

                # If Ctrl+Enter didn't work, try clicking the button
                if not post_clicked:
                    # Find the Post button by checking if it's enabled
                    post_button_selectors = [
                        # Most specific: Enabled Post button within dialog
                        '[role="dialog"] [role="button"][aria-label="Post"]:not([aria-disabled="true"])',
                        # Backup: Any enabled Post button
                        '[role="button"][aria-label="Post"]:not([aria-disabled="true"])',
                        # Fallback: Any Post button
                        '[role="button"][aria-label="Post"]',
                    ]

                    for selector in post_button_selectors:
                        try:
                            buttons = page.locator(selector)
                            count = buttons.count()
                            if count > 0:
                                print(f"   Found {count} button(s) matching: {selector}")

                                # Collect all buttons with their positions
                                button_info = []
                                for i in range(count):
                                    button = buttons.nth(i)
                                    if not button.is_visible():
                                        continue

                                    try:
                                        aria_label = button.get_attribute('aria-label')
                                        aria_disabled = button.get_attribute('aria-disabled')

                                        # Skip if disabled
                                        if aria_disabled == "true":
                                            print(f"   Skipping button #{i+1}: disabled")
                                            continue

                                        # Skip if it's "Add to your post" button
                                        if aria_label and "Add to your post" in aria_label:
                                            print(f"   Skipping button #{i+1}: 'Add to your post'")
                                            continue

                                        # Get button position
                                        bbox = button.bounding_box()
                                        if bbox:
                                            button_info.append({
                                                'index': i,
                                                'y': bbox['y'],
                                                'x': bbox['x'],
                                                'aria_label': aria_label,
                                                'aria_disabled': aria_disabled,
                                                'button': button
                                            })
                                            print(f"   Button #{i+1}: aria-label='{aria_label}', disabled={aria_disabled}, y={int(bbox['y'])}, x={int(bbox['x'])}")
                                    except Exception as e:
                                        print(f"   Could not get info for button #{i+1}: {e}")
                                        continue

                                if not button_info:
                                    print(f"   No valid buttons found for selector: {selector}")
                                    continue

                                # Sort by y position (descending) - highest y is at the bottom
                                button_info.sort(key=lambda b: b['y'], reverse=True)

                                # Click the button with the highest y (at the bottom)
                                bottom_button = button_info[0]
                                print(f"   🎯 Selecting button at BOTTOM: y={int(bottom_button['y'])}, x={int(bottom_button['x'])}")

                                # Try JavaScript click first
                                try:
                                    print(f"   Trying JavaScript click...")
                                    page.evaluate("""(selector, index) => {
                                        const buttons = document.querySelectorAll(selector);
                                        if (buttons[index]) {
                                            buttons[index].click();
                                            return true;
                                        }
                                        return false;
                                    }""", selector, bottom_button['index'])
                                    print(f"✅ JavaScript clicked Post button at bottom")
                                    post_clicked = True
                                    break
                                except Exception as e1:
                                    print(f"   JavaScript click failed, trying force click...")

                                    # Try force click as backup
                                    try:
                                        bottom_button['button'].click(timeout=3000, force=True)
                                        print(f"✅ Force clicked Post button at bottom")
                                        post_clicked = True
                                        break
                                    except Exception as e2:
                                        print(f"   Force click failed: {str(e2)[:80]}")
                                        continue

                        except Exception as e:
                            print(f"   Selector {selector} failed: {str(e)[:80]}")
                            continue

                if not post_clicked:
                    print("❌ Could not find or click Post button")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Post button not found",
                        "message": "Could not find or click the Post button"
                    }

                # Wait briefly for post to be submitted
                print("⏳ Waiting for post to be submitted...")
                page.wait_for_timeout(2000)

                # Verify post was actually submitted by checking for failure indicators
                print("🔍 Verifying post submission...")

                # Check for "save draft" or "discard" modals (indicates failure)
                draft_indicators = [
                    "Save draft",
                    "Discard post",
                    "Save as draft",
                    "Discard",
                ]

                found_draft_modal = False
                for indicator in draft_indicators:
                    if page.locator(f'text="{indicator}"').count() > 0:
                        print(f"   ❌ Found draft/discard modal: '{indicator}'")
                        found_draft_modal = True
                        break

                # If draft modal found, post failed
                if found_draft_modal:
                    print("❌ Post was NOT submitted - draft/discard modal detected")

                    # Take screenshot for debugging
                    try:
                        screenshot_path = self.vault_path / "gold" / "debug_facebook_draft_modal.png"
                        page.screenshot(path=str(screenshot_path))
                        print(f"   📸 Screenshot saved: {screenshot_path}")
                    except:
                        pass

                    browser.close()
                    return {
                        "success": False,
                        "error": "Draft modal detected",
                        "message": "Post was not submitted - save draft modal appeared. The wrong button was clicked."
                    }

                # If no draft modal found, assume success
                # (Success messages disappear too quickly to reliably detect)
                print("✅ No draft modal detected - post submitted successfully!")

                # Wait a bit longer to ensure post is fully processed
                page.wait_for_timeout(2000)

                browser.close()

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

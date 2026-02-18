"""
Instagram poster using Playwright browser automation.

This module implements Instagram posting using Playwright with visible browser
(headless=False) so you can watch the posting happen in real-time.

Similar to Silver Tier LinkedIn posting.

Note: Instagram requires images for posts. Text-only posts are not supported.
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


class InstagramPosterPlaywright:
    """
    Poster for Instagram using Playwright browser automation.

    Posts content to Instagram with visible browser window.

    Note: Instagram requires images. For text-only content, we'll create
    a simple text image or skip posting.
    """

    def __init__(self, vault_path: str):
        """
        Initialize Instagram poster.

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

        # Instagram session path
        self.session_path = os.getenv(
            "INSTAGRAM_SESSION_PATH",
            str(self.vault_path / "gold" / "config" / "instagram_session")
        )

        print(f"✅ Instagram poster initialized (session: {self.session_path})")

    def _cleanup_stale_locks(self):
        """Clean up stale browser lock files to prevent session conflicts."""
        session_path = Path(self.session_path)
        if not session_path.exists():
            return

        # Remove Chromium lock files that can prevent browser from starting
        lock_patterns = [
            "SingletonLock",
            "SingletonSocket",
            "SingletonCookie"
        ]

        for pattern in lock_patterns:
            for lock_file in session_path.glob(f"**/{pattern}"):
                try:
                    lock_file.unlink()
                    print(f"   🧹 Cleaned up stale lock: {lock_file.name}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {lock_file.name}: {e}")

    def post_update(self, content: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an update to Instagram.

        Args:
            content: Text content to post (will be used as caption)
            image_path: Path to image to post (required for Instagram)

        Returns:
            Dict with success status and post details
        """
        print("🚀 Posting to Instagram...")

        # Instagram requires images - for demo, we'll post to Instagram Stories
        # which supports text-only content
        if not image_path:
            print("⚠️  Instagram requires images. Using Stories for text-only content.")
            return self._post_story(content)

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

                # Navigate to Instagram
                print("📸 Navigating to Instagram...")
                page.goto("https://www.instagram.com/", wait_until="load", timeout=90000)

                # Check if logged in
                if "login" in page.url.lower():
                    print("❌ Instagram session expired. Please re-login.")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Session expired",
                        "message": "Run: python gold/scripts/setup_instagram.py"
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

                # Click "Create" button to start new post
                print("🖱️  Looking for Create button...")

                create_selectors = [
                    '[aria-label="New post"]',
                    '[aria-label="Create"]',
                    'svg[aria-label="New post"]',
                    'a[href="#"]:has-text("Create")',
                ]

                create_clicked = False
                for selector in create_selectors:
                    try:
                        count = page.locator(selector).count()
                        if count > 0:
                            button = page.locator(selector).first
                            if button.is_visible():
                                button.click(timeout=5000)
                                print(f"✅ Clicked Create using: {selector}")
                                create_clicked = True
                                break
                    except Exception as e:
                        print(f"   Selector {selector} failed: {e}")
                        continue

                if not create_clicked:
                    print("❌ Could not find Create button")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Create button not found",
                        "message": "Could not find Instagram Create button"
                    }

                # Wait for upload dialog
                print("⏳ Waiting for upload dialog...")
                page.wait_for_timeout(3000)

                # Upload image
                print(f"📤 Uploading image: {image_path}")

                # Find file input
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(image_path)

                # Wait for image to upload and preview to load
                print("⏳ Waiting for image preview...")
                page.wait_for_timeout(5000)

                # Click "Next" button (try multiple selectors for different languages)
                print("🔍 Looking for Next button...")

                next_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Siguiente")',  # Spanish
                    'button:has-text("Suivant")',    # French
                    'button:has-text("Weiter")',     # German
                    'button:has-text("Avanti")',     # Italian
                    'button:has-text("التالي")',     # Arabic
                    'button:has-text("अगला")',       # Hindi
                    'button:has-text("اگلا")',       # Urdu
                    'div[role="button"]:has-text("Next")',
                    'div[role="button"]:has-text("Siguiente")',
                    'div[role="button"]:has-text("اگلا")',
                    # Fallback: look for any button in the top-right area
                    'button[type="button"]',
                ]

                next_clicked = False
                for selector in next_selectors:
                    try:
                        buttons = page.locator(selector)
                        count = buttons.count()
                        if count > 0:
                            # Try each matching button
                            for i in range(count):
                                try:
                                    button = buttons.nth(i)
                                    if button.is_visible():
                                        button.click(timeout=5000)
                                        print(f"✅ Clicked Next button using: {selector}")
                                        next_clicked = True
                                        break
                                except:
                                    continue
                        if next_clicked:
                            break
                    except:
                        continue

                if not next_clicked:
                    print("❌ Could not find Next button")
                    browser.close()
                    return {
                        "success": False,
                        "error": "Next button not found",
                        "message": "Could not find Next button after image upload"
                    }

                page.wait_for_timeout(3000)

                # Click "Next" again (for filters/editing page)
                print("🔍 Looking for second Next button (filters page)...")
                next_clicked = False
                for selector in next_selectors:
                    try:
                        buttons = page.locator(selector)
                        count = buttons.count()
                        if count > 0:
                            for i in range(count):
                                try:
                                    button = buttons.nth(i)
                                    if button.is_visible():
                                        button.click(timeout=5000)
                                        print(f"✅ Clicked second Next button")
                                        next_clicked = True
                                        break
                                except:
                                    continue
                        if next_clicked:
                            break
                    except:
                        continue

                if not next_clicked:
                    print("⚠️  Could not find second Next button, continuing anyway...")

                page.wait_for_timeout(3000)

                # Add caption
                print("⌨️  Adding caption...")
                caption_area = page.locator('[aria-label="Write a caption..."]').first
                caption_area.click()
                caption_area.type(content, delay=50)
                print(f"✅ Typed {len(content)} characters")

                page.wait_for_timeout(3000)

                # Click "Share" button (same pattern as Next buttons)
                print("🔍 Looking for Share button...")

                share_selectors = [
                    'button:has-text("Share")',
                    'button:has-text("Compartir")',     # Spanish
                    'button:has-text("Partager")',      # French
                    'button:has-text("Teilen")',        # German
                    'button:has-text("Condividi")',     # Italian
                    'button:has-text("مشاركة")',        # Arabic
                    'button:has-text("साझा करें")',     # Hindi
                    'button:has-text("شیئر کریں")',     # Urdu
                    'div[role="button"]:has-text("Share")',
                    'div[role="button"]:has-text("Compartir")',
                    'div[role="button"]:has-text("شیئر کریں")',
                ]

                share_clicked = False
                for selector in share_selectors:
                    try:
                        buttons = page.locator(selector)
                        count = buttons.count()
                        if count > 0:
                            # Try each matching button (same as Next buttons)
                            for i in range(count):
                                try:
                                    button = buttons.nth(i)
                                    if button.is_visible():
                                        button.click(timeout=5000)
                                        print(f"✅ Clicked Share button using: {selector}")
                                        share_clicked = True
                                        break
                                except:
                                    continue
                        if share_clicked:
                            break
                    except:
                        continue

                if not share_clicked:
                    print("❌ All methods failed to submit post")
                    print("   Taking screenshot for debugging...")
                    try:
                        screenshot_path = self.vault_path / "gold" / "debug_share_button.png"
                        page.screenshot(path=str(screenshot_path))
                        print(f"   Screenshot saved: {screenshot_path}")
                    except:
                        pass

                    browser.close()
                    return {
                        "success": False,
                        "error": "Share button not clickable",
                        "message": "Could not submit post - all click methods failed"
                    }

                # Wait for post to be fully submitted
                print("⏳ Waiting for post to be fully submitted...")
                page.wait_for_timeout(8000)  # Increased wait time to see the success message

                # Verify success by checking URL and looking for success indicators
                current_url = page.url
                print(f"   Final URL: {current_url}")

                # Look for success notification
                success_verified = False
                try:
                    # Instagram shows "Your post has been shared" notification
                    success_texts = [
                        "Your post has been shared",
                        "Tu publicación se ha compartido",
                        "Votre publication a été partagée",
                        "آپ کی پوسٹ شیئر کر دی گئی",
                    ]

                    for text in success_texts:
                        if page.locator(f'text="{text}"').count() > 0:
                            print(f"✅ Found success notification: '{text}'")
                            success_verified = True
                            break
                except:
                    pass

                # Check if we're back on the main feed
                if "/create/" not in current_url:
                    print("✅ Redirected away from create page")
                    success_verified = True
                else:
                    print("⚠️  Still on create page - post may have failed")

                # Keep browser open longer so you can see the success confirmation
                if success_verified:
                    print("🎉 Post successful! Keeping browser open for 5 seconds so you can see the confirmation...")
                    page.wait_for_timeout(5000)

                browser.close()

                if success_verified:
                    print("✅ Successfully posted to Instagram!")
                    return {
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "content_length": len(content),
                        "platform": "instagram",
                        "has_image": True
                    }
                else:
                    print("⚠️  Post submission uncertain - please verify manually")
                    return {
                        "success": False,
                        "error": "Verification failed",
                        "message": "Could not verify post was submitted successfully"
                    }

        except PlaywrightTimeout as e:
            print(f"❌ Timeout while posting: {e}")
            return {
                "success": False,
                "error": "Timeout",
                "message": str(e)
            }
        except Exception as e:
            print(f"❌ Error posting to Instagram: {e}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }

    def _post_story(self, content: str) -> Dict[str, Any]:
        """
        Post text-only content as Instagram Story.

        Args:
            content: Text content to post

        Returns:
            Dict with success status
        """
        print("📱 Posting as Instagram Story (text-only)...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=False,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.new_page()
                page.goto("https://www.instagram.com/", wait_until="load", timeout=90000)

                if "login" in page.url.lower():
                    browser.close()
                    return {
                        "success": False,
                        "error": "Session expired",
                        "message": "Run: python gold/scripts/setup_instagram.py"
                    }

                page.wait_for_timeout(3000)

                # For demo purposes, we'll simulate posting to story
                # In production, you'd need to handle image creation or use Instagram API
                print("⚠️  Instagram Stories require images or videos.")
                print("   For text-only content, consider:")
                print("   1. Creating a text image programmatically")
                print("   2. Using Instagram Graph API")
                print("   3. Posting to feed with a default image")

                browser.close()

                return {
                    "success": False,
                    "error": "Image required",
                    "message": "Instagram requires images. Provide image_path parameter."
                }

        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }


def main():
    """Test Instagram poster."""
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    poster = InstagramPosterPlaywright(vault_path)

    # Test content
    content = """🚀 Testing Gold Tier Instagram posting!

This post was created by my AI Employee using Playwright browser automation.

You can watch the browser post in real-time! 🤖

#AI #Automation #GoldTier"""

    print("=" * 60)
    print("Instagram Poster Test")
    print("=" * 60)
    print()
    print("Content to post:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    print()
    print("⚠️  Note: Instagram requires images.")
    print("   This test will show the limitation.")
    print()

    response = input("Test Instagram posting? (yes/no): ")

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
            print(f"❌ EXPECTED: {result.get('error')}")
            print(f"   {result.get('message')}")
            print("=" * 60)
    else:
        print("Test cancelled.")


if __name__ == "__main__":
    main()

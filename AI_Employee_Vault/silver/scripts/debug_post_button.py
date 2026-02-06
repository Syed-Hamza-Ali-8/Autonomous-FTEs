#!/usr/bin/env python3
"""
Debug script to investigate LinkedIn Post button interaction.
This simulates the full posting flow and captures detailed state information.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_post_button():
    """Debug the Post button interaction in LinkedIn."""

    vault_path = Path(__file__).parent.parent.parent
    session_dir = vault_path / "silver" / "config" / "linkedin_session"

    if not session_dir.exists():
        logger.error(f"Session directory not found: {session_dir}")
        return

    logger.info("=" * 60)
    logger.info("LinkedIn Post Button Debug")
    logger.info("=" * 60)

    with sync_playwright() as p:
        # Launch browser with saved session
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={"width": 1280, "height": 720}
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            # Navigate to LinkedIn feed
            logger.info("Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
            page.wait_for_timeout(3000)

            # STEP 1: Click "Start a post"
            logger.info("\n" + "=" * 60)
            logger.info("STEP 1: Finding and clicking 'Start a post' button")
            logger.info("=" * 60)

            # Take screenshot before clicking
            screenshot_path = vault_path / "silver" / "Logs" / "start_post_before_click.png"
            page.screenshot(path=str(screenshot_path))
            logger.info(f"  Screenshot saved: {screenshot_path}")

            # More specific selectors that target the actual clickable button
            start_button_selectors = [
                # Target the share box trigger specifically
                'button.share-box-feed-entry__trigger',
                '.share-box-feed-entry__trigger',
                '[data-control-name="share_box_trigger"]',
                # Role-based selectors
                '[role="button"]:has-text("Start a post")',
                'div[role="button"]:has-text("Start a post")',
                # Fallback to broader selectors
                'button:has-text("Start a post")',
                'div:has-text("Start a post")',
            ]

            start_clicked = False
            for selector in start_button_selectors:
                try:
                    count = page.locator(selector).count()
                    logger.info(f"\n  Selector: {selector}")
                    logger.info(f"  Count: {count}")

                    if count > 0:
                        # Find the first VISIBLE and ENABLED element
                        for i in range(count):
                            try:
                                button = page.locator(selector).nth(i)
                                if button.is_visible() and button.is_enabled():
                                    logger.info(f"  Found visible/enabled element at index {i}")
                                    button.wait_for(state="visible", timeout=5000)
                                    button.click(timeout=5000)
                                    logger.info(f"  ✓ Clicked successfully!")
                                    start_clicked = True
                                    break
                            except Exception as e:
                                logger.debug(f"  Element {i} failed: {e}")
                                continue

                        if start_clicked:
                            break
                except Exception as e:
                    logger.info(f"  ✗ Failed: {e}")

            if not start_clicked:
                logger.error("Could not click 'Start a post' button")
                browser.close()
                return

            # STEP 2: Wait for editor and type test content
            logger.info("\n" + "=" * 60)
            logger.info("STEP 2: Typing test content")
            logger.info("=" * 60)

            page.wait_for_selector('[role="textbox"]', timeout=10000)
            editor = page.locator('[role="textbox"]').first
            editor.click()
            page.wait_for_timeout(500)

            test_content = "Test post - debugging Post button interaction"
            editor.fill("")
            page.wait_for_timeout(500)
            editor.type(test_content, delay=50)

            logger.info(f"  ✓ Typed content: {test_content}")

            # Wait for content to be processed
            page.wait_for_timeout(3000)

            # STEP 3: Check for "Done" button
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: Checking for 'Done' button")
            logger.info("=" * 60)

            done_selectors = [
                'button:has-text("Done")',
                '[role="dialog"] button:has-text("Done")',
                'button[aria-label*="Done"]',
            ]

            done_clicked = False
            for selector in done_selectors:
                try:
                    count = page.locator(selector).count()
                    logger.info(f"  Selector: {selector}")
                    logger.info(f"  Count: {count}")

                    if count > 0:
                        button = page.locator(selector).first
                        if not button.is_disabled():
                            button.click(timeout=5000)
                            logger.info(f"  ✓ Clicked 'Done' button")
                            done_clicked = True
                            page.wait_for_timeout(2000)
                            break
                except Exception as e:
                    logger.info(f"  ✗ Failed: {e}")

            if not done_clicked:
                logger.info("  No 'Done' button found - proceeding to 'Post'")

            # STEP 4: Analyze Post button in detail
            logger.info("\n" + "=" * 60)
            logger.info("STEP 4: Analyzing 'Post' button")
            logger.info("=" * 60)

            page.wait_for_timeout(2000)

            # Take screenshot before attempting to click
            screenshot_path = vault_path / "silver" / "Logs" / "post_button_before_click.png"
            page.screenshot(path=str(screenshot_path))
            logger.info(f"  Screenshot saved: {screenshot_path}")

            post_button_selectors = [
                'button.share-actions__primary-action:not([disabled])',
                '[role="dialog"] button.share-actions__primary-action:not([disabled])',
                'button:has-text("Post"):not([disabled])',
                'button[aria-label*="Post"]:not([disabled])',
                'button.artdeco-button--primary:has-text("Post")',
            ]

            logger.info("\n  Testing all Post button selectors:")
            for i, selector in enumerate(post_button_selectors, 1):
                try:
                    count = page.locator(selector).count()
                    logger.info(f"\n  [{i}] Selector: {selector}")
                    logger.info(f"      Count: {count}")

                    if count > 0:
                        button = page.locator(selector).first

                        # Get detailed button state
                        is_visible = button.is_visible()
                        is_enabled = button.is_enabled()
                        is_disabled = button.is_disabled()

                        logger.info(f"      Visible: {is_visible}")
                        logger.info(f"      Enabled: {is_enabled}")
                        logger.info(f"      Disabled: {is_disabled}")

                        # Get button attributes
                        try:
                            aria_label = button.get_attribute("aria-label")
                            logger.info(f"      Aria-label: {aria_label}")
                        except:
                            pass

                        try:
                            classes = button.get_attribute("class")
                            logger.info(f"      Classes: {classes}")
                        except:
                            pass

                except Exception as e:
                    logger.info(f"      Error: {e}")

            # STEP 5: Attempt to click Post button
            logger.info("\n" + "=" * 60)
            logger.info("STEP 5: Attempting to click 'Post' button")
            logger.info("=" * 60)

            post_clicked = False
            for selector in post_button_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        button = page.locator(selector).first
                        button.wait_for(state="visible", timeout=5000)

                        if not button.is_disabled():
                            button.scroll_into_view_if_needed()
                            page.wait_for_timeout(500)

                            logger.info(f"  Attempting click with: {selector}")
                            button.click(timeout=5000)
                            logger.info(f"  ✓ Click executed")
                            post_clicked = True
                            break
                except Exception as e:
                    logger.info(f"  ✗ Failed: {e}")

            if not post_clicked:
                logger.error("Could not click Post button")
                browser.close()
                return

            # STEP 6: Verify submission
            logger.info("\n" + "=" * 60)
            logger.info("STEP 6: Verifying post submission")
            logger.info("=" * 60)

            page.wait_for_timeout(3000)

            # Check if modal is still open
            modal_count = page.locator('[role="dialog"]').count()
            logger.info(f"  Modal count after click: {modal_count}")

            if modal_count > 0:
                logger.warning("  ⚠ Modal still open - post may not have submitted")

                # Take another screenshot
                screenshot_path = vault_path / "silver" / "Logs" / "post_button_after_click.png"
                page.screenshot(path=str(screenshot_path))
                logger.info(f"  Screenshot saved: {screenshot_path}")

                # Wait a bit more
                page.wait_for_timeout(3000)
                modal_count = page.locator('[role="dialog"]').count()
                logger.info(f"  Modal count after additional wait: {modal_count}")

                if modal_count > 0:
                    logger.error("  ✗ Post did NOT submit - modal still open")
                else:
                    logger.info("  ✓ Modal closed - post submitted successfully")
            else:
                logger.info("  ✓ Modal closed immediately - post submitted successfully")

            logger.info("\n" + "=" * 60)
            logger.info("Debug complete - browser will stay open for inspection")
            logger.info("Press Enter to close...")
            logger.info("=" * 60)
            input()

        except Exception as e:
            logger.error(f"Error during debug: {e}", exc_info=True)
        finally:
            browser.close()

if __name__ == "__main__":
    debug_post_button()

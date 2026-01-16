#!/usr/bin/env python3
"""
LinkedIn posting with CORRECT two-step flow: Done → Post

This script implements the actual LinkedIn posting flow:
1. Fill content
2. Click "Done" to confirm content
3. Click "Post" to submit
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger

# Playwright imports
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def post_to_linkedin_correct_flow(content: str, headless: bool = False, inspection_time: int = 30):
    """
    Post to LinkedIn with correct two-step flow.

    Args:
        content: Text content to post
        headless: Whether to run in headless mode
        inspection_time: Seconds to keep browser open for inspection

    Returns:
        bool: True if post succeeded, False otherwise
    """

    logger = get_logger("linkedin_correct_flow")

    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed")
        return False

    # Get vault path
    vault_path = Path(__file__).parent.parent.parent

    # Load environment variables
    env_path = vault_path / "silver" / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Get LinkedIn session path
    session_path = os.getenv(
        "LINKEDIN_SESSION_PATH",
        str(vault_path / "silver" / "config" / "linkedin_session")
    )

    print("=" * 70)
    print("LinkedIn Posting - CORRECT FLOW (Done → Post)")
    print("=" * 70)
    print(f"\n📝 Content to post:\n{content}\n")
    print("-" * 70)

    try:
        with sync_playwright() as p:
            print("\n1️⃣  Launching browser...")

            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("2️⃣  Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Check if logged in
            if "login" in page.url.lower() or "authwall" in page.url.lower():
                print("\n❌ LinkedIn session expired!")
                print("   Run: python silver/scripts/setup_linkedin.py")
                browser.close()
                return False

            print("   ✅ Logged in successfully")

            # Wait for page to load
            print("\n3️⃣  Waiting for page to fully load...")
            page.wait_for_timeout(3000)
            print("   ✅ Page loaded")

            # Click "Start a post"
            print("\n4️⃣  Clicking 'Start a post' button...")
            page.click('button:has-text("Start a post")', timeout=15000)
            print("   ✅ Clicked 'Start a post'")

            # Wait for editor to appear
            print("\n5️⃣  Waiting for editor to appear...")
            page.wait_for_selector('[role="textbox"]', timeout=10000)
            print("   ✅ Editor appeared")

            # Fill content
            print("\n6️⃣  Filling content...")
            editor = page.locator('[role="textbox"]').first
            editor.click()
            editor.fill(content)
            print("   ✅ Content filled")

            # Wait for content to be processed
            page.wait_for_timeout(2000)

            # STEP 1: Click "Done" button to confirm content
            print("\n7️⃣  Looking for 'Done' button...")

            done_selectors = [
                'button:has-text("Done")',
                '[role="dialog"] button:has-text("Done")',
                'button[aria-label*="Done"]',
            ]

            done_clicked = False
            for selector in done_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"   Found 'Done' button: {selector} ({count} found)")
                        button = page.locator(selector).first

                        if not button.is_disabled():
                            button.click(timeout=5000)
                            print(f"   ✅ Clicked 'Done' button")
                            done_clicked = True
                            break
                except Exception as e:
                    print(f"   ⚠️  Selector {selector} failed: {e}")
                    continue

            if not done_clicked:
                print("   ⚠️  No 'Done' button found - might not be needed")
                print("   Proceeding to look for 'Post' button...")
            else:
                # Wait after clicking Done
                print("   Waiting for preview to appear...")
                page.wait_for_timeout(2000)

            # STEP 2: Click "Post" button to actually submit
            print("\n8️⃣  Looking for 'Post' button to submit...")

            # After clicking Done (or if no Done button), look for the submit Post button
            post_selectors = [
                'button.share-actions__primary-action',                    # Primary action button
                '[role="dialog"] button.share-actions__primary-action',   # More specific
                'button:has-text("Post"):not([disabled])',                 # Enabled Post button
                '[aria-label*="Post"]',                                    # Post aria-label
            ]

            post_clicked = False
            for selector in post_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"   Found 'Post' button: {selector} ({count} found)")
                        button = page.locator(selector).first

                        if not button.is_disabled():
                            # Wait for button to be ready
                            button.wait_for(state="visible", timeout=5000)

                            # Click the button
                            button.click(timeout=5000)
                            print(f"   ✅ Clicked 'Post' button using: {selector}")
                            post_clicked = True
                            break
                except Exception as e:
                    print(f"   ⚠️  Selector {selector} failed: {e}")
                    continue

            if not post_clicked:
                print("\n❌ Could not find or click 'Post' button")
                print("   Keeping browser open for manual inspection...")
                page.wait_for_timeout(60000)  # 60 seconds
                browser.close()
                return False

            # VERIFICATION: Check if modal closed
            print("\n9️⃣  Verifying post submission...")
            page.wait_for_timeout(3000)

            modal_count = page.locator('[role="dialog"]').count()
            print(f"   Modal count after clicking: {modal_count}")

            if modal_count == 0:
                print("   ✅ Modal closed - post submitted successfully!")
                success = True
            else:
                print("   ⚠️  Modal still open - checking if post is processing...")

                # Sometimes modal stays open briefly while processing
                page.wait_for_timeout(3000)
                modal_count = page.locator('[role="dialog"]').count()

                if modal_count == 0:
                    print("   ✅ Modal closed after delay - post submitted!")
                    success = True
                else:
                    print("   ❌ Modal still open - post did NOT submit")
                    success = False

            # Take screenshot
            screenshot_path = vault_path / "linkedin_post_result.png"
            page.screenshot(path=str(screenshot_path))
            print(f"\n📸 Screenshot saved: {screenshot_path}")

            # Keep browser open for inspection
            print(f"\n🔍 Keeping browser open for {inspection_time} seconds for inspection...")
            print("   Check your LinkedIn profile to verify the post appeared")
            page.wait_for_timeout(inspection_time * 1000)

            browser.close()

            print("\n" + "=" * 70)
            if success:
                print("✅ POST SUCCESSFULLY SUBMITTED!")
                print("\nVerify on LinkedIn:")
                print("1. Go to your profile")
                print("2. Check 'Activity' section")
                print("3. Post should appear within 30 seconds")
            else:
                print("❌ POST FAILED TO SUBMIT")
                print("\nTroubleshooting:")
                print("1. Check the screenshot to see what happened")
                print("2. Try posting manually to see the exact flow")
                print("3. LinkedIn UI may have changed - update selectors")
            print("=" * 70)

            return success

    except PlaywrightTimeout as e:
        print(f"\n❌ Timeout: {e}")
        logger.error(f"Timeout: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""

    # Test content
    content = """🚀 Testing LinkedIn automation with correct two-step flow!

This post uses the proper sequence:
1. Fill content
2. Click "Done"
3. Click "Post"

#Automation #Testing #AI"""

    print("\n🔧 LinkedIn Posting - Correct Flow Test")
    print("   This script implements: Done → Post\n")

    # Run with visible browser and 30 second inspection time
    success = post_to_linkedin_correct_flow(
        content,
        headless=False,
        inspection_time=30  # 30 seconds to verify
    )

    if success:
        print("\n✅ Success! Check your LinkedIn profile to verify the post.")
        sys.exit(0)
    else:
        print("\n❌ Failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

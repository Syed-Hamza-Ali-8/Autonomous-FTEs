#!/usr/bin/env python3
"""
Fixed LinkedIn posting script with proper button targeting and verification.

This script addresses the issue where the post appears to succeed but doesn't actually post.
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


def post_to_linkedin_fixed(content: str, headless: bool = False):
    """
    Post to LinkedIn with proper button targeting and verification.

    Args:
        content: Text content to post
        headless: Whether to run in headless mode

    Returns:
        bool: True if post succeeded, False otherwise
    """

    logger = get_logger("linkedin_fixed")

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

    print("=" * 60)
    print("LinkedIn Posting Script (FIXED)")
    print("=" * 60)
    print(f"\n📝 Content to post:\n{content}\n")
    print("-" * 60)

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

            # CRITICAL: Wait for Post button to become enabled
            print("\n7️⃣  Waiting for Post button to be enabled...")
            page.wait_for_timeout(2000)  # Give LinkedIn time to enable the button

            # Find the CORRECT Post button - the one inside the modal that's NOT disabled
            print("\n8️⃣  Finding the correct Post button...")

            # Strategy: Use the most specific selector that targets the submit button
            # The button inside the dialog that's not an aria-label button
            correct_selector = '[role="dialog"] button.share-actions__primary-action'

            # Fallback selectors in order of preference
            selectors_to_try = [
                '[role="dialog"] button.share-actions__primary-action',  # Most specific
                'button.share-actions__primary-action',                   # Primary action
                '[role="dialog"] button:has-text("Post"):not([disabled])', # Dialog Post not disabled
            ]

            clicked = False
            for selector in selectors_to_try:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        # Check if button is enabled
                        button = page.locator(selector).first
                        is_disabled = button.is_disabled()

                        print(f"   Trying: {selector}")
                        print(f"   Found: {count}, Disabled: {is_disabled}")

                        if not is_disabled:
                            # Wait for button to be visible and enabled
                            button.wait_for(state="visible", timeout=5000)

                            # Click the button
                            button.click(timeout=5000)
                            print(f"   ✅ Clicked using: {selector}")
                            clicked = True
                            break
                except Exception as e:
                    print(f"   ❌ Failed with {selector}: {e}")
                    continue

            if not clicked:
                print("\n❌ Could not click Post button")
                browser.close()
                return False

            # CRITICAL: Verify the post was submitted
            print("\n9️⃣  Verifying post submission...")

            # Wait and check if modal closed (indicates successful post)
            page.wait_for_timeout(3000)

            modal_count = page.locator('[role="dialog"]').count()
            print(f"   Modal count after click: {modal_count}")

            if modal_count == 0:
                print("   ✅ Modal closed - post submitted successfully!")

                # Additional verification: Check if we're back on feed
                page.wait_for_timeout(2000)
                current_url = page.url

                if "feed" in current_url:
                    print("   ✅ Returned to feed - post confirmed!")
                    success = True
                else:
                    print(f"   ⚠️  Unexpected URL: {current_url}")
                    success = False
            else:
                print("   ❌ Modal still open - post did NOT submit")
                print("   This means the wrong button was clicked or post failed")
                success = False

            # Take screenshot for verification
            screenshot_path = vault_path / "linkedin_post_result.png"
            page.screenshot(path=str(screenshot_path))
            print(f"\n📸 Screenshot saved: {screenshot_path}")

            # Keep browser open briefly if visible
            if not headless:
                print("\n🔍 Keeping browser open for 5 seconds for inspection...")
                page.wait_for_timeout(5000)

            browser.close()

            print("\n" + "=" * 60)
            if success:
                print("✅ POST SUCCESSFULLY SUBMITTED!")
            else:
                print("❌ POST FAILED TO SUBMIT")
            print("=" * 60)

            return success

    except PlaywrightTimeout as e:
        print(f"\n❌ Timeout: {e}")
        logger.error(f"Timeout: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error: {e}")
        return False


def main():
    """Main entry point."""

    # Test content
    content = """🚀 Testing automated LinkedIn posting with improved button targeting!

This post is being made by an AI automation system that properly identifies and clicks the correct Post button.

#Automation #Testing #AI"""

    print("\n🔧 LinkedIn Posting Fix Test")
    print("   This script uses improved button targeting\n")

    # Run with visible browser so user can see what happens
    success = post_to_linkedin_fixed(content, headless=False)

    if success:
        print("\n✅ Success! Check your LinkedIn profile to verify the post.")
        sys.exit(0)
    else:
        print("\n❌ Failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

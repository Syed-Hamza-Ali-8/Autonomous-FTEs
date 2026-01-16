#!/usr/bin/env python3
"""
Debug script for LinkedIn posting with visible browser and step-by-step execution.

This script opens a visible browser and pauses at each step so you can see what's happening.
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


def debug_linkedin_post():
    """Debug LinkedIn posting with visible browser and step-by-step execution."""

    logger = get_logger("debug_linkedin")

    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed")
        print("Run: pip install playwright && playwright install chromium")
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

    # Content to post
    content = """🚀 Excited to share insights on AI automation and business productivity!

Leveraging AI tools to streamline workflows and boost efficiency is no longer optional—it's essential for staying competitive in 2026.

What's your experience with AI automation in your business?

#AI #Automation #BusinessProductivity #DigitalTransformation"""

    print("=" * 60)
    print("LinkedIn Posting Debug Script")
    print("=" * 60)
    print(f"\n📝 Content to post:\n{content}\n")
    print("-" * 60)
    print("\n⚠️  This will open a VISIBLE browser window")
    print("   You'll be able to see each step as it happens\n")

    input("Press Enter to start...")

    try:
        with sync_playwright() as p:
            print("\n1️⃣  Launching browser (VISIBLE mode)...")

            # Launch browser with persistent session - VISIBLE (headless=False)
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # VISIBLE BROWSER
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
            page.wait_for_timeout(3000)  # Simple 3 second wait
            print("   ✅ Page loaded")

            # Take screenshot before posting
            screenshot_path = vault_path / "linkedin_before_post.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot saved: {screenshot_path}")

            # Click "Start a post"
            print("\n4️⃣  Clicking 'Start a post' button...")
            input("   Press Enter to click 'Start a post'...")

            page.click('button:has-text("Start a post")', timeout=15000)
            print("   ✅ Clicked 'Start a post'")

            # Wait for editor to appear
            print("\n5️⃣  Waiting for editor to appear...")
            page.wait_for_selector('[role="textbox"]', timeout=10000)
            print("   ✅ Editor appeared")

            # Fill content
            print("\n6️⃣  Filling content...")
            input("   Press Enter to fill content...")

            editor = page.locator('[role="textbox"]').first
            editor.click()
            editor.fill(content)
            print("   ✅ Content filled")

            page.wait_for_timeout(2000)

            # Click Post button
            print("\n7️⃣  Ready to click 'Post' button...")

            # Show how many Post buttons are on the page
            post_button_count = page.locator('button:has-text("Post")').count()
            print(f"   Found {post_button_count} 'Post' button(s)")

            input("   Press Enter to click 'Post'...")

            # Target the Post button inside the modal dialog specifically
            post_button_selectors = [
                '[role="dialog"] button:has-text("Post")',  # Post button inside dialog
                'button[data-test-modal-close-btn]',         # Modal close/submit button
                '.share-actions__primary-action',            # Primary action button
            ]

            clicked = False
            for selector in post_button_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"   Trying selector: {selector} ({count} found)")
                        page.locator(selector).first.click(timeout=5000)
                        print(f"   ✅ Clicked using: {selector}")
                        clicked = True
                        break
                except Exception as e:
                    print(f"   ❌ Failed with {selector}: {e}")
                    continue

            if not clicked:
                print("   ❌ Could not click Post button")
                browser.close()
                return False

            # Wait for post to submit
            print("\n8️⃣  Waiting for post to submit...")
            page.wait_for_timeout(5000)

            # Check if modal closed (indicates successful post)
            modal_count = page.locator('[role="dialog"]').count()
            print(f"   Modal count: {modal_count}")

            if modal_count == 0:
                print("   ✅ Modal closed - post submitted successfully!")
            else:
                print("   ⚠️  Modal still open - post may not have submitted")

            # Take screenshot after posting
            screenshot_path = vault_path / "linkedin_after_post.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot saved: {screenshot_path}")

            print("\n9️⃣  Keeping browser open for 10 seconds...")
            print("   (Check your LinkedIn profile to verify the post)")
            page.wait_for_timeout(10000)

            browser.close()

            print("\n" + "=" * 60)
            print("✅ Debug script completed!")
            print("=" * 60)
            print("\nCheck your LinkedIn profile to verify the post appeared.")
            print(f"Screenshots saved in: {vault_path}")

            return True

    except PlaywrightTimeout as e:
        print(f"\n❌ Timeout: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Debug script failed: {e}")
        return False


def main():
    """Main entry point."""
    print("\n🐛 LinkedIn Posting Debug Script")
    print("   This script will show you exactly what's happening\n")

    success = debug_linkedin_post()

    if not success:
        print("\n❌ Debug script failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
LinkedIn debug script - opens browser in visible mode to see what's happening.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger


def debug_linkedin():
    """Debug LinkedIn posting by opening browser in visible mode."""
    logger = get_logger("linkedin_debug")

    vault_path = Path(__file__).parent.parent.parent.absolute()
    session_path = vault_path / "silver" / "config" / "linkedin_session"

    print("=" * 60)
    print("LinkedIn Debug - Visual Mode")
    print("=" * 60)
    print()
    print("This will open a visible browser window.")
    print("You can see exactly what's happening on LinkedIn.")
    print()
    print("=" * 60)
    print()

    try:
        with sync_playwright() as p:
            # Launch browser in VISIBLE mode
            print("🌐 Opening browser (visible mode)...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,  # VISIBLE browser
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn feed
            print("📱 Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Check if logged in
            current_url = page.url
            print(f"✅ Current URL: {current_url}")

            if "login" in current_url.lower() or "authwall" in current_url.lower():
                print("❌ Not logged in! Session expired.")
                print("   Please run: python silver/scripts/setup_linkedin.py")
                browser.close()
                return

            print("✅ Logged in successfully!")
            print()

            # Wait for page to load
            print("⏳ Waiting for page to load (5 seconds)...")
            page.wait_for_timeout(5000)

            # Take screenshot
            screenshot_path = vault_path / "silver" / "Logs" / "linkedin_debug.png"
            page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")
            print()

            # Try to find "Start a post" button
            print("🔍 Looking for 'Start a post' button...")
            print()

            # Try different selectors
            selectors = [
                'button:has-text("Start a post")',
                'button:has-text("Start a Post")',
                'button:has-text("Share")',
                'button:has-text("share")',
                '[data-test-id="share-box-open"]',
                '.share-box-feed-entry__trigger',
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Share"]',
            ]

            found_buttons = []

            for selector in selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"✅ Found {count} element(s) with selector: {selector}")
                        found_buttons.append(selector)

                        # Get button text
                        for i in range(min(count, 3)):  # Check first 3
                            try:
                                text = page.locator(selector).nth(i).inner_text()
                                print(f"   Button {i+1} text: '{text}'")
                            except:
                                pass
                    else:
                        print(f"❌ Not found: {selector}")
                except Exception as e:
                    print(f"❌ Error with {selector}: {e}")

            print()

            if found_buttons:
                print(f"✅ Found {len(found_buttons)} working selector(s)!")
                print()
                print("Recommended selector:")
                print(f"   {found_buttons[0]}")
                print()

                # Try clicking the first one
                print("🖱️  Attempting to click the button...")
                try:
                    page.click(found_buttons[0], timeout=5000)
                    print("✅ Button clicked successfully!")
                    print()

                    # Wait for modal
                    page.wait_for_timeout(2000)

                    # Check if modal appeared
                    modal_count = page.locator('[role="dialog"]').count()
                    if modal_count > 0:
                        print(f"✅ Modal appeared! ({modal_count} dialog(s) found)")

                        # Take screenshot of modal
                        modal_screenshot = vault_path / "silver" / "Logs" / "linkedin_modal.png"
                        page.screenshot(path=str(modal_screenshot))
                        print(f"📸 Modal screenshot: {modal_screenshot}")
                    else:
                        print("⚠️  No modal appeared")

                except Exception as e:
                    print(f"❌ Click failed: {e}")
            else:
                print("❌ No working selectors found!")
                print()
                print("Possible reasons:")
                print("1. LinkedIn UI has changed")
                print("2. Different language/region")
                print("3. Account type (personal vs business)")
                print("4. Page not fully loaded")

            print()
            print("=" * 60)
            print("Browser will stay open for 30 seconds.")
            print("You can inspect the page manually.")
            print("=" * 60)
            print()

            # Keep browser open for inspection
            page.wait_for_timeout(30000)

            browser.close()
            print("✅ Debug complete!")

    except Exception as e:
        logger.error(f"Debug error: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_linkedin()

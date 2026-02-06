#!/usr/bin/env python3
"""
Visual LinkedIn Debugging Script
This script runs in visible mode with screenshots at each step
to help diagnose the posting issue.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def debug_linkedin_posting():
    """Debug LinkedIn posting with visual feedback."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"
    debug_dir = Path(__file__).parent.parent / "debug_screenshots"
    debug_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("Visual LinkedIn Debugging")
    print("=" * 70)
    print(f"\n📁 Session: {session_dir}")
    print(f"📁 Debug screenshots: {debug_dir}")

    test_content = """🔍 LinkedIn Debug Test

Testing our posting automation with visual debugging.

#Test #Automation"""

    print(f"\n📝 Content ({len(test_content)} chars):")
    print("-" * 70)
    print(test_content)
    print("-" * 70)

    with sync_playwright() as p:
        print("\n🌐 Launching browser (VISIBLE mode)...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,  # VISIBLE
            viewport={"width": 1280, "height": 900},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        try:
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Step 1: Navigate to LinkedIn
            print("\n📍 Step 1: Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            page.screenshot(path=str(debug_dir / "01_feed_loaded.png"))
            print(f"   ✓ Screenshot: 01_feed_loaded.png")
            print(f"   ✓ URL: {page.url}")

            # Check login status
            if "login" in page.url or "authwall" in page.url:
                print("   ❌ Not logged in!")
                return False
            print("   ✓ Logged in")

            # Step 2: Find and click "Start a post"
            print("\n📍 Step 2: Finding 'Start a post' button...")
            selectors = [
                'button:has-text("Start a post")',
                'button[aria-label*="Start a post"]',
                '.share-box-feed-entry__trigger',
            ]

            start_button = None
            for selector in selectors:
                try:
                    count = page.locator(selector).count()
                    print(f"   Trying: {selector} (found: {count})")
                    if count > 0:
                        start_button = page.locator(selector).first
                        print(f"   ✓ Found with: {selector}")
                        break
                except Exception as e:
                    print(f"   ✗ Failed: {e}")

            if not start_button:
                print("   ❌ Could not find 'Start a post' button")
                page.screenshot(path=str(debug_dir / "02_no_start_button.png"))
                return False

            print("   Clicking 'Start a post'...")
            start_button.click()
            time.sleep(2)
            page.screenshot(path=str(debug_dir / "02_clicked_start.png"))
            print(f"   ✓ Screenshot: 02_clicked_start.png")

            # Step 3: Find editor and type content
            print("\n📍 Step 3: Finding editor and typing content...")
            editor_selectors = [
                'div[role="textbox"][contenteditable="true"]',
                'div.ql-editor',
                '[contenteditable="true"]',
            ]

            editor = None
            for selector in editor_selectors:
                try:
                    count = page.locator(selector).count()
                    print(f"   Trying: {selector} (found: {count})")
                    if count > 0:
                        editor = page.locator(selector).first
                        print(f"   ✓ Found editor with: {selector}")
                        break
                except Exception as e:
                    print(f"   ✗ Failed: {e}")

            if not editor:
                print("   ❌ Could not find editor")
                page.screenshot(path=str(debug_dir / "03_no_editor.png"))
                return False

            print("   Typing content...")
            editor.click()
            time.sleep(0.5)
            editor.fill("")  # Clear first
            time.sleep(0.5)
            editor.type(test_content, delay=50)
            time.sleep(2)
            page.screenshot(path=str(debug_dir / "03_content_typed.png"))
            print(f"   ✓ Screenshot: 03_content_typed.png")

            # Step 4: Wait and check Post button state
            print("\n📍 Step 4: Checking Post button state...")
            time.sleep(3)  # Wait for LinkedIn to process
            page.screenshot(path=str(debug_dir / "04_before_post.png"))
            print(f"   ✓ Screenshot: 04_before_post.png")

            # Find Post button
            post_selectors = [
                'button.share-actions__primary-action',
                'button:has-text("Post")',
                'button[aria-label*="Post"]',
            ]

            post_button = None
            for selector in post_selectors:
                try:
                    count = page.locator(selector).count()
                    print(f"   Trying: {selector} (found: {count})")
                    if count > 0:
                        button = page.locator(selector).first
                        is_visible = button.is_visible()
                        is_enabled = not button.is_disabled()
                        print(f"   Button state: visible={is_visible}, enabled={is_enabled}")

                        if is_visible and is_enabled:
                            post_button = button
                            print(f"   ✓ Found enabled Post button with: {selector}")
                            break
                except Exception as e:
                    print(f"   ✗ Failed: {e}")

            if not post_button:
                print("   ❌ Could not find enabled Post button")
                page.screenshot(path=str(debug_dir / "04_no_post_button.png"))

                # Print page content for debugging
                print("\n   🔍 Checking for validation errors...")
                error_selectors = [
                    '.artdeco-inline-feedback--error',
                    '[role="alert"]',
                    '.share-creation-state__error',
                ]
                for selector in error_selectors:
                    try:
                        errors = page.locator(selector).all()
                        if errors:
                            for error in errors:
                                text = error.text_content()
                                print(f"   ⚠️  Error found: {text}")
                    except:
                        pass

                return False

            # Step 5: Click Post button
            print("\n📍 Step 5: Clicking Post button...")
            post_button.scroll_into_view_if_needed()
            time.sleep(0.5)

            try:
                post_button.click(timeout=5000)
                print("   ✓ Clicked Post button")
            except Exception as e:
                print(f"   ⚠️  Normal click failed: {e}")
                print("   Trying force click...")
                post_button.click(force=True)
                print("   ✓ Force clicked Post button")

            time.sleep(2)
            page.screenshot(path=str(debug_dir / "05_after_click.png"))
            print(f"   ✓ Screenshot: 05_after_click.png")

            # Step 6: Wait and verify
            print("\n📍 Step 6: Verifying post submission...")
            time.sleep(5)
            page.screenshot(path=str(debug_dir / "06_final_state.png"))
            print(f"   ✓ Screenshot: 06_final_state.png")

            # Check if modal is still open
            modal_count = page.locator('[role="dialog"]').count()
            print(f"   Modal count: {modal_count}")

            if modal_count > 0:
                print("   ❌ Modal still open - post did NOT submit")

                # Check for any error messages
                print("\n   🔍 Looking for error messages...")
                page.screenshot(path=str(debug_dir / "06_modal_still_open.png"))
                return False
            else:
                print("   ✓ Modal closed - post likely submitted!")

                # Check if we're back on feed
                current_url = page.url
                print(f"   Current URL: {current_url}")

                if "feed" in current_url:
                    print("   ✓ Back on feed - SUCCESS!")
                    return True
                else:
                    print(f"   ⚠️  Unexpected URL: {current_url}")
                    return False

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path=str(debug_dir / "error.png"))
                print(f"   Error screenshot: error.png")
            except:
                pass
            return False

        finally:
            print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)
            print("🔒 Closing browser...")
            browser.close()

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Visual LinkedIn Debugging - Watch the browser!")
    print("=" * 70)

    success = debug_linkedin_posting()

    print("\n" + "=" * 70)
    if success:
        print("✅ DEBUG COMPLETE - Posting works!")
    else:
        print("❌ DEBUG COMPLETE - Issue identified, check screenshots")
    print("=" * 70)
    print("\n📁 Check debug_screenshots/ folder for step-by-step images")

    sys.exit(0 if success else 1)

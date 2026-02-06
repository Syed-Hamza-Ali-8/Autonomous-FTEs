#!/usr/bin/env python3
"""
LinkedIn Simple Diagnostic
Uses simpler wait conditions and takes screenshots to diagnose the issue.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def diagnose_linkedin():
    """Diagnose LinkedIn posting issue with screenshots."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"
    screenshot_dir = Path(__file__).parent.parent / "debug_screenshots"
    screenshot_dir.mkdir(exist_ok=True)

    print("\n" + "="*70)
    print("LinkedIn Simple Diagnostic")
    print("="*70)

    with sync_playwright() as p:
        # Launch browser with session
        print("\n1. Launching browser...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,  # Visible browser
            viewport={"width": 1280, "height": 720},
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # Navigate to LinkedIn feed with simpler wait condition
        print("2. Navigating to LinkedIn feed (using domcontentloaded)...")
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            print("   ✓ Page loaded (domcontentloaded)")
        except Exception as e:
            print(f"   ✗ Error loading page: {e}")
            screenshot_path = screenshot_dir / "error_loading.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   Screenshot saved: {screenshot_path}")
            browser.close()
            return

        # Wait a bit for dynamic content
        print("3. Waiting for dynamic content to load...")
        page.wait_for_timeout(5000)

        # Take screenshot of current state
        screenshot_path = screenshot_dir / "linkedin_feed.png"
        page.screenshot(path=str(screenshot_path))
        print(f"   ✓ Screenshot saved: {screenshot_path}")

        # Check if we're logged in
        print("4. Checking login status...")
        url = page.url
        print(f"   Current URL: {url}")

        if "feed" not in url:
            print("   ✗ Not on feed page - might need to log in")
            screenshot_path = screenshot_dir / "not_logged_in.png"
            page.screenshot(path=str(screenshot_path))
            print(f"   Screenshot saved: {screenshot_path}")
            browser.close()
            return

        print("   ✓ On feed page")

        # Try to find any button with "Start" in the text
        print("5. Looking for buttons with 'Start' in text...")
        try:
            start_buttons = page.locator('button:has-text("Start")').all()
            print(f"   Found {len(start_buttons)} buttons with 'Start'")

            for i, button in enumerate(start_buttons[:5]):  # First 5 buttons
                try:
                    text = button.inner_text(timeout=1000)
                    is_visible = button.is_visible()
                    print(f"   Button {i}: '{text}' (visible={is_visible})")
                except:
                    pass
        except Exception as e:
            print(f"   Error finding buttons: {e}")

        # Try to find share box elements
        print("6. Looking for share box elements...")
        share_selectors = [
            '.share-box-feed-entry__trigger',
            '[data-control-name*="share"]',
            'button[aria-label*="post"]',
            'button[aria-label*="Start"]',
        ]

        for selector in share_selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    elem = page.locator(selector).first
                    is_visible = elem.is_visible()
                    text = elem.inner_text(timeout=1000) if is_visible else "N/A"
                    print(f"   ✓ Found '{selector}': count={count}, visible={is_visible}, text='{text}'")
                else:
                    print(f"   ✗ Not found: '{selector}'")
            except Exception as e:
                print(f"   ✗ Error with '{selector}': {str(e)[:50]}")

        # Get page title
        print("7. Page information...")
        title = page.title()
        print(f"   Page title: {title}")

        # Try to execute JavaScript to find elements
        print("8. Using JavaScript to find elements...")
        try:
            result = page.evaluate("""() => {
                // Find all buttons
                const buttons = Array.from(document.querySelectorAll('button'));
                const startButtons = buttons.filter(b =>
                    b.textContent.toLowerCase().includes('start') ||
                    b.textContent.toLowerCase().includes('post')
                );

                return startButtons.map(b => ({
                    text: b.textContent.trim(),
                    className: b.className,
                    ariaLabel: b.getAttribute('aria-label'),
                    dataControl: b.getAttribute('data-control-name')
                })).slice(0, 10);  // First 10 matches
            }""")

            print(f"   Found {len(result)} relevant buttons:")
            for i, btn in enumerate(result):
                print(f"   {i}. Text: '{btn['text'][:50]}'")
                print(f"      Class: '{btn['className'][:80]}'")
                print(f"      Aria: '{btn['ariaLabel']}'")
                print(f"      Data: '{btn['dataControl']}'")
                print()
        except Exception as e:
            print(f"   Error executing JavaScript: {e}")

        print("\n" + "="*70)
        print("Keeping browser open for 30 seconds for manual inspection...")
        print("="*70)
        page.wait_for_timeout(30000)

        browser.close()

        print("\n✓ Diagnostic complete!")
        print(f"\nScreenshots saved to: {screenshot_dir}")
        print("\nNext steps:")
        print("1. Review the console output above")
        print("2. Check the screenshots")
        print("3. Look for the correct selector information")

if __name__ == "__main__":
    try:
        diagnose_linkedin()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

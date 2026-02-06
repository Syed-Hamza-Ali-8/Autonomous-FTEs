#!/usr/bin/env python3
"""
Find LinkedIn Selectors - Simple Diagnostic
This script opens LinkedIn and prints all possible selectors for the "Start a post" button.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def find_selectors():
    """Find all possible selectors for LinkedIn posting."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"

    print("\n" + "="*70)
    print("LinkedIn Selector Finder")
    print("="*70)

    with sync_playwright() as p:
        # Launch browser with session
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,  # Visible browser
            viewport={"width": 1280, "height": 720},
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # Navigate to LinkedIn feed
        print("\n1. Navigating to LinkedIn feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        print("\n2. Analyzing page elements...")

        # Find all buttons
        print("\n--- All Button Texts ---")
        buttons = page.locator('button').all()
        for i, button in enumerate(buttons[:20]):  # First 20 buttons
            try:
                text = button.inner_text(timeout=1000)
                if text and len(text) < 50:  # Only short texts
                    print(f"  Button {i}: '{text}'")
            except:
                pass

        # Find elements with "post" in text (case insensitive)
        print("\n--- Elements containing 'post' ---")
        post_elements = page.locator('text=/post/i').all()
        for i, elem in enumerate(post_elements[:10]):
            try:
                tag = elem.evaluate('el => el.tagName')
                text = elem.inner_text(timeout=1000)
                classes = elem.evaluate('el => el.className')
                print(f"  {i}. <{tag}> class='{classes}' text='{text[:50]}'")
            except:
                pass

        # Find share box elements
        print("\n--- Share box elements ---")
        share_selectors = [
            '.share-box-feed-entry__trigger',
            '[data-control-name*="share"]',
            '.artdeco-button--tertiary',
            'button[aria-label*="post"]',
            'button[aria-label*="share"]',
        ]

        for selector in share_selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    elem = page.locator(selector).first
                    text = elem.inner_text(timeout=1000)
                    print(f"  ✓ Found {count}x '{selector}': '{text}'")
            except Exception as e:
                print(f"  ✗ '{selector}': {str(e)[:50]}")

        # Try to find the actual "Start a post" button by various methods
        print("\n--- Testing specific selectors ---")
        test_selectors = [
            'button:has-text("Start a post")',
            'button:has-text("Start")',
            'div[role="button"]:has-text("Start")',
            '.share-box-feed-entry__trigger',
            'button.share-box-feed-entry__trigger',
            '[data-control-name="share_box_trigger"]',
            'button[aria-label*="Start"]',
        ]

        for selector in test_selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    elem = page.locator(selector).first
                    is_visible = elem.is_visible()
                    text = elem.inner_text(timeout=1000) if is_visible else "N/A"
                    print(f"  ✓ FOUND: '{selector}' (count={count}, visible={is_visible}, text='{text}')")
                else:
                    print(f"  ✗ Not found: '{selector}'")
            except Exception as e:
                print(f"  ✗ Error with '{selector}': {str(e)[:50]}")

        # Take a screenshot
        screenshot_path = Path(__file__).parent.parent / "linkedin_selector_debug.png"
        page.screenshot(path=str(screenshot_path))
        print(f"\n3. Screenshot saved: {screenshot_path}")

        # Wait for manual inspection
        print("\n" + "="*70)
        print("MANUAL INSPECTION TIME")
        print("="*70)
        print("The browser will stay open for 30 seconds.")
        print("Please look at the page and identify the 'Start a post' button.")
        print("Check the console output above for possible selectors.")
        print("="*70)

        page.wait_for_timeout(30000)  # Wait 30 seconds

        browser.close()

        print("\n✓ Analysis complete!")
        print(f"✓ Screenshot saved to: {screenshot_path}")
        print("\nNext steps:")
        print("1. Review the console output above")
        print("2. Check the screenshot")
        print("3. Update the LinkedIn poster with the correct selector")

if __name__ == "__main__":
    try:
        find_selectors()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
LinkedIn Live Inspector
Opens LinkedIn in visible mode and pauses for manual inspection.
This helps identify the correct selectors for the current LinkedIn UI.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def inspect_linkedin():
    """Open LinkedIn and pause for manual inspection."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"

    print("\n" + "="*70)
    print("LinkedIn Live Inspector")
    print("="*70)
    print("\nThis script will:")
    print("1. Open LinkedIn in a visible browser")
    print("2. Navigate to your feed")
    print("3. Pause for 2 minutes so you can inspect the page")
    print("\nWhile the browser is open:")
    print("- Right-click on the 'Start a post' button")
    print("- Select 'Inspect' or 'Inspect Element'")
    print("- Look at the HTML to find the correct selector")
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

        print("\n2. Page loaded successfully!")
        print("\n" + "="*70)
        print("MANUAL INSPECTION TIME")
        print("="*70)
        print("\nThe browser is now open. Please:")
        print("1. Look for the 'Start a post' button on the page")
        print("2. Right-click on it and select 'Inspect'")
        print("3. Note down the button's:")
        print("   - Text content (exact text)")
        print("   - CSS classes")
        print("   - Any data-* attributes")
        print("   - aria-label attribute")
        print("\n4. Also try these in the browser console:")
        print("   document.querySelector('button:has-text(\"Start\")')")
        print("   document.querySelector('.share-box-feed-entry__trigger')")
        print("   document.querySelectorAll('button')")
        print("\nBrowser will stay open for 2 minutes...")
        print("="*70)

        # Wait 2 minutes for manual inspection
        page.wait_for_timeout(120000)

        print("\n3. Closing browser...")
        browser.close()

        print("\n✓ Inspection complete!")
        print("\nNext steps:")
        print("1. Share the selector information you found")
        print("2. We'll update the LinkedIn poster with the correct selector")

if __name__ == "__main__":
    try:
        inspect_linkedin()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

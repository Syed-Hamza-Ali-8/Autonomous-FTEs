#!/usr/bin/env python3
"""
Setup Facebook session for Playwright automation.

This script opens Facebook in a browser and saves your login session
so the automation can post on your behalf.

Similar to Silver Tier's setup_linkedin.py
"""

import sys
from pathlib import Path

# Add parent directory to path
VAULT_PATH = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(VAULT_PATH))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed!")
    print()
    print("Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


def setup_facebook_session():
    """Setup Facebook session for automation."""
    print("=" * 70)
    print("🔧 FACEBOOK SESSION SETUP")
    print("=" * 70)
    print()
    print("This script will:")
    print("  1. Open Facebook in a browser")
    print("  2. Let you log in manually")
    print("  3. Save your session for automation")
    print()
    print("=" * 70)
    print()

    # Session path
    session_path = VAULT_PATH / "gold" / "config" / "facebook_session"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📁 Session will be saved to: {session_path}")
    print()

    input("Press Enter to open Facebook in browser...")
    print()

    with sync_playwright() as p:
        # Launch browser with persistent context
        print("🌐 Opening browser...")
        browser = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.new_page()

        # Navigate to Facebook
        print("📱 Navigating to Facebook...")
        page.goto("https://www.facebook.com/", wait_until="load")

        print()
        print("=" * 70)
        print("👤 PLEASE LOG IN TO FACEBOOK")
        print("=" * 70)
        print()
        print("Instructions:")
        print("  1. Log in to your Facebook account in the browser")
        print("  2. Complete any 2FA/security checks")
        print("  3. Wait until you see your Facebook feed")
        print("  4. Come back here and press Enter")
        print()
        print("⚠️  DO NOT close the browser window!")
        print()
        print("=" * 70)
        print()

        input("Press Enter after you've logged in and see your feed...")

        # Verify login
        print()
        print("🔍 Verifying login...")

        current_url = page.url
        if "login" in current_url.lower():
            print("❌ Still on login page. Please complete login and try again.")
            browser.close()
            sys.exit(1)

        print("✅ Login verified!")
        print()

        # Close browser
        browser.close()

        print("=" * 70)
        print("✅ FACEBOOK SESSION SAVED!")
        print("=" * 70)
        print()
        print(f"Session saved to: {session_path}")
        print()
        print("You can now use the Facebook poster:")
        print("  python gold/src/actions/facebook_poster_playwright.py")
        print()
        print("Or test the complete workflow:")
        print("  python gold/scripts/test_social_approval_workflow.py")
        print()


if __name__ == "__main__":
    setup_facebook_session()

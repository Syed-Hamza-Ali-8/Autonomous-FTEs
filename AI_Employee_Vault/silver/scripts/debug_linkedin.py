#!/usr/bin/env python3
"""
Simple LinkedIn session debug script.

This script opens LinkedIn in a visible browser to verify your session is working.
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


def debug_linkedin_session():
    """Debug LinkedIn session by opening browser and checking login status."""

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

    print("=" * 60)
    print("LinkedIn Session Debug Script")
    print("=" * 60)
    print(f"\n📂 Session path: {session_path}")

    # Check if session exists
    if not Path(session_path).exists():
        print("❌ Session directory not found!")
        print("\nRun: python silver/scripts/setup_linkedin.py")
        return False

    print("✅ Session directory exists")
    print("\n⚠️  Opening LinkedIn in visible browser...")
    print("   Browser will stay open for 30 seconds\n")

    input("Press Enter to start...")

    try:
        with sync_playwright() as p:
            print("\n1️⃣  Launching browser...")

            # Launch browser with persistent session - VISIBLE
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # VISIBLE BROWSER
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("2️⃣  Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Wait for page to load
            page.wait_for_timeout(3000)

            # Check if logged in
            print("\n3️⃣  Checking login status...")

            if "login" in page.url.lower() or "authwall" in page.url.lower():
                print("❌ NOT LOGGED IN")
                print(f"   Current URL: {page.url}")
                print("\n   Your session has expired.")
                print("   Run: python silver/scripts/setup_linkedin.py")
                browser.close()
                return False

            print("✅ LOGGED IN")
            print(f"   Current URL: {page.url}")

            # Check for "Start a post" button
            print("\n4️⃣  Checking page elements...")
            start_post_count = page.locator('button:has-text("Start a post")').count()
            print(f"   'Start a post' buttons found: {start_post_count}")

            if start_post_count > 0:
                print("   ✅ Post button is available")
            else:
                print("   ⚠️  Post button not found (page may still be loading)")

            # Take screenshot
            screenshot_path = vault_path / "linkedin_debug.png"
            page.screenshot(path=str(screenshot_path))
            print(f"\n📸 Screenshot saved: {screenshot_path}")

            # Keep browser open
            print("\n5️⃣  Browser will stay open for 30 seconds...")
            print("   (You can manually check your LinkedIn profile)")
            page.wait_for_timeout(30000)

            browser.close()

            print("\n" + "=" * 60)
            print("✅ Session debug completed!")
            print("=" * 60)
            print("\nYour LinkedIn session is working correctly.")
            print("You can now use: python3 silver/scripts/debug_linkedin_post.py")

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
    print("\n🐛 LinkedIn Session Debug Script")
    print("   This script checks if your LinkedIn session is working\n")

    success = debug_linkedin_session()

    if not success:
        print("\n❌ Session debug failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

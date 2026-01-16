#!/usr/bin/env python3
"""
LinkedIn setup script for browser session authentication.

This script opens a browser window for you to login to LinkedIn manually.
The session is saved and will be reused by the LinkedIn poster.
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger


def setup_linkedin_session(vault_path: str):
    """
    Setup LinkedIn session by opening browser for manual login.

    Args:
        vault_path: Path to the Obsidian vault root
    """
    logger = get_logger("linkedin_setup")

    # Session storage path
    session_path = Path(vault_path) / "silver" / "config" / "linkedin_session"
    session_path.mkdir(parents=True, exist_ok=True)

    logger.info("Starting LinkedIn session setup...")
    print("\n" + "=" * 60)
    print("LinkedIn Session Setup")
    print("=" * 60)
    print("\nThis will open a browser window for you to login to LinkedIn.")
    print("After logging in successfully, close the browser window.")
    print("\nIMPORTANT:")
    print("- Use your fake/test LinkedIn profile")
    print("- Complete any security checks if prompted")
    print("- Stay logged in (don't logout)")
    print("=" * 60 + "\n")

    input("Press Enter to open browser...")

    try:
        with sync_playwright() as p:
            # Launch browser with persistent context (saves session)
            print("\n🌐 Opening browser...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,  # Show browser for manual login
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("📱 Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/login", wait_until="networkidle")

            print("\n✅ Browser opened!")
            print("\nPlease:")
            print("1. Login to your LinkedIn account")
            print("2. Complete any security verification")
            print("3. Wait until you see your LinkedIn feed")
            print("4. Close this browser window when done")
            print("\n⏳ Waiting for you to login and close the browser...")

            # Wait for user to close browser
            try:
                page.wait_for_timeout(300000)  # Wait up to 5 minutes
            except Exception:
                pass

            browser.close()

        # Verify session was saved
        if (session_path / "Default").exists():
            print("\n✅ LinkedIn session saved successfully!")
            print(f"📁 Session location: {session_path}")

            # Update .env file
            env_path = Path(vault_path) / "silver" / "config" / ".env"
            env_content = ""

            if env_path.exists():
                env_content = env_path.read_text()

            # Add or update LinkedIn session path
            if "LINKEDIN_SESSION_PATH" not in env_content:
                env_content += f"\n# LinkedIn\nLINKEDIN_SESSION_PATH={session_path}\n"
                env_path.write_text(env_content)
                print("✅ Updated .env file")

            print("\n" + "=" * 60)
            print("Setup Complete!")
            print("=" * 60)
            print("\nYou can now use the LinkedIn poster:")
            print("  python silver/src/watchers/linkedin_poster.py")
            print("\nOr test posting:")
            print("  python silver/scripts/test_linkedin.py")
            print("=" * 60 + "\n")

            return True
        else:
            print("\n❌ Session not saved properly.")
            print("Please try again and make sure to login successfully.")
            return False

    except Exception as e:
        logger.error(f"Error during setup: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Playwright is installed:")
        print("   playwright install chromium")
        print("2. Check your internet connection")
        print("3. Try running the script again")
        return False


def main():
    """Main entry point."""
    # Get vault path
    vault_path = Path(__file__).parent.parent.parent.absolute()

    print(f"Vault path: {vault_path}")

    success = setup_linkedin_session(str(vault_path))

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Inspect LinkedIn Post buttons to identify the correct one.

This script will show detailed information about all Post buttons on the page.
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


def inspect_post_buttons():
    """Inspect all Post buttons on LinkedIn to identify the correct one."""

    logger = get_logger("inspect_linkedin")

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

    content = "Test post for debugging"

    print("=" * 60)
    print("LinkedIn Post Button Inspector")
    print("=" * 60)
    print("\nThis script will show you all Post buttons and their attributes\n")

    input("Press Enter to start...")

    try:
        with sync_playwright() as p:
            print("\n1️⃣  Launching browser...")

            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("2️⃣  Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
            page.wait_for_timeout(3000)

            # Click "Start a post"
            print("3️⃣  Clicking 'Start a post'...")
            page.click('button:has-text("Start a post")', timeout=15000)
            page.wait_for_selector('[role="textbox"]', timeout=10000)

            # Fill content
            print("4️⃣  Filling content...")
            editor = page.locator('[role="textbox"]').first
            editor.click()
            editor.fill(content)
            page.wait_for_timeout(2000)

            # Inspect all Post buttons
            print("\n5️⃣  Inspecting all Post buttons...")
            print("=" * 60)

            # Get all buttons with text "Post"
            all_post_buttons = page.locator('button:has-text("Post")')
            count = all_post_buttons.count()
            print(f"\nFound {count} button(s) with text 'Post'\n")

            for i in range(count):
                button = all_post_buttons.nth(i)
                print(f"Button #{i + 1}:")
                print("-" * 40)

                # Get attributes
                try:
                    # Check if inside dialog
                    is_in_dialog = page.locator('[role="dialog"]').locator(f'button:has-text("Post")').nth(i).count() > 0
                    print(f"  Inside dialog: {is_in_dialog}")
                except:
                    print(f"  Inside dialog: Unknown")

                # Get class
                try:
                    class_attr = button.get_attribute('class')
                    print(f"  Class: {class_attr}")
                except:
                    print(f"  Class: None")

                # Get aria-label
                try:
                    aria_label = button.get_attribute('aria-label')
                    print(f"  Aria-label: {aria_label}")
                except:
                    print(f"  Aria-label: None")

                # Get data attributes
                try:
                    data_control = button.get_attribute('data-control-name')
                    if data_control:
                        print(f"  Data-control-name: {data_control}")
                except:
                    pass

                # Check if disabled
                try:
                    is_disabled = button.is_disabled()
                    print(f"  Disabled: {is_disabled}")
                except:
                    print(f"  Disabled: Unknown")

                # Check if visible
                try:
                    is_visible = button.is_visible()
                    print(f"  Visible: {is_visible}")
                except:
                    print(f"  Visible: Unknown")

                # Get text content
                try:
                    text = button.text_content()
                    print(f"  Text: '{text}'")
                except:
                    print(f"  Text: Unknown")

                print()

            # Now check buttons inside dialog specifically
            print("\n" + "=" * 60)
            print("Buttons inside [role=\"dialog\"]:")
            print("=" * 60)

            dialog_buttons = page.locator('[role="dialog"] button:has-text("Post")')
            dialog_count = dialog_buttons.count()
            print(f"\nFound {dialog_count} button(s) inside dialog\n")

            for i in range(dialog_count):
                button = dialog_buttons.nth(i)
                print(f"Dialog Button #{i + 1}:")
                print("-" * 40)

                # Get all attributes
                try:
                    class_attr = button.get_attribute('class')
                    print(f"  Class: {class_attr}")
                except:
                    pass

                try:
                    aria_label = button.get_attribute('aria-label')
                    print(f"  Aria-label: {aria_label}")
                except:
                    pass

                try:
                    data_control = button.get_attribute('data-control-name')
                    if data_control:
                        print(f"  Data-control-name: {data_control}")
                except:
                    pass

                try:
                    is_disabled = button.is_disabled()
                    print(f"  Disabled: {is_disabled}")
                except:
                    pass

                try:
                    text = button.text_content()
                    print(f"  Text: '{text}'")
                except:
                    pass

                print()

            print("\n" + "=" * 60)
            print("Inspection complete!")
            print("=" * 60)
            print("\nBrowser will stay open for 60 seconds...")
            print("You can manually inspect the buttons in the browser.\n")

            page.wait_for_timeout(60000)

            browser.close()

            return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Inspection failed: {e}")
        return False


def main():
    """Main entry point."""
    print("\n🔍 LinkedIn Post Button Inspector")
    print("   This will show you details about all Post buttons\n")

    success = inspect_post_buttons()

    if not success:
        print("\n❌ Inspection failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

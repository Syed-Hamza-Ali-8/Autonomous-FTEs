#!/usr/bin/env python3
"""
LinkedIn Post Button Fixer
This script will help identify and fix the Post button issue
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

VAULT_PATH = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
SESSION_PATH = f"{VAULT_PATH}/silver/config/linkedin_session"

def test_post_button():
    """Test different Post button selectors to find the working one."""

    print("=" * 60)
    print("LinkedIn Post Button Diagnostic")
    print("=" * 60)
    print()

    test_content = "Test post from automation script - please ignore"

    with sync_playwright() as p:
        print("1️⃣  Launching browser (VISIBLE)...")
        browser = p.chromium.launch_persistent_context(
            SESSION_PATH,
            headless=False,  # Visible browser
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.new_page()

        print("2️⃣  Navigating to LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

        if "login" in page.url.lower():
            print("❌ Not logged in! Run: python silver/scripts/setup_linkedin.py")
            browser.close()
            return

        print("   ✅ Logged in")
        print()

        print("3️⃣  Clicking 'Start a post'...")
        page.wait_for_timeout(2000)
        page.click('button:has-text("Start a post")', timeout=15000)
        print("   ✅ Clicked")
        print()

        print("4️⃣  Waiting for editor...")
        page.wait_for_selector('[role="textbox"]', timeout=10000)
        print("   ✅ Editor appeared")
        print()

        print("5️⃣  Filling content...")
        editor = page.locator('[role="textbox"]').first
        editor.click()
        editor.fill(test_content)
        page.wait_for_timeout(1000)
        print("   ✅ Content filled")
        print()

        print("6️⃣  Analyzing Post buttons...")
        print()

        # Test different selectors
        selectors = [
            ('button:has-text("Post"):not([aria-label])', 'Text-based without aria-label'),
            ('[role="dialog"] button:has-text("Post")', 'Dialog Post button'),
            ('button[type="submit"]:has-text("Post")', 'Submit button with Post text'),
            ('.share-actions button:has-text("Post")', 'Share actions Post button'),
            ('button.share-actions__primary-action', 'Primary action button'),
            ('button[data-test-modal-close-btn]', 'Modal close button'),
        ]

        working_selector = None

        for selector, description in selectors:
            try:
                count = page.locator(selector).count()
                print(f"   Selector: {selector}")
                print(f"   Description: {description}")
                print(f"   Count: {count}")

                if count > 0:
                    # Check if button is enabled
                    is_disabled = page.locator(selector).first.is_disabled()
                    print(f"   Disabled: {is_disabled}")

                    if not is_disabled:
                        print(f"   ✅ This selector looks good!")
                        if working_selector is None:
                            working_selector = selector
                else:
                    print(f"   ❌ Not found")

                print()

            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

        if working_selector:
            print("=" * 60)
            print(f"✅ Found working selector: {working_selector}")
            print("=" * 60)
            print()

            response = input("Do you want to test clicking this button? (yes/no): ")

            if response.lower() == 'yes':
                print()
                print("7️⃣  Clicking Post button...")
                try:
                    page.locator(working_selector).first.click(timeout=5000)
                    print("   ✅ Clicked!")
                    print()

                    print("8️⃣  Waiting 5 seconds...")
                    page.wait_for_timeout(5000)

                    # Check if modal closed
                    modal_count = page.locator('[role="dialog"]').count()
                    print(f"   Modal count after click: {modal_count}")

                    if modal_count == 0:
                        print("   ✅ Modal closed - post likely submitted!")
                        print()
                        print("🎉 SUCCESS! Check your LinkedIn profile.")
                        print()
                        print(f"Working selector: {working_selector}")
                    else:
                        print("   ⚠️  Modal still open - post may not have submitted")
                        print()
                        print("   Keeping browser open for inspection...")
                        input("   Press Enter to close browser...")

                except Exception as e:
                    print(f"   ❌ Error clicking: {e}")
            else:
                print("Skipping click test.")
        else:
            print("❌ No working selector found!")
            print()
            print("Keeping browser open for manual inspection...")
            input("Press Enter to close browser...")

        browser.close()

if __name__ == "__main__":
    test_post_button()

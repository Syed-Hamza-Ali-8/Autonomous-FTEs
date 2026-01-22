#!/usr/bin/env python3
"""
Comprehensive WhatsApp contact debug - tries multiple selectors and captures screenshots
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Contact Debug - Comprehensive")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"
screenshot_dir = vault_path / "silver" / "debug_screenshots"
screenshot_dir.mkdir(exist_ok=True)

try:
    with sync_playwright() as p:
        print("1. Opening browser...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("2. Going to WhatsApp Web...")
        page.goto('https://web.whatsapp.com', timeout=120000)

        print("3. Waiting for WhatsApp to load (this takes ~150 seconds)...")

        # Wait patiently for chat list
        max_wait = 180  # 3 minutes
        check_interval = 30
        elapsed = 0

        while elapsed < max_wait:
            chat_list = page.locator('div[aria-label="Chat list"]')
            if chat_list.is_visible(timeout=2000):
                print(f"   ✅ Loaded after {elapsed} seconds!")
                break

            progress_bar = page.locator('progress')
            if progress_bar.is_visible(timeout=2000):
                try:
                    value = progress_bar.get_attribute('value')
                    max_val = progress_bar.get_attribute('max')
                    percentage = int((int(value) / int(max_val)) * 100)
                    print(f"   [{elapsed}s] Loading... {percentage}%")
                except:
                    print(f"   [{elapsed}s] Loading...")

            time.sleep(check_interval)
            elapsed += check_interval

        print()
        print("4. Waiting 10 more seconds for chats to populate...")
        time.sleep(10)

        print("5. Taking screenshot...")
        page.screenshot(path=str(screenshot_dir / "contacts_loaded.png"), full_page=True)
        print(f"   Saved: {screenshot_dir / 'contacts_loaded.png'}")

        print()
        print("6. Trying multiple selectors to find contacts...")
        print()

        selectors = [
            ('div[role="listitem"]', 'List items'),
            ('div[data-testid="cell-frame-container"]', 'Cell frame containers'),
            ('div[data-testid="chat-list-item"]', 'Chat list items'),
            ('span[title]', 'Elements with title attribute'),
            ('div[aria-label="Chat list"] > div > div', 'Direct children of chat list'),
            ('div._ak8l', 'WhatsApp chat item class'),
            ('div[class*="chat"]', 'Elements with "chat" in class'),
        ]

        for selector, description in selectors:
            try:
                elements = page.locator(selector).all()
                print(f"   {description}: {len(elements)} found")

                if len(elements) > 0 and len(elements) < 50:
                    # Try to get text from first few elements
                    for i, elem in enumerate(elements[:5], 1):
                        try:
                            text = elem.inner_text(timeout=1000)
                            if text and len(text) < 100:
                                print(f"      {i}. {text[:50]}...")
                        except:
                            pass
            except Exception as e:
                print(f"   {description}: Error - {e}")

        print()
        print("7. Checking search box functionality...")

        # Try to click search box and type
        try:
            search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
            if search_box.is_visible(timeout=5000):
                print("   ✅ Search box found and visible")

                # Click and type a test search
                search_box.click()
                time.sleep(1)
                search_box.fill("test")
                time.sleep(2)

                print("   Taking screenshot of search results...")
                page.screenshot(path=str(screenshot_dir / "search_test.png"))
                print(f"   Saved: {screenshot_dir / 'search_test.png'}")

                # Clear search
                search_box.fill("")
                time.sleep(1)
            else:
                print("   ❌ Search box not visible")
        except Exception as e:
            print(f"   ❌ Search box error: {e}")

        print()
        print("8. Getting HTML of chat list area...")
        try:
            chat_list = page.locator('div[aria-label="Chat list"]')
            if chat_list.is_visible(timeout=2000):
                html = chat_list.inner_html()
                html_file = screenshot_dir / "chat_list.html"
                html_file.write_text(html)
                print(f"   Saved HTML to: {html_file}")
                print(f"   HTML length: {len(html)} characters")
        except Exception as e:
            print(f"   ❌ Error getting HTML: {e}")

        print()
        print("9. Keeping browser open for 30 seconds for manual inspection...")
        print("   Please check if you can see any contacts in the browser window.")
        print("   If you see contacts, note their exact names.")
        time.sleep(30)

        browser.close()

        print()
        print("=" * 70)
        print("✅ Debug complete!")
        print(f"   Screenshots: {screenshot_dir}")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

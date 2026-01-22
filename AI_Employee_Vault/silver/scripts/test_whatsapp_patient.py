#!/usr/bin/env python3
"""
Patient WhatsApp test - waits as long as needed for WhatsApp to load
Monitors loading progress and reports status every 30 seconds
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Message Test - Patient Version")
print("Will wait up to 15 minutes for WhatsApp to load")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"

recipient = "Mr Honey"
message = "🧪 Test from AI Employee - WhatsApp working after patient wait!"

print(f"Recipient: {recipient}")
print(f"Message: {message}")
print()

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

        print("3. Waiting patiently for WhatsApp to load...")
        print("   Checking every 30 seconds for up to 15 minutes...")
        print()

        max_wait_time = 900  # 15 minutes
        check_interval = 30  # Check every 30 seconds
        elapsed = 0

        chat_list_loaded = False

        while elapsed < max_wait_time:
            # Check for QR code (not logged in)
            qr_code = page.locator('canvas[aria-label="Scan me!"]')
            if qr_code.is_visible(timeout=2000):
                print("❌ QR CODE FOUND - Session not authenticated!")
                print("   Run: python silver/scripts/setup_whatsapp.py")
                browser.close()
                sys.exit(1)

            # Check for chat list (fully loaded)
            chat_list = page.locator('div[aria-label="Chat list"]')
            if chat_list.is_visible(timeout=2000):
                print(f"✅ Chat list loaded after {elapsed} seconds!")
                chat_list_loaded = True
                break

            # Check loading progress
            progress_bar = page.locator('progress')
            if progress_bar.is_visible(timeout=2000):
                try:
                    value = progress_bar.get_attribute('value')
                    max_val = progress_bar.get_attribute('max')
                    percentage = int((int(value) / int(max_val)) * 100)
                    print(f"   [{elapsed}s] Still loading... {percentage}%")
                except:
                    print(f"   [{elapsed}s] Still loading... (progress unknown)")
            else:
                # No progress bar visible - check for search box
                search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                if search_box.is_visible(timeout=2000):
                    print(f"✅ Search box appeared after {elapsed} seconds!")
                    chat_list_loaded = True
                    break
                else:
                    print(f"   [{elapsed}s] Waiting... (no progress bar visible)")

            # Wait before next check
            time.sleep(check_interval)
            elapsed += check_interval

        if not chat_list_loaded:
            print()
            print(f"❌ WhatsApp did not load after {max_wait_time} seconds (15 minutes)")
            print("   This suggests the session is corrupted or stuck.")
            print("   Recommendation: Reset session with reset_whatsapp_session.py")
            browser.close()
            sys.exit(1)

        print()
        print("4. Searching for contact...")

        try:
            # Click search box
            search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
            search_box.click()
            time.sleep(0.5)

            # Type contact name
            search_box.fill(recipient)
            time.sleep(2)

            print(f"5. Looking for '{recipient}'...")

            # Click on the contact
            contact = page.locator(f'span[title="{recipient}"]').first
            if not contact.is_visible(timeout=10000):
                print(f"❌ Contact '{recipient}' not found in search results")
                print("   Make sure the contact name matches exactly as it appears in WhatsApp")
                browser.close()
                sys.exit(1)

            contact.click()
            time.sleep(1)

            print("6. Sending message...")

            # Find message box and send
            message_box = page.locator('div[contenteditable="true"][data-tab="10"]').first
            message_box.click()
            time.sleep(0.5)
            message_box.fill(message)
            time.sleep(0.5)
            message_box.press('Enter')

            print()
            print("✅ Message sent successfully!")
            print()
            print("Check your WhatsApp to verify!")

            # Keep browser open to see result
            print("Keeping browser open for 10 seconds...")
            time.sleep(10)

            browser.close()

            print()
            print("=" * 70)
            print("✅ WhatsApp test PASSED!")
            print(f"   Total wait time: {elapsed} seconds")
            print("=" * 70)

        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            print("Browser will stay open for 30 seconds so you can see what happened...")
            time.sleep(30)
            browser.close()
            sys.exit(1)

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
Flexible WhatsApp test - accepts recipient and message as arguments
Usage:
  python scripts/test_whatsapp_flexible.py "Mr Honey 😎" "Hello from AI!"
  python scripts/test_whatsapp_flexible.py  # Uses defaults
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Message Test - Flexible Version")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"

# Accept command-line arguments or use defaults
if len(sys.argv) >= 3:
    recipient = sys.argv[1]
    message = sys.argv[2]
    print("Using provided arguments:")
elif len(sys.argv) == 2:
    recipient = sys.argv[1]
    message = "🧪 Test message from AI Employee"
    print("Using provided recipient with default message:")
else:
    recipient = "Mr Honey 😎"
    message = "🧪 Test from AI Employee - WhatsApp working!"
    print("Using default values:")

print(f"  Recipient: {recipient}")
print(f"  Message: {message}")
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

        print("3. Waiting for WhatsApp to load (smart wait for chat list)...")
        try:
            page.wait_for_selector('div[aria-label="Chat list"]', timeout=180000)
            print("   ✅ Chat list loaded!")
        except Exception as e:
            print(f"   ⚠️ Chat list timeout: {e}")
            print("   Trying alternative approach...")
            page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=60000)
            print("   ✅ Search box found!")

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
                print("   Available contacts:")
                print("   Run: python scripts/list_whatsapp_contacts_v2.py")
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
            print("Keeping browser open for 30 seconds...")
            time.sleep(30)

            browser.close()

            print()
            print("=" * 70)
            print("✅ WhatsApp test PASSED!")
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

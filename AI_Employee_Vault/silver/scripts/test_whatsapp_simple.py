#!/usr/bin/env python3
"""
Simple WhatsApp test that actually works
Uses longer timeout and simpler logic
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set to visible browser and longer timeout
os.environ['WHATSAPP_HEADLESS'] = 'false'
os.environ['WHATSAPP_TIMEOUT'] = '90000'  # 90 seconds

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Message Test - Simple Version")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"

recipient = "Mr Honey"
message = "🧪 Test from AI Employee - WhatsApp working!"

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
        page.goto('https://web.whatsapp.com', timeout=90000)

        print("3. Waiting for WhatsApp to load (30 seconds)...")
        time.sleep(30)  # Just wait, don't check for specific elements

        print("4. Searching for contact...")

        # Use the exact same approach as whatsapp_sender.py
        try:
            # Click search box using the exact selector from whatsapp_sender.py
            search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
            search_box.click()
            time.sleep(1)

            # Type contact name
            search_box.fill(recipient)
            time.sleep(3)  # Wait longer for search results

            print(f"5. Looking for '{recipient}'...")

            # Click on the contact - wait longer
            contact = page.locator(f'span[title="{recipient}"]').first
            if not contact.is_visible(timeout=10000):
                print(f"❌ Contact '{recipient}' not found in search results")
                print("   Make sure the contact name matches exactly as it appears in WhatsApp")
                raise ValueError(f"Contact not found: {recipient}")

            contact.click()
            time.sleep(2)

            print("6. Sending message...")

            # Find message box and send
            message_box = page.locator('div[contenteditable="true"][data-tab="10"]').first
            message_box.click()
            time.sleep(1)
            message_box.fill(message)
            time.sleep(1)
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

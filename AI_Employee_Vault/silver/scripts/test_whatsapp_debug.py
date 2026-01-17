#!/usr/bin/env python3
"""
WhatsApp Debug Test - Takes screenshots to see what's happening
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set to visible browser and longer timeout
os.environ['WHATSAPP_HEADLESS'] = 'false'
os.environ['WHATSAPP_TIMEOUT'] = '90000'

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Debug Test - With Screenshots")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"
screenshots_path = vault_path / "silver" / "debug_screenshots"
screenshots_path.mkdir(exist_ok=True)

recipient = "Mr Honey 😎"
message = "🧪 Test from AI Employee - WhatsApp working!"

print(f"Recipient: {recipient}")
print(f"Message: {message}")
print(f"Screenshots will be saved to: {screenshots_path}")
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
        time.sleep(30)

        # Take screenshot after load
        screenshot1 = screenshots_path / "01_after_load.png"
        page.screenshot(path=str(screenshot1))
        print(f"   📸 Screenshot saved: {screenshot1}")

        print("4. Looking for search box...")

        # Try to find and click search box
        try:
            search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
            search_box.click()
            time.sleep(1)
            print("   ✅ Search box found and clicked")

            # Take screenshot after clicking search
            screenshot2 = screenshots_path / "02_search_clicked.png"
            page.screenshot(path=str(screenshot2))
            print(f"   📸 Screenshot saved: {screenshot2}")

        except Exception as e:
            print(f"   ❌ Could not click search box: {e}")
            screenshot_error = screenshots_path / "error_search_box.png"
            page.screenshot(path=str(screenshot_error))
            print(f"   📸 Error screenshot saved: {screenshot_error}")
            raise

        print(f"5. Typing '{recipient}' in search...")
        search_box.fill(recipient)
        time.sleep(3)

        # Take screenshot after typing
        screenshot3 = screenshots_path / "03_after_typing.png"
        page.screenshot(path=str(screenshot3))
        print(f"   📸 Screenshot saved: {screenshot3}")

        print("6. Looking for contact in results...")

        # Try to find all spans with title attribute
        all_titles = page.locator('span[title]').all()
        print(f"   Found {len(all_titles)} elements with title attribute:")
        for i, elem in enumerate(all_titles[:10]):  # Show first 10
            try:
                title = elem.get_attribute('title')
                print(f"     - {title}")
            except:
                pass

        # Try exact match
        contact = page.locator(f'span[title="{recipient}"]').first

        if contact.is_visible(timeout=5000):
            print(f"   ✅ Found contact: {recipient}")
            contact.click()
            time.sleep(2)

            # Take screenshot after clicking contact
            screenshot4 = screenshots_path / "04_contact_clicked.png"
            page.screenshot(path=str(screenshot4))
            print(f"   📸 Screenshot saved: {screenshot4}")

            print("7. Sending message...")

            # Find message box
            message_box = page.locator('div[contenteditable="true"][data-tab="10"]').first
            message_box.click()
            time.sleep(1)
            message_box.fill(message)
            time.sleep(1)
            message_box.press('Enter')

            time.sleep(2)

            # Take screenshot after sending
            screenshot5 = screenshots_path / "05_message_sent.png"
            page.screenshot(path=str(screenshot5))
            print(f"   📸 Screenshot saved: {screenshot5}")

            print()
            print("✅ Message sent successfully!")
            print()
            print("Check your WhatsApp to verify!")

            time.sleep(5)
            browser.close()

            print()
            print("=" * 70)
            print("✅ WhatsApp test PASSED!")
            print("=" * 70)

        else:
            print(f"   ❌ Contact '{recipient}' not visible")

            # Take screenshot of failed search
            screenshot_fail = screenshots_path / "error_contact_not_found.png"
            page.screenshot(path=str(screenshot_fail))
            print(f"   📸 Screenshot saved: {screenshot_fail}")

            print()
            print("   Keeping browser open for 30 seconds so you can inspect...")
            time.sleep(30)
            browser.close()
            sys.exit(1)

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

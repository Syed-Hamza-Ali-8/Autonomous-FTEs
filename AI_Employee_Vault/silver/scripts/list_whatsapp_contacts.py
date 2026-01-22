#!/usr/bin/env python3
"""
List all WhatsApp contacts to find the correct name
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Contact Lister")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"

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
        print("4. Getting list of contacts...")
        print()

        # Get all chat items
        chat_items = page.locator('div[role="listitem"]').all()

        print(f"Found {len(chat_items)} chats:")
        print("-" * 70)

        contacts = []
        for i, item in enumerate(chat_items[:20], 1):  # Show first 20
            try:
                # Try to get the contact name from the title attribute
                title_elem = item.locator('span[title]').first
                if title_elem.is_visible(timeout=1000):
                    name = title_elem.get_attribute('title')
                    if name:
                        contacts.append(name)
                        print(f"{i}. {name}")
            except:
                continue

        print("-" * 70)
        print(f"\nTotal contacts shown: {len(contacts)}")
        print()
        print("Use one of these exact names in your test script.")
        print()

        # Keep browser open for inspection
        print("Keeping browser open for 20 seconds for manual inspection...")
        time.sleep(20)

        browser.close()

        print()
        print("=" * 70)
        print("✅ Contact list retrieved!")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

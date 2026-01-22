#!/usr/bin/env python3
"""
List WhatsApp contacts using the correct selectors
Based on debug findings: div._ak8l (67 items) and span[title] (134 items)
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Contact Lister - Using Correct Selectors")
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

        print("3. Waiting for WhatsApp to load...")

        # Wait for chat list with progress monitoring
        max_wait = 180
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

        print("4. Waiting 10 seconds for chats to populate...")
        time.sleep(10)

        print()
        print("5. Getting contacts using working selectors...")
        print()

        # Method 1: Use the chat item class that worked (._ak8l)
        print("Method 1: Using div._ak8l selector (found 67 items in debug)")
        chat_items = page.locator('div._ak8l').all()
        print(f"   Found {len(chat_items)} chat items")

        contacts = []
        for i, item in enumerate(chat_items[:20], 1):  # Show first 20
            try:
                # Try to find span with title inside this chat item
                title_elem = item.locator('span[title]').first
                name = title_elem.get_attribute('title', timeout=1000)
                if name:
                    contacts.append(name)
                    print(f"   {i}. {name}")
            except:
                # Try to get any text from the item
                try:
                    text = item.inner_text(timeout=1000)
                    if text:
                        # Take first line as contact name
                        first_line = text.split('\n')[0]
                        if first_line and len(first_line) < 50:
                            contacts.append(first_line)
                            print(f"   {i}. {first_line}")
                except:
                    pass

        print()
        print("Method 2: Using span[title] selector (found 134 items in debug)")
        title_elements = page.locator('span[title]').all()
        print(f"   Found {len(title_elements)} title elements")

        # Get unique contact names from title elements
        all_titles = []
        for elem in title_elements[:50]:  # Check first 50
            try:
                title = elem.get_attribute('title', timeout=500)
                if title and len(title) > 0 and len(title) < 100:
                    all_titles.append(title)
            except:
                pass

        # Remove duplicates and filter out non-contact titles
        unique_titles = []
        seen = set()
        for title in all_titles:
            if title not in seen and not any(x in title.lower() for x in ['search', 'menu', 'new chat', 'status']):
                seen.add(title)
                unique_titles.append(title)

        print(f"   Unique contact names found: {len(unique_titles)}")
        for i, name in enumerate(unique_titles[:20], 1):
            print(f"   {i}. {name}")

        print()
        print("-" * 70)
        print(f"Total contacts from Method 1: {len(contacts)}")
        print(f"Total contacts from Method 2: {len(unique_titles)}")
        print("-" * 70)
        print()

        if len(contacts) > 0:
            print("✅ Use one of these exact names in your test script:")
            print(f"   Example: recipient = \"{contacts[0]}\"")
        elif len(unique_titles) > 0:
            print("✅ Use one of these exact names in your test script:")
            print(f"   Example: recipient = \"{unique_titles[0]}\"")
        else:
            print("⚠️  No contacts found. Please check the browser window manually.")

        print()
        print("Keeping browser open for 30 seconds for manual inspection...")
        time.sleep(30)

        browser.close()

        print()
        print("=" * 70)
        print("✅ Contact list complete!")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

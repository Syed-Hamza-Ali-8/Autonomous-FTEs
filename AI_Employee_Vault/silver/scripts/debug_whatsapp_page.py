#!/usr/bin/env python3
"""
Debug script to see what's actually on WhatsApp Web page
Takes screenshots and checks for various elements
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Web Debug - Checking Page State")
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
        page.goto('https://web.whatsapp.com', timeout=90000)

        print("3. Taking initial screenshot...")
        page.screenshot(path=str(screenshot_dir / "01_initial_load.png"))
        print(f"   Saved: {screenshot_dir / '01_initial_load.png'}")

        print("4. Waiting 30 seconds for page to load...")
        time.sleep(30)

        print("5. Taking screenshot after 30 seconds...")
        page.screenshot(path=str(screenshot_dir / "02_after_30sec.png"))
        print(f"   Saved: {screenshot_dir / '02_after_30sec.png'}")

        print("6. Checking for various elements...")

        # Check for QR code (not logged in)
        qr_code = page.locator('canvas[aria-label="Scan this QR code to link a device!"]')
        if qr_code.is_visible(timeout=2000):
            print("   ❌ QR CODE FOUND - Session not authenticated!")
            print("   You need to scan the QR code to log in")
            page.screenshot(path=str(screenshot_dir / "03_qr_code.png"))
        else:
            print("   ✅ No QR code - Session appears authenticated")

        # Check for chat list (logged in)
        chat_list = page.locator('div[aria-label="Chat list"]')
        if chat_list.is_visible(timeout=2000):
            print("   ✅ Chat list found - WhatsApp is loaded")
        else:
            print("   ❌ Chat list not found")

        # Check for search box
        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        if search_box.is_visible(timeout=2000):
            print("   ✅ Search box found - Ready to search")
        else:
            print("   ❌ Search box not found")

        # Check for alternative search box selector
        alt_search = page.locator('div[title="Search input textbox"]')
        if alt_search.is_visible(timeout=2000):
            print("   ✅ Alternative search box found")
        else:
            print("   ❌ Alternative search box not found")

        print("\n7. Waiting 30 more seconds...")
        time.sleep(30)

        print("8. Taking final screenshot...")
        page.screenshot(path=str(screenshot_dir / "04_after_60sec.png"))
        print(f"   Saved: {screenshot_dir / '04_after_60sec.png'}")

        # Check again after more waiting
        print("\n9. Checking elements again after 60 seconds total...")

        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        if search_box.is_visible(timeout=2000):
            print("   ✅ Search box NOW visible!")
        else:
            print("   ❌ Search box still not visible")

        print("\n10. Getting page title and URL...")
        print(f"   Title: {page.title()}")
        print(f"   URL: {page.url}")

        print("\n11. Keeping browser open for 20 seconds so you can inspect...")
        print("   Check the screenshots in: silver/debug_screenshots/")
        time.sleep(20)

        browser.close()

        print()
        print("=" * 70)
        print("✅ Debug complete - Check screenshots!")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

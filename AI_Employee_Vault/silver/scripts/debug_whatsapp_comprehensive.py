#!/usr/bin/env python3
"""
Comprehensive WhatsApp debug - captures everything about the page state
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright
import time

print("=" * 70)
print("WhatsApp Web Comprehensive Debug")
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

        print("3. Taking initial screenshot...")
        page.screenshot(path=str(screenshot_dir / "debug_01_initial.png"))

        print("4. Waiting 30 seconds...")
        time.sleep(30)

        print("5. Taking screenshot after 30s...")
        page.screenshot(path=str(screenshot_dir / "debug_02_after_30s.png"))

        print("6. Getting page info...")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        print("\n7. Checking for various selectors...")

        # Check for QR code
        selectors_to_check = [
            ('QR Code (not logged in)', 'canvas[aria-label="Scan me!"]'),
            ('QR Code (alt)', 'canvas[aria-label="Scan this QR code to link a device!"]'),
            ('Chat list', 'div[aria-label="Chat list"]'),
            ('Search box (data-tab=3)', 'div[contenteditable="true"][data-tab="3"]'),
            ('Search box (alt)', 'div[title="Search input textbox"]'),
            ('Main panel', 'div[id="main"]'),
            ('Side panel', 'div[id="side"]'),
            ('App wrapper', 'div[id="app"]'),
            ('Loading spinner', 'div[data-icon="spinner"]'),
            ('Progress bar', 'progress'),
        ]

        for name, selector in selectors_to_check:
            try:
                element = page.locator(selector)
                is_visible = element.is_visible(timeout=2000)
                count = element.count()
                print(f"   {'✅' if is_visible else '❌'} {name}: visible={is_visible}, count={count}")
            except Exception as e:
                print(f"   ❌ {name}: error checking - {e}")

        print("\n8. Getting page HTML (first 2000 chars)...")
        html = page.content()
        print(f"   HTML length: {len(html)} characters")
        print(f"   First 2000 chars:\n{html[:2000]}")

        print("\n9. Saving full HTML to file...")
        html_file = screenshot_dir / "debug_page.html"
        html_file.write_text(html)
        print(f"   Saved to: {html_file}")

        print("\n10. Checking console logs...")
        # Enable console logging
        page.on("console", lambda msg: print(f"   CONSOLE: {msg.type}: {msg.text}"))

        print("\n11. Waiting another 60 seconds...")
        time.sleep(60)

        print("12. Taking final screenshot...")
        page.screenshot(path=str(screenshot_dir / "debug_03_after_90s.png"))

        print("\n13. Re-checking selectors after 90s total...")
        for name, selector in selectors_to_check[:5]:  # Check main ones again
            try:
                element = page.locator(selector)
                is_visible = element.is_visible(timeout=2000)
                print(f"   {'✅' if is_visible else '❌'} {name}: {is_visible}")
            except:
                print(f"   ❌ {name}: still not found")

        print("\n14. Keeping browser open for 20 seconds for manual inspection...")
        time.sleep(20)

        browser.close()

        print()
        print("=" * 70)
        print("✅ Debug complete!")
        print(f"   Screenshots: {screenshot_dir}")
        print(f"   HTML: {html_file}")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python3
"""
LinkedIn DOM Inspector - Find all available elements
This script inspects the LinkedIn feed to identify the correct selectors.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def inspect_linkedin_dom():
    """Inspect LinkedIn DOM to find posting elements."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"

    print("=" * 70)
    print("LinkedIn DOM Inspector")
    print("=" * 70)

    with sync_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        try:
            page = browser.pages[0] if browser.pages else browser.new_page()

            print("\n📍 Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=30000)
            time.sleep(5)  # Extra wait for dynamic content

            print(f"✓ URL: {page.url}")

            # Check login
            if "login" in page.url or "authwall" in page.url:
                print("❌ Not logged in")
                return False

            print("✓ Logged in successfully")

            # Inspect all buttons
            print("\n" + "=" * 70)
            print("🔍 INSPECTING ALL BUTTONS")
            print("=" * 70)

            buttons = page.locator('button').all()
            print(f"\nFound {len(buttons)} buttons total")

            print("\n📋 Buttons with text containing 'post', 'share', or 'start':")
            print("-" * 70)
            for i, button in enumerate(buttons[:50]):  # First 50 buttons
                try:
                    text = button.text_content().strip()
                    aria_label = button.get_attribute('aria-label') or ""
                    class_name = button.get_attribute('class') or ""

                    if any(keyword in text.lower() or keyword in aria_label.lower()
                           for keyword in ['post', 'share', 'start', 'write']):
                        print(f"\n{i+1}. Text: '{text}'")
                        print(f"   Aria-label: '{aria_label}'")
                        print(f"   Class: '{class_name[:100]}'")
                        print(f"   Visible: {button.is_visible()}")
                        print(f"   Enabled: {not button.is_disabled()}")
                except Exception as e:
                    pass

            # Inspect divs with role="button"
            print("\n" + "=" * 70)
            print("🔍 INSPECTING DIV BUTTONS (role='button')")
            print("=" * 70)

            div_buttons = page.locator('div[role="button"]').all()
            print(f"\nFound {len(div_buttons)} div buttons")

            print("\n📋 Div buttons with relevant text:")
            print("-" * 70)
            for i, div in enumerate(div_buttons[:30]):
                try:
                    text = div.text_content().strip()
                    aria_label = div.get_attribute('aria-label') or ""
                    class_name = div.get_attribute('class') or ""

                    if any(keyword in text.lower() or keyword in aria_label.lower()
                           for keyword in ['post', 'share', 'start', 'write']):
                        print(f"\n{i+1}. Text: '{text[:100]}'")
                        print(f"   Aria-label: '{aria_label}'")
                        print(f"   Class: '{class_name[:100]}'")
                        print(f"   Visible: {div.is_visible()}")
                except Exception as e:
                    pass

            # Look for share box specifically
            print("\n" + "=" * 70)
            print("🔍 LOOKING FOR SHARE BOX ELEMENTS")
            print("=" * 70)

            share_selectors = [
                '.share-box',
                '[class*="share"]',
                '[class*="composer"]',
                '[data-control-name*="share"]',
                'form[class*="share"]',
            ]

            for selector in share_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        print(f"\n✓ Found {len(elements)} elements for: {selector}")
                        for i, elem in enumerate(elements[:3]):
                            try:
                                text = elem.text_content().strip()[:100]
                                class_name = elem.get_attribute('class') or ""
                                print(f"  {i+1}. Text: '{text}'")
                                print(f"     Class: '{class_name[:100]}'")
                            except:
                                pass
                except Exception as e:
                    print(f"✗ Selector failed: {selector} - {e}")

            # Take a screenshot
            screenshot_path = Path(__file__).parent.parent / "linkedin_dom_inspection.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n📸 Full page screenshot: {screenshot_path}")

            # Print page HTML (first 5000 chars)
            print("\n" + "=" * 70)
            print("🔍 PAGE HTML SAMPLE (first 5000 chars)")
            print("=" * 70)
            html = page.content()
            print(html[:5000])

            print("\n⏸️  Browser staying open for 30 seconds for manual inspection...")
            time.sleep(30)

            return True

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n🔒 Closing browser...")
            browser.close()

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LinkedIn DOM Inspector - Finding the correct selectors")
    print("=" * 70)

    inspect_linkedin_dom()

    print("\n" + "=" * 70)
    print("✅ Inspection complete - check output above")
    print("=" * 70)

#!/usr/bin/env python3
"""
LinkedIn UI inspector - extracts all interactive elements to understand the structure.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger


def inspect_linkedin_ui():
    """Inspect LinkedIn UI to find all buttons and interactive elements."""
    logger = get_logger("linkedin_inspector")

    vault_path = Path(__file__).parent.parent.parent.absolute()
    session_path = vault_path / "silver" / "config" / "linkedin_session"

    print("=" * 60)
    print("LinkedIn UI Inspector")
    print("=" * 60)
    print()

    try:
        with sync_playwright() as p:
            print("🌐 Opening browser...")
            browser = p.chromium.launch_persistent_context(
                str(session_path),
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            print("📱 Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Check if logged in
            current_url = page.url
            if "login" in current_url.lower() or "authwall" in current_url.lower():
                print("❌ Not logged in! Session expired.")
                browser.close()
                return

            print("✅ Logged in successfully!")
            print()

            # Wait for page to load
            print("⏳ Waiting for page to load (5 seconds)...")
            page.wait_for_timeout(5000)

            print("🔍 Extracting all buttons and interactive elements...")
            print()

            # Extract all buttons
            buttons_info = page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button, [role="button"], a[role="button"]'));
                    return buttons.slice(0, 50).map((btn, idx) => {
                        return {
                            index: idx,
                            tagName: btn.tagName,
                            text: btn.innerText?.substring(0, 100) || '',
                            ariaLabel: btn.getAttribute('aria-label') || '',
                            className: btn.className || '',
                            id: btn.id || '',
                            role: btn.getAttribute('role') || '',
                            dataTestId: btn.getAttribute('data-test-id') || '',
                            dataControlName: btn.getAttribute('data-control-name') || ''
                        };
                    });
                }
            """)

            print(f"Found {len(buttons_info)} buttons/interactive elements:")
            print()

            # Look for post-related buttons
            post_related = []
            for btn in buttons_info:
                text_lower = btn['text'].lower()
                aria_lower = btn['ariaLabel'].lower()

                if any(keyword in text_lower or keyword in aria_lower
                       for keyword in ['post', 'share', 'start', 'write']):
                    post_related.append(btn)
                    print(f"🎯 POTENTIAL POST BUTTON #{btn['index']}:")
                    print(f"   Tag: {btn['tagName']}")
                    print(f"   Text: {btn['text'][:80]}")
                    print(f"   Aria-label: {btn['ariaLabel'][:80]}")
                    print(f"   Class: {btn['className'][:80]}")
                    print(f"   Data-control-name: {btn['dataControlName']}")
                    print()

            if not post_related:
                print("⚠️  No post-related buttons found in first 50 elements!")
                print()
                print("Showing all buttons:")
                for btn in buttons_info[:20]:
                    print(f"Button #{btn['index']}: {btn['text'][:50]} | {btn['ariaLabel'][:50]}")
                print()

            # Try to find the share box / post composer
            print("🔍 Looking for share box / post composer...")
            share_boxes = page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('[class*="share"], [class*="composer"], [class*="post"]'));
                    return elements.slice(0, 20).map((el, idx) => {
                        return {
                            index: idx,
                            tagName: el.tagName,
                            className: el.className || '',
                            id: el.id || '',
                            text: el.innerText?.substring(0, 100) || ''
                        };
                    });
                }
            """)

            if share_boxes:
                print(f"Found {len(share_boxes)} potential share/composer elements:")
                for box in share_boxes[:10]:
                    print(f"  Element #{box['index']}: {box['tagName']} | {box['className'][:60]}")
                print()

            # Save detailed HTML of the top section
            print("💾 Saving HTML structure...")
            html_content = page.evaluate("""
                () => {
                    const main = document.querySelector('main') || document.body;
                    return main.innerHTML.substring(0, 50000);
                }
            """)

            html_file = vault_path / "silver" / "Logs" / "linkedin_ui_structure.html"
            html_file.write_text(html_content)
            print(f"📄 HTML saved to: {html_file}")
            print()

            # Take screenshot
            screenshot_path = vault_path / "silver" / "Logs" / "linkedin_ui_inspector.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            print()

            print("=" * 60)
            print("Browser will stay open for 30 seconds for manual inspection.")
            print("=" * 60)
            page.wait_for_timeout(30000)

            browser.close()
            print("✅ Inspection complete!")

    except Exception as e:
        logger.error(f"Inspection error: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    inspect_linkedin_ui()

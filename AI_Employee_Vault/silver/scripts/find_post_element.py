#!/usr/bin/env python3
"""
Find LinkedIn Post Element
Comprehensive search for the actual posting UI element.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def find_post_element():
    """Find the actual LinkedIn posting element."""

    session_dir = Path(__file__).parent.parent / "config" / "linkedin_session"
    screenshot_dir = Path(__file__).parent.parent / "debug_screenshots"
    screenshot_dir.mkdir(exist_ok=True)

    print("\n" + "="*70)
    print("LinkedIn Post Element Finder")
    print("="*70)

    with sync_playwright() as p:
        # Launch browser
        print("\n1. Launching browser...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # Navigate to LinkedIn feed
        print("2. Navigating to LinkedIn feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        print("3. Searching for posting UI elements...")

        # Search for various patterns
        search_patterns = [
            ('Input fields', 'input[type="text"]'),
            ('Textareas', 'textarea'),
            ('Contenteditable divs', '[contenteditable="true"]'),
            ('Buttons with "post"', 'button:has-text("post")'),
            ('Buttons with "share"', 'button:has-text("share")'),
            ('Buttons with "write"', 'button:has-text("write")'),
            ('Buttons with "create"', 'button:has-text("create")'),
            ('Divs with role=button', 'div[role="button"]'),
            ('Share box classes', '[class*="share"]'),
            ('Post box classes', '[class*="post"]'),
        ]

        for name, selector in search_patterns:
            try:
                count = page.locator(selector).count()
                print(f"\n{name}: {selector}")
                print(f"  Found: {count} elements")

                if count > 0 and count <= 5:
                    for i in range(count):
                        elem = page.locator(selector).nth(i)
                        try:
                            is_visible = elem.is_visible()
                            if is_visible:
                                text = elem.inner_text(timeout=1000)
                                classes = elem.get_attribute('class')
                                aria_label = elem.get_attribute('aria-label')
                                placeholder = elem.get_attribute('placeholder')

                                print(f"  [{i}] Visible: {is_visible}")
                                if text and len(text) < 100:
                                    print(f"      Text: '{text}'")
                                if placeholder:
                                    print(f"      Placeholder: '{placeholder}'")
                                if aria_label:
                                    print(f"      Aria-label: '{aria_label}'")
                                if classes and len(classes) < 200:
                                    print(f"      Classes: '{classes}'")
                        except:
                            pass
            except Exception as e:
                print(f"  Error: {str(e)[:50]}")

        # Use JavaScript to find the most likely posting element
        print("\n4. Using JavaScript to find posting elements...")
        try:
            result = page.evaluate("""() => {
                // Look for elements that might be the post composer trigger
                const candidates = [];

                // Check for input-like elements with post-related text
                document.querySelectorAll('input, textarea, [contenteditable], button, div[role="button"]').forEach(el => {
                    const text = el.textContent?.toLowerCase() || '';
                    const placeholder = el.getAttribute('placeholder')?.toLowerCase() || '';
                    const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
                    const className = el.className?.toLowerCase() || '';

                    // Look for post-related keywords
                    const keywords = ['post', 'share', 'write', 'start', 'create', 'what', 'mind', 'thinking'];
                    const hasKeyword = keywords.some(kw =>
                        text.includes(kw) || placeholder.includes(kw) || ariaLabel.includes(kw) || className.includes(kw)
                    );

                    if (hasKeyword) {
                        const rect = el.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && rect.top >= 0;

                        if (isVisible) {
                            candidates.push({
                                tag: el.tagName,
                                text: text.substring(0, 100),
                                placeholder: placeholder,
                                ariaLabel: ariaLabel,
                                className: el.className.substring(0, 150),
                                id: el.id,
                                top: Math.round(rect.top),
                                left: Math.round(rect.left),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            });
                        }
                    }
                });

                // Sort by position (top to bottom, left to right)
                candidates.sort((a, b) => {
                    if (Math.abs(a.top - b.top) > 50) return a.top - b.top;
                    return a.left - b.left;
                });

                return candidates.slice(0, 10);  // Top 10 candidates
            }""")

            print(f"\n  Found {len(result)} candidate elements:")
            for i, elem in enumerate(result):
                print(f"\n  Candidate {i+1}:")
                print(f"    Tag: {elem['tag']}")
                print(f"    Text: '{elem['text']}'")
                if elem['placeholder']:
                    print(f"    Placeholder: '{elem['placeholder']}'")
                if elem['ariaLabel']:
                    print(f"    Aria-label: '{elem['ariaLabel']}'")
                if elem['id']:
                    print(f"    ID: '{elem['id']}'")
                print(f"    Position: top={elem['top']}, left={elem['left']}")
                print(f"    Size: {elem['width']}x{elem['height']}")
                print(f"    Classes: '{elem['className']}'")

        except Exception as e:
            print(f"  Error: {e}")

        # Take screenshot
        screenshot_path = screenshot_dir / "post_element_search.png"
        page.screenshot(path=str(screenshot_path))
        print(f"\n5. Screenshot saved: {screenshot_path}")

        print("\n" + "="*70)
        print("Keeping browser open for 60 seconds for manual inspection...")
        print("Please look at the page and identify the posting element!")
        print("="*70)
        page.wait_for_timeout(60000)

        browser.close()

        print("\n✓ Search complete!")
        print("\nBased on the output above, we should be able to identify the correct selector.")

if __name__ == "__main__":
    try:
        find_post_element()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

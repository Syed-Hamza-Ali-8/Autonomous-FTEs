#!/usr/bin/env python3
"""
LinkedIn Posting - Updated with Modern Selectors

This script uses updated selectors that work with LinkedIn's current UI.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time


def find_start_post_element(page):
    """
    Find the 'Start a post' element using multiple strategies.

    LinkedIn's UI can vary, so we try multiple approaches:
    1. Text-based selectors
    2. Class-based selectors
    3. Data attribute selectors
    4. Role-based selectors
    5. Combination selectors
    """

    strategies = [
        # Strategy 1: Text-based (most reliable if text hasn't changed)
        {
            'name': 'Text: "Start a post"',
            'selector': 'button:has-text("Start a post")',
            'wait': True
        },
        {
            'name': 'Text: "Start"',
            'selector': 'button:has-text("Start")',
            'wait': True
        },

        # Strategy 2: Share box trigger (common pattern)
        {
            'name': 'Share box trigger',
            'selector': '.share-box-feed-entry__trigger',
            'wait': True
        },
        {
            'name': 'Share box button',
            'selector': 'button.share-box-feed-entry__trigger',
            'wait': True
        },

        # Strategy 3: Data attributes
        {
            'name': 'Data control name',
            'selector': '[data-control-name="share_box_trigger"]',
            'wait': True
        },

        # Strategy 4: Aria labels
        {
            'name': 'Aria label: post',
            'selector': 'button[aria-label*="post" i]',
            'wait': True
        },
        {
            'name': 'Aria label: Start',
            'selector': 'button[aria-label*="Start" i]',
            'wait': True
        },

        # Strategy 5: Class patterns (LinkedIn often uses these)
        {
            'name': 'Share creation class',
            'selector': '.share-creation-state__text',
            'wait': True
        },
        {
            'name': 'Artdeco button share',
            'selector': 'button.artdeco-button[aria-label*="post" i]',
            'wait': True
        },

        # Strategy 6: Clickable div (sometimes LinkedIn uses divs with role="button")
        {
            'name': 'Div with button role',
            'selector': 'div[role="button"]:has-text("Start")',
            'wait': True
        },

        # Strategy 7: Generic share/post area
        {
            'name': 'Share box area',
            'selector': '.share-box-feed-entry',
            'wait': True
        },
    ]

    print("\n🔍 Trying multiple strategies to find 'Start a post' element...")

    for strategy in strategies:
        try:
            selector = strategy['selector']
            print(f"\n   Trying: {strategy['name']}")
            print(f"   Selector: {selector}")

            # Check if element exists
            count = page.locator(selector).count()

            if count > 0:
                print(f"   ✅ Found {count} element(s)!")

                # Get the first element
                element = page.locator(selector).first

                # Check if it's visible
                if element.is_visible():
                    print(f"   ✅ Element is visible!")
                    return {
                        'success': True,
                        'element': element,
                        'selector': selector,
                        'strategy': strategy['name']
                    }
                else:
                    print(f"   ⚠️ Element exists but not visible")
            else:
                print(f"   ❌ Not found")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    return {
        'success': False,
        'error': 'Could not find Start a post element with any strategy'
    }


def post_to_linkedin_updated(session_path: str, content: str, headless: bool = False) -> dict:
    """Post to LinkedIn using updated selectors."""

    print("\n" + "=" * 70)
    print("📝 LinkedIn Posting - Updated Method")
    print("=" * 70)

    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("\n1️⃣ Navigating to LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Check if logged in
            if "login" in page.url.lower() or "authwall" in page.url.lower():
                browser.close()
                return {
                    "success": False,
                    "error": "Session expired",
                    "message": "Run: python silver/scripts/setup_linkedin.py"
                }

            print("   ✅ Logged in successfully")

            # Wait for page to fully load
            print("\n2️⃣ Waiting for page to load...")
            page.wait_for_timeout(5000)

            # Find the start post element
            print("\n3️⃣ Finding 'Start a post' element...")
            result = find_start_post_element(page)

            if not result['success']:
                # Take screenshot for debugging
                screenshot_path = "linkedin_failed.png"
                page.screenshot(path=screenshot_path)
                browser.close()
                return {
                    "success": False,
                    "error": result['error'],
                    "screenshot": screenshot_path
                }

            print(f"\n   ✅ Found element using: {result['strategy']}")

            # Click the element
            print("\n4️⃣ Clicking 'Start a post' element...")
            result['element'].click(timeout=10000)

            # Wait for editor to appear
            print("\n5️⃣ Waiting for post editor...")
            page.wait_for_selector('[role="textbox"]', timeout=10000)
            print("   ✅ Editor appeared")

            # Type content
            print("\n6️⃣ Typing content...")
            editor = page.locator('[role="textbox"]').first
            editor.click()
            editor.fill(content)
            print("   ✅ Content entered")

            # Wait for content to be processed
            page.wait_for_timeout(2000)

            # Find and click Post button
            print("\n7️⃣ Finding 'Post' button...")

            post_button_selectors = [
                'button.share-actions__primary-action',
                '[role="dialog"] button.share-actions__primary-action',
                'button[aria-label*="Post" i]:not([disabled])',
                'button.artdeco-button--primary:has-text("Post")',
                '[role="dialog"] button:has-text("Post"):not([disabled])',
            ]

            post_clicked = False
            for selector in post_button_selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        button = page.locator(selector).first
                        if button.is_visible() and not button.is_disabled():
                            print(f"   ✅ Found Post button: {selector}")
                            button.click(timeout=5000)
                            post_clicked = True
                            break
                except Exception as e:
                    continue

            if not post_clicked:
                screenshot_path = "linkedin_no_post_button.png"
                page.screenshot(path=screenshot_path)
                browser.close()
                return {
                    "success": False,
                    "error": "Could not find or click Post button",
                    "screenshot": screenshot_path
                }

            print("   ✅ Clicked Post button")

            # Verify post submitted
            print("\n8️⃣ Verifying post submission...")
            page.wait_for_timeout(3000)

            # Check if modal closed
            modal_count = page.locator('[role="dialog"]').count()

            if modal_count > 0:
                print("   ⚠️ Modal still open - waiting longer...")
                page.wait_for_timeout(3000)
                modal_count = page.locator('[role="dialog"]').count()

                if modal_count > 0:
                    screenshot_path = "linkedin_modal_open.png"
                    page.screenshot(path=screenshot_path)
                    browser.close()
                    return {
                        "success": False,
                        "error": "Modal did not close",
                        "message": "Post may not have submitted",
                        "screenshot": screenshot_path
                    }

            print("   ✅ Modal closed - post submitted!")

            # Take success screenshot
            screenshot_path = "linkedin_success.png"
            page.screenshot(path=screenshot_path)

            browser.close()

            print("\n" + "=" * 70)
            print("✅ SUCCESS! Post submitted to LinkedIn")
            print("=" * 70)

            return {
                "success": True,
                "message": "Post submitted successfully",
                "screenshot": screenshot_path,
                "strategy_used": result['strategy']
            }

    except PlaywrightTimeout as e:
        return {
            "success": False,
            "error": "Timeout",
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e)
        }


def main():
    """Main execution."""

    # Get session path
    vault_path = Path(__file__).parent.parent.parent
    session_path = vault_path / "silver" / "config" / "linkedin_session"

    if not session_path.exists():
        print(f"\n❌ LinkedIn session not found at: {session_path}")
        print("   Run: python silver/scripts/setup_linkedin.py")
        return 1

    # Test content
    test_content = """🚀 Testing automated LinkedIn posting with updated selectors!

This post verifies that our AI Employee system can successfully post to LinkedIn.

#Automation #Testing #AI #SilverTier"""

    print("\nTest content:")
    print("-" * 70)
    print(test_content)
    print("-" * 70)

    # Ask for confirmation
    response = input("\nPost this to LinkedIn? (yes/no): ")

    if response.lower() != "yes":
        print("\n✅ Test cancelled.")
        return 0

    # Post to LinkedIn (visible browser for debugging)
    result = post_to_linkedin_updated(str(session_path), test_content, headless=False)

    if result["success"]:
        print(f"\n   Screenshot: {result['screenshot']}")
        print(f"   Strategy used: {result['strategy_used']}")
        print("\n   Check your LinkedIn profile to verify the post!")
        return 0
    else:
        print(f"\n   Error: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        if 'screenshot' in result:
            print(f"   Screenshot: {result['screenshot']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

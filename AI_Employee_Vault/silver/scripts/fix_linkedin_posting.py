#!/usr/bin/env python3
"""
LinkedIn Posting Fix - Comprehensive Solution

This script fixes the LinkedIn posting timeout issue by:
1. Checking session validity
2. Using multiple selector strategies
3. Adding robust error handling
4. Providing clear diagnostics
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time


def test_linkedin_session(session_path: str) -> dict:
    """Test if LinkedIn session is valid."""
    print("\n🔍 Testing LinkedIn Session...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # Visible for debugging
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("   Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)

            # Check if logged in
            current_url = page.url.lower()
            if "login" in current_url or "authwall" in current_url:
                browser.close()
                return {
                    "valid": False,
                    "error": "Session expired - need to re-login",
                    "url": page.url
                }

            print(f"   ✅ Logged in successfully")
            print(f"   Current URL: {page.url}")

            # Wait for page to load
            page.wait_for_timeout(3000)

            # Find "Start a post" button using multiple strategies
            print("\n🔍 Looking for 'Start a post' button...")

            selectors = [
                'button:has-text("Start a post")',
                'button:has-text("Start")',
                '[data-control-name="share_box_trigger"]',
                '.share-box-feed-entry__trigger',
                'button[aria-label*="Start a post"]',
                'button[aria-label*="post"]',
            ]

            found_selector = None
            for selector in selectors:
                try:
                    count = page.locator(selector).count()
                    if count > 0:
                        print(f"   ✅ Found button with: {selector} (count: {count})")
                        found_selector = selector
                        break
                    else:
                        print(f"   ❌ Not found: {selector}")
                except Exception as e:
                    print(f"   ❌ Error with {selector}: {e}")

            if not found_selector:
                # Take screenshot for debugging
                screenshot_path = "linkedin_debug.png"
                page.screenshot(path=screenshot_path)
                print(f"\n   📸 Screenshot saved to: {screenshot_path}")

                browser.close()
                return {
                    "valid": True,
                    "button_found": False,
                    "error": "Could not find 'Start a post' button",
                    "screenshot": screenshot_path
                }

            browser.close()
            return {
                "valid": True,
                "button_found": True,
                "selector": found_selector,
                "url": page.url
            }

    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def post_to_linkedin(session_path: str, content: str, selector: str) -> dict:
    """Post to LinkedIn using the working selector."""
    print("\n📝 Posting to LinkedIn...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # Visible for debugging
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            page = browser.new_page()

            # Navigate to LinkedIn
            print("   Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
            page.wait_for_timeout(3000)

            # Click "Start a post" button
            print(f"   Clicking button with: {selector}")
            page.click(selector, timeout=15000)

            # Wait for editor
            print("   Waiting for editor...")
            page.wait_for_selector('[role="textbox"]', timeout=10000)

            # Type content
            print("   Typing content...")
            editor = page.locator('[role="textbox"]').first
            editor.click()
            editor.fill(content)
            page.wait_for_timeout(2000)

            # Look for "Post" button (primary action)
            print("   Looking for 'Post' button...")

            post_selectors = [
                'button.share-actions__primary-action',
                '[role="dialog"] button.share-actions__primary-action',
                'button:has-text("Post"):not([disabled])',
            ]

            post_clicked = False
            for post_selector in post_selectors:
                try:
                    count = page.locator(post_selector).count()
                    if count > 0:
                        button = page.locator(post_selector).first
                        if not button.is_disabled():
                            print(f"   Clicking 'Post' button with: {post_selector}")
                            button.click(timeout=5000)
                            post_clicked = True
                            break
                except Exception as e:
                    print(f"   ❌ Failed with {post_selector}: {e}")

            if not post_clicked:
                browser.close()
                return {
                    "success": False,
                    "error": "Could not find or click 'Post' button"
                }

            # Verify post submitted (modal should close)
            print("   Verifying post submission...")
            page.wait_for_timeout(3000)

            modal_count = page.locator('[role="dialog"]').count()
            if modal_count > 0:
                print("   ⚠️ Modal still open - post may not have submitted")
                browser.close()
                return {
                    "success": False,
                    "error": "Modal did not close - post not submitted"
                }

            print("   ✅ Modal closed - post submitted successfully!")

            # Take success screenshot
            screenshot_path = "linkedin_success.png"
            page.screenshot(path=screenshot_path)
            print(f"   📸 Screenshot saved to: {screenshot_path}")

            browser.close()

            return {
                "success": True,
                "message": "Post submitted successfully",
                "screenshot": screenshot_path
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
    print("=" * 60)
    print("LinkedIn Posting Fix - Comprehensive Test")
    print("=" * 60)

    # Get session path
    vault_path = Path(__file__).parent.parent.parent
    session_path = vault_path / "silver" / "config" / "linkedin_session"

    if not session_path.exists():
        print(f"\n❌ LinkedIn session not found at: {session_path}")
        print("   Run: python silver/scripts/setup_linkedin.py")
        return 1

    # Test session
    result = test_linkedin_session(str(session_path))

    if not result.get("valid"):
        print(f"\n❌ Session Invalid: {result.get('error')}")
        print("   Run: python silver/scripts/setup_linkedin.py")
        return 1

    if not result.get("button_found"):
        print(f"\n❌ Button Not Found: {result.get('error')}")
        print(f"   Screenshot: {result.get('screenshot')}")
        print("\n   LinkedIn UI may have changed. Check screenshot for details.")
        return 1

    print(f"\n✅ Session Valid!")
    print(f"   Working selector: {result['selector']}")

    # Ask user if they want to test posting
    print("\n" + "=" * 60)
    response = input("Do you want to test posting to LinkedIn? (yes/no): ")

    if response.lower() != "yes":
        print("\n✅ Session test complete. Exiting.")
        return 0

    # Generate test content
    test_content = """🚀 Testing automated LinkedIn posting!

This is a test post from my AI Employee system.

#Automation #Testing #AI"""

    print(f"\nTest content:")
    print("-" * 60)
    print(test_content)
    print("-" * 60)

    # Post to LinkedIn
    post_result = post_to_linkedin(str(session_path), test_content, result['selector'])

    if post_result["success"]:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! LinkedIn posting is working!")
        print("=" * 60)
        print(f"   Screenshot: {post_result['screenshot']}")
        print("\n   Check your LinkedIn profile to verify the post.")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED! LinkedIn posting did not work.")
        print("=" * 60)
        print(f"   Error: {post_result.get('error')}")
        print(f"   Message: {post_result.get('message')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

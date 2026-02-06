#!/usr/bin/env python3
"""
Quick LinkedIn posting test with VISIBLE browser.

This script tests ONLY LinkedIn posting so you can quickly verify the modal fixes.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster


def main():
    """Quick LinkedIn posting test."""

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    print("=" * 70)
    print("🧪 QUICK LINKEDIN POSTING TEST")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Open LinkedIn in a VISIBLE browser window")
    print("  2. Post a test message")
    print("  3. You can watch the entire process")
    print()
    print("⚠️  This will post to your LinkedIn profile!")
    print()

    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Test cancelled.")
        return

    print()
    print("Initializing LinkedIn poster...")

    try:
        poster = LinkedInPoster(vault_path)

        # Generate test content
        content = """🧪 Testing LinkedIn automation - Modal Fix Test

This is a test post to verify that the 8-modal issue is fixed.

✅ Browser automation working
✅ Modal handling improved
✅ Post submission working

#Automation #Testing #AI"""

        print()
        print("📝 Post content:")
        print("─" * 60)
        print(content)
        print("─" * 60)
        print()
        print("🚀 Posting to LinkedIn...")
        print("   (Watch the browser window - you'll see everything)")
        print()

        # Post with visible browser
        result = poster.post_update(content)

        print()
        if result["success"]:
            print("✅ SUCCESS! Post published to LinkedIn!")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print()
            print("🔍 Check your LinkedIn profile to see the post")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            print(f"   Message: {result.get('message', '')}")
            print()
            print("Troubleshooting:")
            print("  1. Check the browser window - what did you see?")
            print("  2. Check screenshot: silver/Logs/after_start_post_click.png")
            print("  3. How many modals appeared?")
            print("  4. Did the textbox appear after pressing Escape?")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

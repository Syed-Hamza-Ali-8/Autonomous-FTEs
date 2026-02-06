#!/usr/bin/env python3
"""
Test LinkedIn posting with VISIBLE browser.

This script posts to LinkedIn with the browser visible so you can see
what's happening and debug any issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster


def main():
    """Test LinkedIn posting with visible browser."""

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    print("=" * 70)
    print("🧪 LINKEDIN POSTING TEST (VISIBLE BROWSER)")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Open a VISIBLE browser window")
    print("  2. Navigate to LinkedIn")
    print("  3. Post a test message")
    print("  4. You can watch the entire process")
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
        content = """🧪 Testing LinkedIn automation!

This is a test post from my AI Employee system.

✅ Browser automation working
✅ Session persistence working
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

        # Post with visible browser (headless=False is default in post_update)
        # We need to temporarily modify the poster to use headless=False
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
            print("  1. Check if LinkedIn session is valid")
            print("  2. Try running: python3 scripts/setup_linkedin.py")
            print("  3. Check your internet connection")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

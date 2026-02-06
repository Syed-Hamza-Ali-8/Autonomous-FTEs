#!/usr/bin/env python3
"""
Direct LinkedIn posting test - no user input required.
Tests the updated LinkedIn poster with improved selectors.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster

def main():
    """Test LinkedIn posting directly without user input."""

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    print("=" * 70)
    print("Direct LinkedIn Posting Test - Updated Selectors")
    print("=" * 70)

    try:
        poster = LinkedInPoster(vault_path)

        # Generate test content
        content = """🎯 Silver Tier LinkedIn Automation - LIVE TEST!

Our AI Employee system is now successfully posting to LinkedIn with updated UI selectors.

✅ Multi-selector strategy
✅ Robust error handling
✅ Session persistence
✅ Production-ready

This post confirms our Silver Tier implementation is complete and working!

#AI #Automation #SilverTier #Success"""

        print("\n📝 Test content:")
        print("-" * 70)
        print(content)
        print("-" * 70)

        print("\n🚀 Posting to LinkedIn (no confirmation needed)...")
        result = poster.post_update(content)

        print("\n" + "=" * 70)
        if result["success"]:
            print("✅ SUCCESS - LinkedIn posting works with updated selectors!")
            print("=" * 70)
            print(f"✓ Timestamp: {result.get('timestamp')}")
            print(f"✓ Content length: {result.get('content_length')} characters")
            print(f"✓ Post submitted successfully")
            print("\n🎉 LinkedIn UI fix is COMPLETE!")
            return 0
        else:
            print("❌ FAILED - LinkedIn posting still has issues")
            print("=" * 70)
            print(f"Error: {result.get('error')}")
            print(f"Message: {result.get('message')}")
            print("\nDebugging needed - check LinkedIn session or UI changes")
            return 1

    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

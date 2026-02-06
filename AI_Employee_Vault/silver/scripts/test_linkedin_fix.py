#!/usr/bin/env python3
"""
Test script to verify the LinkedIn posting fixes.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster


def main():
    """Test the updated LinkedIn poster implementation."""
    print("\n" + "=" * 60)
    print("Testing LinkedIn Poster Fixes")
    print("=" * 60)

    vault_path = Path(__file__).parent.parent.parent.absolute()

    # Initialize poster
    print("\n1️⃣  Initializing LinkedIn poster...")
    poster = LinkedInPoster(str(vault_path))
    print("   ✅ LinkedIn poster initialized")

    # Test content
    test_content = """Testing LinkedIn posting fixes - improved button detection and modal verification.

Key improvements:
✅ Better "Start a post" button detection
✅ Element visibility/enabled state checking
✅ Simplified Post button click logic
✅ Modal verification for successful submission

#automation #testing #linkedin"""

    print("\n2️⃣  Posting test content...")
    print(f"   Content length: {len(test_content)} characters")

    result = poster.post_update(test_content)

    print("\n3️⃣  Result:")
    print(f"   {result}")

    if result.get("success"):
        print("\n   ✅ Post submitted successfully!")
        return True
    else:
        print(f"\n   ❌ Post failed: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for LinkedIn posting functionality.

This script tests the LinkedIn poster with your fake profile.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster
from src.utils import get_logger


def test_linkedin_poster(dry_run: bool = False):
    """
    Test LinkedIn posting functionality.

    Args:
        dry_run: If True, only generate content without posting
    """
    logger = get_logger("test_linkedin")

    print("\n" + "=" * 60)
    print("LinkedIn Poster Test")
    print("=" * 60)

    vault_path = Path(__file__).parent.parent.parent.absolute()

    try:
        # Initialize poster
        print("\n1️⃣  Initializing LinkedIn poster...")
        poster = LinkedInPoster(str(vault_path))
        print("   ✅ LinkedIn poster initialized")

        # Check session exists
        session_path = Path(vault_path) / "silver" / "config" / "linkedin_session"
        if not session_path.exists():
            print("\n   ❌ LinkedIn session not found!")
            print("   Run: python silver/scripts/setup_linkedin.py")
            return False

        print(f"   ✅ Session found at: {session_path}")

        # Generate content
        print("\n2️⃣  Generating business content...")
        topics = [
            "AI automation",
            "business productivity",
            "workflow optimization",
            "digital transformation"
        ]

        import random
        topic = random.choice(topics)
        content = poster.generate_business_post(topic)

        print(f"   ✅ Generated content for topic: {topic}")
        print("\n" + "-" * 60)
        print(content)
        print("-" * 60)

        if dry_run:
            print("\n🔍 DRY RUN MODE - No actual posting")
            print("   Content generated successfully!")
            return True

        # Ask for confirmation
        print("\n3️⃣  Ready to post to LinkedIn")
        response = input("\n   Post this to LinkedIn? (yes/no): ")

        if response.lower() != "yes":
            print("\n   ⏭️  Posting cancelled by user")
            return True

        # Post to LinkedIn
        print("\n   📤 Posting to LinkedIn...")
        result = poster.post_update(content)

        if result["success"]:
            print("\n   ✅ Successfully posted to LinkedIn!")
            print(f"   📅 Timestamp: {result['timestamp']}")
            print(f"   📝 Content length: {result['content_length']} characters")
            return True
        else:
            print(f"\n   ❌ Failed to post: {result.get('error')}")
            print(f"   💡 Message: {result.get('message')}")
            return False

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure Playwright is installed:")
        print("  playwright install chromium")
        return False

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        return False

    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test LinkedIn posting")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate content without posting"
    )

    args = parser.parse_args()

    print("\n🧪 Testing LinkedIn Poster")

    if args.dry_run:
        print("   Mode: DRY RUN (no actual posting)")
    else:
        print("   Mode: LIVE (will post to LinkedIn)")

    success = test_linkedin_poster(dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

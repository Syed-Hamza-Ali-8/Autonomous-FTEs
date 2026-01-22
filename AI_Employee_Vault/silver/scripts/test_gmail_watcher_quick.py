#!/usr/bin/env python3
"""
Quick test of Gmail watcher with the new account.
This script checks if the watcher can connect and read emails.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.gmail_watcher import GmailWatcher


def test_gmail_watcher():
    """Test Gmail watcher with new account."""
    print("=" * 60)
    print("Gmail Watcher Quick Test")
    print("=" * 60)
    print()

    # Get vault path
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )

    config_path = os.path.join(vault_path, "silver", "config", "watcher_config.yaml")

    print("1️⃣  Initializing Gmail watcher...")
    try:
        watcher = GmailWatcher(vault_path, config_path)
        print("   ✅ Gmail watcher initialized")
        print(f"   📧 Account: {watcher.email_address if hasattr(watcher, 'email_address') else 'Connected'}")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return False

    print()
    print("2️⃣  Checking for new messages...")
    try:
        updates = watcher.check_for_updates()
        print(f"   ✅ Check completed")
        print(f"   📬 Found {len(updates)} new message(s)")

        if updates:
            print()
            print("   Messages found:")
            for i, msg in enumerate(updates[:5], 1):  # Show first 5
                print(f"   {i}. Message ID: {msg.get('id', 'unknown')}")
        else:
            print()
            print("   ℹ️  No new messages (this is normal for a fresh account)")
            print()
            print("   💡 To test message detection:")
            print("      1. Send an email to: hey349073@gmail.com")
            print("      2. Run this script again")
            print("      3. Or start the watcher: python3 -m silver.src.watchers.gmail_watcher")
    except Exception as e:
        print(f"   ❌ Failed to check messages: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ Gmail Watcher Test PASSED!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("   1. Send a test email to: hey349073@gmail.com")
    print("   2. Start the watcher: python3 -m silver.src.watchers.gmail_watcher")
    print("   3. Check Needs_Action/ folder for detected messages")
    print()

    return True


if __name__ == "__main__":
    success = test_gmail_watcher()
    sys.exit(0 if success else 1)

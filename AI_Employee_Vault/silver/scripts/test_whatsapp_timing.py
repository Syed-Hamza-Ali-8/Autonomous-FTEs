#!/usr/bin/env python3
"""
Test WhatsApp message timing to verify immediate delivery.

This script tests the fix for delayed message delivery by:
1. Sending a message to a contact
2. Monitoring the timing of each step
3. Verifying the message is delivered immediately after chat loads
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.actions.whatsapp_sender import WhatsAppSender
from silver.src.utils import setup_logging

def main():
    """Test WhatsApp message timing."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    print("=" * 80)
    print("  WhatsApp Message Timing Test")
    print("=" * 80)
    print()
    print("This test verifies that messages are delivered immediately")
    print("after the chat finishes loading (not queued during sync).")
    print()

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize sender
        print("1. Initializing WhatsApp sender...")
        sender = WhatsAppSender(vault_path)
        print("   ✅ Initialized")
        print()

        # Get recipient
        recipient = input("Enter recipient name (e.g., 'Ubaid GIAIC'): ").strip()
        if not recipient:
            print("❌ No recipient provided")
            sys.exit(1)

        print()
        print("2. Sending message with timing monitoring...")
        print("   Watch for these steps:")
        print("   - Contact selected")
        print("   - Waiting for chat to load (10-60s)")
        print("   - Chat fully loaded")
        print("   - Message sent")
        print("   - Delivery confirmed")
        print()

        # Record start time
        start_time = time.time()

        # Send message
        result = sender.send_message(
            to=recipient,
            message="🧪 Timing test: This message should arrive immediately after chat loads!",
            wait_for_delivery=True
        )

        # Record end time
        end_time = time.time()
        total_time = end_time - start_time

        print()
        print("=" * 80)
        print("  Test Results")
        print("=" * 80)
        print()

        if result['success']:
            print(f"✅ Message sent successfully!")
            print(f"   Total time: {total_time:.1f} seconds")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Recipient: {result['recipient']}")
            print()
            print("Expected behavior:")
            print("  - Chat loading: 10-60 seconds (depends on chat size)")
            print("  - Message delivery: Immediate after chat loads")
            print()
            print("Ask the recipient:")
            print("  - Did they receive the message immediately?")
            print("  - Or did it arrive after a delay?")
            print()
            print("If immediate: ✅ Fix working!")
            print("If delayed: ❌ Issue persists")
        else:
            print(f"❌ Failed to send message: {result['error']}")
            sys.exit(1)

        print()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

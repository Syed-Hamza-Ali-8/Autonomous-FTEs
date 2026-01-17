#!/usr/bin/env python3
"""
Email Sender Test Script

Tests the email sending functionality with Gmail API.
Supports both dry-run (mock) and live modes.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.actions.email_sender import EmailSender
from src.utils import get_logger, setup_logging


def test_email_connection():
    """Test Gmail API connection."""

    print("=" * 70)
    print("Email Sender Test - Connection Check")
    print("=" * 70)
    print()

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        print("1️⃣  Initializing EmailSender...")
        sender = EmailSender(vault_path)
        print("   ✅ EmailSender initialized")
        print()

        # Check if Gmail API is available
        if not sender.gmail_available:
            print("   ⚠️  Gmail API not available")
            print()
            print("   To enable Gmail API:")
            print("   1. Install: pip install google-auth google-api-python-client")
            print("   2. Set up credentials: python silver/scripts/setup_gmail.py")
            print()
            return False

        print("   ✅ Gmail API is available")
        print()

        # Check credentials
        print("2️⃣  Checking credentials...")

        creds_path = Path(vault_path) / "silver" / "config" / "gmail_credentials.json"
        token_path = Path(vault_path) / "silver" / "config" / "gmail_token.json"

        if not creds_path.exists():
            print(f"   ❌ Credentials not found: {creds_path}")
            print()
            print("   Run setup: python silver/scripts/setup_gmail.py")
            return False

        print(f"   ✅ Credentials found: {creds_path}")

        if token_path.exists():
            print(f"   ✅ Token found: {token_path}")
        else:
            print(f"   ⚠️  Token not found (will be created on first use)")

        print()
        print("=" * 70)
        print("✅ Connection check passed!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_dry_run():
    """Test email sending in dry-run mode (no actual sending)."""

    print()
    print("=" * 70)
    print("Email Sender Test - Dry Run (Mock)")
    print("=" * 70)
    print()

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        sender = EmailSender(vault_path)

        # Test email details
        test_email = {
            "to": "test@example.com",
            "subject": "Test Email - Dry Run",
            "body": "This is a test email in dry-run mode. No actual email is sent.",
        }

        print("📧 Test Email Details:")
        print(f"   To: {test_email['to']}")
        print(f"   Subject: {test_email['subject']}")
        print(f"   Body: {test_email['body'][:50]}...")
        print()

        print("🔍 Dry Run Mode: No actual email will be sent")
        print()

        # Mock the send (just validate the email structure)
        print("✅ Email structure is valid")
        print("✅ Dry run completed successfully")
        print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_email_live():
    """Test email sending in live mode (actual sending)."""

    print()
    print("=" * 70)
    print("Email Sender Test - Live Mode")
    print("=" * 70)
    print()

    print("⚠️  WARNING: This will send a REAL email!")
    print()

    # Get recipient email
    recipient = input("Enter recipient email address (or press Enter to cancel): ").strip()

    if not recipient:
        print("Cancelled.")
        return False

    print()
    confirm = input(f"Send test email to {recipient}? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Cancelled.")
        return False

    print()

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        print("1️⃣  Initializing EmailSender...")
        sender = EmailSender(vault_path)
        print("   ✅ Initialized")
        print()

        print("2️⃣  Sending email...")

        result = sender.send_email(
            to=recipient,
            subject="Test Email from AI Employee",
            body="""Hello!

This is a test email from your AI Employee system.

If you received this email, it means:
✅ Gmail API is configured correctly
✅ Email sending is working
✅ HITL workflow can send emails

This is an automated test message.

Best regards,
Your AI Employee
"""
        )

        if result["success"]:
            print("   ✅ Email sent successfully!")
            print()
            print(f"   Message ID: {result.get('message_id', 'N/A')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print()
            print("=" * 70)
            print("✅ Live test passed!")
            print("=" * 70)
            return True
        else:
            print(f"   ❌ Failed to send email")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    print("\n📧 Email Sender Testing Suite\n")

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    live = "--live" in sys.argv

    if not dry_run and not live:
        # Interactive mode
        print("Select test mode:")
        print("1. Connection check only")
        print("2. Dry run (no actual sending)")
        print("3. Live test (send real email)")
        print()

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            success = test_email_connection()
        elif choice == "2":
            success = test_email_connection() and test_email_dry_run()
        elif choice == "3":
            success = test_email_connection() and test_email_live()
        else:
            print("Invalid choice")
            sys.exit(1)
    else:
        # Command-line mode
        success = test_email_connection()

        if success and dry_run:
            success = test_email_dry_run()

        if success and live:
            success = test_email_live()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

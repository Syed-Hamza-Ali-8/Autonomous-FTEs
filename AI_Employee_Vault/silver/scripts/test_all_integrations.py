#!/usr/bin/env python3
"""
Comprehensive Integration Test for Gmail, WhatsApp, and LinkedIn

Tests all three communication channels with clear status reporting.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger, setup_logging


def test_linkedin():
    """Test LinkedIn posting functionality."""

    print("=" * 70)
    print("1️⃣  TESTING LINKEDIN POSTING")
    print("=" * 70)
    print()

    try:
        from src.watchers.linkedin_poster import LinkedInPoster

        vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        poster = LinkedInPoster(vault_path)

        # Check if session exists
        session_path = Path(vault_path) / "silver" / "config" / "linkedin_session"

        if not session_path.exists():
            print("❌ LinkedIn session not found")
            print()
            print("Setup required:")
            print("  python3 silver/scripts/setup_linkedin.py")
            print()
            return False

        print("✅ LinkedIn session found")
        print()

        # Generate test content
        test_content = """🧪 Testing LinkedIn automation from AI Employee system!

This is an automated test post to verify the LinkedIn integration is working correctly.

If you see this post, it means:
✅ LinkedIn session is valid
✅ Playwright automation is working
✅ Post submission flow is correct

#Automation #Testing #AI"""

        print("📝 Test content:")
        print(test_content)
        print()

        # Ask for confirmation
        print("⚠️  This will post to your LinkedIn profile!")
        confirm = input("Continue with LinkedIn test? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("Skipped LinkedIn test")
            return None

        print()
        print("Posting to LinkedIn...")
        print("(Browser will open - this may take 10-15 seconds)")
        print()

        # Post with visible browser
        result = poster.post_update(content=test_content, headless=False)

        if result["success"]:
            print("✅ LinkedIn post successful!")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print()
            print("🔍 Verify: Check your LinkedIn profile to see the post")
            print()
            return True
        else:
            print(f"❌ LinkedIn post failed: {result.get('error', 'Unknown error')}")
            print()
            return False

    except Exception as e:
        print(f"❌ LinkedIn test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_whatsapp():
    """Test WhatsApp messaging functionality."""

    print("=" * 70)
    print("2️⃣  TESTING WHATSAPP MESSAGING")
    print("=" * 70)
    print()

    try:
        from src.actions.whatsapp_sender import WhatsAppSender

        vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        sender = WhatsAppSender(vault_path)

        # Check if session exists
        session_path = Path(vault_path) / "silver" / "config" / "whatsapp_session"

        if not session_path.exists():
            print("❌ WhatsApp session not found")
            print()
            print("Setup required:")
            print("  python3 silver/scripts/setup_whatsapp.py")
            print()
            return False

        print("✅ WhatsApp session found")
        print()

        # Get recipient
        print("Enter test recipient:")
        print("  - Phone number (e.g., +1234567890)")
        print("  - Or contact name (e.g., 'John Doe')")
        print()

        recipient = input("Recipient: ").strip()

        if not recipient:
            print("Skipped WhatsApp test")
            return None

        test_message = """🧪 Test message from AI Employee system

This is an automated test to verify WhatsApp integration is working.

✅ WhatsApp Web session is valid
✅ Playwright automation is working
✅ Message sending is functional"""

        print()
        print("📝 Test message:")
        print(test_message)
        print()

        # Ask for confirmation
        print(f"⚠️  This will send a WhatsApp message to: {recipient}")
        confirm = input("Continue with WhatsApp test? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("Skipped WhatsApp test")
            return None

        print()
        print("Sending WhatsApp message...")
        print("(Browser will open - this may take 10-15 seconds)")
        print()

        # Send with visible browser
        result = sender.send_message(
            to=recipient,
            message=test_message,
            headless=False
        )

        if result["success"]:
            print("✅ WhatsApp message sent successfully!")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print()
            print("🔍 Verify: Check WhatsApp to see the message")
            print()
            return True
        else:
            print(f"❌ WhatsApp message failed: {result.get('error', 'Unknown error')}")
            print()
            return False

    except Exception as e:
        print(f"❌ WhatsApp test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gmail():
    """Test Gmail sending functionality."""

    print("=" * 70)
    print("3️⃣  TESTING GMAIL SENDING")
    print("=" * 70)
    print()

    try:
        from src.actions.email_sender import EmailSender

        vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

        # Check if credentials exist
        creds_path = Path(vault_path) / "silver" / "config" / "gmail_credentials.json"

        if not creds_path.exists():
            print("❌ Gmail credentials not found")
            print()
            print("Setup required:")
            print("  1. Go to: https://console.cloud.google.com/")
            print("  2. Create a project and enable Gmail API")
            print("  3. Download credentials.json")
            print("  4. Run: python3 silver/scripts/setup_gmail.py")
            print()
            print("📚 Full guide: https://developers.google.com/gmail/api/quickstart")
            print()
            return False

        print("✅ Gmail credentials found")
        print()

        sender = EmailSender(vault_path)

        if not sender.gmail_available:
            print("❌ Gmail API not available")
            print()
            print("Install required packages:")
            print("  pip install google-auth google-api-python-client")
            print()
            return False

        print("✅ Gmail API available")
        print()

        # Get recipient
        recipient = input("Enter recipient email address: ").strip()

        if not recipient:
            print("Skipped Gmail test")
            return None

        test_subject = "Test Email from AI Employee"
        test_body = """Hello!

This is a test email from your AI Employee system.

If you received this email, it means:
✅ Gmail API is configured correctly
✅ OAuth authentication is working
✅ Email sending is functional

This is an automated test message.

Best regards,
Your AI Employee"""

        print()
        print("📧 Test email:")
        print(f"   To: {recipient}")
        print(f"   Subject: {test_subject}")
        print(f"   Body: {test_body[:100]}...")
        print()

        # Ask for confirmation
        print(f"⚠️  This will send a real email to: {recipient}")
        confirm = input("Continue with Gmail test? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("Skipped Gmail test")
            return None

        print()
        print("Sending email...")
        print()

        result = sender.send_email(
            to=recipient,
            subject=test_subject,
            body=test_body
        )

        if result["success"]:
            print("✅ Email sent successfully!")
            print(f"   Message ID: {result.get('message_id', 'N/A')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            print()
            print("🔍 Verify: Check the recipient's inbox")
            print()
            return True
        else:
            print(f"❌ Email failed: {result.get('error', 'Unknown error')}")
            print()
            return False

    except Exception as e:
        print(f"❌ Gmail test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    print()
    print("=" * 70)
    print("🧪 COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)
    print()
    print("This script will test:")
    print("  1. LinkedIn posting")
    print("  2. WhatsApp messaging")
    print("  3. Gmail sending")
    print()
    print("Each test is interactive - you'll be asked to confirm before")
    print("any real actions are taken.")
    print()

    input("Press Enter to start testing...")
    print()

    results = {
        "linkedin": None,
        "whatsapp": None,
        "gmail": None,
    }

    # Test LinkedIn
    results["linkedin"] = test_linkedin()

    if results["linkedin"] is not None:
        input("\nPress Enter to continue to WhatsApp test...")
        print()

    # Test WhatsApp
    results["whatsapp"] = test_whatsapp()

    if results["whatsapp"] is not None:
        input("\nPress Enter to continue to Gmail test...")
        print()

    # Test Gmail
    results["gmail"] = test_gmail()

    # Summary
    print()
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print()

    def status_icon(result):
        if result is True:
            return "✅ PASSED"
        elif result is False:
            return "❌ FAILED"
        else:
            return "⏭️  SKIPPED"

    print(f"LinkedIn:  {status_icon(results['linkedin'])}")
    print(f"WhatsApp:  {status_icon(results['whatsapp'])}")
    print(f"Gmail:     {status_icon(results['gmail'])}")
    print()

    # Count results
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print()

    if failed == 0 and passed > 0:
        print("✅ All tested integrations are working!")
        sys.exit(0)
    elif failed > 0:
        print("⚠️  Some integrations need attention")
        sys.exit(1)
    else:
        print("ℹ️  No integrations were tested")
        sys.exit(0)


if __name__ == "__main__":
    main()

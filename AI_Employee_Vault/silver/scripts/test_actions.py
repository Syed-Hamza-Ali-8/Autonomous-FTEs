#!/usr/bin/env python3
"""
Test script for action execution.

This script tests the action execution workflow including:
- EmailSender (Gmail API)
- WhatsAppSender (WhatsApp Web)
- ActionExecutor (orchestration and retry logic)
"""

import os
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.actions.action_executor import ActionExecutor
from src.actions.email_sender import EmailSender
from src.actions.whatsapp_sender import WhatsAppSender
from src.utils import setup_logging


def test_email_sender(vault_path: str) -> bool:
    """Test EmailSender functionality."""
    print("=" * 60)
    print("Testing EmailSender")
    print("=" * 60)
    print()

    try:
        sender = EmailSender(vault_path)
        print("✅ EmailSender initialized")

        # Test: Validate email addresses
        print("\n📋 Testing email validation...")

        valid_email = "test@example.com"
        try:
            sender._validate_email(valid_email)
            print(f"   {valid_email}: valid ✅")
        except ValueError:
            print(f"   {valid_email}: invalid ❌")
            return False

        invalid_email = "invalid-email"
        try:
            sender._validate_email(invalid_email)
            print(f"   {invalid_email}: should be invalid ❌")
            return False
        except ValueError:
            print(f"   {invalid_email}: correctly rejected ✅")

        print("✅ Email validation works")

        # Test: Get sent messages
        print("\n📬 Testing get sent messages...")
        sent_messages = sender.get_sent_messages(max_results=5)
        print(f"   Found {len(sent_messages)} recent sent messages")

        if sent_messages:
            print("   Recent messages:")
            for msg in sent_messages[:3]:
                print(f"      - To: {msg['to']}")
                print(f"        Subject: {msg['subject']}")

        print("✅ Get sent messages works")

        # Test: Send test email (optional, requires user confirmation)
        print("\n📧 Testing email sending...")
        print("   Note: This will send a real email!")

        response = input("   Send test email? (y/N): ").strip().lower()
        if response == 'y':
            to = input("   Enter recipient email: ").strip()
            if to:
                result = sender.send_email(
                    to=to,
                    subject="Test Email from AI Employee Vault",
                    body="""
                    <html>
                    <body>
                        <h1>Test Email</h1>
                        <p>This is a test email from the AI Employee Vault Silver tier.</p>
                        <p>If you received this, email sending is working correctly!</p>
                    </body>
                    </html>
                    """,
                    html=True
                )

                if result['success']:
                    print(f"   ✅ Email sent successfully!")
                    print(f"      Message ID: {result['message_id']}")
                else:
                    print(f"   ❌ Failed to send: {result['error']}")
                    return False
        else:
            print("   ⏭️  Skipped email sending test")

        return True

    except Exception as e:
        print(f"❌ EmailSender test failed: {e}")
        return False


def test_whatsapp_sender(vault_path: str) -> bool:
    """Test WhatsAppSender functionality."""
    print()
    print("=" * 60)
    print("Testing WhatsAppSender")
    print("=" * 60)
    print()

    try:
        sender = WhatsAppSender(vault_path)
        print("✅ WhatsAppSender initialized")

        # Test: Verify session
        print("\n🔍 Testing session verification...")
        is_logged_in = sender.verify_session()

        if is_logged_in:
            print("   ✅ WhatsApp Web session active")
        else:
            print("   ❌ WhatsApp Web not logged in")
            print("   Run: python silver/scripts/setup_whatsapp.py")
            return False

        # Test: Send test message (optional, requires user confirmation)
        print("\n💬 Testing message sending...")
        print("   Note: This will send a real WhatsApp message!")

        response = input("   Send test message? (y/N): ").strip().lower()
        if response == 'y':
            to = input("   Enter recipient name or phone: ").strip()
            if to:
                result = sender.send_message(
                    to=to,
                    message="Test message from AI Employee Vault Silver tier. "
                           "If you received this, WhatsApp sending is working!",
                    wait_for_delivery=True
                )

                if result['success']:
                    print(f"   ✅ Message sent successfully!")
                    print(f"      Message ID: {result['message_id']}")
                else:
                    print(f"   ❌ Failed to send: {result['error']}")
                    return False
        else:
            print("   ⏭️  Skipped message sending test")

        return True

    except Exception as e:
        print(f"❌ WhatsAppSender test failed: {e}")
        return False


def test_action_executor(vault_path: str, config_path: str) -> bool:
    """Test ActionExecutor functionality."""
    print()
    print("=" * 60)
    print("Testing ActionExecutor")
    print("=" * 60)
    print()

    try:
        executor = ActionExecutor(vault_path, config_path)
        print("✅ ActionExecutor initialized")

        # Test: Register handlers
        print("\n📋 Testing handler registration...")

        def mock_email_handler(action_details):
            return {
                "success": True,
                "message_id": "mock_email_123",
            }

        def mock_whatsapp_handler(action_details):
            return {
                "success": True,
                "message_id": "mock_whatsapp_456",
            }

        executor.register_handler('send_email', mock_email_handler)
        executor.register_handler('send_whatsapp', mock_whatsapp_handler)

        print("   ✅ Registered send_email handler")
        print("   ✅ Registered send_whatsapp handler")

        # Test: Get execution stats
        print("\n📊 Testing execution statistics...")
        stats = executor.get_execution_stats()

        print(f"   Total Executed: {stats['total_executed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Pending Approval: {stats['pending_approval']}")

        print("✅ Execution statistics work")

        # Test: Execute approved actions (if any)
        if stats['pending_approval'] > 0:
            print(f"\n⚙️  Testing action execution...")
            print(f"   Found {stats['pending_approval']} approved actions")

            response = input("   Execute approved actions? (y/N): ").strip().lower()
            if response == 'y':
                results = executor.execute_all_approved_actions()

                print(f"\n   Execution Results:")
                print(f"      Total: {results['total']}")
                print(f"      Successful: {results['successful']}")
                print(f"      Failed: {results['failed']}")

                for result in results['results']:
                    if result['success']:
                        print(f"      ✅ {result.get('action_id', 'unknown')}")
                    else:
                        print(f"      ❌ {result.get('action_id', 'unknown')}: {result.get('error', 'unknown')}")
            else:
                print("   ⏭️  Skipped action execution")
        else:
            print("\n⚠️  No approved actions to execute")

        return True

    except Exception as e:
        print(f"❌ ActionExecutor test failed: {e}")
        return False


def test_integration(vault_path: str, config_path: str) -> bool:
    """Test end-to-end action execution workflow."""
    print()
    print("=" * 60)
    print("Testing End-to-End Action Execution")
    print("=" * 60)
    print()

    try:
        # Initialize components
        executor = ActionExecutor(vault_path, config_path)
        email_sender = EmailSender(vault_path)
        whatsapp_sender = WhatsAppSender(vault_path)

        print("✅ All components initialized")

        # Register real handlers
        print("\n📋 Registering action handlers...")

        def handle_send_email(action_details):
            return email_sender.send_email(
                to=action_details.get('to', ''),
                subject=action_details.get('subject', ''),
                body=action_details.get('body', ''),
                html=True
            )

        def handle_send_whatsapp(action_details):
            return whatsapp_sender.send_message(
                to=action_details.get('to', ''),
                message=action_details.get('message', ''),
                wait_for_delivery=True
            )

        executor.register_handler('send_email', handle_send_email)
        executor.register_handler('send_whatsapp', handle_send_whatsapp)

        print("   ✅ Registered email handler")
        print("   ✅ Registered WhatsApp handler")

        # Get current stats
        print("\n📊 Current execution statistics...")
        stats = executor.get_execution_stats()

        print(f"   Total Executed: {stats['total_executed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Pending Approval: {stats['pending_approval']}")

        # Execute approved actions if any
        if stats['pending_approval'] > 0:
            print(f"\n⚙️  Executing {stats['pending_approval']} approved actions...")
            print("   Note: This will execute real actions!")

            response = input("   Proceed with execution? (y/N): ").strip().lower()
            if response == 'y':
                results = executor.execute_all_approved_actions()

                print(f"\n✅ Execution completed:")
                print(f"   Total: {results['total']}")
                print(f"   Successful: {results['successful']}")
                print(f"   Failed: {results['failed']}")

                print("\n   Results:")
                for result in results['results']:
                    if result['success']:
                        print(f"      ✅ {result.get('action_id', 'unknown')}")
                        print(f"         Retry count: {result.get('retry_count', 0)}")
                    else:
                        print(f"      ❌ {result.get('action_id', 'unknown')}")
                        print(f"         Error: {result.get('error', 'unknown')}")
                        print(f"         Retry count: {result.get('retry_count', 0)}")

                return results['failed'] == 0
            else:
                print("   ⏭️  Skipped execution")
        else:
            print("\n⚠️  No approved actions to execute")
            print("   Create an approval request first to test end-to-end workflow")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Main entry point."""
    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    print("=" * 60)
    print("Silver Tier - Action Execution Test Suite")
    print("=" * 60)
    print()

    # Run tests
    results = {
        "EmailSender": test_email_sender(vault_path),
        "WhatsAppSender": test_whatsapp_sender(vault_path),
        "ActionExecutor": test_action_executor(vault_path, config_path),
        "Integration": test_integration(vault_path, config_path),
    }

    # Print summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

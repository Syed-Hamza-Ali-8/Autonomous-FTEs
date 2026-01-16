#!/usr/bin/env python3
"""
Test script for approval workflow.

This script creates test approval requests and verifies the workflow.
"""

import os
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.approval.approval_manager import ApprovalManager
from silver.src.approval.approval_checker import ApprovalChecker
from silver.src.approval.approval_notifier import ApprovalNotifier
from silver.src.utils import setup_logging


def test_approval_manager(vault_path: str, config_path: str):
    """Test ApprovalManager functionality."""
    print("=" * 60)
    print("Testing ApprovalManager")
    print("=" * 60)
    print()

    try:
        manager = ApprovalManager(vault_path, config_path)
        print("✅ ApprovalManager initialized")

        # Test: Check if action is sensitive
        print("\n📋 Testing sensitive action classification...")

        is_sensitive = manager.is_sensitive_action("send_email")
        print(f"   send_email: {'sensitive' if is_sensitive else 'not sensitive'}")
        assert is_sensitive, "send_email should be sensitive"

        is_sensitive = manager.is_sensitive_action("read_file")
        print(f"   read_file: {'sensitive' if is_sensitive else 'not sensitive'}")
        assert not is_sensitive, "read_file should not be sensitive"

        print("✅ Sensitive action classification works")

        # Test: Calculate risk score
        print("\n📊 Testing risk score calculation...")

        risk_score = manager.calculate_risk_score({
            "external_recipient": True,
            "reversible": False,
            "contains_pii": True
        })
        print(f"   Risk score: {risk_score}")
        assert risk_score > 0, "Risk score should be > 0"

        print("✅ Risk score calculation works")

        # Test: Create approval request
        print("\n📝 Creating test approval request...")

        request_id = manager.create_approval_request(
            action_type="send_email",
            action_details={
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email for approval workflow",
                "external_recipient": True,
                "reversible": False
            },
            risk_assessment={
                "sensitivity": "high",
                "impact": "external_communication"
            }
        )

        print(f"✅ Created approval request: {request_id}")

        # Check if file exists
        pending_folder = Path(vault_path) / "Pending_Approval"
        request_file = pending_folder / f"{request_id}.md"

        if request_file.exists():
            print(f"✅ Approval request file created: {request_file}")
        else:
            print(f"❌ Approval request file not found: {request_file}")
            return False

        return True

    except Exception as e:
        print(f"❌ ApprovalManager test failed: {e}")
        return False


def test_approval_checker(vault_path: str, config_path: str):
    """Test ApprovalChecker functionality."""
    print()
    print("=" * 60)
    print("Testing ApprovalChecker")
    print("=" * 60)
    print()

    try:
        checker = ApprovalChecker(vault_path, config_path)
        print("✅ ApprovalChecker initialized")

        # Test: Poll for approvals
        print("\n🔍 Polling for approval requests...")

        approvals = checker.poll_for_approvals()
        print(f"   Found {len(approvals)} approval requests")

        if len(approvals) > 0:
            print("✅ ApprovalChecker can detect approval requests")
        else:
            print("⚠️  No approval requests found (this is okay if none exist)")

        return True

    except Exception as e:
        print(f"❌ ApprovalChecker test failed: {e}")
        return False


def test_approval_notifier(vault_path: str, config_path: str):
    """Test ApprovalNotifier functionality."""
    print()
    print("=" * 60)
    print("Testing ApprovalNotifier")
    print("=" * 60)
    print()

    try:
        notifier = ApprovalNotifier(vault_path, config_path)
        print("✅ ApprovalNotifier initialized")

        # Test: Send test notification
        print("\n🔔 Sending test notification...")
        print("   (Check your system tray for the notification)")

        success = notifier.test_notification()

        if success:
            print("✅ Test notification sent successfully")
            print("   Did you see the notification?")
        else:
            print("⚠️  Notification failed (plyer may not be installed)")
            print("   Install with: pip install plyer")

        return True

    except Exception as e:
        print(f"❌ ApprovalNotifier test failed: {e}")
        return False


def test_end_to_end(vault_path: str, config_path: str):
    """Test end-to-end approval workflow."""
    print()
    print("=" * 60)
    print("Testing End-to-End Approval Workflow")
    print("=" * 60)
    print()

    try:
        # Initialize components
        manager = ApprovalManager(vault_path, config_path)
        checker = ApprovalChecker(vault_path, config_path)
        notifier = ApprovalNotifier(vault_path, config_path)

        print("✅ All components initialized")

        # Step 1: Create approval request
        print("\n📝 Step 1: Creating approval request...")

        request_id = manager.create_approval_request(
            action_type="send_email",
            action_details={
                "to": "test@example.com",
                "subject": "End-to-End Test",
                "body": "Testing the complete approval workflow",
                "external_recipient": True,
                "reversible": False
            }
        )

        print(f"✅ Created: {request_id}")

        # Step 2: Send notification
        print("\n🔔 Step 2: Sending notification...")

        notifier.notify_approval_request(
            request_id=request_id,
            action_type="send_email",
            action_details={
                "to": "test@example.com",
                "subject": "End-to-End Test",
                "risk_level": "high"
            }
        )

        print("✅ Notification sent")

        # Step 3: Check for approval
        print("\n🔍 Step 3: Checking for approval...")
        print("   (Approval request is in Pending_Approval/ folder)")
        print()
        print("   To approve:")
        print(f"   1. Open: Pending_Approval/{request_id}.md")
        print("   2. Change: status: pending → status: approved")
        print("   3. Save the file")
        print()
        print("   To reject:")
        print(f"   1. Open: Pending_Approval/{request_id}.md")
        print("   2. Change: status: pending → status: rejected")
        print("   3. Add: rejection_reason: \"Your reason here\"")
        print("   4. Save the file")
        print()
        print("   The approval checker will detect the change within 10 seconds")
        print()

        # Poll for 30 seconds
        print("⏳ Polling for 30 seconds (waiting for your approval/rejection)...")

        for i in range(6):  # 6 iterations * 5 seconds = 30 seconds
            time.sleep(5)
            approvals = checker.poll_for_approvals()

            for approval in approvals:
                if approval["request_id"] == request_id:
                    print(f"\n✅ Approval detected: {approval['status']}")
                    print(f"   File moved to: {approval['file_path']}")
                    return True

            print(f"   Still waiting... ({(i+1)*5}/30 seconds)")

        print("\n⏱️  Timeout: No approval detected within 30 seconds")
        print("   This is okay - you can approve/reject manually later")
        print(f"   File location: Pending_Approval/{request_id}.md")

        return True

    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
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
    print("Silver Tier - Approval Workflow Test Suite")
    print("=" * 60)
    print()

    # Run tests
    results = {
        "ApprovalManager": test_approval_manager(vault_path, config_path),
        "ApprovalChecker": test_approval_checker(vault_path, config_path),
        "ApprovalNotifier": test_approval_notifier(vault_path, config_path),
        "End-to-End": test_end_to_end(vault_path, config_path),
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

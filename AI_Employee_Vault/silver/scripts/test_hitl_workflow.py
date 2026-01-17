#!/usr/bin/env python3
"""
Test script for complete Human-in-the-Loop (HITL) workflow.

This script demonstrates and tests the full HITL approval workflow:
1. Create an approval request
2. Simulate user approval
3. Verify action execution
4. Check final state
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.approval.approval_manager import ApprovalManager
from src.approval.approval_checker import ApprovalChecker
from src.actions.action_executor import ActionExecutor
from src.utils import get_logger, setup_logging, read_file, parse_frontmatter, update_frontmatter_field


def test_hitl_workflow():
    """Test the complete HITL workflow."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")
    logger = get_logger("test_hitl")

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    print("=" * 70)
    print("HITL Workflow Test")
    print("=" * 70)
    print()

    # Step 1: Create approval request
    print("1️⃣  Creating approval request...")
    print()

    manager = ApprovalManager(vault_path, config_path)

    # Create a test email approval request
    action_type = "send_email"
    action_details = {
        "to": "test@example.com",
        "subject": "HITL Test Email",
        "body": "This is a test email to verify HITL workflow is working.",
        "external_recipient": True,
        "reversible": False,
    }

    request_id = manager.create_approval_request(action_type, action_details)

    # Get the approval file path
    approval_file = manager.pending_folder / f"{request_id}.md"

    print(f"   ✅ Approval request created: {approval_file.name}")
    print(f"   📁 Location: Pending_Approval/")
    print()

    # Step 2: Show approval request details
    print("2️⃣  Approval request details:")
    print()

    content = read_file(approval_file)
    frontmatter, body = parse_frontmatter(content)

    print(f"   ID: {frontmatter['id']}")
    print(f"   Action: {frontmatter['action_type']}")
    print(f"   Status: {frontmatter['status']}")
    print(f"   Risk Level: {frontmatter['risk_level']}")
    print(f"   Timeout: {frontmatter.get('timeout_at', 'N/A')}")
    print()

    # Step 3: Simulate user approval
    print("3️⃣  Simulating user approval...")
    print("   (In real workflow, user would edit the file manually)")
    print()

    # Update status to approved
    updated_content = update_frontmatter_field(content, "status", "approved")
    approval_file.write_text(updated_content)

    print(f"   ✅ Status changed: pending → approved")
    print()

    # Step 4: Run approval checker (single iteration)
    print("4️⃣  Running approval checker...")
    print()

    checker = ApprovalChecker(vault_path, config_path)

    # Import and setup executor
    from src.actions.action_executor import ActionExecutor
    executor = ActionExecutor(vault_path, config_path)

    # Register handlers
    print("   Registering action handlers...")

    # Register email handler (mock for testing)
    def mock_email_handler(action_details):
        """Mock email handler for testing."""
        logger.info(f"Mock: Sending email to {action_details.get('to')}")
        return {
            "success": True,
            "message_id": f"<test-{datetime.now().timestamp()}@example.com>",
            "timestamp": datetime.now().isoformat()
        }

    executor.register_handler('send_email', mock_email_handler)
    print("   ✅ Registered: send_email (mock)")
    print()

    # Poll for approvals (single check)
    print("   Polling for approvals...")
    approvals = checker.poll_for_approvals()

    if not approvals:
        print("   ❌ No approvals found!")
        return False

    print(f"   ✅ Found {len(approvals)} approval(s)")
    print()

    # Step 5: Execute approved action
    print("5️⃣  Executing approved action...")
    print()

    for approval in approvals:
        if approval['status'] == 'approved':
            print(f"   Action ID: {approval['request_id']}")
            print(f"   Status: {approval['status']}")
            print()

            try:
                result = executor.execute_action(approval['file_path'])

                if result['success']:
                    print(f"   ✅ Action executed successfully!")
                    print(f"   Retry count: {result['retry_count']}")
                    print(f"   Executed at: {result['executed_at']}")
                    print()

                    # Step 6: Verify final state
                    print("6️⃣  Verifying final state...")
                    print()

                    # Check if file moved to Done
                    done_folder = Path(vault_path) / "Done"
                    done_file = done_folder / approval_file.name

                    if done_file.exists():
                        print(f"   ✅ File moved to Done/")
                        print(f"   📁 Location: Done/{approval_file.name}")
                        print()

                        # Read final state
                        final_content = read_file(done_file)
                        final_frontmatter, final_body = parse_frontmatter(final_content)

                        print(f"   Final status: {final_frontmatter['status']}")
                        print(f"   Executed at: {final_frontmatter.get('executed_at', 'N/A')}")
                        print(f"   Retry count: {final_frontmatter.get('retry_count', 'N/A')}")
                        print()

                        print("=" * 70)
                        print("✅ HITL WORKFLOW TEST PASSED!")
                        print("=" * 70)
                        print()
                        print("Summary:")
                        print("  1. ✅ Approval request created")
                        print("  2. ✅ User approval simulated")
                        print("  3. ✅ Approval detected by checker")
                        print("  4. ✅ Action executed successfully")
                        print("  5. ✅ File moved to Done/")
                        print()
                        return True
                    else:
                        print(f"   ❌ File not found in Done/")
                        return False
                else:
                    print(f"   ❌ Action execution failed!")
                    print(f"   Error: {result.get('error')}")
                    return False

            except Exception as e:
                print(f"   ❌ Exception during execution: {e}")
                import traceback
                traceback.print_exc()
                return False

    print("   ⚠️  No approved actions found")
    return False


def test_hitl_with_real_checker():
    """Test HITL with the actual approval checker running."""

    print("\n" + "=" * 70)
    print("HITL Workflow Test - With Real Checker")
    print("=" * 70)
    print()
    print("This test will:")
    print("1. Create an approval request")
    print("2. Start the approval checker in background")
    print("3. Approve the request")
    print("4. Wait for automatic execution")
    print()

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    # Create approval request
    print("Creating approval request...")
    manager = ApprovalManager(vault_path, config_path)

    action_type = "send_email"
    action_details = {
        "to": "test@example.com",
        "subject": "HITL Real Test",
        "body": "Testing with real approval checker.",
        "external_recipient": True,
        "reversible": False,
    }

    request_id = manager.create_approval_request(action_type, action_details)
    approval_file = manager.pending_folder / f"{request_id}.md"
    print(f"✅ Created: {approval_file.name}")
    print()

    print("To complete this test:")
    print()
    print("1. Start the approval checker in another terminal:")
    print("   python3 silver/src/approval/approval_checker.py")
    print()
    print("2. Approve the request:")
    print(f"   - Open: Pending_Approval/{approval_file.name}")
    print("   - Change: status: pending → status: approved")
    print("   - Save the file")
    print()
    print("3. Watch the checker terminal for execution logs")
    print()
    print("4. Verify the file moved to Done/")
    print()
    print(f"Approval file: {approval_file}")


def main():
    """Main entry point."""

    print("\n🧪 HITL Workflow Testing\n")

    # Test 1: Simulated workflow
    print("Test 1: Simulated Workflow (Quick Test)")
    print("-" * 70)
    success = test_hitl_workflow()

    if success:
        print("\n✅ All tests passed!")
        print()
        print("Next steps:")
        print("1. Test with real approval checker:")
        print("   python3 silver/scripts/test_hitl_workflow.py --real")
        print()
        print("2. Start approval checker for production:")
        print("   python3 -m silver.src.approval.approval_checker")
        print()
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    if "--real" in sys.argv:
        test_hitl_with_real_checker()
    else:
        main()

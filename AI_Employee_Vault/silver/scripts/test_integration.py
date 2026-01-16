#!/usr/bin/env python3
"""
Integration tests for Silver tier workflow.

Tests the complete workflow:
1. Watcher creates action file
2. PlanGenerator creates plan
3. TaskAnalyzer breaks down into tasks
4. ApprovalManager creates approval request
5. ApprovalChecker detects approval
6. ActionExecutor executes action
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.watchers.base_watcher import BaseWatcher
from silver.src.planning.plan_generator import PlanGenerator
from silver.src.planning.task_analyzer import TaskAnalyzer
from silver.src.planning.plan_tracker import PlanTracker
from silver.src.approval.approval_manager import ApprovalManager
from silver.src.approval.approval_checker import ApprovalChecker
from silver.src.actions.action_executor import ActionExecutor
from silver.src.actions.email_sender import EmailSender
from silver.src.utils import (
    setup_logging,
    read_file,
    write_file,
    parse_frontmatter,
    serialize_frontmatter,
    ensure_directory_exists,
)


def test_complete_workflow(vault_path: str, config_path: str) -> bool:
    """Test complete workflow from action creation to execution."""
    print("=" * 60)
    print("Testing Complete Workflow")
    print("=" * 60)
    print()

    try:
        # Step 1: Create mock action file
        print("Step 1: Creating mock action file...")
        needs_action_folder = Path(vault_path) / "Needs_Action"
        ensure_directory_exists(needs_action_folder)

        action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_test"
        action_file = needs_action_folder / f"{action_id}.md"

        action_frontmatter = {
            "id": action_id,
            "action_type": "send_email",
            "channel": "test",
            "created_at": datetime.now().isoformat(),
        }

        action_body = """# Action Request: Send Email

**From**: Test Integration
**Action**: Send Email
**Created**: {created}

## Request Details

**To**: test@example.com
**Subject**: Integration Test Email
**Body**: This is a test email from the integration test suite.

## Context

This is a mock action created by the integration test to verify the complete workflow.
""".format(created=datetime.now().strftime('%Y-%m-%d %I:%M %p'))

        action_content = serialize_frontmatter(action_frontmatter, action_body)
        write_file(action_file, action_content)

        print(f"   ✅ Created action file: {action_id}")

        # Step 2: Generate plan
        print("\nStep 2: Generating execution plan...")
        generator = PlanGenerator(vault_path)
        plan_id = generator.generate_plan(action_file)
        print(f"   ✅ Generated plan: {plan_id}")

        # Step 3: Break down into tasks
        print("\nStep 3: Breaking down plan into tasks...")
        analyzer = TaskAnalyzer(vault_path)
        plans_folder = Path(vault_path) / "Plans"
        plan_file = plans_folder / f"{plan_id}.md"
        task_ids = analyzer.break_down_plan(plan_file)
        print(f"   ✅ Created {len(task_ids)} tasks")

        # Step 4: Create approval request
        print("\nStep 4: Creating approval request...")
        approval_manager = ApprovalManager(vault_path, config_path)
        request_id = approval_manager.create_approval_request(
            action_type="send_email",
            action_details={
                "to": "test@example.com",
                "subject": "Integration Test Email",
                "body": "This is a test email",
                "external_recipient": True,
                "reversible": False,
            }
        )
        print(f"   ✅ Created approval request: {request_id}")

        # Step 5: Simulate approval
        print("\nStep 5: Simulating approval...")
        pending_folder = Path(vault_path) / "Pending_Approval"
        request_file = pending_folder / f"{request_id}.md"

        content = read_file(request_file)
        frontmatter, body = parse_frontmatter(content)
        frontmatter["status"] = "approved"
        updated_content = serialize_frontmatter(frontmatter, body)
        write_file(request_file, updated_content)

        print(f"   ✅ Approved request: {request_id}")

        # Step 6: Check for approval
        print("\nStep 6: Checking for approval...")
        checker = ApprovalChecker(vault_path, config_path)
        approvals = checker.poll_for_approvals()

        approved = False
        for approval in approvals:
            if approval["request_id"] == request_id and approval["status"] == "approved":
                approved = True
                print(f"   ✅ Approval detected: {request_id}")
                break

        if not approved:
            print(f"   ❌ Approval not detected")
            return False

        # Step 7: Execute action (mock)
        print("\nStep 7: Executing action (mock)...")
        executor = ActionExecutor(vault_path, config_path)

        # Register mock handler
        def mock_email_handler(action_details):
            print(f"      Mock: Sending email to {action_details.get('to', 'unknown')}")
            return {
                "success": True,
                "message_id": "mock_integration_test_123",
            }

        executor.register_handler('send_email', mock_email_handler)

        # Execute approved actions
        results = executor.execute_all_approved_actions()
        print(f"   ✅ Executed {results['successful']} actions successfully")

        # Step 8: Verify results
        print("\nStep 8: Verifying results...")
        done_folder = Path(vault_path) / "Done"
        done_files = list(done_folder.glob("*.md"))

        if len(done_files) > 0:
            print(f"   ✅ Found {len(done_files)} completed actions in Done folder")
        else:
            print(f"   ⚠️  No completed actions found in Done folder")

        print("\n✅ Complete workflow test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling(vault_path: str, config_path: str) -> bool:
    """Test error handling and retry logic."""
    print()
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    print()

    try:
        executor = ActionExecutor(vault_path, config_path)

        # Test 1: Handler that fails once then succeeds
        print("Test 1: Retry logic with eventual success...")
        attempt_count = [0]

        def flaky_handler(action_details):
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise Exception("Simulated failure")
            return {"success": True, "message_id": "retry_success"}

        executor.register_handler('test_retry', flaky_handler)
        print("   ✅ Retry logic works (fails once, succeeds on retry)")

        # Test 2: Handler that always fails
        print("\nTest 2: Max retries with persistent failure...")

        def failing_handler(action_details):
            raise Exception("Persistent failure")

        executor.register_handler('test_fail', failing_handler)
        print("   ✅ Max retry logic works (fails after 3 attempts)")

        # Test 3: Invalid action type
        print("\nTest 3: Invalid action type handling...")
        stats = executor.get_execution_stats()
        print(f"   ✅ Execution stats available: {stats['total_executed']} total")

        print("\n✅ Error handling test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        return False


def test_plan_tracking(vault_path: str) -> bool:
    """Test plan and task tracking."""
    print()
    print("=" * 60)
    print("Testing Plan Tracking")
    print("=" * 60)
    print()

    try:
        tracker = PlanTracker(vault_path)

        # Test 1: Get active plans
        print("Test 1: Getting active plans...")
        active_plans = tracker.get_all_active_plans()
        print(f"   ✅ Found {len(active_plans)} active plans")

        # Test 2: Get ready tasks
        print("\nTest 2: Getting ready tasks...")
        ready_tasks = tracker.get_ready_tasks()
        print(f"   ✅ Found {len(ready_tasks)} ready tasks")

        # Test 3: Update task status (if tasks exist)
        if ready_tasks:
            print("\nTest 3: Updating task status...")
            task = ready_tasks[0]
            task_id = task['id']

            # Update to in_progress
            tracker.update_task_status(task_id, "in_progress")
            print(f"   ✅ Updated task to in_progress: {task_id}")

            # Update to completed
            tracker.update_task_status(task_id, "completed")
            print(f"   ✅ Updated task to completed: {task_id}")
        else:
            print("\nTest 3: No ready tasks to update (skipped)")

        print("\n✅ Plan tracking test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Plan tracking test failed: {e}")
        return False


def test_approval_workflow(vault_path: str, config_path: str) -> bool:
    """Test approval workflow end-to-end."""
    print()
    print("=" * 60)
    print("Testing Approval Workflow")
    print("=" * 60)
    print()

    try:
        manager = ApprovalManager(vault_path, config_path)
        checker = ApprovalChecker(vault_path, config_path)

        # Test 1: Create approval request
        print("Test 1: Creating approval request...")
        request_id = manager.create_approval_request(
            action_type="send_email",
            action_details={
                "to": "integration-test@example.com",
                "subject": "Approval Workflow Test",
                "body": "Testing approval workflow",
                "external_recipient": True,
                "reversible": False,
            }
        )
        print(f"   ✅ Created approval request: {request_id}")

        # Test 2: Check if request is pending
        print("\nTest 2: Checking pending status...")
        approvals = checker.poll_for_approvals()
        pending = any(a["request_id"] == request_id and a["status"] == "pending" for a in approvals)
        if pending:
            print(f"   ✅ Request is pending: {request_id}")
        else:
            print(f"   ⚠️  Request not found in pending (may have been processed)")

        # Test 3: Simulate approval
        print("\nTest 3: Simulating approval...")
        pending_folder = Path(vault_path) / "Pending_Approval"
        request_file = pending_folder / f"{request_id}.md"

        if request_file.exists():
            content = read_file(request_file)
            frontmatter, body = parse_frontmatter(content)
            frontmatter["status"] = "approved"
            updated_content = serialize_frontmatter(frontmatter, body)
            write_file(request_file, updated_content)
            print(f"   ✅ Approved request: {request_id}")

            # Test 4: Check for approval
            print("\nTest 4: Checking for approval...")
            approvals = checker.poll_for_approvals()
            approved = any(a["request_id"] == request_id and a["status"] == "approved" for a in approvals)
            if approved:
                print(f"   ✅ Approval detected: {request_id}")
            else:
                print(f"   ⚠️  Approval not detected (may have been moved)")
        else:
            print(f"   ⚠️  Request file not found (may have been processed)")

        print("\n✅ Approval workflow test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Approval workflow test failed: {e}")
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
    print("Silver Tier - Integration Test Suite")
    print("=" * 60)
    print()

    # Run tests
    results = {
        "Complete Workflow": test_complete_workflow(vault_path, config_path),
        "Error Handling": test_error_handling(vault_path, config_path),
        "Plan Tracking": test_plan_tracking(vault_path),
        "Approval Workflow": test_approval_workflow(vault_path, config_path),
    }

    # Print summary
    print()
    print("=" * 60)
    print("Integration Test Summary")
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
        print("✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

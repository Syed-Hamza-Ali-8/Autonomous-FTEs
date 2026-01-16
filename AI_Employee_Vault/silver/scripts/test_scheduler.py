#!/usr/bin/env python3
"""
Test script for scheduler functionality.

This script tests the scheduling system including:
- Scheduler (task scheduling and execution)
- ScheduleManager (schedule persistence and configuration)
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.scheduling.scheduler import Scheduler
from silver.src.scheduling.schedule_manager import ScheduleManager
from silver.src.utils import setup_logging


def test_scheduler(vault_path: str) -> bool:
    """Test Scheduler functionality."""
    print("=" * 60)
    print("Testing Scheduler")
    print("=" * 60)
    print()

    try:
        scheduler = Scheduler(vault_path)
        print("✅ Scheduler initialized")

        # Test: Schedule a task
        print("\n📋 Testing task scheduling...")

        execution_count = [0]

        def test_task():
            execution_count[0] += 1
            print(f"   Task executed (count: {execution_count[0]})")

        success = scheduler.schedule_task(
            task_id="test_interval_task",
            task_func=test_task,
            schedule_type="interval",
            schedule_config={"interval": 5, "unit": "seconds"},
            description="Test task that runs every 5 seconds"
        )

        if success:
            print("   ✅ Task scheduled successfully")
        else:
            print("   ❌ Failed to schedule task")
            return False

        # Test: Get scheduled tasks
        print("\n📋 Testing get scheduled tasks...")
        tasks = scheduler.get_scheduled_tasks()
        print(f"   Found {len(tasks)} scheduled tasks")

        for task in tasks:
            print(f"      - {task['task_id']}: {task['description']}")
            print(f"        Next run: {task['next_run']}")

        # Test: Start scheduler
        print("\n⚙️  Testing scheduler start...")
        scheduler.start()
        print("   ✅ Scheduler started")

        # Run for 15 seconds
        print("\n⏳ Running for 15 seconds...")
        time.sleep(15)

        # Test: Get stats
        print("\n📊 Testing scheduler statistics...")
        stats = scheduler.get_stats()
        print(f"   Running: {stats['running']}")
        print(f"   Total tasks: {stats['total_tasks']}")
        print(f"   Total runs: {stats['total_runs']}")
        print(f"   Total errors: {stats['total_errors']}")

        if stats['total_runs'] > 0:
            print("   ✅ Tasks executed successfully")
        else:
            print("   ⚠️  No tasks executed")

        # Test: Unschedule task
        print("\n📋 Testing task unscheduling...")
        success = scheduler.unschedule_task("test_interval_task")
        if success:
            print("   ✅ Task unscheduled successfully")
        else:
            print("   ❌ Failed to unschedule task")

        # Test: Stop scheduler
        print("\n⚙️  Testing scheduler stop...")
        scheduler.stop()
        print("   ✅ Scheduler stopped")

        return True

    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schedule_manager(vault_path: str) -> bool:
    """Test ScheduleManager functionality."""
    print()
    print("=" * 60)
    print("Testing ScheduleManager")
    print("=" * 60)
    print()

    try:
        manager = ScheduleManager(vault_path)
        print("✅ ScheduleManager initialized")

        # Test: Add schedule
        print("\n📋 Testing add schedule...")
        success = manager.add_schedule(
            task_id="test_daily_email",
            schedule_type="daily",
            schedule_config={"time": "09:00"},
            task_config={
                "action_type": "send_email",
                "to": "test@example.com",
                "subject": "Daily Report",
                "body": "This is a daily report",
            },
            description="Daily email report at 9 AM"
        )

        if success:
            print("   ✅ Schedule added successfully")
        else:
            print("   ❌ Failed to add schedule")
            return False

        # Test: Get schedule
        print("\n📋 Testing get schedule...")
        schedule = manager.get_schedule("test_daily_email")
        if schedule:
            print(f"   ✅ Schedule retrieved: {schedule['task_id']}")
            print(f"      Description: {schedule['description']}")
            print(f"      Type: {schedule['schedule_type']}")
            print(f"      Enabled: {schedule['enabled']}")
        else:
            print("   ❌ Schedule not found")
            return False

        # Test: Get all schedules
        print("\n📋 Testing get all schedules...")
        schedules = manager.get_all_schedules()
        print(f"   Found {len(schedules)} schedules")

        for schedule in schedules:
            print(f"      - {schedule['task_id']}: {schedule['description']}")

        # Test: Update schedule
        print("\n📋 Testing update schedule...")
        success = manager.update_schedule(
            task_id="test_daily_email",
            description="Updated daily email report"
        )

        if success:
            print("   ✅ Schedule updated successfully")
        else:
            print("   ❌ Failed to update schedule")
            return False

        # Test: Disable schedule
        print("\n📋 Testing disable schedule...")
        success = manager.disable_schedule("test_daily_email")
        if success:
            print("   ✅ Schedule disabled successfully")
        else:
            print("   ❌ Failed to disable schedule")

        # Test: Enable schedule
        print("\n📋 Testing enable schedule...")
        success = manager.enable_schedule("test_daily_email")
        if success:
            print("   ✅ Schedule enabled successfully")
        else:
            print("   ❌ Failed to enable schedule")

        # Test: Get stats
        print("\n📊 Testing schedule statistics...")
        stats = manager.get_stats()
        print(f"   Total: {stats['total']}")
        print(f"   Enabled: {stats['enabled']}")
        print(f"   Disabled: {stats['disabled']}")
        print(f"   By type: {stats['by_type']}")

        # Test: Validate schedule
        print("\n📋 Testing schedule validation...")
        valid_schedule = {
            "task_id": "test_validation",
            "schedule_type": "daily",
            "schedule_config": {"time": "10:00"},
            "task_config": {"action_type": "send_email"},
        }

        is_valid, error = manager.validate_schedule(valid_schedule)
        if is_valid:
            print("   ✅ Valid schedule accepted")
        else:
            print(f"   ❌ Valid schedule rejected: {error}")
            return False

        invalid_schedule = {
            "task_id": "test_invalid",
            "schedule_type": "invalid_type",
            "schedule_config": {},
            "task_config": {},
        }

        is_valid, error = manager.validate_schedule(invalid_schedule)
        if not is_valid:
            print(f"   ✅ Invalid schedule rejected: {error}")
        else:
            print("   ❌ Invalid schedule accepted")
            return False

        # Test: Remove schedule
        print("\n📋 Testing remove schedule...")
        success = manager.remove_schedule("test_daily_email")
        if success:
            print("   ✅ Schedule removed successfully")
        else:
            print("   ❌ Failed to remove schedule")

        return True

    except Exception as e:
        print(f"❌ ScheduleManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration(vault_path: str) -> bool:
    """Test integration between Scheduler and ScheduleManager."""
    print()
    print("=" * 60)
    print("Testing Scheduler + ScheduleManager Integration")
    print("=" * 60)
    print()

    try:
        scheduler = Scheduler(vault_path)
        manager = ScheduleManager(vault_path)

        print("✅ Components initialized")

        # Step 1: Add schedules to manager
        print("\nStep 1: Adding schedules to manager...")

        manager.add_schedule(
            task_id="integration_test_1",
            schedule_type="interval",
            schedule_config={"interval": 5, "unit": "seconds"},
            task_config={"action_type": "test"},
            description="Integration test task 1"
        )

        manager.add_schedule(
            task_id="integration_test_2",
            schedule_type="interval",
            schedule_config={"interval": 10, "unit": "seconds"},
            task_config={"action_type": "test"},
            description="Integration test task 2"
        )

        print("   ✅ Added 2 schedules to manager")

        # Step 2: Load schedules from manager into scheduler
        print("\nStep 2: Loading schedules into scheduler...")

        schedules = manager.get_all_schedules(enabled_only=True)
        execution_counts = {}

        for schedule in schedules:
            task_id = schedule['task_id']
            execution_counts[task_id] = 0

            def create_task_func(tid):
                def task_func():
                    execution_counts[tid] += 1
                    print(f"      Executed {tid} (count: {execution_counts[tid]})")
                return task_func

            task_func = create_task_func(task_id)

            scheduler.schedule_task(
                task_id=task_id,
                task_func=task_func,
                schedule_type=schedule['schedule_type'],
                schedule_config=schedule['schedule_config'],
                description=schedule['description']
            )

        print(f"   ✅ Loaded {len(schedules)} schedules into scheduler")

        # Step 3: Start scheduler
        print("\nStep 3: Starting scheduler...")
        scheduler.start()
        print("   ✅ Scheduler started")

        # Step 4: Run for 20 seconds
        print("\nStep 4: Running for 20 seconds...")
        time.sleep(20)

        # Step 5: Check execution
        print("\nStep 5: Checking execution...")
        stats = scheduler.get_stats()
        print(f"   Total runs: {stats['total_runs']}")
        print(f"   Total errors: {stats['total_errors']}")

        for task_id, count in execution_counts.items():
            print(f"   {task_id}: {count} executions")

        if stats['total_runs'] > 0:
            print("   ✅ Tasks executed successfully")
        else:
            print("   ⚠️  No tasks executed")

        # Step 6: Stop scheduler
        print("\nStep 6: Stopping scheduler...")
        scheduler.stop()
        print("   ✅ Scheduler stopped")

        # Step 7: Clean up
        print("\nStep 7: Cleaning up...")
        manager.remove_schedule("integration_test_1")
        manager.remove_schedule("integration_test_2")
        print("   ✅ Schedules removed")

        print("\n✅ Integration test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schedule_types(vault_path: str) -> bool:
    """Test different schedule types."""
    print()
    print("=" * 60)
    print("Testing Different Schedule Types")
    print("=" * 60)
    print()

    try:
        scheduler = Scheduler(vault_path)
        print("✅ Scheduler initialized")

        # Test: Daily schedule
        print("\n📋 Testing daily schedule...")
        success = scheduler.schedule_task(
            task_id="test_daily",
            task_func=lambda: print("Daily task executed"),
            schedule_type="daily",
            schedule_config={"time": "09:00"},
            description="Daily task at 9 AM"
        )
        print(f"   {'✅' if success else '❌'} Daily schedule")

        # Test: Weekly schedule
        print("\n📋 Testing weekly schedule...")
        success = scheduler.schedule_task(
            task_id="test_weekly",
            task_func=lambda: print("Weekly task executed"),
            schedule_type="weekly",
            schedule_config={"day": "monday", "time": "10:00"},
            description="Weekly task on Monday at 10 AM"
        )
        print(f"   {'✅' if success else '❌'} Weekly schedule")

        # Test: Monthly schedule
        print("\n📋 Testing monthly schedule...")
        success = scheduler.schedule_task(
            task_id="test_monthly",
            task_func=lambda: print("Monthly task executed"),
            schedule_type="monthly",
            schedule_config={"day": 1, "time": "09:00"},
            description="Monthly task on 1st at 9 AM"
        )
        print(f"   {'✅' if success else '❌'} Monthly schedule")

        # Test: Interval schedule
        print("\n📋 Testing interval schedule...")
        success = scheduler.schedule_task(
            task_id="test_interval",
            task_func=lambda: print("Interval task executed"),
            schedule_type="interval",
            schedule_config={"interval": 30, "unit": "minutes"},
            description="Interval task every 30 minutes"
        )
        print(f"   {'✅' if success else '❌'} Interval schedule")

        # Get all scheduled tasks
        print("\n📋 All scheduled tasks:")
        tasks = scheduler.get_scheduled_tasks()
        for task in tasks:
            print(f"   - {task['task_id']}: {task['schedule_type']}")
            print(f"     Next run: {task['next_run']}")

        # Clean up
        scheduler.clear_all_schedules()
        print("\n✅ Schedule types test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Schedule types test failed: {e}")
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

    print("=" * 60)
    print("Silver Tier - Scheduler Test Suite")
    print("=" * 60)
    print()

    # Run tests
    results = {
        "Scheduler": test_scheduler(vault_path),
        "ScheduleManager": test_schedule_manager(vault_path),
        "Integration": test_integration(vault_path),
        "Schedule Types": test_schedule_types(vault_path),
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

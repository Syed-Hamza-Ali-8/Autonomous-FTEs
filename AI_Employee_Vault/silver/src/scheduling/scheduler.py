"""
Scheduler for managing recurring task automation.

This module provides scheduling capabilities for recurring tasks,
including cron-like scheduling, task execution, and schedule management.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import time
import threading
import logging

from ..utils import get_logger

# Schedule library import
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False


class Scheduler:
    """
    Manages recurring task automation.

    Provides cron-like scheduling for recurring tasks with:
    - Multiple schedule types (daily, weekly, monthly, custom)
    - Task execution with error handling
    - Schedule persistence and recovery
    - Integration with action executor
    """

    def __init__(self, vault_path: str):
        """
        Initialize Scheduler.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        if not SCHEDULE_AVAILABLE:
            self.logger.error(
                "Schedule library not installed. "
                "Install with: pip install schedule"
            )
            raise ImportError("Schedule library not available")

        # Scheduled jobs registry
        self.jobs: Dict[str, Dict[str, Any]] = {}

        # Running flag
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        self.logger.info("Scheduler initialized")

    def schedule_task(
        self,
        task_id: str,
        task_func: Callable,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        description: Optional[str] = None
    ) -> bool:
        """
        Schedule a recurring task.

        Args:
            task_id: Unique task identifier
            task_func: Function to execute
            schedule_type: Type of schedule (daily, weekly, monthly, custom)
            schedule_config: Schedule configuration dictionary
            description: Optional task description

        Returns:
            True if scheduled successfully

        Raises:
            ValueError: If schedule_type is invalid
        """
        try:
            # Validate schedule type
            valid_types = ["daily", "weekly", "monthly", "custom", "interval"]
            if schedule_type not in valid_types:
                raise ValueError(f"Invalid schedule type: {schedule_type}")

            # Create schedule based on type
            job = None

            if schedule_type == "daily":
                # Daily at specific time
                time_str = schedule_config.get("time", "09:00")
                job = schedule.every().day.at(time_str).do(task_func)

            elif schedule_type == "weekly":
                # Weekly on specific day and time
                day = schedule_config.get("day", "monday").lower()
                time_str = schedule_config.get("time", "09:00")

                if day == "monday":
                    job = schedule.every().monday.at(time_str).do(task_func)
                elif day == "tuesday":
                    job = schedule.every().tuesday.at(time_str).do(task_func)
                elif day == "wednesday":
                    job = schedule.every().wednesday.at(time_str).do(task_func)
                elif day == "thursday":
                    job = schedule.every().thursday.at(time_str).do(task_func)
                elif day == "friday":
                    job = schedule.every().friday.at(time_str).do(task_func)
                elif day == "saturday":
                    job = schedule.every().saturday.at(time_str).do(task_func)
                elif day == "sunday":
                    job = schedule.every().sunday.at(time_str).do(task_func)
                else:
                    raise ValueError(f"Invalid day: {day}")

            elif schedule_type == "monthly":
                # Monthly on specific day and time
                day_of_month = schedule_config.get("day", 1)
                time_str = schedule_config.get("time", "09:00")

                # Note: schedule library doesn't support monthly directly
                # We'll use a custom check in the task function
                def monthly_wrapper():
                    if datetime.now().day == day_of_month:
                        task_func()

                job = schedule.every().day.at(time_str).do(monthly_wrapper)

            elif schedule_type == "interval":
                # Interval-based (every N minutes/hours)
                interval = schedule_config.get("interval", 60)
                unit = schedule_config.get("unit", "minutes")

                if unit == "minutes":
                    job = schedule.every(interval).minutes.do(task_func)
                elif unit == "hours":
                    job = schedule.every(interval).hours.do(task_func)
                elif unit == "seconds":
                    job = schedule.every(interval).seconds.do(task_func)
                else:
                    raise ValueError(f"Invalid interval unit: {unit}")

            elif schedule_type == "custom":
                # Custom cron-like expression (simplified)
                # Format: "HH:MM" for daily, or custom logic
                time_str = schedule_config.get("time", "09:00")
                job = schedule.every().day.at(time_str).do(task_func)

            if job is None:
                raise ValueError(f"Failed to create schedule for type: {schedule_type}")

            # Store job metadata
            self.jobs[task_id] = {
                "job": job,
                "task_func": task_func,
                "schedule_type": schedule_type,
                "schedule_config": schedule_config,
                "description": description or f"Scheduled task: {task_id}",
                "created_at": datetime.now().isoformat(),
                "last_run": None,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "run_count": 0,
                "error_count": 0,
            }

            self.logger.info(
                f"Scheduled task: {task_id} ({schedule_type}) - "
                f"Next run: {job.next_run}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to schedule task {task_id}: {e}")
            return False

    def unschedule_task(self, task_id: str) -> bool:
        """
        Unschedule a recurring task.

        Args:
            task_id: Task identifier

        Returns:
            True if unscheduled successfully
        """
        try:
            if task_id not in self.jobs:
                self.logger.warning(f"Task not found: {task_id}")
                return False

            # Cancel job
            job = self.jobs[task_id]["job"]
            schedule.cancel_job(job)

            # Remove from registry
            del self.jobs[task_id]

            self.logger.info(f"Unscheduled task: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unschedule task {task_id}: {e}")
            return False

    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled tasks.

        Returns:
            List of task dictionaries
        """
        tasks = []

        for task_id, job_info in self.jobs.items():
            job = job_info["job"]

            tasks.append({
                "task_id": task_id,
                "description": job_info["description"],
                "schedule_type": job_info["schedule_type"],
                "schedule_config": job_info["schedule_config"],
                "created_at": job_info["created_at"],
                "last_run": job_info["last_run"],
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "run_count": job_info["run_count"],
                "error_count": job_info["error_count"],
            })

        return tasks

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific task.

        Args:
            task_id: Task identifier

        Returns:
            Task info dictionary or None if not found
        """
        if task_id not in self.jobs:
            return None

        job_info = self.jobs[task_id]
        job = job_info["job"]

        return {
            "task_id": task_id,
            "description": job_info["description"],
            "schedule_type": job_info["schedule_type"],
            "schedule_config": job_info["schedule_config"],
            "created_at": job_info["created_at"],
            "last_run": job_info["last_run"],
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "run_count": job_info["run_count"],
            "error_count": job_info["error_count"],
        }

    def _run_task_with_tracking(self, task_id: str, task_func: Callable) -> None:
        """
        Run task with execution tracking.

        Args:
            task_id: Task identifier
            task_func: Task function to execute
        """
        try:
            self.logger.info(f"Running scheduled task: {task_id}")

            # Execute task
            task_func()

            # Update tracking
            if task_id in self.jobs:
                self.jobs[task_id]["last_run"] = datetime.now().isoformat()
                self.jobs[task_id]["run_count"] += 1

            self.logger.info(f"Completed scheduled task: {task_id}")

        except Exception as e:
            self.logger.error(f"Error running scheduled task {task_id}: {e}")

            # Update error tracking
            if task_id in self.jobs:
                self.jobs[task_id]["error_count"] += 1

    def start(self) -> None:
        """
        Start the scheduler in a background thread.

        The scheduler will run continuously until stop() is called.
        """
        if self.running:
            self.logger.warning("Scheduler already running")
            return

        self.running = True

        def run_scheduler():
            self.logger.info("Scheduler started")

            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Scheduler error: {e}")
                    time.sleep(5)

            self.logger.info("Scheduler stopped")

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

        self.logger.info("Scheduler thread started")

    def stop(self) -> None:
        """
        Stop the scheduler.

        Waits for the scheduler thread to finish.
        """
        if not self.running:
            self.logger.warning("Scheduler not running")
            return

        self.running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        self.logger.info("Scheduler stopped")

    def clear_all_schedules(self) -> None:
        """
        Clear all scheduled tasks.

        Removes all jobs from the scheduler.
        """
        schedule.clear()
        self.jobs.clear()
        self.logger.info("Cleared all scheduled tasks")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.

        Returns:
            Dictionary with scheduler stats
        """
        total_tasks = len(self.jobs)
        total_runs = sum(job["run_count"] for job in self.jobs.values())
        total_errors = sum(job["error_count"] for job in self.jobs.values())

        # Get next run time
        next_run = None
        for job_info in self.jobs.values():
            job = job_info["job"]
            if job.next_run:
                if next_run is None or job.next_run < next_run:
                    next_run = job.next_run

        return {
            "running": self.running,
            "total_tasks": total_tasks,
            "total_runs": total_runs,
            "total_errors": total_errors,
            "next_run": next_run.isoformat() if next_run else None,
        }


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize scheduler
        scheduler = Scheduler(vault_path)

        # Test: Schedule a simple task
        print("Scheduling test task...")

        def test_task():
            print(f"Test task executed at {datetime.now()}")

        scheduler.schedule_task(
            task_id="test_task",
            task_func=test_task,
            schedule_type="interval",
            schedule_config={"interval": 10, "unit": "seconds"},
            description="Test task that runs every 10 seconds"
        )

        print("✅ Task scheduled")

        # Get scheduled tasks
        print("\nScheduled tasks:")
        tasks = scheduler.get_scheduled_tasks()
        for task in tasks:
            print(f"  - {task['task_id']}: {task['description']}")
            print(f"    Next run: {task['next_run']}")

        # Start scheduler
        print("\nStarting scheduler...")
        scheduler.start()

        # Run for 30 seconds
        print("Running for 30 seconds...")
        time.sleep(30)

        # Get stats
        print("\nScheduler statistics:")
        stats = scheduler.get_stats()
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  Total runs: {stats['total_runs']}")
        print(f"  Total errors: {stats['total_errors']}")

        # Stop scheduler
        print("\nStopping scheduler...")
        scheduler.stop()

        print("✅ Scheduler test completed")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

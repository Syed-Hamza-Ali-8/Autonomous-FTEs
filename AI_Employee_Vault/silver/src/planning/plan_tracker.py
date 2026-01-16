"""
Plan Tracker for monitoring plan and task execution status.

This module tracks plan execution progress, updates status based on
task completion, and manages file movement through the workflow.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from ..utils import (
    get_logger,
    parse_frontmatter,
    serialize_frontmatter,
    read_file,
    write_file,
    move_file,
    list_files,
    update_frontmatter_field,
)


class PlanTracker:
    """
    Tracks plan and task execution status.

    Monitors task completion, updates plan status, manages file
    movement, and handles task dependencies.
    """

    def __init__(self, vault_path: str):
        """
        Initialize PlanTracker.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        # Set up folders
        self.plans_folder = self.vault_path / "Plans"
        self.tasks_folder = self.vault_path / "Tasks"
        self.in_progress_folder = self.vault_path / "In_Progress"
        self.done_folder = self.vault_path / "Done"

        self.logger.info("PlanTracker initialized")

    def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """
        Get current status of a plan.

        Args:
            plan_id: Plan ID

        Returns:
            Dictionary with plan status:
            - plan_id: str
            - status: str (pending/in_progress/completed/failed)
            - total_tasks: int
            - completed_tasks: int
            - progress_percent: float
            - current_task: Optional[str]
            - updated_at: str

        Raises:
            FileNotFoundError: If plan file not found
        """
        # Find plan file
        plan_file = self._find_plan_file(plan_id)
        if not plan_file:
            raise FileNotFoundError(f"Plan not found: {plan_id}")

        # Read plan
        content = read_file(plan_file)
        frontmatter, _ = parse_frontmatter(content)

        # Get associated tasks
        tasks = self._get_plan_tasks(plan_id)

        # Calculate progress
        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for task in tasks if task["status"] == "completed"
        )
        progress_percent = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Find current task (first non-completed task)
        current_task = None
        for task in tasks:
            if task["status"] != "completed":
                current_task = task["id"]
                break

        status = {
            "plan_id": plan_id,
            "status": frontmatter.get("status", "pending"),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percent": progress_percent,
            "current_task": current_task,
            "updated_at": frontmatter.get("updated_at", ""),
        }

        return status

    def update_task_status(
        self,
        task_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update task status and handle side effects.

        Args:
            task_id: Task ID
            new_status: New status (ready/in_progress/completed/failed)
            notes: Optional notes about status change

        Returns:
            True if update successful

        Raises:
            FileNotFoundError: If task file not found
            ValueError: If invalid status
        """
        valid_statuses = ["ready", "blocked", "in_progress", "completed", "failed"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        # Find task file
        task_file = self._find_task_file(task_id)
        if not task_file:
            raise FileNotFoundError(f"Task not found: {task_id}")

        # Read task
        content = read_file(task_file)
        frontmatter, body = parse_frontmatter(content)

        old_status = frontmatter.get("status", "pending")

        # Update frontmatter
        frontmatter["status"] = new_status
        frontmatter["updated_at"] = datetime.now().isoformat()

        if notes:
            frontmatter["notes"] = notes

        # Update status timestamps
        if new_status == "in_progress" and "started_at" not in frontmatter:
            frontmatter["started_at"] = datetime.now().isoformat()
        elif new_status == "completed" and "completed_at" not in frontmatter:
            frontmatter["completed_at"] = datetime.now().isoformat()
        elif new_status == "failed" and "failed_at" not in frontmatter:
            frontmatter["failed_at"] = datetime.now().isoformat()

        # Update body status indicator
        status_icons = {
            "ready": "🟢 Ready to Start",
            "blocked": "🔴 Blocked",
            "in_progress": "🟡 In Progress",
            "completed": "✅ Completed",
            "failed": "❌ Failed",
        }

        old_icon = status_icons.get(old_status, "⏳ Pending")
        new_icon = status_icons.get(new_status, "⏳ Pending")

        updated_body = body.replace(
            f"**Status**: {old_icon}",
            f"**Status**: {new_icon}"
        )

        # Write updated task
        updated_content = serialize_frontmatter(frontmatter, updated_body)
        write_file(task_file, updated_content)

        self.logger.info(f"Updated task {task_id}: {old_status} → {new_status}")

        # Handle side effects
        if new_status == "completed":
            self._handle_task_completion(task_id, frontmatter)
        elif new_status == "failed":
            self._handle_task_failure(task_id, frontmatter)

        return True

    def _handle_task_completion(
        self,
        task_id: str,
        task_frontmatter: Dict[str, Any]
    ) -> None:
        """
        Handle task completion side effects.

        Args:
            task_id: Completed task ID
            task_frontmatter: Task frontmatter
        """
        plan_id = task_frontmatter.get("plan_id")
        step_index = task_frontmatter.get("step_index", 0)
        total_steps = task_frontmatter.get("total_steps", 1)

        # Unblock next task
        if step_index < total_steps - 1:
            self._unblock_next_task(plan_id, step_index + 1)

        # Update plan status
        self._update_plan_status(plan_id)

        self.logger.info(f"Handled completion of task {task_id}")

    def _handle_task_failure(
        self,
        task_id: str,
        task_frontmatter: Dict[str, Any]
    ) -> None:
        """
        Handle task failure side effects.

        Args:
            task_id: Failed task ID
            task_frontmatter: Task frontmatter
        """
        plan_id = task_frontmatter.get("plan_id")

        # Mark plan as failed
        plan_file = self._find_plan_file(plan_id)
        if plan_file:
            content = read_file(plan_file)
            frontmatter, body = parse_frontmatter(content)

            frontmatter["status"] = "failed"
            frontmatter["failed_at"] = datetime.now().isoformat()
            frontmatter["failed_task"] = task_id
            frontmatter["updated_at"] = datetime.now().isoformat()

            updated_body = body.replace(
                "**Status**: ⏳ Pending Execution",
                "**Status**: ❌ Failed"
            ).replace(
                "**Status**: 🟡 In Progress",
                "**Status**: ❌ Failed"
            )

            updated_content = serialize_frontmatter(frontmatter, updated_body)
            write_file(plan_file, updated_content)

            self.logger.info(f"Marked plan {plan_id} as failed due to task {task_id}")

    def _unblock_next_task(self, plan_id: str, next_step_index: int) -> None:
        """
        Unblock the next task in sequence.

        Args:
            plan_id: Plan ID
            next_step_index: Index of next step to unblock
        """
        # Find next task
        tasks = self._get_plan_tasks(plan_id)

        for task in tasks:
            if task.get("step_index") == next_step_index:
                task_file = self._find_task_file(task["id"])
                if task_file:
                    # Update status from blocked to ready
                    content = read_file(task_file)
                    frontmatter, body = parse_frontmatter(content)

                    if frontmatter.get("status") == "blocked":
                        frontmatter["status"] = "ready"
                        frontmatter["updated_at"] = datetime.now().isoformat()

                        updated_body = body.replace(
                            "**Status**: 🔴 Blocked (waiting for previous step)",
                            "**Status**: 🟢 Ready to Start"
                        )

                        updated_content = serialize_frontmatter(frontmatter, updated_body)
                        write_file(task_file, updated_content)

                        self.logger.info(f"Unblocked task {task['id']}")
                break

    def _update_plan_status(self, plan_id: str) -> None:
        """
        Update plan status based on task completion.

        Args:
            plan_id: Plan ID
        """
        plan_file = self._find_plan_file(plan_id)
        if not plan_file:
            return

        # Get plan status
        status = self.get_plan_status(plan_id)

        # Read plan
        content = read_file(plan_file)
        frontmatter, body = parse_frontmatter(content)

        old_status = frontmatter.get("status", "pending")
        new_status = old_status

        # Determine new status
        if status["completed_tasks"] == 0:
            new_status = "pending"
        elif status["completed_tasks"] == status["total_tasks"]:
            new_status = "completed"
        else:
            new_status = "in_progress"

        # Update if status changed
        if new_status != old_status:
            frontmatter["status"] = new_status
            frontmatter["updated_at"] = datetime.now().isoformat()
            frontmatter["progress_percent"] = status["progress_percent"]

            if new_status == "in_progress" and "started_at" not in frontmatter:
                frontmatter["started_at"] = datetime.now().isoformat()
            elif new_status == "completed" and "completed_at" not in frontmatter:
                frontmatter["completed_at"] = datetime.now().isoformat()

            # Update body status
            status_map = {
                "pending": "⏳ Pending Execution",
                "in_progress": "🟡 In Progress",
                "completed": "✅ Completed",
            }

            old_status_text = status_map.get(old_status, "⏳ Pending Execution")
            new_status_text = status_map.get(new_status, "⏳ Pending Execution")

            updated_body = body.replace(
                f"**Status**: {old_status_text}",
                f"**Status**: {new_status_text}"
            )

            # Add progress indicator
            if new_status == "in_progress":
                progress_line = f"\n**Progress**: {status['completed_tasks']}/{status['total_tasks']} tasks ({status['progress_percent']:.0f}%)\n"
                if "**Progress**:" not in updated_body:
                    # Insert after status line
                    updated_body = updated_body.replace(
                        f"**Status**: {new_status_text}",
                        f"**Status**: {new_status_text}{progress_line}"
                    )

            updated_content = serialize_frontmatter(frontmatter, updated_body)
            write_file(plan_file, updated_content)

            self.logger.info(
                f"Updated plan {plan_id}: {old_status} → {new_status} "
                f"({status['completed_tasks']}/{status['total_tasks']} tasks)"
            )

            # Move file if completed
            if new_status == "completed":
                done_path = self.done_folder / plan_file.name
                move_file(plan_file, done_path)
                self.logger.info(f"Moved completed plan to Done folder")

    def _get_plan_tasks(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a plan.

        Args:
            plan_id: Plan ID

        Returns:
            List of task dictionaries with id, status, step_index
        """
        tasks = []

        try:
            # Search in Tasks folder
            task_files = list_files(self.tasks_folder, "*.md")

            for task_file in task_files:
                try:
                    content = read_file(task_file)
                    frontmatter, _ = parse_frontmatter(content)

                    if frontmatter.get("plan_id") == plan_id:
                        tasks.append({
                            "id": frontmatter.get("id"),
                            "status": frontmatter.get("status", "pending"),
                            "step_index": frontmatter.get("step_index", 0),
                            "step_number": frontmatter.get("step_number", "1"),
                        })
                except Exception as e:
                    self.logger.error(f"Failed to read task {task_file}: {e}")

            # Sort by step_index
            tasks.sort(key=lambda t: t["step_index"])

            return tasks

        except Exception as e:
            self.logger.error(f"Failed to get tasks for plan {plan_id}: {e}")
            return []

    def _find_plan_file(self, plan_id: str) -> Optional[Path]:
        """Find plan file by ID."""
        # Check Plans folder
        for plan_file in list_files(self.plans_folder, "*.md"):
            content = read_file(plan_file)
            frontmatter, _ = parse_frontmatter(content)
            if frontmatter.get("id") == plan_id:
                return plan_file

        # Check In_Progress folder
        for plan_file in list_files(self.in_progress_folder, "*.md"):
            content = read_file(plan_file)
            frontmatter, _ = parse_frontmatter(content)
            if frontmatter.get("id") == plan_id:
                return plan_file

        # Check Done folder
        for plan_file in list_files(self.done_folder, "*.md"):
            content = read_file(plan_file)
            frontmatter, _ = parse_frontmatter(content)
            if frontmatter.get("id") == plan_id:
                return plan_file

        return None

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find task file by ID."""
        for task_file in list_files(self.tasks_folder, "*.md"):
            content = read_file(task_file)
            frontmatter, _ = parse_frontmatter(content)
            if frontmatter.get("id") == task_id:
                return task_file

        return None

    def get_all_active_plans(self) -> List[Dict[str, Any]]:
        """
        Get all active plans (pending or in_progress).

        Returns:
            List of plan status dictionaries
        """
        active_plans = []

        try:
            # Check Plans folder
            for plan_file in list_files(self.plans_folder, "*.md"):
                content = read_file(plan_file)
                frontmatter, _ = parse_frontmatter(content)

                plan_id = frontmatter.get("id")
                status = frontmatter.get("status", "pending")

                if status in ["pending", "in_progress"]:
                    plan_status = self.get_plan_status(plan_id)
                    active_plans.append(plan_status)

            # Check In_Progress folder
            for plan_file in list_files(self.in_progress_folder, "*.md"):
                content = read_file(plan_file)
                frontmatter, _ = parse_frontmatter(content)

                plan_id = frontmatter.get("id")
                plan_status = self.get_plan_status(plan_id)
                active_plans.append(plan_status)

            return active_plans

        except Exception as e:
            self.logger.error(f"Failed to get active plans: {e}")
            return []

    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks that are ready to execute.

        Returns:
            List of task dictionaries
        """
        ready_tasks = []

        try:
            task_files = list_files(self.tasks_folder, "*.md")

            for task_file in task_files:
                content = read_file(task_file)
                frontmatter, _ = parse_frontmatter(content)

                if frontmatter.get("status") == "ready":
                    ready_tasks.append({
                        "id": frontmatter.get("id"),
                        "plan_id": frontmatter.get("plan_id"),
                        "action_type": frontmatter.get("action_type"),
                        "step_number": frontmatter.get("step_number"),
                        "requires_approval": frontmatter.get("requires_approval", False),
                        "requires_external": frontmatter.get("requires_external", False),
                        "file_path": task_file,
                    })

            return ready_tasks

        except Exception as e:
            self.logger.error(f"Failed to get ready tasks: {e}")
            return []


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize tracker
        tracker = PlanTracker(vault_path)

        # Get active plans
        print("Getting active plans...")
        active_plans = tracker.get_all_active_plans()

        if active_plans:
            print(f"\n✅ Found {len(active_plans)} active plans:")
            for plan in active_plans:
                print(f"\n   Plan: {plan['plan_id']}")
                print(f"   Status: {plan['status']}")
                print(f"   Progress: {plan['completed_tasks']}/{plan['total_tasks']} "
                      f"({plan['progress_percent']:.0f}%)")
                if plan['current_task']:
                    print(f"   Current Task: {plan['current_task']}")
        else:
            print("\n⚠️  No active plans found")

        # Get ready tasks
        print("\n" + "="*60)
        print("Getting ready tasks...")
        ready_tasks = tracker.get_ready_tasks()

        if ready_tasks:
            print(f"\n✅ Found {len(ready_tasks)} ready tasks:")
            for task in ready_tasks:
                print(f"\n   Task: {task['id']}")
                print(f"   Plan: {task['plan_id']}")
                print(f"   Step: {task['step_number']}")
                print(f"   Action: {task['action_type']}")
        else:
            print("\n⚠️  No ready tasks found")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

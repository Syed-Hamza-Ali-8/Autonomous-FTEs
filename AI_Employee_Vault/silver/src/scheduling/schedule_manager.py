"""
Schedule Manager for managing schedule persistence and configuration.

This module provides schedule persistence, loading, and configuration
management for the Scheduler.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..utils import (
    get_logger,
    load_yaml_file,
    write_file,
    read_file,
    ensure_directory_exists,
)


class ScheduleManager:
    """
    Manages schedule persistence and configuration.

    Provides:
    - Schedule persistence to YAML files
    - Schedule loading on startup
    - Schedule configuration management
    - Integration with Scheduler
    """

    def __init__(self, vault_path: str):
        """
        Initialize ScheduleManager.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        # Schedule storage path
        self.schedules_folder = self.vault_path / "silver" / "config" / "schedules"
        ensure_directory_exists(self.schedules_folder)

        # Schedule configuration file
        self.config_file = self.schedules_folder / "schedules.yaml"

        # In-memory schedule registry
        self.schedules: Dict[str, Dict[str, Any]] = {}

        # Load existing schedules
        self._load_schedules()

        self.logger.info("ScheduleManager initialized")

    def _load_schedules(self) -> None:
        """Load schedules from configuration file."""
        try:
            if self.config_file.exists():
                config = load_yaml_file(str(self.config_file))
                self.schedules = config.get("schedules", {})
                self.logger.info(f"Loaded {len(self.schedules)} schedules from config")
            else:
                self.schedules = {}
                self.logger.info("No existing schedules found")

        except Exception as e:
            self.logger.error(f"Failed to load schedules: {e}")
            self.schedules = {}

    def _save_schedules(self) -> None:
        """Save schedules to configuration file."""
        try:
            import yaml

            config = {
                "schedules": self.schedules,
                "updated_at": datetime.now().isoformat(),
            }

            content = yaml.dump(config, default_flow_style=False, sort_keys=False)
            write_file(self.config_file, content)

            self.logger.info(f"Saved {len(self.schedules)} schedules to config")

        except Exception as e:
            self.logger.error(f"Failed to save schedules: {e}")

    def add_schedule(
        self,
        task_id: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        task_config: Dict[str, Any],
        description: Optional[str] = None,
        enabled: bool = True
    ) -> bool:
        """
        Add a new schedule.

        Args:
            task_id: Unique task identifier
            schedule_type: Type of schedule (daily, weekly, monthly, interval)
            schedule_config: Schedule configuration
            task_config: Task configuration (action type, parameters, etc.)
            description: Optional description
            enabled: Whether schedule is enabled

        Returns:
            True if added successfully
        """
        try:
            self.schedules[task_id] = {
                "task_id": task_id,
                "schedule_type": schedule_type,
                "schedule_config": schedule_config,
                "task_config": task_config,
                "description": description or f"Scheduled task: {task_id}",
                "enabled": enabled,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            self._save_schedules()

            self.logger.info(f"Added schedule: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add schedule {task_id}: {e}")
            return False

    def remove_schedule(self, task_id: str) -> bool:
        """
        Remove a schedule.

        Args:
            task_id: Task identifier

        Returns:
            True if removed successfully
        """
        try:
            if task_id not in self.schedules:
                self.logger.warning(f"Schedule not found: {task_id}")
                return False

            del self.schedules[task_id]
            self._save_schedules()

            self.logger.info(f"Removed schedule: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove schedule {task_id}: {e}")
            return False

    def update_schedule(
        self,
        task_id: str,
        schedule_type: Optional[str] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        task_config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """
        Update an existing schedule.

        Args:
            task_id: Task identifier
            schedule_type: New schedule type (optional)
            schedule_config: New schedule config (optional)
            task_config: New task config (optional)
            description: New description (optional)
            enabled: New enabled status (optional)

        Returns:
            True if updated successfully
        """
        try:
            if task_id not in self.schedules:
                self.logger.warning(f"Schedule not found: {task_id}")
                return False

            schedule = self.schedules[task_id]

            # Update fields
            if schedule_type is not None:
                schedule["schedule_type"] = schedule_type
            if schedule_config is not None:
                schedule["schedule_config"] = schedule_config
            if task_config is not None:
                schedule["task_config"] = task_config
            if description is not None:
                schedule["description"] = description
            if enabled is not None:
                schedule["enabled"] = enabled

            schedule["updated_at"] = datetime.now().isoformat()

            self._save_schedules()

            self.logger.info(f"Updated schedule: {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update schedule {task_id}: {e}")
            return False

    def get_schedule(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by ID.

        Args:
            task_id: Task identifier

        Returns:
            Schedule dictionary or None if not found
        """
        return self.schedules.get(task_id)

    def get_all_schedules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all schedules.

        Args:
            enabled_only: If True, only return enabled schedules

        Returns:
            List of schedule dictionaries
        """
        schedules = list(self.schedules.values())

        if enabled_only:
            schedules = [s for s in schedules if s.get("enabled", True)]

        return schedules

    def enable_schedule(self, task_id: str) -> bool:
        """
        Enable a schedule.

        Args:
            task_id: Task identifier

        Returns:
            True if enabled successfully
        """
        return self.update_schedule(task_id, enabled=True)

    def disable_schedule(self, task_id: str) -> bool:
        """
        Disable a schedule.

        Args:
            task_id: Task identifier

        Returns:
            True if disabled successfully
        """
        return self.update_schedule(task_id, enabled=False)

    def get_schedules_by_type(self, schedule_type: str) -> List[Dict[str, Any]]:
        """
        Get schedules by type.

        Args:
            schedule_type: Schedule type to filter by

        Returns:
            List of matching schedule dictionaries
        """
        return [
            s for s in self.schedules.values()
            if s.get("schedule_type") == schedule_type
        ]

    def export_schedules(self, export_path: Path) -> bool:
        """
        Export schedules to a file.

        Args:
            export_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            import yaml

            config = {
                "schedules": self.schedules,
                "exported_at": datetime.now().isoformat(),
            }

            content = yaml.dump(config, default_flow_style=False, sort_keys=False)
            write_file(export_path, content)

            self.logger.info(f"Exported {len(self.schedules)} schedules to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export schedules: {e}")
            return False

    def import_schedules(self, import_path: Path, merge: bool = True) -> bool:
        """
        Import schedules from a file.

        Args:
            import_path: Path to import file
            merge: If True, merge with existing schedules; if False, replace

        Returns:
            True if imported successfully
        """
        try:
            config = load_yaml_file(str(import_path))
            imported_schedules = config.get("schedules", {})

            if merge:
                # Merge with existing schedules
                self.schedules.update(imported_schedules)
            else:
                # Replace existing schedules
                self.schedules = imported_schedules

            self._save_schedules()

            self.logger.info(f"Imported {len(imported_schedules)} schedules from {import_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import schedules: {e}")
            return False

    def validate_schedule(self, schedule: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a schedule configuration.

        Args:
            schedule: Schedule dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ["task_id", "schedule_type", "schedule_config", "task_config"]
        for field in required_fields:
            if field not in schedule:
                return False, f"Missing required field: {field}"

        # Validate schedule type
        valid_types = ["daily", "weekly", "monthly", "interval", "custom"]
        if schedule["schedule_type"] not in valid_types:
            return False, f"Invalid schedule type: {schedule['schedule_type']}"

        # Validate schedule config based on type
        schedule_type = schedule["schedule_type"]
        schedule_config = schedule["schedule_config"]

        if schedule_type == "daily":
            if "time" not in schedule_config:
                return False, "Daily schedule requires 'time' field"

        elif schedule_type == "weekly":
            if "day" not in schedule_config or "time" not in schedule_config:
                return False, "Weekly schedule requires 'day' and 'time' fields"

        elif schedule_type == "monthly":
            if "day" not in schedule_config or "time" not in schedule_config:
                return False, "Monthly schedule requires 'day' and 'time' fields"

        elif schedule_type == "interval":
            if "interval" not in schedule_config or "unit" not in schedule_config:
                return False, "Interval schedule requires 'interval' and 'unit' fields"

        # Validate task config
        task_config = schedule["task_config"]
        if "action_type" not in task_config:
            return False, "Task config requires 'action_type' field"

        return True, None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get schedule statistics.

        Returns:
            Dictionary with schedule stats
        """
        total = len(self.schedules)
        enabled = sum(1 for s in self.schedules.values() if s.get("enabled", True))
        disabled = total - enabled

        # Count by type
        by_type = {}
        for schedule in self.schedules.values():
            schedule_type = schedule.get("schedule_type", "unknown")
            by_type[schedule_type] = by_type.get(schedule_type, 0) + 1

        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
            "by_type": by_type,
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
        # Initialize manager
        manager = ScheduleManager(vault_path)

        # Test: Add schedule
        print("Adding test schedule...")
        manager.add_schedule(
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

        print("✅ Schedule added")

        # Test: Get all schedules
        print("\nAll schedules:")
        schedules = manager.get_all_schedules()
        for schedule in schedules:
            print(f"  - {schedule['task_id']}: {schedule['description']}")
            print(f"    Type: {schedule['schedule_type']}")
            print(f"    Enabled: {schedule['enabled']}")

        # Test: Get stats
        print("\nSchedule statistics:")
        stats = manager.get_stats()
        print(f"  Total: {stats['total']}")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Disabled: {stats['disabled']}")
        print(f"  By type: {stats['by_type']}")

        print("\n✅ ScheduleManager test completed")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

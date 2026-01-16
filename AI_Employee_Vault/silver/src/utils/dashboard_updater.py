"""
Dashboard updater for maintaining Dashboard.md with current system status.

Updates pending counts, recent activity, statistics, and watcher status.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .yaml_parser import read_file_with_frontmatter, write_file_with_frontmatter


class DashboardUpdater:
    """Updates Dashboard.md with current system status."""

    def __init__(self, vault_path: Path):
        """
        Initialize DashboardUpdater.

        Args:
            vault_path: Path to the vault root directory
        """
        self.vault_path = Path(vault_path)
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.needs_action = self.vault_path / "Needs_Action"
        self.logger = logging.getLogger(__name__)

    def read_dashboard(self) -> Dict[str, Any]:
        """
        Read current Dashboard.md state.

        Returns:
            Dictionary with frontmatter data
        """
        if not self.dashboard_path.exists():
            # Return default state if dashboard doesn't exist
            return {
                "last_updated": None,
                "watcher_status": "unknown",
                "watcher_last_check": None,
                "pending_count": 0,
                "recent_activity": [],
                "statistics": {
                    "today": 0,
                    "this_week": 0,
                    "total": 0
                }
            }

        try:
            frontmatter, _ = read_file_with_frontmatter(self.dashboard_path)
            return frontmatter
        except Exception as e:
            self.logger.error(f"Error reading dashboard: {e}")
            return {}

    def update_pending_count(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update pending count by counting files in Needs_Action.

        Args:
            state: Current dashboard state

        Returns:
            Updated state with new pending_count
        """
        try:
            # Count metadata files with status="pending"
            pending_count = 0
            metadata_files = list(self.needs_action.glob("FILE_*.md"))

            for metadata_path in metadata_files:
                try:
                    frontmatter, _ = read_file_with_frontmatter(metadata_path)
                    if frontmatter.get("status") == "pending":
                        pending_count += 1
                except Exception:
                    pass  # Skip files that can't be read

            state["pending_count"] = pending_count
        except Exception as e:
            self.logger.error(f"Error updating pending count: {e}")

        return state

    def add_recent_activity(
        self,
        state: Dict[str, Any],
        activity_type: str,
        description: str,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add new activity entry and trim to 5 most recent items.

        Args:
            state: Current dashboard state
            activity_type: Type of activity (file_detected, file_processed, etc.)
            description: Human-readable description
            timestamp: ISO-8601 timestamp (defaults to now)

        Returns:
            Updated state with new activity
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat() + "Z"

        # Get current activity list
        recent_activity = state.get("recent_activity", [])
        if not isinstance(recent_activity, list):
            recent_activity = []

        # Add new activity
        new_activity = {
            "timestamp": timestamp,
            "type": activity_type,
            "description": description
        }
        recent_activity.insert(0, new_activity)

        # Trim to 5 most recent
        state["recent_activity"] = recent_activity[:5]

        return state

    def update_statistics(
        self,
        state: Dict[str, Any],
        increment_by: int = 1
    ) -> Dict[str, Any]:
        """
        Update statistics by incrementing today/week/total counters.

        Args:
            state: Current dashboard state
            increment_by: Number to increment by (default 1)

        Returns:
            Updated state with new statistics
        """
        # Get current statistics
        stats = state.get("statistics", {})
        if not isinstance(stats, dict):
            stats = {"today": 0, "this_week": 0, "total": 0}

        # Increment counters
        stats["today"] = stats.get("today", 0) + increment_by
        stats["this_week"] = stats.get("this_week", 0) + increment_by
        stats["total"] = stats.get("total", 0) + increment_by

        state["statistics"] = stats

        return state

    def update_watcher_status(
        self,
        state: Dict[str, Any],
        status: str,
        last_check: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update watcher status (running/stopped/unknown).

        Args:
            state: Current dashboard state
            status: Watcher status (running, stopped, unknown)
            last_check: ISO-8601 timestamp of last check (defaults to now)

        Returns:
            Updated state with new watcher status
        """
        if last_check is None:
            last_check = datetime.now().isoformat() + "Z"

        state["watcher_status"] = status
        state["watcher_last_check"] = last_check

        return state

    def write_dashboard(self, state: Dict[str, Any]) -> None:
        """
        Write dashboard state to Dashboard.md with atomic file write.

        Uses temp file + rename for atomic operation.

        Args:
            state: Dashboard state to write
        """
        # Update last_updated timestamp
        state["last_updated"] = datetime.now().isoformat() + "Z"

        # Generate body content
        body = self._generate_dashboard_body(state)

        # Write to temp file first
        temp_path = self.dashboard_path.with_suffix(".md.tmp")

        try:
            write_file_with_frontmatter(temp_path, state, body)

            # Atomic rename
            temp_path.replace(self.dashboard_path)

        except Exception as e:
            self.logger.error(f"Error writing dashboard: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _generate_dashboard_body(self, state: Dict[str, Any]) -> str:
        """
        Generate markdown body for Dashboard.md.

        Args:
            state: Dashboard state

        Returns:
            Markdown body content
        """
        # Format watcher status
        watcher_status = state.get("watcher_status", "unknown")
        if watcher_status == "running":
            status_icon = "✅ Running"
        elif watcher_status == "stopped":
            status_icon = "🛑 Stopped"
        else:
            status_icon = "⚠️ Not Started"

        # Format last check
        last_check = state.get("watcher_last_check")
        if last_check:
            try:
                dt = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
                last_check_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                last_check_str = "Unknown"
        else:
            last_check_str = "Never"

        # Format pending count
        pending_count = state.get("pending_count", 0)

        # Format recent activity
        recent_activity = state.get("recent_activity", [])
        if recent_activity:
            activity_lines = []
            for activity in recent_activity:
                timestamp = activity.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except Exception:
                    time_str = "??:??:??"

                activity_type = activity.get("type", "unknown")
                description = activity.get("description", "")

                # Format activity type with icon
                if activity_type == "file_detected":
                    icon = "📥"
                elif activity_type == "file_processed":
                    icon = "✅"
                elif activity_type == "file_quarantined":
                    icon = "⚠️"
                else:
                    icon = "•"

                activity_lines.append(f"- **{time_str}** {icon} {description}")

            activity_section = "\n".join(activity_lines)
        else:
            activity_section = "No activity yet. Drop a file in the Inbox folder to get started!"

        # Format statistics
        stats = state.get("statistics", {})
        today = stats.get("today", 0)
        this_week = stats.get("this_week", 0)
        total = stats.get("total", 0)

        # Format last updated
        last_updated = state.get("last_updated")
        if last_updated:
            try:
                dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                last_updated_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                last_updated_str = "Unknown"
        else:
            last_updated_str = "Never"

        # Generate body
        body = f"""# AI Employee Dashboard

## System Status
- **Watcher:** {status_icon}
- **Last Check:** {last_check_str}

## Pending Items
- **Needs Action:** {pending_count} files

## Recent Activity
{activity_section}

## Statistics
- **Today:** {today} files processed
- **This Week:** {this_week} files processed
- **Total:** {total} files processed

---

*Last updated: {last_updated_str}*
"""

        return body

    def update_for_file_detection(self, filename: str) -> None:
        """
        Update dashboard after file detection.

        Args:
            filename: Name of detected file
        """
        state = self.read_dashboard()
        state = self.update_pending_count(state)
        state = self.add_recent_activity(
            state,
            "file_detected",
            f"Detected: {filename}"
        )
        self.write_dashboard(state)

    def update_for_file_processing(self, filename: str, success: bool = True) -> None:
        """
        Update dashboard after file processing.

        Args:
            filename: Name of processed file
            success: Whether processing succeeded
        """
        state = self.read_dashboard()
        state = self.update_pending_count(state)

        if success:
            state = self.update_statistics(state, increment_by=1)
            state = self.add_recent_activity(
                state,
                "file_processed",
                f"Processed: {filename}"
            )
        else:
            state = self.add_recent_activity(
                state,
                "file_quarantined",
                f"Quarantined: {filename}"
            )

        self.write_dashboard(state)

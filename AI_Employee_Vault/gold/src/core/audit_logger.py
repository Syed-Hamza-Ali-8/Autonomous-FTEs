"""
Audit Logger Module

Comprehensive audit logging with 90-day retention.
All actions logged in newline-delimited JSON format.

Gold Tier Requirement #9: Comprehensive Audit Logging
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum


class ActionType(Enum):
    """Types of actions that can be logged"""
    # Email
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"

    # WhatsApp
    WHATSAPP_SENT = "whatsapp_sent"
    WHATSAPP_RECEIVED = "whatsapp_received"

    # LinkedIn
    LINKEDIN_POST = "linkedin_post"

    # Social Media (Gold Tier)
    FACEBOOK_POST = "facebook_post"
    INSTAGRAM_POST = "instagram_post"
    TWITTER_POST = "twitter_post"
    SOCIAL_POST_DRAFTED = "social_post_drafted"
    SOCIAL_POST_PUBLISHED = "social_post_published"
    SOCIAL_ENGAGEMENT_MONITORED = "social_engagement_monitored"
    ANALYTICS_GENERATED = "analytics_generated"

    # Xero (Gold Tier)
    XERO_SYNC = "xero_sync"
    XERO_INVOICE_CREATED = "xero_invoice_created"
    XERO_INVOICE_UPDATED = "xero_invoice_updated"
    XERO_PAYMENT_RECORDED = "xero_payment_recorded"

    # File Operations
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_MOVED = "file_moved"
    FILE_DELETED = "file_deleted"

    # Task Management
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"

    # Approval Workflow
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Intelligence (Gold Tier)
    CEO_BRIEFING_GENERATED = "ceo_briefing_generated"
    CROSS_DOMAIN_ANALYSIS = "cross_domain_analysis"

    # System
    ERROR_RECOVERY = "error_recovery"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    SYSTEM_ERROR = "system_error"
    MCP_CALL = "mcp_call"
    RALPH_WIGGUM_ITERATION = "ralph_wiggum_iteration"

    # Other
    OTHER = "other"


class ActorType(Enum):
    """Types of actors that can perform actions"""
    SYSTEM = "system"
    USER = "user"
    WATCHER = "watcher"
    AGENT = "agent"
    MCP_SERVER = "mcp_server"
    SCHEDULER = "scheduler"


@dataclass
class AuditLogEntry:
    """Structure for audit log entries"""
    timestamp: str
    action_id: str
    action_type: str
    domain: str  # personal, business, system, cross_domain
    actor: Dict[str, str]  # {type, id, name}
    status: str  # success, partial_success, failed, pending, cancelled
    duration_ms: float
    target: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogger:
    """
    Comprehensive audit logger with 90-day retention.

    Usage:
        logger = AuditLogger(vault_path="/Vault")
        logger.log_action(
            action_type=ActionType.EMAIL_SENT,
            actor_type=ActorType.AGENT,
            actor_id="email_sender",
            status="success",
            duration_ms=1234.56,
            target={"type": "email", "to": "client@example.com"}
        )
    """

    def __init__(self, vault_path: str, retention_days: int = 90):
        self.vault_path = Path(vault_path)
        self.log_dir = self.vault_path / "Logs"
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """Get log file path for a specific date"""
        if date is None:
            date = datetime.now()

        filename = f"{date.strftime('%Y-%m-%d')}.json"
        return self.log_dir / filename

    def _generate_action_id(self) -> str:
        """Generate unique action ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = str(abs(hash(datetime.now())))[:6]
        return f"act_{timestamp}_{random_suffix}"

    def log_action(
        self,
        action_type: ActionType,
        actor_type: ActorType,
        actor_id: str,
        status: str,
        duration_ms: float,
        domain: str = "system",
        actor_name: Optional[str] = None,
        target: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        approval: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        security: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an action to the audit log.

        Args:
            action_type: Type of action performed
            actor_type: Type of actor performing action
            actor_id: Unique identifier for actor
            status: Action status (success, failed, etc.)
            duration_ms: Action duration in milliseconds
            domain: Domain where action occurred
            actor_name: Human-readable actor name
            target: Target of the action
            context: Additional context
            input_data: Input data for the action
            output_data: Output data from the action
            error: Error details if action failed
            approval: Approval details if required
            metrics: Performance metrics
            security: Security-related information
            tags: Tags for categorization
            metadata: Additional metadata

        Returns:
            action_id: Unique identifier for this action
        """
        # Generate action ID
        action_id = self._generate_action_id()

        # Create audit log entry
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            action_id=action_id,
            action_type=action_type.value,
            domain=domain,
            actor={
                "type": actor_type.value,
                "id": actor_id,
                "name": actor_name or actor_id
            },
            status=status,
            duration_ms=duration_ms,
            target=target,
            context=context,
            input=input_data,
            output=output_data,
            error=error,
            approval=approval,
            metrics=metrics,
            security=security,
            tags=tags or [],
            metadata=metadata or {}
        )

        # Convert to JSON
        log_entry = asdict(entry)

        # Remove None values to keep logs clean
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        # Write to log file (newline-delimited JSON)
        log_file = self._get_log_file_path()
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            self.logger.debug(f"Logged action: {action_id} ({action_type.value})")

        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

        return action_id

    def search_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_type: Optional[ActionType] = None,
        actor_id: Optional[str] = None,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.

        Args:
            start_date: Start date for search
            end_date: End date for search
            action_type: Filter by action type
            actor_id: Filter by actor ID
            status: Filter by status
            domain: Filter by domain
            tags: Filter by tags
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        results = []

        # Default to last 7 days if no dates specified
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        # Iterate through log files in date range
        current_date = start_date
        while current_date <= end_date:
            log_file = self._get_log_file_path(current_date)

            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if len(results) >= limit:
                                return results

                            entry = json.loads(line.strip())

                            # Apply filters
                            if action_type and entry.get('action_type') != action_type.value:
                                continue
                            if actor_id and entry.get('actor', {}).get('id') != actor_id:
                                continue
                            if status and entry.get('status') != status:
                                continue
                            if domain and entry.get('domain') != domain:
                                continue
                            if tags and not any(tag in entry.get('tags', []) for tag in tags):
                                continue

                            results.append(entry)

                except Exception as e:
                    self.logger.error(f"Error reading log file {log_file}: {e}")

            current_date += timedelta(days=1)

        return results

    def cleanup_old_logs(self) -> int:
        """
        Delete log files older than retention period.

        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for log_file in self.log_dir.glob("*.json"):
            try:
                # Parse date from filename (YYYY-MM-DD.json)
                file_date_str = log_file.stem
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted old log file: {log_file.name}")

            except Exception as e:
                self.logger.error(f"Error processing log file {log_file}: {e}")

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old log files")

        return deleted_count

    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about audit logs.

        Returns:
            Dictionary with log statistics
        """
        total_files = len(list(self.log_dir.glob("*.json")))
        total_entries = 0
        total_size_bytes = 0

        for log_file in self.log_dir.glob("*.json"):
            try:
                total_size_bytes += log_file.stat().st_size
                with open(log_file, 'r') as f:
                    total_entries += sum(1 for _ in f)
            except Exception as e:
                self.logger.error(f"Error reading log file {log_file}: {e}")

        return {
            "total_files": total_files,
            "total_entries": total_entries,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "retention_days": self.retention_days,
            "log_directory": str(self.log_dir)
        }

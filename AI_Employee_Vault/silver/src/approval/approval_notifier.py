"""
Approval Notifier for sending desktop notifications.

This module sends desktop notifications to alert users of pending approval requests.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..utils import get_logger, load_yaml_file

# Plyer imports (will be installed via pip)
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class ApprovalNotifier:
    """
    Sends desktop notifications for approval requests.

    Uses plyer library for cross-platform desktop notifications.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize ApprovalNotifier.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to approval rules configuration file
        """
        self.vault_path = Path(vault_path)
        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)

        # Load configuration
        self.config = load_yaml_file(str(self.config_path))

        # Check if notifications are enabled
        self.enabled = self.config["notification_settings"]["enabled"]

        if not self.enabled:
            self.logger.info("Desktop notifications disabled in config")
            return

        if not PLYER_AVAILABLE:
            self.logger.warning(
                "Plyer not installed. Desktop notifications will not work. "
                "Install with: pip install plyer"
            )
            self.enabled = False
            return

        self.app_name = "AI Employee Vault"
        self.logger.info("ApprovalNotifier initialized")

    def send_notification(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        timeout: int = 10
    ) -> bool:
        """
        Send desktop notification.

        Args:
            title: Notification title
            message: Notification message
            urgency: Urgency level (low, normal, critical)
            timeout: Seconds to display (0 = until dismissed)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.debug("Notifications disabled, skipping")
            return False

        try:
            # Get urgency settings
            urgency_config = self.config["notification_settings"].get(urgency, {})

            # Send notification
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )

            self.logger.info(f"Notification sent: {title}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False

    def notify_approval_request(
        self,
        request_id: str,
        action_type: str,
        action_details: Dict[str, Any]
    ) -> bool:
        """
        Send notification for new approval request.

        Args:
            request_id: Approval request ID
            action_type: Type of action
            action_details: Action details dictionary

        Returns:
            True if notification sent successfully
        """
        # Format action type for display
        action_title = action_type.replace("_", " ").title()

        # Create notification message
        title = "Approval Required"

        # Create concise message based on action type
        if action_type == "send_email":
            to = action_details.get("to", "unknown")
            subject = action_details.get("subject", "")
            message = f"Send email to {to}\nSubject: {subject}"
        elif action_type == "delete_file":
            file_path = action_details.get("file_path", "unknown")
            message = f"Delete file: {file_path}"
        elif action_type == "post_linkedin":
            message = f"Post to LinkedIn"
        else:
            message = f"{action_title} requires approval"

        # Determine urgency
        risk_level = action_details.get("risk_level", "normal")
        if risk_level == "high":
            urgency = "critical"
        elif risk_level == "low":
            urgency = "low"
        else:
            urgency = "normal"

        # Send notification
        return self.send_notification(
            title=title,
            message=message,
            urgency=urgency,
            timeout=10
        )

    def notify_approval_timeout(
        self,
        request_id: str,
        action_type: str
    ) -> bool:
        """
        Send notification for approval timeout.

        Args:
            request_id: Approval request ID
            action_type: Type of action

        Returns:
            True if notification sent successfully
        """
        action_title = action_type.replace("_", " ").title()

        return self.send_notification(
            title="Approval Timeout",
            message=f"{action_title} request timed out",
            urgency="low",
            timeout=5
        )

    def test_notification(self) -> bool:
        """
        Send test notification to verify setup.

        Returns:
            True if notification sent successfully
        """
        return self.send_notification(
            title="Test Notification",
            message="If you see this, notifications are working!",
            urgency="normal",
            timeout=5
        )


def main():
    """Main entry point for testing notifications."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    try:
        # Initialize notifier
        notifier = ApprovalNotifier(vault_path, config_path)

        # Send test notification
        print("Sending test notification...")
        success = notifier.test_notification()

        if success:
            print("✅ Test notification sent successfully!")
            print("   Did you see the notification? (Check your system tray)")
        else:
            print("❌ Failed to send test notification")
            print("   Check if plyer is installed: pip install plyer")

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

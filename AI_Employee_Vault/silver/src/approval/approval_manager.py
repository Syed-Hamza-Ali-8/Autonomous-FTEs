"""
Approval Manager for creating and managing approval requests.

This module handles the creation of approval requests for sensitive actions
and execution of approved actions with retry logic.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging

from ..utils import (
    get_logger,
    load_yaml_file,
    serialize_frontmatter,
    write_file,
    move_file,
    ensure_directory_exists,
)


class ApprovalManager:
    """
    Manages approval requests for sensitive actions.

    Handles:
    - Creating approval requests
    - Classifying sensitive actions
    - Executing approved actions with retry logic
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize ApprovalManager.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to approval rules configuration file
        """
        self.vault_path = Path(vault_path)
        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)

        # Load configuration
        self.config = load_yaml_file(str(self.config_path))

        # Set up folders
        self.pending_folder = self.vault_path / self.config["workflow"]["folders"]["pending"]
        self.approved_folder = self.vault_path / self.config["workflow"]["folders"]["approved"]
        self.rejected_folder = self.vault_path / self.config["workflow"]["folders"]["rejected"]
        self.done_folder = self.vault_path / self.config["workflow"]["folders"]["done"]

        # Ensure folders exist
        for folder in [self.pending_folder, self.approved_folder, self.rejected_folder, self.done_folder]:
            ensure_directory_exists(folder)

        self.logger.info("ApprovalManager initialized")

    def is_sensitive_action(self, action_type: str) -> bool:
        """
        Check if an action type is sensitive and requires approval.

        Args:
            action_type: Type of action (e.g., "send_email", "delete_file")

        Returns:
            True if action requires approval, False otherwise
        """
        # Check sensitive actions
        for action in self.config["sensitive_actions"]:
            if action["action_type"] == action_type:
                return action["requires_approval"]

        # Check non-sensitive actions
        for action in self.config["non_sensitive_actions"]:
            if action["action_type"] == action_type:
                return action["requires_approval"]

        # Default: require approval for unknown actions
        self.logger.warning(f"Unknown action type: {action_type}, defaulting to require approval")
        return True

    def calculate_risk_score(self, action_details: Dict[str, Any]) -> int:
        """
        Calculate risk score for an action.

        Args:
            action_details: Dictionary with action details

        Returns:
            Risk score (0-100)
        """
        score = 0
        weights = self.config["risk_assessment"]["weights"]

        # Check each risk factor
        if action_details.get("external_recipient"):
            score += weights.get("external_recipient", 40)

        if not action_details.get("reversible", True):
            score += weights.get("irreversible", 30)

        if action_details.get("contains_pii"):
            score += weights.get("contains_pii", 20)

        if action_details.get("has_cost"):
            score += weights.get("has_cost", 10)

        if action_details.get("public_visibility"):
            score += weights.get("public_visibility", 40)

        if action_details.get("professional_reputation"):
            score += weights.get("professional_reputation", 30)

        if action_details.get("data_loss"):
            score += weights.get("data_loss", 50)

        return min(score, 100)  # Cap at 100

    def create_approval_request(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an approval request for a sensitive action.

        Args:
            action_type: Type of action (e.g., "send_email")
            action_details: Dictionary with action details
            risk_assessment: Optional risk assessment data

        Returns:
            Approval request ID

        Raises:
            IOError: If approval request file cannot be created
        """
        # Generate unique request ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request_id = f"approval_{timestamp}_{action_type}"

        # Calculate risk score
        risk_score = self.calculate_risk_score(action_details)

        # Determine risk level
        if risk_score <= 20:
            risk_level = "low"
        elif risk_score <= 50:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Get timeout from config
        timeout_minutes = self._get_timeout_for_action(action_type)
        timeout_at = datetime.now() + timedelta(minutes=timeout_minutes)

        # Create frontmatter
        frontmatter = {
            "id": request_id,
            "action_type": action_type,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "timeout_at": timeout_at.isoformat(),
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

        # Create body
        body = self._create_approval_body(
            action_type,
            action_details,
            risk_assessment or {},
            timeout_minutes
        )

        # Write approval request file
        filename = f"{request_id}.md"
        file_path = self.pending_folder / filename

        content = serialize_frontmatter(frontmatter, body)
        write_file(file_path, content)

        self.logger.info(f"Created approval request: {request_id}")
        return request_id

    def _get_timeout_for_action(self, action_type: str) -> int:
        """
        Get timeout in minutes for an action type.

        Args:
            action_type: Type of action

        Returns:
            Timeout in minutes
        """
        for action in self.config["sensitive_actions"]:
            if action["action_type"] == action_type:
                return action.get("timeout_minutes", 1440)  # Default: 24 hours

        return 1440  # Default: 24 hours

    def _create_approval_body(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        timeout_minutes: int
    ) -> str:
        """
        Create approval request body content.

        Args:
            action_type: Type of action
            action_details: Action details
            risk_assessment: Risk assessment data
            timeout_minutes: Timeout in minutes

        Returns:
            Markdown body content
        """
        # Format action type for display
        action_title = action_type.replace("_", " ").title()

        # Format action details
        details_lines = []
        for key, value in action_details.items():
            formatted_key = key.replace("_", " ").title()
            details_lines.append(f"- **{formatted_key}**: {value}")
        details_str = "\n".join(details_lines)

        # Format risk assessment
        risk_lines = []
        for key, value in risk_assessment.items():
            formatted_key = key.replace("_", " ").title()
            risk_lines.append(f"- **{formatted_key}**: {value}")
        risk_str = "\n".join(risk_lines) if risk_lines else "- No specific risks identified"

        # Format timeout
        timeout_hours = timeout_minutes / 60
        if timeout_hours >= 24:
            timeout_display = f"{int(timeout_hours / 24)} days"
        else:
            timeout_display = f"{int(timeout_hours)} hours"

        body = f"""# Approval Request: {action_title}

**Action**: {action_title}
**Status**: ⏳ Pending Approval
**Created**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
**Timeout**: {timeout_display}

## Action Details

{details_str}

## Risk Assessment

{risk_str}

## Instructions

To approve this action:
1. Change `status: pending` to `status: approved` in the YAML frontmatter above
2. Save the file
3. The action will execute automatically within 1 minute

To reject this action:
1. Change `status: pending` to `status: rejected` in the YAML frontmatter above
2. Add `rejection_reason: "Your reason here"` to the YAML frontmatter
3. Save the file
4. The action will be cancelled

## Timeout

If no response within {timeout_display}, this request will expire and the action will be cancelled.
"""
        return body

    def execute_approved_action(
        self,
        request_id: str,
        max_retries: int = 3,
        retry_delays: list = None
    ) -> Dict[str, Any]:
        """
        Execute an approved action with retry logic.

        Args:
            request_id: Approval request ID
            max_retries: Maximum number of retry attempts
            retry_delays: List of delays (seconds) between retries

        Returns:
            Result dictionary with:
            - success: bool
            - result: Any (if successful)
            - error: str (if failed)
            - retry_count: int

        Raises:
            FileNotFoundError: If approval request file not found
        """
        if retry_delays is None:
            retry_delays = [2, 4, 8]  # Exponential backoff: 2s, 4s, 8s

        # Find approval file
        file_path = self.approved_folder / f"{request_id}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Approval request not found: {request_id}")

        # TODO: Implement actual action execution
        # For now, this is a placeholder that will be implemented in Phase 7
        self.logger.info(f"Executing approved action: {request_id}")

        # Simulate execution with retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                # TODO: Execute actual action based on action_type
                # This will be implemented when we add ActionExecutor in Phase 7
                self.logger.info(f"Attempt {attempt + 1}/{max_retries}")

                # For now, just mark as successful
                result = {
                    "success": True,
                    "result": "Action executed successfully (placeholder)",
                    "retry_count": attempt,
                    "executed_at": datetime.now().isoformat()
                }

                # Move to Done folder
                done_path = self.done_folder / f"{request_id}.md"
                move_file(file_path, done_path)

                self.logger.info(f"Action executed successfully: {request_id}")
                return result

            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Retry with delay if not last attempt
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # All retries failed
        self.logger.error(f"Action execution failed after {max_retries} attempts: {last_error}")
        return {
            "success": False,
            "error": str(last_error),
            "retry_count": max_retries
        }


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    try:
        # Initialize manager
        manager = ApprovalManager(vault_path, config_path)

        # Test: Create approval request
        request_id = manager.create_approval_request(
            action_type="send_email",
            action_details={
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email",
                "external_recipient": True,
                "reversible": False
            },
            risk_assessment={
                "sensitivity": "high",
                "impact": "external_communication"
            }
        )

        print(f"✅ Created approval request: {request_id}")
        print(f"   Check: {vault_path}/Pending_Approval/{request_id}.md")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

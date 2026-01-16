"""
Approval Checker for polling approval status.

This module polls the Pending_Approval folder for status changes
and moves files to Approved or Rejected folders accordingly.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import logging

from ..utils import (
    get_logger,
    load_yaml_file,
    parse_frontmatter,
    update_frontmatter_field,
    read_file,
    write_file,
    move_file,
    list_files,
)


class ApprovalChecker:
    """
    Polls for approval status changes and moves files accordingly.

    Checks Pending_Approval folder every N seconds for:
    - Status changes (pending → approved/rejected)
    - Timeouts (expired approval requests)
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize ApprovalChecker.

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

        # Polling interval
        self.poll_interval = self.config["workflow"]["poll_interval"]

        self.logger.info("ApprovalChecker initialized")

    def poll_for_approvals(self) -> List[Dict[str, Any]]:
        """
        Poll Pending_Approval folder for status changes.

        Returns:
            List of approval status dictionaries with:
            - request_id: str
            - status: str (approved/rejected/timeout)
            - file_path: Path
        """
        approvals = []

        try:
            # Get all pending approval files
            pending_files = list_files(self.pending_folder, "*.md")
            self.logger.debug(f"Found {len(pending_files)} pending approval files")

            for file_path in pending_files:
                try:
                    status = self.check_approval_status(file_path)
                    if status["status"] != "pending":
                        approvals.append(status)
                except Exception as e:
                    self.logger.error(f"Failed to check approval status for {file_path}: {e}")

            return approvals

        except Exception as e:
            self.logger.error(f"Failed to poll for approvals: {e}")
            return []

    def check_approval_status(self, file_path: Path) -> Dict[str, Any]:
        """
        Check approval status of a single file.

        Args:
            file_path: Path to approval request file

        Returns:
            Status dictionary with:
            - request_id: str
            - status: str (pending/approved/rejected/timeout)
            - file_path: Path
            - reason: str (if rejected)
            - updated_at: str (ISO timestamp)
        """
        try:
            # Read file
            content = read_file(file_path)
            frontmatter, body = parse_frontmatter(content)

            request_id = frontmatter.get("id")
            status = frontmatter.get("status", "pending")
            timeout_at = frontmatter.get("timeout_at")

            # Check for timeout
            if status == "pending" and timeout_at:
                timeout_dt = datetime.fromisoformat(timeout_at)
                if datetime.now() > timeout_dt:
                    self.logger.info(f"Approval request {request_id} timed out")
                    return self._handle_timeout(file_path, frontmatter, body)

            # Check for status change
            if status == "approved":
                self.logger.info(f"Approval request {request_id} approved")
                return self._handle_approved(file_path, frontmatter, body)

            elif status == "rejected":
                self.logger.info(f"Approval request {request_id} rejected")
                return self._handle_rejected(file_path, frontmatter, body)

            # Still pending
            return {
                "request_id": request_id,
                "status": "pending",
                "file_path": file_path,
                "updated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to check approval status for {file_path}: {e}")
            raise

    def _handle_approved(
        self,
        file_path: Path,
        frontmatter: Dict[str, Any],
        body: str
    ) -> Dict[str, Any]:
        """
        Handle approved approval request.

        Args:
            file_path: Path to approval request file
            frontmatter: Frontmatter dictionary
            body: Body content

        Returns:
            Status dictionary
        """
        request_id = frontmatter["id"]

        # Update frontmatter
        frontmatter["approved_at"] = datetime.now().isoformat()

        # Update body
        updated_body = body.replace(
            "**Status**: ⏳ Pending Approval",
            "**Status**: ✅ Approved"
        )

        # Write updated content
        from ..utils import serialize_frontmatter
        content = serialize_frontmatter(frontmatter, updated_body)
        write_file(file_path, content)

        # Move to Approved folder
        approved_path = self.approved_folder / file_path.name
        move_file(file_path, approved_path)

        self.logger.info(f"Moved {request_id} to Approved folder")

        return {
            "request_id": request_id,
            "status": "approved",
            "file_path": approved_path,
            "approved_at": frontmatter["approved_at"],
            "updated_at": datetime.now().isoformat()
        }

    def _handle_rejected(
        self,
        file_path: Path,
        frontmatter: Dict[str, Any],
        body: str
    ) -> Dict[str, Any]:
        """
        Handle rejected approval request.

        Args:
            file_path: Path to approval request file
            frontmatter: Frontmatter dictionary
            body: Body content

        Returns:
            Status dictionary
        """
        request_id = frontmatter["id"]
        reason = frontmatter.get("rejection_reason", "No reason provided")

        # Update frontmatter
        frontmatter["rejected_at"] = datetime.now().isoformat()

        # Update body
        updated_body = body.replace(
            "**Status**: ⏳ Pending Approval",
            f"**Status**: ❌ Rejected\n\n**Reason**: {reason}"
        )

        # Write updated content
        from ..utils import serialize_frontmatter
        content = serialize_frontmatter(frontmatter, updated_body)
        write_file(file_path, content)

        # Move to Rejected folder
        rejected_path = self.rejected_folder / file_path.name
        move_file(file_path, rejected_path)

        self.logger.info(f"Moved {request_id} to Rejected folder")

        return {
            "request_id": request_id,
            "status": "rejected",
            "file_path": rejected_path,
            "reason": reason,
            "rejected_at": frontmatter["rejected_at"],
            "updated_at": datetime.now().isoformat()
        }

    def _handle_timeout(
        self,
        file_path: Path,
        frontmatter: Dict[str, Any],
        body: str
    ) -> Dict[str, Any]:
        """
        Handle timed out approval request.

        Args:
            file_path: Path to approval request file
            frontmatter: Frontmatter dictionary
            body: Body content

        Returns:
            Status dictionary
        """
        request_id = frontmatter["id"]
        timeout_minutes = self.config["workflow"]["timeout_behavior"]

        # Update frontmatter
        frontmatter["status"] = "rejected"
        frontmatter["rejected_at"] = datetime.now().isoformat()
        frontmatter["rejection_reason"] = timeout_minutes["reason"].format(
            timeout_minutes=int((datetime.fromisoformat(frontmatter["timeout_at"]) -
                               datetime.fromisoformat(frontmatter["created_at"])).total_seconds() / 60)
        )

        # Update body
        updated_body = body.replace(
            "**Status**: ⏳ Pending Approval",
            f"**Status**: ⏱️ Timeout\n\n**Reason**: {frontmatter['rejection_reason']}"
        )

        # Write updated content
        from ..utils import serialize_frontmatter
        content = serialize_frontmatter(frontmatter, updated_body)
        write_file(file_path, content)

        # Move to Rejected folder
        rejected_path = self.rejected_folder / file_path.name
        move_file(file_path, rejected_path)

        self.logger.info(f"Moved {request_id} to Rejected folder (timeout)")

        return {
            "request_id": request_id,
            "status": "timeout",
            "file_path": rejected_path,
            "reason": frontmatter["rejection_reason"],
            "rejected_at": frontmatter["rejected_at"],
            "updated_at": datetime.now().isoformat()
        }

    def run(self) -> None:
        """
        Main polling loop - continuously check for approval status changes.

        This method runs indefinitely, checking for approvals every N seconds.
        """
        self.logger.info(f"Starting approval checker (poll interval: {self.poll_interval}s)")

        try:
            while True:
                # Poll for approvals
                approvals = self.poll_for_approvals()

                # Process each approval
                for approval in approvals:
                    self.logger.info(
                        f"Processed approval: {approval['request_id']} → {approval['status']}"
                    )

                    # TODO: Trigger action execution for approved requests
                    # This will be implemented when we integrate with ApprovalManager

                # Sleep until next poll
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("Approval checker stopped by user")
        except Exception as e:
            self.logger.error(f"Approval checker error: {e}")
            raise


def main():
    """Main entry point for approval checker."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    config_path = f"{vault_path}/silver/config/approval_rules.yaml"

    try:
        # Initialize checker
        checker = ApprovalChecker(vault_path, config_path)

        # Run polling loop
        checker.run()

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n✅ Approval checker stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

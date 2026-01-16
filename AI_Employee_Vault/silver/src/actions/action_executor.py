"""
Action Executor for executing approved actions.

This module orchestrates action execution, routing actions to appropriate
handlers, managing retry logic, and tracking results.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import time
import logging

from ..utils import (
    get_logger,
    parse_frontmatter,
    serialize_frontmatter,
    read_file,
    write_file,
    move_file,
    list_files,
)
from ..approval.approval_manager import ApprovalManager


class ActionExecutor:
    """
    Executes approved actions with retry logic and result tracking.

    Routes actions to appropriate handlers (email, WhatsApp, etc.),
    manages execution lifecycle, and tracks results.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize ActionExecutor.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to approval rules configuration file
        """
        self.vault_path = Path(vault_path)
        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)

        # Set up folders
        self.approved_folder = self.vault_path / "Approved"
        self.done_folder = self.vault_path / "Done"
        self.failed_folder = self.vault_path / "Failed"

        # Initialize approval manager
        self.approval_manager = ApprovalManager(str(vault_path), str(config_path))

        # Action handlers registry
        self.handlers: Dict[str, Callable] = {}

        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [2, 4, 8]  # Exponential backoff: 2s, 4s, 8s

        self.logger.info("ActionExecutor initialized")

    def register_handler(
        self,
        action_type: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Register an action handler.

        Args:
            action_type: Type of action (e.g., "send_email")
            handler: Handler function that takes action_details and returns result
        """
        self.handlers[action_type] = handler
        self.logger.info(f"Registered handler for action type: {action_type}")

    def execute_action(
        self,
        action_file: Path,
        max_retries: Optional[int] = None,
        retry_delays: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Execute an approved action with retry logic.

        Args:
            action_file: Path to approved action file
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delays: List of delays between retries (default: [2, 4, 8])

        Returns:
            Result dictionary with:
            - success: bool
            - result: Any (if successful)
            - error: str (if failed)
            - retry_count: int
            - executed_at: str (ISO timestamp)

        Raises:
            FileNotFoundError: If action file not found
            ValueError: If action file is invalid
        """
        if not action_file.exists():
            raise FileNotFoundError(f"Action file not found: {action_file}")

        # Use default retry configuration if not provided
        if max_retries is None:
            max_retries = self.max_retries
        if retry_delays is None:
            retry_delays = self.retry_delays

        # Read action file
        content = read_file(action_file)
        frontmatter, body = parse_frontmatter(content)

        action_id = frontmatter.get("id")
        action_type = frontmatter.get("action_type", "unknown")

        if not action_id:
            raise ValueError(f"Action file missing ID: {action_file}")

        self.logger.info(f"Executing action: {action_id} (type: {action_type})")

        # Extract action details from body
        action_details = self._extract_action_details(body, action_type)

        # Get handler for action type
        handler = self.handlers.get(action_type)
        if not handler:
            error_msg = f"No handler registered for action type: {action_type}"
            self.logger.error(error_msg)
            return self._create_failure_result(
                action_id=action_id,
                error=error_msg,
                retry_count=0
            )

        # Execute with retry logic
        last_error = None
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{max_retries}")

                # Execute action
                result = handler(action_details)

                # Success
                success_result = {
                    "success": True,
                    "result": result,
                    "retry_count": attempt,
                    "executed_at": datetime.now().isoformat(),
                    "action_id": action_id,
                    "action_type": action_type,
                }

                # Update action file and move to Done
                self._handle_success(action_file, frontmatter, body, success_result)

                self.logger.info(f"Action executed successfully: {action_id}")
                return success_result

            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Retry with delay if not last attempt
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # All retries failed
        error_msg = f"Action execution failed after {max_retries} attempts: {last_error}"
        self.logger.error(error_msg)

        failure_result = self._create_failure_result(
            action_id=action_id,
            error=str(last_error),
            retry_count=max_retries
        )

        # Update action file and move to Failed
        self._handle_failure(action_file, frontmatter, body, failure_result)

        return failure_result

    def _extract_action_details(self, body: str, action_type: str) -> Dict[str, Any]:
        """
        Extract action details from action file body.

        Args:
            body: Action file body content
            action_type: Type of action

        Returns:
            Dictionary with action details
        """
        details = {"action_type": action_type}

        # Parse body for action-specific details
        lines = body.split("\n")

        for line in lines:
            # Look for key-value pairs in markdown format
            if "**" in line and ":" in line:
                # Extract key and value from "**Key**: Value" format
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].replace("**", "").strip().lower().replace(" ", "_")
                    value = parts[1].strip()
                    details[key] = value

        return details

    def _create_failure_result(
        self,
        action_id: str,
        error: str,
        retry_count: int
    ) -> Dict[str, Any]:
        """Create failure result dictionary."""
        return {
            "success": False,
            "error": error,
            "retry_count": retry_count,
            "executed_at": datetime.now().isoformat(),
            "action_id": action_id,
        }

    def _handle_success(
        self,
        action_file: Path,
        frontmatter: Dict[str, Any],
        body: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle successful action execution.

        Args:
            action_file: Path to action file
            frontmatter: Action frontmatter
            body: Action body
            result: Execution result
        """
        # Update frontmatter
        frontmatter["status"] = "completed"
        frontmatter["executed_at"] = result["executed_at"]
        frontmatter["retry_count"] = result["retry_count"]
        frontmatter["result"] = result.get("result", {})

        # Update body
        updated_body = body.replace(
            "**Status**: ✅ Approved",
            "**Status**: ✅ Completed"
        )

        # Add execution details
        execution_details = f"""

## Execution Details

**Executed At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
**Retry Count**: {result['retry_count']}
**Result**: Success

### Result Data

```json
{result.get('result', {})}
```
"""
        updated_body += execution_details

        # Write updated content
        content = serialize_frontmatter(frontmatter, updated_body)
        write_file(action_file, content)

        # Move to Done folder
        done_path = self.done_folder / action_file.name
        move_file(action_file, done_path)

        self.logger.info(f"Moved completed action to Done folder")

    def _handle_failure(
        self,
        action_file: Path,
        frontmatter: Dict[str, Any],
        body: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle failed action execution.

        Args:
            action_file: Path to action file
            frontmatter: Action frontmatter
            body: Action body
            result: Execution result
        """
        # Update frontmatter
        frontmatter["status"] = "failed"
        frontmatter["executed_at"] = result["executed_at"]
        frontmatter["retry_count"] = result["retry_count"]
        frontmatter["error"] = result["error"]

        # Update body
        updated_body = body.replace(
            "**Status**: ✅ Approved",
            "**Status**: ❌ Failed"
        )

        # Add failure details
        failure_details = f"""

## Execution Details

**Executed At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
**Retry Count**: {result['retry_count']}
**Result**: Failed

### Error

```
{result['error']}
```

### Troubleshooting

- Check error message above for details
- Verify credentials and configuration
- Check logs for more information
- Retry manually if needed
"""
        updated_body += failure_details

        # Write updated content
        content = serialize_frontmatter(frontmatter, updated_body)
        write_file(action_file, content)

        # Move to Failed folder
        failed_path = self.failed_folder / action_file.name
        move_file(action_file, failed_path)

        self.logger.info(f"Moved failed action to Failed folder")

    def execute_all_approved_actions(self) -> Dict[str, Any]:
        """
        Execute all approved actions in Approved folder.

        Returns:
            Summary dictionary with:
            - total: int
            - successful: int
            - failed: int
            - results: List[Dict]
        """
        results = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        try:
            # Get all approved action files
            approved_files = list_files(self.approved_folder, "*.md")
            results["total"] = len(approved_files)

            self.logger.info(f"Found {len(approved_files)} approved actions to execute")

            for action_file in approved_files:
                try:
                    result = self.execute_action(action_file)
                    results["results"].append(result)

                    if result["success"]:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                except Exception as e:
                    self.logger.error(f"Failed to execute action {action_file}: {e}")
                    results["failed"] += 1
                    results["results"].append({
                        "success": False,
                        "error": str(e),
                        "action_file": str(action_file),
                    })

            return results

        except Exception as e:
            self.logger.error(f"Failed to execute approved actions: {e}")
            return results

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary with execution stats:
            - total_executed: int
            - successful: int
            - failed: int
            - pending_approval: int
        """
        try:
            done_files = list_files(self.done_folder, "*.md")
            failed_files = list_files(self.failed_folder, "*.md")
            approved_files = list_files(self.approved_folder, "*.md")

            stats = {
                "total_executed": len(done_files) + len(failed_files),
                "successful": len(done_files),
                "failed": len(failed_files),
                "pending_approval": len(approved_files),
            }

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get execution stats: {e}")
            return {
                "total_executed": 0,
                "successful": 0,
                "failed": 0,
                "pending_approval": 0,
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
        # Initialize executor
        executor = ActionExecutor(vault_path, config_path)

        # Get execution stats
        print("Getting execution statistics...")
        stats = executor.get_execution_stats()

        print(f"\n✅ Execution Statistics:")
        print(f"   Total Executed: {stats['total_executed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Pending Approval: {stats['pending_approval']}")

        # Execute all approved actions
        if stats['pending_approval'] > 0:
            print(f"\nExecuting {stats['pending_approval']} approved actions...")
            results = executor.execute_all_approved_actions()

            print(f"\n✅ Execution Results:")
            print(f"   Total: {results['total']}")
            print(f"   Successful: {results['successful']}")
            print(f"   Failed: {results['failed']}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

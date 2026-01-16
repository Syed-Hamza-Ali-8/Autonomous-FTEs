"""
JSON logger utility with daily log rotation.

Provides structured logging to JSON files with automatic daily rotation.
All log entries follow the schema defined in contracts/log-entry.schema.json.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONLogger:
    """
    Logger that writes structured JSON entries to daily log files.

    Log files are named: Logs/YYYY-MM-DD.json
    Each entry is a single JSON object on one line (newline-delimited JSON).
    """

    def __init__(self, logs_dir: Path):
        """
        Initialize JSON logger.

        Args:
            logs_dir: Path to the Logs directory
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Set up Python logging for console output
        self.console_logger = logging.getLogger(__name__)
        if not self.console_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.console_logger.addHandler(handler)
            self.console_logger.setLevel(logging.INFO)

    def _get_log_file(self) -> Path:
        """Get the log file path for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.logs_dir / f"{today}.json"

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """
        Write a log entry to the daily log file.

        Args:
            entry: Log entry dictionary
        """
        log_file = self._get_log_file()

        # Write as newline-delimited JSON (one JSON object per line)
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
            f.flush()  # Ensure logs survive crashes

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: str,
        result: str,
        parameters: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a system action.

        Args:
            action_type: Type of action (file_detected, file_processed, etc.)
            actor: Component that performed action (watcher, claude_code, human)
            target: Target of the action (filename, path, etc.)
            result: Action result (success, failure, pending)
            parameters: Optional additional parameters
            error_message: Optional error message if result is failure
        """
        entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "result": result
        }

        if parameters:
            entry["parameters"] = parameters

        if error_message:
            entry["error_message"] = error_message

        # Write to JSON log file
        self._write_entry(entry)

        # Also log to console for debugging
        log_msg = f"{action_type} | {actor} → {target} | {result}"
        if result == "success":
            self.console_logger.info(log_msg)
        elif result == "failure":
            self.console_logger.error(f"{log_msg} | {error_message}")
        else:
            self.console_logger.warning(log_msg)

    def log_error(
        self,
        action_type: str,
        target: str,
        error_message: str,
        actor: str = "system"
    ) -> None:
        """
        Convenience method to log an error.

        Args:
            action_type: Type of action that failed
            target: Target of the action
            error_message: Error message
            actor: Component that encountered the error
        """
        self.log_action(
            action_type=action_type,
            actor=actor,
            target=target,
            result="failure",
            error_message=error_message
        )

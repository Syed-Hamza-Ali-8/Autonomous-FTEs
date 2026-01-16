"""
File system watcher for monitoring Inbox folder.

Detects new files and creates metadata in Needs_Action.
"""

import time
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .metadata_creator import MetadataCreator
from ..utils.logger import JSONLogger
from ..utils.dashboard_updater import DashboardUpdater


class InboxHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox folder."""

    def __init__(self, vault_path: Path):
        """
        Initialize InboxHandler.

        Args:
            vault_path: Path to the vault root directory
        """
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.needs_action = self.vault_path / "Needs_Action"
        self.metadata_creator = MetadataCreator(vault_path)
        self.logger = JSONLogger(self.vault_path / "Logs")
        self.dashboard_updater = DashboardUpdater(vault_path)
        self.processing = set()  # Track files being processed

        # Ensure directories exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def on_created(self, event):
        """
        Handle file creation events.

        Args:
            event: FileSystemEvent from watchdog
        """
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Ignore temporary files
        if self._is_temporary_file(filepath):
            return

        # Debounce: wait for file to be fully written
        time.sleep(1)

        # Avoid duplicate processing
        if filepath in self.processing:
            return

        self.processing.add(filepath)

        try:
            self._process_file(filepath)
        except Exception as e:
            self.logger.log_error(
                action_type="file_detection_failed",
                target=str(filepath),
                error_message=str(e),
                actor="watcher"
            )
            logging.error(f"Error processing {filepath}: {e}")
        finally:
            self.processing.discard(filepath)

    def _is_temporary_file(self, filepath: Path) -> bool:
        """
        Check if file is temporary and should be ignored.

        Args:
            filepath: Path to the file

        Returns:
            True if file should be ignored
        """
        name = filepath.name

        # Ignore hidden files (starting with .)
        if name.startswith('.'):
            return True

        # Ignore temporary files
        if name.startswith('~') or name.startswith('~$'):
            return True

        # Ignore common temporary extensions
        temp_extensions = {'.tmp', '.swp', '.swo', '.bak', '.temp'}
        if filepath.suffix.lower() in temp_extensions:
            return True

        return False

    def _process_file(self, filepath: Path):
        """
        Process a detected file.

        Args:
            filepath: Path to the detected file
        """
        # Check if file still exists (might have been moved/deleted)
        if not filepath.exists():
            return

        # Log detection
        self.logger.log_action(
            action_type="file_detected",
            actor="watcher",
            target=filepath.name,
            parameters={"size": filepath.stat().st_size},
            result="success"
        )

        # Create metadata file
        try:
            metadata_path = self.metadata_creator.create_metadata(filepath)

            self.logger.log_action(
                action_type="metadata_created",
                actor="watcher",
                target=metadata_path.name,
                parameters={"original_file": filepath.name},
                result="success"
            )
        except Exception as e:
            self.logger.log_error(
                action_type="metadata_creation_failed",
                target=filepath.name,
                error_message=str(e),
                actor="watcher"
            )
            raise

        # Move file to Needs_Action
        try:
            dest_path = self.needs_action / filepath.name

            # Handle filename conflicts
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                dest_path = self.needs_action / f"{filepath.stem}_{timestamp}{filepath.suffix}"

            filepath.rename(dest_path)

            self.logger.log_action(
                action_type="file_moved",
                actor="watcher",
                target=filepath.name,
                parameters={"from": "Inbox", "to": "Needs_Action"},
                result="success"
            )

            # Update dashboard after successful file detection
            try:
                self.dashboard_updater.update_for_file_detection(filepath.name)
            except Exception as e:
                logging.error(f"Error updating dashboard: {e}")
                # Don't raise - dashboard update failure shouldn't stop file processing

        except Exception as e:
            self.logger.log_error(
                action_type="file_move_failed",
                target=filepath.name,
                error_message=str(e),
                actor="watcher"
            )
            raise


def run_watcher(vault_path: Path):
    """
    Run the file watcher continuously.

    Args:
        vault_path: Path to the vault root directory
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    vault_path = Path(vault_path)
    inbox_path = vault_path / "Inbox"

    # Ensure Inbox exists
    inbox_path.mkdir(parents=True, exist_ok=True)

    # Create handler and observer
    handler = InboxHandler(vault_path)
    observer = Observer()
    observer.schedule(handler, str(inbox_path), recursive=False)
    observer.start()

    logging.info(f"Watcher started. Monitoring: {inbox_path}")
    logging.info("Press Ctrl+C to stop")

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logging.info("Stopping watcher...")
        observer.stop()
        observer.join()
        logging.info("Watcher stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(10)  # Check interval
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Watcher stopped by user")

    observer.join()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.watcher.file_watcher <vault_path>")
        sys.exit(1)

    vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    run_watcher(vault_path)

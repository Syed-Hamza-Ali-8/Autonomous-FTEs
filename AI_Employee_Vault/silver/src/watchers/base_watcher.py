"""
Base watcher abstract class for all communication channel watchers.

This module provides the abstract base class that all watchers must inherit from.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import hashlib

from ..utils import (
    get_logger,
    load_yaml_file,
    serialize_frontmatter,
    write_file,
    ensure_directory_exists,
    file_exists,
)


class BaseWatcher(ABC):
    """
    Abstract base class for all communication channel watchers.

    All watchers must implement:
    - check_for_updates(): Check channel for new messages
    - create_action_file(): Create markdown file in Needs_Action folder
    """

    def __init__(self, vault_path: str, config_path: str, channel_name: str):
        """
        Initialize the watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file
            channel_name: Name of the channel (e.g., "gmail", "whatsapp")
        """
        self.vault_path = Path(vault_path)
        self.config_path = Path(config_path)
        self.channel_name = channel_name
        self.logger = get_logger(f"{__name__}.{channel_name}")

        # Load configuration
        self.config = self._load_config()

        # Set up paths
        self.output_folder = self.vault_path / self.config["general"]["output_folder"]
        ensure_directory_exists(self.output_folder)

        # Deduplication cache
        self.cache_file = self.vault_path / self.config["general"]["deduplication"]["cache_file"]
        self.message_cache = self._load_cache()

        # Error tracking
        self.consecutive_failures = 0
        self.max_failures = self.config["general"]["error_handling"]["max_consecutive_failures"]

        self.logger.info(f"{channel_name} watcher initialized")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load watcher configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        try:
            config = load_yaml_file(str(self.config_path))
            self.logger.debug(f"Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            raise

    def _load_cache(self) -> Dict[str, Any]:
        """
        Load message deduplication cache.

        Returns:
            Cache dictionary with message IDs and timestamps
        """
        if not file_exists(self.cache_file):
            self.logger.debug("Cache file not found, creating new cache")
            return {}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            self.logger.debug(f"Loaded cache with {len(cache)} entries")
            return cache
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load cache: {e}, creating new cache")
            return {}

    def _save_cache(self) -> None:
        """Save message deduplication cache to file."""
        try:
            ensure_directory_exists(self.cache_file.parent)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.message_cache, f, indent=2)
            self.logger.debug(f"Saved cache with {len(self.message_cache)} entries")
        except IOError as e:
            self.logger.error(f"Failed to save cache: {e}")

    def _is_duplicate(self, message_id: str) -> bool:
        """
        Check if message has already been processed.

        Args:
            message_id: Unique message identifier

        Returns:
            True if message is duplicate, False otherwise
        """
        if not self.config["general"]["deduplication"]["enabled"]:
            return False

        # Check if message ID is in cache
        if message_id in self.message_cache:
            cached_time = datetime.fromisoformat(self.message_cache[message_id])
            cache_ttl = self.config["general"]["deduplication"]["cache_ttl"]

            # Check if cache entry is still valid
            age = (datetime.now() - cached_time).total_seconds()
            if age < cache_ttl:
                self.logger.debug(f"Message {message_id} is duplicate (age: {age}s)")
                return True
            else:
                # Cache entry expired, remove it
                del self.message_cache[message_id]

        return False

    def _mark_as_processed(self, message_id: str) -> None:
        """
        Mark message as processed in cache.

        Args:
            message_id: Unique message identifier
        """
        self.message_cache[message_id] = datetime.now().isoformat()
        self._save_cache()
        self.logger.debug(f"Marked message {message_id} as processed")

    def _generate_message_id(self, item: Dict[str, Any]) -> str:
        """
        Generate unique message ID from item data.

        Args:
            item: Message data dictionary

        Returns:
            Unique message ID
        """
        # Create hash from key fields
        key_fields = [
            str(item.get("sender", "")),
            str(item.get("subject", "")),
            str(item.get("timestamp", "")),
            str(item.get("body", ""))[:100],  # First 100 chars of body
        ]
        key_string = "|".join(key_fields)
        hash_value = hashlib.md5(key_string.encode()).hexdigest()[:12]

        return f"msg_{self.channel_name}_{hash_value}"

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check channel for new messages.

        Returns:
            List of message dictionaries with keys:
            - sender: Sender name/email
            - subject: Message subject (if applicable)
            - body: Message content
            - timestamp: Message timestamp (ISO format)
            - metadata: Additional channel-specific data

        Raises:
            Exception: If check fails
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create markdown file in Needs_Action folder.

        Args:
            item: Message data dictionary

        Returns:
            Path to created action file

        Raises:
            IOError: If file cannot be created
        """
        pass

    def run(self) -> None:
        """
        Main watcher loop - check for updates and create action files.

        This method:
        1. Checks for new messages
        2. Filters out duplicates
        3. Creates action files for new messages
        4. Handles errors with exponential backoff
        """
        try:
            self.logger.info(f"Checking {self.channel_name} for updates...")

            # Check for new messages
            messages = self.check_for_updates()
            self.logger.info(f"Found {len(messages)} messages")

            # Process each message
            new_messages = 0
            for item in messages:
                message_id = self._generate_message_id(item)

                # Skip duplicates
                if self._is_duplicate(message_id):
                    self.logger.debug(f"Skipping duplicate message: {message_id}")
                    continue

                # Create action file
                try:
                    action_file = self.create_action_file(item)
                    self._mark_as_processed(message_id)
                    new_messages += 1
                    self.logger.info(f"Created action file: {action_file}")
                except Exception as e:
                    self.logger.error(f"Failed to create action file for {message_id}: {e}")

            self.logger.info(f"Processed {new_messages} new messages")

            # Reset failure counter on success
            self.consecutive_failures = 0

        except Exception as e:
            self.consecutive_failures += 1
            self.logger.error(
                f"Watcher check failed ({self.consecutive_failures}/{self.max_failures}): {e}"
            )

            # Check if max failures reached
            if self.consecutive_failures >= self.max_failures:
                cooldown = self.config["general"]["error_handling"]["failure_cooldown"]
                self.logger.critical(
                    f"Max consecutive failures reached. "
                    f"Entering cooldown for {cooldown} seconds."
                )

                # Notify user if configured
                if self.config["general"]["error_handling"]["notify_on_failure"]:
                    self._notify_failure(e)

    def _notify_failure(self, error: Exception) -> None:
        """
        Notify user of watcher failure.

        Args:
            error: Exception that caused the failure
        """
        # TODO: Implement notification (desktop notification or file-based)
        self.logger.warning(f"Failure notification not yet implemented: {error}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current watcher status.

        Returns:
            Status dictionary with:
            - channel: Channel name
            - enabled: Whether watcher is enabled
            - last_check: Last check timestamp
            - consecutive_failures: Number of consecutive failures
            - cache_size: Number of cached messages
        """
        return {
            "channel": self.channel_name,
            "enabled": self.config[self.channel_name]["enabled"],
            "last_check": datetime.now().isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "cache_size": len(self.message_cache),
        }

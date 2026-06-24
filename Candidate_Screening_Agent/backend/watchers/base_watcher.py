from abc import ABC, abstractmethod
import asyncio
import logging


class BaseWatcher(ABC):
    """
    Abstract base class for background watchers.

    Watchers poll external services (e.g., Gmail) at regular intervals
    and process new items (e.g., emails, replies).
    """

    def __init__(self, check_interval: int = 120):
        """
        Initialize watcher.

        Args:
            check_interval: Seconds between checks (default: 120 = 2 minutes)
        """
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self._handled_items: set = set()  # Track handled items to prevent duplicates

    @abstractmethod
    async def check_for_updates(self) -> list:
        """
        Check for new items to process.

        Returns:
            List of items to process
        """
        pass

    @abstractmethod
    async def handle_item(self, item) -> None:
        """
        Process a single item.

        Args:
            item: Item to process
        """
        pass

    async def run(self):
        """
        Main loop: check for updates and process items.

        Runs indefinitely with error recovery. Errors are logged but
        the loop continues to ensure the watcher never crashes.
        """
        self.logger.info(f"Starting {self.__class__.__name__} (check interval: {self.check_interval}s)")

        while True:
            try:
                # Check for new items
                items = await self.check_for_updates()

                # Deduplicate items (by message_id - first element of tuple)
                seen = set()
                unique_items = []
                for item in items:
                    item_key = str(item[0]) if item else ""
                    if item_key and item_key not in seen and item_key not in self._handled_items:
                        seen.add(item_key)
                        unique_items.append(item)

                # Process each unique item
                for item in unique_items:
                    try:
                        self._handled_items.add(str(item[0]) if item else "")
                        await self.handle_item(item)
                    except Exception as e:
                        self.logger.error(f"Error handling item: {e}")
                        # Continue with next item

            except Exception as e:
                self.logger.error(f"Watcher error: {e}")
                # Continue loop even after error

            # Wait before next check
            await asyncio.sleep(self.check_interval)

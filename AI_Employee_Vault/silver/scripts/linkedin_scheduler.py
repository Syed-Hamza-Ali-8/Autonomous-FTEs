#!/usr/bin/env python3
"""
Scheduled LinkedIn poster service.

This service runs continuously and posts to LinkedIn on a daily schedule.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster
from src.utils import get_logger


class LinkedInScheduler:
    """
    Scheduler for automated LinkedIn posting.

    Posts business content to LinkedIn on a daily schedule.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize LinkedIn scheduler.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger("linkedin_scheduler")

        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.config = config.get('linkedin', {})
        self.enabled = self.config.get('enabled', False)
        self.post_interval = self.config.get('post_interval', 86400)  # 24 hours
        self.post_time = self.config.get('post_time', 9)  # 9 AM
        self.topics = self.config.get('topics', ['business update'])

        # Initialize poster
        self.poster = LinkedInPoster(str(vault_path))

        # Track last post time
        self.last_post_time = None
        self.topic_index = 0

        self.logger.info("LinkedIn scheduler initialized")

    def should_post_now(self) -> bool:
        """
        Check if it's time to post.

        Returns:
            True if should post now, False otherwise
        """
        now = datetime.now()

        # Check if we've already posted today
        if self.last_post_time:
            time_since_last = (now - self.last_post_time).total_seconds()
            if time_since_last < self.post_interval:
                return False

        # Check if it's the right hour
        if now.hour == self.post_time and now.minute < 10:
            return True

        # If we missed the scheduled time and haven't posted today
        if self.last_post_time is None or self.last_post_time.date() < now.date():
            if now.hour >= self.post_time:
                return True

        return False

    def get_next_topic(self) -> str:
        """
        Get next topic from rotation.

        Returns:
            Topic string
        """
        topic = self.topics[self.topic_index]
        self.topic_index = (self.topic_index + 1) % len(self.topics)
        return topic

    def post_to_linkedin(self) -> bool:
        """
        Generate and post content to LinkedIn.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get next topic
            topic = self.get_next_topic()

            self.logger.info(f"Generating content for topic: {topic}")

            # Generate content
            content = self.poster.generate_business_post(topic)

            self.logger.info("Posting to LinkedIn...")

            # Post to LinkedIn
            result = self.poster.post_update(content)

            if result["success"]:
                self.logger.info("✅ Successfully posted to LinkedIn")
                self.last_post_time = datetime.now()
                return True
            else:
                self.logger.error(f"Failed to post: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def run(self):
        """
        Run the scheduler continuously.
        """
        if not self.enabled:
            self.logger.warning("LinkedIn scheduler is disabled in config")
            return

        self.logger.info("Starting LinkedIn scheduler...")
        self.logger.info(f"Post interval: {self.post_interval}s ({self.post_interval/3600:.1f} hours)")
        self.logger.info(f"Scheduled post time: {self.post_time}:00")
        self.logger.info(f"Topics: {', '.join(self.topics)}")

        check_interval = 600  # Check every 10 minutes

        while True:
            try:
                if self.should_post_now():
                    self.logger.info("Time to post!")
                    success = self.post_to_linkedin()

                    if success:
                        self.logger.info(f"Next post scheduled for tomorrow at {self.post_time}:00")
                    else:
                        self.logger.warning("Post failed, will retry in next cycle")

                else:
                    # Calculate time until next post
                    now = datetime.now()
                    next_post = now.replace(hour=self.post_time, minute=0, second=0, microsecond=0)

                    if now.hour >= self.post_time:
                        next_post += timedelta(days=1)

                    time_until = (next_post - now).total_seconds()
                    hours = int(time_until // 3600)
                    minutes = int((time_until % 3600) // 60)

                    self.logger.debug(f"Next post in {hours}h {minutes}m")

                # Sleep until next check
                time.sleep(check_interval)

            except KeyboardInterrupt:
                self.logger.info("Scheduler stopped by user")
                break

            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(check_interval)


def main():
    """Main entry point."""
    vault_path = Path(__file__).parent.parent.parent.absolute()
    config_path = vault_path / "silver" / "config" / "watcher_config.yaml"

    print(f"Vault path: {vault_path}")
    print(f"Config path: {config_path}")

    try:
        scheduler = LinkedInScheduler(str(vault_path), str(config_path))
        scheduler.run()

    except KeyboardInterrupt:
        print("\n\n✋ Scheduler stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

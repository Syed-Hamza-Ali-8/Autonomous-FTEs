#!/usr/bin/env python3
"""
Scheduled LinkedIn poster with HITL approval workflow.

This service creates daily approval requests instead of posting directly.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster
from src.approval.approval_manager import ApprovalManager
from src.utils import get_logger


class LinkedInSchedulerWithApproval:
    """
    Scheduler that creates LinkedIn post approval requests daily.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize LinkedIn scheduler with approval workflow.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger("linkedin_scheduler_approval")

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

        # Initialize approval manager
        approval_config = self.vault_path / "silver" / "config" / "approval_rules.yaml"
        self.approval_manager = ApprovalManager(str(vault_path), str(approval_config))

        # Track last request time
        self.last_request_time = None
        self.topic_index = 0

        self.logger.info("LinkedIn scheduler with approval initialized")

    def should_create_request_now(self) -> bool:
        """
        Check if it's time to create approval request.

        Returns:
            True if should create request now, False otherwise
        """
        now = datetime.now()

        # Check if we've already created request today
        if self.last_request_time:
            time_since_last = (now - self.last_request_time).total_seconds()
            if time_since_last < self.post_interval:
                return False

        # Check if it's the right hour
        if now.hour == self.post_time and now.minute < 10:
            return True

        # If we missed the scheduled time and haven't created request today
        if self.last_request_time is None or self.last_request_time.date() < now.date():
            if now.hour >= self.post_time:
                return True

        return False

    def get_next_topic(self) -> str:
        """Get next topic from rotation."""
        topic = self.topics[self.topic_index]
        self.topic_index = (self.topic_index + 1) % len(self.topics)
        return topic

    def create_approval_request(self) -> bool:
        """
        Create LinkedIn post approval request.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get next topic
            topic = self.get_next_topic()

            self.logger.info(f"Generating content for topic: {topic}")

            # Generate content
            content = self.poster.generate_business_post(topic)

            self.logger.info("Creating approval request...")

            # Create approval request
            approval_data = {
                "action_type": "post_linkedin",
                "content": content,
                "topic": topic,
                "scheduled_time": datetime.now().isoformat(),
                "metadata": {
                    "auto_generated": True,
                    "content_length": len(content),
                    "hashtags": content.count('#')
                }
            }

            # Request approval
            result = self.approval_manager.request_approval(
                action_type="post_linkedin",
                action_data=approval_data,
                reason=f"Daily LinkedIn post about {topic}"
            )

            if result["success"]:
                self.logger.info(f"✅ Approval request created: {result['approval_file']}")
                self.logger.info("📋 Please review and approve in Obsidian")
                self.last_request_time = datetime.now()
                return True
            else:
                self.logger.error(f"Failed to create approval request: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating approval request: {e}")
            return False

    def run(self):
        """
        Run the scheduler continuously.
        """
        if not self.enabled:
            self.logger.warning("LinkedIn scheduler is disabled in config")
            return

        self.logger.info("Starting LinkedIn scheduler with approval workflow...")
        self.logger.info(f"Request interval: {self.post_interval}s ({self.post_interval/3600:.1f} hours)")
        self.logger.info(f"Scheduled request time: {self.post_time}:00")
        self.logger.info(f"Topics: {', '.join(self.topics)}")
        self.logger.info("⚠️  Posts require manual approval in Obsidian")

        check_interval = 600  # Check every 10 minutes

        while True:
            try:
                if self.should_create_request_now():
                    self.logger.info("Time to create approval request!")
                    success = self.create_approval_request()

                    if success:
                        self.logger.info(f"Next request scheduled for tomorrow at {self.post_time}:00")
                        self.logger.info("📋 Don't forget to approve in Obsidian!")
                    else:
                        self.logger.warning("Request creation failed, will retry in next cycle")

                else:
                    # Calculate time until next request
                    now = datetime.now()
                    next_request = now.replace(hour=self.post_time, minute=0, second=0, microsecond=0)

                    if now.hour >= self.post_time:
                        next_request += timedelta(days=1)

                    time_until = (next_request - now).total_seconds()
                    hours = int(time_until // 3600)
                    minutes = int((time_until % 3600) // 60)

                    self.logger.debug(f"Next request in {hours}h {minutes}m")

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
    print()
    print("⚠️  This scheduler creates APPROVAL REQUESTS, not direct posts")
    print("📋 You must approve posts in Obsidian before they are published")
    print()

    try:
        scheduler = LinkedInSchedulerWithApproval(str(vault_path), str(config_path))
        scheduler.run()

    except KeyboardInterrupt:
        print("\n\n✋ Scheduler stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

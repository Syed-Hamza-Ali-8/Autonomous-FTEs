#!/usr/bin/env python3
"""
LinkedIn poster with HITL approval workflow.

This version creates approval requests instead of posting directly.
"""

import sys
from pathlib import Path
from datetime import datetime
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.linkedin_poster import LinkedInPoster
from src.approval.approval_manager import ApprovalManager
from src.utils import get_logger


class LinkedInWithApproval:
    """
    LinkedIn poster that requires human approval before posting.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize LinkedIn poster with approval workflow.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger("linkedin_with_approval")

        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.config = config.get('linkedin', {})
        self.topics = self.config.get('topics', ['business update'])
        self.topic_index = 0

        # Initialize poster
        self.poster = LinkedInPoster(str(vault_path))

        # Initialize approval manager
        approval_config = self.vault_path / "silver" / "config" / "approval_rules.yaml"
        self.approval_manager = ApprovalManager(str(vault_path), str(approval_config))

        self.logger.info("LinkedIn with approval initialized")

    def get_next_topic(self) -> str:
        """Get next topic from rotation."""
        topic = self.topics[self.topic_index]
        self.topic_index = (self.topic_index + 1) % len(self.topics)
        return topic

    def create_post_request(self) -> dict:
        """
        Create LinkedIn post approval request.

        Returns:
            Result dictionary with approval file path
        """
        try:
            # Get next topic
            topic = self.get_next_topic()

            self.logger.info(f"Generating content for topic: {topic}")

            # Generate content
            content = self.poster.generate_business_post(topic)

            self.logger.info("Creating approval request...")

            # Create approval request
            action_details = {
                "content": content,
                "topic": topic,
                "scheduled_time": datetime.now().isoformat(),
                "auto_generated": True,
                "content_length": len(content),
                "hashtags": content.count('#')
            }

            # Create approval request
            request_id = self.approval_manager.create_approval_request(
                action_type="post_linkedin",
                action_details=action_details
            )

            approval_file = self.vault_path / "Pending_Approval" / f"{request_id}.md"

            self.logger.info(f"✅ Approval request created: {request_id}")
            self.logger.info("📋 Please review and approve in Obsidian:")
            self.logger.info(f"   File: Pending_Approval/{request_id}.md")

            return {
                "success": True,
                "request_id": request_id,
                "approval_file": str(approval_file)
            }

        except Exception as e:
            self.logger.error(f"Error creating post request: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_once(self):
        """
        Create one approval request and exit.
        """
        self.logger.info("Creating LinkedIn post approval request...")
        result = self.create_post_request()

        if result["success"]:
            print("\n" + "="*60)
            print("✅ LinkedIn Post Approval Request Created!")
            print("="*60)
            print()
            print("📋 Next Steps:")
            print("   1. Open Obsidian")
            print("   2. Go to: Pending_Approval/")
            print(f"   3. Open file: {Path(result['approval_file']).name}")
            print("   4. Review the content")
            print("   5. Change status: pending → approved")
            print("   6. Save file (Ctrl+S)")
            print()
            print("⏱️  The post will be published within 10 seconds of approval")
            print("="*60)
            return True
        else:
            print(f"\n❌ Failed to create approval request: {result.get('error')}")
            return False


def main():
    """Main entry point."""
    vault_path = Path(__file__).parent.parent.parent.absolute()
    config_path = vault_path / "silver" / "config" / "watcher_config.yaml"

    print(f"Vault path: {vault_path}")
    print(f"Config path: {config_path}")
    print()

    try:
        poster = LinkedInWithApproval(str(vault_path), str(config_path))
        success = poster.run_once()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n✋ Stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

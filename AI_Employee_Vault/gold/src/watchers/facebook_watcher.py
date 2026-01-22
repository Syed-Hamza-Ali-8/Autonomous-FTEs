"""
Facebook Watcher

Monitors Facebook for comments, messages, and mentions.
Gold Tier Requirement #4: Social Media Integration (Facebook monitoring)
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_media_interface import SocialMediaInterface


class FacebookWatcher:
    """Monitors Facebook for engagement and creates action items."""

    def __init__(self, vault_path: str, access_token: Optional[str] = None,
                 page_id: Optional[str] = None, use_mock: bool = False,
                 check_interval: int = 300):
        """
        Initialize Facebook watcher.

        Args:
            vault_path: Path to Obsidian vault
            access_token: Facebook access token (optional if using mock)
            page_id: Facebook page ID (optional if using mock)
            use_mock: Use mock implementation for testing
            check_interval: Seconds between checks (default 300 = 5 minutes)
        """
        self.vault_path = vault_path
        self.access_token = access_token or os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"
        self.check_interval = check_interval

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize Facebook API (real or mock)
        if self.use_mock:
            from gold.src.mocks.mock_facebook import MockFacebookAPI
            self.api: SocialMediaInterface = MockFacebookAPI()
        else:
            # Real Facebook API will be implemented in Phase 4
            from gold.src.mocks.mock_facebook import MockFacebookAPI
            self.api = MockFacebookAPI()

        self.last_check = datetime.now() - timedelta(hours=1)

    def watch(self, continuous: bool = False):
        """
        Watch Facebook for new activity.

        Args:
            continuous: If True, run continuously. If False, run once.
        """
        print(f"🔍 Facebook Watcher started (interval: {self.check_interval}s)")

        while True:
            try:
                self._check_activity()

                if not continuous:
                    break

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n⏹️  Facebook Watcher stopped")
                break
            except Exception as e:
                print(f"❌ Error in Facebook watcher: {e}")
                self.audit_logger.log_action(
                    action_type=ActionType.SYSTEM_ERROR,
                    actor_type=ActorType.SYSTEM,
                    actor_id="facebook_watcher",
                    status="failure",
                    duration_ms=0,
                    domain="system",
                    error={"type": type(e).__name__, "message": str(e)}
                )
                if not continuous:
                    raise
                time.sleep(60)  # Wait 1 minute before retrying

    def _check_activity(self):
        """Check for new comments, messages, and mentions."""
        start_time = datetime.now()

        from ..interfaces.social_media_interface import EngagementType

        # Get new comments (using engagement API)
        comments = self.error_recovery.execute_with_retry(
            func=self.api.get_engagement,
            kwargs={
                "engagement_type": EngagementType.COMMENT,
                "start_date": self.last_check.isoformat()
            },
            error_type=ErrorType.TRANSIENT
        )

        # Get new messages (using direct_messages API)
        messages = self.error_recovery.execute_with_retry(
            func=self.api.get_direct_messages,
            kwargs={"unread_only": True},
            error_type=ErrorType.TRANSIENT
        )

        # Get new mentions
        mentions = self.error_recovery.execute_with_retry(
            func=self.api.get_mentions,
            kwargs={"start_date": self.last_check.isoformat()},
            error_type=ErrorType.TRANSIENT
        )

        # Process comments
        for comment in comments:
            self._create_action_item("comment", comment)

        # Process messages
        for message in messages:
            self._create_action_item("message", message)

        # Process mentions
        for mention in mentions:
            self._create_action_item("mention", mention)

        # Update last check time
        self.last_check = datetime.now()

        # Log activity check
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.audit_logger.log_action(
            action_type=ActionType.SOCIAL_ENGAGEMENT_MONITORED,
            actor_type=ActorType.AGENT,
            actor_id="facebook_watcher",
            status="success",
            duration_ms=duration_ms,
            domain="business",
            metadata={
                "comments": len(comments),
                "messages": len(messages),
                "mentions": len(mentions)
            }
        )

        if comments or messages or mentions:
            print(f"✅ Facebook: {len(comments)} comments, {len(messages)} messages, {len(mentions)} mentions")

    def _create_action_item(self, item_type: str, item_data: Dict[str, Any]):
        """
        Create an action item in Needs_Action folder.

        Args:
            item_type: Type of item (comment, message, mention)
            item_data: Item data
        """
        item_id = f"fb_{item_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        item_path = os.path.join(self.vault_path, "Needs_Action", f"{item_id}.md")

        content = f"""---
type: social_media_action
platform: facebook
action_type: {item_type}
status: pending
created: {datetime.now().isoformat()}
item_id: {item_id}
---

# Facebook {item_type.title()}

**From**: {item_data.get('author', 'Unknown')}
**Time**: {item_data.get('timestamp', 'Unknown')}

## Content
{item_data.get('text', 'No content')}

## Actions
- [ ] Reply
- [ ] Ignore
- [ ] Flag for review

**To reply**: Add your response below and check the "Reply" box.

---

## Response

[Your response here]
"""

        os.makedirs(os.path.dirname(item_path), exist_ok=True)
        with open(item_path, 'w') as f:
            f.write(content)

        print(f"📝 Created action item: {item_id}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Facebook Watcher")
    parser.add_argument("--vault-path", default=os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"))
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")

    args = parser.parse_args()

    watcher = FacebookWatcher(
        vault_path=args.vault_path,
        use_mock=True,
        check_interval=args.interval
    )

    watcher.watch(continuous=args.continuous)

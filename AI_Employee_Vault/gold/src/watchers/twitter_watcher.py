"""
Twitter Watcher

Monitors Twitter for mentions, replies, and direct messages.
Gold Tier Requirement #4: Social Media Integration (Twitter monitoring)
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_media_interface import SocialMediaInterface


class TwitterWatcher:
    """Monitors Twitter for engagement and creates action items."""

    def __init__(self, vault_path: str, api_key: Optional[str] = None,
                 api_secret: Optional[str] = None, access_token: Optional[str] = None,
                 access_token_secret: Optional[str] = None, use_mock: bool = False,
                 check_interval: int = 300):
        """
        Initialize Twitter watcher.

        Args:
            vault_path: Path to Obsidian vault
            api_key: Twitter API key (optional if using mock)
            api_secret: Twitter API secret (optional if using mock)
            access_token: Twitter access token (optional if using mock)
            access_token_secret: Twitter access token secret (optional if using mock)
            use_mock: Use mock implementation for testing
            check_interval: Seconds between checks (default 300 = 5 minutes)
        """
        self.vault_path = vault_path
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"
        self.check_interval = check_interval

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize Twitter API (real or mock)
        if self.use_mock:
            from gold.src.mocks.mock_twitter import MockTwitterAPI
            self.api: SocialMediaInterface = MockTwitterAPI()
        else:
            # Real Twitter API will be implemented in Phase 4
            from gold.src.mocks.mock_twitter import MockTwitterAPI
            self.api = MockTwitterAPI()

        self.last_check = datetime.now() - timedelta(hours=1)

    def watch(self, continuous: bool = False):
        """
        Watch Twitter for new activity.

        Args:
            continuous: If True, run continuously. If False, run once.
        """
        print(f"🔍 Twitter Watcher started (interval: {self.check_interval}s)")

        while True:
            try:
                self._check_activity()

                if not continuous:
                    break

                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n⏹️  Twitter Watcher stopped")
                break
            except Exception as e:
                print(f"❌ Error in Twitter watcher: {e}")
                self.audit_logger.log_action(
                    action_type=ActionType.SYSTEM_ERROR,
                    actor_type=ActorType.SYSTEM,
                    actor_id="twitter_watcher",
                    status="failure",
                    duration_ms=0,
                    domain="system",
                    error={"type": type(e).__name__, "message": str(e)}
                )
                if not continuous:
                    raise
                time.sleep(60)  # Wait 1 minute before retrying

    def _check_activity(self):
        """Check for new replies, mentions, and messages."""
        start_time = datetime.now()

        from ..interfaces.social_media_interface import EngagementType

        # Get new replies (using engagement API)
        replies = self.error_recovery.execute_with_retry(
            func=self.api.get_engagement,
            kwargs={
                "engagement_type": EngagementType.REPLY,
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

        # Process replies
        for reply in replies:
            self._create_action_item("reply", reply)

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
            actor_id="twitter_watcher",
            status="success",
            duration_ms=duration_ms,
            domain="business",
            metadata={
                "replies": len(replies),
                "messages": len(messages),
                "mentions": len(mentions)
            }
        )

        if replies or messages or mentions:
            print(f"✅ Twitter: {len(replies)} replies, {len(messages)} messages, {len(mentions)} mentions")

    def _create_action_item(self, item_type: str, item_data: Dict[str, Any]):
        """
        Create an action item in Needs_Action folder.

        Args:
            item_type: Type of item (reply, message, mention)
            item_data: Item data
        """
        item_id = f"tw_{item_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        item_path = os.path.join(self.vault_path, "Needs_Action", f"{item_id}.md")

        content = f"""---
type: social_media_action
platform: twitter
action_type: {item_type}
status: pending
created: {datetime.now().isoformat()}
item_id: {item_id}
---

# Twitter {item_type.title()}

**From**: {item_data.get('author', 'Unknown')}
**Time**: {item_data.get('timestamp', 'Unknown')}

## Content
{item_data.get('text', 'No content')}

## Actions
- [ ] Reply
- [ ] Retweet
- [ ] Like
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

    parser = argparse.ArgumentParser(description="Twitter Watcher")
    parser.add_argument("--vault-path", default=os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"))
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds")

    args = parser.parse_args()

    watcher = TwitterWatcher(
        vault_path=args.vault_path,
        use_mock=True,
        check_interval=args.interval
    )

    watcher.watch(continuous=args.continuous)

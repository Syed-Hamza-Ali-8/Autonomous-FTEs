"""
Twitter Poster

Posts content to Twitter and handles approval workflow.
Gold Tier Requirement #4: Social Media Integration (Twitter)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_interface import SocialMediaInterface


class TwitterPoster:
    """Posts content to Twitter with approval workflow."""

    def __init__(self, vault_path: str, api_key: Optional[str] = None,
                 api_secret: Optional[str] = None, access_token: Optional[str] = None,
                 access_token_secret: Optional[str] = None, use_mock: bool = False):
        """
        Initialize Twitter poster.

        Args:
            vault_path: Path to Obsidian vault
            api_key: Twitter API key (optional if using mock)
            api_secret: Twitter API secret (optional if using mock)
            access_token: Twitter access token (optional if using mock)
            access_token_secret: Twitter access token secret (optional if using mock)
            use_mock: Use mock implementation for testing
        """
        self.vault_path = vault_path
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize Twitter API (real or mock)
        if self.use_mock:
            from gold.src.mocks.mock_social import MockTwitterAPI
            self.api: SocialMediaInterface = MockTwitterAPI()
        else:
            # Real Twitter API will be implemented in Phase 4
            from gold.src.mocks.mock_social import MockTwitterAPI
            self.api = MockTwitterAPI()

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None,
             require_approval: bool = True) -> Dict[str, Any]:
        """
        Post content to Twitter.

        Args:
            content: Tweet text (max 280 characters)
            media_urls: Optional list of image/video URLs
            metadata: Optional metadata (reply_to, quote_tweet, etc.)
            require_approval: Whether to require human approval before posting

        Returns:
            Dict with post_id, url, status, and timestamp
        """
        start_time = datetime.now()

        # Validate tweet length
        if len(content) > 280 and not require_approval:
            raise ValueError(f"Tweet too long: {len(content)} characters (max 280)")

        try:
            # Step 1: Create draft in vault for approval
            if require_approval:
                draft_result = self._create_draft(content, media_urls, metadata)

                # Log draft creation
                self.audit_logger.log_action(
                    action_type=ActionType.SOCIAL_POST_DRAFTED,
                    actor_type=ActorType.AGENT,
                    actor_id="twitter_poster",
                    status="success",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    domain="business",
                    target={"type": "twitter_draft", "draft_id": draft_result["draft_id"]},
                    metadata={"content_length": len(content), "has_media": bool(media_urls)}
                )

                return {
                    "status": "pending_approval",
                    "draft_id": draft_result["draft_id"],
                    "draft_path": draft_result["draft_path"],
                    "message": "Draft created. Approve in vault to post."
                }

            # Step 2: Post to Twitter (if approved or no approval required)
            result = self.error_recovery.execute_with_retry(
                func=self.api.post,
                kwargs={"content": content, "media_urls": media_urls, "metadata": metadata},
                error_type=ErrorType.TRANSIENT
            )

            # Log successful post
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.SOCIAL_POST_PUBLISHED,
                actor_type=ActorType.AGENT,
                actor_id="twitter_poster",
                status="success",
                duration_ms=duration_ms,
                domain="business",
                target={"type": "twitter_post", "post_id": result["post_id"], "url": result.get("url")},
                metadata={
                    "content_length": len(content),
                    "has_media": bool(media_urls),
                    "engagement": result.get("engagement", {})
                }
            )

            return result

        except Exception as e:
            # Log failure
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.SOCIAL_POST_PUBLISHED,
                actor_type=ActorType.AGENT,
                actor_id="twitter_poster",
                status="failure",
                duration_ms=duration_ms,
                domain="business",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def post_thread(self, tweets: List[str], require_approval: bool = True) -> Dict[str, Any]:
        """
        Post a Twitter thread.

        Args:
            tweets: List of tweet texts
            require_approval: Whether to require human approval before posting

        Returns:
            Dict with thread_id, tweet_ids, and status
        """
        if require_approval:
            # Create draft for thread
            draft_id = f"tw_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            draft_path = os.path.join(self.vault_path, "Needs_Action", f"{draft_id}.md")

            thread_content = "\n\n---\n\n".join([f"**Tweet {i+1}:**\n{tweet}" for i, tweet in enumerate(tweets)])

            draft_content = f"""---
type: social_media_draft
platform: twitter
status: pending_approval
created: {datetime.now().isoformat()}
draft_id: {draft_id}
thread: true
---

# Twitter Thread Draft

{thread_content}

## Actions
- [ ] Approve and post
- [ ] Edit and resubmit
- [ ] Reject

**To approve**: Check the "Approve and post" box above.
"""

            os.makedirs(os.path.dirname(draft_path), exist_ok=True)
            with open(draft_path, 'w') as f:
                f.write(draft_content)

            return {
                "status": "pending_approval",
                "draft_id": draft_id,
                "draft_path": draft_path,
                "message": "Thread draft created. Approve in vault to post."
            }

        # Post thread without approval
        tweet_ids = []
        reply_to = None

        for i, tweet in enumerate(tweets):
            metadata = {"reply_to": reply_to} if reply_to else {}
            result = self.post(tweet, metadata=metadata, require_approval=False)
            tweet_ids.append(result["post_id"])
            reply_to = result["post_id"]

        return {
            "status": "posted",
            "thread_id": tweet_ids[0],
            "tweet_ids": tweet_ids,
            "count": len(tweet_ids)
        }

    def _create_draft(self, content: str, media_urls: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a draft tweet in the vault for approval."""
        draft_id = f"tw_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        draft_path = os.path.join(self.vault_path, "Needs_Action", f"{draft_id}.md")

        char_count = len(content)
        char_warning = f"\n\n⚠️ **Warning**: Tweet is {char_count} characters (max 280)" if char_count > 280 else ""

        draft_content = f"""---
type: social_media_draft
platform: twitter
status: pending_approval
created: {datetime.now().isoformat()}
draft_id: {draft_id}
---

# Twitter Draft

## Tweet ({char_count}/280 characters)
{content}{char_warning}

## Media
{json.dumps(media_urls or [], indent=2)}

## Metadata
{json.dumps(metadata or {}, indent=2)}

## Actions
- [ ] Approve and post
- [ ] Edit and resubmit
- [ ] Reject

**To approve**: Check the "Approve and post" box above.
**To reject**: Check the "Reject" box above.
"""

        os.makedirs(os.path.dirname(draft_path), exist_ok=True)
        with open(draft_path, 'w') as f:
            f.write(draft_content)

        return {"draft_id": draft_id, "draft_path": draft_path}


if __name__ == "__main__":
    # Test the poster
    vault_path = os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    poster = TwitterPoster(vault_path, use_mock=True)

    # Test single tweet
    result = poster.post(
        content="🚀 Excited to announce our new feature! Check it out: https://example.com #tech #innovation",
        require_approval=True
    )

    print(f"✅ Twitter poster test: {result['status']}")
    print(f"   Draft: {result.get('draft_path')}")

    # Test thread
    thread_result = poster.post_thread([
        "1/ Thread about our new feature 🧵",
        "2/ It solves a major pain point for our users",
        "3/ Available now! Try it out and let us know what you think"
    ], require_approval=True)

    print(f"✅ Twitter thread test: {thread_result['status']}")
    print(f"   Draft: {thread_result.get('draft_path')}")

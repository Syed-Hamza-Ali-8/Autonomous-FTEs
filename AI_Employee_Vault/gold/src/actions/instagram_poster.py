"""
Instagram Poster

Posts content to Instagram and handles approval workflow.
Gold Tier Requirement #4: Social Media Integration (Instagram)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_interface import SocialMediaInterface


class InstagramPoster:
    """Posts content to Instagram with approval workflow."""

    def __init__(self, vault_path: str, access_token: Optional[str] = None,
                 account_id: Optional[str] = None, use_mock: bool = False):
        """
        Initialize Instagram poster.

        Args:
            vault_path: Path to Obsidian vault
            access_token: Instagram access token (optional if using mock)
            account_id: Instagram account ID (optional if using mock)
            use_mock: Use mock implementation for testing
        """
        self.vault_path = vault_path
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize Instagram API (real or mock)
        if self.use_mock:
            from gold.src.mocks.mock_social import MockInstagramAPI
            self.api: SocialMediaInterface = MockInstagramAPI()
        else:
            # Real Instagram API will be implemented in Phase 4
            from gold.src.mocks.mock_social import MockInstagramAPI
            self.api = MockInstagramAPI()

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None,
             require_approval: bool = True) -> Dict[str, Any]:
        """
        Post content to Instagram.

        Args:
            content: Caption text
            media_urls: Required list of image/video URLs (Instagram requires media)
            metadata: Optional metadata (hashtags, location, etc.)
            require_approval: Whether to require human approval before posting

        Returns:
            Dict with post_id, url, status, and timestamp
        """
        start_time = datetime.now()

        # Instagram requires media
        if not media_urls and not require_approval:
            raise ValueError("Instagram posts require at least one image or video")

        try:
            # Step 1: Create draft in vault for approval
            if require_approval:
                draft_result = self._create_draft(content, media_urls, metadata)

                # Log draft creation
                self.audit_logger.log_action(
                    action_type=ActionType.SOCIAL_POST_DRAFTED,
                    actor_type=ActorType.AGENT,
                    actor_id="instagram_poster",
                    status="success",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    domain="business",
                    target={"type": "instagram_draft", "draft_id": draft_result["draft_id"]},
                    metadata={"content_length": len(content), "media_count": len(media_urls or [])}
                )

                return {
                    "status": "pending_approval",
                    "draft_id": draft_result["draft_id"],
                    "draft_path": draft_result["draft_path"],
                    "message": "Draft created. Approve in vault to post."
                }

            # Step 2: Post to Instagram (if approved or no approval required)
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
                actor_id="instagram_poster",
                status="success",
                duration_ms=duration_ms,
                domain="business",
                target={"type": "instagram_post", "post_id": result["post_id"], "url": result.get("url")},
                metadata={
                    "content_length": len(content),
                    "media_count": len(media_urls or []),
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
                actor_id="instagram_poster",
                status="failure",
                duration_ms=duration_ms,
                domain="business",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def _create_draft(self, content: str, media_urls: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a draft post in the vault for approval."""
        draft_id = f"ig_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        draft_path = os.path.join(self.vault_path, "Needs_Action", f"{draft_id}.md")

        draft_content = f"""---
type: social_media_draft
platform: instagram
status: pending_approval
created: {datetime.now().isoformat()}
draft_id: {draft_id}
---

# Instagram Post Draft

## Caption
{content}

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

    poster = InstagramPoster(vault_path, use_mock=True)

    # Test draft creation
    result = poster.post(
        content="Beautiful sunset today! 🌅 #nature #photography",
        media_urls=["https://example.com/sunset.jpg"],
        require_approval=True
    )

    print(f"✅ Instagram poster test: {result['status']}")
    print(f"   Draft: {result.get('draft_path')}")

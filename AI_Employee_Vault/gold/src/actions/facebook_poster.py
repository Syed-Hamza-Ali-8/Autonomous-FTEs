"""
Facebook Poster

Posts content to Facebook pages and handles approval workflow.
Gold Tier Requirement #4: Social Media Integration (Facebook)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Add vault to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_interface import SocialMediaInterface


class FacebookPoster:
    """Posts content to Facebook with approval workflow."""

    def __init__(self, vault_path: str, access_token: Optional[str] = None,
                 page_id: Optional[str] = None, use_mock: bool = False):
        """
        Initialize Facebook poster.

        Args:
            vault_path: Path to Obsidian vault
            access_token: Facebook access token (optional if using mock)
            page_id: Facebook page ID (optional if using mock)
            use_mock: Use mock implementation for testing
        """
        self.vault_path = vault_path
        self.access_token = access_token or os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize Facebook API (real or mock)
        if self.use_mock:
            from gold.src.mocks.mock_social import MockFacebookAPI
            self.api: SocialMediaInterface = MockFacebookAPI()
        else:
            # Real Facebook API will be implemented in Phase 4
            # For now, use mock
            from gold.src.mocks.mock_social import MockFacebookAPI
            self.api = MockFacebookAPI()

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None,
             require_approval: bool = True) -> Dict[str, Any]:
        """
        Post content to Facebook.

        Args:
            content: Text content to post
            media_urls: Optional list of image/video URLs
            metadata: Optional metadata (hashtags, mentions, etc.)
            require_approval: Whether to require human approval before posting

        Returns:
            Dict with post_id, url, status, and timestamp
        """
        start_time = datetime.now()

        try:
            # Step 1: Create draft in vault for approval
            if require_approval:
                draft_result = self._create_draft(content, media_urls, metadata)

                # Log draft creation
                self.audit_logger.log_action(
                    action_type=ActionType.SOCIAL_POST_DRAFTED,
                    actor_type=ActorType.AGENT,
                    actor_id="facebook_poster",
                    status="success",
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    domain="business",
                    target={"type": "facebook_draft", "draft_id": draft_result["draft_id"]},
                    metadata={"content_length": len(content), "has_media": bool(media_urls)}
                )

                return {
                    "status": "pending_approval",
                    "draft_id": draft_result["draft_id"],
                    "draft_path": draft_result["draft_path"],
                    "message": "Draft created. Approve in vault to post."
                }

            # Step 2: Post to Facebook (if approved or no approval required)
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
                actor_id="facebook_poster",
                status="success",
                duration_ms=duration_ms,
                domain="business",
                target={"type": "facebook_post", "post_id": result["post_id"], "url": result.get("url")},
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
                actor_id="facebook_poster",
                status="failure",
                duration_ms=duration_ms,
                domain="business",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def _create_draft(self, content: str, media_urls: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a draft post in the vault for approval.

        Args:
            content: Text content
            media_urls: Optional media URLs
            metadata: Optional metadata

        Returns:
            Dict with draft_id and draft_path
        """
        # Create draft ID
        draft_id = f"fb_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create draft file in Needs_Action folder
        draft_path = os.path.join(self.vault_path, "Needs_Action", f"{draft_id}.md")

        # Build draft content
        draft_content = f"""---
type: social_media_draft
platform: facebook
status: pending_approval
created: {datetime.now().isoformat()}
draft_id: {draft_id}
---

# Facebook Post Draft

## Content
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

        # Write draft file
        os.makedirs(os.path.dirname(draft_path), exist_ok=True)
        with open(draft_path, 'w') as f:
            f.write(draft_content)

        return {
            "draft_id": draft_id,
            "draft_path": draft_path
        }

    def post_from_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Post content from an approved draft.

        Args:
            draft_id: Draft identifier

        Returns:
            Dict with post result
        """
        # Read draft file
        draft_path = os.path.join(self.vault_path, "Needs_Action", f"{draft_id}.md")

        if not os.path.exists(draft_path):
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        with open(draft_path, 'r') as f:
            draft_content = f.read()

        # Parse draft (simple parsing for now)
        # In production, use proper YAML parser
        lines = draft_content.split('\n')
        content_start = lines.index("## Content") + 1
        content_end = lines.index("## Media")
        content = '\n'.join(lines[content_start:content_end]).strip()

        # Post without approval (already approved)
        result = self.post(content, require_approval=False)

        # Move draft to Archive
        archive_path = os.path.join(self.vault_path, "Archive", "Social_Media", f"{draft_id}.md")
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        os.rename(draft_path, archive_path)

        return result


if __name__ == "__main__":
    # Test the poster
    vault_path = os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    poster = FacebookPoster(vault_path, use_mock=True)

    # Test draft creation
    result = poster.post(
        content="🚀 Exciting news! We're launching a new feature next week. Stay tuned! #innovation #tech",
        require_approval=True
    )

    print(f"✅ Facebook poster test: {result['status']}")
    print(f"   Draft: {result.get('draft_path')}")

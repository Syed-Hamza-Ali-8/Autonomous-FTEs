"""
Social Media Poster Module

Unified poster for Facebook, Instagram, and Twitter.
Handles post creation, scheduling, and publishing with approval workflow.

Gold Tier Requirements #4, #5: Social Media Integration
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..mocks.mock_facebook import MockFacebookAPI
from ..mocks.mock_instagram import MockInstagramAPI
from ..mocks.mock_twitter import MockTwitterAPI
from ..interfaces.social_media_interface import PostStatus
from ..core.audit_logger import AuditLogger, ActionType, ActorType


class SocialMediaPoster:
    """
    Unified social media poster.

    Features:
    - Post to multiple platforms simultaneously
    - Draft and schedule posts
    - Approval workflow for sensitive posts
    - Cross-platform analytics
    """

    def __init__(
        self,
        vault_path: str,
        use_mock: bool = True
    ):
        """
        Initialize social media poster.

        Args:
            vault_path: Path to Obsidian vault
            use_mock: Use mock APIs (True) or real APIs (False)
        """
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.logger = logging.getLogger(__name__)

        # Create directories if they don't exist
        self.pending_approval.mkdir(parents=True, exist_ok=True)
        self.approved.mkdir(parents=True, exist_ok=True)

        # Initialize platform APIs
        if use_mock:
            self.facebook = MockFacebookAPI()
            self.instagram = MockInstagramAPI()
            self.twitter = MockTwitterAPI()
            self.logger.info("Using Mock Social Media APIs")
        else:
            # TODO: Initialize real APIs in Phase 4
            raise NotImplementedError("Real social media APIs not yet implemented")

        # Initialize audit logger
        self.audit_logger = AuditLogger(vault_path)

        self.logger.info("Social Media Poster initialized")

    def create_post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Create a post for one or more platforms.

        Args:
            content: Post text content
            platforms: List of platforms ("facebook", "instagram", "twitter")
            media_urls: Optional list of media URLs
            tags: Optional list of hashtags/mentions
            scheduled_time: Optional time to schedule post
            require_approval: Whether to require human approval

        Returns:
            Dictionary with post IDs for each platform
        """
        result = {
            "status": "pending_approval" if require_approval else "draft",
            "platforms": {},
            "created_at": datetime.now().isoformat()
        }

        try:
            # Validate platforms
            valid_platforms = ["facebook", "instagram", "twitter"]
            for platform in platforms:
                if platform.lower() not in valid_platforms:
                    raise ValueError(f"Invalid platform: {platform}")

            # Create posts on each platform
            for platform in platforms:
                platform_lower = platform.lower()

                try:
                    if platform_lower == "facebook":
                        post = self.facebook.create_post(
                            content=content,
                            media_urls=media_urls,
                            scheduled_time=scheduled_time,
                            tags=tags
                        )
                        result["platforms"]["facebook"] = post

                    elif platform_lower == "instagram":
                        # Instagram requires media
                        if not media_urls:
                            self.logger.warning("Instagram requires media URLs, skipping")
                            result["platforms"]["instagram"] = {
                                "error": "Instagram requires at least one media URL"
                            }
                            continue

                        post = self.instagram.create_post(
                            content=content,
                            media_urls=media_urls,
                            scheduled_time=scheduled_time,
                            tags=tags
                        )
                        result["platforms"]["instagram"] = post

                    elif platform_lower == "twitter":
                        # Twitter has 280 character limit
                        if len(content) > 280:
                            self.logger.warning(f"Twitter content too long ({len(content)} chars), truncating")
                            twitter_content = content[:277] + "..."
                        else:
                            twitter_content = content

                        post = self.twitter.create_post(
                            content=twitter_content,
                            media_urls=media_urls,
                            scheduled_time=scheduled_time,
                            tags=tags
                        )
                        result["platforms"]["twitter"] = post

                    self.logger.info(f"Created post on {platform}")

                except Exception as e:
                    self.logger.error(f"Error creating post on {platform}: {e}")
                    result["platforms"][platform_lower] = {"error": str(e)}

            # Create approval file if required
            if require_approval:
                approval_file = self._create_approval_file(result, content, platforms)
                result["approval_file"] = str(approval_file)

            # Log to audit
            self.audit_logger.log_action(
                action_type=ActionType.SOCIAL_POST_DRAFTED,
                actor_type=ActorType.AGENT,
                actor_id="social_media_poster",
                status="success",
                duration_ms=0,
                domain="business",
                context={
                    "platforms": platforms,
                    "require_approval": require_approval
                }
            )

        except Exception as e:
            self.logger.error(f"Error creating post: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def publish_post(
        self,
        post_ids: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Publish draft posts.

        Args:
            post_ids: Dictionary mapping platform names to post IDs

        Returns:
            Dictionary with publish results for each platform
        """
        result = {
            "status": "published",
            "platforms": {},
            "published_at": datetime.now().isoformat()
        }

        try:
            for platform, post_id in post_ids.items():
                try:
                    if platform == "facebook":
                        post = self.facebook.publish_post(post_id)
                        result["platforms"]["facebook"] = post

                    elif platform == "instagram":
                        post = self.instagram.publish_post(post_id)
                        result["platforms"]["instagram"] = post

                    elif platform == "twitter":
                        post = self.twitter.publish_post(post_id)
                        result["platforms"]["twitter"] = post

                    self.logger.info(f"Published post on {platform}: {post_id}")

                except Exception as e:
                    self.logger.error(f"Error publishing post on {platform}: {e}")
                    result["platforms"][platform] = {"error": str(e)}

            # Log to audit
            self.audit_logger.log_action(
                action_type=ActionType.SOCIAL_POST_PUBLISHED,
                actor_type=ActorType.AGENT,
                actor_id="social_media_poster",
                status="success",
                duration_ms=0,
                domain="business",
                context={
                    "platforms": list(post_ids.keys())
                }
            )

        except Exception as e:
            self.logger.error(f"Error publishing posts: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def get_post_analytics(
        self,
        platform: str,
        post_id: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific post.

        Args:
            platform: Platform name
            post_id: Post ID

        Returns:
            Post analytics
        """
        try:
            if platform == "facebook":
                post = self.facebook.get_post(post_id)
            elif platform == "instagram":
                post = self.instagram.get_post(post_id)
            elif platform == "twitter":
                post = self.twitter.get_post(post_id)
            else:
                raise ValueError(f"Invalid platform: {platform}")

            return {
                "platform": platform,
                "post_id": post_id,
                "status": post["status"],
                "engagement": post["engagement"],
                "reach": post.get("reach", 0),
                "impressions": post.get("impressions", 0),
                "created_at": post["created_at"],
                "published_at": post.get("published_at")
            }

        except Exception as e:
            self.logger.error(f"Error getting post analytics: {e}")
            return {"error": str(e)}

    def _create_approval_file(
        self,
        post_data: Dict[str, Any],
        content: str,
        platforms: List[str]
    ) -> Path:
        """Create approval request file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"SOCIAL_POST_{timestamp}.md"
        filepath = self.pending_approval / filename

        # Extract post IDs
        post_ids = {}
        for platform, data in post_data["platforms"].items():
            if "id" in data:
                post_ids[platform] = data["id"]

        approval_content = f"""---
type: approval_request
action: social_media_post
platforms: {', '.join(platforms)}
created: {datetime.now().isoformat()}
status: pending
---

## Social Media Post Approval

**Platforms**: {', '.join(platforms)}
**Created**: {datetime.now().isoformat()}

### Post Content
```
{content}
```

### Post IDs
{self._format_post_ids(post_ids)}

### To Approve
Move this file to `/Approved` folder.

### To Reject
Move this file to `/Rejected` folder or delete it.

### Notes
- This post will be published to {len(platforms)} platform(s)
- Review content for tone, accuracy, and brand alignment
- Check for typos and formatting issues
"""

        filepath.write_text(approval_content)
        self.logger.info(f"Created approval file: {filename}")

        return filepath

    def _format_post_ids(self, post_ids: Dict[str, str]) -> str:
        """Format post IDs for display."""
        if not post_ids:
            return "No post IDs available"

        lines = []
        for platform, post_id in post_ids.items():
            lines.append(f"- **{platform.capitalize()}**: `{post_id}`")

        return "\n".join(lines)


def main():
    """Main entry point for social media poster."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Social Media Poster")
    parser.add_argument(
        "--vault-path",
        default=os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"),
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--content",
        required=True,
        help="Post content"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["facebook", "instagram", "twitter"],
        help="Platforms to post to"
    )
    parser.add_argument(
        "--no-approval",
        action="store_true",
        help="Skip approval workflow"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create poster
    poster = SocialMediaPoster(vault_path=args.vault_path)

    # Create post
    result = poster.create_post(
        content=args.content,
        platforms=args.platforms,
        require_approval=not args.no_approval
    )

    print(f"Post created: {result}")


if __name__ == "__main__":
    main()

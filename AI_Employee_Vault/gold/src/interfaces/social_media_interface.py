"""
Social Media Interface Module

Abstract interface for social media platforms (Facebook, Instagram, Twitter).
Enables swapping between Mock and Real implementations.

Gold Tier Requirements #4, #5: Social Media Integration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PostStatus(Enum):
    """Status of a social media post"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class EngagementType(Enum):
    """Types of social media engagement"""
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    RETWEET = "retweet"
    REPLY = "reply"
    MENTION = "mention"
    DIRECT_MESSAGE = "direct_message"


class SocialMediaInterface(ABC):
    """
    Abstract interface for social media platforms.

    Implementations:
    - MockFacebookAPI (Phase 2)
    - MockInstagramAPI (Phase 2)
    - MockTwitterAPI (Phase 2)
    - RealFacebookAPI (Phase 4 - optional)
    - RealInstagramAPI (Phase 4 - optional)
    - RealTwitterAPI (Phase 4 - optional)
    """

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name.

        Returns:
            Platform name (e.g., "Facebook", "Instagram", "Twitter")
        """
        pass

    @abstractmethod
    def create_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new post (draft or published).

        Args:
            content: Post text content
            media_urls: Optional list of media URLs to attach
            scheduled_time: Optional time to schedule post
            tags: Optional list of hashtags/mentions

        Returns:
            Post object with id, status, created_at, etc.
        """
        pass

    @abstractmethod
    def publish_post(self, post_id: str) -> Dict[str, Any]:
        """
        Publish a draft post.

        Args:
            post_id: ID of the draft post

        Returns:
            Updated post object with published status
        """
        pass

    @abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post.

        Args:
            post_id: ID of the post to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_posts(
        self,
        status: Optional[PostStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get posts with optional filters.

        Args:
            status: Filter by post status
            start_date: Filter posts after this date (YYYY-MM-DD)
            end_date: Filter posts before this date (YYYY-MM-DD)
            limit: Maximum number of posts to return

        Returns:
            List of post objects
        """
        pass

    @abstractmethod
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Get a specific post by ID.

        Args:
            post_id: ID of the post

        Returns:
            Post object
        """
        pass

    @abstractmethod
    def get_engagement(
        self,
        post_id: Optional[str] = None,
        engagement_type: Optional[EngagementType] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get engagement (likes, comments, shares, etc.).

        Args:
            post_id: Optional filter by specific post
            engagement_type: Optional filter by engagement type
            start_date: Filter engagement after this date (YYYY-MM-DD)
            end_date: Filter engagement before this date (YYYY-MM-DD)
            limit: Maximum number of engagement items to return

        Returns:
            List of engagement objects
        """
        pass

    @abstractmethod
    def get_analytics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Analytics object with metrics (reach, engagement, etc.)
        """
        pass

    @abstractmethod
    def get_mentions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get mentions of your account.

        Args:
            start_date: Filter mentions after this date (YYYY-MM-DD)
            end_date: Filter mentions before this date (YYYY-MM-DD)
            limit: Maximum number of mentions to return

        Returns:
            List of mention objects
        """
        pass

    @abstractmethod
    def get_direct_messages(
        self,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get direct messages.

        Args:
            unread_only: Only return unread messages
            limit: Maximum number of messages to return

        Returns:
            List of message objects
        """
        pass

    @abstractmethod
    def send_direct_message(
        self,
        recipient_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send a direct message.

        Args:
            recipient_id: ID of the recipient
            content: Message content

        Returns:
            Message object
        """
        pass

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """
        Get account profile information.

        Returns:
            Profile object with followers, following, bio, etc.
        """
        pass

    @abstractmethod
    def update_profile(
        self,
        bio: Optional[str] = None,
        profile_image_url: Optional[str] = None,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update account profile.

        Args:
            bio: Optional new bio text
            profile_image_url: Optional new profile image URL
            website: Optional new website URL

        Returns:
            Updated profile object
        """
        pass

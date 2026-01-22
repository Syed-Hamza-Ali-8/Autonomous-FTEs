"""
Social Media Interface

Abstract interface for social media platforms (Facebook, Instagram, Twitter).
Enables consistent API across different platforms and mock/real implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class SocialMediaInterface(ABC):
    """Abstract interface for social media platforms."""

    @abstractmethod
    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Post content to the platform.

        Args:
            content: Text content to post
            media_urls: Optional list of media URLs to attach
            metadata: Optional platform-specific metadata (hashtags, mentions, etc.)

        Returns:
            Dict with post_id, url, timestamp, and platform-specific data
        """
        pass

    @abstractmethod
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific post by ID.

        Args:
            post_id: Platform-specific post identifier

        Returns:
            Dict with post data including engagement metrics
        """
        pass

    @abstractmethod
    def get_comments(self, post_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get comments on a post.

        Args:
            post_id: Platform-specific post identifier
            since: Optional datetime to filter comments after this time

        Returns:
            List of comment dicts with id, author, text, timestamp
        """
        pass

    @abstractmethod
    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """
        Reply to a comment.

        Args:
            comment_id: Platform-specific comment identifier
            reply_text: Text of the reply

        Returns:
            Dict with reply_id and timestamp
        """
        pass

    @abstractmethod
    def get_messages(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get direct messages.

        Args:
            since: Optional datetime to filter messages after this time

        Returns:
            List of message dicts with id, sender, text, timestamp
        """
        pass

    @abstractmethod
    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """
        Send a direct message.

        Args:
            recipient_id: Platform-specific recipient identifier
            message_text: Text of the message

        Returns:
            Dict with message_id and timestamp
        """
        pass

    @abstractmethod
    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get analytics for the specified date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dict with engagement metrics (likes, comments, shares, reach, impressions)
        """
        pass

    @abstractmethod
    def get_mentions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get mentions of the account.

        Args:
            since: Optional datetime to filter mentions after this time

        Returns:
            List of mention dicts with id, author, text, timestamp
        """
        pass

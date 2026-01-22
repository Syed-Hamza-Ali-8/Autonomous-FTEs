"""
Mock Social Media APIs

Mock implementations of Facebook, Instagram, and Twitter APIs for testing.
Implements SocialMediaInterface for consistent behavior.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.interfaces.social_interface import SocialMediaInterface


class MockFacebookAPI(SocialMediaInterface):
    """Mock Facebook API for testing."""

    def __init__(self):
        self._posts = []
        self._comments = []
        self._messages = []
        self._mentions = []

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a mock Facebook post."""
        post_id = f"fb_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()

        post = {
            "post_id": post_id,
            "platform": "facebook",
            "content": content,
            "media_urls": media_urls or [],
            "metadata": metadata or {},
            "url": f"https://facebook.com/posts/{post_id}",
            "timestamp": timestamp.isoformat(),
            "engagement": {
                "likes": random.randint(10, 100),
                "comments": random.randint(2, 20),
                "shares": random.randint(1, 15)
            }
        }

        self._posts.append(post)
        return post

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a mock Facebook post."""
        for post in self._posts:
            if post["post_id"] == post_id:
                return post
        raise ValueError(f"Post not found: {post_id}")

    def get_comments(self, post_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock comments on a post."""
        comments = [c for c in self._comments if c["post_id"] == post_id]
        if since:
            comments = [c for c in comments if datetime.fromisoformat(c["timestamp"]) > since]
        return comments

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """Reply to a mock comment."""
        reply_id = f"fb_reply_{uuid.uuid4().hex[:12]}"
        reply = {
            "reply_id": reply_id,
            "comment_id": comment_id,
            "text": reply_text,
            "timestamp": datetime.now().isoformat()
        }
        return reply

    def get_messages(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock direct messages."""
        messages = self._messages.copy()
        if since:
            messages = [m for m in messages if datetime.fromisoformat(m["timestamp"]) > since]
        return messages

    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """Send a mock direct message."""
        message_id = f"fb_msg_{uuid.uuid4().hex[:12]}"
        message = {
            "message_id": message_id,
            "recipient_id": recipient_id,
            "text": message_text,
            "timestamp": datetime.now().isoformat()
        }
        self._messages.append(message)
        return message

    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get mock analytics."""
        days = (end_date - start_date).days
        return {
            "platform": "facebook",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": {
                "total_posts": random.randint(5, 20),
                "total_likes": random.randint(100, 1000),
                "total_comments": random.randint(20, 200),
                "total_shares": random.randint(10, 100),
                "reach": random.randint(1000, 10000),
                "impressions": random.randint(2000, 20000),
                "engagement_rate": round(random.uniform(2.0, 8.0), 2)
            }
        }

    def get_mentions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock mentions."""
        mentions = self._mentions.copy()
        if since:
            mentions = [m for m in mentions if datetime.fromisoformat(m["timestamp"]) > since]
        return mentions


class MockInstagramAPI(SocialMediaInterface):
    """Mock Instagram API for testing."""

    def __init__(self):
        self._posts = []
        self._comments = []
        self._messages = []
        self._mentions = []

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a mock Instagram post."""
        post_id = f"ig_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()

        post = {
            "post_id": post_id,
            "platform": "instagram",
            "content": content,
            "media_urls": media_urls or [],
            "metadata": metadata or {},
            "url": f"https://instagram.com/p/{post_id}",
            "timestamp": timestamp.isoformat(),
            "engagement": {
                "likes": random.randint(50, 500),
                "comments": random.randint(5, 50),
                "saves": random.randint(2, 30)
            }
        }

        self._posts.append(post)
        return post

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a mock Instagram post."""
        for post in self._posts:
            if post["post_id"] == post_id:
                return post
        raise ValueError(f"Post not found: {post_id}")

    def get_comments(self, post_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock comments on a post."""
        comments = [c for c in self._comments if c["post_id"] == post_id]
        if since:
            comments = [c for c in comments if datetime.fromisoformat(c["timestamp"]) > since]
        return comments

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """Reply to a mock comment."""
        reply_id = f"ig_reply_{uuid.uuid4().hex[:12]}"
        reply = {
            "reply_id": reply_id,
            "comment_id": comment_id,
            "text": reply_text,
            "timestamp": datetime.now().isoformat()
        }
        return reply

    def get_messages(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock direct messages."""
        messages = self._messages.copy()
        if since:
            messages = [m for m in messages if datetime.fromisoformat(m["timestamp"]) > since]
        return messages

    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """Send a mock direct message."""
        message_id = f"ig_msg_{uuid.uuid4().hex[:12]}"
        message = {
            "message_id": message_id,
            "recipient_id": recipient_id,
            "text": message_text,
            "timestamp": datetime.now().isoformat()
        }
        self._messages.append(message)
        return message

    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get mock analytics."""
        days = (end_date - start_date).days
        return {
            "platform": "instagram",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": {
                "total_posts": random.randint(5, 15),
                "total_likes": random.randint(200, 2000),
                "total_comments": random.randint(30, 300),
                "total_saves": random.randint(10, 150),
                "reach": random.randint(2000, 20000),
                "impressions": random.randint(4000, 40000),
                "engagement_rate": round(random.uniform(3.0, 10.0), 2)
            }
        }

    def get_mentions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock mentions."""
        mentions = self._mentions.copy()
        if since:
            mentions = [m for m in mentions if datetime.fromisoformat(m["timestamp"]) > since]
        return mentions


class MockTwitterAPI(SocialMediaInterface):
    """Mock Twitter API for testing."""

    def __init__(self):
        self._posts = []
        self._comments = []
        self._messages = []
        self._mentions = []

    def post(self, content: str, media_urls: Optional[List[str]] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a mock tweet."""
        post_id = f"tw_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now()

        post = {
            "post_id": post_id,
            "platform": "twitter",
            "content": content,
            "media_urls": media_urls or [],
            "metadata": metadata or {},
            "url": f"https://twitter.com/status/{post_id}",
            "timestamp": timestamp.isoformat(),
            "engagement": {
                "likes": random.randint(20, 200),
                "retweets": random.randint(5, 50),
                "replies": random.randint(2, 30),
                "impressions": random.randint(500, 5000)
            }
        }

        self._posts.append(post)
        return post

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a mock tweet."""
        for post in self._posts:
            if post["post_id"] == post_id:
                return post
        raise ValueError(f"Post not found: {post_id}")

    def get_comments(self, post_id: str, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock replies to a tweet."""
        comments = [c for c in self._comments if c["post_id"] == post_id]
        if since:
            comments = [c for c in comments if datetime.fromisoformat(c["timestamp"]) > since]
        return comments

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict[str, Any]:
        """Reply to a mock tweet."""
        reply_id = f"tw_reply_{uuid.uuid4().hex[:12]}"
        reply = {
            "reply_id": reply_id,
            "comment_id": comment_id,
            "text": reply_text,
            "timestamp": datetime.now().isoformat()
        }
        return reply

    def get_messages(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock direct messages."""
        messages = self._messages.copy()
        if since:
            messages = [m for m in messages if datetime.fromisoformat(m["timestamp"]) > since]
        return messages

    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """Send a mock direct message."""
        message_id = f"tw_msg_{uuid.uuid4().hex[:12]}"
        message = {
            "message_id": message_id,
            "recipient_id": recipient_id,
            "text": message_text,
            "timestamp": datetime.now().isoformat()
        }
        self._messages.append(message)
        return message

    def get_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get mock analytics."""
        days = (end_date - start_date).days
        return {
            "platform": "twitter",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": {
                "total_tweets": random.randint(10, 50),
                "total_likes": random.randint(100, 1500),
                "total_retweets": random.randint(20, 300),
                "total_replies": random.randint(10, 150),
                "impressions": random.randint(5000, 50000),
                "profile_visits": random.randint(100, 1000),
                "engagement_rate": round(random.uniform(1.5, 6.0), 2)
            }
        }

    def get_mentions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get mock mentions."""
        mentions = self._mentions.copy()
        if since:
            mentions = [m for m in mentions if datetime.fromisoformat(m["timestamp"]) > since]
        return mentions


if __name__ == "__main__":
    # Test mock APIs
    print("Testing Mock Social Media APIs...")

    # Test Facebook
    fb = MockFacebookAPI()
    fb_post = fb.post("Test Facebook post", media_urls=["https://example.com/image.jpg"])
    print(f"✅ Facebook: {fb_post['post_id']} - {fb_post['engagement']['likes']} likes")

    # Test Instagram
    ig = MockInstagramAPI()
    ig_post = ig.post("Test Instagram post", media_urls=["https://example.com/photo.jpg"])
    print(f"✅ Instagram: {ig_post['post_id']} - {ig_post['engagement']['likes']} likes")

    # Test Twitter
    tw = MockTwitterAPI()
    tw_post = tw.post("Test tweet")
    print(f"✅ Twitter: {tw_post['post_id']} - {tw_post['engagement']['likes']} likes")

    # Test analytics
    start = datetime.now() - timedelta(days=7)
    end = datetime.now()
    fb_analytics = fb.get_analytics(start, end)
    print(f"✅ Facebook Analytics: {fb_analytics['metrics']['engagement_rate']}% engagement")

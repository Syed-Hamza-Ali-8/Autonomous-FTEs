"""
Mock Instagram API Implementation

Mock implementation of Instagram API for development and testing.
Provides realistic data without requiring real Instagram API credentials.

Gold Tier Requirement #4: Instagram Integration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..interfaces.social_media_interface import (
    SocialMediaInterface,
    PostStatus,
    EngagementType
)
import random
import uuid


class MockInstagramAPI(SocialMediaInterface):
    """
    Mock Instagram API implementation.

    Provides realistic mock data for:
    - Posts (feed posts, stories, reels)
    - Engagement (likes, comments, saves)
    - Analytics (reach, impressions, engagement rate)
    - Mentions and direct messages
    - Profile information
    """

    def __init__(self):
        """Initialize mock Instagram API with sample data."""
        self.platform_name = "Instagram"
        self._posts = self._generate_mock_posts()
        self._engagement = self._generate_mock_engagement()
        self._mentions = self._generate_mock_mentions()
        self._messages = self._generate_mock_messages()
        self._profile = self._generate_mock_profile()

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.platform_name

    def create_post(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Instagram post."""
        post_id = f"ig_post_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        status = PostStatus.DRAFT
        if scheduled_time:
            status = PostStatus.SCHEDULED
        elif scheduled_time is None:
            status = PostStatus.PUBLISHED

        # Instagram requires at least one media URL
        if not media_urls and status == PostStatus.PUBLISHED:
            media_urls = ["https://example.com/placeholder.jpg"]

        post = {
            "id": post_id,
            "platform": self.platform_name,
            "content": content,
            "media_urls": media_urls or [],
            "tags": tags or [],
            "status": status.value,
            "post_type": "feed",  # feed, story, reel
            "created_at": now.isoformat(),
            "published_at": now.isoformat() if status == PostStatus.PUBLISHED else None,
            "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
            "engagement": {
                "likes": 0,
                "comments": 0,
                "saves": 0
            },
            "reach": 0,
            "impressions": 0
        }

        self._posts.append(post)
        return post

    def publish_post(self, post_id: str) -> Dict[str, Any]:
        """Publish a draft post."""
        post = self.get_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        if post["status"] != PostStatus.DRAFT.value:
            raise ValueError(f"Post {post_id} is not a draft")

        # Instagram requires media
        if not post["media_urls"]:
            raise ValueError("Instagram posts require at least one media URL")

        post["status"] = PostStatus.PUBLISHED.value
        post["published_at"] = datetime.now().isoformat()

        # Simulate initial engagement
        post["engagement"]["likes"] = random.randint(10, 80)
        post["engagement"]["comments"] = random.randint(0, 15)
        post["engagement"]["saves"] = random.randint(0, 10)
        post["reach"] = random.randint(150, 1500)
        post["impressions"] = random.randint(200, 2000)

        return post

    def delete_post(self, post_id: str) -> bool:
        """Delete a post."""
        self._posts = [p for p in self._posts if p["id"] != post_id]
        return True

    def get_posts(
        self,
        status: Optional[PostStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get posts with optional filters."""
        posts = self._posts.copy()

        # Filter by status
        if status:
            posts = [p for p in posts if p["status"] == status.value]

        # Filter by date range
        if start_date:
            posts = [p for p in posts if p["created_at"] >= start_date]
        if end_date:
            posts = [p for p in posts if p["created_at"] <= end_date]

        # Sort by created_at descending
        posts.sort(key=lambda x: x["created_at"], reverse=True)

        return posts[:limit]

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID."""
        for post in self._posts:
            if post["id"] == post_id:
                return post
        raise ValueError(f"Post {post_id} not found")

    def get_engagement(
        self,
        post_id: Optional[str] = None,
        engagement_type: Optional[EngagementType] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get engagement (likes, comments, saves)."""
        engagement = self._engagement.copy()

        # Filter by post_id
        if post_id:
            engagement = [e for e in engagement if e["post_id"] == post_id]

        # Filter by engagement type
        if engagement_type:
            engagement = [e for e in engagement if e["type"] == engagement_type.value]

        # Filter by date range
        if start_date:
            engagement = [e for e in engagement if e["created_at"] >= start_date]
        if end_date:
            engagement = [e for e in engagement if e["created_at"] <= end_date]

        # Sort by created_at descending
        engagement.sort(key=lambda x: x["created_at"], reverse=True)

        return engagement[:limit]

    def get_analytics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get analytics for a date range."""
        # Filter posts in date range
        posts = [
            p for p in self._posts
            if p["status"] == PostStatus.PUBLISHED.value
            and start_date <= p["published_at"] <= end_date
        ]

        # Calculate metrics
        total_posts = len(posts)
        total_likes = sum(p["engagement"]["likes"] for p in posts)
        total_comments = sum(p["engagement"]["comments"] for p in posts)
        total_saves = sum(p["engagement"]["saves"] for p in posts)
        total_reach = sum(p["reach"] for p in posts)
        total_impressions = sum(p["impressions"] for p in posts)

        total_engagement = total_likes + total_comments + total_saves
        engagement_rate = (total_engagement / total_impressions * 100) if total_impressions > 0 else 0

        return {
            "platform": self.platform_name,
            "start_date": start_date,
            "end_date": end_date,
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_saves": total_saves,
            "total_engagement": total_engagement,
            "total_reach": total_reach,
            "total_impressions": total_impressions,
            "engagement_rate": round(engagement_rate, 2),
            "avg_engagement_per_post": round(total_engagement / total_posts, 2) if total_posts > 0 else 0,
            "avg_reach_per_post": round(total_reach / total_posts, 2) if total_posts > 0 else 0,
            "profile_visits": random.randint(50, 500),
            "website_clicks": random.randint(10, 100)
        }

    def get_mentions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get mentions of your account."""
        mentions = self._mentions.copy()

        # Filter by date range
        if start_date:
            mentions = [m for m in mentions if m["created_at"] >= start_date]
        if end_date:
            mentions = [m for m in mentions if m["created_at"] <= end_date]

        # Sort by created_at descending
        mentions.sort(key=lambda x: x["created_at"], reverse=True)

        return mentions[:limit]

    def get_direct_messages(
        self,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get direct messages."""
        messages = self._messages.copy()

        # Filter by unread
        if unread_only:
            messages = [m for m in messages if not m["read"]]

        # Sort by created_at descending
        messages.sort(key=lambda x: x["created_at"], reverse=True)

        return messages[:limit]

    def send_direct_message(
        self,
        recipient_id: str,
        content: str
    ) -> Dict[str, Any]:
        """Send a direct message."""
        message_id = f"ig_msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        message = {
            "id": message_id,
            "platform": self.platform_name,
            "recipient_id": recipient_id,
            "sender_id": "me",
            "content": content,
            "created_at": now.isoformat(),
            "read": False,
            "direction": "outgoing"
        }

        self._messages.append(message)
        return message

    def get_profile(self) -> Dict[str, Any]:
        """Get account profile information."""
        return self._profile.copy()

    def update_profile(
        self,
        bio: Optional[str] = None,
        profile_image_url: Optional[str] = None,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update account profile."""
        if bio:
            self._profile["bio"] = bio
        if profile_image_url:
            self._profile["profile_image_url"] = profile_image_url
        if website:
            self._profile["website"] = website

        self._profile["updated_at"] = datetime.now().isoformat()
        return self._profile.copy()

    # Private helper methods for generating mock data

    def _generate_mock_posts(self) -> List[Dict[str, Any]]:
        """Generate mock posts."""
        now = datetime.now()
        posts = []

        # Published feed posts
        for i in range(4):
            days_ago = i + 1
            published_at = (now - timedelta(days=days_ago)).isoformat()
            posts.append({
                "id": f"ig_post_{uuid.uuid4().hex[:12]}",
                "platform": self.platform_name,
                "content": f"Mock Instagram post from {days_ago} days ago 📸 #business #entrepreneur",
                "media_urls": [f"https://example.com/image_{i}.jpg"],
                "tags": ["#business", "#entrepreneur"],
                "status": PostStatus.PUBLISHED.value,
                "post_type": "feed",
                "created_at": published_at,
                "published_at": published_at,
                "scheduled_time": None,
                "engagement": {
                    "likes": random.randint(20, 150),
                    "comments": random.randint(0, 25),
                    "saves": random.randint(0, 15)
                },
                "reach": random.randint(300, 3000),
                "impressions": random.randint(400, 4000)
            })

        # Draft post
        posts.append({
            "id": f"ig_post_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "content": "Draft Instagram post - not yet published",
            "media_urls": ["https://example.com/draft.jpg"],
            "tags": [],
            "status": PostStatus.DRAFT.value,
            "post_type": "feed",
            "created_at": now.isoformat(),
            "published_at": None,
            "scheduled_time": None,
            "engagement": {"likes": 0, "comments": 0, "saves": 0},
            "reach": 0,
            "impressions": 0
        })

        return posts

    def _generate_mock_engagement(self) -> List[Dict[str, Any]]:
        """Generate mock engagement."""
        engagement = []
        now = datetime.now()

        # Get some published posts
        published_posts = [p for p in self._posts if p["status"] == PostStatus.PUBLISHED.value]

        for post in published_posts[:3]:
            # Likes
            for i in range(random.randint(10, 20)):
                engagement.append({
                    "id": f"ig_eng_{uuid.uuid4().hex[:12]}",
                    "platform": self.platform_name,
                    "post_id": post["id"],
                    "type": EngagementType.LIKE.value,
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "user_name": f"@user{random.randint(1, 100)}",
                    "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat()
                })

            # Comments
            for i in range(random.randint(0, 8)):
                engagement.append({
                    "id": f"ig_eng_{uuid.uuid4().hex[:12]}",
                    "platform": self.platform_name,
                    "post_id": post["id"],
                    "type": EngagementType.COMMENT.value,
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "user_name": f"@user{random.randint(1, 100)}",
                    "content": "Love this! 🔥",
                    "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat()
                })

        return engagement

    def _generate_mock_mentions(self) -> List[Dict[str, Any]]:
        """Generate mock mentions."""
        mentions = []
        now = datetime.now()

        for i in range(2):
            mentions.append({
                "id": f"ig_mention_{uuid.uuid4().hex[:12]}",
                "platform": self.platform_name,
                "user_id": f"user_{random.randint(1000, 9999)}",
                "user_name": f"@user{random.randint(1, 100)}",
                "content": f"Check out @my_business! Great content 👏",
                "post_url": f"https://instagram.com/p/{uuid.uuid4().hex[:12]}",
                "created_at": (now - timedelta(days=i+1)).isoformat()
            })

        return mentions

    def _generate_mock_messages(self) -> List[Dict[str, Any]]:
        """Generate mock direct messages."""
        messages = []
        now = datetime.now()

        # Incoming messages
        messages.append({
            "id": f"ig_msg_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "sender_id": "user_1234",
            "sender_name": "@potential_client",
            "recipient_id": "me",
            "content": "Hi! Love your content. Do you offer consulting services?",
            "created_at": (now - timedelta(hours=3)).isoformat(),
            "read": False,
            "direction": "incoming"
        })

        messages.append({
            "id": f"ig_msg_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "sender_id": "user_5678",
            "sender_name": "@happy_customer",
            "recipient_id": "me",
            "content": "Thanks for the amazing service! 🙌",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "direction": "incoming"
        })

        return messages

    def _generate_mock_profile(self) -> Dict[str, Any]:
        """Generate mock profile."""
        return {
            "platform": self.platform_name,
            "user_id": "ig_user_me",
            "username": "my_business",
            "display_name": "My Business | Growth Solutions",
            "bio": "Helping businesses scale 📈 | DM for inquiries | Link below 👇",
            "profile_image_url": "https://example.com/profile.jpg",
            "website": "https://mybusiness.com",
            "followers": 2450,
            "following": 180,
            "total_posts": len(self._posts),
            "verified": False,
            "business_account": True,
            "category": "Business Service",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now().isoformat()
        }

"""
Mock Twitter (X) API Implementation

Mock implementation of Twitter/X API for development and testing.
Provides realistic data without requiring real Twitter API credentials.

Gold Tier Requirement #5: Twitter Integration
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


class MockTwitterAPI(SocialMediaInterface):
    """
    Mock Twitter/X API implementation.

    Provides realistic mock data for:
    - Tweets (posts, threads, retweets)
    - Engagement (likes, retweets, replies, quotes)
    - Analytics (impressions, engagement rate, profile visits)
    - Mentions and direct messages
    - Profile information
    """

    def __init__(self):
        """Initialize mock Twitter API with sample data."""
        self.platform_name = "Twitter"
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
        """Create a new tweet."""
        post_id = f"tw_post_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        # Twitter has 280 character limit
        if len(content) > 280:
            raise ValueError(f"Tweet content exceeds 280 characters ({len(content)} chars)")

        status = PostStatus.DRAFT
        if scheduled_time:
            status = PostStatus.SCHEDULED
        elif scheduled_time is None:
            status = PostStatus.PUBLISHED

        post = {
            "id": post_id,
            "platform": self.platform_name,
            "content": content,
            "media_urls": media_urls or [],
            "tags": tags or [],
            "status": status.value,
            "post_type": "tweet",  # tweet, retweet, quote_tweet, thread
            "created_at": now.isoformat(),
            "published_at": now.isoformat() if status == PostStatus.PUBLISHED else None,
            "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
            "engagement": {
                "likes": 0,
                "retweets": 0,
                "replies": 0,
                "quotes": 0
            },
            "impressions": 0,
            "profile_visits": 0,
            "url_clicks": 0
        }

        self._posts.append(post)
        return post

    def publish_post(self, post_id: str) -> Dict[str, Any]:
        """Publish a draft tweet."""
        post = self.get_post(post_id)
        if not post:
            raise ValueError(f"Tweet {post_id} not found")

        if post["status"] != PostStatus.DRAFT.value:
            raise ValueError(f"Tweet {post_id} is not a draft")

        post["status"] = PostStatus.PUBLISHED.value
        post["published_at"] = datetime.now().isoformat()

        # Simulate initial engagement
        post["engagement"]["likes"] = random.randint(5, 60)
        post["engagement"]["retweets"] = random.randint(0, 15)
        post["engagement"]["replies"] = random.randint(0, 10)
        post["engagement"]["quotes"] = random.randint(0, 3)
        post["impressions"] = random.randint(200, 2500)
        post["profile_visits"] = random.randint(10, 100)
        post["url_clicks"] = random.randint(0, 50)

        return post

    def delete_post(self, post_id: str) -> bool:
        """Delete a tweet."""
        self._posts = [p for p in self._posts if p["id"] != post_id]
        return True

    def get_posts(
        self,
        status: Optional[PostStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get tweets with optional filters."""
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
        """Get a specific tweet by ID."""
        for post in self._posts:
            if post["id"] == post_id:
                return post
        raise ValueError(f"Tweet {post_id} not found")

    def get_engagement(
        self,
        post_id: Optional[str] = None,
        engagement_type: Optional[EngagementType] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get engagement (likes, retweets, replies, quotes)."""
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
        total_retweets = sum(p["engagement"]["retweets"] for p in posts)
        total_replies = sum(p["engagement"]["replies"] for p in posts)
        total_quotes = sum(p["engagement"]["quotes"] for p in posts)
        total_impressions = sum(p["impressions"] for p in posts)
        total_profile_visits = sum(p["profile_visits"] for p in posts)
        total_url_clicks = sum(p["url_clicks"] for p in posts)

        total_engagement = total_likes + total_retweets + total_replies + total_quotes
        engagement_rate = (total_engagement / total_impressions * 100) if total_impressions > 0 else 0

        return {
            "platform": self.platform_name,
            "start_date": start_date,
            "end_date": end_date,
            "total_tweets": total_posts,
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_replies": total_replies,
            "total_quotes": total_quotes,
            "total_engagement": total_engagement,
            "total_impressions": total_impressions,
            "total_profile_visits": total_profile_visits,
            "total_url_clicks": total_url_clicks,
            "engagement_rate": round(engagement_rate, 2),
            "avg_engagement_per_tweet": round(total_engagement / total_posts, 2) if total_posts > 0 else 0,
            "avg_impressions_per_tweet": round(total_impressions / total_posts, 2) if total_posts > 0 else 0
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
        message_id = f"tw_msg_{uuid.uuid4().hex[:12]}"
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
            # Twitter bio has 160 character limit
            if len(bio) > 160:
                raise ValueError(f"Bio exceeds 160 characters ({len(bio)} chars)")
            self._profile["bio"] = bio
        if profile_image_url:
            self._profile["profile_image_url"] = profile_image_url
        if website:
            self._profile["website"] = website

        self._profile["updated_at"] = datetime.now().isoformat()
        return self._profile.copy()

    # Private helper methods for generating mock data

    def _generate_mock_posts(self) -> List[Dict[str, Any]]:
        """Generate mock tweets."""
        now = datetime.now()
        posts = []

        # Published tweets
        tweet_contents = [
            "Just launched our new product! Check it out 🚀 #startup #innovation",
            "5 tips for growing your business in 2026:\n1. Focus on customer value\n2. Build strong relationships\n3. Embrace automation\n4. Stay adaptable\n5. Never stop learning",
            "Excited to announce our partnership with @partner_company! Big things coming 🎉",
            "Behind the scenes at our office today. Team is crushing it! 💪 #teamwork",
            "New blog post: How AI is transforming business operations. Link in bio 📝"
        ]

        for i in range(5):
            days_ago = i + 1
            published_at = (now - timedelta(days=days_ago)).isoformat()
            posts.append({
                "id": f"tw_post_{uuid.uuid4().hex[:12]}",
                "platform": self.platform_name,
                "content": tweet_contents[i] if i < len(tweet_contents) else f"Mock tweet from {days_ago} days ago",
                "media_urls": [] if i % 2 == 0 else [f"https://example.com/image_{i}.jpg"],
                "tags": ["#business", "#growth"],
                "status": PostStatus.PUBLISHED.value,
                "post_type": "tweet",
                "created_at": published_at,
                "published_at": published_at,
                "scheduled_time": None,
                "engagement": {
                    "likes": random.randint(10, 100),
                    "retweets": random.randint(0, 20),
                    "replies": random.randint(0, 15),
                    "quotes": random.randint(0, 5)
                },
                "impressions": random.randint(300, 3500),
                "profile_visits": random.randint(15, 150),
                "url_clicks": random.randint(0, 80)
            })

        # Draft tweet
        posts.append({
            "id": f"tw_post_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "content": "Draft tweet - not yet published",
            "media_urls": [],
            "tags": [],
            "status": PostStatus.DRAFT.value,
            "post_type": "tweet",
            "created_at": now.isoformat(),
            "published_at": None,
            "scheduled_time": None,
            "engagement": {"likes": 0, "retweets": 0, "replies": 0, "quotes": 0},
            "impressions": 0,
            "profile_visits": 0,
            "url_clicks": 0
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
            for i in range(random.randint(5, 15)):
                engagement.append({
                    "id": f"tw_eng_{uuid.uuid4().hex[:12]}",
                    "platform": self.platform_name,
                    "post_id": post["id"],
                    "type": EngagementType.LIKE.value,
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "user_name": f"@user{random.randint(1, 100)}",
                    "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat()
                })

            # Retweets
            for i in range(random.randint(0, 5)):
                engagement.append({
                    "id": f"tw_eng_{uuid.uuid4().hex[:12]}",
                    "platform": self.platform_name,
                    "post_id": post["id"],
                    "type": EngagementType.RETWEET.value,
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "user_name": f"@user{random.randint(1, 100)}",
                    "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat()
                })

            # Replies
            for i in range(random.randint(0, 3)):
                engagement.append({
                    "id": f"tw_eng_{uuid.uuid4().hex[:12]}",
                    "platform": self.platform_name,
                    "post_id": post["id"],
                    "type": EngagementType.REPLY.value,
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "user_name": f"@user{random.randint(1, 100)}",
                    "content": "Great insight! Thanks for sharing.",
                    "created_at": (now - timedelta(hours=random.randint(1, 48))).isoformat()
                })

        return engagement

    def _generate_mock_mentions(self) -> List[Dict[str, Any]]:
        """Generate mock mentions."""
        mentions = []
        now = datetime.now()

        mention_contents = [
            "Just discovered @my_business and their content is 🔥",
            "Shoutout to @my_business for the amazing service!",
            "If you're looking for business solutions, check out @my_business"
        ]

        for i in range(3):
            mentions.append({
                "id": f"tw_mention_{uuid.uuid4().hex[:12]}",
                "platform": self.platform_name,
                "user_id": f"user_{random.randint(1000, 9999)}",
                "user_name": f"@user{random.randint(1, 100)}",
                "content": mention_contents[i] if i < len(mention_contents) else "Mentioning @my_business",
                "tweet_url": f"https://twitter.com/user/status/{uuid.uuid4().hex[:12]}",
                "created_at": (now - timedelta(days=i+1)).isoformat()
            })

        return mentions

    def _generate_mock_messages(self) -> List[Dict[str, Any]]:
        """Generate mock direct messages."""
        messages = []
        now = datetime.now()

        # Incoming messages
        messages.append({
            "id": f"tw_msg_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "sender_id": "user_1234",
            "sender_name": "@potential_client",
            "recipient_id": "me",
            "content": "Hi! Saw your tweet about business automation. Can we discuss a potential collaboration?",
            "created_at": (now - timedelta(hours=4)).isoformat(),
            "read": False,
            "direction": "incoming"
        })

        messages.append({
            "id": f"tw_msg_{uuid.uuid4().hex[:12]}",
            "platform": self.platform_name,
            "sender_id": "user_5678",
            "sender_name": "@satisfied_customer",
            "recipient_id": "me",
            "content": "Thanks for the quick response! Your solution worked perfectly.",
            "created_at": (now - timedelta(days=1)).isoformat(),
            "read": True,
            "direction": "incoming"
        })

        return messages

    def _generate_mock_profile(self) -> Dict[str, Any]:
        """Generate mock profile."""
        return {
            "platform": self.platform_name,
            "user_id": "tw_user_me",
            "username": "my_business",
            "display_name": "My Business | Growth Solutions",
            "bio": "Helping businesses scale with AI & automation 🚀 | DM for inquiries | Newsletter below 👇",
            "profile_image_url": "https://example.com/profile.jpg",
            "banner_image_url": "https://example.com/banner.jpg",
            "website": "https://mybusiness.com",
            "location": "San Francisco, CA",
            "followers": 3200,
            "following": 450,
            "total_tweets": len(self._posts),
            "verified": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now().isoformat()
        }

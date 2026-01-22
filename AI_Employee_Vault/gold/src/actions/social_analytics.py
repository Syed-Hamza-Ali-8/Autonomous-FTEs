"""
Social Analytics

Aggregates analytics across all social media platforms.
Gold Tier Requirement #4: Social Media Integration (Analytics)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.interfaces.social_interface import SocialMediaInterface


class SocialAnalytics:
    """Aggregates analytics across social media platforms."""

    def __init__(self, vault_path: str, use_mock: bool = False):
        """
        Initialize social analytics.

        Args:
            vault_path: Path to Obsidian vault
            use_mock: Use mock implementations for testing
        """
        self.vault_path = vault_path
        self.use_mock = use_mock or os.getenv("USE_MOCK_SOCIAL", "false").lower() == "true"

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize platform APIs
        if self.use_mock:
            from gold.src.mocks.mock_social import MockFacebookAPI, MockInstagramAPI, MockTwitterAPI
            self.facebook_api: SocialMediaInterface = MockFacebookAPI()
            self.instagram_api: SocialMediaInterface = MockInstagramAPI()
            self.twitter_api: SocialMediaInterface = MockTwitterAPI()
        else:
            # Real APIs will be implemented in Phase 4
            from gold.src.mocks.mock_social import MockFacebookAPI, MockInstagramAPI, MockTwitterAPI
            self.facebook_api = MockFacebookAPI()
            self.instagram_api = MockInstagramAPI()
            self.twitter_api = MockTwitterAPI()

    def get_aggregated_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get aggregated analytics across all platforms.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dict with aggregated metrics and per-platform breakdowns
        """
        start_time = datetime.now()

        try:
            # Get analytics from each platform
            facebook_analytics = self.error_recovery.execute_with_retry(
                func=self.facebook_api.get_analytics,
                kwargs={"start_date": start_date, "end_date": end_date},
                error_type=ErrorType.TRANSIENT
            )

            instagram_analytics = self.error_recovery.execute_with_retry(
                func=self.instagram_api.get_analytics,
                kwargs={"start_date": start_date, "end_date": end_date},
                error_type=ErrorType.TRANSIENT
            )

            twitter_analytics = self.error_recovery.execute_with_retry(
                func=self.twitter_api.get_analytics,
                kwargs={"start_date": start_date, "end_date": end_date},
                error_type=ErrorType.TRANSIENT
            )

            # Aggregate metrics
            aggregated = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "total_metrics": {
                    "total_posts": (
                        facebook_analytics["metrics"]["total_posts"] +
                        instagram_analytics["metrics"]["total_posts"] +
                        twitter_analytics["metrics"]["total_tweets"]
                    ),
                    "total_engagement": (
                        facebook_analytics["metrics"]["total_likes"] +
                        facebook_analytics["metrics"]["total_comments"] +
                        facebook_analytics["metrics"]["total_shares"] +
                        instagram_analytics["metrics"]["total_likes"] +
                        instagram_analytics["metrics"]["total_comments"] +
                        instagram_analytics["metrics"]["total_saves"] +
                        twitter_analytics["metrics"]["total_likes"] +
                        twitter_analytics["metrics"]["total_retweets"] +
                        twitter_analytics["metrics"]["total_replies"]
                    ),
                    "total_reach": (
                        facebook_analytics["metrics"]["reach"] +
                        instagram_analytics["metrics"]["reach"]
                    ),
                    "total_impressions": (
                        facebook_analytics["metrics"]["impressions"] +
                        instagram_analytics["metrics"]["impressions"] +
                        twitter_analytics["metrics"]["impressions"]
                    ),
                    "average_engagement_rate": round(
                        (
                            facebook_analytics["metrics"]["engagement_rate"] +
                            instagram_analytics["metrics"]["engagement_rate"] +
                            twitter_analytics["metrics"]["engagement_rate"]
                        ) / 3,
                        2
                    )
                },
                "by_platform": {
                    "facebook": facebook_analytics["metrics"],
                    "instagram": instagram_analytics["metrics"],
                    "twitter": twitter_analytics["metrics"]
                },
                "top_platform": self._determine_top_platform(
                    facebook_analytics["metrics"],
                    instagram_analytics["metrics"],
                    twitter_analytics["metrics"]
                )
            }

            # Log analytics retrieval
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.ANALYTICS_GENERATED,
                actor_type=ActorType.AGENT,
                actor_id="social_analytics",
                status="success",
                duration_ms=duration_ms,
                domain="business",
                metadata={
                    "period_days": aggregated["period"]["days"],
                    "total_posts": aggregated["total_metrics"]["total_posts"],
                    "total_engagement": aggregated["total_metrics"]["total_engagement"]
                }
            )

            return aggregated

        except Exception as e:
            # Log failure
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.ANALYTICS_GENERATED,
                actor_type=ActorType.AGENT,
                actor_id="social_analytics",
                status="failure",
                duration_ms=duration_ms,
                domain="business",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def _determine_top_platform(self, fb_metrics: Dict, ig_metrics: Dict, tw_metrics: Dict) -> Dict[str, Any]:
        """
        Determine which platform performed best.

        Args:
            fb_metrics: Facebook metrics
            ig_metrics: Instagram metrics
            tw_metrics: Twitter metrics

        Returns:
            Dict with top platform name and reason
        """
        # Calculate engagement scores
        fb_score = fb_metrics["engagement_rate"]
        ig_score = ig_metrics["engagement_rate"]
        tw_score = tw_metrics["engagement_rate"]

        if fb_score >= ig_score and fb_score >= tw_score:
            return {
                "platform": "facebook",
                "engagement_rate": fb_score,
                "reason": "Highest engagement rate"
            }
        elif ig_score >= fb_score and ig_score >= tw_score:
            return {
                "platform": "instagram",
                "engagement_rate": ig_score,
                "reason": "Highest engagement rate"
            }
        else:
            return {
                "platform": "twitter",
                "engagement_rate": tw_score,
                "reason": "Highest engagement rate"
            }

    def generate_report(self, start_date: datetime, end_date: datetime) -> str:
        """
        Generate a markdown report of social media analytics.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Markdown-formatted report
        """
        analytics = self.get_aggregated_analytics(start_date, end_date)

        report = f"""# Social Media Analytics Report

**Period**: {analytics['period']['start_date']} to {analytics['period']['end_date']} ({analytics['period']['days']} days)

## Overall Performance

- **Total Posts**: {analytics['total_metrics']['total_posts']}
- **Total Engagement**: {analytics['total_metrics']['total_engagement']:,}
- **Total Reach**: {analytics['total_metrics']['total_reach']:,}
- **Total Impressions**: {analytics['total_metrics']['total_impressions']:,}
- **Average Engagement Rate**: {analytics['total_metrics']['average_engagement_rate']}%

## Top Platform

🏆 **{analytics['top_platform']['platform'].title()}** - {analytics['top_platform']['engagement_rate']}% engagement rate

## Platform Breakdown

### Facebook
- Posts: {analytics['by_platform']['facebook']['total_posts']}
- Likes: {analytics['by_platform']['facebook']['total_likes']:,}
- Comments: {analytics['by_platform']['facebook']['total_comments']:,}
- Shares: {analytics['by_platform']['facebook']['total_shares']:,}
- Reach: {analytics['by_platform']['facebook']['reach']:,}
- Impressions: {analytics['by_platform']['facebook']['impressions']:,}
- Engagement Rate: {analytics['by_platform']['facebook']['engagement_rate']}%

### Instagram
- Posts: {analytics['by_platform']['instagram']['total_posts']}
- Likes: {analytics['by_platform']['instagram']['total_likes']:,}
- Comments: {analytics['by_platform']['instagram']['total_comments']:,}
- Saves: {analytics['by_platform']['instagram']['total_saves']:,}
- Reach: {analytics['by_platform']['instagram']['reach']:,}
- Impressions: {analytics['by_platform']['instagram']['impressions']:,}
- Engagement Rate: {analytics['by_platform']['instagram']['engagement_rate']}%

### Twitter
- Tweets: {analytics['by_platform']['twitter']['total_tweets']}
- Likes: {analytics['by_platform']['twitter']['total_likes']:,}
- Retweets: {analytics['by_platform']['twitter']['total_retweets']:,}
- Replies: {analytics['by_platform']['twitter']['total_replies']:,}
- Impressions: {analytics['by_platform']['twitter']['impressions']:,}
- Profile Visits: {analytics['by_platform']['twitter']['profile_visits']:,}
- Engagement Rate: {analytics['by_platform']['twitter']['engagement_rate']}%

---

*Generated: {datetime.now().isoformat()}*
"""

        return report

    def save_report(self, start_date: datetime, end_date: datetime, output_path: Optional[str] = None) -> str:
        """
        Generate and save analytics report to vault.

        Args:
            start_date: Start of date range
            end_date: End of date range
            output_path: Optional custom output path

        Returns:
            Path to saved report
        """
        report = self.generate_report(start_date, end_date)

        if not output_path:
            report_id = f"social_analytics_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            output_path = os.path.join(self.vault_path, "Reports", "Social_Media", f"{report_id}.md")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"✅ Report saved: {output_path}")
        return output_path


if __name__ == "__main__":
    # Test social analytics
    vault_path = os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    analytics = SocialAnalytics(vault_path, use_mock=True)

    # Get analytics for last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    result = analytics.get_aggregated_analytics(start_date, end_date)

    print(f"✅ Social Analytics Test")
    print(f"   Total Posts: {result['total_metrics']['total_posts']}")
    print(f"   Total Engagement: {result['total_metrics']['total_engagement']:,}")
    print(f"   Average Engagement Rate: {result['total_metrics']['average_engagement_rate']}%")
    print(f"   Top Platform: {result['top_platform']['platform'].title()}")

    # Generate report
    report_path = analytics.save_report(start_date, end_date)
    print(f"   Report: {report_path}")

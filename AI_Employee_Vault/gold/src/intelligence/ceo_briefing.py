"""
CEO Briefing Generator

Generates weekly executive briefings combining insights from all domains.
Gold Tier Requirement #5: CEO Briefing (Weekly Executive Summary)
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from gold.src.core import AuditLogger, ActionType, ActorType, ErrorRecovery, ErrorType
from gold.src.actions import SocialAnalytics

# Gold Tier: Import Odoo Client for real accounting data (Python native)
try:
    from gold.mcp.odoo_mcp_python.odoo_client import OdooClient
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False

# Mock Odoo for development/testing
class MockOdooAPI:
    """Mock Odoo API for development without real Odoo instance"""

    def get_financial_summary(self, date_from: str, date_to: str):
        return {
            "revenue": 12450.00,
            "expenses": 7200.00,
            "profit": 5250.00,
            "profit_margin": 42.17,
            "outstanding_invoices": 3,
            "outstanding_amount": 4500.00,
            "date_from": date_from,
            "date_to": date_to
        }

    def get_invoices(self, filters=None):
        return [
            {"name": "INV/2026/0001", "amount_total": 1500.00, "payment_state": "paid"},
            {"name": "INV/2026/0002", "amount_total": 2000.00, "payment_state": "not_paid"},
            {"name": "INV/2026/0003", "amount_total": 1000.00, "payment_state": "paid"}
        ]


class CEOBriefingGenerator:
    """Generates comprehensive CEO briefings from all data sources."""

    def __init__(self, vault_path: str, use_mock: bool = False):
        """
        Initialize CEO Briefing generator.

        Args:
            vault_path: Path to Obsidian vault
            use_mock: Use mock implementations for testing
        """
        self.vault_path = vault_path
        self.use_mock = use_mock or os.getenv("USE_MOCK_ODOO", "false").lower() == "true"

        self.audit_logger = AuditLogger(vault_path)
        self.error_recovery = ErrorRecovery()

        # Initialize data sources
        # Gold Tier: Use real Odoo client if available and not in mock mode
        if self.use_mock or not ODOO_AVAILABLE:
            print("⚠️  Using Mock Odoo API (set USE_MOCK_ODOO=false to use real Odoo)")
            self.accounting_api = MockOdooAPI()
        else:
            print("✅ Using Odoo Client for real accounting data")
            # Initialize Odoo client with environment variables
            import os
            self.accounting_api = OdooClient(
                url=os.getenv("ODOO_URL", "http://localhost:8069"),
                db=os.getenv("ODOO_DB", "ai_employee_accounting"),
                username=os.getenv("ODOO_USERNAME", "api@aiemployee.local"),
                password=os.getenv("ODOO_PASSWORD", "")
            )

        self.social_analytics = SocialAnalytics(vault_path, use_mock=True)

    def generate_briefing(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate CEO briefing for the specified period.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Dict with briefing data
        """
        start_time = datetime.now()

        try:
            # Gather data from all sources
            financial_data = self._get_financial_summary(start_date, end_date)
            social_data = self._get_social_summary(start_date, end_date)
            email_data = self._get_email_summary(start_date, end_date)
            action_items = self._get_action_items()

            # Generate insights
            insights = self._generate_insights(financial_data, social_data, email_data)

            # Compile briefing
            briefing = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "generated_at": datetime.now().isoformat(),
                "financial": financial_data,
                "social_media": social_data,
                "communications": email_data,
                "action_items": action_items,
                "insights": insights,
                "summary": self._generate_executive_summary(
                    financial_data, social_data, email_data, insights
                )
            }

            # Log briefing generation
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.CEO_BRIEFING_GENERATED,
                actor_type=ActorType.AGENT,
                actor_id="ceo_briefing_generator",
                status="success",
                duration_ms=duration_ms,
                domain="business",
                metadata={
                    "period_days": briefing["period"]["days"],
                    "insights_count": len(insights),
                    "action_items_count": len(action_items)
                }
            )

            return briefing

        except Exception as e:
            # Log failure
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.audit_logger.log_action(
                action_type=ActionType.CEO_BRIEFING_GENERATED,
                actor_type=ActorType.AGENT,
                actor_id="ceo_briefing_generator",
                status="failure",
                duration_ms=duration_ms,
                domain="business",
                error={"type": type(e).__name__, "message": str(e)}
            )
            raise

    def _get_financial_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get financial summary from accounting system (Odoo or Mock)."""
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date.strftime("%Y-%m-%d")

        # Use Odoo client (real or mock) - both have same interface
        summary = self.accounting_api.get_financial_summary(date_from, date_to)

        # Get all invoices for detailed breakdown
        all_invoices = self.accounting_api.get_invoices({
            "date_from": date_from,
            "date_to": date_to
        })

        paid_invoices = [inv for inv in all_invoices if inv.get("payment_state") == "paid"]

        return {
            "revenue": summary["revenue"],
            "expenses": summary["expenses"],
            "net_profit": summary["profit"],
            "profit_margin": round(summary["profit_margin"], 2),
            "invoices": {
                "total_count": len(all_invoices),
                "total_amount": sum(inv.get("amount_total", 0) for inv in all_invoices),
                "paid_count": len(paid_invoices),
                "paid_amount": sum(inv.get("amount_total", 0) for inv in paid_invoices),
                "outstanding_count": summary["outstanding_invoices"],
                "outstanding_amount": summary["outstanding_amount"]
            }
        }

    def _get_social_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get social media summary."""
        analytics = self.social_analytics.get_aggregated_analytics(start_date, end_date)

        return {
            "total_posts": analytics["total_metrics"]["total_posts"],
            "total_engagement": analytics["total_metrics"]["total_engagement"],
            "total_reach": analytics["total_metrics"]["total_reach"],
            "total_impressions": analytics["total_metrics"]["total_impressions"],
            "engagement_rate": analytics["total_metrics"]["average_engagement_rate"],
            "top_platform": analytics["top_platform"]["platform"],
            "by_platform": analytics["by_platform"]
        }

    def _get_email_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get email/communications summary from audit logs."""
        # Query audit logs for all activity in the period
        all_logs = self.audit_logger.search_logs(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        # Filter by action types
        email_sent = [log for log in all_logs if log.get("action_type") == "email_sent"]
        email_received = [log for log in all_logs if log.get("action_type") == "email_received"]
        whatsapp_sent = [log for log in all_logs if log.get("action_type") == "whatsapp_sent"]
        linkedin_posts = [log for log in all_logs if log.get("action_type") == "linkedin_post"]

        total_comms = len(email_sent) + len(email_received) + len(whatsapp_sent) + len(linkedin_posts)

        return {
            "emails_sent": len(email_sent),
            "emails_received": len(email_received),
            "whatsapp_messages": len(whatsapp_sent),
            "linkedin_posts": len(linkedin_posts),
            "total_communications": total_comms
        }

    def _get_action_items(self) -> List[Dict[str, Any]]:
        """Get pending action items from Needs_Action folder."""
        needs_action_path = os.path.join(self.vault_path, "Needs_Action")

        if not os.path.exists(needs_action_path):
            return []

        action_items = []
        for filename in os.listdir(needs_action_path):
            if filename.endswith(".md"):
                filepath = os.path.join(needs_action_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()

                    # Parse frontmatter (simple parsing)
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            # Extract type and status
                            lines = parts[1].strip().split("\n")
                            item_type = "unknown"
                            status = "pending"
                            created = "unknown"

                            for line in lines:
                                if line.startswith("type:"):
                                    item_type = line.split(":", 1)[1].strip()
                                elif line.startswith("status:"):
                                    status = line.split(":", 1)[1].strip()
                                elif line.startswith("created:"):
                                    created = line.split(":", 1)[1].strip()

                            action_items.append({
                                "filename": filename,
                                "type": item_type,
                                "status": status,
                                "created": created
                            })
                except Exception as e:
                    # Skip files that can't be parsed
                    continue

        return action_items

    def _generate_insights(self, financial: Dict, social: Dict, email: Dict) -> List[Dict[str, Any]]:
        """Generate insights from cross-domain data."""
        insights = []

        # Financial insights
        if financial["profit_margin"] > 50:
            insights.append({
                "category": "financial",
                "type": "positive",
                "title": "Strong Profit Margin",
                "description": f"Profit margin of {financial['profit_margin']}% indicates healthy business operations.",
                "priority": "medium"
            })
        elif financial["profit_margin"] < 20:
            insights.append({
                "category": "financial",
                "type": "warning",
                "title": "Low Profit Margin",
                "description": f"Profit margin of {financial['profit_margin']}% is below target. Review expenses.",
                "priority": "high"
            })

        # Outstanding invoices
        if financial["invoices"]["outstanding_amount"] > financial["revenue"] * 0.3:
            insights.append({
                "category": "financial",
                "type": "warning",
                "title": "High Outstanding Invoices",
                "description": f"${financial['invoices']['outstanding_amount']:.2f} in outstanding invoices. Follow up with clients.",
                "priority": "high"
            })

        # Social media insights
        if social["engagement_rate"] > 5.0:
            insights.append({
                "category": "social",
                "type": "positive",
                "title": "Strong Social Engagement",
                "description": f"{social['engagement_rate']}% engagement rate exceeds industry average.",
                "priority": "low"
            })
        elif social["engagement_rate"] < 2.0:
            insights.append({
                "category": "social",
                "type": "warning",
                "title": "Low Social Engagement",
                "description": f"{social['engagement_rate']}% engagement rate. Consider content strategy review.",
                "priority": "medium"
            })

        # Cross-domain insight: Social vs Revenue
        if social["total_posts"] > 0 and financial["revenue"] > 0:
            revenue_per_post = financial["revenue"] / social["total_posts"]
            insights.append({
                "category": "cross_domain",
                "type": "info",
                "title": "Social Media ROI",
                "description": f"Average revenue per social post: ${revenue_per_post:.2f}",
                "priority": "low"
            })

        return insights

    def _generate_executive_summary(self, financial: Dict, social: Dict,
                                   email: Dict, insights: List[Dict]) -> str:
        """Generate executive summary text."""
        high_priority_insights = [i for i in insights if i["priority"] == "high"]
        positive_insights = [i for i in insights if i["type"] == "positive"]

        summary = f"""**Financial Performance**: Revenue of ${financial['revenue']:,.2f} with {financial['profit_margin']}% profit margin. """

        if financial["invoices"]["outstanding_count"] > 0:
            summary += f"{financial['invoices']['outstanding_count']} invoices outstanding (${financial['invoices']['outstanding_amount']:,.2f}). "

        summary += f"""

**Social Media**: {social['total_posts']} posts across platforms with {social['engagement_rate']}% engagement rate. Top platform: {social['top_platform'].title()}.

**Communications**: {email['emails_sent']} emails sent, {email['whatsapp_messages']} WhatsApp messages, {email['linkedin_posts']} LinkedIn posts.
"""

        if high_priority_insights:
            summary += f"\n**⚠️ High Priority Items**: {len(high_priority_insights)} items require attention."

        if positive_insights:
            summary += f"\n**✅ Wins**: {len(positive_insights)} positive developments this period."

        return summary.strip()

    def generate_markdown_report(self, start_date: datetime, end_date: datetime) -> str:
        """Generate markdown-formatted CEO briefing."""
        briefing = self.generate_briefing(start_date, end_date)

        report = f"""# CEO Briefing

**Period**: {briefing['period']['start_date']} to {briefing['period']['end_date']} ({briefing['period']['days']} days)
**Generated**: {briefing['generated_at']}

---

## Executive Summary

{briefing['summary']}

---

## Financial Performance

- **Revenue**: ${briefing['financial']['revenue']:,.2f}
- **Expenses**: ${briefing['financial']['expenses']:,.2f}
- **Net Profit**: ${briefing['financial']['net_profit']:,.2f}
- **Profit Margin**: {briefing['financial']['profit_margin']}%

### Invoices
- **Total**: {briefing['financial']['invoices']['total_count']} invoices (${briefing['financial']['invoices']['total_amount']:,.2f})
- **Paid**: {briefing['financial']['invoices']['paid_count']} invoices (${briefing['financial']['invoices']['paid_amount']:,.2f})
- **Outstanding**: {briefing['financial']['invoices']['outstanding_count']} invoices (${briefing['financial']['invoices']['outstanding_amount']:,.2f})

---

## Social Media Performance

- **Total Posts**: {briefing['social_media']['total_posts']}
- **Total Engagement**: {briefing['social_media']['total_engagement']:,}
- **Reach**: {briefing['social_media']['total_reach']:,}
- **Impressions**: {briefing['social_media']['total_impressions']:,}
- **Engagement Rate**: {briefing['social_media']['engagement_rate']}%
- **Top Platform**: {briefing['social_media']['top_platform'].title()}

### Platform Breakdown
"""

        for platform, metrics in briefing['social_media']['by_platform'].items():
            report += f"\n**{platform.title()}**: {metrics.get('total_posts', metrics.get('total_tweets', 0))} posts, {metrics['engagement_rate']}% engagement"

        report += f"""

---

## Communications

- **Emails Sent**: {briefing['communications']['emails_sent']}
- **Emails Received**: {briefing['communications']['emails_received']}
- **WhatsApp Messages**: {briefing['communications']['whatsapp_messages']}
- **LinkedIn Posts**: {briefing['communications']['linkedin_posts']}
- **Total Communications**: {briefing['communications']['total_communications']}

---

## Insights & Recommendations

"""

        # Group insights by priority
        high_priority = [i for i in briefing['insights'] if i['priority'] == 'high']
        medium_priority = [i for i in briefing['insights'] if i['priority'] == 'medium']
        low_priority = [i for i in briefing['insights'] if i['priority'] == 'low']

        if high_priority:
            report += "\n### 🔴 High Priority\n"
            for insight in high_priority:
                icon = "⚠️" if insight['type'] == 'warning' else "✅" if insight['type'] == 'positive' else "ℹ️"
                report += f"\n{icon} **{insight['title']}**: {insight['description']}\n"

        if medium_priority:
            report += "\n### 🟡 Medium Priority\n"
            for insight in medium_priority:
                icon = "⚠️" if insight['type'] == 'warning' else "✅" if insight['type'] == 'positive' else "ℹ️"
                report += f"\n{icon} **{insight['title']}**: {insight['description']}\n"

        if low_priority:
            report += "\n### 🟢 Low Priority\n"
            for insight in low_priority:
                icon = "⚠️" if insight['type'] == 'warning' else "✅" if insight['type'] == 'positive' else "ℹ️"
                report += f"\n{icon} **{insight['title']}**: {insight['description']}\n"

        report += f"""

---

## Action Items

**Pending**: {len(briefing['action_items'])} items in Needs_Action folder

"""

        for item in briefing['action_items'][:10]:  # Show first 10
            report += f"- [{item['type']}] {item['filename']}\n"

        if len(briefing['action_items']) > 10:
            report += f"\n*...and {len(briefing['action_items']) - 10} more*\n"

        report += """

---

*This briefing was automatically generated by your Gold Tier AI Employee.*
"""

        return report

    def save_briefing(self, start_date: datetime, end_date: datetime,
                     output_path: Optional[str] = None) -> str:
        """
        Generate and save CEO briefing to vault.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            output_path: Optional custom output path

        Returns:
            Path to saved briefing
        """
        report = self.generate_markdown_report(start_date, end_date)

        if not output_path:
            briefing_id = f"ceo_briefing_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            output_path = os.path.join(self.vault_path, "Reports", "CEO_Briefings", f"{briefing_id}.md")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"✅ CEO Briefing saved: {output_path}")
        return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CEO Briefing Generator")
    parser.add_argument(
        "--vault-path",
        default=os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"),
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run in scheduled mode (waits for Sunday 7 AM)"
    )
    parser.add_argument(
        "--use-mock",
        action="store_true",
        default=True,
        help="Use mock data"
    )

    args = parser.parse_args()

    generator = CEOBriefingGenerator(args.vault_path, use_mock=args.use_mock)

    if args.schedule:
        # Scheduled mode: wait for Sunday 7 AM
        import time
        from datetime import datetime, timedelta

        print("📅 CEO Briefing Scheduler started")
        print("   Waiting for Sunday 7:00 AM...")

        while True:
            now = datetime.now()

            # Check if it's Sunday and 7 AM
            if now.weekday() == 6 and now.hour == 7 and now.minute < 5:
                print(f"⏰ Generating CEO Briefing for {now.strftime('%Y-%m-%d')}")

                # Generate briefing for last 7 days
                end_date = now
                start_date = end_date - timedelta(days=7)

                try:
                    briefing_path = generator.save_briefing(start_date, end_date)
                    print(f"✅ CEO Briefing saved: {briefing_path}")
                except Exception as e:
                    print(f"❌ Error generating CEO Briefing: {e}")

                # Wait 1 hour to avoid generating multiple times
                time.sleep(3600)

            # Check every 5 minutes
            time.sleep(300)
    else:
        # Test mode: generate briefing immediately
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        briefing_path = generator.save_briefing(start_date, end_date)

        print(f"✅ CEO Briefing Test Complete")
        print(f"   Report: {briefing_path}")


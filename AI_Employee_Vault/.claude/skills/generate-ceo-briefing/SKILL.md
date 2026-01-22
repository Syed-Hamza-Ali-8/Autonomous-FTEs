# Generate CEO Briefing Skill

**Skill ID**: generate-ceo-briefing
**Version**: 1.0.0
**User Story**: US-GOLD-2 - Weekly Business Intelligence Report
**Priority**: P1 (Gold Tier MVP)

## Purpose

Generate comprehensive weekly CEO briefings that aggregate data from multiple domains (Financial, Social Media, Communications, Tasks) to provide actionable business intelligence. This skill implements autonomous business analysis and reporting, transforming the AI from a reactive assistant into a proactive business partner.

## Capabilities

- **Cross-Domain Data Aggregation**: Collect data from Odoo (accounting), social media, communications, and task management
- **Financial Analysis**: Revenue, expenses, profit margins, outstanding invoices, cash flow trends
- **Social Media Analytics**: Engagement metrics, reach, impressions, top-performing content
- **Task Performance**: Completion rates, bottlenecks, time tracking
- **Subscription Audit**: Identify unused or underutilized services
- **Insight Generation**: Automatically generate 6 types of insights (trends, anomalies, opportunities, risks, recommendations, predictions)
- **Scheduled Execution**: Run automatically every Sunday at 7:00 AM
- **Markdown Report**: Generate formatted report in Reports/CEO_Briefings/

## Architecture

### Core Components

1. **CEOBriefingGenerator** (`gold/src/intelligence/ceo_briefing.py`)
   - `generate_briefing(date_from, date_to)` → Dict[sections]
   - `generate_financial_summary()` → Dict
   - `generate_social_summary()` → Dict
   - `generate_task_summary()` → Dict
   - `generate_insights()` → List[Insight]
   - `generate_recommendations()` → List[Recommendation]

2. **Data Collectors** (`gold/src/intelligence/`)
   - `OdooDataCollector` - Financial data from Odoo MCP
   - `SocialMediaCollector` - Engagement from Facebook, Instagram, Twitter
   - `CommunicationsCollector` - Email, WhatsApp, LinkedIn activity
   - `TaskCollector` - Task completion from vault folders

3. **Insight Engine** (`gold/src/intelligence/insight_engine.py`)
   - `detect_trends(data)` → List[Trend]
   - `detect_anomalies(data)` → List[Anomaly]
   - `identify_opportunities(data)` → List[Opportunity]
   - `assess_risks(data)` → List[Risk]
   - `generate_recommendations(insights)` → List[Recommendation]

### Briefing Generation Workflow

```
1. Data Collection → Gather data from all sources
                  → Odoo: Financial transactions, invoices
                  → Social: Engagement metrics
                  → Communications: Email/WhatsApp activity
                  → Tasks: Completion rates from vault

2. Analysis → Calculate KPIs and metrics
           → Detect trends and patterns
           → Identify anomalies
           → Compare to previous periods

3. Insight Generation → Generate 6 types of insights
                      → Prioritize by impact
                      → Create actionable recommendations

4. Report Generation → Format as markdown
                    → Include charts and tables
                    → Add executive summary
                    → Save to Reports/CEO_Briefings/

5. Notification → Create action file in Needs_Action/
               → Notify user of new briefing
               → Log to audit trail
```

## Configuration

### CEO Briefing Config (`gold/config/ceo_briefing_config.yaml`)

```yaml
schedule:
  enabled: true
  day: sunday
  time: "07:00"
  timezone: "America/New_York"

data_sources:
  odoo:
    enabled: true
    mcp_server: "gold/mcp/odoo-mcp"
  social_media:
    enabled: true
    platforms: ["facebook", "instagram", "twitter"]
  communications:
    enabled: true
    sources: ["email", "whatsapp", "linkedin"]
  tasks:
    enabled: true
    folders: ["Needs_Action", "Done", "In_Progress"]

analysis:
  period: "weekly"  # weekly, monthly, quarterly
  compare_to_previous: true
  include_trends: true
  include_predictions: true

insights:
  min_confidence: 0.7
  max_insights: 10
  types:
    - trends
    - anomalies
    - opportunities
    - risks
    - recommendations
    - predictions

output:
  format: "markdown"
  location: "Reports/CEO_Briefings"
  filename_pattern: "ceo_briefing_{date}.md"
  include_charts: false  # Future: ASCII charts
  include_raw_data: false
```

### Environment Variables (`.env`)

```bash
# CEO Briefing
CEO_BRIEFING_ENABLED=true
CEO_BRIEFING_DAY=sunday
CEO_BRIEFING_TIME=07:00

# Data Sources
ODOO_MCP_PATH=gold/mcp/odoo-mcp
USE_MOCK_ODOO=true  # Set to false for real Odoo
```

## Usage

### Generate Briefing Manually

```python
from gold.src.intelligence.ceo_briefing import CEOBriefingGenerator

generator = CEOBriefingGenerator(vault_path="/path/to/vault")

# Generate briefing for last 7 days
briefing = generator.generate_briefing(
    date_from="2026-01-12",
    date_to="2026-01-19"
)

print(f"Briefing saved to: {briefing['file_path']}")
```

### Using Claude Code Skill

```bash
# Generate briefing for current week
claude --skill generate-ceo-briefing

# Generate briefing for specific period
claude --skill generate-ceo-briefing \
  --date-from 2026-01-01 \
  --date-to 2026-01-31

# Generate briefing with specific focus
claude --skill generate-ceo-briefing \
  --focus financial
```

### Scheduled Execution (PM2)

```bash
# Start CEO Briefing scheduler
pm2 start gold/ecosystem.config.js --only gold-ceo-briefing

# Check status
pm2 list | grep ceo-briefing

# View logs
pm2 logs gold-ceo-briefing
```

## Output Format

### CEO Briefing Report

**Location**: `Reports/CEO_Briefings/ceo_briefing_2026-01-19.md`

```markdown
---
generated: 2026-01-19T07:00:00Z
period: 2026-01-12 to 2026-01-19
type: weekly_ceo_briefing
version: 1.0.0
---

# Weekly CEO Briefing
**Period**: January 12-19, 2026
**Generated**: Sunday, January 19, 2026 at 7:00 AM

---

## Executive Summary

Strong week with revenue ahead of target. Social media engagement up 25%. One critical bottleneck identified in client onboarding process.

**Key Highlights**:
- 📈 Revenue: $12,450 (+15% vs last week)
- 💰 Profit Margin: 42% (+3% vs last week)
- 📱 Social Engagement: 1,247 interactions (+25%)
- ✅ Task Completion: 87% (target: 90%)

**Action Required**:
- Review client onboarding bottleneck (see Tasks section)
- Approve subscription cancellation for unused tools (see Recommendations)

---

## Financial Summary

### Revenue & Expenses
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Revenue | $12,450 | $10,800 | +15% ↗️ |
| Expenses | $7,200 | $6,900 | +4% ↗️ |
| Profit | $5,250 | $3,900 | +35% ↗️ |
| Profit Margin | 42% | 36% | +6pp ↗️ |

### Outstanding Invoices
| Client | Amount | Due Date | Days Overdue |
|--------|--------|----------|--------------|
| Client A | $2,500 | Jan 15 | 4 days |
| Client B | $1,800 | Jan 18 | 1 day |
| Client C | $3,200 | Jan 25 | - |

**Total Outstanding**: $7,500

### Cash Flow Trend
- Week 1: $8,200
- Week 2: $10,800
- Week 3: $12,450 ↗️

**Insight**: Revenue trending upward. Maintain momentum.

---

## Social Media Performance

### Engagement Metrics
| Platform | Posts | Likes | Comments | Shares | Total Engagement |
|----------|-------|-------|----------|--------|------------------|
| Facebook | 3 | 245 | 18 | 12 | 275 |
| Instagram | 5 | 892 | 67 | 0 | 959 |
| Twitter | 7 | 89 | 24 | 15 | 128 |
| **Total** | **15** | **1,226** | **109** | **27** | **1,362** |

### Top Performing Content
1. **Instagram**: "AI automation breakthrough" - 312 likes, 23 comments
2. **Facebook**: "Client success story" - 156 likes, 12 comments
3. **Twitter**: "Industry insights thread" - 45 retweets, 18 replies

### Insights
- Instagram engagement up 35% (visual content performing well)
- Twitter threads driving 2x more engagement than single tweets
- Facebook posts with questions get 3x more comments

---

## Communications Activity

### Email
- **Received**: 127 emails
- **Sent**: 43 emails
- **Response Time**: Avg 2.3 hours (target: <4 hours) ✅
- **Pending**: 8 emails in Needs_Action

### WhatsApp
- **Messages**: 34 messages
- **Urgent**: 3 messages (all responded)
- **Response Time**: Avg 15 minutes

### LinkedIn
- **Connection Requests**: 12 (8 accepted)
- **Messages**: 7 (5 responded)
- **Profile Views**: 89 (+12% vs last week)

---

## Task Performance

### Completion Rates
| Status | Count | Percentage |
|--------|-------|------------|
| Completed | 23 | 87% |
| In Progress | 2 | 8% |
| Pending | 1 | 4% |

**Target**: 90% completion rate
**Status**: ⚠️ Slightly below target

### Bottlenecks Identified
1. **Client Onboarding**: Taking 5 days (expected: 2 days)
   - **Impact**: High - delaying revenue recognition
   - **Recommendation**: Review onboarding checklist, automate steps

2. **Invoice Generation**: Manual process taking 30 min per invoice
   - **Impact**: Medium - time-consuming
   - **Recommendation**: Automate with Odoo templates

### Time Tracking
- **Total Hours**: 42 hours
- **Billable**: 35 hours (83%)
- **Non-Billable**: 7 hours (admin, meetings)

---

## Subscription Audit

### Active Subscriptions
| Service | Cost/Month | Last Used | Status |
|---------|------------|-----------|--------|
| Notion | $15 | 45 days ago | ⚠️ Unused |
| Slack | $8 | Today | ✅ Active |
| Adobe CC | $55 | 3 days ago | ✅ Active |
| Zoom | $15 | Today | ✅ Active |

### Recommendations
- **Cancel Notion** ($15/month): No team activity in 45 days. Migrate to Obsidian (free).
- **Potential Savings**: $180/year

---

## Insights & Recommendations

### 🔥 Critical
1. **Client Onboarding Bottleneck**
   - **Issue**: Onboarding taking 2.5x longer than expected
   - **Impact**: Delaying revenue, poor client experience
   - **Action**: Review process, identify automation opportunities
   - **Priority**: High

### 💡 Opportunities
2. **Instagram Growth**
   - **Observation**: Instagram engagement up 35%
   - **Opportunity**: Double down on visual content
   - **Action**: Increase Instagram posting to 2x per day
   - **Priority**: Medium

3. **Twitter Threads**
   - **Observation**: Threads get 2x more engagement
   - **Opportunity**: Create weekly thread series
   - **Action**: Plan 4 thread topics for next week
   - **Priority**: Medium

### ⚠️ Risks
4. **Overdue Invoices**
   - **Issue**: $4,300 in overdue invoices (Client A, Client B)
   - **Risk**: Cash flow impact if not collected
   - **Action**: Send payment reminders, follow up calls
   - **Priority**: High

### 📊 Trends
5. **Revenue Growth**
   - **Trend**: Revenue up 15% week-over-week
   - **Prediction**: If maintained, $50K+ monthly revenue by March
   - **Action**: Maintain current sales activities
   - **Priority**: Low (monitoring)

---

## Action Items for Next Week

### High Priority
- [ ] Review and optimize client onboarding process
- [ ] Follow up on overdue invoices (Client A, Client B)
- [ ] Approve Notion cancellation (save $15/month)

### Medium Priority
- [ ] Increase Instagram posting frequency
- [ ] Plan 4 Twitter thread topics
- [ ] Automate invoice generation in Odoo

### Low Priority
- [ ] Review time tracking data for optimization
- [ ] Update LinkedIn profile with recent achievements

---

## Upcoming Deadlines

- **Jan 25**: Client C invoice due ($3,200)
- **Jan 31**: Quarterly tax prep deadline
- **Feb 1**: Notion subscription renewal (cancel before this date)

---

**Next Briefing**: Sunday, January 26, 2026 at 7:00 AM

---

*Generated by AI Employee v1.0.0 | Gold Tier*
*Data Sources: Odoo, Facebook, Instagram, Twitter, Email, WhatsApp, LinkedIn, Task Vault*
```

### Notification File (Needs_Action/)

```markdown
---
type: ceo_briefing_notification
created_at: 2026-01-19T07:00:05Z
briefing_path: Reports/CEO_Briefings/ceo_briefing_2026-01-19.md
---

# 📊 Weekly CEO Briefing Available

Your weekly CEO briefing for January 12-19, 2026 is ready for review.

**Location**: `Reports/CEO_Briefings/ceo_briefing_2026-01-19.md`

**Key Highlights**:
- Revenue: $12,450 (+15%)
- Social Engagement: +25%
- 3 high-priority action items

**Action Required**: Review briefing and address high-priority items.
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
requests = "^2.31.0"  # For MCP communication
```

### System Requirements

- Python 3.13+
- Odoo MCP server (for financial data)
- Social media mock APIs (or real APIs)
- Vault with proper folder structure

## Setup Instructions

### 1. Configure CEO Briefing

```bash
# Edit configuration
nano gold/config/ceo_briefing_config.yaml

# Customize schedule, data sources, analysis settings
```

### 2. Ensure Data Sources Available

```bash
# Check Odoo MCP server
curl http://localhost:3002/health

# Check social media watchers
pm2 list | grep watcher

# Verify vault folders exist
ls -la Reports/CEO_Briefings/
```

### 3. Test Manual Generation

```bash
# Generate test briefing
python gold/src/intelligence/ceo_briefing.py

# Check output
cat Reports/CEO_Briefings/ceo_briefing_*.md
```

### 4. Enable Scheduled Execution

```bash
# Start CEO Briefing scheduler
pm2 start gold/ecosystem.config.js --only gold-ceo-briefing

# Verify scheduled
pm2 list | grep ceo-briefing

# Check logs
pm2 logs gold-ceo-briefing
```

## Error Handling

### Data Source Unavailable

**Error**: "Odoo MCP server not responding"

**Recovery**:
- Use cached data from previous briefing
- Generate briefing with available data sources
- Note missing data in report
- Notify user of incomplete data

### Insufficient Data

**Error**: "Not enough data for trend analysis"

**Recovery**:
- Generate briefing with available metrics
- Skip trend analysis section
- Note data limitations in report

### Generation Failure

**Error**: "Failed to generate briefing"

**Recovery**:
- Log error details
- Retry once after 5 minutes
- If still fails, notify user
- Keep previous briefing available

## Performance

- **Generation Time**: ~30-60 seconds
- **Data Collection**: ~20 seconds
- **Analysis**: ~15 seconds
- **Report Generation**: ~10 seconds
- **Memory**: ~100MB during generation
- **CPU**: ~20% during generation

## Testing

### Unit Tests

```bash
pytest gold/tests/unit/test_ceo_briefing.py
pytest gold/tests/unit/test_insight_engine.py
```

### Integration Tests

```bash
pytest gold/tests/integration/test_ceo_briefing_generation.py
```

### Manual Testing

1. **Generate Test Briefing**:
   ```bash
   python gold/src/intelligence/ceo_briefing.py --test
   ```

2. **Verify Output**: Check `Reports/CEO_Briefings/`

3. **Review Content**: Ensure all sections present

4. **Check Insights**: Verify insights are actionable

5. **Validate Data**: Cross-check with source data

## Success Criteria

- ✅ Briefing generated automatically every Sunday at 7:00 AM
- ✅ All data sources integrated (Odoo, social media, communications, tasks)
- ✅ Financial summary accurate and up-to-date
- ✅ Social media analytics comprehensive
- ✅ Insights actionable and prioritized
- ✅ Recommendations specific and measurable
- ✅ Report formatted professionally
- ✅ Notification created in Needs_Action/
- ✅ Audit log entry created

## Related Skills

- **post-to-social-media**: Social media data source
- **monitor-social-media**: Engagement data collection
- **monitor-system-health**: System status included in briefing
- **manage-approvals**: Approval workflow for recommendations

## References

- See `references/data_sources.md` for data source details
- See `references/analysis_methods.md` for analysis algorithms
- See `references/insight_generation.md` for insight types

## Examples

- See `examples/weekly_briefing_example.md` for sample weekly briefing
- See `examples/monthly_briefing_example.md` for sample monthly briefing

## Templates

- See `templates/briefing_template.md` for report structure

## Changelog

- **1.0.0** (2026-01-19): Initial implementation for Gold tier
  - Weekly CEO briefing generation
  - Cross-domain data aggregation
  - 6 types of insights
  - Automated scheduling
  - Comprehensive reporting

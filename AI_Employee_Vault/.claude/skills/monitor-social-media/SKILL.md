# Monitor Social Media Skill

**Skill ID**: monitor-social-media
**Version**: 1.0.0
**User Story**: US-GOLD-4 - Social Media Engagement Monitoring
**Priority**: P1 (Gold Tier MVP)

## Purpose

Monitor Facebook, Instagram, and Twitter for engagement events (DMs, mentions, comments, replies) and create action files for Claude to process. This skill implements the **Perception** phase for social media, enabling the AI Employee to respond to customer interactions autonomously.

## Capabilities

- **Multi-Platform Monitoring**: Monitor Facebook, Instagram, and Twitter simultaneously
- **Engagement Detection**: Detect DMs, mentions, comments, replies, and shares
- **Action File Creation**: Create structured action files in Needs_Action/ folder
- **Priority Classification**: Classify engagement by urgency (high/medium/low)
- **Continuous Monitoring**: Run continuously with configurable check intervals
- **Duplicate Prevention**: Track processed engagements to avoid duplicates
- **Error Recovery**: Handle API rate limits and connection failures gracefully

## Architecture

### Core Components

1. **SocialMediaMonitor** (`gold/src/watchers/social_media_monitor.py`)
   - `monitor_all_platforms()` → List[Engagement]
   - `create_action_file(engagement)` → str (file_path)
   - `classify_priority(engagement)` → str (high/medium/low)

2. **Platform Watchers** (`gold/src/watchers/`)
   - `FacebookWatcher` - Monitor Facebook page/profile
   - `InstagramWatcher` - Monitor Instagram account
   - `TwitterWatcher` - Monitor Twitter account

3. **EngagementProcessor** (`gold/src/utils/engagement_processor.py`)
   - `extract_keywords(text)` → List[str]
   - `detect_sentiment(text)` → str (positive/negative/neutral)
   - `suggest_response(engagement)` → str

### Monitoring Workflow

```
1. Continuous Monitoring → Check platforms every 5 minutes
                        → Detect new engagements
                        → Filter by keywords/urgency

2. Engagement Processing → Extract relevant information
                        → Classify by type and priority
                        → Check for duplicates

3. Action File Creation → Create markdown file in Needs_Action/
                       → Include engagement details
                       → Suggest response actions

4. Notification → Log to audit trail
               → Update engagement tracking
               → Continue monitoring
```

## Configuration

### Social Media Monitor Config (`gold/config/social_media_monitor_config.yaml`)

```yaml
monitoring:
  enabled: true
  interval_seconds: 300  # 5 minutes
  platforms:
    - facebook
    - instagram
    - twitter

engagement_types:
  - direct_messages
  - mentions
  - comments
  - replies

priority_keywords:
  high:
    - urgent
    - asap
    - help
    - problem
    - issue
    - invoice
    - payment
  medium:
    - question
    - inquiry
    - interested
    - pricing
  low:
    - thanks
    - great
    - awesome

filters:
  min_engagement_score: 0
  exclude_spam: true
  exclude_bots: true
```

## Usage

### Manual Monitoring

```python
from gold.src.watchers.social_media_monitor import SocialMediaMonitor

monitor = SocialMediaMonitor(vault_path="/path/to/vault")

# Monitor all platforms once
engagements = monitor.monitor_all_platforms()

print(f"Found {len(engagements)} new engagements")

for engagement in engagements:
    action_file = monitor.create_action_file(engagement)
    print(f"Created: {action_file}")
```

### Using Claude Code Skill

```bash
# Monitor all platforms
claude --skill monitor-social-media

# Monitor specific platform
claude --skill monitor-social-media --platform instagram

# Check for high-priority only
claude --skill monitor-social-media --priority high
```

### Continuous Monitoring (PM2)

```bash
# Start all social media watchers
pm2 start gold/ecosystem.config.js --only "gold-facebook-watcher,gold-instagram-watcher,gold-twitter-watcher"

# Check status
pm2 list | grep watcher

# View logs
pm2 logs gold-facebook-watcher
```

## Output Format

### Action File (Needs_Action/)

```markdown
---
type: social_media_engagement
platform: instagram
engagement_type: direct_message
priority: high
created_at: 2026-01-19T16:45:00Z
from_user: "@potential_client"
---

# Instagram Direct Message

**Platform**: Instagram
**Type**: Direct Message
**Priority**: 🔴 High
**From**: @potential_client
**Time**: 2026-01-19 4:45 PM

## Message Content

"Hi! I'm interested in your AI automation services. Can you send me pricing information? I need something ASAP for my business."

## Context

- **Follower**: Yes (following since 2026-01-15)
- **Previous Interactions**: 2 (liked 2 posts)
- **Sentiment**: Positive
- **Keywords Detected**: interested, pricing, asap

## Suggested Actions

1. **Respond with Pricing** (Priority: High)
   - Send pricing sheet
   - Offer consultation call
   - Response template: "Thanks for your interest! I'd love to help..."

2. **Schedule Follow-up** (Priority: Medium)
   - Add to CRM
   - Schedule follow-up in 2 days if no response

## Response Template

```
Hi @potential_client! Thanks for reaching out! 🚀

I'd be happy to share our pricing and discuss how we can help your business.

Our AI automation packages start at $X/month and include:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Would you like to schedule a quick 15-minute call to discuss your specific needs?

Looking forward to connecting!
```

## Instructions

**To Respond**:
1. Review message and context
2. Edit response template if needed
3. Copy response and send via Instagram DM
4. Mark this file as completed (move to Done/)

**To Ignore**:
1. Move this file to Rejected/ if not relevant
```

## Dependencies

```toml
[tool.poetry.dependencies]
requests = "^2.31.0"  # API calls
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

## Setup Instructions

```bash
# 1. Configure monitoring
nano gold/config/social_media_monitor_config.yaml

# 2. Test monitoring
python gold/src/watchers/social_media_monitor.py --test

# 3. Start continuous monitoring
pm2 start gold/ecosystem.config.js --only "gold-facebook-watcher,gold-instagram-watcher,gold-twitter-watcher"

# 4. Verify monitoring
pm2 logs gold-facebook-watcher
```

## Success Criteria

- ✅ All 3 platforms monitored every 5 minutes
- ✅ Engagements detected and classified correctly
- ✅ Action files created with context and suggestions
- ✅ Priority keywords working correctly
- ✅ Duplicate prevention working
- ✅ Error recovery for rate limits
- ✅ Audit logging for all engagements

## Related Skills

- **post-to-social-media**: Posts content that may generate engagement
- **manage-approvals**: Approval workflow for responses
- **generate-ceo-briefing**: Includes social media analytics

## Changelog

- **1.0.0** (2026-01-19): Initial implementation for Gold tier

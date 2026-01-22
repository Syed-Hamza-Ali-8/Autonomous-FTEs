# Twitter Post Example

## Scenario
Posting a concise business update to Twitter with character limit constraints.

## Input

```python
from gold.src.actions.social_media_poster import SocialMediaPoster

poster = SocialMediaPoster(vault_path="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

# Create draft for Twitter
draft_path = poster.create_draft(
    content="🚀 Just launched our AI automation platform! "
            "Clients are saving 12+ hours/week on repetitive tasks. "
            "Email management, scheduling, social media - all automated. "
            "Want to learn more? DM us! "
            "#AI #Automation #Productivity",
    platforms=["twitter"],
    image_path=None
)
```

## Draft File Created

**Location**: `Needs_Action/social_post_20260119_150030_tw001.md`

```markdown
---
id: social_post_20260119_150030_tw001
type: social_media_post
status: pending_approval
created_at: 2026-01-19T15:00:30Z
timeout_at: 2026-01-20T15:00:30Z
platforms:
  - twitter
---

# Social Media Post Draft

**Status**: ⏳ Pending Approval
**Created**: 2026-01-19 3:00 PM
**Platform**: Twitter

## Content

🚀 Just launched our AI automation platform! Clients are saving 12+ hours/week on repetitive tasks. Email management, scheduling, social media - all automated. Want to learn more? DM us! #AI #Automation #Productivity

## Platform Details

- **Character Count**: 213 / 280 (76%)
- **Hashtags**: 3
- **Mentions**: 0
- **Links**: 0
- **Images**: 0

⚠️ **Note**: Twitter character limit is 280. This post is within limits.

## Instructions

**To Approve**: Change `status: pending_approval` to `status: approved` and save.
**To Reject**: Change `status: pending_approval` to `status: rejected` and add `rejection_reason`.
**To Edit**: Modify content above, then approve.
```

## User Action

User reviews and approves:

```yaml
status: approved
```

## Execution

```python
results = poster.execute_approved_draft(draft_path)
print(results)
```

## Output

```json
{
  "twitter": {
    "success": true,
    "post_id": "1234567890123456789",
    "url": "https://twitter.com/user/status/1234567890123456789",
    "timestamp": "2026-01-19T15:05:15Z",
    "engagement": {
      "likes": 0,
      "retweets": 0,
      "replies": 0,
      "impressions": 0
    }
  }
}
```

## Final File (Done/)

**Location**: `Done/social_post_20260119_150030_tw001.md`

```yaml
---
id: social_post_20260119_150030_tw001
type: social_media_post
status: completed
created_at: 2026-01-19T15:00:30Z
approved_at: 2026-01-19T15:05:10Z
executed_at: 2026-01-19T15:05:15Z
platforms:
  twitter:
    success: true
    post_id: "1234567890123456789"
    url: "https://twitter.com/user/status/1234567890123456789"
    engagement:
      likes: 0
      retweets: 0
      replies: 0
      impressions: 0
---
```

## Audit Log Entry

```json
{
  "timestamp": "2026-01-19T15:05:15Z",
  "action_type": "social_media_post",
  "action_id": "social_post_20260119_150030_tw001",
  "actor": "claude_code",
  "platform": "twitter",
  "status": "success",
  "post_id": "1234567890123456789",
  "content_length": 213,
  "hashtags": 3,
  "approval_status": "approved",
  "approved_by": "human",
  "execution_time_ms": 1876
}
```

## Character Limit Handling

Twitter's 280-character limit requires careful content optimization:

### Original Content (if too long)
```
🚀 Just launched our AI automation platform! Our clients are saving an average of 12+ hours per week on repetitive tasks like email management, scheduling, and social media posting - all automated. Want to learn more about how we can help your business? DM us! #AI #Automation #Productivity #Business
```
**Length**: 312 characters ❌ (exceeds 280 limit)

### Optimized Content
```
🚀 Just launched our AI automation platform! Clients are saving 12+ hours/week on repetitive tasks. Email management, scheduling, social media - all automated. Want to learn more? DM us! #AI #Automation #Productivity
```
**Length**: 213 characters ✅ (within 280 limit)

### Optimization Techniques
1. Remove unnecessary words ("an average of" → "")
2. Use abbreviations ("per week" → "/week")
3. Shorten phrases ("Want to learn more about how we can help your business?" → "Want to learn more?")
4. Reduce hashtags if needed (removed #Business)
5. Use emojis to replace words where appropriate

## Success Criteria

- ✅ Draft created successfully
- ✅ Character limit respected (213/280)
- ✅ Human approval required and obtained
- ✅ Post published to Twitter
- ✅ Post ID and URL captured
- ✅ File moved to Done/
- ✅ Audit log entry created
- ✅ No errors or warnings

## Notes

- Twitter has strict 280-character limit (including hashtags, mentions, and spaces)
- Hashtags count toward character limit
- Links are automatically shortened by Twitter (t.co URLs)
- Emojis count as 2 characters each
- Engagement metrics updated by watchers
- Mock API returns immediate success; real API may have delays

# Facebook Post Example

## Scenario
Posting a business update to Facebook to generate leads and build brand awareness.

## Input

```python
from gold.src.actions.social_media_poster import SocialMediaPoster

poster = SocialMediaPoster(vault_path="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

# Create draft for Facebook
draft_path = poster.create_draft(
    content="🚀 Exciting news! We've just launched our AI-powered workflow automation platform.\n\n"
            "Our clients are saving an average of 12 hours per week on repetitive tasks. "
            "From email management to social media scheduling, we're making business automation accessible to everyone.\n\n"
            "Want to see how it works? Drop a comment or DM us!\n\n"
            "#AI #Automation #BusinessGrowth #Productivity #Innovation",
    platforms=["facebook"],
    image_path=None
)
```

## Draft File Created

**Location**: `Needs_Action/social_post_20260119_143045_fb001.md`

```markdown
---
id: social_post_20260119_143045_fb001
type: social_media_post
status: pending_approval
created_at: 2026-01-19T14:30:45Z
timeout_at: 2026-01-20T14:30:45Z
platforms:
  - facebook
---

# Social Media Post Draft

**Status**: ⏳ Pending Approval
**Created**: 2026-01-19 2:30 PM
**Platform**: Facebook

## Content

🚀 Exciting news! We've just launched our AI-powered workflow automation platform.

Our clients are saving an average of 12 hours per week on repetitive tasks. From email management to social media scheduling, we're making business automation accessible to everyone.

Want to see how it works? Drop a comment or DM us!

#AI #Automation #BusinessGrowth #Productivity #Innovation

## Platform Details

- **Character Count**: 342 / 63,206 (0.5%)
- **Hashtags**: 5
- **Mentions**: 0
- **Links**: 0
- **Images**: 0

## Instructions

**To Approve**: Change `status: pending_approval` to `status: approved` and save.
**To Reject**: Change `status: pending_approval` to `status: rejected` and add `rejection_reason`.
**To Edit**: Modify content above, then approve.
```

## User Action

User reviews the draft and approves it:

```yaml
status: approved  # Changed from pending_approval
```

## Execution

```python
# Automatic execution after approval detected
results = poster.execute_approved_draft(draft_path)

print(results)
```

## Output

```json
{
  "facebook": {
    "success": true,
    "post_id": "123456789_987654321",
    "url": "https://facebook.com/123456789/posts/987654321",
    "timestamp": "2026-01-19T14:35:20Z",
    "engagement": {
      "likes": 0,
      "comments": 0,
      "shares": 0
    }
  }
}
```

## Final File (Done/)

**Location**: `Done/social_post_20260119_143045_fb001.md`

```yaml
---
id: social_post_20260119_143045_fb001
type: social_media_post
status: completed
created_at: 2026-01-19T14:30:45Z
approved_at: 2026-01-19T14:35:12Z
executed_at: 2026-01-19T14:35:20Z
platforms:
  facebook:
    success: true
    post_id: "123456789_987654321"
    url: "https://facebook.com/123456789/posts/987654321"
    engagement:
      likes: 0
      comments: 0
      shares: 0
---
```

## Audit Log Entry

**Location**: `Logs/2026-01-19.json`

```json
{
  "timestamp": "2026-01-19T14:35:20Z",
  "action_type": "social_media_post",
  "action_id": "social_post_20260119_143045_fb001",
  "actor": "claude_code",
  "platform": "facebook",
  "status": "success",
  "post_id": "123456789_987654321",
  "content_length": 342,
  "hashtags": 5,
  "approval_status": "approved",
  "approved_by": "human",
  "execution_time_ms": 2341
}
```

## Success Criteria

- ✅ Draft created successfully
- ✅ Human approval required and obtained
- ✅ Post published to Facebook
- ✅ Post ID and URL captured
- ✅ File moved to Done/
- ✅ Audit log entry created
- ✅ No errors or warnings

## Notes

- Facebook has a very high character limit (63,206), so truncation is rarely needed
- Hashtags work well on Facebook but are less critical than on Instagram/Twitter
- Engagement metrics start at 0 and are updated by watchers
- Mock API returns immediate success; real API may have delays

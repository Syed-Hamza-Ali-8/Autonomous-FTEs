# Failed Post Example

## Scenario
Attempting to post to multiple platforms, but Instagram fails due to rate limiting.

## Input

```python
from gold.src.actions.social_media_poster import SocialMediaPoster

poster = SocialMediaPoster(vault_path="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

# Create draft for all platforms
draft_path = poster.create_draft(
    content="🎉 Big announcement coming tomorrow! Stay tuned for something exciting. #ComingSoon #Innovation #Business",
    platforms=["facebook", "instagram", "twitter"],
    image_path=None
)
```

## Execution

After approval, the system attempts to post to all three platforms:

```python
results = poster.execute_approved_draft(draft_path)
```

## Output (Partial Failure)

```json
{
  "facebook": {
    "success": true,
    "post_id": "123456789_987654321",
    "url": "https://facebook.com/123456789/posts/987654321",
    "timestamp": "2026-01-19T16:15:20Z"
  },
  "instagram": {
    "success": false,
    "error": "Rate limit exceeded. Please try again in 15 minutes.",
    "error_code": 429,
    "retry_after": 900,
    "timestamp": "2026-01-19T16:15:22Z"
  },
  "twitter": {
    "success": true,
    "post_id": "1234567890123456789",
    "url": "https://twitter.com/user/status/1234567890123456789",
    "timestamp": "2026-01-19T16:15:23Z"
  }
}
```

## File Status (Approved/)

**Location**: `Approved/social_post_20260119_161500_multi001.md`

File remains in Approved/ folder (not moved to Done/) because not all platforms succeeded:

```yaml
---
id: social_post_20260119_161500_multi001
type: social_media_post
status: partial_failure
created_at: 2026-01-19T16:15:00Z
approved_at: 2026-01-19T16:15:15Z
last_attempt_at: 2026-01-19T16:15:23Z
retry_count: 1
next_retry_at: 2026-01-19T16:30:23Z
platforms:
  facebook:
    success: true
    post_id: "123456789_987654321"
    url: "https://facebook.com/123456789/posts/987654321"
  instagram:
    success: false
    error: "Rate limit exceeded. Please try again in 15 minutes."
    error_code: 429
    retry_after: 900
  twitter:
    success: true
    post_id: "1234567890123456789"
    url: "https://twitter.com/user/status/1234567890123456789"
---

# Social Media Post Draft

**Status**: ⚠️ Partial Failure
**Created**: 2026-01-19 4:15 PM
**Platforms**: Facebook ✅, Instagram ❌, Twitter ✅

## Content

🎉 Big announcement coming tomorrow! Stay tuned for something exciting. #ComingSoon #Innovation #Business

## Execution Results

### Facebook ✅
- **Status**: Success
- **Post ID**: 123456789_987654321
- **URL**: https://facebook.com/123456789/posts/987654321

### Instagram ❌
- **Status**: Failed
- **Error**: Rate limit exceeded. Please try again in 15 minutes.
- **Error Code**: 429
- **Retry After**: 15 minutes

### Twitter ✅
- **Status**: Success
- **Post ID**: 1234567890123456789
- **URL**: https://twitter.com/user/status/1234567890123456789

## Next Steps

The system will automatically retry posting to Instagram in 15 minutes.

**Manual Retry**: If you want to retry immediately, change `status: partial_failure` to `status: retry_now` and save.

**Cancel Retry**: To cancel the retry, change `status: partial_failure` to `status: cancelled` and save.
```

## Retry Logic

The system will automatically retry the failed platform:

```python
# Automatic retry after 15 minutes
time.sleep(900)  # Wait 15 minutes

# Retry only Instagram
retry_result = poster.retry_failed_platform(
    draft_path=draft_path,
    platform="instagram"
)
```

## Retry Output (Success)

```json
{
  "instagram": {
    "success": true,
    "post_id": "ABC123XYZ",
    "url": "https://instagram.com/p/ABC123XYZ",
    "timestamp": "2026-01-19T16:30:25Z",
    "retry_attempt": 2
  }
}
```

## Final File (Done/)

After successful retry, file moves to Done/:

```yaml
---
id: social_post_20260119_161500_multi001
type: social_media_post
status: completed
created_at: 2026-01-19T16:15:00Z
approved_at: 2026-01-19T16:15:15Z
executed_at: 2026-01-19T16:15:23Z
completed_at: 2026-01-19T16:30:25Z
retry_count: 2
platforms:
  facebook:
    success: true
    post_id: "123456789_987654321"
    url: "https://facebook.com/123456789/posts/987654321"
  instagram:
    success: true
    post_id: "ABC123XYZ"
    url: "https://instagram.com/p/ABC123XYZ"
    retry_attempt: 2
  twitter:
    success: true
    post_id: "1234567890123456789"
    url: "https://twitter.com/user/status/1234567890123456789"
---
```

## Audit Log Entries

### Initial Attempt
```json
{
  "timestamp": "2026-01-19T16:15:23Z",
  "action_type": "social_media_post",
  "action_id": "social_post_20260119_161500_multi001",
  "actor": "claude_code",
  "platforms": ["facebook", "instagram", "twitter"],
  "status": "partial_failure",
  "facebook": {"success": true, "post_id": "123456789_987654321"},
  "instagram": {"success": false, "error": "Rate limit exceeded", "error_code": 429},
  "twitter": {"success": true, "post_id": "1234567890123456789"},
  "execution_time_ms": 3421
}
```

### Retry Attempt
```json
{
  "timestamp": "2026-01-19T16:30:25Z",
  "action_type": "social_media_post_retry",
  "action_id": "social_post_20260119_161500_multi001",
  "actor": "claude_code",
  "platform": "instagram",
  "status": "success",
  "post_id": "ABC123XYZ",
  "retry_attempt": 2,
  "execution_time_ms": 2156
}
```

## Error Handling

### Common Errors

**Rate Limit (429)**:
- Wait for `retry_after` seconds
- Automatic retry scheduled
- No user action needed

**Authentication Failed (401)**:
- Credentials expired or invalid
- Notify user to re-authenticate
- Manual intervention required

**Invalid Content (400)**:
- Content violates platform policies
- User must edit content
- No automatic retry

**Network Timeout (504)**:
- Temporary network issue
- Automatic retry with exponential backoff
- Max 3 retry attempts

### Graceful Degradation

When one platform fails:
1. ✅ Continue posting to other platforms
2. ✅ Log the failure with details
3. ✅ Schedule automatic retry if appropriate
4. ✅ Keep file in Approved/ (not Done/)
5. ✅ Notify user of partial failure
6. ✅ Update file with status and next steps

## Success Criteria

- ✅ Partial success handled gracefully
- ✅ Successful platforms posted correctly
- ✅ Failed platform logged with error details
- ✅ Automatic retry scheduled
- ✅ Retry successful after waiting
- ✅ File moved to Done/ after all platforms succeed
- ✅ Audit log entries for both attempts
- ✅ User notified of status

## Notes

- Partial failures are common with multi-platform posting
- Rate limits are the most common cause of failures
- System handles retries automatically
- User can manually retry or cancel
- File only moves to Done/ when ALL platforms succeed
- Each platform's result is tracked independently

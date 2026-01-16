# Failed LinkedIn Post Example

This example shows a failed LinkedIn post execution with error recovery.

## Scenario

**Topic**: workflow optimization
**Posting Time**: 2026-01-16 09:00:00
**Status**: Failed (Session Expired)

## Generated Content

```
💡 Key insight from this week: workflow optimization

Automation isn't about replacing humans—it's about empowering
them to focus on what matters most.

What's your take on AI-powered business automation?

#AI #BusinessGrowth #Productivity
```

## Execution Log

```json
{
  "timestamp": "2026-01-16T09:00:15",
  "level": "ERROR",
  "service": "linkedin_scheduler",
  "action": "post_to_linkedin",
  "topic": "workflow optimization",
  "content_length": 195,
  "has_image": false,
  "result": {
    "success": false,
    "error": "Session expired",
    "message": "LinkedIn session expired. Please re-login.",
    "retry_count": 0,
    "execution_time_ms": 8230
  }
}
```

## Browser Automation Steps

1. ✅ Launched Chromium with persistent session
2. ✅ Navigated to https://www.linkedin.com/feed/
3. ❌ Detected redirect to login page (session expired)
4. ❌ Aborted posting attempt
5. ✅ Closed browser
6. ✅ Logged error with recovery instructions

**Total execution time**: 8.23 seconds

## Error Details

**Error Type**: Session Expired
**Error Code**: AUTH_EXPIRED
**Recovery Action**: Re-run setup script

## Recovery Steps

1. **Immediate**: Log error and notify user
2. **Manual**: User runs setup script
   ```bash
   python silver/scripts/setup_linkedin.py
   ```
3. **Automatic**: Next scheduled post will retry

## Root Cause Analysis

**Why did session expire?**
- LinkedIn sessions typically last 7-30 days
- Session may have been invalidated by:
  - Password change
  - Security check
  - Manual logout from another device
  - LinkedIn security policy

**Prevention**:
- Monitor session health
- Periodic session refresh (future enhancement)
- Alert user before expiration (future enhancement)

## User Notification

```
⚠️ LinkedIn Posting Failed

Error: Session expired
Action Required: Re-run setup script

Command:
  python silver/scripts/setup_linkedin.py

This will open a browser for you to login again.
Your session will be saved for future posts.
```

## Next Steps

1. User re-runs setup script
2. New session saved
3. Next scheduled post will succeed
4. Monitor logs for recurring issues

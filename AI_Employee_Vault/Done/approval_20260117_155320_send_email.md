---
id: approval_20260117_155320_send_email
action_type: send_email
status: completed
created_at: '2026-01-17T15:53:20.546628'
timeout_at: '2026-01-18T15:53:20.546618'
risk_level: high
risk_score: 70
approved_at: '2026-01-17T15:53:20.613589'
executed_at: '2026-01-17T15:53:20.633387'
retry_count: 0
result:
  success: true
  message_id: <test-1768647200.633372@example.com>
  timestamp: '2026-01-17T15:53:20.633381'
---
# Approval Request: Send Email

**Action**: Send Email
**Status**: ✅ Completed
**Created**: 2026-01-17 03:53 PM
**Timeout**: 1 days

## Action Details

- **To**: test@example.com
- **Subject**: HITL Test Email
- **Body**: This is a test email to verify HITL workflow is working.
- **External Recipient**: True
- **Reversible**: False

## Risk Assessment

- No specific risks identified

## Instructions

To approve this action:
1. Change `status: pending` to `status: approved` in the YAML frontmatter above
2. Save the file
3. The action will execute automatically within 1 minute

To reject this action:
1. Change `status: pending` to `status: rejected` in the YAML frontmatter above
2. Add `rejection_reason: "Your reason here"` to the YAML frontmatter
3. Save the file
4. The action will be cancelled

## Timeout

If no response within 1 days, this request will expire and the action will be cancelled.


## Execution Details

**Executed At**: 2026-01-17 03:53 PM
**Retry Count**: 0
**Result**: Success

### Result Data

```json
{'success': True, 'message_id': '<test-1768647200.633372@example.com>', 'timestamp': '2026-01-17T15:53:20.633381'}
```

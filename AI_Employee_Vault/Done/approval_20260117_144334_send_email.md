---
id: approval_20260117_144334_send_email
action_type: send_email
status: completed
created_at: '2026-01-17T14:43:34.634579'
timeout_at: '2026-01-18T14:43:34.634565'
risk_level: high
risk_score: 70
approved_at: '2026-01-17T14:43:34.993822'
executed_at: '2026-01-17T14:43:35.054769'
retry_count: 0
result:
  success: true
  message_id: <test-1768643015.054721@example.com>
  timestamp: '2026-01-17T14:43:35.054747'
---
# Approval Request: Send Email

**Action**: Send Email
**Status**: ✅ Completed
**Created**: 2026-01-17 02:43 PM
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

**Executed At**: 2026-01-17 02:43 PM
**Retry Count**: 0
**Result**: Success

### Result Data

```json
{'success': True, 'message_id': '<test-1768643015.054721@example.com>', 'timestamp': '2026-01-17T14:43:35.054747'}
```

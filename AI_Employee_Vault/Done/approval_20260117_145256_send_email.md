---
id: approval_20260117_145256_send_email
action_type: send_email
status: completed
created_at: '2026-01-17T14:52:56.988191'
timeout_at: '2026-01-18T14:52:56.988182'
risk_level: high
risk_score: 70
approved_at: '2026-01-17T14:52:57.086032'
executed_at: '2026-01-17T14:52:57.198964'
retry_count: 0
result:
  success: true
  message_id: mock_integration_test_123
---
# Approval Request: Send Email

**Action**: Send Email
**Status**: ✅ Completed
**Created**: 2026-01-17 02:52 PM
**Timeout**: 1 days

## Action Details

- **To**: test@example.com
- **Subject**: Integration Test Email
- **Body**: This is a test email
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

**Executed At**: 2026-01-17 02:52 PM
**Retry Count**: 0
**Result**: Success

### Result Data

```json
{'success': True, 'message_id': 'mock_integration_test_123'}
```

---
id: approval_20260114_022832_send_email
action_type: send_email
status: rejected
created_at: '2026-01-14T02:28:32.554922'
timeout_at: '2026-01-15T02:28:32.554666'
risk_level: high
risk_score: 70
rejected_at: '2026-01-15T02:28:36.464008'
rejection_reason: Timeout - no response within 1439 minutes
---
# Approval Request: Send Email

**Action**: Send Email
**Status**: ⏱️ Timeout

**Reason**: Timeout - no response within 1439 minutes
**Created**: 2026-01-14 02:28 AM
**Timeout**: 1 days

## Action Details

- **To**: test@example.com
- **Subject**: Test Email
- **Body**: This is a test email for approval workflow
- **External Recipient**: True
- **Reversible**: False

## Risk Assessment

- **Sensitivity**: high
- **Impact**: external_communication

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

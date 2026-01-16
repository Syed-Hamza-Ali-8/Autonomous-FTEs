---
id: approval_20260114_022833_send_email
action_type: send_email
status: rejected
created_at: '2026-01-14T02:28:33.599574'
timeout_at: '2026-01-15T02:28:33.599564'
risk_level: high
risk_score: 70
rejected_at: '2026-01-15T02:28:36.676895'
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
- **Subject**: End-to-End Test
- **Body**: Testing the complete approval workflow
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

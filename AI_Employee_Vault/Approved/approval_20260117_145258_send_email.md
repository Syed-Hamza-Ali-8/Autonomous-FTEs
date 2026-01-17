---
id: approval_20260117_145258_send_email
action_type: send_email
status: approved
created_at: '2026-01-17T14:52:58.102440'
timeout_at: '2026-01-18T14:52:58.102431'
risk_level: high
risk_score: 70
approved_at: '2026-01-17T14:52:58.190037'
---
# Approval Request: Send Email

**Action**: Send Email
**Status**: ✅ Approved
**Created**: 2026-01-17 02:52 PM
**Timeout**: 1 days

## Action Details

- **To**: integration-test@example.com
- **Subject**: Approval Workflow Test
- **Body**: Testing approval workflow
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

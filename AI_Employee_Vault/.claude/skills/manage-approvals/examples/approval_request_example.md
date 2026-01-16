---
id: approval_20260113_103045_abc123
action_type: send_email
status: pending
created_at: 2026-01-13T10:30:45Z
timeout_at: 2026-01-14T10:30:45Z
risk_level: high
---

# Approval Request: Send Email

**Action**: Send Email
**Status**: ⏳ Pending Approval
**Created**: 2026-01-13 10:30 AM
**Timeout**: 2026-01-14 10:30 AM (24 hours)

## Action Details

- **To**: client@example.com
- **Subject**: Project Update - Q1 2026
- **Body Preview**: Hi John, I wanted to share the latest updates on our Q1 progress...
- **Attachments**: None
- **CC**: None
- **BCC**: None

## Risk Assessment

- **Sensitivity**: High
- **Reversible**: No (email cannot be unsent)
- **Impact**: External Communication
- **Consequences**: Email will be sent to external recipient. This represents you professionally.

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

If no response within 24 hours, this request will expire and the action will be cancelled.

## Full Email Content

```
From: you@example.com
To: client@example.com
Subject: Project Update - Q1 2026

Hi John,

I wanted to share the latest updates on our Q1 progress. We've completed the initial phase and are on track for the March deadline.

Key achievements:
- Feature A completed (95% test coverage)
- Feature B in progress (60% complete)
- Documentation updated

Next steps:
- Complete Feature B by end of January
- Begin integration testing in February
- Final review and deployment in March

Let me know if you have any questions or concerns.

Best regards,
Your Name
```

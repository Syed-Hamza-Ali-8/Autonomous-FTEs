---
id: {{APPROVAL_ID}}
action_type: {{ACTION_TYPE}}
status: pending
created_at: {{CREATED_AT}}
timeout_at: {{TIMEOUT_AT}}
risk_level: {{RISK_LEVEL}}
---

# Approval Request: {{ACTION_TITLE}}

**Action**: {{ACTION_TYPE}}
**Status**: ⏳ Pending Approval
**Created**: {{CREATED_DATE}}
**Timeout**: {{TIMEOUT_DATE}}

## Action Details

{{ACTION_DETAILS}}

## Risk Assessment

- **Sensitivity**: {{SENSITIVITY}}
- **Reversible**: {{REVERSIBLE}}
- **Impact**: {{IMPACT}}
- **Consequences**: {{CONSEQUENCES}}

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

If no response within {{TIMEOUT_HOURS}} hours, this request will expire and the action will be cancelled.

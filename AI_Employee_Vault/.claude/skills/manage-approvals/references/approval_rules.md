# Approval Rules Configuration

## Overview

This document provides detailed guidance on configuring approval rules for the HITL (Human-in-the-Loop) approval workflow.

## Rule Structure

Each approval rule consists of:

```yaml
action_type: string          # Unique identifier for action type
requires_approval: boolean   # Whether approval is required
auto_approve_threshold: int  # Auto-approve if risk score below threshold (null = never)
timeout_minutes: int         # Minutes before request expires
notification_urgency: string # low, normal, critical
```

## Sensitive Actions

### Email Sending

```yaml
- action_type: send_email
  requires_approval: true
  auto_approve_threshold: null  # Never auto-approve
  timeout_minutes: 1440  # 24 hours
  notification_urgency: normal
  risk_factors:
    - external_recipient
    - irreversible
    - reputation_impact
```

**Rationale**: Emails are irreversible and represent the user externally. Always require approval.

### LinkedIn Posting

```yaml
- action_type: post_linkedin
  requires_approval: true
  auto_approve_threshold: null
  timeout_minutes: 1440
  notification_urgency: normal
  risk_factors:
    - public_visibility
    - professional_reputation
    - irreversible
```

**Rationale**: LinkedIn posts are public and affect professional reputation. Always require approval.

### File Deletion

```yaml
- action_type: delete_file
  requires_approval: true
  auto_approve_threshold: null
  timeout_minutes: 60  # 1 hour
  notification_urgency: critical
  risk_factors:
    - data_loss
    - irreversible
```

**Rationale**: File deletion is irreversible. Always require approval.

### External API Calls

```yaml
- action_type: api_call
  requires_approval: true
  auto_approve_threshold: 30  # Auto-approve if risk score < 30
  timeout_minutes: 120  # 2 hours
  notification_urgency: normal
  risk_factors:
    - external_service
    - potential_cost
    - data_exposure
```

**Rationale**: External API calls may have costs or expose data. Require approval unless low risk.

## Non-Sensitive Actions

### Read Operations

```yaml
- action_type: read_file
  requires_approval: false
  auto_approve_threshold: 0
  timeout_minutes: null
  notification_urgency: null
```

**Rationale**: Read-only operations have no side effects. No approval needed.

### Search Operations

```yaml
- action_type: search_vault
  requires_approval: false
  auto_approve_threshold: 0
  timeout_minutes: null
  notification_urgency: null
```

**Rationale**: Search operations are read-only. No approval needed.

### Plan Creation

```yaml
- action_type: create_plan
  requires_approval: false
  auto_approve_threshold: 0
  timeout_minutes: null
  notification_urgency: null
```

**Rationale**: Creating plans is internal and reversible. No approval needed.

## Risk Assessment

### Risk Score Calculation

Risk score is calculated based on multiple factors:

```python
def calculate_risk_score(action_details):
    score = 0

    # External impact
    if action_details.get('external_recipient'):
        score += 40

    # Reversibility
    if not action_details.get('reversible', True):
        score += 30

    # Data sensitivity
    if action_details.get('contains_pii'):
        score += 20

    # Financial impact
    if action_details.get('has_cost'):
        score += 10

    return score
```

### Risk Levels

- **0-20**: Low risk (may auto-approve)
- **21-50**: Medium risk (require approval)
- **51-100**: High risk (require approval + additional review)

## Timeout Configuration

### Recommended Timeouts

- **Critical actions** (delete, payment): 1 hour
- **External communication** (email, post): 24 hours
- **Internal operations** (file move, rename): 4 hours
- **API calls**: 2 hours

### Timeout Behavior

When a request times out:
1. Status changed to `rejected`
2. Rejection reason: "Timeout - no response within {timeout_minutes} minutes"
3. File moved to `Rejected/` folder
4. Audit log entry created
5. User notified (if notifications enabled)

## Notification Settings

### Urgency Levels

```yaml
notification_settings:
  low:
    sound: false
    desktop: true
    priority: low

  normal:
    sound: true
    desktop: true
    priority: normal

  critical:
    sound: true
    desktop: true
    priority: critical
    repeat_interval: 300  # Repeat every 5 minutes until acknowledged
```

### Platform-Specific Settings

**Linux (libnotify)**:
```yaml
linux:
  icon: /path/to/icon.png
  timeout: 10000  # milliseconds
  category: "approval-request"
```

**Windows**:
```yaml
windows:
  app_id: "AI Employee Vault"
  icon: "C:\\path\\to\\icon.ico"
  duration: "short"  # short, long
```

**macOS**:
```yaml
macos:
  subtitle: "Approval Required"
  sound: "default"
```

## Custom Rules

### Adding New Action Types

1. Define action type in `approval_rules.yaml`:

```yaml
- action_type: custom_action
  requires_approval: true
  auto_approve_threshold: null
  timeout_minutes: 120
  notification_urgency: normal
```

2. Update `ApprovalManager.is_sensitive_action()`:

```python
def is_sensitive_action(self, action_type: str) -> bool:
    sensitive_actions = [
        'send_email',
        'post_linkedin',
        'delete_file',
        'api_call',
        'custom_action'  # Add here
    ]
    return action_type in sensitive_actions
```

3. Create approval request template in `templates/custom_action_template.md`

### Rule Inheritance

Rules can inherit from parent rules:

```yaml
- action_type: send_email_internal
  inherits_from: send_email
  requires_approval: false  # Override: internal emails don't need approval
  auto_approve_threshold: 0
```

## Best Practices

1. **Default to requiring approval**: When in doubt, require approval
2. **Short timeouts for critical actions**: Delete operations should timeout quickly
3. **Clear rejection reasons**: Always provide context for why action was rejected
4. **Test notification delivery**: Ensure notifications work on target platform
5. **Audit all decisions**: Log every approval/rejection for accountability
6. **Review rules regularly**: Update rules based on usage patterns

## Examples

See `examples/` folder for:
- `approval_request_example.md` - Standard approval request
- `high_risk_approval_example.md` - High-risk action requiring additional review
- `auto_approved_example.md` - Low-risk action that was auto-approved

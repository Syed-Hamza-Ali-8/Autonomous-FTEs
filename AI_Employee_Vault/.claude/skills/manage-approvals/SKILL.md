# Manage Approvals Skill

**Skill ID**: manage-approvals
**Version**: 1.0.0
**User Story**: US2 - Human-in-the-Loop Approval Workflow
**Priority**: P1 (MVP)

## Purpose

Implement human-in-the-loop (HITL) approval workflow for sensitive actions. This skill ensures 100% compliance with the constitution requirement that all sensitive actions (emails, posts, payments) require explicit human approval before execution.

## Capabilities

- **Approval Request Creation**: Create structured approval requests in Pending_Approval folder
- **Approval Status Checking**: Poll for user responses (Approved/Rejected)
- **Desktop Notifications**: Notify user of pending approvals using system notifications
- **Action Execution**: Execute approved actions with retry logic and error handling
- **Audit Logging**: Log all approval decisions and action results

## Architecture

### Core Components

1. **ApprovalManager** (`silver/src/approval/approval_manager.py`)
   - `create_approval_request(action_type, action_details, risk_assessment)` → request_id
   - `is_sensitive_action(action_type)` → bool
   - `execute_approved_action(request_id)` → result

2. **ApprovalChecker** (`silver/src/approval/approval_checker.py`)
   - `poll_for_approvals()` → List[ApprovalRequest]
   - `check_approval_status(request_id)` → status (pending/approved/rejected)

3. **ApprovalNotifier** (`silver/src/approval/approval_notifier.py`)
   - `send_notification(title, message, urgency)` → success

### Approval Workflow

```
1. Action Detected → Is Sensitive? → Yes → Create Approval Request
                                   → No → Execute Directly

2. Approval Request Created → Move to Pending_Approval/
                           → Send Desktop Notification
                           → Poll for User Response

3. User Reviews → Edit YAML frontmatter → Set status: approved/rejected
                                        → Add reason (if rejected)

4. Status Detected → Approved → Move to Approved/ → Execute Action
                  → Rejected → Move to Rejected/ → Log Reason
```

## Configuration

### Approval Rules (`silver/config/approval_rules.yaml`)

```yaml
sensitive_actions:
  # Email sending
  - action_type: send_email
    requires_approval: true
    auto_approve_threshold: null  # Never auto-approve
    timeout_minutes: 1440  # 24 hours

  # LinkedIn posting
  - action_type: post_linkedin
    requires_approval: true
    auto_approve_threshold: null
    timeout_minutes: 1440

  # File operations
  - action_type: delete_file
    requires_approval: true
    auto_approve_threshold: null
    timeout_minutes: 60

  # External API calls
  - action_type: api_call
    requires_approval: true
    auto_approve_threshold: null
    timeout_minutes: 120

non_sensitive_actions:
  # Read-only operations
  - action_type: read_file
    requires_approval: false

  - action_type: search_vault
    requires_approval: false

  - action_type: create_plan
    requires_approval: false

notification_settings:
  enabled: true
  urgency: normal  # low, normal, critical
  sound: true
  desktop: true
```

## Usage

### Create Approval Request

```python
from silver.src.approval.approval_manager import ApprovalManager

manager = ApprovalManager(vault_path="/path/to/vault")

# Create approval request for email sending
request_id = manager.create_approval_request(
    action_type="send_email",
    action_details={
        "to": "client@example.com",
        "subject": "Project Update",
        "body": "Here's the latest update...",
        "attachments": []
    },
    risk_assessment={
        "sensitivity": "high",
        "reversible": False,
        "impact": "external_communication"
    }
)

print(f"Approval request created: {request_id}")
# Desktop notification sent to user
```

### Check Approval Status

```python
from silver.src.approval.approval_checker import ApprovalChecker

checker = ApprovalChecker(vault_path="/path/to/vault")

# Check status of specific request
status = checker.check_approval_status(request_id)

if status["status"] == "approved":
    print("Action approved by user")
    # Execute action
elif status["status"] == "rejected":
    print(f"Action rejected: {status['reason']}")
    # Log rejection
else:
    print("Still pending approval")
```

### Execute Approved Action

```python
# Execute action with retry logic
result = manager.execute_approved_action(request_id)

if result["success"]:
    print(f"Action executed successfully: {result['message_id']}")
else:
    print(f"Action failed: {result['error']}")
    # Retry logic: max 3 attempts, exponential backoff (2s, 4s, 8s)
```

## Output Format

### Approval Request File

Created in `Pending_Approval/` folder:

```markdown
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
- **Subject**: Project Update
- **Body Preview**: Here's the latest update...
- **Attachments**: None

## Risk Assessment

- **Sensitivity**: High
- **Reversible**: No
- **Impact**: External Communication
- **Consequences**: Email will be sent to external recipient

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
```

### After Approval

File moves to `Approved/` folder with updated frontmatter:

```yaml
---
id: approval_20260113_103045_abc123
action_type: send_email
status: approved
created_at: 2026-01-13T10:30:45Z
approved_at: 2026-01-13T10:35:12Z
executed_at: 2026-01-13T10:35:15Z
execution_result: success
message_id: <abc123@smtp.gmail.com>
---
```

### After Rejection

File moves to `Rejected/` folder with rejection reason:

```yaml
---
id: approval_20260113_103045_abc123
action_type: send_email
status: rejected
created_at: 2026-01-13T10:30:45Z
rejected_at: 2026-01-13T10:35:12Z
rejection_reason: "Not ready to send yet, need to review content first"
---
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
plyer = "^2.1.0"  # Desktop notifications
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
watchdog = "^4.0.0"  # File system monitoring (optional)
```

### System Requirements

- Python 3.13+
- Desktop notification support (Linux: libnotify, Windows: native, macOS: native)

## Setup Instructions

### 1. Configure Approval Rules

```bash
# Edit approval rules
nano silver/config/approval_rules.yaml

# Customize sensitive actions, timeouts, notification settings
```

### 2. Create Vault Folders

```bash
# Create approval folders
mkdir -p Pending_Approval Approved Rejected

# Verify folders exist
ls -la | grep -E "Pending_Approval|Approved|Rejected"
```

### 3. Test Notifications

```bash
# Test desktop notifications
python silver/scripts/test_approval.py --test-notification

# Should see desktop notification appear
```

### 4. Start Approval Checker

```bash
# Start approval checker (polls every 10 seconds)
python -m silver.src.approval.approval_checker &

# Or use startup script
./silver/scripts/start_watchers.sh
```

## Error Handling

### Timeout Handling

- **Default timeout**: 24 hours for most actions
- **Expired requests**: Automatically moved to Rejected/ with reason "Timeout"
- **Notification**: User notified 1 hour before timeout

### File System Errors

- **Permission denied**: Log error, notify user
- **File not found**: Assume request was manually deleted, skip
- **Invalid YAML**: Notify user, keep in Pending_Approval/

### Notification Errors

- **Notification failed**: Log error, continue (user can still check folder manually)
- **No notification support**: Graceful degradation (file-based only)

## Performance

- **Polling interval**: 10 seconds (configurable)
- **Memory**: ~20MB per checker process
- **CPU**: Minimal (<1% on modern systems)
- **Disk I/O**: Low (only reads changed files)

## Testing

### Unit Tests

```bash
pytest silver/tests/unit/test_approval_manager.py
pytest silver/tests/unit/test_approval_checker.py
pytest silver/tests/unit/test_approval_notifier.py
```

### Integration Tests

```bash
pytest silver/tests/integration/test_approval_workflow.py
```

### Manual Testing

1. Create test approval request:
   ```bash
   python silver/scripts/test_approval.py --create-test-request
   ```

2. Verify desktop notification appears

3. Open `Pending_Approval/` folder and find the request file

4. Edit YAML frontmatter: change `status: pending` to `status: approved`

5. Save file

6. Verify file moves to `Approved/` within 10 seconds

7. Check audit log in `Logs/YYYY-MM-DD.json`

## Success Criteria

- ✅ 100% approval compliance for sensitive actions
- ✅ Desktop notifications delivered within 1 second
- ✅ Approval status detected within 10 seconds
- ✅ Approved actions executed within 1 minute
- ✅ Audit log entry created for every approval decision
- ✅ Graceful handling of timeouts and errors

## Related Skills

- **monitor-communications**: Creates action files that may require approval
- **execute-actions**: Executes approved actions via MCP server
- **create-plans**: Plans may include actions requiring approval

## References

- See `references/approval_rules.md` for detailed approval rule configuration
- See `references/notification_api.md` for desktop notification API details

## Examples

- See `examples/approval_request_example.md` for approval request format
- See `examples/approved_action_example.md` for approved action format
- See `examples/rejected_action_example.md` for rejected action format

## Changelog

- **1.0.0** (2026-01-13): Initial implementation for Silver tier MVP

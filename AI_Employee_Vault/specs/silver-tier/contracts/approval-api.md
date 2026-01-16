# Approval API Contract

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Purpose**: Define the interface contract for Human-in-the-Loop (HITL) approval workflow

## Overview

The approval workflow ensures that all sensitive actions require explicit human approval before execution. This contract defines the interfaces for creating approval requests, checking approval status, and executing approved actions.

---

## ApprovalManager Class

### create_approval_request()

```python
def create_approval_request(
    self,
    action_type: str,
    action_details: Dict[str, Any],
    risk_assessment: Dict[str, str]
) -> str:
    """
    Create an approval request for a sensitive action.

    Args:
        action_type: Type of action (email_send, linkedin_post, payment, file_delete)
        action_details: Action-specific parameters (to, subject, content, etc.)
        risk_assessment: Risk analysis (sensitivity, reversibility, impact)

    Returns:
        request_id: Unique identifier for the approval request

    Raises:
        ValueError: If action_type is invalid or action_details missing required fields
        PermissionError: If cannot write to Pending_Approval folder

    Contract Requirements:
        - Must create file in /Pending_Approval folder
        - Filename format: APPROVAL_{action_type}_{timestamp}.md
        - Must include YAML frontmatter with all required fields
        - Must set expires to 24 hours from creation (per spec FR-015)
        - Must include clear approval instructions in markdown body
        - Must send desktop notification to user (per spec FR-016)
        - Must log approval request creation to audit log
        - Must return unique request_id for tracking
    """
```

**Expected Behavior**:
- Validate action_type is one of: email_send, linkedin_post, payment, file_delete
- Validate action_details has required fields for action_type
- Generate unique request_id: `req_{timestamp}_{random}`
- Calculate expires timestamp: created + 24 hours
- Create approval request file with YAML frontmatter
- Send desktop notification: "Approval needed: {action_type}"
- Log to audit log with action_type and request_id
- Return request_id for tracking

**File Format**:
```yaml
---
type: approval_request
request_id: "req_20260113_103045_abc"
action_type: email_send
created: "2026-01-13T10:30:45Z"
expires: "2026-01-14T10:30:45Z"
status: pending
approved_by: null
approved_at: null
rejection_reason: null
tags: [approval, email, sensitive]
---

## Action Details

**Type**: Send Email
**To**: client@example.com
**Subject**: Re: Project Update

## Proposed Content

[Draft email content]

## Risk Assessment

- **Sensitivity**: High (external client communication)
- **Reversibility**: Low (email cannot be unsent)
- **Impact**: Medium (affects client relationship)

## Approval Instructions

To approve: Change `status: pending` to `status: approved` and save.
To reject: Change `status: pending` to `status: rejected` and add `rejection_reason`.
```

---

### check_approval_status()

```python
def check_approval_status(self, request_id: str) -> Dict[str, Any]:
    """
    Check the current status of an approval request.

    Args:
        request_id: Unique identifier from create_approval_request()

    Returns:
        Dictionary with status information:
        - status (str): "pending" | "approved" | "rejected" | "expired"
        - approved_by (str, optional): Who approved (always "human")
        - approved_at (str, optional): ISO-8601 timestamp
        - rejection_reason (str, optional): Why rejected
        - file_path (Path): Path to approval request file

    Raises:
        FileNotFoundError: If approval request file doesn't exist
        ValueError: If request_id is invalid format

    Contract Requirements:
        - Must check /Pending_Approval, /Approved, /Rejected folders
        - Must read YAML frontmatter to get current status
        - Must check if request has expired (current time > expires)
        - Must auto-expire if past expiration time
        - Must move expired requests to /Rejected with auto-generated reason
        - Must return current status even if expired
        - Must not modify file unless auto-expiring
    """
```

**Expected Behavior**:
- Validate request_id format
- Search for file in /Pending_Approval, /Approved, /Rejected folders
- Read YAML frontmatter to get status
- Check if current time > expires timestamp
- If expired and still pending:
  - Update status to "expired"
  - Add rejection_reason: "Approval request expired after 24 hours"
  - Move to /Rejected folder
  - Log expiration to audit log
- Return status dictionary with all fields

**Status Transitions**:
```
pending → approved (user edits file)
pending → rejected (user edits file)
pending → expired (auto-expire after 24 hours)
```

---

### execute_approved_action()

```python
def execute_approved_action(self, request_id: str) -> Dict[str, Any]:
    """
    Execute an action that has been approved by the user.

    Args:
        request_id: Unique identifier for approved request

    Returns:
        Dictionary with execution result:
        - action_id (str): Unique identifier for executed action
        - result (str): "success" | "failure"
        - executed_at (str): ISO-8601 timestamp
        - error_message (str, optional): Error details if failed

    Raises:
        ValueError: If request is not in approved status
        FileNotFoundError: If approval request file doesn't exist
        ExecutionError: If action execution fails after max retries

    Contract Requirements:
        - Must verify status is "approved" before executing
        - Must create Action entity in /Approved folder
        - Must execute action through appropriate service (MCP, API)
        - Must implement retry logic with exponential backoff (max 3 retries per spec FR-031)
        - Must log all execution attempts to audit log
        - Must move to /Done folder after successful execution
        - Must update Dashboard with execution result
        - Must return execution result dictionary
    """
```

**Expected Behavior**:
- Check approval status is "approved"
- Read action details from approval request file
- Create Action entity in /Approved folder
- Execute action based on action_type:
  - `email_send`: Call MCP email server
  - `linkedin_post`: Call LinkedIn API
  - `payment`: Call payment service (future)
  - `file_delete`: Delete file with confirmation
- Implement retry logic:
  - Attempt 1: Execute immediately
  - Attempt 2: Wait 2 seconds, retry
  - Attempt 3: Wait 4 seconds, retry
  - Attempt 4: Wait 8 seconds, retry (max 3 retries)
- Log each attempt to audit log
- If success:
  - Update Action status to "completed"
  - Move to /Done folder
  - Update Dashboard
  - Return success result
- If failure after max retries:
  - Update Action status to "failed"
  - Log error details
  - Notify user of failure
  - Return failure result

---

## ApprovalChecker Class

### poll_for_approvals()

```python
def poll_for_approvals(self, interval: int = 30):
    """
    Continuously poll for approval status changes.

    Args:
        interval: Seconds between polls (default 30)

    Contract Requirements:
        - Must run indefinitely until interrupted
        - Must check all pending approval requests every interval seconds
        - Must detect status changes (pending → approved/rejected)
        - Must execute approved actions immediately
        - Must handle expired requests (auto-expire)
        - Must log all status changes to audit log
        - Must respect SIGTERM for graceful shutdown
    """
```

**Expected Behavior**:
- Enter infinite loop:
  1. List all files in /Pending_Approval
  2. For each file, check approval status
  3. If status changed to "approved":
     - Execute action via execute_approved_action()
     - Move to /Approved folder
  4. If status changed to "rejected":
     - Log rejection with reason
     - Move to /Rejected folder
  5. If expired:
     - Auto-expire and move to /Rejected
  6. Sleep for interval seconds
- Handle SIGTERM gracefully
- Continue running even after errors

---

## ApprovalNotifier Class

### send_notification()

```python
def send_notification(
    self,
    title: str,
    message: str,
    urgency: str = "normal"
):
    """
    Send desktop notification to user.

    Args:
        title: Notification title
        message: Notification body
        urgency: "low" | "normal" | "critical"

    Contract Requirements:
        - Must use cross-platform notification library (plyer)
        - Must work on Linux, Windows, macOS
        - Must not block execution (async notification)
        - Must handle notification failures gracefully (log and continue)
        - Must respect system notification settings
    """
```

**Expected Behavior**:
- Use `plyer.notification.notify()` for cross-platform support
- Set notification title and message
- Set urgency level (affects notification priority)
- Send notification asynchronously (don't block)
- If notification fails (permissions, system settings):
  - Log warning
  - Continue execution (don't crash)

---

## Sensitive Action Classification

### is_sensitive_action()

```python
def is_sensitive_action(
    action_type: str,
    action_details: Dict[str, Any]
) -> bool:
    """
    Determine if an action requires approval.

    Args:
        action_type: Type of action
        action_details: Action-specific parameters

    Returns:
        True if action requires approval, False otherwise

    Contract Requirements:
        - Must follow constitution HITL rules
        - Must check action_type against sensitive action list
        - Must check action_details against auto-approve thresholds
        - Must err on the side of caution (approve if uncertain)
    """
```

**Sensitive Actions (Always Require Approval)**:
- Email to new contacts or bulk sends
- All payments to new payees or > $100
- Social media replies, DMs, or unscheduled posts
- File deletions or moves outside vault
- Any irreversible action

**Auto-Approve Thresholds (No Approval Needed)**:
- Email replies to known contacts
- Payments < $50 to recurring payees
- Scheduled social media posts (pre-approved)
- File operations within vault (create, read, update)

---

## Configuration

Approval rules are configured in `silver/config/approval_rules.yaml`:

```yaml
sensitive_actions:
  email_send:
    always_approve: true
    exceptions:
      - condition: "recipient in known_contacts"
        auto_approve: true
      - condition: "is_reply and recipient in recent_conversations"
        auto_approve: true

  linkedin_post:
    always_approve: true
    exceptions:
      - condition: "is_scheduled and pre_approved"
        auto_approve: true

  payment:
    always_approve: true
    exceptions:
      - condition: "amount < 50 and payee in recurring_payees"
        auto_approve: true

  file_delete:
    always_approve: true
    exceptions:
      - condition: "path within vault"
        auto_approve: false  # Still require approval for deletes

auto_expire_hours: 24
notification_enabled: true
polling_interval: 30  # seconds
```

---

## Error Types

```python
class ApprovalError(Exception):
    """Base exception for approval workflow errors."""

class ApprovalExpiredError(ApprovalError):
    """Raised when approval request has expired."""

class ApprovalRejectedError(ApprovalError):
    """Raised when user rejects approval request."""

class ExecutionError(ApprovalError):
    """Raised when action execution fails after max retries."""
```

---

## Testing Contract

All approval workflow implementations must pass these tests:

1. **Unit Tests**:
   - `test_create_approval_request_format()`
   - `test_check_approval_status_pending()`
   - `test_check_approval_status_approved()`
   - `test_check_approval_status_expired()`
   - `test_execute_approved_action_success()`
   - `test_execute_approved_action_retry()`

2. **Integration Tests**:
   - `test_end_to_end_approval_workflow()`
   - `test_auto_expire_after_24_hours()`
   - `test_notification_delivery()`
   - `test_concurrent_approval_requests()`

3. **Security Tests**:
   - `test_cannot_bypass_approval()`
   - `test_cannot_modify_approved_action()`
   - `test_approval_file_tampering_detection()`

---

## Logging Contract

All approval operations must log to audit log:

```json
{
  "timestamp": "2026-01-13T10:30:45.123Z",
  "action_type": "approval_created",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {
    "request_id": "req_20260113_103045_abc",
    "action_type": "email_send",
    "expires": "2026-01-14T10:30:45Z"
  },
  "approval_status": "pending",
  "result": "success"
}
```

---

**Contract Status**: ✅ Complete
**Implementations Required**: ApprovalManager, ApprovalChecker, ApprovalNotifier

# Data Model: Silver Tier

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Storage**: Local Obsidian vault (markdown files with YAML frontmatter)

## Overview

This document defines the data entities for Silver tier. All entities are stored as markdown files with YAML frontmatter in the Obsidian vault. This maintains the local-first, privacy-focused architecture while enabling structured data management.

---

## 1. Watcher

**Purpose**: Configuration and state for communication channel monitoring scripts

**Storage Location**: `silver/config/watcher_config.yaml`

**Structure**:
```yaml
watchers:
  - id: gmail-watcher
    type: gmail
    enabled: true
    check_interval: 300  # seconds (5 minutes)
    last_check: "2026-01-13T10:30:00Z"
    last_message_id: "msg_abc123"
    config:
      query: "is:unread is:important"
      max_results: 10

  - id: whatsapp-watcher
    type: whatsapp
    enabled: true
    check_interval: 300  # seconds (5 minutes)
    last_check: "2026-01-13T10:30:00Z"
    session_path: "/path/to/session"
    config:
      urgent_keywords: ["urgent", "asap", "important"]

  - id: linkedin-watcher
    type: linkedin
    enabled: true
    check_interval: 900  # seconds (15 minutes)
    last_check: "2026-01-13T10:15:00Z"
    config:
      check_messages: true
      check_notifications: false
```

**Fields**:
- `id` (string, required): Unique identifier for watcher
- `type` (enum, required): gmail | whatsapp | linkedin
- `enabled` (boolean, required): Whether watcher is active
- `check_interval` (integer, required): Seconds between checks
- `last_check` (ISO-8601, optional): Timestamp of last check
- `last_message_id` (string, optional): ID of last processed message (for deduplication)
- `config` (object, required): Watcher-specific configuration

**Validation Rules**:
- `check_interval` must be >= 300 (5 minutes) to avoid rate limits
- `type` must be one of: gmail, whatsapp, linkedin
- `enabled` defaults to true if not specified

---

## 2. Message

**Purpose**: Communication received from monitored channels

**Storage Location**: `Needs_Action/MESSAGE_<channel>_<id>.md`

**Structure**:
```yaml
---
type: message
channel: gmail|whatsapp|linkedin
message_id: "unique_id_from_channel"
from: "sender@example.com" or "Sender Name"
subject: "Email subject" or null
received: "2026-01-13T10:30:00Z"
priority: high|medium|low
status: pending|processing|completed
tags: [email, important, business]
wikilinks: ["[[Dashboard]]", "[[Contact Name]]"]
---

## Message Content

[Full message text extracted from channel]

## Context

- **Channel**: Gmail
- **Thread ID**: thread_xyz789
- **Labels**: INBOX, IMPORTANT, UNREAD

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to team
- [ ] Create task in vault
```

**Fields**:
- `type` (string, required): Always "message"
- `channel` (enum, required): gmail | whatsapp | linkedin
- `message_id` (string, required): Unique ID from source channel
- `from` (string, required): Sender identifier
- `subject` (string, optional): Message subject (email only)
- `received` (ISO-8601, required): When message was received
- `priority` (enum, required): high | medium | low
- `status` (enum, required): pending | processing | completed
- `tags` (array, optional): Categorization tags
- `wikilinks` (array, optional): Links to other vault files

**Validation Rules**:
- `message_id` must be unique per channel
- `priority` determined by channel-specific rules (e.g., Gmail "important" label)
- `status` starts as "pending", moves to "processing" when AI analyzes, "completed" when done

**State Transitions**:
```
pending → processing → completed
```

---

## 3. ApprovalRequest

**Purpose**: Pending action requiring human approval before execution

**Storage Location**: `Pending_Approval/APPROVAL_<action_type>_<timestamp>.md`

**Structure**:
```yaml
---
type: approval_request
request_id: "req_20260113_103045_abc"
action_type: email_send|linkedin_post|payment|file_delete
created: "2026-01-13T10:30:45Z"
expires: "2026-01-14T10:30:45Z"  # 24 hours
status: pending|approved|rejected|expired
approved_by: null|"human"
approved_at: null|"2026-01-13T10:35:00Z"
rejection_reason: null|"Not appropriate for business context"
tags: [approval, email, sensitive]
---

## Action Details

**Type**: Send Email
**To**: client@example.com
**Subject**: Re: Project Update

## Proposed Content

[Draft email content or action details]

## Risk Assessment

- **Sensitivity**: High (external client communication)
- **Reversibility**: Low (email cannot be unsent)
- **Impact**: Medium (affects client relationship)

## Approval Instructions

To approve this action:
1. Change `status: pending` to `status: approved` in frontmatter
2. Save this file
3. System will execute within 1 minute

To reject this action:
1. Change `status: pending` to `status: rejected` in frontmatter
2. Add `rejection_reason: "Your reason here"` in frontmatter
3. Save this file
```

**Fields**:
- `type` (string, required): Always "approval_request"
- `request_id` (string, required): Unique identifier
- `action_type` (enum, required): email_send | linkedin_post | payment | file_delete
- `created` (ISO-8601, required): When request was created
- `expires` (ISO-8601, required): When request auto-expires (24 hours)
- `status` (enum, required): pending | approved | rejected | expired
- `approved_by` (string, optional): Who approved (always "human" for now)
- `approved_at` (ISO-8601, optional): When approved
- `rejection_reason` (string, optional): Why rejected

**Validation Rules**:
- `expires` must be exactly 24 hours after `created` (per spec FR-015)
- `status` can only transition: pending → approved/rejected/expired
- `approved_by` and `approved_at` required if status is "approved"
- `rejection_reason` required if status is "rejected"

**State Transitions**:
```
pending → approved → (moved to /Approved)
pending → rejected → (moved to /Rejected)
pending → expired → (moved to /Rejected with auto-generated reason)
```

---

## 4. Plan

**Purpose**: Structured plan for completing complex tasks

**Storage Location**: `Plans/PLAN_<task_name>_<date>.md`

**Structure**:
```yaml
---
type: plan
plan_id: "plan_20260113_product_launch"
title: "Product Launch Plan"
created: "2026-01-13T10:30:00Z"
updated: "2026-01-13T11:45:00Z"
status: draft|active|completed|cancelled
priority: high|medium|low
tags: [planning, product, launch]
wikilinks: ["[[Dashboard]]", "[[Product Roadmap]]"]
---

## Objective

Launch new product feature to existing customers by end of Q1 2026.

## Steps

- [ ] **Step 1**: Market research and competitive analysis
  - Dependencies: None
  - Estimated time: 1 week
  - Owner: Marketing team

- [ ] **Step 2**: Feature development and testing
  - Dependencies: Step 1 complete
  - Estimated time: 3 weeks
  - Owner: Engineering team

- [ ] **Step 3**: Marketing campaign preparation
  - Dependencies: Step 2 in progress
  - Estimated time: 2 weeks
  - Owner: Marketing team

## Dependencies

- Budget approval from finance
- Engineering resources available
- Marketing collateral ready

## Risks

1. **Technical Risk**: Feature complexity may delay timeline
   - Mitigation: Start with MVP, iterate based on feedback

2. **Market Risk**: Competitors may launch similar feature first
   - Mitigation: Monitor competitor activity, accelerate if needed

## Success Criteria

- Feature launched to 100% of customers
- 80% customer satisfaction score
- Zero critical bugs in first week
- 50% feature adoption within first month

## Progress Tracking

- **Overall**: 25% complete
- **Last Updated**: 2026-01-13 11:45:00
- **Next Review**: 2026-01-20
```

**Fields**:
- `type` (string, required): Always "plan"
- `plan_id` (string, required): Unique identifier
- `title` (string, required): Human-readable plan title
- `created` (ISO-8601, required): When plan was created
- `updated` (ISO-8601, required): Last modification time
- `status` (enum, required): draft | active | completed | cancelled
- `priority` (enum, required): high | medium | low
- `tags` (array, optional): Categorization tags
- `wikilinks` (array, optional): Links to related vault files

**Validation Rules**:
- `plan_id` must be unique
- `updated` must be >= `created`
- Steps must use checkbox format: `- [ ]` or `- [x]`
- Each step should have dependencies, time estimate, and owner

**State Transitions**:
```
draft → active → completed
draft → cancelled
active → cancelled
```

---

## 5. Action

**Purpose**: External action to be executed through MCP server

**Storage Location**: `Approved/ACTION_<type>_<timestamp>.md` (after approval)

**Structure**:
```yaml
---
type: action
action_id: "act_20260113_103045_xyz"
action_type: email_send|linkedin_post|calendar_event
approval_request_id: "req_20260113_103045_abc"
created: "2026-01-13T10:30:45Z"
approved_at: "2026-01-13T10:35:00Z"
executed_at: null|"2026-01-13T10:36:00Z"
status: approved|executing|completed|failed
retry_count: 0
max_retries: 3
result: null|"success"|"failure"
error_message: null|"SMTP connection timeout"
tags: [action, email, external]
---

## Action Details

**Type**: Send Email
**Service**: Email MCP Server
**Endpoint**: /send-email

## Parameters

```json
{
  "to": "client@example.com",
  "subject": "Re: Project Update",
  "body": "Email content here...",
  "from": "me@example.com"
}
```

## Execution Log

- **10:36:00**: Attempt 1 - Connecting to MCP server
- **10:36:05**: Attempt 1 - Sending email via SMTP
- **10:36:10**: Attempt 1 - Success (Message-ID: <abc@example.com>)
```

**Fields**:
- `type` (string, required): Always "action"
- `action_id` (string, required): Unique identifier
- `action_type` (enum, required): email_send | linkedin_post | calendar_event
- `approval_request_id` (string, required): Link to approval request
- `created` (ISO-8601, required): When action was created
- `approved_at` (ISO-8601, required): When action was approved
- `executed_at` (ISO-8601, optional): When execution completed
- `status` (enum, required): approved | executing | completed | failed
- `retry_count` (integer, required): Number of retry attempts
- `max_retries` (integer, required): Maximum retries (3 per spec FR-031)
- `result` (enum, optional): success | failure
- `error_message` (string, optional): Error details if failed

**Validation Rules**:
- `approval_request_id` must reference valid approval request
- `retry_count` must be <= `max_retries`
- `executed_at` required if status is "completed" or "failed"
- `result` required if status is "completed" or "failed"
- `error_message` required if result is "failure"

**State Transitions**:
```
approved → executing → completed (success)
approved → executing → failed → executing (retry) → completed/failed
```

---

## 6. Schedule

**Purpose**: Configuration for scheduled watcher execution

**Storage Location**: `silver/config/watcher_config.yaml` (embedded in Watcher entity)

**Structure**: See Watcher entity above

**Fields**:
- `check_interval` (integer, required): Seconds between executions
- `enabled` (boolean, required): Whether schedule is active
- `last_check` (ISO-8601, optional): Last execution timestamp

**Validation Rules**:
- `check_interval` must be >= 300 (5 minutes per spec FR-033)
- Schedule continues even after errors (per spec FR-034)

---

## 7. AuditLog

**Purpose**: Record of all system actions for transparency and debugging

**Storage Location**: `Logs/<YYYY-MM-DD>.json` (newline-delimited JSON)

**Structure**:
```json
{
  "timestamp": "2026-01-13T10:30:45.123Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {
    "subject": "Re: Project Update",
    "approval_request_id": "req_20260113_103045_abc"
  },
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success",
  "execution_time_ms": 5234,
  "error": null
}
```

**Fields**:
- `timestamp` (ISO-8601, required): When action occurred
- `action_type` (string, required): Type of action (email_send, watcher_check, approval_created, etc.)
- `actor` (enum, required): claude_code | watcher | human | mcp_server
- `target` (string, required): Target of action (email address, file path, etc.)
- `parameters` (object, optional): Action-specific parameters (no sensitive data)
- `approval_status` (enum, optional): auto | approved | rejected | not_required
- `approved_by` (string, optional): Who approved (human | system)
- `result` (enum, required): success | failure | pending
- `execution_time_ms` (integer, optional): Execution duration in milliseconds
- `error` (string, optional): Error message if failed

**Validation Rules**:
- `timestamp` must be ISO-8601 format with milliseconds
- No sensitive data in logs (mask credentials, PII per constitution)
- Logs retained for minimum 90 days (per constitution)
- One log entry per line (newline-delimited JSON)

---

## Entity Relationships

```
Watcher --creates--> Message
Message --triggers--> ApprovalRequest (if sensitive)
ApprovalRequest --becomes--> Action (if approved)
Action --logs-to--> AuditLog
Plan --references--> Message (context)
Plan --creates--> ApprovalRequest (for plan steps)
```

---

## File Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| Message | `MESSAGE_<channel>_<id>.md` | `MESSAGE_gmail_abc123.md` |
| ApprovalRequest | `APPROVAL_<type>_<timestamp>.md` | `APPROVAL_email_20260113_103045.md` |
| Plan | `PLAN_<task>_<date>.md` | `PLAN_product_launch_20260113.md` |
| Action | `ACTION_<type>_<timestamp>.md` | `ACTION_email_20260113_103045.md` |
| AuditLog | `<YYYY-MM-DD>.json` | `2026-01-13.json` |

---

## Storage Summary

| Entity | Location | Format | Count (typical) |
|--------|----------|--------|-----------------|
| Watcher | `silver/config/watcher_config.yaml` | YAML | 3-5 |
| Message | `Needs_Action/` | Markdown + YAML | 10-50/day |
| ApprovalRequest | `Pending_Approval/` | Markdown + YAML | 5-20/day |
| Plan | `Plans/` | Markdown + YAML | 1-10/week |
| Action | `Approved/` then `Done/` | Markdown + YAML | 5-20/day |
| AuditLog | `Logs/` | NDJSON | 1 file/day |

---

**Data Model Status**: ✅ Complete
**Ready for Contracts**: Yes

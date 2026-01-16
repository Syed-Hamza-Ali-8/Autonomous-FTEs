# Data Model: Bronze Tier Foundation

**Date**: 2026-01-12
**Feature**: Bronze Tier Foundation
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data structures used in the Bronze Tier Foundation. All data is stored as files in the Obsidian vault using markdown with YAML frontmatter for structured data and JSON for logs.

## Entity Definitions

### 1. File Metadata

**Purpose**: Represents information about a file awaiting processing in the Needs_Action folder.

**Storage**: Markdown file with YAML frontmatter
**Location**: `Needs_Action/{FILE_ID}.md`
**Naming Pattern**: `FILE_{original_filename}_{timestamp}.md`

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| type | string | Yes | Entity type identifier | "file_drop" |
| original_name | string | Yes | Original filename with extension | "document.pdf" |
| size | integer | Yes | File size in bytes | 1024000 |
| detected_at | datetime | Yes | ISO-8601 timestamp of detection | "2026-01-12T15:30:00Z" |
| status | enum | Yes | Processing status | "pending", "processing", "completed", "error" |
| file_type | string | Yes | Detected file type category | "pdf", "text", "image", "unknown" |
| mime_type | string | No | MIME type if detected | "application/pdf" |
| processing_notes | string | No | Notes from processing or errors | "Corrupted file header" |

**State Transitions**:
- `pending` → `processing` (when Agent Skill starts)
- `processing` → `completed` (successful processing)
- `processing` → `error` (processing failed)
- `error` → `pending` (manual retry by user)

**Validation Rules**:
- `original_name` must not be empty
- `size` must be >= 0
- `detected_at` must be valid ISO-8601 timestamp
- `status` must be one of the defined enum values
- `file_type` must be one of: "text", "pdf", "image", "document", "unknown"

**Example**:
```yaml
---
type: file_drop
original_name: quarterly-report.pdf
size: 2048576
detected_at: 2026-01-12T15:30:00Z
status: pending
file_type: pdf
mime_type: application/pdf
---

## File Information
- **Name:** quarterly-report.pdf
- **Size:** 2.0 MB
- **Type:** PDF document

## Suggested Actions
- [ ] Analyze content
- [ ] Extract key information
- [ ] Create summary
- [ ] Move to Done
```

---

### 2. Dashboard State

**Purpose**: Represents current system status and activity for user visibility.

**Storage**: Markdown file with YAML frontmatter
**Location**: `Dashboard.md` (vault root)
**Update Frequency**: After each file processing event

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| last_updated | datetime | Yes | ISO-8601 timestamp of last update | "2026-01-12T15:30:00Z" |
| watcher_status | enum | Yes | Watcher running state | "running", "stopped", "unknown" |
| watcher_last_check | datetime | No | Last successful Watcher check | "2026-01-12T15:29:55Z" |
| pending_count | integer | Yes | Number of files in Needs_Action | 3 |
| recent_activity | array | Yes | Last 5 processed files | See below |
| statistics | object | Yes | Processing statistics | See below |

**Recent Activity Item**:
```yaml
- timestamp: "2026-01-12T15:25:00Z"
  filename: "document.pdf"
  action: "processed"
  summary_length: 250
```

**Statistics Object**:
```yaml
statistics:
  today: 12
  this_week: 45
  total: 127
```

**Validation Rules**:
- `last_updated` must be valid ISO-8601 timestamp
- `watcher_status` must be one of: "running", "stopped", "unknown"
- `pending_count` must be >= 0
- `recent_activity` array max length: 5 items
- `statistics` all values must be >= 0

**Example**:
```yaml
---
last_updated: 2026-01-12T15:30:00Z
watcher_status: running
watcher_last_check: 2026-01-12T15:29:55Z
pending_count: 3
recent_activity:
  - timestamp: 2026-01-12T15:25:00Z
    filename: document.pdf
    action: processed
    summary_length: 250
  - timestamp: 2026-01-12T15:20:00Z
    filename: notes.txt
    action: processed
    summary_length: 120
statistics:
  today: 12
  this_week: 45
  total: 127
---

# AI Employee Dashboard

## System Status
- **Watcher:** ✅ Running
- **Last Check:** 2026-01-12 15:29:55

## Pending Items
- **Needs Action:** 3 files

## Recent Activity
1. [15:25] Processed: document.pdf → Summary created (250 chars)
2. [15:20] Processed: notes.txt → Archived (120 chars)

## Statistics
- **Today:** 12 files processed
- **This Week:** 45 files processed
- **Total:** 127 files processed
```

---

### 3. Processing Log Entry

**Purpose**: Represents a record of system actions for audit and debugging.

**Storage**: JSON (newline-delimited)
**Location**: `Logs/{YYYY-MM-DD}.json`
**Naming Pattern**: Daily log files (e.g., `2026-01-12.json`)

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| timestamp | datetime | Yes | ISO-8601 timestamp | "2026-01-12T15:30:00Z" |
| action_type | enum | Yes | Type of action performed | "file_detected", "file_processed", "error" |
| actor | enum | Yes | Component that performed action | "watcher", "claude_code", "human" |
| target | string | Yes | Target of the action | "document.pdf" |
| parameters | object | No | Additional action parameters | {"size": 1024000, "type": "pdf"} |
| result | enum | Yes | Action result | "success", "failure", "pending" |
| error_message | string | No | Error details if result is failure | "Permission denied" |

**Action Types**:
- `file_detected` - Watcher detected new file
- `metadata_created` - Metadata file created
- `file_moved` - File moved between folders
- `file_processed` - Agent Skill processed file
- `dashboard_updated` - Dashboard.md updated
- `error` - Error occurred

**Actor Types**:
- `watcher` - Python Watcher script
- `claude_code` - Claude Code Agent Skill
- `human` - Manual user action

**Result Types**:
- `success` - Action completed successfully
- `failure` - Action failed
- `pending` - Action in progress

**Validation Rules**:
- `timestamp` must be valid ISO-8601 timestamp
- `action_type` must be one of defined types
- `actor` must be one of defined actors
- `target` must not be empty
- `result` must be one of defined results
- `error_message` required if result is "failure"

**Example**:
```json
{"timestamp":"2026-01-12T15:30:00Z","action_type":"file_detected","actor":"watcher","target":"document.pdf","parameters":{"size":1024000,"type":"pdf"},"result":"success"}
{"timestamp":"2026-01-12T15:30:01Z","action_type":"metadata_created","actor":"watcher","target":"FILE_document.pdf_20260112153000.md","parameters":{"original_file":"document.pdf"},"result":"success"}
{"timestamp":"2026-01-12T15:30:15Z","action_type":"file_processed","actor":"claude_code","target":"document.pdf","parameters":{"summary_length":250},"result":"success"}
```

---

### 4. Company Rules

**Purpose**: Represents guidelines for AI behavior and processing rules.

**Storage**: Markdown file with structured sections
**Location**: `Company_Handbook.md` (vault root)
**Update Frequency**: Manual (user edits)

**Structure**:

```markdown
# Company Handbook

## Purpose and Scope
[Description of the AI Employee's role and boundaries]

## Processing Rules

### Text Files (.txt, .md)
- Extract main topics
- Summarize in 2-3 sentences
- Identify action items if present

### PDF Documents (.pdf)
- Extract title and author if available
- Summarize key sections
- Note page count

### Images (.png, .jpg, .jpeg)
- Describe visual content
- Identify text if present (OCR not required for Bronze)
- Note dimensions and file size

### Unknown File Types
- Record filename and size
- Note that content analysis is not available
- Move to Done without deep analysis

## Logging Requirements
- Log all file detections
- Log all processing attempts
- Log all errors with full details
- Use JSON format for machine readability

## Error Handling Guidelines
- Corrupted files → Move to Quarantine subfolder
- Permission errors → Log and skip
- Unknown file types → Create basic metadata only
- Processing timeout → Log error and mark as failed
```

**Validation Rules**:
- Must contain all required sections
- Processing rules must cover all supported file types
- Rules must be clear and actionable

---

## Relationships

```
File Metadata (1) ←→ (1) Physical File
  - One metadata file per physical file
  - Metadata filename includes original filename

Dashboard State (1) ←→ (N) Recent Activity Items
  - Dashboard contains array of recent activities
  - Max 5 items retained

Processing Log (1 file per day) ←→ (N) Log Entries
  - One log file per day
  - Multiple entries per file (newline-delimited JSON)

Company Rules (1) ←→ (N) File Metadata
  - Rules guide processing of all files
  - Referenced by Agent Skill during processing
```

---

## Data Flow

```
1. File Drop
   User → Inbox/ → Physical File

2. Detection
   Watcher → Detects File → Creates File Metadata → Needs_Action/

3. Processing
   Agent Skill → Reads File Metadata → Reads Physical File
   → Creates Summary → Updates File Metadata (status: completed)
   → Moves Physical File → Done/

4. Dashboard Update
   Agent Skill → Reads Dashboard State → Updates Recent Activity
   → Updates Statistics → Writes Dashboard.md

5. Logging
   All Steps → Append Log Entry → Logs/{date}.json
```

---

## Storage Estimates

**Per File**:
- Physical file: Variable (assume 1MB average)
- Metadata file: ~1KB
- Log entries: ~500 bytes (3 entries per file)
- Dashboard update: Negligible (single file)

**Daily (50 files)**:
- Physical files: 50MB
- Metadata files: 50KB
- Log file: 25KB
- Total: ~50MB/day

**90 Days (Bronze tier retention)**:
- Physical files: 4.5GB
- Metadata files: 4.5MB
- Log files: 2.25MB
- Total: ~4.5GB

**Mitigation**: User manually archives old files from Done/ folder. Logs can be compressed or deleted after 90 days.

---

## Schema Evolution

**Bronze Tier**: Fixed schemas (no migrations needed)

**Silver Tier Considerations**:
- Add `priority` field to File Metadata
- Add `approval_required` field for HITL
- Add `source` field (inbox, gmail, whatsapp)

**Gold Tier Considerations**:
- Add `retry_count` and `last_retry` for error recovery
- Add `processing_duration` for performance tracking
- Add `tags` array for categorization

# Research: Bronze Tier Foundation

**Date**: 2026-01-12
**Feature**: Bronze Tier Foundation
**Phase**: Phase 0 - Research & Technology Decisions

## Overview

This document captures research findings and technology decisions for the Bronze Tier Foundation. Each decision includes rationale, alternatives considered, and best practices.

## Technology Decisions

### 1. File System Monitoring: Python watchdog

**Decision**: Use Python `watchdog` library for monitoring the Inbox folder.

**Rationale**:
- Cross-platform support (Windows, macOS, Linux)
- Event-driven architecture (efficient, low CPU usage)
- Mature library (10+ years, widely used)
- Simple API for basic file monitoring
- Handles edge cases (file moves, renames, temporary files)

**Alternatives Considered**:
- **Polling with os.listdir()**: Rejected - inefficient, high CPU usage, misses rapid changes
- **inotify (Linux) / FSEvents (macOS) / ReadDirectoryChangesW (Windows)**: Rejected - platform-specific, complex to implement cross-platform
- **watchfiles (Rust-based)**: Rejected - newer library, less documentation, overkill for Bronze tier

**Best Practices**:
- Use `FileSystemEventHandler` class for clean event handling
- Implement debouncing for rapid file changes (wait 1 second after last event)
- Filter out temporary files (.tmp, .swp, ~$)
- Log all events for debugging
- Graceful shutdown with signal handlers (SIGINT, SIGTERM)

**Implementation Pattern**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            # Process file after debounce period
            pass
```

---

### 2. Structured Data in Markdown: YAML Frontmatter

**Decision**: Use YAML frontmatter for structured metadata in markdown files.

**Rationale**:
- Standard pattern in static site generators (Jekyll, Hugo, Obsidian)
- Human-readable and editable
- Obsidian natively supports YAML frontmatter
- Python `pyyaml` library for parsing
- Separates metadata from content

**Alternatives Considered**:
- **JSON files + separate .md files**: Rejected - two files per item, harder to manage
- **Embedded JSON in markdown**: Rejected - not human-friendly, breaks Obsidian rendering
- **Custom format**: Rejected - reinventing the wheel, no tooling support

**Best Practices**:
- Use `---` delimiters at start and end of frontmatter
- Keep frontmatter minimal (only structured data)
- Use ISO-8601 for timestamps
- Use lowercase with underscores for keys (snake_case)
- Validate required fields on read

**Example**:
```yaml
---
type: file_drop
original_name: document.pdf
size: 1024000
detected_at: 2026-01-12T15:30:00Z
status: pending
---

## File Information
Content goes here...
```

---

### 3. Agent Skills Implementation: Claude Agent Skills SDK

**Decision**: Implement file processing as a Claude Agent Skill using the official SDK.

**Rationale**:
- Constitution requirement (Principle II: Agent Skills Mandatory)
- Provides structure and error handling
- Integrates with Claude Code CLI
- Enables skill composition and reuse
- Better logging and observability

**Alternatives Considered**:
- **Standalone Python script**: Rejected - violates constitution, no integration with Claude Code
- **Custom CLI wrapper**: Rejected - reinventing Agent Skills framework

**Best Practices**:
- One skill per logical workflow (process-files skill)
- Clear SKILL.md documentation with usage examples
- Input validation at skill entry point
- Structured output (JSON or markdown)
- Error handling with meaningful messages
- Idempotent operations (safe to retry)

**Skill Structure**:
```
.claude/skills/process-files/
├── SKILL.md          # Documentation
└── skill.py          # Implementation
```

---

### 4. File Type Detection: mimetypes + magic numbers

**Decision**: Use Python `mimetypes` module with fallback to file extension.

**Rationale**:
- Built-in Python module (no external dependency)
- Sufficient for Bronze tier (common file types)
- Fast and reliable for standard extensions
- Fallback to extension if MIME type unknown

**Alternatives Considered**:
- **python-magic (libmagic)**: Rejected - external C dependency, overkill for Bronze tier
- **Extension-only detection**: Rejected - unreliable (files can have wrong extensions)
- **Content inspection**: Rejected - complex, slow, not needed for Bronze tier

**Best Practices**:
- Normalize extensions to lowercase
- Map MIME types to user-friendly categories (document, image, text)
- Handle unknown types gracefully (generic "file" category)
- Log detected types for debugging

**Implementation**:
```python
import mimetypes

def detect_file_type(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type:
        if mime_type.startswith('text/'):
            return 'text'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type == 'application/pdf':
            return 'pdf'
    return 'unknown'
```

---

### 5. Logging: JSON structured logs with daily rotation

**Decision**: Use JSON format for logs with daily file rotation by filename.

**Rationale**:
- Machine-readable (easy to parse, analyze)
- Human-readable with proper formatting
- Daily rotation prevents large files
- Filename-based rotation (no complex log rotation library needed)
- Supports required log format from constitution

**Alternatives Considered**:
- **Plain text logs**: Rejected - hard to parse, no structure
- **Python logging module with RotatingFileHandler**: Rejected - size-based rotation is complex, daily rotation simpler
- **Database logging**: Rejected - overkill for Bronze tier, violates local-first principle

**Best Practices**:
- One JSON object per line (newline-delimited JSON)
- ISO-8601 timestamps
- Include all required fields: timestamp, action_type, actor, target, result
- Flush after each write (ensure logs survive crashes)
- Use `Logs/YYYY-MM-DD.json` naming pattern

**Log Entry Format**:
```json
{
  "timestamp": "2026-01-12T15:30:00Z",
  "action_type": "file_detected",
  "actor": "watcher",
  "target": "document.pdf",
  "parameters": {"size": 1024000, "type": "pdf"},
  "result": "success"
}
```

---

### 6. Error Handling: Try-catch with continue-on-error

**Decision**: Wrap Watcher operations in try-catch blocks, log errors, and continue processing.

**Rationale**:
- Watcher must stay running (24+ hour uptime requirement)
- One bad file shouldn't crash the entire system
- Errors are logged for debugging
- Graceful degradation (skip problematic files)

**Alternatives Considered**:
- **Fail-fast**: Rejected - violates uptime requirement
- **Retry logic**: Deferred to Gold tier (error recovery feature)
- **Dead letter queue**: Deferred to Silver tier (too complex for Bronze)

**Best Practices**:
- Catch specific exceptions (FileNotFoundError, PermissionError, etc.)
- Log full exception details (type, message, traceback)
- Move problematic files to Quarantine folder
- Continue processing other files
- Signal handler for graceful shutdown (SIGINT, SIGTERM)

**Implementation Pattern**:
```python
try:
    process_file(filepath)
except Exception as e:
    logger.error(f"Error processing {filepath}: {e}")
    move_to_quarantine(filepath)
    continue  # Keep processing other files
```

---

### 7. Dashboard Updates: Direct file write with atomic replace

**Decision**: Update Dashboard.md by writing to temp file, then atomic rename.

**Rationale**:
- Prevents corruption if write is interrupted
- Atomic operation (file is never in partial state)
- Obsidian will reload file automatically
- Simple implementation (no locking needed)

**Alternatives Considered**:
- **Direct write**: Rejected - risk of corruption if interrupted
- **File locking**: Rejected - complex, platform-specific, can deadlock
- **Database**: Rejected - overkill, violates local-first principle

**Best Practices**:
- Write to `.Dashboard.md.tmp` first
- Use `os.replace()` for atomic rename (works on all platforms)
- Include last_updated timestamp in frontmatter
- Keep Recent Activity to last 5 items (trim older entries)

**Implementation**:
```python
import os

def update_dashboard(data):
    temp_path = "Dashboard.md.tmp"
    final_path = "Dashboard.md"

    with open(temp_path, 'w') as f:
        f.write(render_dashboard(data))

    os.replace(temp_path, final_path)  # Atomic
```

---

## Performance Considerations

### File Detection Latency
- **Target**: <10 seconds from file drop to metadata creation
- **Approach**: Event-driven watchdog (immediate notification) + 1-second debounce
- **Expected**: 1-2 seconds typical, 5 seconds worst case

### Processing Throughput
- **Target**: <30 seconds for text files, <60 seconds for PDFs/images
- **Bottleneck**: Claude Code API latency (network + inference time)
- **Mitigation**: Sequential processing (Bronze tier), parallel processing deferred to Gold tier

### Memory Usage
- **Target**: <100MB for Watcher process
- **Approach**: Event-driven (no polling), no file caching, stream large files
- **Expected**: 20-50MB typical

### Disk Usage
- **Target**: <1GB vault size for Bronze tier
- **Approach**: Manual log cleanup (user responsibility), no automatic rotation
- **Expected**: 10-100MB typical (depends on file volume)

---

## Security Considerations

### File System Access
- **Risk**: Watcher has read/write access to entire vault
- **Mitigation**: Run Watcher with user permissions (not root/admin), validate file paths

### Malicious Files
- **Risk**: User drops malicious file (virus, exploit)
- **Mitigation**: No file execution, only read/analyze, rely on OS-level antivirus

### Log Injection
- **Risk**: Filenames with special characters could break JSON logs
- **Mitigation**: JSON encoding handles escaping automatically

### Obsidian Vault Corruption
- **Risk**: Concurrent writes could corrupt files
- **Mitigation**: Atomic file writes, Obsidian handles concurrent reads gracefully

---

## Testing Strategy

### Unit Tests
- Test metadata creation with various file types
- Test logger JSON formatting
- Test file type detection
- Test Dashboard rendering

### Integration Tests
- End-to-end: Drop file → Watcher detects → Metadata created → Agent processes → File moved to Done
- Test with multiple file types (txt, pdf, image)
- Test error cases (corrupted file, permission denied)

### Manual Tests
- 24-hour uptime test (Watcher stability)
- Obsidian integration (Dashboard updates visible)
- Performance test (10 files dropped simultaneously)

---

## Open Questions & Future Research

### For Silver Tier
- How to integrate multiple Watchers (Gmail, WhatsApp) without conflicts?
- MCP server architecture for external actions
- HITL approval workflow implementation

### For Gold Tier
- Ralph Wiggum loop implementation details
- Error recovery and retry strategies
- Process management (PM2 vs supervisord)

---

## References

- [watchdog documentation](https://python-watchdog.readthedocs.io/)
- [YAML frontmatter spec](https://jekyllrb.com/docs/front-matter/)
- [Claude Agent Skills SDK](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Python mimetypes module](https://docs.python.org/3/library/mimetypes.html)
- [Newline-delimited JSON](http://ndjson.org/)

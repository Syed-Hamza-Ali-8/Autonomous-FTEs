# Watcher API Contract

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Purpose**: Define the interface contract for all communication channel watchers

## Overview

All watchers must implement the `BaseWatcher` abstract class to ensure consistent behavior across different communication channels (Gmail, WhatsApp, LinkedIn). This contract defines the required methods and expected behavior.

---

## BaseWatcher Abstract Class

### Constructor

```python
def __init__(self, vault_path: str, check_interval: int = 60):
    """
    Initialize the watcher.

    Args:
        vault_path: Absolute path to Obsidian vault root
        check_interval: Seconds between checks (minimum 300)

    Raises:
        ValueError: If check_interval < 300 (5 minutes)
        FileNotFoundError: If vault_path doesn't exist
    """
```

**Contract Requirements**:
- `vault_path` must be an absolute path to existing directory
- `check_interval` must be >= 300 seconds (5 minutes) to avoid rate limits
- Constructor must initialize `self.needs_action` path as `vault_path / 'Needs_Action'`
- Constructor must set up logger with watcher class name

---

## Required Methods

### 1. check_for_updates()

```python
@abstractmethod
def check_for_updates(self) -> List[Dict[str, Any]]:
    """
    Check the communication channel for new messages.

    Returns:
        List of message dictionaries with required fields:
        - message_id (str): Unique identifier from source channel
        - from (str): Sender identifier (email, name, username)
        - subject (str, optional): Message subject (email only)
        - content (str): Full message text
        - received (str): ISO-8601 timestamp
        - priority (str): "high" | "medium" | "low"
        - metadata (dict): Channel-specific metadata

    Raises:
        AuthenticationError: If credentials are invalid or expired
        RateLimitError: If channel rate limit exceeded
        NetworkError: If network connection fails

    Contract Requirements:
        - Must return empty list if no new messages
        - Must deduplicate messages (track last_message_id)
        - Must handle authentication errors gracefully
        - Must respect rate limits (check_interval >= 300 seconds)
        - Must not raise exceptions for transient errors (return empty list)
    """
```

**Expected Behavior**:
- Check channel for new messages since last check
- Filter out already-processed messages using `last_message_id`
- Extract required fields from channel-specific format
- Determine priority based on channel rules (e.g., Gmail "important" label)
- Return structured list of message dictionaries
- Log all checks to audit log with timestamp and result

**Error Handling**:
- Authentication errors: Log error, notify user, return empty list
- Rate limit errors: Log warning, increase check_interval temporarily, return empty list
- Network errors: Log error, retry with exponential backoff (max 3 attempts), return empty list
- Parsing errors: Log error with message details, skip malformed message, continue processing

---

### 2. create_action_file()

```python
@abstractmethod
def create_action_file(self, item: Dict[str, Any]) -> Path:
    """
    Create a markdown file in Needs_Action folder for the message.

    Args:
        item: Message dictionary from check_for_updates()

    Returns:
        Path to created action file

    Raises:
        FileExistsError: If action file already exists (duplicate)
        PermissionError: If cannot write to Needs_Action folder
        ValueError: If item is missing required fields

    Contract Requirements:
        - File must be created in self.needs_action directory
        - Filename format: MESSAGE_{channel}_{message_id}.md
        - Must include YAML frontmatter with all required fields
        - Must include message content in markdown body
        - Must create wikilinks to Dashboard and relevant entities
        - Must add appropriate tags based on content
        - Must be atomic (write to temp file, then rename)
    """
```

**Expected Behavior**:
- Validate item has all required fields
- Generate unique filename: `MESSAGE_{channel}_{message_id}.md`
- Create YAML frontmatter with metadata
- Format message content as markdown
- Add suggested actions as checkboxes
- Create wikilinks to Dashboard and related files
- Write atomically (temp file + rename to avoid corruption)
- Update `last_message_id` in watcher config
- Log file creation to audit log

**File Format**:
```yaml
---
type: message
channel: gmail|whatsapp|linkedin
message_id: "unique_id"
from: "sender@example.com"
subject: "Subject line" or null
received: "2026-01-13T10:30:00Z"
priority: high|medium|low
status: pending
tags: [email, important, business]
wikilinks: ["[[Dashboard]]"]
---

## Message Content

[Full message text]

## Context

- **Channel**: Gmail
- **Thread ID**: thread_xyz

## Suggested Actions

- [ ] Reply to sender
- [ ] Create task
```

---

### 3. run()

```python
def run(self):
    """
    Main watcher loop - checks for updates at configured interval.

    Contract Requirements:
        - Must run indefinitely until interrupted
        - Must check for updates every check_interval seconds
        - Must handle all exceptions gracefully (log and continue)
        - Must respect SIGTERM for graceful shutdown
        - Must log all executions to audit log
        - Must update last_check timestamp after each cycle
    """
```

**Expected Behavior**:
- Log startup message with watcher name and configuration
- Enter infinite loop:
  1. Call `check_for_updates()`
  2. For each message, call `create_action_file()`
  3. Update `last_check` timestamp in config
  4. Log execution result (success/failure, message count)
  5. Sleep for `check_interval` seconds
- Handle SIGTERM gracefully (finish current cycle, then exit)
- Continue running even after errors (per spec FR-034)

**Error Handling**:
- Catch all exceptions in main loop
- Log error with full traceback
- Continue to next cycle (don't crash)
- Implement exponential backoff if repeated failures

---

## Channel-Specific Implementations

### GmailWatcher

**Additional Methods**:
```python
def authenticate(self) -> Credentials:
    """Authenticate with Gmail API using OAuth2."""

def refresh_token(self) -> Credentials:
    """Refresh expired OAuth2 token."""

def build_query(self) -> str:
    """Build Gmail API query string (e.g., 'is:unread is:important')."""
```

**Configuration**:
```yaml
type: gmail
config:
  query: "is:unread is:important"
  max_results: 10
  credentials_path: ".env"  # OAuth2 tokens
```

---

### WhatsAppWatcher

**Additional Methods**:
```python
def init_browser(self) -> Browser:
    """Initialize Playwright browser with persistent session."""

def scan_qr_code(self) -> bool:
    """Wait for user to scan QR code (first-time setup)."""

def extract_messages(self, page: Page) -> List[Dict]:
    """Extract messages from WhatsApp Web DOM."""
```

**Configuration**:
```yaml
type: whatsapp
config:
  session_path: "/path/to/session"
  urgent_keywords: ["urgent", "asap", "important"]
  headless: true
```

---

### LinkedInWatcher

**Additional Methods**:
```python
def authenticate(self) -> Session:
    """Authenticate with LinkedIn API or unofficial library."""

def get_messages(self) -> List[Dict]:
    """Fetch unread messages from LinkedIn."""

def get_notifications(self) -> List[Dict]:
    """Fetch unread notifications from LinkedIn."""
```

**Configuration**:
```yaml
type: linkedin
config:
  check_messages: true
  check_notifications: false
  credentials_path: ".env"  # API keys
```

---

## Error Types

```python
class WatcherError(Exception):
    """Base exception for watcher errors."""

class AuthenticationError(WatcherError):
    """Raised when authentication fails or credentials expire."""

class RateLimitError(WatcherError):
    """Raised when channel rate limit is exceeded."""

class NetworkError(WatcherError):
    """Raised when network connection fails."""

class ParsingError(WatcherError):
    """Raised when message parsing fails."""
```

---

## Testing Contract

All watcher implementations must pass these tests:

1. **Unit Tests**:
   - `test_check_for_updates_returns_list()`
   - `test_check_for_updates_deduplicates()`
   - `test_create_action_file_format()`
   - `test_create_action_file_atomic()`
   - `test_run_handles_errors()`

2. **Integration Tests**:
   - `test_end_to_end_message_detection()`
   - `test_authentication_failure_recovery()`
   - `test_rate_limit_handling()`
   - `test_graceful_shutdown()`

3. **Performance Tests**:
   - Check cycle completes within check_interval
   - Memory usage remains stable over 24 hours
   - No resource leaks (file handles, network connections)

---

## Logging Contract

All watchers must log to audit log with this format:

```json
{
  "timestamp": "2026-01-13T10:30:45.123Z",
  "action_type": "watcher_check",
  "actor": "gmail_watcher",
  "target": "Gmail API",
  "parameters": {
    "query": "is:unread is:important",
    "check_interval": 300
  },
  "result": "success",
  "execution_time_ms": 1234,
  "messages_found": 3,
  "error": null
}
```

---

## Configuration Contract

All watchers must read configuration from `silver/config/watcher_config.yaml`:

```yaml
watchers:
  - id: gmail-watcher
    type: gmail
    enabled: true
    check_interval: 300
    config:
      # Watcher-specific config
```

**Required Fields**:
- `id`: Unique identifier
- `type`: Watcher type (gmail, whatsapp, linkedin)
- `enabled`: Boolean flag
- `check_interval`: Seconds between checks (>= 300)
- `config`: Watcher-specific configuration

---

**Contract Status**: ✅ Complete
**Implementations Required**: GmailWatcher, WhatsAppWatcher, LinkedInWatcher

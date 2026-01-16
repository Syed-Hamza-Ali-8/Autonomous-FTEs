# Monitor Communications Skill

**Skill ID**: monitor-communications
**Version**: 1.0.0
**User Story**: US1 - Multi-Channel Communication Monitoring
**Priority**: P1 (MVP)

## Purpose

Monitor Gmail and WhatsApp channels for new messages and create action files in the Needs_Action folder for AI processing. This skill implements the **Perception** phase of the Perception → Reasoning → Action architecture.

## Capabilities

- **Gmail Monitoring**: Monitor Gmail inbox using Gmail API with OAuth2 authentication
- **WhatsApp Monitoring**: Monitor WhatsApp Web using Playwright browser automation
- **Action File Creation**: Create structured markdown files with YAML frontmatter in Needs_Action folder
- **Deduplication**: Track processed messages to prevent duplicate action files
- **Error Recovery**: Handle authentication failures, rate limits, and network interruptions gracefully

## Architecture

### BaseWatcher Pattern

All watchers inherit from `BaseWatcher` abstract class:

```python
class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60)

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path

    def run(self)
```

### Channel-Specific Watchers

1. **GmailWatcher** (`silver/src/watchers/gmail_watcher.py`)
   - Uses Gmail API with OAuth2
   - Checks for unread messages in INBOX
   - Rate limit: 200,000 emails/day (free tier)
   - Check interval: 5 minutes

2. **WhatsAppWatcher** (`silver/src/watchers/whatsapp_watcher.py`)
   - Uses Playwright for WhatsApp Web automation
   - Requires QR code scan for initial authentication
   - Session persistence via browser cookies
   - Check interval: 5 minutes

## Configuration

### Watcher Config (`silver/config/watcher_config.yaml`)

```yaml
gmail:
  enabled: true
  check_interval: 300  # 5 minutes
  credentials_path: "silver/config/.env"
  filters:
    - "is:unread"
    - "in:inbox"

whatsapp:
  enabled: true
  check_interval: 300  # 5 minutes
  session_path: "silver/config/whatsapp_session"
  headless: true
```

### Environment Variables (`.env`)

```bash
# Gmail API
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# WhatsApp (session stored in browser profile)
WHATSAPP_SESSION_PATH=./silver/config/whatsapp_session
```

## Usage

### Start All Watchers

```bash
cd silver
python -m src.watchers.gmail_watcher &
python -m src.watchers.whatsapp_watcher &
```

Or use the startup script:

```bash
./silver/scripts/start_watchers.sh
```

### Test Individual Watchers

```bash
# Test Gmail watcher
python silver/scripts/test_watchers.sh gmail

# Test WhatsApp watcher
python silver/scripts/test_watchers.sh whatsapp
```

## Output Format

### Action File Structure

Created in `Needs_Action/` folder:

```markdown
---
id: msg_gmail_1234567890
source: gmail
channel: email
sender: john@example.com
subject: "Project Update"
timestamp: 2026-01-13T10:30:00Z
status: pending
priority: normal
---

# Message from john@example.com

**Subject**: Project Update

**Received**: 2026-01-13 10:30 AM

## Content

[Message body here...]

## Suggested Actions

- [ ] Reply to sender
- [ ] Add to task list
- [ ] File in appropriate folder
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
google-auth = "^2.27.0"
google-auth-oauthlib = "^1.2.0"
google-api-python-client = "^2.115.0"
playwright = "^1.40.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

### System Requirements

- Python 3.13+
- Node.js (for Playwright browser binaries)
- Internet connection
- Gmail account with API access enabled
- WhatsApp account with WhatsApp Web access

## Setup Instructions

### 1. Gmail API Setup

```bash
# Run interactive setup
python silver/scripts/setup_gmail.py

# Follow OAuth2 flow in browser
# Credentials saved to silver/config/.env
```

### 2. WhatsApp Web Setup

```bash
# Run interactive setup
python silver/scripts/setup_whatsapp.py

# Scan QR code with WhatsApp mobile app
# Session saved to silver/config/whatsapp_session/
```

### 3. Verify Setup

```bash
# Test both watchers
./silver/scripts/test_watchers.sh all
```

## Error Handling

### Gmail Errors

- **401 Unauthorized**: Refresh OAuth2 token automatically
- **429 Rate Limit**: Exponential backoff (2s, 4s, 8s)
- **Network Error**: Retry up to 3 times, then log and continue

### WhatsApp Errors

- **Session Expired**: Notify user to re-scan QR code
- **Element Not Found**: Update selectors (see references/whatsapp_selectors.md)
- **Browser Crash**: Restart browser and restore session

## Performance

- **Gmail**: ~2-3 seconds per check (API call)
- **WhatsApp**: ~5-10 seconds per check (browser automation)
- **Memory**: ~50MB per watcher (Gmail), ~200MB per watcher (WhatsApp with browser)
- **CPU**: Minimal (<5% on modern systems)

## Testing

### Unit Tests

```bash
pytest silver/tests/unit/test_gmail_watcher.py
pytest silver/tests/unit/test_whatsapp_watcher.py
```

### Integration Tests

```bash
pytest silver/tests/integration/test_watchers.py
```

### Manual Testing

1. Send test email to monitored Gmail account
2. Send test WhatsApp message to monitored account
3. Verify action files created in Needs_Action/ within 5 minutes
4. Verify YAML frontmatter is valid
5. Verify message content is extracted correctly

## Success Criteria

- ✅ 95% message detection rate across both channels
- ✅ Action files created within 5 minutes of message receipt
- ✅ No duplicate action files for same message
- ✅ Graceful handling of authentication failures
- ✅ Continuous operation for 7+ days without manual intervention

## Related Skills

- **manage-approvals**: Processes action files created by this skill
- **execute-actions**: Executes approved actions (e.g., send reply email)

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Playwright Documentation](https://playwright.dev/python/)
- See `references/gmail_api_docs.md` for detailed API reference
- See `references/whatsapp_selectors.md` for WhatsApp Web selectors

## Examples

- See `examples/gmail_message_example.json` for Gmail API response format
- See `examples/whatsapp_message_example.json` for WhatsApp message structure
- See `examples/action_file_example.md` for output action file format

## Changelog

- **1.0.0** (2026-01-13): Initial implementation for Silver tier MVP

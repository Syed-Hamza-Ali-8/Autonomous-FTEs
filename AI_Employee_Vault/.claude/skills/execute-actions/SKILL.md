# Execute Actions Skill

**Skill ID**: execute-actions
**Version**: 1.0.0
**User Story**: US5 - External Action Execution
**Priority**: P3

## Purpose

Execute approved actions through external services, primarily via the MCP (Model Context Protocol) email server. This skill implements the **Action** phase of the Perception → Reasoning → Action architecture, ensuring all external actions are executed reliably with retry logic and comprehensive error handling.

## Capabilities

- **Email Sending**: Send emails via SMTP through MCP server
- **Action Execution**: Execute approved actions from Approved/ folder
- **Retry Logic**: Exponential backoff for failed actions (max 3 retries)
- **Error Handling**: Graceful handling of network failures, SMTP errors, rate limits
- **Audit Logging**: Log all action attempts and results
- **Status Tracking**: Track action execution status and results

## Architecture

### Core Components

1. **ActionExecutor** (`silver/src/actions/action_executor.py`)
   - `execute_action(action_id)` → result
   - `retry_failed_action(action_id)` → result
   - `get_action_status(action_id)` → status

2. **EmailSender** (`silver/src/actions/email_sender.py`)
   - `send_email(to, subject, body, attachments)` → message_id
   - `validate_email(email_address)` → bool
   - `connect_to_mcp()` → connection

3. **MCP Email Server** (`silver/mcp/email-server/index.js`)
   - Node.js server implementing MCP protocol
   - `send-email` endpoint with retry logic
   - SMTP integration with Nodemailer
   - Error handling and validation

### Execution Workflow

```
1. Approved Action Detected → Load action details from Approved/ folder
                            → Validate action parameters
                            → Execute via appropriate handler

2. Email Action → Connect to MCP server
               → Send email via send-email endpoint
               → Handle response (success/failure)
               → Retry if failed (max 3 attempts, exponential backoff)

3. Result Handling → Success: Update action file, move to Done/
                   → Failure: Log error, notify user, keep in Approved/
                   → Audit: Log all attempts to audit log
```

## Configuration

### MCP Server Config (`silver/mcp/email-server/.env`)

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false  # true for 465, false for other ports
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# MCP Server Configuration
MCP_PORT=3000
MCP_HOST=localhost

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAYS=2000,4000,8000  # milliseconds (2s, 4s, 8s)

# Rate Limiting
RATE_LIMIT_WINDOW=60000  # 1 minute
RATE_LIMIT_MAX_REQUESTS=10
```

### Action Executor Config (`silver/config/action_config.yaml`)

```yaml
email:
  mcp_server_url: "http://localhost:3000"
  timeout_seconds: 30
  max_retries: 3
  retry_delays: [2, 4, 8]  # seconds
  validate_recipients: true
  max_recipients: 50

logging:
  audit_log_path: "Logs/"
  log_level: "INFO"
  log_format: "json"

error_handling:
  notify_on_failure: true
  max_consecutive_failures: 5
  failure_cooldown_minutes: 15
```

## Usage

### Execute Approved Email Action

```python
from silver.src.actions.action_executor import ActionExecutor

executor = ActionExecutor(vault_path="/path/to/vault")

# Execute action by ID
result = executor.execute_action(action_id="approval_20260113_103045_abc123")

if result["success"]:
    print(f"Email sent successfully: {result['message_id']}")
    print(f"Sent to: {result['recipients']}")
else:
    print(f"Email failed: {result['error']}")
    print(f"Retry count: {result['retry_count']}")
```

### Send Email Directly (for testing)

```python
from silver.src.actions.email_sender import EmailSender

sender = EmailSender(mcp_server_url="http://localhost:3000")

# Send email
result = sender.send_email(
    to="recipient@example.com",
    subject="Test Email",
    body="This is a test email from AI Employee Vault",
    attachments=[]
)

if result["success"]:
    print(f"Message ID: {result['message_id']}")
else:
    print(f"Error: {result['error']}")
```

### Start MCP Email Server

```bash
# Navigate to MCP server directory
cd silver/mcp/email-server

# Install dependencies
npm install

# Start server
npm start

# Or use PM2 for production
pm2 start index.js --name "mcp-email-server"
```

## Output Format

### Successful Execution

Action file updated in `Done/` folder:

```yaml
---
id: approval_20260113_103045_abc123
action_type: send_email
status: completed
created_at: 2026-01-13T10:30:45Z
approved_at: 2026-01-13T10:35:12Z
executed_at: 2026-01-13T10:35:15Z
execution_result: success
message_id: <abc123xyz@smtp.gmail.com>
retry_count: 0
---
```

### Failed Execution

Action file remains in `Approved/` folder with error details:

```yaml
---
id: approval_20260113_103045_abc123
action_type: send_email
status: failed
created_at: 2026-01-13T10:30:45Z
approved_at: 2026-01-13T10:35:12Z
last_attempt_at: 2026-01-13T10:35:30Z
execution_result: failed
error: "SMTP connection timeout after 30 seconds"
retry_count: 3
next_retry_at: 2026-01-13T10:50:30Z
---
```

### Audit Log Entry

Logged in `Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-01-13T10:35:15Z",
  "action_id": "approval_20260113_103045_abc123",
  "action_type": "send_email",
  "status": "success",
  "message_id": "<abc123xyz@smtp.gmail.com>",
  "recipients": ["client@example.com"],
  "retry_count": 0,
  "execution_time_ms": 1234,
  "mcp_server": "http://localhost:3000"
}
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
requests = "^2.31.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

### Node.js Packages (MCP Server)

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "nodemailer": "^6.9.8",
    "express": "^4.18.2",
    "dotenv": "^16.3.1",
    "express-rate-limit": "^7.1.5"
  }
}
```

### System Requirements

- Python 3.13+
- Node.js v24+ LTS
- SMTP server access (Gmail, SendGrid, etc.)
- Internet connection

## Setup Instructions

### 1. Configure SMTP Credentials

```bash
# Create .env file for MCP server
cd silver/mcp/email-server
cp .env.example .env

# Edit .env with your SMTP credentials
nano .env

# For Gmail: Use App Password (not regular password)
# https://support.google.com/accounts/answer/185833
```

### 2. Install MCP Server Dependencies

```bash
cd silver/mcp/email-server
npm install
```

### 3. Test SMTP Connection

```bash
# Test SMTP connection
python silver/scripts/test_smtp.py

# Should output: ✅ SMTP connection successful
```

### 4. Start MCP Server

```bash
# Development mode
cd silver/mcp/email-server
npm start

# Production mode with PM2
pm2 start index.js --name "mcp-email-server"
pm2 save
pm2 startup
```

### 5. Test MCP Server

```bash
# Test MCP server endpoints
python silver/scripts/test_mcp.py

# Should output: ✅ MCP server responding correctly
```

### 6. Verify End-to-End

```bash
# Create test approval request
python silver/scripts/test_approval.py --create-email-test

# Approve the request (edit file in Pending_Approval/)

# Execute action
python -m silver.src.actions.action_executor

# Check Done/ folder for completed action
```

## Error Handling

### SMTP Errors

- **535 Authentication Failed**: Check SMTP credentials, use App Password for Gmail
- **550 Recipient Rejected**: Verify recipient email address is valid
- **552 Message Size Exceeded**: Reduce email size or attachments
- **554 Transaction Failed**: Check SMTP server logs, may be rate limited

### MCP Server Errors

- **Connection Refused**: MCP server not running, start with `npm start`
- **Timeout**: MCP server overloaded, check server logs
- **500 Internal Server Error**: Check MCP server logs for details

### Retry Logic

```python
# Exponential backoff: 2s, 4s, 8s
retry_delays = [2, 4, 8]  # seconds

for attempt in range(max_retries):
    try:
        result = send_email(...)
        if result["success"]:
            break
    except Exception as e:
        if attempt < max_retries - 1:
            delay = retry_delays[attempt]
            time.sleep(delay)
        else:
            # Max retries reached, log failure
            log_failure(action_id, error=str(e))
```

## Performance

- **Email Sending**: ~1-3 seconds per email (SMTP latency)
- **MCP Server**: ~50ms overhead per request
- **Retry Logic**: 2s + 4s + 8s = 14s total for 3 retries
- **Memory**: ~30MB per executor process, ~50MB for MCP server
- **CPU**: Minimal (<5% on modern systems)

## Testing

### Unit Tests

```bash
pytest silver/tests/unit/test_action_executor.py
pytest silver/tests/unit/test_email_sender.py
```

### Integration Tests

```bash
pytest silver/tests/integration/test_mcp_integration.py
```

### Manual Testing

1. **Test SMTP Connection**:
   ```bash
   python silver/scripts/test_smtp.py
   ```

2. **Test MCP Server**:
   ```bash
   curl -X POST http://localhost:3000/send-email \
     -H "Content-Type: application/json" \
     -d '{"to":"test@example.com","subject":"Test","body":"Test"}'
   ```

3. **Test End-to-End**:
   - Create approval request
   - Approve request
   - Execute action
   - Verify email received
   - Check audit log

## Success Criteria

- ✅ 80% first-attempt success rate for email sending
- ✅ Retry logic works correctly (exponential backoff)
- ✅ All execution attempts logged in audit log
- ✅ Failed actions remain in Approved/ with error details
- ✅ Successful actions moved to Done/ with message ID
- ✅ MCP server handles 10+ concurrent requests
- ✅ Graceful handling of SMTP errors and rate limits

## Related Skills

- **manage-approvals**: Provides approved actions for execution
- **monitor-communications**: May trigger actions (e.g., auto-reply)
- **create-plans**: Plans may include actions requiring execution

## References

- See `references/mcp_api_docs.md` for MCP server API specification
- See `references/retry_logic.md` for retry strategy details
- See `references/smtp_configuration.md` for SMTP setup guide

## Examples

- See `examples/email_action_example.json` for email action format
- See `examples/successful_execution.md` for successful execution result
- See `examples/failed_execution.md` for failed execution with retry

## Changelog

- **1.0.0** (2026-01-13): Initial implementation for Silver tier

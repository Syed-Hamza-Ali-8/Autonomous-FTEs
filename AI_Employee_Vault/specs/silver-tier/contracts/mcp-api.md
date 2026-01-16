# MCP Server API Contract

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Purpose**: Define the interface contract for Model Context Protocol (MCP) server for external action execution

## Overview

The MCP server provides a standardized interface for executing external actions (email sending, calendar events, etc.) with proper authentication, error handling, and retry logic. This contract defines the server implementation requirements and client interaction patterns.

---

## Server Implementation

### Email MCP Server

**Technology**: Node.js v24+ LTS with @modelcontextprotocol/sdk and nodemailer

**Location**: `silver/mcp/email-server/`

**Entry Point**: `index.js`

---

## MCP Protocol Endpoints

### 1. send-email

```typescript
interface SendEmailRequest {
  to: string | string[];
  subject: string;
  body: string;
  from?: string;
  cc?: string | string[];
  bcc?: string | string[];
  attachments?: Attachment[];
  replyTo?: string;
}

interface Attachment {
  filename: string;
  content: string;  // Base64 encoded
  contentType: string;
}

interface SendEmailResponse {
  success: boolean;
  messageId?: string;
  error?: string;
  timestamp: string;
}
```

**Contract Requirements**:
- Must validate all required fields (to, subject, body)
- Must validate email addresses using RFC 5322 format
- Must support single recipient or array of recipients
- Must support CC and BCC fields
- Must support file attachments (Base64 encoded)
- Must return unique messageId on success
- Must return detailed error message on failure
- Must log all send attempts to audit log
- Must implement rate limiting (configurable per provider)

**Expected Behavior**:
- Validate request parameters
- Connect to SMTP server using configured credentials
- Send email via nodemailer
- Return messageId from SMTP server
- Log success/failure to audit log
- Handle SMTP errors gracefully (connection timeout, auth failure, etc.)

**Error Handling**:
- Invalid email address: Return error with details
- SMTP connection failure: Retry with exponential backoff (max 3 attempts)
- Authentication failure: Return error, don't retry (credentials issue)
- Rate limit exceeded: Return error with retry-after timestamp
- Attachment too large: Return error with size limit

---

### 2. get-email-status

```typescript
interface GetEmailStatusRequest {
  messageId: string;
}

interface GetEmailStatusResponse {
  messageId: string;
  status: "sent" | "delivered" | "bounced" | "failed";
  timestamp: string;
  error?: string;
}
```

**Contract Requirements**:
- Must track email delivery status (if provider supports it)
- Must return current status for given messageId
- Must handle unknown messageId gracefully
- Must cache status for performance

**Expected Behavior**:
- Look up messageId in status cache
- If not found, query email provider (if supported)
- Return current status
- Update cache with latest status

---

### 3. validate-email

```typescript
interface ValidateEmailRequest {
  email: string;
}

interface ValidateEmailResponse {
  valid: boolean;
  reason?: string;
}
```

**Contract Requirements**:
- Must validate email format using RFC 5322
- Must check for common typos (e.g., @gmial.com)
- Must not perform DNS lookup (privacy concern)
- Must return validation result with reason if invalid

**Expected Behavior**:
- Parse email address
- Validate format (local@domain)
- Check for common typos in popular domains
- Return validation result

---

## Configuration

MCP server configuration in `silver/mcp/email-server/.env`:

```env
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Rate Limiting
RATE_LIMIT_PER_HOUR=100
RATE_LIMIT_PER_DAY=500

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY_MS=2000
RETRY_BACKOFF_MULTIPLIER=2

# Logging
LOG_LEVEL=info
LOG_FILE=/path/to/vault/Logs/mcp-email.log
```

**Required Fields**:
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP server port (587 for TLS, 465 for SSL)
- `SMTP_SECURE`: Use SSL (true) or TLS (false)
- `SMTP_USER`: SMTP username (usually email address)
- `SMTP_PASS`: SMTP password or app-specific password

**Optional Fields**:
- `RATE_LIMIT_PER_HOUR`: Max emails per hour (default: 100)
- `RATE_LIMIT_PER_DAY`: Max emails per day (default: 500)
- `MAX_RETRIES`: Max retry attempts (default: 3)
- `RETRY_DELAY_MS`: Initial retry delay (default: 2000ms)
- `RETRY_BACKOFF_MULTIPLIER`: Backoff multiplier (default: 2)

---

## Server Lifecycle

### Startup

```javascript
async function startServer() {
  // 1. Load configuration from .env
  // 2. Validate SMTP credentials
  // 3. Initialize MCP server
  // 4. Register endpoints (send-email, get-email-status, validate-email)
  // 5. Start listening on configured port
  // 6. Log startup message
}
```

**Contract Requirements**:
- Must validate configuration before starting
- Must test SMTP connection on startup
- Must fail fast if configuration is invalid
- Must log startup success/failure
- Must handle SIGTERM for graceful shutdown

---

### Shutdown

```javascript
async function shutdownServer() {
  // 1. Stop accepting new requests
  // 2. Wait for in-flight requests to complete (max 30 seconds)
  // 3. Close SMTP connections
  // 4. Flush logs
  // 5. Exit cleanly
}
```

**Contract Requirements**:
- Must handle SIGTERM signal
- Must complete in-flight requests before exiting
- Must close all connections cleanly
- Must flush all logs before exit
- Must exit with code 0 on clean shutdown

---

## Client Integration

### Python Client

```python
import requests
import json

class MCPEmailClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = requests.Session()

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        **kwargs
    ) -> dict:
        """
        Send email via MCP server.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body (plain text or HTML)
            **kwargs: Optional fields (cc, bcc, attachments, etc.)

        Returns:
            Response dictionary with success, messageId, error

        Raises:
            MCPError: If MCP server returns error
            NetworkError: If cannot connect to MCP server
        """
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
            **kwargs
        }

        try:
            response = self.session.post(
                f"{self.server_url}/send-email",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"MCP server error: {e}")

    def validate_email(self, email: str) -> bool:
        """Validate email address format."""
        response = self.session.post(
            f"{self.server_url}/validate-email",
            json={"email": email},
            timeout=5
        )
        return response.json()["valid"]
```

**Contract Requirements**:
- Must use requests library for HTTP communication
- Must set reasonable timeouts (30s for send, 5s for validate)
- Must handle network errors gracefully
- Must retry on transient errors (connection timeout, 5xx errors)
- Must not retry on client errors (4xx errors)
- Must log all MCP calls to audit log

---

## Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  success: false;
  error: string;
  errorCode: string;
  timestamp: string;
  retryable: boolean;
}
```

**Error Codes**:
- `INVALID_REQUEST`: Missing or invalid parameters (4xx)
- `AUTH_FAILED`: SMTP authentication failed (4xx)
- `RATE_LIMIT_EXCEEDED`: Too many requests (429)
- `SMTP_ERROR`: SMTP server error (5xx)
- `NETWORK_ERROR`: Network connection failed (5xx)
- `INTERNAL_ERROR`: Server internal error (5xx)

**Retryable Errors**:
- `SMTP_ERROR`: Yes (transient SMTP issues)
- `NETWORK_ERROR`: Yes (network interruption)
- `RATE_LIMIT_EXCEEDED`: Yes (after delay)
- `AUTH_FAILED`: No (credentials issue)
- `INVALID_REQUEST`: No (client error)

---

## Retry Logic

### Exponential Backoff

```javascript
async function sendWithRetry(emailData, maxRetries = 3) {
  let attempt = 0;
  let delay = 2000; // 2 seconds

  while (attempt < maxRetries) {
    try {
      const result = await sendEmail(emailData);
      return result;
    } catch (error) {
      attempt++;

      if (!isRetryable(error) || attempt >= maxRetries) {
        throw error;
      }

      await sleep(delay);
      delay *= 2; // Exponential backoff
    }
  }
}
```

**Contract Requirements**:
- Must implement exponential backoff (2s, 4s, 8s)
- Must respect max retries (3 per spec FR-031)
- Must only retry on retryable errors
- Must log each retry attempt
- Must return final error if all retries fail

---

## Security

### Authentication

**MCP Server Authentication**:
- Server runs locally (localhost only)
- No authentication required (local-first architecture)
- Future: Add API key authentication if exposed to network

**SMTP Authentication**:
- Use app-specific passwords (not account password)
- Store credentials in .env file (gitignored)
- Rotate credentials monthly
- Never log credentials

### Input Validation

**Email Address Validation**:
- Validate format using RFC 5322
- Sanitize input to prevent injection
- Check for suspicious patterns (e.g., multiple @)
- Reject invalid addresses before sending

**Content Validation**:
- Sanitize HTML content to prevent XSS
- Validate attachment sizes (max 25MB per Gmail)
- Check attachment types (block executables)
- Validate total message size

---

## Logging

### Audit Log Format

```json
{
  "timestamp": "2026-01-13T10:30:45.123Z",
  "action_type": "email_send",
  "actor": "mcp_server",
  "target": "client@example.com",
  "parameters": {
    "subject": "Re: Project Update",
    "approval_request_id": "req_20260113_103045_abc",
    "messageId": "abc123@smtp.gmail.com"
  },
  "result": "success",
  "execution_time_ms": 1234,
  "retry_count": 0,
  "error": null
}
```

**Contract Requirements**:
- Log all send attempts (success and failure)
- Include messageId for tracking
- Include retry count
- Include execution time
- Mask sensitive data (passwords, tokens)
- Write to vault Logs/ directory

---

## Testing Contract

### Unit Tests

```javascript
describe('MCP Email Server', () => {
  test('send-email validates required fields', async () => {
    const response = await sendEmail({});
    expect(response.success).toBe(false);
    expect(response.errorCode).toBe('INVALID_REQUEST');
  });

  test('send-email validates email format', async () => {
    const response = await sendEmail({
      to: 'invalid-email',
      subject: 'Test',
      body: 'Test'
    });
    expect(response.success).toBe(false);
  });

  test('send-email succeeds with valid input', async () => {
    const response = await sendEmail({
      to: 'test@example.com',
      subject: 'Test',
      body: 'Test'
    });
    expect(response.success).toBe(true);
    expect(response.messageId).toBeDefined();
  });
});
```

### Integration Tests

```javascript
describe('MCP Email Server Integration', () => {
  test('end-to-end email sending', async () => {
    // 1. Start MCP server
    // 2. Send email via client
    // 3. Verify email received (test account)
    // 4. Check audit log entry
    // 5. Shutdown server
  });

  test('retry on transient failure', async () => {
    // 1. Mock SMTP server with transient failure
    // 2. Send email
    // 3. Verify retry attempts
    // 4. Verify eventual success
  });
});
```

---

## Deployment

### Process Management

**Using PM2** (cross-platform):
```bash
pm2 start silver/mcp/email-server/index.js --name mcp-email
pm2 save
pm2 startup
```

**Using systemd** (Linux):
```ini
[Unit]
Description=MCP Email Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/vault/silver/mcp/email-server
ExecStart=/usr/bin/node index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Contract Requirements**:
- Must auto-restart on failure
- Must start on system boot
- Must log to system journal or file
- Must run as non-root user

---

## Performance Requirements

- **Latency**: Email send completes within 5 seconds (90th percentile)
- **Throughput**: Support 100 emails per hour
- **Memory**: Use < 100MB RAM
- **CPU**: Use < 5% CPU when idle
- **Startup**: Start within 2 seconds
- **Shutdown**: Graceful shutdown within 30 seconds

---

**Contract Status**: ✅ Complete
**Implementation Required**: Node.js MCP server with nodemailer

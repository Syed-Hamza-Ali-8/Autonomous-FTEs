# MCP Email Server API Documentation

## Overview

The MCP (Model Context Protocol) Email Server is a Node.js server that provides email sending capabilities through a standardized API. It implements the MCP protocol for integration with Claude Code and other AI systems.

## Server Information

- **Protocol**: HTTP/JSON
- **Default Port**: 3000
- **Base URL**: `http://localhost:3000`
- **Authentication**: None (local server, trusted environment)

## API Endpoints

### 1. Send Email

**Endpoint**: `POST /send-email`

**Description**: Send an email via SMTP with retry logic and error handling.

**Request Body**:
```json
{
  "to": "string | string[]",
  "subject": "string",
  "body": "string",
  "from": "string (optional)",
  "cc": "string | string[] (optional)",
  "bcc": "string | string[] (optional)",
  "attachments": "array (optional)"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "messageId": "<abc123xyz@smtp.gmail.com>",
  "timestamp": "2026-01-13T10:35:15Z",
  "recipients": ["recipient@example.com"],
  "retryCount": 0
}
```

**Response (Failure)**:
```json
{
  "success": false,
  "error": "SMTP connection timeout",
  "errorCode": "ETIMEDOUT",
  "timestamp": "2026-01-13T10:35:15Z",
  "retryCount": 3
}
```

**Status Codes**:
- `200 OK`: Email sent successfully
- `400 Bad Request`: Invalid request parameters
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: SMTP error or server error
- `503 Service Unavailable`: SMTP server unavailable

### 2. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the MCP server is running and SMTP connection is available.

**Response**:
```json
{
  "status": "healthy",
  "smtp": {
    "connected": true,
    "host": "smtp.gmail.com",
    "port": 587
  },
  "uptime": 3600,
  "timestamp": "2026-01-13T10:35:15Z"
}
```

### 3. Server Info

**Endpoint**: `GET /info`

**Description**: Get server configuration and capabilities.

**Response**:
```json
{
  "version": "1.0.0",
  "protocol": "MCP",
  "capabilities": ["send-email"],
  "rateLimit": {
    "window": 60000,
    "maxRequests": 10
  },
  "retryConfig": {
    "maxRetries": 3,
    "delays": [2000, 4000, 8000]
  }
}
```

## Request Validation

### Email Address Validation

Email addresses are validated using RFC 5322 format:

```javascript
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateEmail(email) {
  return emailRegex.test(email);
}
```

**Valid Examples**:
- `user@example.com`
- `john.doe@company.co.uk`
- `support+tag@service.com`

**Invalid Examples**:
- `invalid.email` (no @)
- `@example.com` (no local part)
- `user@` (no domain)

### Request Size Limits

- **Maximum recipients**: 50 (to + cc + bcc combined)
- **Maximum subject length**: 998 characters (RFC 5322)
- **Maximum body size**: 10 MB
- **Maximum attachment size**: 25 MB total

## Retry Logic

### Retry Strategy

The MCP server implements exponential backoff for failed SMTP operations:

```javascript
const retryDelays = [2000, 4000, 8000]; // milliseconds
const maxRetries = 3;

async function sendEmailWithRetry(emailData) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const result = await sendEmail(emailData);
      return { success: true, ...result, retryCount: attempt };
    } catch (error) {
      if (attempt < maxRetries - 1) {
        await sleep(retryDelays[attempt]);
      } else {
        return { success: false, error: error.message, retryCount: attempt + 1 };
      }
    }
  }
}
```

### Retryable Errors

The following errors trigger automatic retry:
- `ETIMEDOUT`: Connection timeout
- `ECONNREFUSED`: Connection refused
- `ENOTFOUND`: DNS lookup failed
- `ECONNRESET`: Connection reset by peer
- `EPIPE`: Broken pipe

### Non-Retryable Errors

The following errors do NOT trigger retry:
- `535`: Authentication failed (invalid credentials)
- `550`: Recipient rejected (invalid email address)
- `552`: Message size exceeded
- `554`: Transaction failed (permanent failure)

## Rate Limiting

### Configuration

```javascript
const rateLimit = {
  windowMs: 60000,        // 1 minute
  maxRequests: 10,        // 10 requests per window
  message: "Too many requests, please try again later"
};
```

### Rate Limit Headers

Response includes rate limit headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705167045000
```

### Rate Limit Response

When rate limit is exceeded:

```json
{
  "success": false,
  "error": "Too many requests, please try again later",
  "retryAfter": 45000
}
```

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "errorCode": "MACHINE_READABLE_CODE",
  "timestamp": "2026-01-13T10:35:15Z",
  "details": {
    "field": "to",
    "reason": "Invalid email address"
  }
}
```

### Common Error Codes

- `INVALID_EMAIL`: Email address validation failed
- `INVALID_REQUEST`: Missing required fields
- `SMTP_ERROR`: SMTP server error
- `ETIMEDOUT`: Connection timeout
- `EAUTH`: Authentication failed
- `RATE_LIMIT`: Rate limit exceeded

## SMTP Configuration

### Supported SMTP Servers

- **Gmail**: smtp.gmail.com:587 (TLS)
- **Outlook**: smtp-mail.outlook.com:587 (TLS)
- **SendGrid**: smtp.sendgrid.net:587 (TLS)
- **Mailgun**: smtp.mailgun.org:587 (TLS)
- **Custom**: Any SMTP server with TLS support

### Gmail Configuration

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # NOT regular password
```

**Important**: Gmail requires App Password, not regular password.
Generate at: https://myaccount.google.com/apppasswords

## Security

### TLS/SSL

All SMTP connections use TLS encryption:

```javascript
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: false,  // true for 465, false for other ports
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD
  },
  tls: {
    rejectUnauthorized: true  // Verify SSL certificate
  }
});
```

### Input Sanitization

All inputs are sanitized to prevent injection attacks:

```javascript
function sanitizeInput(input) {
  // Remove null bytes
  input = input.replace(/\0/g, '');

  // Trim whitespace
  input = input.trim();

  // Limit length
  if (input.length > 10000) {
    throw new Error('Input too long');
  }

  return input;
}
```

## Logging

### Log Format

All requests are logged in JSON format:

```json
{
  "timestamp": "2026-01-13T10:35:15Z",
  "method": "POST",
  "endpoint": "/send-email",
  "recipients": ["recipient@example.com"],
  "success": true,
  "messageId": "<abc123xyz@smtp.gmail.com>",
  "duration": 1234,
  "retryCount": 0
}
```

### Log Levels

- `INFO`: Successful operations
- `WARN`: Retryable errors, rate limits
- `ERROR`: Non-retryable errors, server errors

## Client Integration

### Python Client Example

```python
import requests

def send_email_via_mcp(to, subject, body):
    url = "http://localhost:3000/send-email"

    payload = {
        "to": to,
        "subject": subject,
        "body": body
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        raise Exception(f"MCP error: {response.text}")
```

### Error Handling Example

```python
try:
    result = send_email_via_mcp(
        to="recipient@example.com",
        subject="Test",
        body="Test email"
    )
    print(f"Email sent: {result['messageId']}")
except requests.exceptions.Timeout:
    print("MCP server timeout")
except requests.exceptions.ConnectionError:
    print("MCP server not available")
except Exception as e:
    print(f"Error: {e}")
```

## Monitoring

### Health Check

Regularly check server health:

```bash
curl http://localhost:3000/health
```

### Metrics

The server exposes metrics at `/metrics` (if enabled):

```json
{
  "totalRequests": 1234,
  "successfulRequests": 1180,
  "failedRequests": 54,
  "averageResponseTime": 1234,
  "uptime": 86400
}
```

## References

- [Nodemailer Documentation](https://nodemailer.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [RFC 5322 (Email Format)](https://tools.ietf.org/html/rfc5322)
- [SMTP Status Codes](https://en.wikipedia.org/wiki/List_of_SMTP_server_return_codes)

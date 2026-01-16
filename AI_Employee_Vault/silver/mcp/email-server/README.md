# Email MCP Server

**Type**: Python MCP Server
**Version**: 1.0.0
**Protocol**: Model Context Protocol (MCP)

## Overview

A Python-based MCP server that provides email sending capabilities using Gmail API with OAuth2 authentication. This server exposes email functionality as MCP tools that can be used by Claude Code and other MCP clients.

## Features

- **send_email**: Send emails via Gmail API with OAuth2
- **validate_email**: Validate email addresses (RFC 5321 compliant)
- Secure OAuth2 authentication
- HTML and plain text email support
- CC and BCC support
- Comprehensive error handling
- Logging and audit trail

## Requirements

- Python 3.13+
- Gmail API credentials (OAuth2)
- MCP Python SDK

## Installation

### 1. Install Dependencies

```bash
# Using uv (recommended)
cd silver/mcp/email-server
uv pip install mcp google-auth google-api-python-client

# Or using pip
pip install mcp google-auth google-api-python-client
```

### 2. Configure Gmail API

The server uses the same Gmail API credentials as the Silver tier system:

```bash
# Credentials should be in silver/config/.env
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
```

If not configured, run:
```bash
python silver/scripts/setup_gmail.py
```

## Usage

### Running the Server

```bash
# From vault root
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault

# Activate virtual environment
source silver/.venv/bin/activate

# Run the MCP server
python silver/mcp/email-server/server.py
```

The server runs using stdio transport and communicates via stdin/stdout.

### Configuring in Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": [
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver/mcp/email-server/server.py"
      ],
      "env": {
        "VAULT_PATH": "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
      }
    }
  }
}
```

### Using the Tools

#### send_email

Send an email via Gmail API:

```python
# Tool call
{
  "name": "send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email",
    "html": true
  }
}
```

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject line
- `body` (required): Email body content
- `from_email` (optional): Sender email (uses authenticated account by default)
- `cc` (optional): CC recipients (comma-separated)
- `bcc` (optional): BCC recipients (comma-separated)
- `html` (optional): Whether body is HTML (default: true)

**Response:**
```
✅ Email sent successfully!
Message ID: <message_id>
To: recipient@example.com
Subject: Test Email
```

#### validate_email

Validate email address format:

```python
# Tool call
{
  "name": "validate_email",
  "arguments": {
    "email": "test@example.com"
  }
}
```

**Parameters:**
- `email` (required): Email address to validate

**Response:**
```
✅ Valid email address: test@example.com
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                            │
│                  (Claude Code)                           │
└─────────────────────────────────────────────────────────┘
                         ↓ stdio
┌─────────────────────────────────────────────────────────┐
│                  Email MCP Server                        │
│                    (server.py)                           │
│                                                          │
│  Tools:                                                  │
│  - send_email                                            │
│  - validate_email                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   EmailSender                            │
│            (silver.src.actions.email_sender)             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Gmail API                             │
│                  (OAuth2 + REST)                         │
└─────────────────────────────────────────────────────────┘
```

## Testing

### Manual Test

```bash
# Test the server directly
python silver/mcp/email-server/server.py

# The server will wait for MCP protocol messages on stdin
# Send a test message (JSON-RPC format)
```

### Integration Test

```bash
# Test via Claude Code
# The server will be automatically invoked when you use email tools
```

## Logging

Logs are written to:
- Console: INFO level and above
- File: `Logs/mcp_email_server.log` (if configured)

## Error Handling

The server handles errors gracefully:

- **Invalid email format**: Returns validation error
- **Missing credentials**: Returns authentication error
- **Gmail API errors**: Returns API error with details
- **Network errors**: Returns connection error

All errors are logged for debugging.

## Security

- **OAuth2 Authentication**: No passwords stored
- **Credentials Protection**: Stored in .env file (gitignored)
- **Input Validation**: All inputs validated before processing
- **Error Masking**: Sensitive data not exposed in errors

## Troubleshooting

### Server Won't Start

**Check Python version:**
```bash
python3 --version  # Should be 3.13+
```

**Check dependencies:**
```bash
pip list | grep mcp
pip list | grep google-auth
```

**Install missing dependencies:**
```bash
uv pip install mcp google-auth google-api-python-client
```

### Authentication Errors

**Check credentials:**
```bash
cat silver/config/.env | grep GMAIL
```

**Re-run setup:**
```bash
python silver/scripts/setup_gmail.py
```

### Email Not Sending

**Check logs:**
```bash
tail -f Logs/mcp_email_server.log
```

**Test Gmail API directly:**
```bash
python -c "
from silver.src.actions.email_sender import EmailSender
sender = EmailSender('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault', 'silver/config/.env')
result = sender.send_email('test@example.com', 'Test', 'Test body')
print(result)
"
```

## Development

### Running Tests

```bash
# Install dev dependencies
uv pip install pytest pytest-asyncio

# Run tests
pytest silver/mcp/email-server/tests/
```

### Adding New Tools

1. Add tool definition to `list_tools()`
2. Add handler function (e.g., `handle_new_tool()`)
3. Add case to `call_tool()`
4. Update documentation

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)

## License

Part of the Silver Tier AI Assistant project.

## Version History

- **1.0.0** (2026-01-14): Initial Python implementation
  - Migrated from Node.js to Python
  - Uses official MCP Python SDK
  - Integrates with existing EmailSender component

# Gmail API Reference

## Authentication

### OAuth2 Flow

1. Create OAuth2 credentials in Google Cloud Console
2. Enable Gmail API
3. Request scopes: `https://www.googleapis.com/auth/gmail.readonly`
4. Exchange authorization code for refresh token
5. Store refresh token securely in `.env`

### Token Refresh

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

## API Endpoints

### List Messages

```
GET https://gmail.googleapis.com/gmail/v1/users/me/messages
```

**Query Parameters**:
- `q`: Query string (e.g., "is:unread in:inbox")
- `maxResults`: Max number of messages (default: 100)
- `pageToken`: Token for pagination

**Response**:
```json
{
  "messages": [
    {"id": "18d1234567890abcd", "threadId": "18d1234567890abcd"}
  ],
  "nextPageToken": "token123",
  "resultSizeEstimate": 42
}
```

### Get Message

```
GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}
```

**Query Parameters**:
- `format`: FULL | METADATA | MINIMAL | RAW (default: FULL)

**Response**:
```json
{
  "id": "18d1234567890abcd",
  "threadId": "18d1234567890abcd",
  "labelIds": ["INBOX", "UNREAD"],
  "snippet": "Message preview...",
  "payload": {
    "headers": [
      {"name": "From", "value": "sender@example.com"},
      {"name": "Subject", "value": "Test Subject"}
    ],
    "body": {"data": "base64_encoded_body"}
  },
  "internalDate": "1705147800000"
}
```

## Rate Limits

- **Quota**: 1 billion quota units per day (free tier)
- **Per-user rate limit**: 250 quota units per user per second
- **List messages**: 5 quota units
- **Get message**: 5 quota units

**Best Practices**:
- Use batch requests when possible
- Implement exponential backoff for 429 errors
- Cache message IDs to avoid re-fetching

## Error Codes

- **400**: Invalid request (check query syntax)
- **401**: Invalid credentials (refresh token)
- **403**: Insufficient permissions (check scopes)
- **429**: Rate limit exceeded (exponential backoff)
- **500**: Server error (retry with backoff)

## Query Syntax

### Common Queries

```
is:unread in:inbox          # Unread messages in inbox
from:sender@example.com     # Messages from specific sender
subject:urgent              # Messages with "urgent" in subject
after:2026/01/01            # Messages after date
has:attachment              # Messages with attachments
```

### Operators

- `AND`: Implicit (space between terms)
- `OR`: Explicit operator
- `-`: Negation (e.g., `-is:read`)
- `()`: Grouping

## Python SDK

### Installation

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### Basic Usage

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('gmail', 'v1', credentials=creds)

# List unread messages
results = service.users().messages().list(
    userId='me',
    q='is:unread in:inbox',
    maxResults=10
).execute()

messages = results.get('messages', [])

# Get message details
for msg in messages:
    message = service.users().messages().get(
        userId='me',
        id=msg['id'],
        format='full'
    ).execute()
```

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth2 Scopes](https://developers.google.com/gmail/api/auth/scopes)

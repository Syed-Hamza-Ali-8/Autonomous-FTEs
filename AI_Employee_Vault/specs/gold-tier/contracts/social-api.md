# Social Media MCP Server API Contract

**Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Active

## Overview

This document defines the API contract for the Social Media MCP (Model Context Protocol) server, which provides integration with LinkedIn, Facebook, Instagram, and Twitter for the Gold Tier autonomous employee.

## Base Configuration

```json
{
  "mcpServers": {
    "social": {
      "command": "node",
      "args": ["gold/mcp/social/server.js"],
      "env": {
        "LINKEDIN_ACCESS_TOKEN": "${LINKEDIN_ACCESS_TOKEN}",
        "FACEBOOK_ACCESS_TOKEN": "${FACEBOOK_ACCESS_TOKEN}",
        "FACEBOOK_PAGE_ID": "${FACEBOOK_PAGE_ID}",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "${INSTAGRAM_BUSINESS_ACCOUNT_ID}",
        "TWITTER_API_KEY": "${TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_SECRET": "${TWITTER_ACCESS_SECRET}"
      }
    }
  }
}
```

## Authentication

### LinkedIn OAuth 2.0

**Authorization URL**: `https://www.linkedin.com/oauth/v2/authorization`
**Token URL**: `https://www.linkedin.com/oauth/v2/accessToken`
**Scopes**: `w_member_social`, `r_liteprofile`, `r_emailaddress`

### Facebook/Instagram Graph API

**Authorization URL**: `https://www.facebook.com/v18.0/dialog/oauth`
**Token URL**: `https://graph.facebook.com/v18.0/oauth/access_token`
**Scopes**: `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`

### Twitter API v2

**Authentication**: OAuth 1.0a or OAuth 2.0
**API Keys**: Consumer Key, Consumer Secret, Access Token, Access Token Secret

---

## API Methods

### 1. createPost

Create a social media post (draft or publish).

**Input**:
```json
{
  "method": "createPost",
  "params": {
    "platform": "linkedin|facebook|instagram|twitter",
    "content": "Post content text",
    "media_urls": ["https://example.com/image.jpg"],
    "scheduled_at": "2026-01-15T10:30:00Z",
    "approval_required": true,
    "hashtags": ["ProjectManagement", "Innovation"],
    "mentions": ["@company"]
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "platform": "linkedin",
    "status": "pending_approval",
    "file_path": "/Vault/Social_Media/Posts/post_linkedin_20260115_103000.md",
    "approval_request_id": "apr_20260115_103000"
  }
}
```

**Approval Required**: Yes (if approval_required = true)

---

### 2. publishPost

Publish an approved post to the platform.

**Input**:
```json
{
  "method": "publishPost",
  "params": {
    "post_id": "post_linkedin_20260115_103000"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "platform": "linkedin",
    "status": "published",
    "published_at": "2026-01-15T10:30:05Z",
    "platform_post_id": "urn:li:share:1234567890",
    "url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890"
  }
}
```

---

### 3. getEngagement

Get engagement metrics for a published post.

**Input**:
```json
{
  "method": "getEngagement",
  "params": {
    "post_id": "post_linkedin_20260115_103000"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "platform": "linkedin",
    "engagement": {
      "likes": 45,
      "comments": 8,
      "shares": 12,
      "impressions": 1250,
      "clicks": 67,
      "last_updated": "2026-01-16T10:00:00Z"
    },
    "engagement_rate": 5.2
  }
}
```

---

### 4. getComments

Retrieve comments on a post.

**Input**:
```json
{
  "method": "getComments",
  "params": {
    "post_id": "post_linkedin_20260115_103000",
    "limit": 50
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "comments": [
      {
        "comment_id": "comment_123",
        "author": "John Doe",
        "author_profile": "https://linkedin.com/in/johndoe",
        "text": "Great work! Congratulations!",
        "created_at": "2026-01-15T11:00:00Z",
        "likes": 3
      }
    ],
    "total": 8
  }
}
```

---

### 5. replyToComment

Reply to a comment on a post.

**Input**:
```json
{
  "method": "replyToComment",
  "params": {
    "post_id": "post_linkedin_20260115_103000",
    "comment_id": "comment_123",
    "reply_text": "Thank you! We're excited about this milestone."
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "reply_id": "reply_456",
    "comment_id": "comment_123",
    "created_at": "2026-01-15T11:05:00Z"
  }
}
```

**Approval Required**: No (replies are auto-approved if < 100 chars)

---

### 6. getDMs

Get direct messages (platform-specific).

**Input**:
```json
{
  "method": "getDMs",
  "params": {
    "platform": "linkedin|facebook|instagram|twitter",
    "since": "2026-01-15T00:00:00Z",
    "limit": 50
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "platform": "linkedin",
    "messages": [
      {
        "message_id": "dm_linkedin_123",
        "from": "Jane Smith",
        "from_profile": "https://linkedin.com/in/janesmith",
        "text": "Hi, I'd like to discuss a potential collaboration.",
        "created_at": "2026-01-15T09:00:00Z",
        "read": false
      }
    ],
    "total": 3
  }
}
```

---

### 7. sendDM

Send a direct message (requires approval).

**Input**:
```json
{
  "method": "sendDM",
  "params": {
    "platform": "linkedin|facebook|instagram|twitter",
    "recipient": "user_id or username",
    "message": "Message text"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "message_id": "dm_linkedin_456",
    "recipient": "janesmith",
    "sent_at": "2026-01-15T09:05:00Z"
  }
}
```

**Approval Required**: Yes (all DMs require approval)

---

### 8. getAnalytics

Get analytics for a time period.

**Input**:
```json
{
  "method": "getAnalytics",
  "params": {
    "platform": "linkedin|facebook|instagram|twitter|all",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "period": "2026-01-01 to 2026-01-31",
    "platforms": {
      "linkedin": {
        "posts": 12,
        "total_engagement": 450,
        "avg_engagement_rate": 4.2,
        "followers_gained": 25,
        "top_post": {
          "post_id": "post_linkedin_20260115_103000",
          "engagement": 65
        }
      },
      "twitter": {
        "posts": 20,
        "total_engagement": 280,
        "avg_engagement_rate": 3.1,
        "followers_gained": 15
      }
    },
    "summary": {
      "total_posts": 32,
      "total_engagement": 730,
      "avg_engagement_rate": 3.7
    }
  }
}
```

---

### 9. schedulePost

Schedule a post for future publishing.

**Input**:
```json
{
  "method": "schedulePost",
  "params": {
    "post_id": "post_linkedin_20260115_103000",
    "scheduled_at": "2026-01-15T10:30:00Z"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "status": "scheduled",
    "scheduled_at": "2026-01-15T10:30:00Z",
    "scheduler_job_id": "job_123"
  }
}
```

---

### 10. deletePost

Delete a published post.

**Input**:
```json
{
  "method": "deletePost",
  "params": {
    "post_id": "post_linkedin_20260115_103000"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "post_id": "post_linkedin_20260115_103000",
    "status": "deleted",
    "deleted_at": "2026-01-15T12:00:00Z"
  }
}
```

**Approval Required**: Yes (all deletions require approval)

---

## Platform-Specific Constraints

### LinkedIn
- **Max Length**: 3,000 characters
- **Media**: Up to 9 images or 1 video
- **Rate Limit**: 100 posts per day
- **Best Times**: Tuesday-Thursday, 10:00 AM - 12:00 PM

### Facebook
- **Max Length**: 63,206 characters
- **Media**: Up to 10 images or 1 video
- **Rate Limit**: 200 posts per day
- **Best Times**: Wednesday-Friday, 1:00 PM - 4:00 PM

### Instagram
- **Max Length**: 2,200 characters
- **Media**: Required (1-10 images or 1 video)
- **Rate Limit**: 25 posts per day
- **Best Times**: Monday-Friday, 11:00 AM - 1:00 PM

### Twitter
- **Max Length**: 280 characters (or thread)
- **Media**: Up to 4 images or 1 video
- **Rate Limit**: 300 posts per 3 hours
- **Best Times**: Monday-Friday, 12:00 PM - 3:00 PM

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "type": "transient|auth|logic|data|system",
    "recoverable": true,
    "retry_after": 60
  }
}
```

### Error Codes

| Code | Type | Recoverable | Description |
|------|------|-------------|-------------|
| `SOCIAL_AUTH_FAILED` | auth | Yes | Authentication failed |
| `SOCIAL_TOKEN_EXPIRED` | auth | Yes | Access token expired |
| `SOCIAL_RATE_LIMIT` | transient | Yes | Rate limit exceeded |
| `SOCIAL_CONTENT_TOO_LONG` | logic | No | Content exceeds platform limit |
| `SOCIAL_MEDIA_REQUIRED` | logic | No | Media required for platform |
| `SOCIAL_POST_NOT_FOUND` | data | No | Post not found |
| `SOCIAL_NETWORK_ERROR` | transient | Yes | Network error |

---

## Rate Limiting

**MCP Server Handling**:
- Track rate limits per platform
- Queue posts when approaching limit
- Automatic retry with exponential backoff
- Return `SOCIAL_RATE_LIMIT` error if queue full

---

## Testing

### Test Accounts

Create test accounts for each platform:
- LinkedIn: Personal test account
- Facebook: Test page
- Instagram: Test business account
- Twitter: Test account

### Test Cases

1. **Post Creation**
   - Create draft post
   - Submit for approval
   - Publish approved post

2. **Engagement Tracking**
   - Publish test post
   - Wait for engagement
   - Retrieve metrics

3. **Comment Management**
   - Get comments on post
   - Reply to comment
   - Verify reply published

4. **Analytics**
   - Generate analytics report
   - Verify calculations
   - Check all platforms

5. **Error Handling**
   - Test rate limit handling
   - Test content length validation
   - Test network error recovery

---

## Security

### Credentials Storage

- OAuth tokens encrypted at rest
- API keys never logged
- Tokens refreshed automatically before expiry

### Data Handling

- All social media data classified as "internal"
- Audit logging for all social operations
- No caching of DMs or private messages

### Compliance

- GDPR compliant data handling
- Platform terms of service compliance
- User privacy protection

---

## Integration Points

### Watchers
- `FacebookWatcher`: Monitors comments and DMs
- `InstagramWatcher`: Monitors comments and DMs
- `TwitterWatcher`: Monitors mentions and DMs

### Actions
- `SocialPoster`: Creates and publishes posts
- `SocialAnalytics`: Generates analytics reports
- `CommentResponder`: Responds to comments

### Intelligence
- `CEOBriefingGenerator`: Uses social data for performance analysis
- `ContentOptimizer`: Analyzes post performance for optimization

---

**API Version**: 1.0
**Platform API Versions**: LinkedIn v2, Facebook Graph v18.0, Instagram Graph v18.0, Twitter API v2
**Last Updated**: 2026-01-17

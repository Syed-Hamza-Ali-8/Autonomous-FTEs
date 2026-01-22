# Social Media MCP Server

Python MCP server for social media posting and analytics across Facebook, Instagram, and Twitter/X.

## Features

- **7 Tools** for social media management
- **Mock mode** for development without real API credentials
- **Multi-platform** support (Facebook, Instagram, Twitter)
- **Analytics** retrieval for all platforms

## Installation

```bash
cd gold/mcp/social
uv pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
nano .env  # Configure your API credentials
```

**Mock Mode (Default):**
```bash
SOCIAL_MEDIA_MOCK=true
```

**Real APIs:**
```bash
SOCIAL_MEDIA_MOCK=false
# Add your API credentials
```

## Available Tools

### 1. post_to_facebook
Post content to Facebook page or profile.

**Input:**
```json
{
  "content": "Your post content",
  "image_url": "https://example.com/image.jpg",
  "link": "https://example.com"
}
```

### 2. post_to_instagram
Post content to Instagram (requires image).

**Input:**
```json
{
  "caption": "Your caption",
  "image_url": "https://example.com/image.jpg",
  "hashtags": ["business", "ai", "automation"]
}
```

### 3. post_to_twitter
Post tweet to Twitter/X.

**Input:**
```json
{
  "text": "Your tweet (max 280 chars)",
  "image_url": "https://example.com/image.jpg"
}
```

### 4. get_facebook_analytics
Get Facebook analytics and engagement metrics.

**Input:**
```json
{
  "date_from": "2026-01-01",
  "date_to": "2026-01-19"
}
```

### 5. get_instagram_analytics
Get Instagram analytics and engagement metrics.

### 6. get_twitter_analytics
Get Twitter/X analytics and engagement metrics.

### 7. health_check
Check social media API connections.

## Usage

### Running the MCP Server

```bash
python server.py
```

### Testing

```bash
# Test with mock mode
export SOCIAL_MEDIA_MOCK=true
python server.py
```

## Integration with Agent Skills

The `post-to-social-media` Agent Skill uses this MCP server:

```
.claude/skills/post-to-social-media/
├── SKILL.md
├── templates/
├── examples/
└── references/
```

## Mock Mode

In mock mode, all operations return realistic mock data without making real API calls:

- Posts return mock post IDs and URLs
- Analytics return realistic engagement metrics
- No real API credentials required

## Real API Integration

To use real APIs, set `SOCIAL_MEDIA_MOCK=false` and configure credentials:

### Facebook
1. Create Facebook App at developers.facebook.com
2. Get Page Access Token
3. Add to `.env`

### Instagram
1. Use Instagram Graph API or instagrapi
2. Configure credentials in `.env`

### Twitter
1. Create Twitter App at developer.twitter.com
2. Get API keys and tokens
3. Add to `.env`

## Security

- Never commit `.env` file
- Use environment variables for credentials
- Implement HITL approval for sensitive posts
- Log all actions for audit trail

## Architecture

```
Social Media MCP Server
├── server.py           # MCP server implementation
├── requirements.txt    # Dependencies
├── .env.example        # Configuration template
└── README.md           # This file
```

## Status

- ✅ Mock mode implemented
- ✅ 7 tools available
- ✅ MCP protocol compliant
- ⏳ Real API integration (Phase 2)

## Version

1.0.0 - Initial implementation with mock mode

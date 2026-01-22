# Post to Social Media Skill

**Skill ID**: post-to-social-media
**Version**: 1.0.0
**User Story**: US-GOLD-1 - Multi-Platform Social Media Posting
**Priority**: P1 (Gold Tier MVP)

## Purpose

Post content to multiple social media platforms (Facebook, Instagram, Twitter) with human-in-the-loop approval workflow. This skill implements the **Action** phase for social media engagement, enabling autonomous business content distribution across platforms while maintaining human oversight for sensitive external communications.

## Capabilities

- **Multi-Platform Posting**: Post to Facebook, Instagram, and Twitter simultaneously or individually
- **Content Generation**: Generate platform-optimized content from templates
- **HITL Approval**: Require human approval before posting to external platforms
- **Draft Management**: Create drafts in Needs_Action folder for review
- **Platform-Specific Formatting**: Optimize content for each platform (hashtags, mentions, character limits)
- **Error Recovery**: Handle platform-specific errors and rate limits
- **Audit Logging**: Track all posting activity for compliance

## Architecture

### Core Components

1. **SocialMediaPoster** (`gold/src/actions/social_media_poster.py`)
   - `post_to_platform(platform, content, image_path)` → Dict[success, post_id]
   - `post_to_all_platforms(content, image_path)` → Dict[platform: result]
   - `create_draft(content, platforms)` → str (draft_file_path)

2. **PlatformPosters** (`gold/src/actions/`)
   - `FacebookPoster` - Post to Facebook via mock API
   - `InstagramPoster` - Post to Instagram via mock API
   - `TwitterPoster` - Post to Twitter via mock API

3. **ContentOptimizer** (`gold/src/utils/content_optimizer.py`)
   - `optimize_for_platform(content, platform)` → str
   - `add_hashtags(content, platform)` → str
   - `truncate_if_needed(content, platform)` → str

### Posting Workflow

```
1. Content Creation → Generate or receive content
                   → Optimize for each platform
                   → Create draft in Needs_Action/

2. Human Review → User reviews draft in Needs_Action/
               → User edits content if needed
               → User moves to Approved/ or Rejected/

3. Execution → Detect approved draft
            → Post to selected platforms
            → Handle platform-specific errors
            → Log results

4. Result Tracking → Update draft file with results
                  → Move to Done/ if successful
                  → Keep in Approved/ if failed (with error)
                  → Log to audit trail
```

## Configuration

### Social Media Config (`gold/config/social_media_config.yaml`)

```yaml
platforms:
  facebook:
    enabled: true
    use_mock: true  # Set to false for real API
    api_url: "http://localhost:3001/facebook"
    max_length: 63206
    supports_images: true
    supports_hashtags: true

  instagram:
    enabled: true
    use_mock: true
    api_url: "http://localhost:3001/instagram"
    max_length: 2200
    supports_images: true
    supports_hashtags: true
    hashtag_limit: 30

  twitter:
    enabled: true
    use_mock: true
    api_url: "http://localhost:3001/twitter"
    max_length: 280
    supports_images: true
    supports_hashtags: true

content_optimization:
  auto_hashtags: true
  hashtag_count: 3
  platform_specific_formatting: true

approval:
  required: true
  timeout_hours: 24
  notify_on_draft: true
```

### Environment Variables (`.env`)

```bash
# Facebook (Real API - Phase 4)
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# Instagram (Real API - Phase 4)
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_ACCOUNT_ID=your_instagram_account_id

# Twitter (Real API - Phase 4)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Mock Mode (Current)
USE_MOCK_SOCIAL=true
```

## Usage

### Post to All Platforms

```python
from gold.src.actions.social_media_poster import SocialMediaPoster

poster = SocialMediaPoster(vault_path="/path/to/vault")

# Create draft for approval
draft_path = poster.create_draft(
    content="🚀 Excited to share our latest AI automation breakthrough! "
            "We're helping businesses save 10+ hours per week. "
            "Interested in learning more? Let's connect! "
            "#AI #Automation #Business",
    platforms=["facebook", "instagram", "twitter"],
    image_path=None  # Optional
)

print(f"Draft created: {draft_path}")
print("Please review and approve in Needs_Action/ folder")

# After approval, execute posting
results = poster.execute_approved_draft(draft_path)

for platform, result in results.items():
    if result["success"]:
        print(f"✅ {platform}: Posted successfully (ID: {result['post_id']})")
    else:
        print(f"❌ {platform}: Failed - {result['error']}")
```

### Post to Single Platform

```python
# Post only to Facebook
result = poster.post_to_platform(
    platform="facebook",
    content="Check out our latest blog post!",
    image_path="/path/to/image.jpg"
)

if result["success"]:
    print(f"Posted to Facebook: {result['post_id']}")
```

### Using Claude Code Skill

```bash
# Create draft for all platforms
claude --skill post-to-social-media \
  --content "Your post content here" \
  --platforms facebook,instagram,twitter

# Create draft for specific platform
claude --skill post-to-social-media \
  --content "Your post content here" \
  --platform twitter
```

## Output Format

### Draft File (Needs_Action/)

Created in `Needs_Action/` folder:

```markdown
---
id: social_post_20260119_143045_abc123
type: social_media_post
status: pending_approval
created_at: 2026-01-19T14:30:45Z
timeout_at: 2026-01-20T14:30:45Z
platforms:
  - facebook
  - instagram
  - twitter
---

# Social Media Post Draft

**Status**: ⏳ Pending Approval
**Created**: 2026-01-19 2:30 PM
**Platforms**: Facebook, Instagram, Twitter

## Content

🚀 Excited to share our latest AI automation breakthrough!

We're helping businesses save 10+ hours per week with intelligent workflow automation.

Interested in learning more? Let's connect!

#AI #Automation #Business

## Platform-Specific Previews

### Facebook
[Full content - no truncation needed]

### Instagram
[Full content with hashtags optimized]

### Twitter
[Truncated to 280 characters if needed]

## Instructions

**To Approve**:
1. Review content above
2. Edit if needed (changes will apply to all platforms)
3. Change `status: pending_approval` to `status: approved`
4. Save file
5. Post will execute automatically within 1 minute

**To Reject**:
1. Change `status: pending_approval` to `status: rejected`
2. Add `rejection_reason: "Your reason"` to frontmatter
3. Save file

**To Edit**:
- Edit the content section directly
- Platform-specific optimizations will be reapplied
- Save and approve when ready

## Timeout

If no response within 24 hours, this draft will expire.
```

### After Successful Posting (Done/)

```yaml
---
id: social_post_20260119_143045_abc123
type: social_media_post
status: completed
created_at: 2026-01-19T14:30:45Z
approved_at: 2026-01-19T14:35:12Z
executed_at: 2026-01-19T14:35:20Z
platforms:
  facebook:
    success: true
    post_id: "123456789_987654321"
    url: "https://facebook.com/posts/987654321"
  instagram:
    success: true
    post_id: "ABC123XYZ"
    url: "https://instagram.com/p/ABC123XYZ"
  twitter:
    success: true
    post_id: "1234567890123456789"
    url: "https://twitter.com/user/status/1234567890123456789"
---
```

### After Failed Posting (Approved/)

```yaml
---
id: social_post_20260119_143045_abc123
type: social_media_post
status: failed
created_at: 2026-01-19T14:30:45Z
approved_at: 2026-01-19T14:35:12Z
last_attempt_at: 2026-01-19T14:35:20Z
retry_count: 3
platforms:
  facebook:
    success: true
    post_id: "123456789_987654321"
  instagram:
    success: false
    error: "Rate limit exceeded. Try again in 15 minutes."
  twitter:
    success: true
    post_id: "1234567890123456789"
---
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
requests = "^2.31.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
pillow = "^10.1.0"  # Image processing
```

### System Requirements

- Python 3.13+
- Internet connection (for real APIs)
- Mock APIs running (for testing)

## Setup Instructions

### 1. Configure Social Media Credentials

```bash
# Copy environment template
cp gold/.env.example gold/.env

# Edit with your credentials (Phase 4 - Real APIs)
nano gold/.env

# For now, use mock mode
USE_MOCK_SOCIAL=true
```

### 2. Start Mock APIs (Testing)

```bash
# Mock APIs are already running via PM2
pm2 list | grep social

# If not running, start them
pm2 start gold/ecosystem.config.js --only "gold-facebook-watcher,gold-instagram-watcher,gold-twitter-watcher"
```

### 3. Test Posting

```bash
# Test with mock APIs
python gold/src/actions/social_media_poster.py \
  --content "Test post from AI Employee" \
  --platforms facebook,instagram,twitter \
  --dry-run

# Live test (creates draft)
python gold/src/actions/social_media_poster.py \
  --content "Test post from AI Employee" \
  --platforms facebook,instagram,twitter
```

### 4. Verify Draft Created

```bash
# Check Needs_Action folder
ls -lh Needs_Action/ | grep social_post

# Review draft
cat Needs_Action/social_post_*.md
```

## Error Handling

### Platform-Specific Errors

**Facebook**:
- **190**: Access token expired → Re-authenticate
- **368**: Temporarily blocked for spam → Wait 24 hours
- **100**: Invalid parameter → Check content format

**Instagram**:
- **429**: Rate limit exceeded → Wait 15 minutes
- **400**: Invalid media → Check image format/size
- **403**: Permission denied → Check account permissions

**Twitter**:
- **187**: Status is duplicate → Content already posted
- **326**: Account locked → Verify account
- **429**: Rate limit → Wait for rate limit reset

### Retry Logic

```python
# Exponential backoff: 2s, 4s, 8s
retry_delays = [2, 4, 8]  # seconds

for attempt in range(max_retries):
    try:
        result = post_to_platform(...)
        if result["success"]:
            break
    except RateLimitError as e:
        if attempt < max_retries - 1:
            delay = retry_delays[attempt]
            time.sleep(delay)
        else:
            log_failure(platform, error=str(e))
```

### Graceful Degradation

- **One platform fails**: Continue posting to other platforms
- **All platforms fail**: Keep draft in Approved/, notify user
- **Network error**: Retry with exponential backoff
- **Authentication error**: Notify user, pause posting

## Performance

- **Posting Time**: ~2-5 seconds per platform
- **Multi-Platform**: ~10-15 seconds for all 3 platforms
- **Memory**: ~50MB per poster process
- **CPU**: Minimal (<5% on modern systems)
- **Network**: ~100KB per post (text only), ~2MB with image

## Testing

### Unit Tests

```bash
pytest gold/tests/unit/test_social_media_poster.py
pytest gold/tests/unit/test_facebook_poster.py
pytest gold/tests/unit/test_instagram_poster.py
pytest gold/tests/unit/test_twitter_poster.py
```

### Integration Tests

```bash
pytest gold/tests/integration/test_multi_platform_posting.py
```

### Manual Testing

1. **Create Test Draft**:
   ```bash
   python gold/scripts/test_social_posting.py --create-draft
   ```

2. **Review Draft**: Check `Needs_Action/` folder

3. **Approve Draft**: Edit YAML frontmatter, set `status: approved`

4. **Verify Posting**: Check mock API responses

5. **Check Audit Log**: `cat Logs/$(date +%Y-%m-%d).json | grep social_media_post`

## Success Criteria

- ✅ Posts successfully to all 3 platforms (mock mode)
- ✅ HITL approval workflow enforced (100% compliance)
- ✅ Platform-specific content optimization working
- ✅ Error handling graceful (partial failures handled)
- ✅ Audit logging complete for all attempts
- ✅ Draft creation and approval workflow smooth
- ✅ Retry logic working for transient errors

## Security & Compliance

⚠️ **Important Security Notes**:

1. **Platform ToS**: Automated posting may violate platform Terms of Service
2. **Use Test Accounts**: Always use test accounts for automation
3. **Rate Limiting**: Respect platform rate limits (max 1 post/hour recommended)
4. **Content Review**: Always require human approval before posting
5. **Credentials**: Never commit API credentials to version control

**Best Practices**:
- ✅ Use mock APIs for testing
- ✅ Require approval for all posts
- ✅ Respect rate limits
- ✅ Monitor for suspension warnings
- ✅ Use environment variables for credentials
- ❌ Never auto-post without approval
- ❌ Never exceed platform rate limits

## Related Skills

- **manage-approvals**: Provides approval workflow for posts
- **monitor-social-media**: Monitors engagement on posted content
- **generate-ceo-briefing**: Includes social media analytics

## References

- See `references/facebook_api_docs.md` for Facebook API details
- See `references/instagram_api_docs.md` for Instagram API details
- See `references/twitter_api_docs.md` for Twitter API details
- See `references/content_guidelines.md` for content best practices

## Examples

- See `examples/facebook_post_example.md` for Facebook posting example
- See `examples/instagram_post_example.md` for Instagram posting example
- See `examples/twitter_post_example.md` for Twitter posting example
- See `examples/failed_post_example.md` for error handling example

## Templates

- See `templates/social_post_template.md` for post structure template

## Changelog

- **1.0.0** (2026-01-19): Initial implementation for Gold tier
  - Multi-platform posting (Facebook, Instagram, Twitter)
  - HITL approval workflow
  - Platform-specific content optimization
  - Mock API integration
  - Comprehensive error handling and retry logic

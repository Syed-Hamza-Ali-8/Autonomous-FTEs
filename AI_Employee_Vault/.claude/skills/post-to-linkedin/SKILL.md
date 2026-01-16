# Post to LinkedIn Skill

**Skill ID**: post-to-linkedin
**Version**: 1.0.0
**User Story**: US2 - LinkedIn Auto-Posting for Sales Generation
**Priority**: P1 (MVP)

## Purpose

Automatically generate and post business content to LinkedIn to generate sales leads and build brand awareness. This skill implements the **Action** phase of the Perception → Reasoning → Action architecture, executing automated LinkedIn posting for business development.

## Capabilities

- **Content Generation**: Generate engaging business posts from templates
- **Scheduled Posting**: Post to LinkedIn on a daily schedule
- **Session Management**: Maintain LinkedIn Web session via Playwright
- **Topic Rotation**: Rotate through business topics for variety
- **Error Recovery**: Handle session expiration and posting failures
- **Activity Logging**: Track all posting activity for audit trail

## Architecture

### Core Components

1. **LinkedInPoster** (`silver/src/watchers/linkedin_poster.py`)
   - `post_update(content, image_path)` → Dict[success, timestamp]
   - `generate_business_post(topic)` → str
   - `schedule_post(content, schedule_time)` → Dict[success, file_path]

2. **LinkedInScheduler** (`silver/scripts/linkedin_scheduler.py`)
   - `should_post_now()` → bool
   - `get_next_topic()` → str
   - `post_to_linkedin()` → bool
   - `run()` → continuous loop

3. **Setup Script** (`silver/scripts/setup_linkedin.py`)
   - `setup_linkedin_session(vault_path)` → bool
   - Interactive browser-based authentication
   - Session persistence to `linkedin_session/`

### Posting Workflow

```
1. Scheduler Check → Is it posting time? → Yes: Continue
                                        → No: Sleep 10 minutes

2. Content Generation → Select next topic from rotation
                     → Generate post from template
                     → Log content

3. Post to LinkedIn → Launch browser with saved session
                   → Navigate to LinkedIn feed
                   → Click "Start a post"
                   → Fill content
                   → Click "Post"
                   → Verify success

4. Result Tracking → Log success/failure
                  → Update last post time
                  → Schedule next post
```

## Configuration

### Watcher Config (`silver/config/watcher_config.yaml`)

```yaml
linkedin:
  enabled: true
  post_interval: 86400  # seconds (24 hours)
  session_path: "silver/config/linkedin_session"
  headless: true
  timeout: 30
  auto_generate: true
  topics:
    - "AI automation"
    - "business productivity"
    - "workflow optimization"
    - "digital transformation"
    - "sales automation"
  post_time: 9  # Hour of day (24h format)
```

### Environment Variables (`.env`)

```bash
# LinkedIn session path (auto-configured during setup)
LINKEDIN_SESSION_PATH=./silver/config/linkedin_session
```

## Usage

### Interactive Setup

```bash
# First-time setup: Login to LinkedIn and save session
python silver/scripts/setup_linkedin.py
```

**What happens:**
1. Browser opens to LinkedIn login
2. User logs in with fake/test profile
3. Session saved to `linkedin_session/`
4. .env file updated automatically

### Manual Posting

```bash
# Post immediately with auto-generated content
cd silver
python -m src.watchers.linkedin_poster
```

**Workflow:**
1. Generates business content
2. Shows preview
3. Asks for confirmation
4. Posts to LinkedIn
5. Reports result

### Scheduled Posting

```bash
# Start LinkedIn scheduler (daily posting at 9 AM)
python silver/scripts/linkedin_scheduler.py &

# Or start with all services
./silver/scripts/startup.sh
```

**Behavior:**
- Posts once per day at configured time (default 9 AM)
- Rotates through topics automatically
- Runs continuously in background
- Logs all activity to `Logs/linkedin_scheduler.log`

### Testing

```bash
# Dry run (no actual posting)
python silver/scripts/test_linkedin.py --dry-run

# Live test (posts to LinkedIn)
python silver/scripts/test_linkedin.py
```

## Output Format

### Generated Post Structure

```markdown
🚀 [Engaging opening line about topic]

[2-3 sentences about business value]

[Call to action]

#Hashtag1 #Hashtag2 #Hashtag3
```

### Example Generated Post

```
🚀 Excited to share our latest progress in AI automation!

We're building innovative solutions that help businesses
automate their workflows and increase productivity.

Interested in learning more? Let's connect!

#Business #Automation #Innovation
```

### Log Entry Format

```json
{
  "timestamp": "2026-01-16T10:30:45",
  "level": "INFO",
  "message": "Successfully posted to LinkedIn",
  "topic": "AI automation",
  "content_length": 187,
  "success": true
}
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
playwright = "^1.40.0"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

### System Requirements

- Python 3.13+
- Playwright with Chromium browser
- Internet connection
- LinkedIn account (fake/test recommended)

## Setup Instructions

### 1. Install Playwright

```bash
# Activate virtual environment
source silver/.venv/bin/activate

# Install Playwright
uv pip install playwright

# Install Chromium browser
playwright install chromium

# Install system dependencies (Linux/WSL)
playwright install-deps chromium
```

### 2. Create Test LinkedIn Profile

⚠️ **Important**: Use a fake/test profile to avoid ToS violations

- Create new LinkedIn account with temporary email
- Use fake name and details
- Complete basic profile setup
- This protects your real account

### 3. Run Setup Script

```bash
python silver/scripts/setup_linkedin.py
```

Follow the prompts to login and save session.

### 4. Verify Setup

```bash
# Test without posting
python silver/scripts/test_linkedin.py --dry-run

# Test with actual posting
python silver/scripts/test_linkedin.py
```

## Error Handling

### Session Expired

**Error**: "LinkedIn session expired. Please re-login."

**Recovery**:
```bash
python silver/scripts/setup_linkedin.py
```

### Posting Timeout

**Error**: "Timeout while posting"

**Possible causes**:
- LinkedIn UI changed (selectors outdated)
- Network issues
- Session expired

**Recovery**:
1. Check logs: `tail -f Logs/linkedin_scheduler.log`
2. Re-run setup if session expired
3. Test manually: `python silver/scripts/test_linkedin.py`

### Browser Not Found

**Error**: "Playwright not installed" or "Chromium not found"

**Recovery**:
```bash
playwright install chromium
playwright install-deps chromium  # Linux/WSL only
```

## Performance

- **Posting Time**: ~10-15 seconds per post
- **Memory Usage**: ~200MB (Chromium browser)
- **CPU Usage**: <5% (idle), ~20% (during posting)
- **Network**: Minimal (only during posting)
- **Disk Space**: ~300MB (Chromium + session data)

## Testing

### Unit Tests

```bash
pytest silver/tests/unit/test_linkedin_poster.py
```

### Integration Tests

```bash
pytest silver/tests/integration/test_linkedin_posting.py
```

### Manual Testing

1. Run dry run test: `python silver/scripts/test_linkedin.py --dry-run`
2. Verify content generation works
3. Run live test: `python silver/scripts/test_linkedin.py`
4. Verify post appears on LinkedIn
5. Check logs: `tail -f Logs/linkedin_scheduler.log`

## Success Criteria

- ✅ Daily posts published automatically at 9 AM
- ✅ Content is engaging and professional
- ✅ No account suspension or ToS violations
- ✅ Session persists for 7+ days without re-login
- ✅ Error recovery works (session expiration, network issues)
- ✅ All activity logged for audit trail

## Security & Compliance

⚠️ **Important Security Notes**:

1. **LinkedIn ToS**: Automated posting may violate LinkedIn's Terms of Service
2. **Use Test Account**: Always use a fake/test profile for automation
3. **Rate Limiting**: Post maximum once per day to avoid detection
4. **Session Security**: Session stored locally, not committed to git
5. **Content Review**: Review generated content before posting (manual mode)

**Best Practices**:
- ✅ Use disposable test accounts
- ✅ Post maximum once per day
- ✅ Vary content (topic rotation)
- ✅ Monitor for suspension warnings
- ❌ Never use real LinkedIn account
- ❌ Never post more than once per day

## Related Skills

- **monitor-communications**: Monitors responses to LinkedIn posts (future)
- **manage-approvals**: Optional approval workflow for posts
- **schedule-tasks**: Schedules daily posting

## References

- See `references/linkedin_automation.md` for automation best practices
- See `references/content_guidelines.md` for content creation guidelines
- See `references/playwright_selectors.md` for LinkedIn Web selectors
- See `examples/successful_post.md` for example successful post
- See `examples/failed_post.md` for example error handling
- See `templates/post_template.md` for post structure template

## Changelog

- **1.0.0** (2026-01-16): Initial implementation for Silver tier completion
  - LinkedIn poster with Playwright automation
  - Daily scheduled posting at 9 AM
  - Topic rotation (5 business topics)
  - Session management and error recovery
  - Comprehensive logging and monitoring

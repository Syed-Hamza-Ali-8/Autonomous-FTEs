# Scheduled Post Template

This template defines the structure for scheduled LinkedIn posts stored in the vault.

## File Format

Scheduled posts are stored as markdown files with YAML frontmatter in:
```
silver/scheduled_posts/linkedin_YYYYMMDD_HHMMSS.md
```

## Frontmatter Structure

```yaml
---
type: linkedin_post
scheduled_time: YYYY-MM-DDTHH:MM:SS
status: pending
topic: string
priority: normal
created_at: YYYY-MM-DDTHH:MM:SS
retry_count: 0
last_attempt: null
error: null
---
```

## Full Template

```markdown
---
type: linkedin_post
scheduled_time: {{SCHEDULED_TIME}}
status: {{STATUS}}
topic: {{TOPIC}}
priority: {{PRIORITY}}
created_at: {{CREATED_AT}}
retry_count: 0
last_attempt: null
error: null
---

# Scheduled LinkedIn Post

**Topic**: {{TOPIC}}
**Scheduled For**: {{SCHEDULED_TIME}}

## Content

{{POST_CONTENT}}

## Metadata

- **Character Count**: {{CHAR_COUNT}}
- **Hashtags**: {{HASHTAG_COUNT}}
- **Has Image**: {{HAS_IMAGE}}

## Status History

- {{CREATED_AT}}: Post created
```

## Status Values

- `pending` - Waiting to be posted
- `in_progress` - Currently being posted
- `completed` - Successfully posted
- `failed` - Failed to post (see error field)
- `cancelled` - Manually cancelled

## Priority Values

- `low` - Post when convenient
- `normal` - Standard priority
- `high` - Post as soon as possible

## Example Scheduled Post

```markdown
---
type: linkedin_post
scheduled_time: 2026-01-17T09:00:00
status: pending
topic: AI automation
priority: normal
created_at: 2026-01-16T14:30:00
retry_count: 0
last_attempt: null
error: null
---

# Scheduled LinkedIn Post

**Topic**: AI automation
**Scheduled For**: 2026-01-17 09:00:00

## Content

🚀 Excited to share our latest progress in AI automation!

We're building innovative solutions that help businesses
automate their workflows and increase productivity.

Interested in learning more? Let's connect!

#Business #Automation #Innovation

## Metadata

- **Character Count**: 187
- **Hashtags**: 3
- **Has Image**: false

## Status History

- 2026-01-16 14:30:00: Post created
```

## Scheduler Processing

### Scheduler Workflow

```python
def process_scheduled_posts():
    """Process scheduled posts."""
    scheduled_dir = Path("silver/scheduled_posts")

    for post_file in scheduled_dir.glob("linkedin_*.md"):
        # Parse frontmatter
        with open(post_file) as f:
            content = f.read()
            frontmatter, body = parse_markdown(content)

        # Check if it's time to post
        scheduled_time = datetime.fromisoformat(frontmatter['scheduled_time'])
        now = datetime.now()

        if now >= scheduled_time and frontmatter['status'] == 'pending':
            # Extract content
            post_content = extract_post_content(body)

            # Update status
            update_frontmatter(post_file, {'status': 'in_progress'})

            # Post to LinkedIn
            result = poster.post_update(post_content)

            if result['success']:
                # Mark as completed
                update_frontmatter(post_file, {
                    'status': 'completed',
                    'last_attempt': now.isoformat()
                })

                # Move to archive
                archive_post(post_file)
            else:
                # Mark as failed
                update_frontmatter(post_file, {
                    'status': 'failed',
                    'last_attempt': now.isoformat(),
                    'retry_count': frontmatter['retry_count'] + 1,
                    'error': result['error']
                })
```

## Creating Scheduled Posts

### Via Code

```python
from datetime import datetime, timedelta

def schedule_linkedin_post(content, topic, schedule_time=None):
    """Schedule a LinkedIn post."""
    if schedule_time is None:
        # Default: tomorrow at 9 AM
        schedule_time = datetime.now().replace(
            hour=9, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

    # Create scheduled post file
    filename = f"linkedin_{schedule_time.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = Path("silver/scheduled_posts") / filename

    # Generate frontmatter
    frontmatter = {
        'type': 'linkedin_post',
        'scheduled_time': schedule_time.isoformat(),
        'status': 'pending',
        'topic': topic,
        'priority': 'normal',
        'created_at': datetime.now().isoformat(),
        'retry_count': 0,
        'last_attempt': None,
        'error': None
    }

    # Write file
    with open(filepath, 'w') as f:
        f.write('---\n')
        for key, value in frontmatter.items():
            f.write(f'{key}: {value}\n')
        f.write('---\n\n')
        f.write(f'# Scheduled LinkedIn Post\n\n')
        f.write(f'**Topic**: {topic}\n')
        f.write(f'**Scheduled For**: {schedule_time}\n\n')
        f.write(f'## Content\n\n{content}\n')

    return filepath
```

### Via CLI

```bash
# Schedule post for tomorrow at 9 AM
python silver/scripts/schedule_linkedin_post.py \
    --content "Your post content here" \
    --topic "AI automation" \
    --time "2026-01-17 09:00"
```

## Retry Logic

### Automatic Retry

```python
def should_retry(frontmatter):
    """Check if post should be retried."""
    max_retries = 3
    retry_delay = 3600  # 1 hour

    if frontmatter['status'] != 'failed':
        return False

    if frontmatter['retry_count'] >= max_retries:
        return False

    if frontmatter['last_attempt']:
        last_attempt = datetime.fromisoformat(frontmatter['last_attempt'])
        time_since = (datetime.now() - last_attempt).total_seconds()

        if time_since < retry_delay:
            return False

    return True
```

### Manual Retry

```bash
# Reset failed post to pending
python silver/scripts/retry_linkedin_post.py \
    --file silver/scheduled_posts/linkedin_20260117_090000.md
```

## Cancelling Scheduled Posts

### Via Code

```python
def cancel_scheduled_post(post_file):
    """Cancel a scheduled post."""
    update_frontmatter(post_file, {
        'status': 'cancelled',
        'last_attempt': datetime.now().isoformat()
    })

    # Move to cancelled folder
    cancelled_dir = Path("silver/scheduled_posts/cancelled")
    cancelled_dir.mkdir(exist_ok=True)

    shutil.move(post_file, cancelled_dir / post_file.name)
```

### Via CLI

```bash
# Cancel scheduled post
python silver/scripts/cancel_linkedin_post.py \
    --file silver/scheduled_posts/linkedin_20260117_090000.md
```

## Archiving

### Completed Posts

Completed posts are moved to:
```
silver/scheduled_posts/archive/YYYY/MM/
```

### Failed Posts

Failed posts (after max retries) are moved to:
```
silver/scheduled_posts/failed/
```

## Monitoring

### List Scheduled Posts

```bash
# List all pending posts
ls -lh silver/scheduled_posts/linkedin_*.md

# Count by status
grep -r "status: pending" silver/scheduled_posts/ | wc -l
grep -r "status: failed" silver/scheduled_posts/ | wc -l
```

### View Post Details

```bash
# View specific post
cat silver/scheduled_posts/linkedin_20260117_090000.md
```

## Summary

**Scheduled post workflow**:
1. Create scheduled post file
2. Scheduler checks every 10 minutes
3. Post when scheduled time arrives
4. Update status (completed/failed)
5. Archive or retry as needed

**Key features**:
- YAML frontmatter for metadata
- Status tracking
- Automatic retry logic
- Priority levels
- Archive management

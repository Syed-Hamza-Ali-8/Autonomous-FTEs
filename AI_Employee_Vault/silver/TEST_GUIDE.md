# Silver Tier Testing Guide

This guide walks you through testing Gmail, WhatsApp, and LinkedIn functionality.

## Prerequisites Check

```bash
# Navigate to silver directory
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.14.0
```

## Test 1: Gmail Watcher

### Single Check (Recommended First)

```bash
# Run Gmail watcher once (will check for unread emails and exit)
python -m src.watchers.gmail_watcher
```

**Expected Output:**
```
INFO - Gmail watcher initialized successfully
INFO - Found X messages matching query
INFO - Created action file: /path/to/Needs_Action/msg_gmail_XXXXX.md
```

**What to Check:**
- New files appear in `Needs_Action/` folder
- Files have `.md` extension with `msg_gmail_` prefix
- Open a file to verify email content is captured

**Troubleshooting:**
- **Error: "Gmail credentials not configured"** → Run `python scripts/setup_gmail.py`
- **Error: "401 Unauthorized"** → OAuth token expired, re-run setup
- **No messages found** → Send yourself a test email first

---

## Test 2: WhatsApp Watcher

### Single Check (Recommended First)

```bash
# Run WhatsApp watcher once
python -m src.watchers.whatsapp_watcher
```

**Expected Output:**
```
INFO - WhatsApp watcher initialized successfully
INFO - Found X unread chats
INFO - Processing chat: Contact Name
INFO - Created action file: /path/to/Needs_Action/msg_whatsapp_XXXXX.md
```

**What to Check:**
- Browser opens (if headless=false) or runs in background
- New files appear in `Needs_Action/` with `msg_whatsapp_` prefix
- WhatsApp messages are captured correctly

**Troubleshooting:**
- **Error: "WhatsApp session expired"** → Run `python scripts/setup_whatsapp.py`
- **Error: "QR code detected"** → Session expired, re-scan QR code
- **Error: "Playwright not installed"** → Run `playwright install chromium`
- **No messages found** → Send yourself a WhatsApp message first

---

## Test 3: LinkedIn Poster

### Test Content Generation Only

```bash
# Test content generation without posting
python -c "
from src.watchers.linkedin_poster import LinkedInPoster
poster = LinkedInPoster('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
content = poster.generate_business_post('AI automation')
print('Generated content:')
print('-' * 50)
print(content)
"
```

**Expected Output:**
```
Generated content:
--------------------------------------------------
🚀 Excited to share our latest progress in AI automation!

We're building innovative solutions that help businesses
automate their workflows and increase productivity.

Interested in learning more? Let's connect!

#Business #Automation #Innovation
```

### Test Actual Posting (Interactive)

```bash
# Run LinkedIn poster with confirmation prompt
python -m src.watchers.linkedin_poster
```

**Expected Output:**
```
Generated content:
--------------------------------------------------
[Content preview]
--------------------------------------------------

Post this to LinkedIn? (yes/no):
```

Type `yes` to post, `no` to cancel.

**What to Check:**
- Browser opens and navigates to LinkedIn
- Post appears in the editor
- Post is published successfully
- Check your LinkedIn profile to verify

**Troubleshooting:**
- **Error: "LinkedIn session expired"** → Run `python scripts/setup_linkedin.py`
- **Error: "Post button not found"** → LinkedIn UI changed, check selectors
- **Browser doesn't open** → Set `headless: false` in `config/watcher_config.yaml`

---

## Test 4: LinkedIn Scheduler (Background)

### Test Scheduling Logic

```bash
# Test if scheduler would post now
python -c "
from scripts.linkedin_scheduler import LinkedInScheduler
scheduler = LinkedInScheduler(
    '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
    'silver/config/watcher_config.yaml'
)
print(f'Should post now: {scheduler.should_post_now()}')
print(f'Next topic: {scheduler.get_next_topic()}')
"
```

### Run Scheduler (Continuous)

```bash
# Start LinkedIn scheduler (runs continuously)
python scripts/linkedin_scheduler.py
```

**Expected Output:**
```
Vault path: /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
Config path: /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver/config/watcher_config.yaml
INFO - LinkedIn scheduler initialized
INFO - Starting LinkedIn scheduler...
INFO - Post interval: 86400.0s (24.0 hours)
INFO - Scheduled post time: 9:00
INFO - Topics: AI automation, business productivity, workflow optimization, digital transformation, sales automation
DEBUG - Next post in Xh Xm
```

**To Stop:** Press `Ctrl+C`

---

## Test 5: Run All Watchers Together

### Option A: Individual Terminals (Recommended for Testing)

Open 3 separate terminals and run:

**Terminal 1 - Gmail:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate
python -m src.watchers.gmail_watcher
```

**Terminal 2 - WhatsApp:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate
python -m src.watchers.whatsapp_watcher
```

**Terminal 3 - LinkedIn:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate
python scripts/linkedin_scheduler.py
```

### Option B: Background Processes

```bash
# Start all watchers in background
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate

# Start Gmail watcher
nohup python -m src.watchers.gmail_watcher > ../Logs/gmail_watcher.log 2>&1 &
echo $! > .pids/gmail_watcher.pid

# Start WhatsApp watcher
nohup python -m src.watchers.whatsapp_watcher > ../Logs/whatsapp_watcher.log 2>&1 &
echo $! > .pids/whatsapp_watcher.pid

# Start LinkedIn scheduler
nohup python scripts/linkedin_scheduler.py > ../Logs/linkedin_scheduler.log 2>&1 &
echo $! > .pids/linkedin_scheduler.pid

# Check processes are running
ps aux | grep -E "gmail_watcher|whatsapp_watcher|linkedin_scheduler"
```

### Stop All Background Processes

```bash
# Kill all watchers
kill $(cat .pids/gmail_watcher.pid) 2>/dev/null
kill $(cat .pids/whatsapp_watcher.pid) 2>/dev/null
kill $(cat .pids/linkedin_scheduler.pid) 2>/dev/null

# Or use the shutdown script
./scripts/shutdown.sh
```

---

## Test 6: Check Results

### View Action Files

```bash
# List all action files created
ls -lh ../Needs_Action/

# View a specific file
cat ../Needs_Action/msg_gmail_*.md | head -50
```

### View Logs

```bash
# View Gmail watcher logs
tail -f ../Logs/gmail_watcher.log

# View WhatsApp watcher logs
tail -f ../Logs/whatsapp_watcher.log

# View LinkedIn scheduler logs
tail -f ../Logs/linkedin_scheduler.log
```

### Check LinkedIn Posts

1. Open LinkedIn in browser
2. Go to your profile
3. Check "Activity" section
4. Verify posts appear with correct content

---

## Quick Test Script

Run this to test all components quickly:

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate

echo "=== Testing Gmail Watcher ==="
timeout 30 python -m src.watchers.gmail_watcher || echo "Gmail test completed"

echo ""
echo "=== Testing WhatsApp Watcher ==="
timeout 30 python -m src.watchers.whatsapp_watcher || echo "WhatsApp test completed"

echo ""
echo "=== Testing LinkedIn Content Generation ==="
python -c "from src.watchers.linkedin_poster import LinkedInPoster; p = LinkedInPoster('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault'); print(p.generate_business_post('test'))"

echo ""
echo "=== Checking Results ==="
echo "Action files created:"
ls -lh ../Needs_Action/ | tail -5
```

---

## Troubleshooting Common Issues

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate
pip install google-auth google-api-python-client playwright pyyaml python-dotenv
playwright install chromium
```

### Issue: "Permission denied"

**Solution:**
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

### Issue: Sessions Expired

**Solution:**
```bash
# Re-setup Gmail
python scripts/setup_gmail.py

# Re-setup WhatsApp
python scripts/setup_whatsapp.py

# Re-setup LinkedIn
python scripts/setup_linkedin.py
```

### Issue: No Files Created

**Check:**
1. Vault folders exist: `ls -la ../Needs_Action/`
2. Credentials are valid: `cat config/.env`
3. Watchers are enabled: `cat config/watcher_config.yaml`
4. Check logs for errors: `tail -f ../Logs/*.log`

---

## Success Criteria

✅ Gmail watcher creates files in `Needs_Action/` with email content
✅ WhatsApp watcher creates files with message content
✅ LinkedIn poster successfully publishes posts
✅ LinkedIn scheduler runs continuously and posts daily
✅ All logs show "INFO" level messages, no errors
✅ Sessions remain valid for 7+ days

---

## Next Steps

After successful testing:
1. Configure posting schedule in `config/watcher_config.yaml`
2. Set up approval workflow (see `manage-approvals` skill)
3. Run watchers continuously with `./scripts/startup.sh`
4. Monitor with `python scripts/dashboard.py`

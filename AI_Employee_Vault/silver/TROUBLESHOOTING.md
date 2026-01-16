# Silver Tier Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Silver tier AI assistant.

---

## Quick Diagnostics

### Run Health Check
```bash
python silver/scripts/health_check.py
```

This will check:
- Service status
- Log file errors
- Credentials configuration
- Vault folder structure
- Python packages
- Recent activity

---

## Common Issues

### 1. Gmail Watcher Issues

#### Issue: "Gmail API credentials not configured"

**Symptoms:**
- Gmail watcher fails to start
- Error: "Gmail credentials not configured"

**Solution:**
```bash
# Run Gmail setup script
python silver/scripts/setup_gmail.py

# Follow the prompts to:
# 1. Enter Client ID
# 2. Enter Client Secret
# 3. Complete OAuth2 flow in browser
# 4. Verify credentials saved to .env
```

**Verification:**
```bash
# Check .env file
cat silver/config/.env | grep GMAIL

# Should see:
# GMAIL_CLIENT_ID=...
# GMAIL_CLIENT_SECRET=...
# GMAIL_REFRESH_TOKEN=...
```

---

#### Issue: "Gmail API quota exceeded"

**Symptoms:**
- Error: "Quota exceeded for quota metric"
- Gmail watcher stops fetching messages

**Solution:**
1. Check Gmail API quota in Google Cloud Console
2. Default quota: 1 billion quota units/day (very high)
3. If exceeded, wait 24 hours for reset
4. Consider reducing polling frequency in `watcher_config.yaml`

**Prevention:**
```yaml
# In watcher_config.yaml
gmail:
  poll_interval: 300  # Increase from 300 to 600 seconds
```

---

#### Issue: "No messages detected"

**Symptoms:**
- Gmail watcher running but no action files created
- No errors in logs

**Diagnosis:**
```bash
# Check if watcher is running
ps aux | grep gmail_watcher

# Check logs
tail -f Logs/gmail_watcher.log

# Manually test
python -m silver.src.watchers.gmail_watcher
```

**Common Causes:**
1. **No unread messages**: Send a test email to monitored account
2. **Wrong query**: Check `query` in `watcher_config.yaml`
3. **Deduplication**: Message already processed (check cache)

**Solution:**
```bash
# Send test email to monitored Gmail account
# Wait 5 minutes (poll interval)
# Check Needs_Action/ folder for new file
ls -la Needs_Action/
```

---

### 2. WhatsApp Watcher Issues

#### Issue: "WhatsApp Web not logged in"

**Symptoms:**
- Error: "WhatsApp Web not logged in"
- QR code detection in logs

**Solution:**
```bash
# Run WhatsApp setup script
python silver/scripts/setup_whatsapp.py

# This will:
# 1. Open browser with WhatsApp Web
# 2. Display QR code
# 3. Scan QR code with phone
# 4. Save session for future use
```

**Verification:**
```bash
# Check session directory exists
ls -la silver/.whatsapp_session/

# Should contain browser session files
```

---

#### Issue: "WhatsApp session expired"

**Symptoms:**
- WhatsApp watcher was working, now shows QR code
- Error: "Session expired"

**Solution:**
```bash
# Re-run setup to create new session
python silver/scripts/setup_whatsapp.py

# Scan QR code again with phone
```

**Prevention:**
- Keep WhatsApp Web active on phone
- Don't log out from WhatsApp Web on phone
- Session persists across restarts

---

#### Issue: "Contact not found"

**Symptoms:**
- Error: "Contact not found: [name]"
- WhatsApp sender fails

**Solution:**
1. **Use exact contact name** as shown in WhatsApp
2. **Or use phone number** with country code: "+1234567890"
3. **Check contact exists** in WhatsApp Web

**Example:**
```python
# Good
sender.send_message(to="John Doe", message="Hello")
sender.send_message(to="+1234567890", message="Hello")

# Bad
sender.send_message(to="john", message="Hello")  # Partial name
```

---

### 3. Approval Workflow Issues

#### Issue: "No desktop notifications"

**Symptoms:**
- Approval requests created but no notifications
- Error: "Plyer not installed"

**Solution:**
```bash
# Install plyer
pip install plyer

# Test notification
python -m silver.src.approval.approval_notifier

# Should see test notification in system tray
```

**Platform-Specific:**
- **Linux**: Requires `notify-send` (usually pre-installed)
- **Windows**: Should work out of the box
- **macOS**: Should work out of the box

---

#### Issue: "Approval not detected"

**Symptoms:**
- Changed status to "approved" in file
- Approval checker doesn't detect it

**Diagnosis:**
```bash
# Check approval checker is running
ps aux | grep approval_checker

# Check logs
tail -f Logs/approval_checker.log

# Manually test
python -m silver.src.approval.approval_checker
```

**Solution:**
1. **Verify file format**: YAML frontmatter must be valid
2. **Check status field**: Must be exactly "approved" (lowercase)
3. **Wait for poll**: Checker polls every 10 seconds
4. **Check file location**: Must be in `Pending_Approval/` folder

**Example:**
```yaml
---
id: approval_20260114_143022_send_email
status: approved  # Must be lowercase, no quotes
---
```

---

#### Issue: "Approval timeout"

**Symptoms:**
- Approval request moved to Rejected/ with timeout reason

**Explanation:**
- Each approval has a timeout (default: 24 hours for emails)
- After timeout, request is automatically rejected

**Solution:**
1. **Approve faster**: Check Pending_Approval/ regularly
2. **Increase timeout**: Edit `approval_rules.yaml`
3. **Re-create request**: If needed, create new approval request

**Configuration:**
```yaml
# In approval_rules.yaml
sensitive_actions:
  - action_type: send_email
    timeout_minutes: 2880  # Increase to 48 hours
```

---

### 4. Action Execution Issues

#### Issue: "Email sending failed"

**Symptoms:**
- Error: "Failed to send email"
- Action moved to Failed/ folder

**Common Causes:**
1. **Invalid credentials**: Gmail OAuth2 token expired
2. **Invalid recipient**: Email address format wrong
3. **Network error**: No internet connection
4. **Gmail API error**: Temporary Gmail issue

**Solution:**
```bash
# Test email sending directly
python -m silver.src.actions.email_sender

# Enter test recipient when prompted
# Check if email sends successfully

# If fails, re-run Gmail setup
python silver/scripts/setup_gmail.py
```

---

#### Issue: "WhatsApp sending failed"

**Symptoms:**
- Error: "Failed to send WhatsApp message"
- Action moved to Failed/ folder

**Common Causes:**
1. **Session expired**: Need to re-scan QR code
2. **Contact not found**: Name doesn't match exactly
3. **Browser timeout**: WhatsApp Web took too long to load
4. **Network error**: No internet connection

**Solution:**
```bash
# Test WhatsApp sending directly
python -m silver.src.actions.whatsapp_sender

# Enter test recipient when prompted
# Check if message sends successfully

# If fails, re-run WhatsApp setup
python silver/scripts/setup_whatsapp.py
```

---

### 5. Scheduler Issues

#### Issue: "Scheduled tasks not executing"

**Symptoms:**
- Scheduler running but tasks not executing
- No errors in logs

**Diagnosis:**
```bash
# Check scheduler is running
ps aux | grep scheduler

# Check logs
tail -f Logs/scheduler.log

# Check schedule configuration
cat silver/config/schedules/schedules.yaml
```

**Common Causes:**
1. **No schedules configured**: `schedules.yaml` is empty
2. **Schedules disabled**: `enabled: false` in config
3. **Wrong time format**: Time must be "HH:MM" (24-hour)
4. **Scheduler not started**: Need to start manually

**Solution:**
```bash
# Add test schedule
python -m silver.src.scheduling.schedule_manager

# Or edit schedules.yaml directly
# Then restart scheduler
```

---

#### Issue: "Schedule not persisting"

**Symptoms:**
- Added schedule but it's gone after restart

**Solution:**
- Schedules are saved to `silver/config/schedules/schedules.yaml`
- Check file exists and is writable
- Verify YAML format is valid

**Verification:**
```bash
# Check schedule file
cat silver/config/schedules/schedules.yaml

# Should contain your schedules
```

---

### 6. General System Issues

#### Issue: "Services won't start"

**Symptoms:**
- `startup.sh` fails
- Services start then immediately stop

**Diagnosis:**
```bash
# Check prerequisites
python silver/scripts/health_check.py

# Check Python version
python3 --version  # Should be 3.13+

# Check virtual environment
echo $VIRTUAL_ENV  # Should show venv path

# Check dependencies
pip list | grep google-auth
pip list | grep playwright
```

**Solution:**
```bash
# Install dependencies
pip install -r silver/requirements.txt

# Install Playwright browsers
playwright install chromium

# Activate virtual environment
source venv/bin/activate

# Try starting again
./silver/scripts/startup.sh
```

---

#### Issue: "High CPU usage"

**Symptoms:**
- System slow
- High CPU usage from Python processes

**Common Causes:**
1. **Polling too frequently**: Reduce poll intervals
2. **Too many watchers**: Disable unused watchers
3. **Browser automation**: WhatsApp watcher uses Chromium

**Solution:**
```yaml
# In watcher_config.yaml
gmail:
  poll_interval: 600  # Increase from 300 to 600 seconds

whatsapp:
  poll_interval: 600  # Increase from 300 to 600 seconds
  headless: true      # Ensure headless mode enabled
```

---

#### Issue: "Logs filling up disk"

**Symptoms:**
- Disk space running low
- Large log files in Logs/ folder

**Solution:**
```bash
# Check log sizes
du -sh Logs/*.log

# Rotate logs manually
for log in Logs/*.log; do
    mv "$log" "$log.old"
    touch "$log"
done

# Or set up log rotation
# Create /etc/logrotate.d/silver-tier
```

**Log Rotation Config:**
```
/path/to/vault/Logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In any Python script
from src.utils import setup_logging

setup_logging(log_level="DEBUG", log_format="text")
```

### Check Process Status

```bash
# List all Silver tier processes
ps aux | grep -E "gmail_watcher|whatsapp_watcher|approval_checker|scheduler"

# Check process resource usage
top -p $(pgrep -f gmail_watcher)
```

### Monitor Logs in Real-Time

```bash
# Watch all logs simultaneously
tail -f Logs/*.log

# Or use multitail (if installed)
multitail Logs/gmail_watcher.log Logs/whatsapp_watcher.log
```

### Test Components Individually

```bash
# Test Gmail watcher
python -m silver.src.watchers.gmail_watcher

# Test WhatsApp watcher
python -m silver.src.watchers.whatsapp_watcher

# Test approval workflow
python silver/scripts/test_approval.py

# Test action execution
python silver/scripts/test_actions.py

# Test scheduler
python silver/scripts/test_scheduler.py
```

---

## Getting Help

### Check Documentation

1. **README.md**: Overview and quick start
2. **IMPLEMENTATION_PROGRESS.md**: Implementation status
3. **This file**: Troubleshooting guide

### Check Logs

```bash
# Recent errors
grep -i error Logs/*.log | tail -20

# Recent warnings
grep -i warning Logs/*.log | tail -20

# Specific service
tail -100 Logs/gmail_watcher.log
```

### Run Health Check

```bash
python silver/scripts/health_check.py
```

This provides:
- Service status
- Error summary
- Configuration validation
- Actionable recommendations

---

## Emergency Procedures

### Force Stop All Services

```bash
# Graceful shutdown
./silver/scripts/shutdown.sh

# Force stop if graceful fails
./silver/scripts/shutdown.sh --force

# Or manually
pkill -9 -f gmail_watcher
pkill -9 -f whatsapp_watcher
pkill -9 -f approval_checker
pkill -9 -f scheduler
```

### Reset Everything

```bash
# Stop all services
./silver/scripts/shutdown.sh --force

# Clear PID files
rm -rf silver/.pids/*.pid

# Clear logs (optional)
rm -f Logs/*.log

# Re-run setup
python silver/scripts/setup_gmail.py
python silver/scripts/setup_whatsapp.py

# Start fresh
./silver/scripts/startup.sh
```

### Backup Configuration

```bash
# Backup credentials
cp silver/config/.env silver/config/.env.backup

# Backup schedules
cp silver/config/schedules/schedules.yaml silver/config/schedules/schedules.yaml.backup

# Backup WhatsApp session
tar -czf whatsapp_session_backup.tar.gz silver/.whatsapp_session/
```

---

## Performance Optimization

### Reduce Polling Frequency

```yaml
# In watcher_config.yaml
gmail:
  poll_interval: 600  # 10 minutes instead of 5

whatsapp:
  poll_interval: 600  # 10 minutes instead of 5
```

### Enable Headless Mode

```yaml
# In watcher_config.yaml
whatsapp:
  headless: true  # Reduces resource usage
```

### Limit Log File Size

```python
# In src/utils/logger.py
# Add RotatingFileHandler instead of FileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
```

---

## Contact & Support

For issues not covered in this guide:

1. **Check logs** for detailed error messages
2. **Run health check** for diagnostic information
3. **Review code** in `silver/src/` for implementation details
4. **Test components** individually to isolate issues

---

**Last Updated**: 2026-01-14
**Version**: Silver Tier v1.0

# Silver Tier Quickstart Guide

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Estimated Setup Time**: 30-45 minutes

## Overview

This guide walks you through setting up the Silver tier AI assistant from scratch. By the end, you'll have a functional assistant that monitors Gmail, WhatsApp, and LinkedIn, creates intelligent plans, and executes approved actions.

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Bronze tier complete and working** (100% functionality)
- ✅ **Python 3.13+** installed (`python --version`)
- ✅ **Node.js v24+ LTS** installed (`node --version`)
- ✅ **Git** for version control
- ✅ **Obsidian** v1.10.6+ with vault open
- ✅ **Active accounts**: Gmail, WhatsApp, LinkedIn
- ✅ **30-45 minutes** for setup

---

## Step 1: Install Dependencies

### Python Dependencies

```bash
cd silver/
uv pip install -e .
```

Or using pip:
```bash
cd silver/
pip install -e .
```

This installs:
- Gmail API: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`
- WhatsApp: `playwright`
- LinkedIn: `linkedin-api`
- Scheduling: `schedule`
- Notifications: `plyer`
- Core: `watchdog`, `pyyaml`, `requests`, `python-dotenv`

### Node.js Dependencies (MCP Server)

```bash
cd silver/mcp/email-server/
npm install
```

This installs:
- MCP SDK: `@modelcontextprotocol/sdk`
- Email: `nodemailer`

### Playwright Browser Setup

```bash
playwright install chromium
```

This downloads Chromium browser for WhatsApp Web automation.

---

## Step 2: Configure Credentials

### Create .env File

```bash
cd silver/
cp config/.env.example config/.env
```

Edit `config/.env` with your credentials:

```env
# Gmail API (OAuth2)
GMAIL_CREDENTIALS_PATH=config/gmail_credentials.json
GMAIL_TOKEN_PATH=config/gmail_token.json

# LinkedIn API
LINKEDIN_USERNAME=your-email@example.com
LINKEDIN_PASSWORD=your-password

# SMTP for Email Sending (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# WhatsApp Web Session
WHATSAPP_SESSION_PATH=config/whatsapp_session

# Vault Path
VAULT_PATH=/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
```

**Important**: Add `.env` to `.gitignore` immediately!

```bash
echo "config/.env" >> .gitignore
echo "config/gmail_token.json" >> .gitignore
echo "config/whatsapp_session/" >> .gitignore
```

---

## Step 3: Set Up Gmail API

### 3.1 Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "AI Employee Vault"
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 3.2 Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "AI Employee Vault - Silver Tier"
5. Download credentials JSON
6. Save as `silver/config/gmail_credentials.json`

### 3.3 Authorize Application

```bash
cd silver/
python scripts/setup_gmail.py
```

This will:
- Open browser for OAuth2 consent
- Ask you to sign in to Google
- Request Gmail API permissions
- Save token to `config/gmail_token.json`

**First-time setup**: You'll see a warning "This app isn't verified". Click "Advanced" > "Go to AI Employee Vault (unsafe)" to proceed.

---

## Step 4: Set Up WhatsApp Web

### 4.1 Run WhatsApp Setup Script

```bash
cd silver/
python scripts/setup_whatsapp.py
```

This will:
- Launch Chromium browser
- Navigate to WhatsApp Web
- Display QR code
- Wait for you to scan with your phone

### 4.2 Scan QR Code

1. Open WhatsApp on your phone
2. Tap "Settings" > "Linked Devices"
3. Tap "Link a Device"
4. Scan the QR code displayed in browser

### 4.3 Verify Session

The script will:
- Wait for successful login
- Save session data to `config/whatsapp_session/`
- Close browser
- Confirm setup complete

**Important**: Keep your phone connected to internet. WhatsApp Web requires phone to be online.

---

## Step 5: Set Up LinkedIn API

### 5.1 LinkedIn Credentials

LinkedIn doesn't have an official API for personal accounts. We use the unofficial `linkedin-api` library.

**Option 1: Username/Password** (stored in .env):
```env
LINKEDIN_USERNAME=your-email@example.com
LINKEDIN_PASSWORD=your-password
```

**Option 2: Session Cookies** (more secure):
```bash
cd silver/
python scripts/setup_linkedin.py
```

This will:
- Prompt for LinkedIn credentials
- Authenticate and save session cookies
- Store in `config/linkedin_session.json`

**Security Note**: LinkedIn may flag automated access. Use at your own risk. Consider creating a separate LinkedIn account for testing.

---

## Step 6: Configure SMTP for Email Sending

### Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Google account
2. Generate App Password:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click "2-Step Verification"
   - Scroll to "App passwords"
   - Generate password for "Mail" on "Other (Custom name)"
   - Name it "AI Employee Vault"
3. Copy the 16-character password
4. Add to `.env`:
   ```env
   SMTP_USER=your-email@gmail.com
   SMTP_PASS=abcd efgh ijkl mnop  # App password
   ```

### Test SMTP Connection

```bash
cd silver/
python scripts/test_smtp.py
```

This will:
- Connect to SMTP server
- Send test email to yourself
- Verify delivery
- Confirm setup complete

---

## Step 7: Configure Watchers

Edit `silver/config/watcher_config.yaml`:

```yaml
watchers:
  - id: gmail-watcher
    type: gmail
    enabled: true
    check_interval: 300  # 5 minutes
    config:
      query: "is:unread is:important"
      max_results: 10

  - id: whatsapp-watcher
    type: whatsapp
    enabled: true
    check_interval: 300  # 5 minutes
    config:
      urgent_keywords: ["urgent", "asap", "important", "help"]

  - id: linkedin-watcher
    type: linkedin
    enabled: true
    check_interval: 900  # 15 minutes
    config:
      check_messages: true
      check_notifications: false
```

**Customization**:
- Adjust `check_interval` (minimum 300 seconds)
- Modify Gmail query (e.g., `from:boss@company.com`)
- Add WhatsApp urgent keywords
- Enable/disable LinkedIn notifications

---

## Step 8: Configure Approval Rules

Edit `silver/config/approval_rules.yaml`:

```yaml
sensitive_actions:
  email_send:
    always_approve: true
    exceptions:
      - condition: "recipient in known_contacts"
        auto_approve: false  # Still require approval for now

  linkedin_post:
    always_approve: true
    exceptions: []

  payment:
    always_approve: true
    exceptions: []

  file_delete:
    always_approve: true
    exceptions: []

auto_expire_hours: 24
notification_enabled: true
polling_interval: 30  # seconds
```

**Security Note**: Start with `always_approve: true` for all actions. Relax rules only after testing.

---

## Step 9: Start MCP Email Server

### 9.1 Start Server

```bash
cd silver/mcp/email-server/
node index.js
```

You should see:
```
MCP Email Server started on port 3000
SMTP connection verified: smtp.gmail.com:587
Ready to send emails
```

### 9.2 Test MCP Server

In another terminal:
```bash
cd silver/
python scripts/test_mcp.py
```

This will:
- Connect to MCP server
- Send test email
- Verify delivery
- Confirm MCP working

### 9.3 Run as Background Service

**Using PM2** (recommended):
```bash
cd silver/mcp/email-server/
pm2 start index.js --name mcp-email
pm2 save
pm2 startup  # Auto-start on boot
```

**Using systemd** (Linux):
```bash
sudo cp silver/scripts/mcp-email.service /etc/systemd/system/
sudo systemctl enable mcp-email
sudo systemctl start mcp-email
sudo systemctl status mcp-email
```

---

## Step 10: Start Watchers

### 10.1 Test Watchers Individually

**Gmail Watcher**:
```bash
cd silver/
python -m src.watchers.gmail_watcher
```

Send yourself a test email and verify it's detected.

**WhatsApp Watcher**:
```bash
cd silver/
python -m src.watchers.whatsapp_watcher
```

Send yourself a WhatsApp message and verify it's detected.

**LinkedIn Watcher**:
```bash
cd silver/
python -m src.watchers.linkedin_watcher
```

Send yourself a LinkedIn message and verify it's detected.

### 10.2 Start All Watchers

```bash
cd silver/
./scripts/start_watchers.sh
```

This will:
- Start all enabled watchers
- Run in background
- Log to `Logs/watchers.log`

### 10.3 Verify Watchers Running

```bash
ps aux | grep watcher
```

You should see 3 processes (gmail, whatsapp, linkedin).

---

## Step 11: Start Approval Checker

```bash
cd silver/
python -m src.approval.approval_checker
```

This will:
- Poll `/Pending_Approval` every 30 seconds
- Detect approval status changes
- Execute approved actions
- Send desktop notifications

**Run as background service**:
```bash
pm2 start "python -m src.approval.approval_checker" --name approval-checker
pm2 save
```

---

## Step 12: Configure Scheduling

### Linux/macOS (cron)

```bash
cd silver/
./scripts/setup_scheduling.sh
```

This will add cron jobs:
```cron
# Start watchers on boot
@reboot /path/to/silver/scripts/start_watchers.sh

# Restart watchers daily (for stability)
0 3 * * * /path/to/silver/scripts/restart_watchers.sh
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task: "AI Employee Watchers"
3. Trigger: "When the computer starts"
4. Action: "Start a program"
5. Program: `C:\path\to\silver\scripts\start_watchers.bat`
6. Finish

---

## Step 13: Verify Setup

### 13.1 Check Dashboard

Open `Dashboard.md` in Obsidian. You should see:
- Watcher status: ✅ Running
- Last check: Recent timestamp
- Pending approvals: 0

### 13.2 Send Test Messages

1. **Gmail**: Send yourself an important email
2. **WhatsApp**: Send yourself a message with "urgent"
3. **LinkedIn**: Send yourself a LinkedIn message

Wait 5-15 minutes (depending on check intervals).

### 13.3 Verify Detection

Check `Needs_Action/` folder:
- Should have 3 new MESSAGE_*.md files
- Each with proper YAML frontmatter
- Content extracted correctly

### 13.4 Test Approval Workflow

1. Create test approval request:
   ```bash
   cd silver/
   python scripts/test_approval.py
   ```

2. Check `Pending_Approval/` folder
3. Open approval request in Obsidian
4. Change `status: pending` to `status: approved`
5. Save file
6. Wait 30 seconds
7. Check `Approved/` folder - file should move
8. Check `Logs/` - should have audit log entry

### 13.5 Test Email Sending

1. Approve test email from previous step
2. Wait for execution
3. Check your inbox for test email
4. Verify messageId in audit log

---

## Step 14: Create Agent Skills

Agent Skills are already implemented in `.claude/skills/`. Verify they exist:

```bash
ls -la .claude/skills/
```

You should see:
- `process-files/` (Bronze tier)
- `monitor-communications/` (Silver tier)
- `manage-approvals/` (Silver tier)
- `post-linkedin/` (Silver tier)
- `create-plans/` (Silver tier)
- `execute-actions/` (Silver tier)

Test a skill:
```bash
claude-code --skill monitor-communications
```

---

## Troubleshooting

### Gmail API Errors

**Error**: "The user has not granted the app..."
**Solution**: Re-run `python scripts/setup_gmail.py` and grant permissions

**Error**: "Quota exceeded"
**Solution**: Wait 24 hours or increase quota in Google Cloud Console

### WhatsApp Web Issues

**Error**: "QR code expired"
**Solution**: Re-run `python scripts/setup_whatsapp.py`

**Error**: "Phone not connected"
**Solution**: Ensure your phone is online and WhatsApp is running

### LinkedIn Authentication

**Error**: "Challenge required"
**Solution**: LinkedIn detected automation. Log in manually via browser, then retry.

**Error**: "Account restricted"
**Solution**: LinkedIn flagged your account. Wait 24 hours or use different account.

### MCP Server Not Starting

**Error**: "Port 3000 already in use"
**Solution**: Kill existing process: `lsof -ti:3000 | xargs kill -9`

**Error**: "SMTP authentication failed"
**Solution**: Verify app password in `.env`, regenerate if needed

### Watchers Not Detecting Messages

**Error**: No files in `Needs_Action/`
**Solution**:
1. Check watcher logs: `tail -f Logs/watchers.log`
2. Verify credentials in `.env`
3. Test watcher individually (see Step 10.1)
4. Check `check_interval` is >= 300 seconds

### Approval Workflow Not Working

**Error**: Approved actions not executing
**Solution**:
1. Verify approval checker is running: `ps aux | grep approval_checker`
2. Check polling interval in `approval_rules.yaml`
3. Verify MCP server is running
4. Check audit logs for errors

---

## Next Steps

Now that Silver tier is set up:

1. **Test thoroughly**: Send various messages, create approvals, verify execution
2. **Monitor logs**: Check `Logs/` daily for errors
3. **Adjust configuration**: Fine-tune check intervals, approval rules
4. **Create plans**: Use Claude Code to create Plan.md files for complex tasks
5. **Post on LinkedIn**: Test automated LinkedIn posting with approval
6. **Review Dashboard**: Check system status daily

---

## Daily Operations

### Morning Routine

1. Check Dashboard.md for overnight activity
2. Review pending approvals in `/Pending_Approval`
3. Check logs for errors: `tail -100 Logs/$(date +%Y-%m-%d).json`
4. Verify watchers running: `ps aux | grep watcher`

### Weekly Maintenance

1. Review audit logs for patterns
2. Rotate credentials (monthly)
3. Update dependencies: `uv pip install --upgrade -e .`
4. Backup vault: `git commit -am "Weekly backup"`
5. Test approval workflow end-to-end

---

## Security Checklist

- ✅ `.env` file is gitignored
- ✅ Gmail uses app-specific password (not account password)
- ✅ WhatsApp session is encrypted
- ✅ LinkedIn credentials are secure
- ✅ SMTP credentials are secure
- ✅ All sensitive actions require approval
- ✅ Audit logs are enabled
- ✅ Credentials rotate monthly

---

## Performance Benchmarks

After setup, you should see:

- **Gmail watcher**: Detects messages within 5 minutes
- **WhatsApp watcher**: Detects messages within 5 minutes
- **LinkedIn watcher**: Detects messages within 15 minutes
- **Approval checker**: Responds within 30 seconds
- **Email sending**: Completes within 5 seconds
- **Memory usage**: < 500MB total (all watchers + MCP)
- **CPU usage**: < 5% when idle

---

## Support

If you encounter issues:

1. Check logs: `Logs/$(date +%Y-%m-%d).json`
2. Review troubleshooting section above
3. Test components individually
4. Check constitution compliance
5. Verify Bronze tier is working

---

**Setup Status**: Ready to start
**Estimated Time**: 30-45 minutes
**Difficulty**: Intermediate

Good luck with your Silver tier setup! 🚀

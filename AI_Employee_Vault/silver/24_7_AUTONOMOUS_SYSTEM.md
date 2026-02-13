# 24/7 Autonomous AI Employee System

**Status**: ✅ Production Ready
**Last Updated**: 2026-02-14

---

## 🎯 What This System Does

Your AI Employee runs **24/7 in the background** and:

1. **Monitors** Gmail/WhatsApp every 2 minutes for new messages
2. **Detects** incoming messages → Creates files in `Needs_Action/`
3. **Generates** AI replies every 5 minutes → Creates files in `Pending_Approval/`
4. **Waits** for your approval in Obsidian
5. **Executes** automatically when you drag to `Approved/`
6. **Sends** WhatsApp/Email replies automatically

**YOU ONLY USE OBSIDIAN** - No manual script running needed!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Daemon

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/run_daemon.py
```

### Step 2: Open Obsidian

Open your AI_Employee_Vault in Obsidian and watch the folders:
- `Needs_Action/` - Incoming messages
- `Pending_Approval/` - AI-generated replies waiting for your review
- `Approved/` - Drag files here to send
- `Done/` - Completed actions

### Step 3: Review & Approve

When AI generates a reply:
1. Open the file in `Pending_Approval/`
2. Review the suggested reply
3. Edit if needed
4. **Drag to `Approved/`** to send automatically

**That's it!** The system handles everything else.

---

## 🔄 Complete Workflow

```
📧 Client sends WhatsApp message
         ↓
📁 Watcher detects (every 2 min) → Needs_Action/msg_whatsapp_abc123.md
         ↓
🧠 Orchestrator runs (every 5 min) → Generates AI reply
         ↓
📝 Creates approval file → Pending_Approval/approval_20260214_123456_reply_whatsapp.md
         ↓
👤 YOU review in Obsidian
         ↓
✅ YOU drag to Approved/
         ↓
🚀 Daemon detects (instant) → Opens WhatsApp Web → Sends reply
         ↓
✅ Moves to Done/ → Client receives reply
```

**Total time from client message to reply sent:** 2-7 minutes (depending on timing) + your review time

---

## 🌙 Running 24/7 in Background

### Option 1: Using `screen` (Recommended for WSL)

**Start daemon in background:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate

# Create a screen session
screen -S ai_employee

# Run daemon
python silver/scripts/run_daemon.py

# Detach: Press Ctrl+A, then D
```

**Check if running:**
```bash
screen -ls
```

**Reattach to see logs:**
```bash
screen -r ai_employee
```

**Stop daemon:**
```bash
# Reattach first
screen -r ai_employee

# Then press Ctrl+C
```

---

### Option 2: Using `tmux`

**Start daemon:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate

# Create tmux session
tmux new -s ai_employee

# Run daemon
python silver/scripts/run_daemon.py

# Detach: Press Ctrl+B, then D
```

**Reattach:**
```bash
tmux attach -t ai_employee
```

---

### Option 3: Using `nohup` (Simple)

**Start daemon:**
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate

nohup python silver/scripts/run_daemon.py > daemon.log 2>&1 &
```

**Check logs:**
```bash
tail -f daemon.log
```

**Stop daemon:**
```bash
# Find process ID
ps aux | grep run_daemon.py

# Kill it
kill <PID>
```

---

## 📊 Monitoring

### Check Daemon Status

**If using screen:**
```bash
screen -ls
# Should show: ai_employee (Attached/Detached)
```

**If using nohup:**
```bash
ps aux | grep run_daemon.py
# Should show the running process
```

### View Real-Time Logs

**If using screen:**
```bash
screen -r ai_employee
# You'll see live output
```

**If using nohup:**
```bash
tail -f daemon.log
```

### Check Activity

**In Obsidian:**
- `Needs_Action/` - New messages appear here
- `Pending_Approval/` - AI replies appear here
- `Done/` - Completed actions

**Expected output in logs:**
```
[01:23:45] 📧 Checking Gmail...
   ✅ Found 2 new email(s)
      Created: msg_gmail_abc123.md
      Created: msg_gmail_def456.md

[01:25:00] 🧠 Running AI Orchestrator...
   ✅ Processed 2 message(s)

🔔 NEW APPROVAL DETECTED: approval_20260214_012500_reply_email.md
📧 Processing email reply: approval_20260214_012500_reply_email.md
   To: client@example.com
   Subject: Re: Your inquiry
✅ Email sent successfully!
   Moved to: Done/approval_20260214_012500_reply_email.md
```

---

## 🛠️ Configuration

### Timing Settings

Edit `silver/scripts/run_daemon.py`:

```python
self.check_interval = 120  # Gmail/WhatsApp check (seconds)
self.orchestrator_interval = 300  # AI reply generation (seconds)
```

**Recommended:**
- `check_interval`: 120 (2 minutes) - Balance between responsiveness and API limits
- `orchestrator_interval`: 300 (5 minutes) - Gives time for messages to accumulate

### WhatsApp Session

If WhatsApp session expires:
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/setup_whatsapp.py
```

### Gmail OAuth

If Gmail token expires:
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/setup_gmail.py
```

### Keyword Filtering (Smart Message Prioritization)

**Problem:** You have 133 unread WhatsApp messages. Without filtering, all 133 would create files in Needs_Action and Pending_Approval = folder chaos!

**Solution:** Keyword filtering only processes messages containing priority keywords like "urgent", "fast", "important", etc.

**Configuration:** Edit `silver/config/watcher_config.yaml`

```yaml
whatsapp:
  keyword_filter:
    enabled: true  # Set to false to process ALL messages
    keywords:
      - "urgent"
      - "fast"
      - "important"
      - "asap"
      - "help"
      - "priority"
      - "emergency"
      - "critical"
      - "immediate"
      - "quick"
      - "now"
      - "please"
    case_sensitive: false
```

**Result:**
- ✅ Only messages with keywords are processed
- ✅ Clean folders (10 priority messages instead of 133)
- ✅ Focus on what matters
- ❌ Messages without keywords stay unread (you can check manually later)

**See full documentation:** `silver/KEYWORD_FILTERING.md`

---

## 🎯 Your Daily Workflow

### Morning (5 minutes)

1. **Start daemon** (if not already running):
   ```bash
   screen -S ai_employee
   cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
   source silver/.venv/bin/activate
   python silver/scripts/run_daemon.py
   # Ctrl+A, D to detach
   ```

2. **Open Obsidian** - Keep it open all day

### Throughout the Day (As needed)

1. **Check `Pending_Approval/`** folder in Obsidian
2. **Review AI-generated replies**
3. **Edit if needed**
4. **Drag to `Approved/`** to send

**That's it!** The system handles:
- Detecting new messages
- Generating replies
- Sending approved replies
- Moving files to Done/

### Evening (1 minute)

**Optional:** Stop daemon if you want:
```bash
screen -r ai_employee
# Press Ctrl+C
```

**Or leave it running 24/7!**

---

## 🚨 Troubleshooting

### Daemon Not Detecting Messages

**Check:**
1. Is daemon running? `screen -ls` or `ps aux | grep run_daemon`
2. Are credentials valid? Check logs for "expired" or "invalid"
3. Is WhatsApp session active? Run `python silver/scripts/setup_whatsapp.py`

### AI Not Generating Replies

**Check:**
1. Are there files in `Needs_Action/`?
2. Is orchestrator running? Check logs for "🧠 Running AI Orchestrator"
3. Wait 5 minutes - orchestrator runs every 5 minutes

### Replies Not Sending

**Check:**
1. Did you drag file to `Approved/`? (Not just move, must be in Approved/)
2. Is daemon watching Approved/? Check logs for "👀 Watching"
3. Are credentials valid? Check logs for errors

### WhatsApp Messages Not Delivering

**Check:**
1. Is session valid? Browser should open and show logged-in WhatsApp
2. Is chat syncing? Wait 15-20 seconds after opening chat
3. Check logs for "✅ Message sent! Keeping browser open for 20s"

---

## 📈 Performance

**Expected Response Times:**
- Message detection: 0-2 minutes (depends on check interval)
- AI reply generation: 0-5 minutes (depends on orchestrator interval)
- Reply sending: Instant (when you approve)

**Total time:** 2-7 minutes + your review time

**Resource Usage:**
- CPU: ~5% when idle, ~20% when processing
- RAM: ~200MB
- Network: Minimal (only when checking/sending)

---

## 🎓 Advanced: Systemd Service (Linux)

For true 24/7 operation that survives reboots:

**Create service file:**
```bash
sudo nano /etc/systemd/system/ai-employee.service
```

**Content:**
```ini
[Unit]
Description=AI Employee Daemon
After=network.target

[Service]
Type=simple
User=hamza
WorkingDirectory=/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
ExecStart=/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver/.venv/bin/python silver/scripts/run_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable ai-employee
sudo systemctl start ai-employee
```

**Check status:**
```bash
sudo systemctl status ai-employee
```

**View logs:**
```bash
sudo journalctl -u ai-employee -f
```

---

## ✅ Success Checklist

- [ ] Daemon running in background (screen/tmux/nohup)
- [ ] Obsidian open with AI_Employee_Vault
- [ ] Gmail credentials configured
- [ ] WhatsApp session active
- [ ] Test message sent and detected
- [ ] AI reply generated in Pending_Approval/
- [ ] Approved reply sent successfully
- [ ] File moved to Done/

**If all checked:** 🎉 Your 24/7 AI Employee is operational!

---

## 📞 Support

**Check logs first:**
- Daemon logs: `screen -r ai_employee` or `tail -f daemon.log`
- Silver tier logs: `tail -f silver/Logs/*.log`

**Common issues:**
- Session expired → Re-run setup scripts
- Not detecting → Check timing intervals
- Not sending → Check Approved/ folder and credentials

---

**System Version:** Silver Tier + Gold Tier (Ralph Wiggum)
**Last Updated:** 2026-02-14
**Status:** ✅ Production Ready - 24/7 Autonomous Operation

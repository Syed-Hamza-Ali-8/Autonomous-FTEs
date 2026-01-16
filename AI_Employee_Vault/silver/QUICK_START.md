# Silver Tier Quick Start Guide

**Status**: Ready for Credential Configuration
**Time Required**: 30-45 minutes
**Date**: 2026-01-14

---

## 🚀 Quick Deployment (3 Commands)

### Step 1: Configure Gmail OAuth2 (15-20 min)
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/setup_gmail.py
```

**You'll need**:
- Google Cloud Project with Gmail API enabled
- OAuth2 Client ID and Client Secret
- Browser access for authorization

**Get credentials**: https://console.cloud.google.com/

---

### Step 2: Configure WhatsApp Web (5-10 min)
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/setup_whatsapp.py
```

**You'll need**:
- WhatsApp on your mobile device
- Ability to scan QR code

---

### Step 3: Start All Services (2 min)
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
./silver/scripts/startup.sh
```

**Services started**:
- Gmail Watcher (monitors inbox every 5 minutes)
- WhatsApp Watcher (monitors messages every 5 minutes)
- Approval Checker (polls every 10 seconds)
- Scheduler (runs scheduled tasks)

---

## ✅ Verify Deployment

### Check System Health
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/health_check.py
```

**Expected**: All services running, all checks green

---

### Monitor Real-Time
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source silver/.venv/bin/activate
python silver/scripts/dashboard.py
```

**Shows**: Service status, activity metrics, errors, system resources

---

### Watch Logs
```bash
# All logs
tail -f Logs/*.log

# Specific service
tail -f Logs/gmail_watcher.log
```

---

## 🧪 Test the System

### Test 1: Gmail Monitoring
1. Send email to your monitored Gmail account
2. Wait 5 minutes
3. Check: `ls -lh Needs_Action/`
4. Expected: New action file created

### Test 2: Approval Workflow
1. Check: `ls -lh Pending_Approval/`
2. Open approval file, change `status: pending` to `status: approved`
3. Wait 10 seconds
4. Check: `ls -lh Approved/`
5. Expected: File moved to Approved/

### Test 3: Action Execution
1. Approve an email action
2. Wait 1 minute
3. Check: `ls -lh Done/`
4. Verify: Email received by recipient

---

## 🛑 Stop Services

### Graceful Shutdown
```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
./silver/scripts/shutdown.sh
```

### Force Stop
```bash
./silver/scripts/shutdown.sh --force
```

---

## 📚 Full Documentation

- **Deployment Checklist**: `silver/DEPLOYMENT_CHECKLIST.md` (comprehensive guide)
- **Deployment Guide**: `silver/DEPLOYMENT_GUIDE.md` (detailed instructions)
- **Troubleshooting**: `silver/TROUBLESHOOTING.md` (1,000+ lines)
- **README**: `silver/README.md` (overview)

---

## 🆘 Quick Troubleshooting

### Services Won't Start
```bash
source silver/.venv/bin/activate
uv pip install google-auth google-api-python-client playwright schedule plyer pyyaml mcp
playwright install chromium
./silver/scripts/startup.sh
```

### Gmail Not Working
```bash
# Re-run setup
python silver/scripts/setup_gmail.py
```

### WhatsApp Session Expired
```bash
# Re-run setup
python silver/scripts/setup_whatsapp.py
```

### Check Logs for Errors
```bash
tail -100 Logs/gmail_watcher.log
tail -100 Logs/whatsapp_watcher.log
tail -100 Logs/approval_checker.log
```

---

## 📊 What's Already Done

✅ All code complete (19,800+ lines)
✅ All tests passing (16/16 = 100%)
✅ All documentation complete
✅ .env file created
✅ Virtual environment ready
✅ Dependencies installed
✅ MCP server tested
✅ Startup scripts verified

---

## ⏳ What You Need to Do

1. **Gmail OAuth2** (15-20 min) - Run `python silver/scripts/setup_gmail.py`
2. **WhatsApp Session** (5-10 min) - Run `python silver/scripts/setup_whatsapp.py`
3. **Start Services** (2 min) - Run `./silver/scripts/startup.sh`
4. **Verify & Monitor** (ongoing) - Run `python silver/scripts/dashboard.py`

**Total Time**: 30-45 minutes

---

## 🎯 Success Criteria

Deployment is successful when:
- ✅ All 4 services running
- ✅ Health check all green
- ✅ Test email detected in Needs_Action/
- ✅ Approval workflow functional
- ✅ Email sent successfully
- ✅ No errors in logs

---

**Quick Start Version**: 1.0
**Date**: 2026-01-14
**Status**: Ready to Deploy

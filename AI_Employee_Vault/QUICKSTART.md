# 🚀 Quick Start Guide - AI Employee Vault

**Last Updated**: 2026-02-06
**Silver Tier Status**: ✅ 100% Complete
**Architecture**: Autonomous AI Employee with Human-in-the-Loop Approval

---

## 📖 What is AI Employee Vault?

An **autonomous AI Employee** that monitors your communications (Gmail, WhatsApp, LinkedIn), creates actionable tasks in Obsidian, requests human approval for sensitive actions, and executes approved actions automatically.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: WATCHERS (Perception)                         │
│  Gmail → WhatsApp → LinkedIn                            │
│  Monitor communications → Create action files           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: OBSIDIAN (Dashboard)                          │
│  Needs_Action/ → Pending_Approval/ → Approved/ → Done/  │
│  Review tasks in your Obsidian vault                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: HUMAN-IN-THE-LOOP (Approval)                  │
│  Review approval requests → Approve/Reject              │
│  Drag files to Approved/ folder                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 4: EXECUTION (Action)                            │
│  Approval checker detects approved actions              │
│  Executes: Send email, Post LinkedIn, Send WhatsApp     │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.13+** (Silver Tier uses Python 3.14)
- ✅ **Git** installed
- ✅ **Obsidian** (for dashboard and task management)
- ✅ **Gmail account** (for email monitoring)
- ✅ **WhatsApp account** (for messaging automation)
- ✅ **LinkedIn account** (for posting automation)
- ✅ **Terminal/Command line** access

---

## 🎯 Quick Start Options

Choose your path:

### Option A: Complete Workflow Test (Recommended)
**Time**: 5 minutes
**Purpose**: See the entire autonomous system in action
**Best for**: First-time users, demos, understanding the full workflow

### Option B: Individual Component Testing
**Time**: 2-3 minutes per component
**Purpose**: Test specific features (Gmail, WhatsApp, LinkedIn)
**Best for**: Debugging, verifying specific integrations

### Option C: Production Mode
**Time**: 10 minutes setup, then runs 24/7
**Purpose**: Run the AI Employee continuously
**Best for**: Daily use, production deployment

---

## 🚀 Option A: Complete Workflow Test (Recommended)

This demonstrates the **full autonomous workflow** from monitoring to execution.

### Step 1: Activate Virtual Environment

```bash
# Navigate to project directory
cd /path/to/AI_Employee_Vault

# Activate Silver Tier virtual environment
source silver/.venv/bin/activate

# You should see (silver) prefix in your terminal
```

### Step 2: Run Complete Workflow Test

```bash
python silver/scripts/test_complete_workflow.py
```

### What This Does

The script will:

1. **Monitor Gmail** → Find new emails → Create action files in `Needs_Action/`
2. **Monitor WhatsApp** → Find unread messages → Create action files
3. **Generate LinkedIn Post** → Create approval request in `Pending_Approval/`
4. **Wait for Your Approval** → You review and approve in Obsidian
5. **Execute Actions** → Post to LinkedIn, send messages automatically

### Expected Output

```
================================================================================
  🤖 AI EMPLOYEE - COMPLETE WORKFLOW TEST
================================================================================

PHASE 1: WATCHERS (Monitoring)
────────────────────────────────────────────────────────────────────────────────
STEP 1: GMAIL WATCHER - Monitoring Inbox
📧 Checking Gmail inbox for new messages...
✅ Found 1 new email(s)
   1. Created: msg_gmail_39006bc42a73.md
      From: Google <no-reply@accounts.google.com>
      Subject: Security alert

STEP 2: WHATSAPP WATCHER - Monitoring Messages
💬 Checking WhatsApp Web for unread messages...
✅ Found 0 new messages

STEP 3: LINKEDIN POSTER - Creating Approval Request
🔵 Generating LinkedIn post content...
✅ Created approval request: approval_20260206_232242_post_linkedin.md

PHASE 2: OBSIDIAN (Dashboard Review)
────────────────────────────────────────────────────────────────────────────────
📊 Open Obsidian and navigate to AI_Employee_Vault/
✅ Needs_Action/ folder: 1 new email file(s)
✅ Pending_Approval/ folder: 1 LinkedIn post approval request

Press Enter after you've reviewed the files in Obsidian...

PHASE 3: APPROVAL (Human-in-the-Loop)
────────────────────────────────────────────────────────────────────────────────
⏳ Waiting for you to approve the LinkedIn post in Obsidian...
Instructions:
  1. Open Obsidian
  2. Go to Pending_Approval/ folder
  3. Drag the approval file to Approved/ folder

Press Enter after you've moved the file to Approved/ folder...

PHASE 4: EXECUTION (Automated Actions)
────────────────────────────────────────────────────────────────────────────────
✅ Found 1 approved LinkedIn post(s)
🚀 Posting to LinkedIn...
✅ Post successful!

================================================================================
  ✅ WORKFLOW TEST COMPLETE
================================================================================
```

### Step 3: Verify Results

1. **Check Obsidian**:
   - `Needs_Action/` → Email files created
   - `Done/` → Completed actions moved here

2. **Check LinkedIn**:
   - Visit your LinkedIn profile
   - Verify the post appeared

3. **Check Logs**:
   - `Logs/` folder contains detailed execution logs

---

## 🔧 Option B: Individual Component Testing

Test specific components independently.

### Activate Virtual Environment

```bash
cd /path/to/AI_Employee_Vault
source silver/.venv/bin/activate
```

### Test 1: Gmail Watcher

```bash
python silver/scripts/test_gmail_connection.py
```

**What it does**: Connects to Gmail API, counts messages, verifies access

**Expected output**:
```
✅ Gmail API connection successful!
   Total messages: 6,287
   Unread messages: 5
```

---

### Test 2: WhatsApp Sender

**Important**: WhatsApp messages now wait for chat to fully load before sending (10-60 seconds). This ensures **immediate delivery** to recipients.

```bash
# Option A: Send to specific contact
python silver/scripts/test_whatsapp_timing.py

# Option B: Quick test (hardcoded recipient)
python silver/scripts/test_whatsapp_simple.py
```

**What it does**:
- Opens WhatsApp Web
- Waits for chat to fully load (10-60 seconds)
- Sends message
- Confirms delivery

**Expected output**:
```
1. Opening browser...
2. Going to WhatsApp Web...
3. Waiting for WhatsApp to load...
   ✅ WhatsApp Web loaded successfully
4. Contact selected: Ubaid GIAIC, waiting for chat to load...
   Waiting for chat to fully load (this may take 10-60 seconds)...
   ✅ Message input box visible
   Chat still loading messages... (10s elapsed)
   Chat still loading messages... (20s elapsed)
   ✅ Chat fully loaded and ready to send (25s)
5. Sending message...
   ✅ Message sent
   ✅ Message delivery confirmed

✅ WhatsApp message sent successfully!
```

**Why the wait?** WhatsApp Web syncs chat history when opening a conversation. If we send during sync, the message gets queued and delayed. By waiting for the chat to fully load, messages are delivered **immediately**.

#### Find Available Contacts

```bash
python silver/scripts/list_whatsapp_contacts_v2.py
```

**Output**: Lists all WhatsApp contacts with exact names (including emojis)

---

### Test 3: LinkedIn Poster

```bash
# Dry-run mode (no actual posting)
python silver/scripts/test_linkedin.py --dry-run

# Actual posting
python silver/scripts/test_linkedin.py
```

**What it does**: Generates business content, posts to LinkedIn

**Expected output**:
```
============================================================
LinkedIn Poster Test
============================================================

1️⃣  Initializing LinkedIn poster...
   ✅ LinkedIn poster initialized
   ✅ Session found at: silver/config/linkedin_session

2️⃣  Generating business content...
   ✅ Generated content for topic: digital transformation

------------------------------------------------------------
📊 Quick update on our digital transformation initiative:

✅ Streamlined communication workflows
✅ Reduced manual tasks by 70%
✅ Improved response times

Ready to transform your business operations? DM me to learn more!

#Automation #Efficiency #Sales
------------------------------------------------------------

✅ Post successful!
```

---

## 🏭 Option C: Production Mode (Continuous Operation)

Run the AI Employee continuously to monitor and act on your behalf.

### Step 1: Activate Virtual Environment

```bash
cd /path/to/AI_Employee_Vault
source silver/.venv/bin/activate
```

### Step 2: Start Approval Checker (Required)

The approval checker monitors `Pending_Approval/` folder and executes approved actions.

```bash
# Start in foreground (see logs in real-time)
python -m silver.src.approval.approval_checker

# Or start in background
python -m silver.src.approval.approval_checker &
```

**What it does**:
- Polls `Pending_Approval/` every 10 seconds
- Detects when you approve actions (move files to `Approved/`)
- Executes approved actions automatically
- Moves completed actions to `Done/`

**Expected output**:
```
2026-02-06 23:21:49 - INFO - Approval checker started
2026-02-06 23:21:49 - INFO - Monitoring: /path/to/AI_Employee_Vault/Pending_Approval
2026-02-06 23:21:49 - INFO - Polling every 10 seconds...
2026-02-06 23:21:59 - INFO - Checking for approved actions...
2026-02-06 23:21:59 - INFO - No approved actions found
```

### Step 3: Start Watchers (Optional)

Run watchers to continuously monitor communications:

```bash
# Gmail watcher (monitors inbox every 2 minutes)
python -m silver.src.watchers.gmail_watcher &

# WhatsApp watcher (monitors messages every 30 seconds)
python -m silver.src.watchers.whatsapp_watcher &

# LinkedIn scheduler (posts daily at 9 AM)
python silver/scripts/linkedin_scheduler.py &
```

### Step 4: Use Obsidian as Your Dashboard

1. **Open Obsidian** and navigate to `AI_Employee_Vault/`
2. **Monitor folders**:
   - `Needs_Action/` → New tasks from watchers
   - `Pending_Approval/` → Actions waiting for your approval
   - `Approved/` → Actions you've approved (auto-executed)
   - `Done/` → Completed actions
3. **Approve actions**: Drag files from `Pending_Approval/` to `Approved/`
4. **Review Dashboard.md**: See summary of recent activity

### Step 5: Stop Services

```bash
# Find running processes
ps aux | grep python

# Kill specific process
kill <PID>

# Or kill all Python processes (careful!)
pkill -f "approval_checker"
pkill -f "gmail_watcher"
pkill -f "whatsapp_watcher"
```

---

## 📊 How the HITL Approval Workflow Works

### 1. System Creates Approval Request

When a watcher detects an action that needs approval (e.g., send email, post LinkedIn), it creates a file in `Pending_Approval/`:

```yaml
---
type: approval_request
action: post_linkedin
status: pending
created: 2026-02-06T23:22:42Z
---

## LinkedIn Post

Content:
🚀 Excited to share our latest progress in AI automation!

We're building innovative solutions that help businesses
automate their workflows and increase productivity.

Interested in learning more? Let's connect!

#Business #Automation #Innovation

## To Approve
Drag this file to Approved/ folder
```

### 2. You Review and Approve

1. Open the file in Obsidian
2. Review the content
3. **To approve**: Drag file to `Approved/` folder
4. **To reject**: Drag file to `Rejected/` folder

### 3. System Executes Automatically

The approval checker (running in background) detects the approved file and:
1. Executes the action (post to LinkedIn, send email, etc.)
2. Logs the result
3. Moves the file to `Done/` folder

**Timing**: Actions execute within 10 seconds of approval

---

## 🔧 Troubleshooting

### Problem: "WhatsApp session expired"

**Symptoms**:
```
⚠️  WhatsApp session expired
   To fix: python3 silver/scripts/setup_whatsapp.py
```

**Solution**:
```bash
python silver/scripts/setup_whatsapp.py
# Scan QR code with your phone when browser opens
```

**Why**: WhatsApp Web sessions expire after ~2 weeks of inactivity

---

### Problem: "Contact not found" (WhatsApp)

**Symptoms**:
```
❌ Contact not found: Mr Honey
```

**Solution**: Contact names must match **exactly**, including emojis

```bash
# Find exact contact names
python silver/scripts/list_whatsapp_contacts_v2.py

# Use exact name (including emoji)
python silver/scripts/test_whatsapp_timing.py
# Enter: Mr Honey 😎  (not "Mr Honey")
```

---

### Problem: "Timeout waiting for chat list" (WhatsApp)

**Symptoms**:
```
⏱️  Timeout waiting for WhatsApp Web
```

**Causes**:
1. WhatsApp Web is loading messages (can take 30-180 seconds)
2. Slow internet connection
3. Large chat history

**Solution**: Be patient, especially on first load
- First load: 150-180 seconds
- Subsequent loads: 30-60 seconds

**If stuck**: Reset session
```bash
python silver/scripts/reset_whatsapp_session.py
python silver/scripts/setup_whatsapp.py
```

---

### Problem: WhatsApp messages arrive delayed

**Symptoms**: Recipient receives message 30-60 seconds after you sent it

**Cause**: Chat was still loading when message was sent

**Solution**: ✅ **Already fixed!** The new version waits for chat to fully load before sending.

**Verify fix**:
```bash
python silver/scripts/test_whatsapp_timing.py
# Watch for: "✅ Chat fully loaded and ready to send"
```

See `silver/WHATSAPP_TIMING_FIX.md` for technical details.

---

### Problem: LinkedIn session expired

**Symptoms**: QR code appears when trying to post

**Solution**:
```bash
python silver/scripts/setup_linkedin.py
# Log in when browser opens
```

---

### Problem: "Module not found" or "Command not found"

**Cause**: Virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source silver/.venv/bin/activate

# Verify activation (should see "silver" prefix)
which python
# Output: /path/to/AI_Employee_Vault/silver/.venv/bin/python
```

---

### Problem: Gmail API not working

**Symptoms**:
```
❌ Gmail API not available
```

**Solution**:
1. Enable Gmail API in Google Cloud Console
2. Download credentials
3. Run setup:
```bash
python silver/scripts/setup_gmail.py
```

---

## 📁 Project Structure

```
AI_Employee_Vault/
├── silver/                              # Silver Tier (Complete autonomous system)
│   ├── .venv/                           # Virtual environment (Python 3.14)
│   ├── src/
│   │   ├── watchers/                    # Perception layer
│   │   │   ├── gmail_watcher.py         # Monitor Gmail inbox
│   │   │   ├── whatsapp_watcher.py      # Monitor WhatsApp messages
│   │   │   └── linkedin_poster.py       # LinkedIn automation
│   │   ├── actions/                     # Action executors
│   │   │   ├── email_sender.py          # Send emails via Gmail API
│   │   │   └── whatsapp_sender.py       # Send WhatsApp messages
│   │   ├── approval/                    # HITL workflow
│   │   │   ├── approval_manager.py      # Create approval requests
│   │   │   └── approval_checker.py      # Monitor and execute approvals
│   │   └── utils/                       # Utilities
│   ├── scripts/                         # Test and setup scripts
│   │   ├── test_complete_workflow.py    # Complete workflow test
│   │   ├── test_whatsapp_timing.py      # WhatsApp timing test
│   │   ├── test_linkedin.py             # LinkedIn test
│   │   ├── test_gmail_connection.py     # Gmail test
│   │   ├── setup_whatsapp.py            # WhatsApp authentication
│   │   ├── setup_linkedin.py            # LinkedIn authentication
│   │   └── setup_gmail.py               # Gmail authentication
│   ├── config/                          # Configuration and sessions
│   │   ├── whatsapp_session/            # WhatsApp Web session data
│   │   ├── linkedin_session/            # LinkedIn session data
│   │   ├── gmail_credentials.json       # Gmail API credentials
│   │   └── watcher_config.yaml          # Watcher configuration
│   └── mcp/                             # MCP servers
│       └── email-server/                # Email MCP server
├── Needs_Action/                        # Tasks from watchers
├── Pending_Approval/                    # Actions awaiting approval
├── Approved/                            # Approved actions (auto-executed)
├── Done/                                # Completed actions
├── Logs/                                # Execution logs
├── Dashboard.md                         # Obsidian dashboard
├── Company_Handbook.md                  # AI behavior rules
└── QUICKSTART.md                        # This file
```

---

## 🎯 Quick Reference Commands

### Environment Management

| Task | Command |
|------|---------|
| **Activate venv** | `source silver/.venv/bin/activate` |
| **Deactivate venv** | `deactivate` |
| **Check Python version** | `python --version` |
| **Install dependencies** | `pip install -r silver/requirements.txt` |

### Testing Commands

| Task | Command |
|------|---------|
| **Complete workflow** | `python silver/scripts/test_complete_workflow.py` |
| **Gmail test** | `python silver/scripts/test_gmail_connection.py` |
| **WhatsApp test** | `python silver/scripts/test_whatsapp_timing.py` |
| **LinkedIn test** | `python silver/scripts/test_linkedin.py --dry-run` |
| **List WhatsApp contacts** | `python silver/scripts/list_whatsapp_contacts_v2.py` |

### Production Commands

| Task | Command |
|------|---------|
| **Start approval checker** | `python -m silver.src.approval.approval_checker` |
| **Start Gmail watcher** | `python -m silver.src.watchers.gmail_watcher &` |
| **Start WhatsApp watcher** | `python -m silver.src.watchers.whatsapp_watcher &` |
| **Start LinkedIn scheduler** | `python silver/scripts/linkedin_scheduler.py &` |
| **Stop all watchers** | `pkill -f "watcher"` |

### Setup Commands

| Task | Command |
|------|---------|
| **Setup WhatsApp** | `python silver/scripts/setup_whatsapp.py` |
| **Setup LinkedIn** | `python silver/scripts/setup_linkedin.py` |
| **Setup Gmail** | `python silver/scripts/setup_gmail.py` |
| **Reset WhatsApp session** | `python silver/scripts/reset_whatsapp_session.py` |

---

## 💡 Tips for Demo/Presentation

### 1. Pre-load WhatsApp (Recommended)

WhatsApp Web takes 30-180 seconds to load on first run. Pre-load before demo:

```bash
python silver/scripts/list_whatsapp_contacts_v2.py
# Let it load completely, then close browser
```

### 2. Use Dry-Run Mode for LinkedIn

Avoid accidental posts during demo:

```bash
python silver/scripts/test_linkedin.py --dry-run
```

### 3. Keep Browser Visible

Both WhatsApp and LinkedIn scripts open visible browsers to show automation in action.

### 4. Prepare Obsidian Dashboard

1. Open Obsidian before demo
2. Navigate to `AI_Employee_Vault/`
3. Show folder structure
4. Open `Dashboard.md`

### 5. Have Test Data Ready

- Know exact WhatsApp contact names (including emojis)
- Have a test email in Gmail inbox
- Prepare a LinkedIn post topic

---

## ✅ Pre-Demo Checklist

Before your demo/presentation, verify:

- [ ] Virtual environment activates successfully
- [ ] WhatsApp Web session is authenticated (no QR code)
- [ ] LinkedIn session is authenticated
- [ ] Gmail API connection works
- [ ] Obsidian vault is open and organized
- [ ] Test scripts run without errors
- [ ] Approval checker starts successfully
- [ ] You know exact contact names for WhatsApp

---

## 📚 Additional Documentation

### Silver Tier Documentation

- **`silver/README.md`** - Silver Tier overview and architecture
- **`silver/SILVER_TIER_STATUS.md`** - Completion status and features
- **`silver/WHATSAPP_USAGE_GUIDE.md`** - Complete WhatsApp automation guide
- **`silver/WHATSAPP_TIMING_FIX.md`** - Technical details of timing fix
- **`silver/HITL_COMPLETE.md`** - Human-in-the-loop workflow guide
- **`silver/TESTING_GUIDE.md`** - Comprehensive testing guide

### Agent Skills Documentation

- **`.claude/skills/`** - All Agent Skills implementations
- **`.claude/skills/monitor-communications/`** - Communication monitoring
- **`.claude/skills/post-to-linkedin/`** - LinkedIn automation
- **`.claude/skills/manage-approvals/`** - HITL approval workflow

---

## 🆘 Need Help?

If you encounter issues not covered in this guide:

1. **Check detailed documentation** in `silver/` directory
2. **Review error messages** carefully
3. **Verify virtual environment** is activated
4. **Check Python version**: `python --version` (should be 3.13+)
5. **Verify dependencies**: `pip list`
6. **Check logs**: `tail -f Logs/*.log`

---

## 🎉 You're Ready!

You now have everything you need to run your autonomous AI Employee!

### What You Can Do

✅ **Monitor** Gmail, WhatsApp, LinkedIn automatically
✅ **Review** tasks in Obsidian dashboard
✅ **Approve** actions with human oversight
✅ **Execute** approved actions automatically
✅ **Track** all activity in logs

### Next Steps

1. **Run the complete workflow test** to see it in action
2. **Start the approval checker** for continuous operation
3. **Customize** `Company_Handbook.md` with your rules
4. **Explore** Gold Tier features (Odoo, social media, CEO briefing)

**Happy Automating!** 🚀

---

*Last Updated: 2026-02-06*
*Silver Tier Status: ✅ 100% Complete*
*Architecture: Autonomous AI Employee with HITL Approval*
*Key Features: Gmail, WhatsApp (with timing fix), LinkedIn, Obsidian integration*

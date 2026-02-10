# Gold Tier Social Media - Playwright Quick Start Guide

**Status**: ✅ Ready to Use with Browser Automation
**Workflow**: Same HITL pattern as Silver Tier LinkedIn
**Platforms**: Facebook, Instagram, Twitter/X
**Special Feature**: 🎬 **WATCH THE BROWSER POST IN REAL-TIME!**

---

## 🎯 Overview

Gold Tier social media uses **Playwright browser automation** - exactly like Silver Tier LinkedIn!

**What this means:**
- ✅ You can **watch the browser** open and post automatically
- ✅ Same approval workflow as LinkedIn (Pending → Approved → Done)
- ✅ Visible browser window (headless=False) for debugging
- ✅ Real browser automation, not mock APIs

**The workflow:**
1. System creates approval file in `Pending_Approval/`
2. You review in Obsidian
3. You drag to `Approved/` folder
4. **Browser opens and posts automatically!** 🎬
5. File moves to `Done/`

---

## 🚀 Quick Start (15 Minutes)

### Step 1: Install Playwright (5 minutes)

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault

# Activate Gold Tier virtual environment
source gold/.venv/bin/activate

# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium
```

**Expected output:**
```
Downloading Chromium 123.0.6312.4 (playwright build v1091)
✅ Chromium 123.0.6312.4 downloaded to /home/user/.cache/ms-playwright/chromium-1091
```

---

### Step 2: Setup Social Media Sessions (5 minutes each)

You need to log in to each platform once to save your session.

#### Facebook Setup

```bash
python gold/scripts/setup_facebook.py
```

**What happens:**
1. Browser opens to Facebook
2. You log in manually
3. Complete any 2FA
4. Press Enter when you see your feed
5. Session saved!

#### Twitter Setup

```bash
python gold/scripts/setup_twitter.py
```

**What happens:**
1. Browser opens to Twitter/X
2. You log in manually
3. Complete any 2FA
4. Press Enter when you see your feed
5. Session saved!

#### Instagram Setup (Optional)

```bash
python gold/scripts/setup_instagram.py
```

**Note**: Instagram requires images for posts. For text-only content, use Facebook and Twitter.

---

### Step 3: Test the Workflow (5 minutes)

#### Create Test Approval Files

```bash
python gold/scripts/test_social_approval_workflow.py
```

**Expected output:**
```
🧪 GOLD TIER: SOCIAL MEDIA APPROVAL WORKFLOW TEST

STEP 1: Creating approval requests...
   ✅ Facebook: approval_20260210_160618_post_facebook.md
   ✅ Instagram: approval_20260210_160619_post_instagram.md
   ✅ Twitter: approval_20260210_160620_post_twitter.md

STEP 2: REVIEW IN OBSIDIAN
📊 Open Obsidian and navigate to:
   /path/to/AI_Employee_Vault/Pending_Approval/
```

#### Start the Daemon

**Open a NEW terminal window:**

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source gold/.venv/bin/activate
python gold/scripts/social_media_daemon.py
```

**Expected output:**
```
======================================================================
🤖 GOLD TIER: SOCIAL MEDIA APPROVAL DAEMON (PLAYWRIGHT)
======================================================================

This daemon watches the Approved/ folder and automatically posts
approved social media content to Facebook, Instagram, and Twitter.

🎬 YOU CAN WATCH THE BROWSER POST IN REAL-TIME!

HOW IT WORKS:
  1. Create approval file in Pending_Approval/
  2. Review in Obsidian
  3. Drag to Approved/ folder
  4. Daemon detects and opens browser to post!
  5. File moves to Done/

SAME WORKFLOW AS SILVER TIER LINKEDIN! ✅

======================================================================

🔧 Initializing Playwright posters...
✅ Facebook poster initialized (session: /path/to/facebook_session)
✅ Twitter poster initialized (session: /path/to/twitter_session)
✅ Instagram poster initialized (session: /path/to/instagram_session)
   ✅ All posters initialized (Playwright with visible browser)

👀 Watching: /path/to/AI_Employee_Vault/Approved
   When you drag files to Approved/, browser will open and post!

✅ Daemon started!
   Press Ctrl+C to stop

======================================================================
```

**Keep this terminal open!**

---

### Step 4: Approve and Watch! 🎬

1. **Open Obsidian**
2. Navigate to `Pending_Approval/` folder
3. Open `approval_*_post_facebook.md`
4. Review the content
5. **Drag the file to `Approved/` folder**

**What happens next:**

In the daemon terminal, you'll see:
```
============================================================
📝 APPROVED: approval_20260210_160618_post_facebook.md
   Platform: FACEBOOK
============================================================

📄 Content Preview:
   🚀 Exciting news from our AI Employee project!...

🚀 Posting to FACEBOOK...
   🎬 WATCH THE BROWSER - you'll see it post in real-time!

🌐 Opening browser...
📱 Navigating to Facebook...
🧹 Closing promotional modals...
🖱️  Looking for post composer...
✅ Clicked composer using: [role="button"][aria-label*="Create a post"]
⏳ Waiting for composer modal...
📝 Looking for text input...
✅ Found textbox using: [role="textbox"][contenteditable="true"]
⌨️  Typing content...
✅ Typed 230 characters
🔍 Looking for Post button...
✅ Clicked Post button using: [role="button"][aria-label="Post"]
⏳ Waiting for post to be submitted...
📊 Modal count after posting: 0

   ✅ Posted successfully!
   📁 Moving to Done/
   ✅ Moved to: /path/to/Done/approval_20260210_160618_post_facebook.md
============================================================
```

**AND YOU'LL SEE THE BROWSER:**
- Open Facebook
- Navigate to your feed
- Click "What's on your mind?"
- Type your content
- Click "Post"
- Close automatically

**IT'S LIKE WATCHING A ROBOT USE YOUR COMPUTER!** 🤖

---

## 📋 Comparison: Silver vs Gold

### Silver Tier (LinkedIn)

```
Pending_Approval/approval_20260206_post_linkedin.md
         ↓ (drag in Obsidian)
Approved/approval_20260206_post_linkedin.md
         ↓ (silver daemon detects)
🎬 Browser opens → LinkedIn → Posts → Closes
         ↓
Done/approval_20260206_post_linkedin.md
```

### Gold Tier (Facebook/Twitter)

```
Pending_Approval/approval_20260210_post_facebook.md
         ↓ (drag in Obsidian)
Approved/approval_20260210_post_facebook.md
         ↓ (gold daemon detects)
🎬 Browser opens → Facebook → Posts → Closes
         ↓
Done/approval_20260210_post_facebook.md
```

**IDENTICAL WORKFLOW!** ✅

---

## 🔧 How to Create Your Own Posts

### Method 1: Manual Creation

Create a file in `Pending_Approval/` with this format:

**File**: `Pending_Approval/approval_20260210_my_facebook_post.md`

```markdown
---
type: approval_request
action: post_facebook
platform: facebook
status: pending
created: 2026-02-10T16:00:00Z
---

## Facebook Post

### Content

Your post content here!

Can include:
- Multiple lines
- Emojis 🚀
- Hashtags #AI #Automation
- Links https://example.com

### To Approve

Drag this file to the **Approved/** folder in Obsidian.

The system will automatically post to Facebook and move this file to Done/.
```

**Platform options:**
- `platform: facebook` → Posts to Facebook
- `platform: twitter` → Posts to Twitter/X
- `platform: instagram` → Posts to Instagram (requires image)

---

### Method 2: Use Test Script

```bash
python gold/scripts/test_social_approval_workflow.py
```

This creates 3 sample approval files (Facebook, Instagram, Twitter) ready for testing.

---

## 🎬 Demo for Hackathon

### Perfect Demo Flow (2-3 minutes)

**Terminal 1**: Start daemon
```bash
python gold/scripts/social_media_daemon.py
```

**Terminal 2**: Create test approvals
```bash
python gold/scripts/test_social_approval_workflow.py
```

**In Obsidian:**
1. Show `Pending_Approval/` folder with 3 files
2. Open `approval_*_post_facebook.md`
3. Review content
4. Drag to `Approved/` folder

**Switch to Terminal 1:**
- Show daemon detecting the approval
- **Point to the browser opening** 🎬
- Watch it post to Facebook
- Show file moved to `Done/`

**Repeat for Twitter:**
- Drag Twitter approval to `Approved/`
- Watch browser post to Twitter
- Show completion

**This demonstrates:**
- ✅ HITL approval workflow
- ✅ Multi-platform support
- ✅ Real browser automation (not mock)
- ✅ Same pattern as Silver Tier LinkedIn
- ✅ Production-ready implementation

---

## 🏭 Production Mode (24/7 Operation)

### Option A: Run Daemon Manually

```bash
# Start in background
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault
source gold/.venv/bin/activate
nohup python gold/scripts/social_media_daemon.py >> Logs/gold_social_daemon.log 2>&1 &

# Check if running
ps aux | grep social_media_daemon

# View logs
tail -f Logs/gold_social_daemon.log

# Stop daemon
pkill -f "social_media_daemon.py"
```

---

### Option B: Add to Cron (Auto-Start on Boot)

```bash
# Edit crontab
crontab -e

# Add these lines:

# Start Gold Tier social media daemon on boot
@reboot cd /path/to/AI_Employee_Vault && gold/.venv/bin/python gold/scripts/social_media_daemon.py >> Logs/gold_social_daemon.log 2>&1

# Health check every 5 minutes (restart if crashed)
*/5 * * * * pgrep -f "social_media_daemon.py" > /dev/null || (cd /path/to/AI_Employee_Vault && gold/.venv/bin/python gold/scripts/social_media_daemon.py >> Logs/gold_social_daemon.log 2>&1 &)
```

**Now both Silver and Gold daemons run 24/7!**

---

## 🔍 Troubleshooting

### Problem: "Playwright not installed"

**Solution:**
```bash
source gold/.venv/bin/activate
pip install playwright
playwright install chromium
```

---

### Problem: "Session expired"

**Symptoms:**
```
❌ Facebook session expired. Please re-login.
   Run: python gold/scripts/setup_facebook.py
```

**Solution:**
```bash
python gold/scripts/setup_facebook.py
# Log in again and save session
```

---

### Problem: Browser not opening

**Cause**: Daemon might be using headless mode

**Solution**: Check `social_media_daemon.py` - should have `headless=False`

---

### Problem: Post button not found

**Cause**: Social media UI changed

**Solution**:
1. Check screenshots in `Logs/` folder
2. Update selectors in poster files
3. Or use mock APIs for demo

---

## ✅ Summary

**What You Have Now:**
- ✅ Playwright browser automation for Facebook, Twitter, Instagram
- ✅ Same HITL workflow as Silver Tier LinkedIn
- ✅ Visible browser window - watch it post in real-time! 🎬
- ✅ Session management (log in once, use forever)
- ✅ Daemon watches `Approved/` folder
- ✅ Automatic posting within seconds of approval
- ✅ All actions logged and tracked

**How to Use:**
1. Setup sessions once: `python gold/scripts/setup_*.py`
2. Start daemon: `python gold/scripts/social_media_daemon.py`
3. Create approval files (manually or via script)
4. Review in Obsidian
5. Drag to `Approved/` folder
6. **Watch the browser post automatically!** 🎬

**For Hackathon:**
- ✅ Demonstrates full HITL workflow
- ✅ Shows multi-platform integration
- ✅ Uses real browser automation (impressive!)
- ✅ Professional approval process
- ✅ Same pattern across all tiers (consistency)

---

**Last Updated**: 2026-02-10
**Status**: ✅ Production Ready with Playwright
**Platforms**: Facebook, Instagram, Twitter/X
**Workflow**: Human-in-the-Loop Approval (same as Silver Tier)
**Special Feature**: 🎬 Visible Browser Automation!

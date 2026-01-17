# Quickstart Guide: Gold Tier Autonomous Employee

**Last Updated**: 2026-01-17
**Estimated Setup Time**: 2-3 hours

## Prerequisites

Before starting Gold Tier, ensure you have:

- ✅ **Silver Tier Complete** - All Silver Tier features operational
- ✅ **Xero Account** - Paid plan with API access
- ✅ **Facebook Developer Account** - For Facebook/Instagram APIs
- ✅ **Twitter Developer Account** - For Twitter API v2
- ✅ **PM2 Installed** - For process management (`npm install -g pm2`)
- ✅ **Node.js 24+ LTS** - For MCP servers
- ✅ **Python 3.13+** - Already installed from Bronze/Silver
- ✅ **Stable Internet** - 10+ Mbps for API calls

## Step 1: Set Up Xero Integration (30 minutes)

### 1.1 Create Xero Developer Account

```bash
# 1. Go to https://developer.xero.com/
# 2. Sign up for developer account
# 3. Create new app:
#    - App name: "AI Employee Gold"
#    - Company/App URL: http://localhost:3000
#    - Redirect URI: http://localhost:3000/callback
# 4. Note down Client ID and Client Secret
```

### 1.2 Install Xero MCP Server

```bash
# Clone Xero MCP server
cd gold/mcp/
git clone https://github.com/XeroAPI/xero-mcp-server.git xero
cd xero

# Install dependencies
npm install

# Configure credentials
cat > config.json << 'EOF'
{
  "clientId": "YOUR_XERO_CLIENT_ID",
  "clientSecret": "YOUR_XERO_CLIENT_SECRET",
  "redirectUri": "http://localhost:3000/callback",
  "scopes": [
    "accounting.transactions",
    "accounting.reports.read",
    "accounting.contacts"
  ]
}
EOF

# Test connection
npm test
```

### 1.3 Configure Xero in Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "xero",
      "command": "node",
      "args": ["gold/mcp/xero/server.js"],
      "env": {
        "XERO_CLIENT_ID": "${XERO_CLIENT_ID}",
        "XERO_CLIENT_SECRET": "${XERO_CLIENT_SECRET}"
      }
    }
  ]
}
```

---

## Step 2: Set Up Social Media Integrations (45 minutes)

### 2.1 Facebook & Instagram Setup

```bash
# 1. Go to https://developers.facebook.com/
# 2. Create new app (Business type)
# 3. Add Facebook Login product
# 4. Add Instagram Basic Display product
# 5. Configure OAuth redirect: http://localhost:3000/callback
# 6. Get App ID and App Secret
# 7. Generate User Access Token with permissions:
#    - pages_manage_posts
#    - pages_read_engagement
#    - instagram_basic
#    - instagram_content_publish
```

### 2.2 Twitter Setup

```bash
# 1. Go to https://developer.twitter.com/
# 2. Create new project and app
# 3. Enable OAuth 2.0
# 4. Set redirect URI: http://localhost:3000/callback
# 5. Get API Key, API Secret, Bearer Token
# 6. Generate Access Token and Secret
```

### 2.3 Install Social Media MCP Server

```bash
# Create social MCP server
cd gold/mcp/
mkdir social
cd social

# Install dependencies
npm init -y
npm install @anthropic/mcp facebook-nodejs-business-sdk twitter-api-v2

# Create server
cat > server.js << 'EOF'
const { MCPServer } = require('@anthropic/mcp');
const { FacebookAdsApi } = require('facebook-nodejs-business-sdk');
const { TwitterApi } = require('twitter-api-v2');

// Server implementation
// (See full implementation in gold/mcp/social/server.js)
EOF

# Configure credentials
cat > config.json << 'EOF'
{
  "facebook": {
    "appId": "YOUR_FACEBOOK_APP_ID",
    "appSecret": "YOUR_FACEBOOK_APP_SECRET",
    "accessToken": "YOUR_FACEBOOK_ACCESS_TOKEN"
  },
  "twitter": {
    "apiKey": "YOUR_TWITTER_API_KEY",
    "apiSecret": "YOUR_TWITTER_API_SECRET",
    "accessToken": "YOUR_TWITTER_ACCESS_TOKEN",
    "accessSecret": "YOUR_TWITTER_ACCESS_SECRET"
  }
}
EOF
```

### 2.4 Configure Social Media in Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "social",
      "command": "node",
      "args": ["gold/mcp/social/server.js"],
      "env": {
        "FACEBOOK_APP_ID": "${FACEBOOK_APP_ID}",
        "TWITTER_API_KEY": "${TWITTER_API_KEY}"
      }
    }
  ]
}
```

---

## Step 3: Set Up Error Recovery & Audit Logging (20 minutes)

### 3.1 Create Error Recovery System

```bash
# Create core directory
mkdir -p gold/src/core

# Create error recovery module
cat > gold/src/core/error_recovery.py << 'EOF'
"""Error recovery system with exponential backoff."""
import time
import random
from typing import Callable, Any
from enum import Enum

class ErrorCategory(Enum):
    TRANSIENT = "transient"
    AUTHENTICATION = "authentication"
    LOGIC = "logic"
    DATA = "data"
    SYSTEM = "system"

def exponential_backoff_with_jitter(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    return max(0, delay + jitter)

def retry_with_backoff(func: Callable, max_attempts: int = 3) -> Any:
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = exponential_backoff_with_jitter(attempt)
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
            time.sleep(delay)
EOF
```

### 3.2 Create Audit Logger

```bash
cat > gold/src/core/audit_logger.py << 'EOF'
"""Comprehensive audit logging system."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class AuditLogger:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(exist_ok=True)

    def log(self, action_type: str, actor: str, target: str,
            parameters: Optional[Dict] = None, result: str = "success",
            error: Optional[str] = None, **kwargs):
        """Log an action to the audit log."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "parameters": parameters or {},
            "result": result,
            "error": error,
            **kwargs
        }

        # Write to daily log file
        log_file = self.logs_dir / f"{datetime.utcnow().date()}.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
EOF
```

---

## Step 4: Set Up Vault Structure for Gold Tier (10 minutes)

### 4.1 Create New Folders

```bash
# Navigate to vault root
cd /path/to/AI_Employee_Vault

# Create Gold Tier folders
mkdir -p Briefings
mkdir -p Accounting/Transactions
mkdir -p Social_Media/Posts
mkdir -p Social_Media/Drafts
mkdir -p Social_Media/Analytics
mkdir -p Context
mkdir -p Ralph_State

# Verify structure
ls -la
# You should see: Briefings, Accounting, Social_Media, Context, Ralph_State
```

### 4.2 Create Business Goals Template

```bash
cat > Business_Goals.md << 'EOF'
---
last_updated: 2026-01-17
review_frequency: weekly
---

# Business Goals

## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $0

### Key Metrics to Track
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

### Active Projects
1. Project Alpha - Due Jan 31 - Budget $5,000
2. Project Beta - Due Feb 15 - Budget $3,500

### Subscription Audit Rules
Flag for review if:
- No login in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool

## Social Media Goals
- LinkedIn: 3 posts/week, 100+ engagements/week
- Twitter: 5 tweets/week, 50+ engagements/week
- Facebook: 1 post/week, 20+ engagements/week
EOF
```

---

## Step 5: Set Up Process Management (15 minutes)

### 5.1 Create PM2 Ecosystem Config

```bash
cat > gold/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    // Existing Silver Tier watchers
    {
      name: 'gmail-watcher',
      script: 'silver/src/watchers/gmail_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    {
      name: 'whatsapp-watcher',
      script: 'silver/src/watchers/whatsapp_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    {
      name: 'linkedin-watcher',
      script: 'silver/src/watchers/linkedin_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    // New Gold Tier watchers
    {
      name: 'xero-watcher',
      script: 'gold/src/watchers/xero_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    {
      name: 'facebook-watcher',
      script: 'gold/src/watchers/facebook_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    {
      name: 'twitter-watcher',
      script: 'gold/src/watchers/twitter_watcher.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '500M'
    },
    // Gold Tier core services
    {
      name: 'watchdog',
      script: 'gold/src/core/watchdog.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '200M'
    },
    {
      name: 'health-monitor',
      script: 'gold/src/core/health_monitor.py',
      interpreter: 'python3',
      autorestart: true,
      max_memory_restart: '200M'
    }
  ]
};
EOF
```

### 5.2 Start All Processes

```bash
# Start all processes
pm2 start gold/ecosystem.config.js

# Save configuration
pm2 save

# Enable startup on boot
pm2 startup

# Check status
pm2 status
```

---

## Step 6: Set Up CEO Briefing Schedule (10 minutes)

### 6.1 Create Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (Sunday 7:00 AM)
0 7 * * 0 /usr/bin/python3 /path/to/gold/src/intelligence/ceo_briefing.py >> /path/to/logs/ceo_briefing.log 2>&1
```

### 6.2 Create Task Scheduler (Windows)

```powershell
# Create scheduled task
schtasks /create /tn "CEO Briefing" /tr "python C:\path\to\gold\src\intelligence\ceo_briefing.py" /sc weekly /d SUN /st 07:00 /ru SYSTEM
```

---

## Step 7: Configure Environment Variables (10 minutes)

### 7.1 Create .env File

```bash
cat > gold/.env << 'EOF'
# Xero
XERO_CLIENT_ID=your_client_id
XERO_CLIENT_SECRET=your_client_secret
XERO_REDIRECT_URI=http://localhost:3000/callback

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token

# Instagram
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
INSTAGRAM_ACCESS_TOKEN=your_access_token

# Twitter
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# General
VAULT_PATH=/path/to/AI_Employee_Vault
LOG_LEVEL=INFO
DRY_RUN=false
EOF

# Add to .gitignore
echo "gold/.env" >> .gitignore
```

---

## Step 8: Test Gold Tier Setup (20 minutes)

### 8.1 Test Xero Integration

```bash
# Test Xero MCP server
node gold/mcp/xero/test.js

# Expected output:
# ✅ Xero connection successful
# ✅ Can read invoices
# ✅ Can create transactions
```

### 8.2 Test Social Media Integration

```bash
# Test social MCP server
node gold/mcp/social/test.js

# Expected output:
# ✅ Facebook connection successful
# ✅ Twitter connection successful
# ✅ Can post to platforms
```

### 8.3 Test Error Recovery

```bash
# Test error recovery
python3 gold/tests/test_error_recovery.py

# Expected output:
# ✅ Exponential backoff working
# ✅ Retry logic working
# ✅ Error classification working
```

### 8.4 Test Audit Logging

```bash
# Test audit logger
python3 gold/tests/test_audit_logger.py

# Expected output:
# ✅ Log entries created
# ✅ Daily rotation working
# ✅ Log format correct
```

### 8.5 Test CEO Briefing (Manual Trigger)

```bash
# Manually trigger CEO briefing
python3 gold/src/intelligence/ceo_briefing.py

# Check output
cat Briefings/$(date +%Y-%m-%d)_Monday_Briefing.md

# Expected: Briefing file created with all sections
```

---

## Step 9: Verify Complete Setup (10 minutes)

### 9.1 Check All Services Running

```bash
# Check PM2 status
pm2 status

# Expected: All processes online (green)
```

### 9.2 Check MCP Servers

```bash
# Test all MCP servers
claude mcp list

# Expected output:
# ✅ email (Silver Tier)
# ✅ xero (Gold Tier)
# ✅ social (Gold Tier)
```

### 9.3 Check Vault Structure

```bash
# Verify all folders exist
ls -la /path/to/AI_Employee_Vault

# Expected folders:
# Inbox, Needs_Action, Done, Logs (Bronze)
# Pending_Approval, Approved (Silver)
# Briefings, Accounting, Social_Media, Context, Ralph_State (Gold)
```

### 9.4 Check Logs

```bash
# Check today's audit log
cat Logs/$(date +%Y-%m-%d).json

# Expected: JSON log entries
```

---

## Troubleshooting

### Xero Connection Issues

**Problem**: "OAuth authentication failed"

**Solution**:
```bash
# 1. Verify credentials in config.json
# 2. Check redirect URI matches exactly
# 3. Ensure app has correct scopes
# 4. Try re-generating access token
```

### Social Media API Errors

**Problem**: "Rate limit exceeded"

**Solution**:
```bash
# 1. Check rate limits in platform dashboard
# 2. Implement queue system
# 3. Reduce posting frequency
# 4. Use batch APIs where available
```

### PM2 Process Crashes

**Problem**: "Process keeps restarting"

**Solution**:
```bash
# Check logs
pm2 logs <process-name>

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Wrong Python path: which python3
# - Permission errors: chmod +x script.py
```

### CEO Briefing Not Generating

**Problem**: "Briefing file not created"

**Solution**:
```bash
# Check cron logs
grep CRON /var/log/syslog

# Test manually
python3 gold/src/intelligence/ceo_briefing.py

# Check permissions
ls -la gold/src/intelligence/ceo_briefing.py
```

---

## Next Steps

After completing setup:

1. **Test Each Integration**:
   - Create test invoice in Xero
   - Post test message to social media
   - Verify CEO Briefing generates

2. **Monitor for 1 Week**:
   - Check PM2 status daily
   - Review audit logs
   - Verify all watchers running

3. **First CEO Briefing**:
   - Wait for Sunday 7:00 AM
   - Review generated briefing
   - Verify accuracy of data

4. **Fine-Tune Settings**:
   - Adjust rate limits
   - Optimize polling intervals
   - Configure alert thresholds

---

## Quick Reference

### Start All Services
```bash
pm2 start gold/ecosystem.config.js
```

### Stop All Services
```bash
pm2 stop all
```

### View Logs
```bash
pm2 logs
```

### Restart Service
```bash
pm2 restart <service-name>
```

### Manual CEO Briefing
```bash
python3 gold/src/intelligence/ceo_briefing.py
```

### Check Health
```bash
cat Health_Status.md
```

---

**Setup Complete!** 🎉

Your Gold Tier Autonomous Employee is now operational. The system will:
- Monitor Xero for financial transactions
- Track social media engagement
- Generate weekly CEO Briefings
- Provide cross-domain intelligence
- Operate autonomously 24/7

---

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Estimated Total Time**: 2-3 hours

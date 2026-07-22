# ReplyWatcher Monitoring & Testing Guide

## Quick Status Check

```bash
# Check if backend is running
curl -s http://localhost:8000/health | python3 -m json.tool

# Expected output:
# {
#   "status": "healthy",
#   "services": {
#     "orchestrator": "running",
#     "gmail_watcher": "running",
#     "reply_watcher": "running",
#     "daily_digest": "scheduled"
#   }
# }
```

---

## Understanding ReplyWatcher Behavior

**Important:** ReplyWatcher only logs when:
1. It starts up
2. It finds a new reply
3. An error occurs

**Silent polling is NORMAL** - if there are no new unprocessed messages, the log stays quiet. This means it's working correctly!

---

## How to Test ReplyWatcher Detection

### Option 1: Send a Real Test Reply (Recommended)

1. **Pick a monitored candidate email:**
   - muhammadubaidansari145@gmail.com
   - test.candidate@gmail.com
   - hanifatima147@gmail.com

2. **Send a reply to h05101092@gmail.com:**
   - Subject: "Re: Interview Invitation - Full Stack Developer"
   - Body: "I am available for Tuesday at 4pm"
   - Make sure it's a REPLY (not a new email)

3. **Watch logs in real-time:**
   ```bash
   cd backend
   tail -f ../logs/backend.log | grep --line-buffered -E "ReplyWatcher|Found.*reply|Pushed.*reply"
   ```

4. **Expected behavior within 60 seconds:**
   ```
   2026-07-20 01:XX:XX - ReplyWatcher - INFO - Found scheduling reply from <email>
   2026-07-20 01:XX:XX - ReplyWatcher - INFO - Pushed scheduling reply for candidate X
   2026-07-20 01:XX:XX - orchestrator - INFO - Popped scheduling reply for candidate X
   ```

### Option 2: Check Redis Processed Cache

```bash
cd backend
uv run python << 'PYEOF'
import asyncio
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

async def check_cache():
    r = await redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    count = await r.scard('processed_emails')
    print(f"Currently tracking {count} processed messages")
    
    # Get a sample
    sample = await r.srandmember('processed_emails', 5)
    print("\nSample message IDs:")
    for msg_id in sample:
        print(f"  - {msg_id.decode()}")
    
    await r.close()

asyncio.run(check_cache())
PYEOF
```

### Option 3: Manual Detection Test

```bash
cd backend
uv run python test_reply_detection.py
```

This will show:
- Number of candidates being monitored
- Recent messages from those candidates
- Whether messages are already processed
- If new replies would be detected

---

## Monitoring Commands

### Live Log Monitoring
```bash
# All activity
tail -f ../logs/backend.log

# Only ReplyWatcher activity
tail -f ../logs/backend.log | grep "ReplyWatcher"

# Errors only
tail -f ../logs/backend.log | grep "ERROR"

# OAuth issues
tail -f ../logs/backend.log | grep "invalid_grant"
```

### Backend Health Checks
```bash
# Quick health check
curl -s http://localhost:8000/health

# Check if process is running
ps aux | grep "uvicorn.*main:app" | grep -v grep

# Check process uptime
ps -p $(pgrep -f "uvicorn.*main:app") -o pid,etime,cmd
```

### Redis Queue Status
```bash
cd backend
uv run python << 'PYEOF'
import asyncio
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

async def check_queues():
    r = await redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    
    queues = {
        'screening_queue': await r.llen('screening_queue'),
        'reply_queue': await r.llen('reply_queue'),
        'scheduling_reply_queue': await r.llen('scheduling_reply_queue'),
        'rejection_reply_queue': await r.llen('rejection_reply_queue')
    }
    
    print("Redis Queue Status:")
    print("=" * 50)
    for queue, length in queues.items():
        status = "⚠️ HAS ITEMS" if length > 0 else "✓ Empty"
        print(f"  {queue}: {length} items [{status}]")
    
    await r.close()

asyncio.run(check_queues())
PYEOF
```

---

## Troubleshooting

### ReplyWatcher Not Detecting Messages

**Check 1: Are there candidates to monitor?**
```bash
cd backend
uv run python test_reply_detection.py
```
Look for "Candidates to monitor: X"

**Check 2: Are new messages arriving?**
```bash
# Search Gmail directly
cd backend
uv run python << 'PYEOF'
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

credentials = Credentials(
    token=None,
    refresh_token=os.getenv('GMAIL_REFRESH_TOKEN'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id=os.getenv('GMAIL_CLIENT_ID'),
    client_secret=os.getenv('GMAIL_CLIENT_SECRET'),
)
service = build('gmail', 'v1', credentials=credentials)

results = service.users().messages().list(
    userId='me', q='in:inbox -in:sent newer_than:1h', maxResults=10
).execute()

messages = results.get('messages', [])
print(f"Found {len(messages)} messages in inbox from last hour")
PYEOF
```

**Check 3: OAuth token issues?**
```bash
tail -50 ../logs/backend.log | grep -i "oauth\|invalid_grant"
```

If you see OAuth errors, restart backend:
```bash
pkill -f "main.py"
cd backend
nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
```

---

## Expected Behavior Timeline

**When a candidate replies:**

```
T+0s:    Candidate sends email reply
T+0-60s: ReplyWatcher polls Gmail (next cycle)
T+0-60s: Detects reply with In-Reply-To header
T+0-60s: Checks Redis cache (not processed before?)
T+0-60s: Pushes to Redis queue (scheduling_reply_queue)
T+0-61s: Orchestrator consumes from queue
T+0-62s: SchedulingAgent processes reply
T+0-65s: Sends response email
```

**Total time from reply to response:** 1-2 minutes (depending on poll cycle)

---

## System Status Indicators

### ✅ Healthy System
- Health endpoint returns 200
- No OAuth errors in logs
- Backend process running
- All 4 orchestrator consumers running
- ReplyWatcher started (logged once at startup)
- No ERROR lines in recent logs

### ⚠️ Requires Attention
- OAuth errors (restart backend)
- Backend process not found
- Redis connection errors
- Database connection errors

### ❌ Critical Issues
- Backend won't start
- Continuous errors in logs
- Health endpoint returns 500
- All services report as failing

---

## Performance Expectations

- **ReplyWatcher poll interval:** 60 seconds
- **GmailWatcher poll interval:** 120 seconds
- **Orchestrator queue consumers:** Real-time (< 1 second)
- **Response email delay:** 1-2 minutes total

---

## Production Checklist

- [ ] Backend running and stable
- [ ] Health endpoint responding
- [ ] No OAuth errors for 1+ hour
- [ ] Test reply successfully detected and processed
- [ ] Response email contains valid Google Meet link
- [ ] No contradictory rescheduling messages
- [ ] Redis queues processing correctly
- [ ] Database connections stable
- [ ] Logs clean (no recurring errors)


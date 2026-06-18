# Intelligent Interview Scheduling System - Complete Guide

## 🎉 What Was Implemented

You now have a **fully autonomous AI-powered interview scheduling agent** that:

1. ✅ **Generates creative, contextual responses** using Grok LLM (not templates)
2. ✅ **Handles full scheduling conversations** autonomously
3. ✅ **Manages calendar availability** and prevents conflicts
4. ✅ **Adapts to candidate replies** naturally
5. ✅ **Routes conversations intelligently** (screening vs scheduling)
6. ✅ **Runs 24/7 with PM2** process management

---

## 🏗️ Architecture Overview

### New Components

1. **Database Models** (`db/models.py`)
   - `InterviewSlot` - Manages available/booked interview times
   - `SchedulingConversation` - Tracks scheduling conversations with candidates

2. **Calendar Service** (`services/calendar_service.py`)
   - Creates available time slots
   - Checks for conflicts
   - Books/proposes/cancels slots
   - Manages timezones

3. **Scheduling Agent** (`services/scheduling_agent.py`)
   - Uses Grok LLM for creative responses
   - Analyzes candidate intent (accept, request alternative, ask question, decline)
   - Handles multi-turn conversations
   - Generates personalized emails

4. **Updated Reply Watcher** (`watchers/reply_watcher.py`)
   - Routes screening replies → `reply_queue`
   - Routes scheduling replies → `scheduling_reply_queue`

5. **Updated Orchestrator** (`orchestrator.py`)
   - Consumes 3 queues concurrently:
     - `screening_queue` - New candidates
     - `reply_queue` - Screening question replies
     - `scheduling_reply_queue` - Scheduling conversation replies

6. **Updated Approval Flow** (`routers/approvals.py`)
   - When hiring manager approves → triggers intelligent scheduling
   - No more generic "we'll reach out" emails

---

## 🔄 Complete Workflow

### 1. Candidate Applies
```
Candidate submits application → Backend extracts CV → AI scores resume
```

### 2. AI Screening
```
If score is good → AI generates screening questions → Sends via Gmail
Candidate replies → AI analyzes answers → Creates approval for hiring manager
```

### 3. Hiring Manager Approves ✨ **NEW**
```
Hiring manager clicks "Approve" in admin dashboard
↓
Scheduling Agent initiates conversation:
  - Gets 5 available slots from calendar
  - Generates creative email with LLM
  - Proposes specific times
  - Sends via Gmail
```

### 4. Candidate Replies ✨ **NEW**
```
Candidate replies to scheduling email
↓
Reply Watcher detects it's a scheduling reply
↓
Routes to scheduling_reply_queue
↓
Scheduling Agent analyzes intent with LLM:
  - Accept slot → Books it, sends confirmation
  - Request alternative → Proposes new times
  - Ask question → Answers intelligently
  - Decline → Sends gracious response
  - Unclear → Asks for clarification
```

### 5. Confirmation ✨ **NEW**
```
When candidate accepts a time:
  - Slot is booked in database
  - Other proposed slots released
  - Creative confirmation email sent
  - Meeting link included (placeholder for now)
```

---

## 🧪 Testing the System

### Step 1: Apply for a Job
1. Go to http://localhost:3000/apply/1
2. Use a **new email** (not one that already applied)
3. Upload your PDF resume
4. Submit application

### Step 2: Check Admin Dashboard
1. Go to http://localhost:3000/candidates
2. Wait for AI to score the resume (~30 seconds)
3. Check the "Approvals" section

### Step 3: Approve Candidate
1. Click "Approve" on the candidate
2. **This triggers the intelligent scheduling agent**
3. Check your email - you'll receive a creative scheduling email with 5 time slots

### Step 4: Reply to Scheduling Email
Reply with one of these to test different flows:

**Accept a slot:**
```
"I'd like to schedule for option 2, please."
"Tuesday at 2 PM works great for me!"
```

**Request alternatives:**
```
"None of these times work for me. Do you have anything next week?"
"I'm not available those days. Can we do mornings?"
```

**Ask a question:**
```
"Will this be a technical interview?"
"How long will the interview take?"
```

**Decline:**
```
"I've accepted another offer. Thank you for your time."
```

### Step 5: Watch the Magic
- The agent analyzes your reply using LLM
- Generates a contextual, creative response
- Handles the conversation autonomously
- Books the slot when you accept

---

## 📊 Database Tables

### Interview Slots (48 created for testing)
```sql
SELECT * FROM interview_slots WHERE status = 'available';
```
- 48 slots created for next 7 days
- 9 AM - 5 PM UTC, weekdays only
- 45-minute duration

### Scheduling Conversations
```sql
SELECT * FROM scheduling_conversations;
```
- Tracks conversation state
- Stores full conversation history
- Links to confirmed slot

---

## 🎮 PM2 Management

### Start Services
```bash
cd /mnt/d/hamza/autonomous-ftes/Candidate_Screening_Agent
./pm2-manage.sh start
```

### Stop Services
```bash
./pm2-manage.sh stop
```

### Restart Services
```bash
./pm2-manage.sh restart
```

### Check Status
```bash
./pm2-manage.sh status
# or
pm2 status
```

### View Logs
```bash
# All logs
./pm2-manage.sh logs

# Backend only
pm2 logs candidate-screening-backend

# Frontend only
pm2 logs candidate-screening-frontend

# Last 100 lines
pm2 logs --lines 100
```

### Monitor in Real-Time
```bash
pm2 monit
```

---

## 🔧 Configuration

### Environment Variables
All in `backend/.env`:
```env
# Grok API for LLM-powered responses
XAI_API_KEY=your_grok_api_key

# Gmail for sending emails
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...

# Database
DATABASE_URL=postgresql+asyncpg://...

# Redis for queues
REDIS_URL=redis://localhost:6379

# Email mode
DRY_RUN=false
```

### Creating More Interview Slots
```bash
cd backend
source .venv/bin/activate
python create_interview_slots.py
```

Edit the script to customize:
- Date range
- Working hours
- Slot duration
- Timezone
- Interviewer details

---

## 🎯 Key Features

### 1. Creative, Contextual Responses
**Before (Template):**
```
Dear Candidate,
We'll reach out shortly to schedule a time.
Best regards,
Hiring Team
```

**After (LLM-Generated):**
```
Hi Hamza!

Great news - we'd love to move forward with an interview!
I have the following times available this week:

1. Tuesday, May 6th at 2:00 PM UTC
2. Wednesday, May 7th at 10:00 AM UTC
3. Thursday, May 8th at 3:30 PM UTC

Which works best for you? If none of these fit your schedule,
feel free to suggest an alternative time.

Looking forward to speaking with you!

Best regards,
AI Recruiting Assistant
```

### 2. Intent Understanding
The agent uses LLM to understand what the candidate means:
- "Option 2 works" → Accepts slot #2
- "I prefer mornings" → Requests alternative times
- "How long is the interview?" → Asks question
- "I'm no longer interested" → Declines

### 3. Conflict Prevention
- Checks for double-booking before proposing slots
- Releases proposed slots when candidate books one
- Marks slots as unavailable when booked

### 4. Conversation State Management
Tracks where each candidate is in the scheduling flow:
- `proposing_times` - Initial slots sent
- `awaiting_confirmation` - Waiting for candidate to choose
- `confirmed` - Interview scheduled
- `rescheduling` - Candidate requested different times
- `cancelled` - Candidate declined

---

## 📝 Logs and Monitoring

### Backend Logs
```bash
tail -f backend/logs/backend-combined.log
```

### Frontend Logs
```bash
tail -f frontend/logs/frontend-combined.log
```

### PM2 Dashboard
```bash
pm2 plus
```
(Requires PM2 Plus account - optional)

---

## 🚀 What's Next

### Enhancements You Can Add:

1. **Calendar Integration**
   - Integrate with Google Calendar API
   - Sync booked slots automatically
   - Generate real meeting links (Zoom, Google Meet)

2. **Timezone Detection**
   - Detect candidate's timezone from email
   - Display times in their local timezone
   - Handle DST automatically

3. **Reminder Emails**
   - Send reminder 24 hours before interview
   - Send reminder 1 hour before interview
   - Include meeting link and preparation tips

4. **Rescheduling**
   - Allow candidates to reschedule
   - Handle cancellations gracefully
   - Notify hiring manager of changes

5. **Multi-Round Interviews**
   - Schedule multiple interview rounds
   - Coordinate with different interviewers
   - Track progress through interview pipeline

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
pm2 delete all
pm2 start ecosystem.config.js
pm2 logs
```

### Database Connection Issues
```bash
# Check database is accessible
psql $DATABASE_URL -c "SELECT 1;"
```

### Redis Connection Issues
```bash
# Check Redis is running
docker ps | grep redis
redis-cli ping
```

### Gmail API Issues
```bash
# Test Gmail connection
cd backend
source .venv/bin/activate
python -c "from services.gmail_service import gmail_service; print(gmail_service.service.users().getProfile(userId='me').execute())"
```

---

## 📚 Code References

- **Scheduling Agent**: `backend/services/scheduling_agent.py`
- **Calendar Service**: `backend/services/calendar_service.py`
- **Reply Watcher**: `backend/watchers/reply_watcher.py`
- **Orchestrator**: `backend/orchestrator.py`
- **Approval Flow**: `backend/routers/approvals.py`
- **Database Models**: `backend/db/models.py`

---

## ✅ Summary

You now have a **fully autonomous interview scheduling agent** that:
- Generates creative, personalized emails
- Understands candidate intent using LLM
- Handles multi-turn conversations
- Manages calendar conflicts
- Runs 24/7 with PM2

**No more generic "we'll reach out" emails!** 🎉

The agent adapts to each candidate's responses and handles the entire scheduling workflow autonomously.

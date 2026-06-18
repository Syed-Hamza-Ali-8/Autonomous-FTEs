# Rejection Reply Handler - Complete Guide

## 🎉 What Was Implemented

You now have an **empathetic AI agent that responds to rejected candidates** with:

1. ✅ **LLM-powered intent analysis** - Understands what the candidate means
2. ✅ **Contextual, empathetic responses** - Not templates, real understanding
3. ✅ **3-response limit** - Prevents endless conversations
4. ✅ **Professional tone** - Maintains brand reputation
5. ✅ **Automatic routing** - Detects rejection email replies and routes to handler

---

## 🏗️ Architecture

### New Components

1. **RejectionReplyHandler** (`services/rejection_reply_handler.py`)
   - Analyzes candidate intent using Grok LLM
   - Generates empathetic, contextual responses
   - Enforces 3-response maximum per candidate
   - Handles different intent types: reconsideration, feedback, questions, gratitude, disappointment

2. **Updated Reply Watcher** (`watchers/reply_watcher.py`)
   - Now detects 3 types of replies: screening, scheduling, rejection
   - Routes rejection replies to `rejection_reply_queue`
   - Matches replies using `rejection_message_id`

3. **Updated Orchestrator** (`orchestrator.py`)
   - Consumes 4 queues concurrently:
     - `screening_queue` - New candidates
     - `reply_queue` - Screening question replies
     - `scheduling_reply_queue` - Scheduling conversation replies
     - `rejection_reply_queue` - Rejection email replies (NEW)

4. **Database Fields** (added to `candidates` table)
   - `rejection_message_id` - Tracks Gmail message ID of rejection email
   - `rejection_reply_count` - Counts responses (max 3)

---

## 🔄 Complete Workflow

### 1. Candidate Gets Rejected
```
Hiring manager clicks "Reject" in admin dashboard
↓
System sends rejection email via Gmail
↓
rejection_message_id is stored in database
↓
rejection_reply_count is initialized to 0
```

### 2. Candidate Replies to Rejection Email
```
Candidate replies to rejection email
↓
Reply Watcher detects it's a rejection reply (matches rejection_message_id)
↓
Routes to rejection_reply_queue
↓
Orchestrator picks it up and calls RejectionReplyHandler
```

### 3. AI Agent Analyzes and Responds
```
RejectionReplyHandler receives the reply
↓
Checks if rejection_reply_count < 3 (MAX_RESPONSES)
↓
If limit reached: Logs and ignores (no response)
↓
If under limit:
  - Analyzes intent with LLM (reconsideration, feedback, question, gratitude, etc.)
  - Generates empathetic, contextual response
  - Sends email via Gmail
  - Increments rejection_reply_count
  - Logs to audit trail
```

---

## 🧪 Testing the System

### Test Case 1: Reconsideration Request (Like Ubaid's Case)

**Scenario**: Candidate asks for another chance, mentions hardship

**Example Reply from Candidate**:
```
Han yaar dekh lo agar ho sake to 1 machine se Kuch nahi khaya
Ghar mein bivi bachay bhokay hain. Agar aap Kaho to apna cv bhaijun?
```

**Expected AI Response**:
- Acknowledges their situation with empathy
- Explains decision was based on job requirements, not personal circumstances
- Firm but kind - decision stands
- Offers to keep resume on file for future opportunities
- Encourages them to apply for other positions
- Professional but human tone

**How to Test**:
1. Go to http://localhost:3000/candidates
2. Find Ubaid's application (muhammadubaidansari145@gmail.com)
3. If not already rejected, click "Reject"
4. Have Ubaid reply to the rejection email with a reconsideration request
5. Wait 1-2 minutes for reply watcher to detect it
6. Check Ubaid's email for empathetic response

---

### Test Case 2: Feedback Request

**Example Reply from Candidate**:
```
Thank you for letting me know. Could you please provide feedback
on why I wasn't selected? I'd like to improve for future applications.
```

**Expected AI Response**:
- Thanks them for interest in feedback
- Explains we look for specific experience alignment
- Mentions competition was strong
- Offers general encouragement
- Suggests continuing skill development
- Constructive and supportive tone

---

### Test Case 3: Simple Question

**Example Reply from Candidate**:
```
Can I reapply for this position in the future if I gain more experience?
```

**Expected AI Response**:
- Answers their question professionally
- Transparent but tactful
- Provides helpful information
- Maintains supportive tone

---

### Test Case 4: Gratitude

**Example Reply from Candidate**:
```
Thank you for considering my application. I appreciate the opportunity
and wish you all the best in finding the right candidate.
```

**Expected AI Response**:
- Thanks them for their graciousness
- Wishes them well in their search
- Keeps door open for future opportunities
- Brief but warm

---

### Test Case 5: Testing the 3-Response Limit

**How to Test**:
1. Have candidate reply to rejection email (Response #1)
2. Wait for AI response
3. Reply again (Response #2)
4. Wait for AI response
5. Reply a third time (Response #3 - FINAL)
6. Wait for AI response (should include "This will be my final response...")
7. Reply a fourth time
8. **No response should be sent** - limit reached

**Verification**:
```sql
-- Check rejection_reply_count in database
SELECT id, email, rejection_reply_count
FROM candidates
WHERE email = 'muhammadubaidansari145@gmail.com';
```

Expected: `rejection_reply_count = 3` after 3 responses

---

## 📊 Intent Types Detected

The AI analyzes replies and categorizes them:

1. **reconsideration** - Asking for another chance, mentioning hardship
2. **feedback** - Asking why they were rejected
3. **question** - Asking about the process or decision
4. **gratitude** - Thanking despite rejection
5. **disappointment** - Expressing disappointment but accepting
6. **other** - General empathetic response

Each intent type gets a tailored response strategy.

---

## 🎯 Key Features

### 1. Empathetic, Contextual Responses

**Before (No Response)**:
```
[Candidate replies to rejection]
[Silence - no response]
```

**After (LLM-Generated)**:
```
Hi Ubaid,

I truly appreciate you reaching out, and I understand how challenging
this situation must be for you. I want to be honest and transparent
with you - the decision was based on the specific technical requirements
for this role, not on your personal circumstances.

While I wish I could change the outcome, the decision stands based on
the job requirements. However, I'd be happy to keep your resume on file
for future opportunities that might be a better fit.

I encourage you to continue applying for other positions, and I genuinely
wish you the best in your job search.

Best regards,
AI Recruiting Assistant
```

### 2. Response Limiting

- Maximum 3 responses per rejected candidate
- Prevents endless conversations
- Final response includes note: "This will be my final response on this matter"
- After limit: Logs to audit but doesn't send email

### 3. Audit Trail

Every interaction is logged:
```sql
SELECT * FROM audit_log
WHERE action_type = 'handle_rejection_reply'
ORDER BY created_at DESC;
```

Includes:
- Candidate ID
- Reply text (first 500 chars)
- Intent detected
- Response sent
- Reply count
- Timestamp

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
```

### Adjusting Response Limit
Edit `backend/services/rejection_reply_handler.py`:
```python
class RejectionReplyHandler:
    MAX_RESPONSES = 3  # Change this to adjust limit
```

---

## 📝 Logs and Monitoring

### Backend Logs
```bash
# Watch all logs
pm2 logs candidate-screening-backend

# Watch rejection reply handler specifically
pm2 logs candidate-screening-backend | grep "rejection"

# Check orchestrator queue consumers
pm2 logs candidate-screening-backend | grep "queue consumer"
```

### Database Queries

**Check rejection reply counts**:
```sql
SELECT
    c.id,
    c.email,
    c.name,
    c.rejection_reply_count,
    c.rejection_message_id,
    c.status
FROM candidates c
WHERE c.status = 'rejected'
ORDER BY c.updated_at DESC;
```

**Check audit logs for rejection replies**:
```sql
SELECT
    al.created_at,
    c.email,
    al.action_type,
    al.result,
    al.output_summary
FROM audit_log al
JOIN candidates c ON al.candidate_id = c.id
WHERE al.action_type IN ('handle_rejection_reply', 'rejection_reply_limit_reached')
ORDER BY al.created_at DESC;
```

---

## 🐛 Troubleshooting

### Issue: Candidate replies but no response

**Check 1: Is reply watcher running?**
```bash
pm2 logs candidate-screening-backend | grep "ReplyWatcher"
```
Should see: "Starting ReplyWatcher (check interval: 60s)"

**Check 2: Is rejection_message_id stored?**
```sql
SELECT rejection_message_id FROM candidates WHERE email = 'candidate@email.com';
```
Should not be NULL for rejected candidates.

**Check 3: Is rejection_reply_queue being consumed?**
```bash
pm2 logs candidate-screening-backend | grep "rejection reply queue"
```
Should see: "Starting rejection reply queue consumer"

**Check 4: Check Redis queue**
```bash
redis-cli
> LLEN rejection_reply_queue
```
Should be 0 if processing correctly.

**Check 5: Check for errors**
```bash
pm2 logs candidate-screening-backend --err
```

---

## ✅ Verification Checklist

After implementation, verify:

- [ ] Database migration completed (rejection_message_id, rejection_reply_count columns exist)
- [ ] PM2 services running (backend, frontend)
- [ ] All 4 queue consumers running (screening, reply, scheduling, rejection)
- [ ] Reply watcher detecting rejection replies
- [ ] Rejection emails store message_id in database
- [ ] AI responds to first rejection reply
- [ ] AI responds to second rejection reply
- [ ] AI responds to third rejection reply with "final response" note
- [ ] AI does NOT respond to fourth rejection reply
- [ ] Audit logs capture all interactions

---

## 🚀 What's Next

### Enhancements You Can Add:

1. **Sentiment Analysis**
   - Detect angry/frustrated candidates
   - Escalate to human if needed
   - Adjust tone based on sentiment

2. **Multi-Language Support**
   - Detect candidate's language
   - Respond in their language
   - Support Urdu, Hindi, Arabic, etc.

3. **Alternative Job Suggestions**
   - Analyze candidate's skills
   - Suggest other open positions
   - Auto-apply if they're interested

4. **Feedback Collection**
   - Ask for feedback on hiring process
   - Improve candidate experience
   - Track satisfaction metrics

---

## 📚 Code References

- **Rejection Reply Handler**: `backend/services/rejection_reply_handler.py`
- **Reply Watcher**: `backend/watchers/reply_watcher.py`
- **Orchestrator**: `backend/orchestrator.py`
- **Approval Flow**: `backend/routers/approvals.py`
- **Database Models**: `backend/db/models.py`
- **Database Migration**: `backend/add_rejection_reply_fields.py`

---

## 🎉 Summary

You now have a **fully empathetic rejection reply handler** that:
- Responds to rejected candidates with understanding and professionalism
- Uses LLM to understand intent and generate contextual responses
- Limits responses to 3 per candidate to prevent endless conversations
- Maintains your brand reputation with empathetic, human-like communication
- Runs 24/7 with PM2 process management

**No more ignored rejection replies!** 🎉

The agent adapts to each candidate's situation and responds with empathy while maintaining professional boundaries.

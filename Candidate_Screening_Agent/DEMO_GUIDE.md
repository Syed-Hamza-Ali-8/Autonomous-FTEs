# Candidate Screening Agent - Complete Demo Guide

## System Overview

This is an **AI-powered candidate screening system** that automates the initial stages of recruitment while keeping humans in the loop for final decisions.

### What Problem Does It Solve?

**Before this system:**
- HR manually reviews 50-100 CVs per job posting (2-3 hours)
- Manually sends screening questions to qualified candidates (1-2 hours)
- Manually reviews responses and schedules interviews (2-3 hours)
- **Total: 5-8 hours per job posting**

**With this system:**
- AI automatically scores CVs against job rubrics (2 minutes per candidate)
- AI generates personalized screening questions (30 seconds)
- AI analyzes candidate replies and provides recommendations
- Human only reviews AI recommendations and approves/rejects (5-10 minutes)
- **Total: 15-30 minutes of human time per job posting**

**Time Savings: 7.5 hours per job posting (93% reduction)**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         EMAIL WORKFLOW                           │
└─────────────────────────────────────────────────────────────────┘

1. Candidate emails CV → h05101092@gmail.com (with label "jobs")
2. Gmail Watcher detects new email (every 2 min)
3. Extracts PDF CV and creates candidate record
4. Pushes to Redis screening_queue
5. Orchestrator processes candidate:
   - Scores CV with Groq AI (gpt-oss-20b model)
   - Generates screening questions
   - Sends questions via Gmail
6. Candidate replies to email
7. Reply Watcher detects reply (every 1 min)
8. Orchestrator analyzes reply with AI
9. Creates pending approval for hiring manager
10. Human reviews in web UI and approves/rejects
11. System sends interview invite or rejection email

┌─────────────────────────────────────────────────────────────────┐
│                         TECH STACK                               │
└─────────────────────────────────────────────────────────────────┘

Backend:
- FastAPI (Python 3.12)
- PostgreSQL (Neon cloud database)
- Redis (message queues)
- SQLAlchemy (async ORM)
- Gmail API (OAuth2)
- Groq API (AI scoring)

Frontend:
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Responsive design

Background Workers:
- Orchestrator (processes queues)
- Gmail Watcher (polls inbox)
- Reply Watcher (polls for replies)
- Daily Digest (8 AM summary email)
```

---

## How to Test the System

### Option 1: Email-Driven Test (Real Workflow)

**Step 1: Send a Test Application**

Send an email to `h05101092@gmail.com` with:
- **Subject:** Application for Senior Backend Engineer
- **Label:** Add "jobs" label in Gmail
- **Attachment:** A PDF resume/CV

**Step 2: Watch the Magic Happen**

Within 2 minutes, the system will:
1. Detect the email
2. Extract CV text from PDF
3. Score the candidate (0-100)
4. Generate 3-5 screening questions
5. Send questions back to the candidate

**Step 3: Reply to Screening Questions**

Reply to the email with answers to the questions.

**Step 4: Review in Web UI**

1. Open http://localhost:3000
2. Go to "Pending Approvals"
3. See AI recommendation with score
4. Click "Approve" or "Reject"
5. System sends interview invite or rejection email

### Option 2: Direct Database Test (Quick Demo)

Since the email workflow requires Gmail access, here's how to test with direct database insertion:

```bash
# Create a test candidate directly in the database
curl -X POST http://localhost:8000/api/jobs/1/test-candidate \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "John Doe",
    "cv_text": "Senior Software Engineer with 8 years of experience in Python, FastAPI, PostgreSQL, Redis, and distributed systems. Built scalable microservices handling 10M+ requests/day. Expert in async programming, API design, and database optimization."
  }'
```

**Note:** This endpoint needs to be implemented. For now, the system is email-driven only.

---

## Current System State

### Jobs Available

```bash
curl http://localhost:8000/api/jobs
```

**Job ID 1: Senior Backend Engineer**
- Rubric: `rubrics/Senior_Backend_Engineer.md`
- Hiring Manager: h05101092@gmail.com
- Status: Active

### Candidates

```bash
curl http://localhost:8000/api/candidates
```

Currently: **0 candidates** (system is ready to receive applications)

### Pending Approvals

```bash
curl http://localhost:8000/api/approvals/pending
```

Currently: **0 pending approvals**

---

## Web UI Features

### 1. Dashboard (http://localhost:3000)
- Overview of all jobs
- Candidate pipeline statistics
- Recent activity
- Quick actions

### 2. Jobs Page (http://localhost:3000/jobs)
- List of all job postings
- Candidate counts per job
- View job details

### 3. Job Detail Page (http://localhost:3000/jobs/1)
- Job description
- Rubric details
- All candidates for this job
- Status breakdown

### 4. Candidates Page (http://localhost:3000/candidates)
- All candidates across all jobs
- Filter by status:
  - queued
  - scoring
  - scored
  - questions_sent
  - awaiting_reply
  - replied
  - shortlisted
  - rejected
  - hired
  - manual_review
- View candidate details

### 5. Pending Approvals (http://localhost:3000/approvals)
- AI recommendations waiting for human review
- One-page candidate brief
- Approve/Reject actions
- Sends emails automatically

---

## AI Scoring System

### Rubric-Based Evaluation

Each job has a rubric (Markdown file) that defines:

1. **Must-Have Requirements** (Pass/Fail)
   - If candidate doesn't meet these, auto-reject

2. **Scoring Criteria** (0-10 scale each)
   - Technical Skills (40%)
   - System Design (30%)
   - Problem Solving (20%)
   - Communication (10%)

3. **Screening Questions**
   - AI generates 3-5 personalized questions based on CV

4. **Red Flags**
   - Job hopping
   - Lack of experience
   - Poor communication

### Example Rubric

See: `backend/rubrics/Senior_Backend_Engineer.md`

---

## Safety Features

### DRY_RUN Mode

Currently enabled in `.env`:
```bash
DRY_RUN=true
```

When enabled:
- ✅ All processing happens normally
- ✅ Database records created
- ✅ AI scoring works
- ❌ NO emails actually sent (logged only)

**To enable real emails:**
```bash
DRY_RUN=false
```

### Human-in-the-Loop

- AI never makes final decisions
- All actions require human approval
- Audit log tracks every action
- Hiring manager gets daily digest

---

## API Endpoints

### Jobs
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Job details with candidates
- `POST /api/jobs` - Create new job

### Candidates
- `GET /api/candidates` - All candidates
- `GET /api/candidates/{id}` - Candidate details
- `GET /api/candidates/by-status/{status}` - Filter by status
- `GET /api/candidates/{id}/brief` - One-page brief

### Approvals
- `GET /api/approvals/pending` - Pending approvals
- `POST /api/approvals/{id}/approve` - Approve candidate
- `POST /api/approvals/{id}/reject` - Reject candidate

### Health
- `GET /health` - System health check
- `GET /` - API info

---

## Portfolio Value

### Why This Project Stands Out

1. **Real-World Problem**: Solves actual HR pain point
2. **Full-Stack**: Backend + Frontend + AI + Email + Database
3. **Production-Ready**: Error handling, logging, monitoring
4. **Modern Stack**: Latest technologies (Next.js 14, FastAPI, Groq)
5. **AI Integration**: Practical use of LLMs (not just chatbot)
6. **Event-Driven**: Redis queues, background workers
7. **Human-in-the-Loop**: Shows understanding of AI limitations
8. **Email Automation**: Gmail API integration
9. **Responsive Design**: Mobile-first UI
10. **Cloud Database**: Neon PostgreSQL

### Skills Demonstrated

**Backend:**
- Python 3.12, FastAPI
- Async/await programming
- SQLAlchemy ORM
- PostgreSQL database design
- Redis message queues
- Background workers
- Gmail API (OAuth2)
- PDF processing
- RESTful API design

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- React hooks
- Tailwind CSS
- Responsive design
- Client/Server components
- Error boundaries

**AI/ML:**
- Groq API integration
- Prompt engineering
- Rubric-based evaluation
- Natural language processing

**DevOps:**
- Docker Compose
- Environment configuration
- Health checks
- Logging and monitoring

**Architecture:**
- Event-driven design
- Microservices patterns
- Queue-based processing
- Separation of concerns

---

## How to Present in Portfolio

### 1. Demo Video (3-5 minutes)

**Script:**
1. Show the problem (manual CV screening)
2. Show the solution (automated workflow)
3. Walk through the UI
4. Show AI scoring in action
5. Show approval workflow
6. Highlight time savings

### 2. GitHub README

Include:
- Problem statement
- Architecture diagram
- Tech stack
- Setup instructions
- Screenshots
- Demo video link
- Live demo link (if deployed)

### 3. Live Demo

Deploy to:
- **Backend:** Railway, Render, or Fly.io
- **Frontend:** Vercel or Netlify
- **Database:** Neon (already using)
- **Redis:** Upstash or Redis Cloud

### 4. Case Study

Write a blog post:
- "Building an AI-Powered Candidate Screening System"
- Technical challenges and solutions
- AI prompt engineering
- Email automation
- Performance optimization

---

## Next Steps to Make Portfolio-Ready

### 1. Add Test Endpoint (Optional)

Create `/api/jobs/{job_id}/test-candidate` endpoint for quick demos without email.

### 2. Add Dashboard Analytics

- Candidates processed today/week/month
- Average processing time
- Approval rate
- Top candidates

### 3. Add Audit Log UI

Show all AI actions and human decisions.

### 4. Deploy to Cloud

- Set up CI/CD pipeline
- Configure production environment
- Add monitoring (Sentry, LogRocket)

### 5. Create Demo Video

- Screen recording with voiceover
- Show complete workflow
- Highlight key features

### 6. Write Documentation

- API documentation (Swagger/OpenAPI)
- User guide
- Developer setup guide
- Architecture decision records

---

## Troubleshooting

### Backend not starting
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

### Frontend not starting
```bash
cd frontend
npm run dev
```

### Database connection error
Check `.env` file has correct `DATABASE_URL`

### Redis connection error
```bash
docker-compose up -d redis
```

### Gmail API not working
1. Check credentials in `.env`
2. Verify OAuth2 consent screen
3. Check refresh token is valid

---

## Contact

For questions or issues, contact the hiring manager at h05101092@gmail.com

---

**Built with ❤️ using FastAPI, Next.js, and Groq AI**

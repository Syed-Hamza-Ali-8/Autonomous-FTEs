# Candidate Screening Agent - Implementation Plan

**Feature**: Autonomous Candidate Screening Digital FTE
**Status**: Draft
**Created**: 2026-04-27
**Last Updated**: 2026-04-27

---

## Executive Summary

This plan outlines the architecture and implementation strategy for the Candidate Screening Agent. The system follows an event-driven architecture with background watchers, Redis job queues, and async orchestration. All AI reasoning uses Grok via OpenAI Agents SDK. Human-in-the-loop (HITL) boundaries are enforced through a pending approvals system.

**Key Architectural Decisions**:
1. Async-first with FastAPI and SQLAlchemy async
2. Event-driven with Redis queues for decoupling
3. Background watchers for Gmail polling (no webhooks)
4. Grok API via OpenAI-compatible interface
5. PostgreSQL for persistence with comprehensive audit logging
6. Next.js 14 App Router for dashboard with real-time polling

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gmail Inbox                              │
│                    (jobs@yourdomain.com)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Background Watchers                           │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ GmailApplicationWatcher│      │   ReplyWatcher      │        │
│  │   (every 2 min)       │      │   (every 1 min)     │        │
│  └──────────┬────────────┘      └──────────┬──────────┘        │
└─────────────┼──────────────────────────────┼───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Redis Queues                             │
│         screening_queue          reply_queue                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Orchestrator                               │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │ process_new_candidate │      │ process_candidate_reply│      │
│  └──────────┬────────────┘      └──────────┬──────────┘        │
└─────────────┼──────────────────────────────┼───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Grok AI Agents                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  CV Scorer   │  │   Question   │  │    Reply     │         │
│  │  (grok-3)    │  │  Generator   │  │   Analyzer   │         │
│  │              │  │ (grok-3-mini)│  │  (grok-3)    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  jobs | candidates | pending_approvals | audit_log              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  /candidates | /approvals | /jobs | /health                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard                             │
│  Pipeline Board | Candidate Details | Approval Panel            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Database Layer (`backend/db/`)

**Purpose**: Persistent storage with async SQLAlchemy ORM.

**Components**:
- `models.py`: SQLAlchemy models for all tables
- `database.py`: Async engine, session factory, `get_db()` dependency
- `crud.py`: CRUD operations for all entities

**Key Decisions**:
- Use `asyncpg` driver for PostgreSQL (fastest async driver)
- Use `async_sessionmaker` for session management
- Indexes on `candidates.status`, `candidates.job_id`, `pending_approvals.status`
- JSON columns for flexible data (score_breakdown, screening_questions, reply_analysis)
- Timestamps with `TIMESTAMPTZ` for timezone awareness

**Schema Design**:
```sql
jobs (id, title, slug, rubric_path, status, created_at)
  ↓ 1:N
candidates (id, job_id, email, name, cv_text, status, total_score,
            must_haves_met, score_breakdown, strengths, weaknesses,
            red_flags, recommendation, confidence, score_summary,
            screening_questions, candidate_reply, reply_analysis,
            gmail_message_id, created_at, updated_at)
  ↓ 1:N
pending_approvals (id, candidate_id, job_id, action, score,
                   recommendation, brief_summary, status, approved_by,
                   created_at, expires_at)

audit_log (id, candidate_id, action_type, actor, input_summary,
           output_summary, approval_status, approved_by, result, created_at)
```

### 2. AI Agent Layer (`backend/screening_agent.py`)

**Purpose**: Grok-powered AI reasoning for candidate evaluation.

**Components**:
- `get_grok_model(model_name)`: Factory for Grok model instances
- `score_candidate(cv_text, rubric_path)`: CV scoring agent
- `generate_screening_questions(cv_text, rubric_path)`: Question generation agent
- `analyze_reply(questions, reply_text, original_score)`: Reply analysis agent

**Key Decisions**:
- Use `OpenAIChatCompletionsModel` (NOT `OpenAIResponsesModel`)
- Always call `set_tracing_disabled(True)` at module top
- Model selection: `grok-3` for deep reasoning, `grok-3-mini` for fast tasks
- JSON-only output with strict parsing and retry logic
- Retry once on JSON parse failure with stricter prompt

**Agent Prompts**:
```python
# CV Scorer (grok-3)
instructions = """
You are an expert technical recruiter. Score this CV objectively based ONLY on the rubric.
Return ONLY valid JSON with no markdown, no prose, no explanations.
Required fields: total_score, must_haves_met, disqualification_reason,
skill_score, experience_score, project_score, communication_score,
bonuses_applied, red_flags, strengths, weaknesses, recommendation,
confidence, summary
"""

# Question Generator (grok-3-mini)
instructions = """
Generate exactly 5 personalized screening questions for this candidate.
Reference specific items from their CV. Align with rubric requirements.
Return ONLY a JSON array of 5 strings. No markdown, no prose.
"""

# Reply Analyzer (grok-3)
instructions = """
Analyze the candidate's replies to screening questions.
Return ONLY valid JSON with: reply_score_delta (-20 to +20),
final_score, answer_quality (high/medium/low), notable_answers (array),
updated_recommendation (advance/reject/review), brief_summary
"""
```

### 3. Services Layer (`backend/services/`)

**Purpose**: Reusable business logic for external integrations.

**Components**:

**`pdf_service.py`**:
- `extract_text_from_pdf(pdf_bytes)`: Extract text using pdfplumber
- Handle scanned PDFs (return "Scanned PDF — manual review required")
- Strip excess whitespace, join pages

**`gmail_service.py`**:
- `GmailService` class with OAuth2 authentication
- `send_email(to, subject, body)`: Base email sending
- `send_screening_questions(to, candidate_name, job_title, questions)`: Template-based
- `send_interview_invite(to, candidate_name, job_title)`: Template-based
- `send_rejection_email(to, candidate_name, job_title, reason)`: Empathetic template
- `send_daily_digest(to, digest_data)`: Daily summary email
- DRY_RUN mode: log to console, return fake message ID

**`audit_service.py`**:
- `log_action(db, action_type, actor, result, **kwargs)`: Wrapper around `crud.create_audit_log`
- Catch and log DB errors silently (audit failures never crash pipeline)

**Key Decisions**:
- Gmail OAuth2 with refresh token (no password authentication)
- DRY_RUN mode by default for safety
- Exponential backoff retry for Gmail API timeouts
- Audit service never raises exceptions

### 4. Watchers Layer (`backend/watchers/`)

**Purpose**: Background polling for Gmail events.

**Components**:

**`base_watcher.py`**:
- Abstract base class with `check_for_updates()` and `handle_item()` methods
- `run()` method with infinite loop and error recovery
- Configurable check interval

**`gmail_watcher.py`**:
- `GmailApplicationWatcher`: Polls for new applications every 2 minutes
- Tracks processed message IDs in `processed_ids.json`
- Extracts PDF attachment, calls `pdf_service.extract_text_from_pdf()`
- Creates candidate record via `crud.create_candidate()`
- Pushes `candidate_id` to Redis `screening_queue`

**`reply_watcher.py`**:
- `ReplyWatcher`: Polls for replies every 1 minute
- Matches replies using `In-Reply-To` / `References` headers
- Queries candidates with status `awaiting_reply`
- Pushes `(candidate_id, reply_text)` to Redis `reply_queue`

**Key Decisions**:
- Polling (not webhooks) for simplicity and reliability
- Persistent tracking of processed IDs to avoid duplicates
- Error recovery: log and continue (never crash watcher loop)
- Redis queues decouple watchers from orchestrator

### 5. Orchestrator Layer (`backend/orchestrator.py`)

**Purpose**: Core business logic for candidate pipeline.

**Components**:

**`process_new_candidate(candidate_id, db)`**:
1. Fetch candidate from DB
2. Call `score_candidate()` with Grok
3. Update DB with score
4. If `must_haves_met == False`:
   - Create `pending_approval` with action="reject"
   - Return (skip screening questions)
5. Call `generate_screening_questions()` with Grok
6. Call `gmail_service.send_screening_questions()`
7. Update status to "awaiting_reply"
8. Log to audit_log

**`process_candidate_reply(candidate_id, reply_text, db)`**:
1. Fetch candidate + original score
2. Call `analyze_reply()` with Grok
3. Update candidate with reply + final score
4. Create `pending_approval` with action="advance"
5. Log to audit_log

**`run_orchestrator()`**:
- Use `asyncio.gather()` to consume both queues concurrently
- Use `redis.brpop(timeout=1)` for non-blocking loop
- Handle exceptions and log errors

**Key Decisions**:
- Orchestrator is stateless (all state in DB)
- Redis queues provide at-least-once delivery
- Concurrent processing of screening and reply queues
- All DB operations in transactions

### 6. API Layer (`backend/routers/`)

**Purpose**: REST API for dashboard and external integrations.

**Components**:

**`candidates.py`**:
- `GET /candidates`: List all candidates with scores
- `GET /candidates/{id}`: Full candidate detail
- `GET /candidates/by-status/{status}`: Filter by status
- `GET /candidates/{id}/brief`: One-page candidate brief

**`approvals.py`**:
- `GET /approvals/pending`: List pending approvals
- `POST /approvals/{id}/approve`: Approve candidate (triggers interview invite)
- `POST /approvals/{id}/reject`: Reject candidate (triggers rejection email)

**`jobs.py`**:
- `GET /jobs`: List all jobs
- `POST /jobs`: Create job with rubric
- `GET /jobs/{id}`: Job detail with candidate counts

**Key Decisions**:
- RESTful design with standard HTTP methods
- Async route handlers with `async def`
- Dependency injection for DB session via `get_db()`
- CORS enabled for Next.js frontend
- Swagger UI at `/docs` for API exploration

### 7. Daily Digest (`backend/daily_digest.py`)

**Purpose**: Automated daily summary email to hiring manager.

**Components**:
- `send_daily_digest(db)`: Main function
- Fetch candidates from past 24 hours
- Group by status
- Use Grok `grok-3-mini` to generate 3-sentence summary
- Call `gmail_service.send_daily_digest()`
- Schedule with APScheduler at 8:00 AM daily

**Key Decisions**:
- APScheduler for cron-like scheduling
- Grok mini for fast, cheap summarization
- Digest includes: new applications, pending approvals, shortlisted, rejected

### 8. Main Application (`backend/main.py`)

**Purpose**: FastAPI application with lifespan management.

**Components**:
- `lifespan()` context manager:
  - Initialize database (`init_db()`)
  - Start orchestrator task
  - Start watcher tasks
  - Setup APScheduler
- FastAPI app with CORS middleware
- Include all routers
- Health check endpoint

**Key Decisions**:
- Use `asynccontextmanager` for lifespan events
- Background tasks via `asyncio.create_task()`
- Graceful shutdown on SIGTERM

### 9. Frontend (`frontend/`)

**Purpose**: Next.js dashboard for hiring manager.

**Components**:

**`app/page.tsx`** (Dashboard):
- Fetch `/candidates` and `/approvals/pending` every 30 seconds
- Display `DigestBanner` with today's stats
- Display `PipelineBoard` with 4 columns
- Pending approval count badge in nav

**`app/candidates/[id]/page.tsx`** (Candidate Detail):
- Fetch `/candidates/{id}` and `/candidates/{id}/brief`
- Display score breakdown with `ScoreBar`
- Display strengths, weaknesses, red flags
- Display screening Q&A
- Display `ApprovalPanel` if status is `pending_approval`

**Components**:
- `CandidateCard.tsx`: Card with score badge, status pill
- `ScoreBar.tsx`: Visual score representation
- `ApprovalPanel.tsx`: Approve/reject buttons with AI recommendation
- `PipelineBoard.tsx`: Kanban board with 4 columns
- `DigestBanner.tsx`: Top banner with stats

**Key Decisions**:
- Next.js 14 App Router (not Pages Router)
- Tailwind CSS for styling
- Client-side polling every 30 seconds (no WebSockets)
- Optimistic UI updates on approve/reject

---

## Data Flow

### Flow 1: New Application Processing

```
1. Gmail Inbox receives email with PDF CV
2. GmailApplicationWatcher polls Gmail API (every 2 min)
3. Watcher downloads PDF, extracts text with pdfplumber
4. Watcher creates candidate record in DB
5. Watcher pushes candidate_id to Redis screening_queue
6. Orchestrator pops from screening_queue
7. Orchestrator calls score_candidate() with Grok grok-3
8. Orchestrator updates DB with score
9. If disqualified:
   - Create pending_approval with action="reject"
   - End flow (skip screening questions)
10. If qualified:
    - Call generate_screening_questions() with Grok grok-3-mini
    - Call gmail_service.send_screening_questions()
    - Update status to "awaiting_reply"
11. Log to audit_log
```

### Flow 2: Candidate Reply Processing

```
1. Candidate replies to screening email
2. ReplyWatcher polls Gmail API (every 1 min)
3. Watcher matches reply to candidate via message headers
4. Watcher pushes (candidate_id, reply_text) to Redis reply_queue
5. Orchestrator pops from reply_queue
6. Orchestrator calls analyze_reply() with Grok grok-3
7. Orchestrator updates DB with reply + final score
8. Orchestrator creates pending_approval with action="advance"
9. Log to audit_log
```

### Flow 3: Human Approval

```
1. Hiring manager opens dashboard
2. Dashboard fetches /approvals/pending
3. Manager clicks candidate to view details
4. Manager reviews AI recommendation + score
5. Manager clicks "Approve" or "Reject"
6. Frontend calls POST /approvals/{id}/approve or /reject
7. Backend updates approval status
8. Backend calls gmail_service.send_interview_invite() or send_rejection_email()
9. Backend updates candidate status
10. Log to audit_log with approver email
```

### Flow 4: Daily Digest

```
1. APScheduler triggers at 8:00 AM
2. send_daily_digest() fetches candidates from past 24 hours
3. Group by status (applied, screening, shortlisted, rejected)
4. Call Grok grok-3-mini to generate 3-sentence summary
5. Call gmail_service.send_daily_digest() to hiring manager
6. Log to audit_log
```

---

## Technology Stack Rationale

### Backend: FastAPI + Async

**Why FastAPI?**
- Native async/await support (critical for I/O-heavy workload)
- Automatic OpenAPI/Swagger documentation
- Pydantic validation built-in
- High performance (comparable to Node.js)

**Why Async?**
- Multiple concurrent candidates
- Gmail polling (2 watchers running continuously)
- Grok API calls (can take 5-30 seconds)
- Database queries
- Blocking I/O would create bottlenecks

### Database: PostgreSQL + SQLAlchemy Async

**Why PostgreSQL?**
- ACID compliance (critical for candidate data)
- JSON columns for flexible data (score_breakdown, etc.)
- Mature async driver (asyncpg)
- Strong indexing for status queries

**Why SQLAlchemy Async?**
- ORM abstraction (easier than raw SQL)
- Async support via asyncpg
- Migration support via Alembic
- Type safety with Pydantic models

### Queue: Redis

**Why Redis?**
- Simple pub/sub and list operations
- Fast (in-memory)
- Async client (redis.asyncio)
- Fallback to in-memory if unavailable

**Why Not Kafka/RabbitMQ?**
- Overkill for this use case
- Redis is simpler to deploy and manage
- No need for complex routing or persistence

### AI: Grok via OpenAI Agents SDK

**Why Grok?**
- State-of-the-art reasoning (comparable to GPT-4)
- OpenAI-compatible API (easy integration)
- Cost-effective (grok-3-mini for fast tasks)

**Why OpenAI Agents SDK?**
- Structured agent framework
- Built-in retry and error handling
- Easy to test with mocks

### Frontend: Next.js 14 + Tailwind

**Why Next.js 14?**
- App Router for modern React patterns
- Server components for performance
- Easy deployment to Vercel
- TypeScript support

**Why Tailwind CSS?**
- Rapid UI development
- Consistent design system
- No CSS-in-JS overhead

---

## Error Handling Strategy

### Transient Errors (Retry)

**Gmail API Timeout**:
```python
@with_retry(max_attempts=3, base_delay=2)
async def fetch_emails():
    # Exponential backoff: 2s → 4s → 8s
    pass
```

**Grok API Error**:
```python
try:
    result = await score_candidate(cv_text, rubric_path)
except Exception as e:
    logger.error(f"Grok API error: {e}")
    await crud.update_candidate_status(db, candidate_id, "manual_review")
    await audit_service.log_action(db, "score_candidate", "grok-3", "failure")
```

**JSON Parse Error**:
```python
try:
    data = json.loads(result.final_output)
except json.JSONDecodeError:
    # Retry once with stricter prompt
    result = await Runner.run(agent, "Return ONLY valid JSON. No markdown.")
    data = json.loads(result.final_output)  # Raise if still fails
```

### Permanent Errors (Fail Loudly)

**Database Unavailable**:
```python
# Never catch DB errors — let them propagate
# System should crash and restart
async def create_candidate(db, ...):
    # No try/except here
    db.add(candidate)
    await db.commit()
```

**Redis Unavailable**:
```python
# Fall back to in-memory queue
try:
    await redis.lpush("screening_queue", candidate_id)
except redis.ConnectionError:
    logger.warning("Redis unavailable, using in-memory queue")
    in_memory_queue.append(candidate_id)
```

### Audit Failures (Never Crash)

```python
async def log_action(db, action_type, actor, result, **kwargs):
    try:
        await crud.create_audit_log(db, action_type, actor, result, **kwargs)
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
        # Never raise — audit failures should not crash pipeline
```

---

## Security Considerations

### Secrets Management

- All secrets in `.env` file (never committed)
- Use `python-dotenv` and `os.getenv()`
- OAuth2 for Gmail (no password storage)
- Grok API key in environment variable

### DRY_RUN Mode

```python
def send_email(self, to, subject, body):
    if os.getenv("DRY_RUN", "true").lower() == "true":
        logger.info(f"[DRY_RUN] Email to {to}: {subject}")
        return f"fake_msg_id_{uuid.uuid4().hex[:8]}"
    return self._send_real_email(to, subject, body)
```

### Audit Trail

- Every AI decision logged with input/output
- Every human action logged with approver email
- Timestamps for all actions
- Immutable audit log (no updates or deletes)

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing Strategy

### Unit Tests

**Target Coverage**: 75-95% depending on module

**Approach**:
- Mock all external APIs (Grok, Gmail)
- Use in-memory SQLite for DB tests
- Use `pytest-asyncio` for async tests
- Use `pytest-mock` for mocking

**Example**:
```python
@pytest.mark.asyncio
async def test_score_candidate_returns_valid_dict(sample_cv_text, sample_rubric_path):
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(sample_score))
        result = await score_candidate(sample_cv_text, sample_rubric_path)
    assert result["total_score"] == 82
```

### Integration Tests

**Focus Areas**:
- End-to-end candidate flow (application → scoring → questions → reply → approval)
- Database transactions and rollbacks
- Redis queue operations
- Gmail API integration (with test account)

### Manual Testing

**Test Cases**:
1. Send test email with PDF CV to jobs inbox
2. Verify candidate appears in dashboard within 2 minutes
3. Verify screening questions sent to candidate
4. Reply to screening email
5. Verify reply analysis and pending approval created
6. Approve candidate in dashboard
7. Verify interview invite sent

---

## Deployment Strategy

### Development Environment

```bash
# Start infrastructure
docker-compose up -d

# Backend
cd backend
uv sync
cp .env.example .env  # Fill in API keys
uv run uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev  # http://localhost:3000
```

### Production Environment

**Backend (Railway)**:
- Deploy via GitHub integration
- Set environment variables in Railway dashboard
- Use Railway PostgreSQL and Redis add-ons
- Health check endpoint: `/health`

**Frontend (Vercel)**:
- Deploy via GitHub integration
- Set `NEXT_PUBLIC_API_URL` to Railway backend URL
- Automatic deployments on push to main

**Monitoring**:
- Railway logs for backend
- Vercel logs for frontend
- PostgreSQL slow query log
- Redis memory usage alerts

---

## Performance Optimization

### Database Indexes

```sql
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_job_id ON candidates(job_id);
CREATE INDEX idx_approvals_status ON pending_approvals(status);
CREATE INDEX idx_audit_candidate ON audit_log(candidate_id);
```

### Connection Pooling

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
)
```

### Caching

- Cache job rubrics in memory (rarely change)
- Cache processed Gmail message IDs in Redis
- No caching for candidate data (always fresh)

### Rate Limiting

```python
MAX_EMAILS_PER_HOUR = int(os.getenv("MAX_EMAILS_PER_HOUR", "20"))
# Implement token bucket algorithm in gmail_service
```

---

## Rollout Plan

### Phase 1: Core Pipeline (Week 1-2)

- Database models and CRUD operations
- AI agents (scoring, questions, reply analysis)
- Services (PDF, Gmail, audit)
- Watchers (Gmail application, reply)
- Orchestrator
- Basic API endpoints

**Success Criteria**: End-to-end flow from application to pending approval

### Phase 2: Dashboard (Week 3)

- Next.js frontend setup
- Pipeline board
- Candidate detail pages
- Approval panel
- Real-time updates

**Success Criteria**: Hiring manager can approve/reject candidates via dashboard

### Phase 3: Daily Digest & Polish (Week 4)

- Daily digest email
- Error handling improvements
- Comprehensive test suite
- Documentation
- Deployment to Railway + Vercel

**Success Criteria**: All tests pass, system runs in production

### Phase 4: Monitoring & Optimization (Week 5+)

- Performance monitoring
- Error tracking
- User feedback collection
- Optimization based on real usage

---

## Open Technical Questions

1. **Q**: Should we use WebSockets for real-time dashboard updates?
   **A**: No. Polling every 30 seconds is simpler and sufficient for this use case.

2. **Q**: Should we implement rate limiting on API endpoints?
   **A**: Not in MVP. Add if abuse detected in production.

3. **Q**: Should we use Celery instead of Redis queues?
   **A**: No. Redis lists are simpler and sufficient for this use case.

4. **Q**: Should we implement database migrations with Alembic?
   **A**: Yes, but not in MVP. Use `Base.metadata.create_all()` initially.

5. **Q**: Should we implement caching for candidate data?
   **A**: No. Always fetch fresh data from DB to ensure consistency.

---

## Next Steps

1. Review and approve this plan
2. Create `tasks.md` with actionable, dependency-ordered tasks
3. Create `data-model.md` with detailed schema
4. Create `research.md` with technical spikes
5. Begin implementation following build order in constitution

---

**Approval Required**: Tech Lead, Product Owner, Security Review

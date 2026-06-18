# Candidate Screening Agent - Implementation Tasks

**Feature**: Autonomous Candidate Screening Digital FTE
**Status**: Ready for Implementation
**Created**: 2026-04-27
**Last Updated**: 2026-04-27

---

## Task Organization

Tasks are organized in dependency order. Each task includes:
- **ID**: Unique task identifier
- **Title**: Brief task description
- **Dependencies**: Tasks that must be completed first
- **Acceptance Criteria**: Testable conditions for completion
- **Estimated Effort**: S (Small: <4h), M (Medium: 4-8h), L (Large: 8-16h), XL (Extra Large: 16h+)

---

## Phase 1: Foundation & Infrastructure

### TASK-001: Project Scaffolding
**Dependencies**: None
**Effort**: S
**Acceptance Criteria**:
- [ ] Run `uv init backend` to create backend project structure
- [ ] Create all required directories: `backend/db/`, `backend/watchers/`, `backend/services/`, `backend/routers/`, `backend/rubrics/`, `backend/tests/`
- [ ] Create `frontend/` directory structure: `app/`, `app/components/`, `app/candidates/[id]/`
- [ ] Create `docker-compose.yml` with PostgreSQL and Redis services
- [ ] Create `.gitignore` with Python, Node, and environment files
- [ ] Create `backend/.env.example` and `frontend/.env.local.example`

### TASK-002: Backend Dependencies
**Dependencies**: TASK-001
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/pyproject.toml` with all required dependencies
- [ ] Run `uv sync` successfully
- [ ] Verify all packages install without errors
- [ ] Add dev dependencies: pytest, pytest-asyncio, pytest-mock, aiosqlite

### TASK-003: Database Infrastructure
**Dependencies**: TASK-002
**Effort**: M
**Acceptance Criteria**:
- [ ] Start PostgreSQL and Redis via `docker-compose up -d`
- [ ] Verify PostgreSQL connection on port 5432
- [ ] Verify Redis connection on port 6379
- [ ] Create test database connection script

---

## Phase 2: Database Layer

### TASK-004: Database Models
**Dependencies**: TASK-003
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/db/models.py` with SQLAlchemy models
- [ ] Implement `Job` model with fields: id, title, slug, rubric_path, status, created_at
- [ ] Implement `Candidate` model with all fields from spec (20+ fields including JSON columns)
- [ ] Implement `PendingApproval` model with fields: id, candidate_id, job_id, action, score, recommendation, brief_summary, status, approved_by, created_at, expires_at
- [ ] Implement `AuditLog` model with fields: id, candidate_id, action_type, actor, input_summary, output_summary, approval_status, approved_by, result, created_at
- [ ] Add foreign key relationships
- [ ] Add indexes on status, job_id, candidate_id

### TASK-005: Database Connection
**Dependencies**: TASK-004
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/db/database.py` with async engine
- [ ] Implement `AsyncSessionLocal` session factory
- [ ] Implement `get_db()` dependency for FastAPI
- [ ] Implement `init_db()` function to create all tables
- [ ] Test database connection and table creation

### TASK-006: CRUD Operations
**Dependencies**: TASK-005
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `backend/db/crud.py` with all async CRUD functions
- [ ] Implement `create_candidate()` with all required fields
- [ ] Implement `get_candidate()`, `update_candidate_status()`, `update_candidate_score()`
- [ ] Implement `update_candidate_questions()`, `update_candidate_reply()`
- [ ] Implement `create_pending_approval()`, `get_pending_approvals()`
- [ ] Implement `approve_candidate()`, `reject_candidate()`
- [ ] Implement `get_candidates_by_status()`, `get_all_candidates()`
- [ ] Implement `create_audit_log()` with all fields
- [ ] Test all CRUD operations with in-memory SQLite

---

## Phase 3: AI Agent Layer

### TASK-007: Grok Model Setup
**Dependencies**: TASK-002
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/screening_agent.py`
- [ ] Add `set_tracing_disabled(True)` at module top
- [ ] Implement `get_grok_model(model_name)` factory function
- [ ] Use `AsyncOpenAI` with base_url="https://api.x.ai/v1"
- [ ] Return `OpenAIChatCompletionsModel` instance
- [ ] Test with mock API key

### TASK-008: CV Scoring Agent
**Dependencies**: TASK-007
**Effort**: L
**Acceptance Criteria**:
- [ ] Implement `score_candidate(cv_text, rubric_path)` async function
- [ ] Create agent with name "CV Scorer" and model `grok-3`
- [ ] Load rubric from file path
- [ ] Construct prompt with CV text and rubric
- [ ] Use `Runner.run()` to execute agent
- [ ] Parse JSON output with try/except
- [ ] Implement retry logic on JSON parse failure
- [ ] Return dict with all required fields: total_score, must_haves_met, disqualification_reason, skill_score, experience_score, project_score, communication_score, bonuses_applied, red_flags, strengths, weaknesses, recommendation, confidence, summary
- [ ] Test with mock Grok API responses

### TASK-009: Question Generation Agent
**Dependencies**: TASK-007
**Effort**: M
**Acceptance Criteria**:
- [ ] Implement `generate_screening_questions(cv_text, rubric_path)` async function
- [ ] Create agent with name "Question Generator" and model `grok-3-mini`
- [ ] Construct prompt requesting exactly 5 personalized questions
- [ ] Use `Runner.run()` to execute agent
- [ ] Parse JSON array output
- [ ] Validate exactly 5 questions returned
- [ ] Test with mock Grok API responses

### TASK-010: Reply Analysis Agent
**Dependencies**: TASK-007
**Effort**: M
**Acceptance Criteria**:
- [ ] Implement `analyze_reply(questions, reply_text, original_score)` async function
- [ ] Create agent with name "Reply Analyzer" and model `grok-3`
- [ ] Construct prompt with questions, reply, and original score
- [ ] Use `Runner.run()` to execute agent
- [ ] Parse JSON output with fields: reply_score_delta, final_score, answer_quality, notable_answers, updated_recommendation, brief_summary
- [ ] Test with mock Grok API responses

---

## Phase 4: Services Layer

### TASK-011: PDF Service
**Dependencies**: TASK-002
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/services/pdf_service.py`
- [ ] Implement `extract_text_from_pdf(pdf_bytes)` function
- [ ] Use `pdfplumber` to extract text from all pages
- [ ] Handle empty/scanned PDFs (return "Scanned PDF — manual review required")
- [ ] Strip excess whitespace
- [ ] Test with sample PDF files

### TASK-012: Gmail Service
**Dependencies**: TASK-002
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `backend/services/gmail_service.py`
- [ ] Implement `GmailService` class with OAuth2 authentication
- [ ] Load credentials from environment variables
- [ ] Implement `send_email(to, subject, body)` with DRY_RUN check
- [ ] Implement `send_screening_questions(to, candidate_name, job_title, questions)`
- [ ] Implement `send_interview_invite(to, candidate_name, job_title)`
- [ ] Implement `send_rejection_email(to, candidate_name, job_title, reason)`
- [ ] Implement `send_daily_digest(to, digest_data)`
- [ ] Test in DRY_RUN mode (no real emails sent)

### TASK-013: Audit Service
**Dependencies**: TASK-006
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/services/audit_service.py`
- [ ] Implement `log_action(db, action_type, actor, result, **kwargs)` function
- [ ] Wrap `crud.create_audit_log()` with try/except
- [ ] Log errors but never raise exceptions
- [ ] Test with mock database

---

## Phase 5: Watchers Layer

### TASK-014: Base Watcher
**Dependencies**: TASK-002
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/watchers/__init__.py`
- [ ] Create `backend/watchers/base_watcher.py`
- [ ] Implement `BaseWatcher` abstract base class
- [ ] Add `check_for_updates()` abstract method
- [ ] Add `handle_item()` abstract method
- [ ] Implement `run()` method with infinite loop and error recovery
- [ ] Add configurable check_interval
- [ ] Test error recovery behavior

### TASK-015: Gmail Application Watcher
**Dependencies**: TASK-011, TASK-012, TASK-014
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `backend/watchers/gmail_watcher.py`
- [ ] Implement `GmailApplicationWatcher` class extending `BaseWatcher`
- [ ] Set check_interval to 120 seconds
- [ ] Implement `check_for_updates()` to poll Gmail API for unread emails with label "jobs"
- [ ] Track processed message IDs in `processed_ids.json`
- [ ] Implement `handle_item()` to download PDF, extract text, create candidate, push to Redis
- [ ] Skip emails without PDF attachments
- [ ] Test with mock Gmail API

### TASK-016: Reply Watcher
**Dependencies**: TASK-012, TASK-014
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/watchers/reply_watcher.py`
- [ ] Implement `ReplyWatcher` class extending `BaseWatcher`
- [ ] Set check_interval to 60 seconds
- [ ] Implement `check_for_updates()` to poll Gmail API for replies
- [ ] Match replies using `In-Reply-To` and `References` headers
- [ ] Query candidates with status "awaiting_reply"
- [ ] Implement `handle_item()` to push (candidate_id, reply_text) to Redis
- [ ] Test with mock Gmail API

---

## Phase 6: Orchestrator Layer

### TASK-017: Process New Candidate
**Dependencies**: TASK-006, TASK-008, TASK-009, TASK-012, TASK-013
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `backend/orchestrator.py`
- [ ] Implement `process_new_candidate(candidate_id, db)` async function
- [ ] Fetch candidate from database
- [ ] Call `score_candidate()` with Grok
- [ ] Update database with score
- [ ] If must_haves_met == False: create pending_approval with action="reject", return
- [ ] If qualified: call `generate_screening_questions()` with Grok
- [ ] Send screening questions via `gmail_service.send_screening_questions()`
- [ ] Update candidate status to "awaiting_reply"
- [ ] Log to audit_log
- [ ] Test with mock dependencies

### TASK-018: Process Candidate Reply
**Dependencies**: TASK-006, TASK-010, TASK-013
**Effort**: M
**Acceptance Criteria**:
- [ ] Implement `process_candidate_reply(candidate_id, reply_text, db)` async function
- [ ] Fetch candidate and original score from database
- [ ] Call `analyze_reply()` with Grok
- [ ] Update candidate with reply text and final score
- [ ] Create pending_approval with action="advance"
- [ ] Log to audit_log
- [ ] Test with mock dependencies

### TASK-019: Orchestrator Main Loop
**Dependencies**: TASK-017, TASK-018
**Effort**: M
**Acceptance Criteria**:
- [ ] Implement `run_orchestrator()` async function
- [ ] Connect to Redis
- [ ] Use `asyncio.gather()` to consume screening_queue and reply_queue concurrently
- [ ] Use `redis.brpop(timeout=1)` for non-blocking loop
- [ ] Handle exceptions and log errors
- [ ] Test with mock Redis

---

## Phase 7: API Layer

### TASK-020: Candidates Router
**Dependencies**: TASK-006
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/routers/__init__.py`
- [ ] Create `backend/routers/candidates.py`
- [ ] Implement `GET /candidates` - list all candidates
- [ ] Implement `GET /candidates/{id}` - full candidate detail
- [ ] Implement `GET /candidates/by-status/{status}` - filter by status
- [ ] Implement `GET /candidates/{id}/brief` - one-page brief
- [ ] Use async route handlers with `get_db()` dependency
- [ ] Test all endpoints

### TASK-021: Approvals Router
**Dependencies**: TASK-006, TASK-012, TASK-013
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/routers/approvals.py`
- [ ] Implement `GET /approvals/pending` - list pending approvals
- [ ] Implement `POST /approvals/{id}/approve` - approve candidate, send interview invite
- [ ] Implement `POST /approvals/{id}/reject` - reject candidate, send rejection email
- [ ] Update candidate status after approval/rejection
- [ ] Log to audit_log with approver email
- [ ] Test all endpoints

### TASK-022: Jobs Router
**Dependencies**: TASK-006
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/routers/jobs.py`
- [ ] Implement `GET /jobs` - list all jobs
- [ ] Implement `POST /jobs` - create job with rubric
- [ ] Implement `GET /jobs/{id}` - job detail with candidate counts
- [ ] Test all endpoints

---

## Phase 8: Daily Digest

### TASK-023: Daily Digest Implementation
**Dependencies**: TASK-006, TASK-007, TASK-012
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/daily_digest.py`
- [ ] Implement `send_daily_digest(db)` async function
- [ ] Fetch candidates from past 24 hours
- [ ] Group by status (applied, screening, shortlisted, rejected)
- [ ] Use Grok `grok-3-mini` to generate 3-sentence executive summary
- [ ] Call `gmail_service.send_daily_digest()` to HIRING_MANAGER_EMAIL
- [ ] Setup APScheduler to run at 8:00 AM daily
- [ ] Test with mock data

---

## Phase 9: Main Application

### TASK-024: FastAPI Application
**Dependencies**: TASK-005, TASK-015, TASK-016, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/main.py`
- [ ] Implement `lifespan()` context manager with `@asynccontextmanager`
- [ ] Call `init_db()` on startup
- [ ] Start orchestrator with `asyncio.create_task(run_orchestrator())`
- [ ] Start watchers with `asyncio.create_task(GmailApplicationWatcher().run())`
- [ ] Start reply watcher with `asyncio.create_task(ReplyWatcher().run())`
- [ ] Setup APScheduler for daily digest
- [ ] Create FastAPI app with lifespan
- [ ] Add CORS middleware with allowed origins
- [ ] Include all routers with prefixes
- [ ] Implement `GET /health` endpoint
- [ ] Test health endpoint returns {"status": "ok"}

---

## Phase 10: Frontend

### TASK-025: Frontend Setup
**Dependencies**: TASK-001
**Effort**: S
**Acceptance Criteria**:
- [ ] Run `npx create-next-app@latest frontend --typescript --tailwind --app`
- [ ] Create `frontend/package.json` with dependencies
- [ ] Install dependencies: `npm install`
- [ ] Configure `tailwind.config.ts`
- [ ] Configure `tsconfig.json`
- [ ] Create `frontend/.env.local` with NEXT_PUBLIC_API_URL
- [ ] Test `npm run dev` starts successfully

### TASK-026: Dashboard Layout
**Dependencies**: TASK-025
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `frontend/app/layout.tsx` with root layout
- [ ] Create `frontend/app/globals.css` with Tailwind imports
- [ ] Add navigation header with logo and pending approval badge
- [ ] Add responsive layout
- [ ] Test layout renders correctly

### TASK-027: Dashboard Components
**Dependencies**: TASK-026
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `frontend/app/components/CandidateCard.tsx` with score badge, status pill
- [ ] Create `frontend/app/components/ScoreBar.tsx` with visual score representation
- [ ] Create `frontend/app/components/ApprovalPanel.tsx` with approve/reject buttons
- [ ] Create `frontend/app/components/PipelineBoard.tsx` with 4 columns (Applied, Screening, Shortlisted, Pending Approval)
- [ ] Create `frontend/app/components/DigestBanner.tsx` with today's stats
- [ ] Test all components render correctly

### TASK-028: Dashboard Page
**Dependencies**: TASK-027
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `frontend/app/page.tsx` as main dashboard
- [ ] Fetch `GET /candidates` and `GET /approvals/pending` every 30 seconds
- [ ] Display `DigestBanner` at top
- [ ] Display `PipelineBoard` with candidate cards
- [ ] Show pending approval count badge in nav
- [ ] Test real-time updates work

### TASK-029: Candidate Detail Page
**Dependencies**: TASK-027
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `frontend/app/candidates/[id]/page.tsx`
- [ ] Fetch `GET /candidates/{id}` and `GET /candidates/{id}/brief`
- [ ] Display candidate name, email, job role, status badge
- [ ] Display `ScoreBar` with total + breakdown
- [ ] Display strengths, weaknesses, red flags as labeled lists
- [ ] Display screening Q&A
- [ ] Display `ApprovalPanel` if status is pending_approval
- [ ] Implement approve action: `POST /approvals/{id}/approve`
- [ ] Implement reject action: `POST /approvals/{id}/reject` with reason input
- [ ] Test all interactions work

---

## Phase 11: Testing

### TASK-030: Test Infrastructure
**Dependencies**: TASK-002
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/tests/__init__.py`
- [ ] Create `backend/tests/conftest.py` with shared fixtures
- [ ] Implement `db_session` fixture with in-memory SQLite
- [ ] Implement `client` fixture with FastAPI test client
- [ ] Implement sample data fixtures (cv_text, rubric_path, score, questions)
- [ ] Test fixtures work correctly

### TASK-031: Screening Agent Tests
**Dependencies**: TASK-008, TASK-009, TASK-010, TASK-030
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_screening_agent.py`
- [ ] Test `score_candidate()` returns valid dict
- [ ] Test `score_candidate()` retries on invalid JSON
- [ ] Test `score_candidate()` raises after two failures
- [ ] Test `score_candidate()` handles disqualified candidates
- [ ] Test `generate_screening_questions()` returns exactly 5 questions
- [ ] Test `generate_screening_questions()` uses grok-3-mini
- [ ] Test `analyze_reply()` returns valid dict
- [ ] Test `analyze_reply()` applies score delta correctly
- [ ] All tests pass with >90% coverage

### TASK-032: PDF Service Tests
**Dependencies**: TASK-011, TASK-030
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_pdf_service.py`
- [ ] Test `extract_text_from_pdf()` returns string
- [ ] Test joins multiple pages
- [ ] Test handles scanned PDFs
- [ ] Test strips whitespace
- [ ] All tests pass with >95% coverage

### TASK-033: Gmail Service Tests
**Dependencies**: TASK-012, TASK-030
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_gmail_service.py`
- [ ] Test `send_email()` in DRY_RUN mode does not call API
- [ ] Test `send_email()` returns fake message ID in DRY_RUN
- [ ] Test `send_screening_questions()` formats correctly
- [ ] Test `send_interview_invite()` uses correct recipient
- [ ] Test `send_rejection_email()` uses correct recipient
- [ ] All tests pass with >85% coverage

### TASK-034: CRUD Tests
**Dependencies**: TASK-006, TASK-030
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_crud.py`
- [ ] Test `create_candidate()` inserts and returns candidate
- [ ] Test `get_candidate()` returns correct candidate
- [ ] Test `update_candidate_status()` updates status
- [ ] Test `update_candidate_score()` stores score breakdown
- [ ] Test `create_pending_approval()` and `get_pending_approvals()`
- [ ] Test `approve_candidate()` sets status and approver
- [ ] All tests pass with >95% coverage

### TASK-035: Orchestrator Tests
**Dependencies**: TASK-017, TASK-018, TASK-030
**Effort**: L
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_orchestrator.py`
- [ ] Test `process_new_candidate()` full flow for qualified candidate
- [ ] Test `process_new_candidate()` creates rejection approval for disqualified
- [ ] Test `process_candidate_reply()` analyzes reply and creates advance approval
- [ ] All tests pass with >85% coverage

### TASK-036: Router Tests
**Dependencies**: TASK-020, TASK-021, TASK-022, TASK-030
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_routers_candidates.py`
- [ ] Test `GET /health` returns 200
- [ ] Test `GET /candidates` returns empty list when no candidates
- [ ] Test `GET /candidates/{id}` returns 404 for non-existent
- [ ] Create `backend/tests/test_routers_approvals.py`
- [ ] Test `GET /approvals/pending` returns empty list
- [ ] Test `POST /approvals/{id}/approve` triggers interview invite
- [ ] All tests pass with >80% coverage

### TASK-037: Watcher Tests
**Dependencies**: TASK-015, TASK-016, TASK-030
**Effort**: M
**Acceptance Criteria**:
- [ ] Create `backend/tests/test_watchers.py`
- [ ] Test `GmailApplicationWatcher` skips processed IDs
- [ ] Test `GmailApplicationWatcher` skips emails without PDF
- [ ] Test `BaseWatcher.run()` continues on error
- [ ] All tests pass with >75% coverage

---

## Phase 12: Documentation & Deployment

### TASK-038: Sample Rubric
**Dependencies**: TASK-001
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/rubrics/Senior_Backend_Engineer.md`
- [ ] Include must-have requirements
- [ ] Include scoring weights table
- [ ] Include nice-to-have bonuses
- [ ] Include red flags with penalties
- [ ] Include screening questions template

### TASK-039: README Documentation
**Dependencies**: TASK-024, TASK-029
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `README.md` in project root
- [ ] Document project overview and features
- [ ] Document tech stack
- [ ] Document setup instructions (Docker, backend, frontend)
- [ ] Document environment variables
- [ ] Document how to run tests
- [ ] Document deployment instructions
- [ ] Include architecture diagram

### TASK-040: Environment Files
**Dependencies**: TASK-001
**Effort**: S
**Acceptance Criteria**:
- [ ] Create `backend/.env.example` with all required variables
- [ ] Create `frontend/.env.local.example` with NEXT_PUBLIC_API_URL
- [ ] Document each variable with comments
- [ ] Ensure no secrets in example files

### TASK-041: Integration Testing
**Dependencies**: TASK-024, TASK-029, TASK-031-037
**Effort**: L
**Acceptance Criteria**:
- [ ] Run `docker-compose up -d` successfully
- [ ] Run `uv run uvicorn main:app --reload` successfully
- [ ] Verify `/health` endpoint returns {"status": "ok"}
- [ ] Run `npm run dev` successfully
- [ ] Verify dashboard loads at http://localhost:3000
- [ ] Run `uv run pytest tests/ -v` - all tests pass
- [ ] Send test email with PDF CV to jobs inbox
- [ ] Verify candidate appears in dashboard within 2 minutes
- [ ] Verify screening questions sent (DRY_RUN mode)
- [ ] Manually create pending approval in DB
- [ ] Verify approval panel works in dashboard
- [ ] Verify all HITL boundaries enforced

### TASK-042: Deployment Preparation
**Dependencies**: TASK-041
**Effort**: M
**Acceptance Criteria**:
- [ ] Create Railway account and project
- [ ] Add PostgreSQL and Redis add-ons in Railway
- [ ] Configure environment variables in Railway
- [ ] Deploy backend to Railway
- [ ] Verify health check endpoint works
- [ ] Create Vercel account and project
- [ ] Configure NEXT_PUBLIC_API_URL to Railway backend URL
- [ ] Deploy frontend to Vercel
- [ ] Verify dashboard loads and connects to backend
- [ ] Test end-to-end flow in production

---

## Summary

**Total Tasks**: 42
**Estimated Total Effort**: ~200-250 hours

**Critical Path**:
1. Foundation (TASK-001 to TASK-003)
2. Database Layer (TASK-004 to TASK-006)
3. AI Agents (TASK-007 to TASK-010)
4. Services (TASK-011 to TASK-013)
5. Orchestrator (TASK-017 to TASK-019)
6. API (TASK-020 to TASK-022)
7. Main App (TASK-024)
8. Frontend (TASK-025 to TASK-029)
9. Testing (TASK-030 to TASK-037)
10. Deployment (TASK-041 to TASK-042)

**Parallel Work Opportunities**:
- Frontend (TASK-025 to TASK-029) can be developed in parallel with backend testing (TASK-030 to TASK-037)
- Documentation (TASK-038 to TASK-040) can be written throughout development

**Risk Mitigation**:
- Test early and often (unit tests alongside implementation)
- Use DRY_RUN mode throughout development
- Mock all external APIs in tests
- Verify HITL boundaries at every stage

---

**Next Steps**: Begin implementation with TASK-001 (Project Scaffolding)

# Candidate Screening Agent — Claude Code Project Spec

> **Instruction for Claude Code:** Read this entire document before writing any code.
> Build every file listed in the folder structure below. Use the exact filenames, imports,
> and logic described. Do not skip any file. After building, run the project to verify it works.

---

## Project Overview

Build a **Candidate Screening Digital FTE** — an autonomous AI agent that manages the full
early-stage hiring pipeline without human intervention, except for final approval decisions.

**What it does end-to-end:**
1. Watches a Gmail inbox for new job applications (CV attached as PDF)
2. Extracts text from the CV using `pdfplumber`
3. Scores the candidate against a Markdown rubric using **Grok via OpenAI Agents SDK**
4. Sends 5 personalized screening questions to the candidate via Gmail
5. Watches for the candidate's reply and analyzes it with Grok
6. Creates a pending approval record for the hiring manager
7. Hiring manager approves/rejects via a **Next.js dashboard**
8. On approval → sends interview invite; on rejection → sends empathetic rejection email
9. Logs every AI decision to an audit log in PostgreSQL
10. Sends a **Daily Talent Digest** email to the hiring manager every morning at 8am

**Core principle:** The agent never sends a final email to a candidate without human approval.
All sensitive actions go through HITL (Human-in-the-Loop).

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| AI Brain | Grok API (xAI) via OpenAI Agents SDK | `grok-3`, `grok-3-mini` |
| Agent Framework | `openai-agents` | latest |
| Backend | FastAPI + Uvicorn | Python 3.11+ |
| Job Queue | Redis + `redis.asyncio` | 7+ |
| Database | PostgreSQL via SQLAlchemy async | 15+ |
| CV Parsing | `pdfplumber` | latest |
| Gmail Integration | Google Gmail API v1 (OAuth2) | latest |
| Frontend | Next.js 14 App Router + Tailwind CSS | Node 20+ |
| Deployment | Railway (backend) + Vercel (frontend) | — |
| Process Manager | PM2 | latest |
| Environment | `python-dotenv` | latest |

---

## Environment Variables

Create `backend/.env` with ALL of the following. Claude Code must wire every one of these
into the relevant files using `os.getenv()` and `load_dotenv()`.

```env
# Grok / xAI
GROQ_API_KEY=xai-your-key-here

# Gmail OAuth2 (download from Google Cloud Console)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
JOBS_INBOX_EMAIL=jobs@yourdomain.com
HIRING_MANAGER_EMAIL=manager@yourdomain.com

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/screening_db

# Redis
REDIS_URL=redis://localhost:6379

# App
DEV_MODE=true
DRY_RUN=true
MAX_EMAILS_PER_HOUR=20
SECRET_KEY=your-secret-key-for-jwt
```

Create `frontend/.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Exact Folder Structure

Claude Code must create every file listed below. Do not deviate from this structure.

```
candidate-screening-agent/
│
├── backend/
│   ├── main.py
│   ├── orchestrator.py
│   ├── screening_agent.py
│   ├── daily_digest.py
│   ├── pyproject.toml
│   ├── .env.example
│   │
│   ├── watchers/
│   │   ├── __init__.py
│   │   ├── base_watcher.py
│   │   ├── gmail_watcher.py
│   │   └── reply_watcher.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── crud.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── candidates.py
│   │   ├── approvals.py
│   │   └── jobs.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gmail_service.py
│   │   ├── pdf_service.py
│   │   └── audit_service.py
│   │
│   └── rubrics/
│       └── Senior_Backend_Engineer.md
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── .env.local.example
│   │
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── globals.css
│       │
│       ├── candidates/
│       │   └── [id]/
│       │       └── page.tsx
│       │
│       └── components/
│           ├── CandidateCard.tsx
│           ├── ScoreBar.tsx
│           ├── ApprovalPanel.tsx
│           ├── PipelineBoard.tsx
│           └── DigestBanner.tsx
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## File-by-File Specifications

Claude Code must implement each file exactly as described below.

---

### `backend/pyproject.toml`

```toml
[project]
name = "candidate-screening-agent"
version = "0.1.0"
description = "Autonomous candidate screening Digital FTE powered by Grok + OpenAI Agents SDK"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.115.0",
    "uvicorn[standard]==0.30.0",
    "openai-agents",
    "openai>=1.0.0",
    "sqlalchemy[asyncio]==2.0.36",
    "asyncpg==0.29.0",
    "alembic==1.13.0",
    "redis[asyncio]==5.0.0",
    "pdfplumber==0.11.0",
    "python-dotenv==1.0.0",
    "google-auth==2.35.0",
    "google-auth-oauthlib==1.2.0",
    "google-api-python-client==2.149.0",
    "apscheduler==3.10.4",
    "python-multipart==0.0.12",
    "pydantic==2.9.0",
    "pydantic-settings==2.5.0",
    "httpx==0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "aiosqlite>=0.20.0",
    "pytest-mock>=3.14.0",
]
```

> **To add a new dependency:** `uv add <package-name>`
> **To remove:** `uv remove <package-name>`
> **To sync after cloning:** `uv sync`

---

### `backend/db/models.py`

Create SQLAlchemy async models for these tables:

**`jobs` table** — columns: `id`, `title`, `slug`, `rubric_path`, `status` (open/closed), `created_at`

**`candidates` table** — columns: `id`, `job_id` (FK→jobs), `email`, `name`,
`cv_text` (Text), `status` (queued / scoring / scored / questions_sent / awaiting_reply /
replied / shortlisted / rejected / hired), `total_score` (Float nullable),
`must_haves_met` (Boolean nullable), `score_breakdown` (JSON nullable),
`strengths` (JSON nullable), `weaknesses` (JSON nullable), `red_flags` (JSON nullable),
`recommendation` (String nullable), `confidence` (String nullable),
`score_summary` (Text nullable), `screening_questions` (JSON nullable),
`candidate_reply` (Text nullable), `reply_analysis` (JSON nullable),
`gmail_message_id` (String nullable), `created_at`, `updated_at`

**`pending_approvals` table** — columns: `id`, `candidate_id` (FK→candidates),
`job_id` (FK→jobs), `action` (advance/reject), `score` (Float),
`recommendation` (Text), `brief_summary` (Text), `status` (pending/approved/rejected),
`approved_by` (String nullable), `created_at`, `expires_at`

**`audit_log` table** — columns: `id`, `candidate_id` (FK→candidates nullable),
`action_type` (String), `actor` (String), `input_summary` (Text nullable),
`output_summary` (Text nullable), `approval_status` (String nullable),
`approved_by` (String nullable), `result` (String), `created_at`

---

### `backend/db/database.py`

Create async SQLAlchemy engine and session factory using `DATABASE_URL` from env.
Export `AsyncSession`, `get_db` dependency for FastAPI, and `init_db()` that creates
all tables on startup.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

### `backend/db/crud.py`

Implement these async functions (all take `db: AsyncSession` as first arg):

- `create_candidate(db, job_id, email, name, cv_text, gmail_message_id) -> Candidate`
- `get_candidate(db, candidate_id) -> Candidate`
- `update_candidate_status(db, candidate_id, status) -> Candidate`
- `update_candidate_score(db, candidate_id, score_data: dict) -> Candidate`
- `update_candidate_questions(db, candidate_id, questions: list) -> Candidate`
- `update_candidate_reply(db, candidate_id, reply_text, analysis: dict) -> Candidate`
- `create_pending_approval(db, candidate_id, job_id, action, score, recommendation, brief_summary) -> PendingApproval`
- `get_pending_approvals(db) -> list[PendingApproval]`
- `approve_candidate(db, approval_id, approved_by) -> PendingApproval`
- `reject_candidate(db, approval_id, approved_by) -> PendingApproval`
- `get_candidates_by_status(db, status) -> list[Candidate]`
- `get_all_candidates(db) -> list[Candidate]`
- `create_audit_log(db, action_type, actor, result, candidate_id=None, input_summary=None, output_summary=None, approval_status=None, approved_by=None)`

---

### `backend/screening_agent.py`

This is the core AI file. Use **OpenAI Agents SDK with Grok**.

```python
import asyncio, json, os
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
set_tracing_disabled(disabled=True)  # Required — no OpenAI key for tracing

def get_grok_model(model_name: str = "grok-3"):
    """Grok is OpenAI-API-compatible. Only base_url and api_key differ from OpenAI."""
    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )
```

Implement these three async functions:

**`score_candidate(cv_text: str, rubric_path: str) -> dict`**
- Agent named "CV Scorer", `model=get_grok_model("grok-3")`
- Instructions: score objectively based only on the rubric, return valid JSON only, no prose
- Returns JSON: `total_score`, `must_haves_met`, `disqualification_reason`, `skill_score`,
  `experience_score`, `project_score`, `communication_score`, `bonuses_applied`,
  `red_flags`, `strengths`, `weaknesses`, `recommendation`, `confidence`, `summary`
- Use `Runner.run()` → `json.loads(result.final_output)`
- On JSON parse fail → retry once with stricter prompt

**`generate_screening_questions(cv_text: str, rubric_path: str) -> list[str]`**
- Agent named "Question Generator", `model=get_grok_model("grok-3-mini")`
- Returns JSON array of exactly 5 personalized questions referencing the candidate's CV
- Use `Runner.run()` → `json.loads(result.final_output)`

**`analyze_reply(questions: list[str], reply_text: str, original_score: dict) -> dict`**
- Agent named "Reply Analyzer", `model=get_grok_model("grok-3")`
- Returns JSON: `reply_score_delta` (int -20 to +20), `final_score` (int),
  `answer_quality` (high/medium/low), `notable_answers` (list[str]),
  `updated_recommendation` (advance/reject/review), `brief_summary` (str)

---

### `backend/services/pdf_service.py`

`extract_text_from_pdf(pdf_bytes: bytes) -> str`:
- Use `pdfplumber` to extract text from all pages
- If text is empty (scanned PDF) → return `"Scanned PDF — manual review required"`
- Strip excess whitespace, return clean joined text

---

### `backend/services/gmail_service.py`

`GmailService` class using Google Gmail API v1 with OAuth2.
Load from env: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`.

Methods:
- `send_email(to, subject, body) -> str` — returns message ID. If `DRY_RUN=true` → log and return fake ID
- `send_screening_questions(to, candidate_name, job_title, questions) -> str`
- `send_interview_invite(to, candidate_name, job_title) -> str`
- `send_rejection_email(to, candidate_name, job_title, reason) -> str` — use Grok agent to write empathetic copy
- `send_daily_digest(to, digest_data: dict) -> str`

---

### `backend/services/audit_service.py`

`log_action(db, action_type, actor, result, **kwargs)` — thin wrapper around
`crud.create_audit_log` that catches and silently logs any DB errors so audit failures
never crash the main pipeline.

---

### `backend/watchers/base_watcher.py`

```python
from abc import ABC, abstractmethod
import asyncio, logging

class BaseWatcher(ABC):
    def __init__(self, check_interval: int = 120):
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def check_for_updates(self) -> list:
        pass

    @abstractmethod
    async def handle_item(self, item) -> None:
        pass

    async def run(self):
        self.logger.info(f"Starting {self.__class__.__name__}")
        while True:
            try:
                items = await self.check_for_updates()
                for item in items:
                    await self.handle_item(item)
            except Exception as e:
                self.logger.error(f"Watcher error: {e}")
            await asyncio.sleep(self.check_interval)
```

---

### `backend/watchers/gmail_watcher.py`

`GmailApplicationWatcher(BaseWatcher)`:
- `check_interval = 120` seconds
- Polls Gmail for unread emails with label `jobs`
- Tracks processed IDs in `processed_ids.json`
- For each new email: extract sender, download PDF attachment,
  call `pdf_service.extract_text_from_pdf()`, insert to DB via `crud.create_candidate()`,
  push `candidate_id` to Redis `screening_queue`
- If no PDF → skip and log warning

---

### `backend/watchers/reply_watcher.py`

`ReplyWatcher(BaseWatcher)`:
- `check_interval = 60` seconds
- Polls Gmail for replies to screening question threads
- Matches by `In-Reply-To` / `References` headers against stored `gmail_message_id`
  from candidates with status `awaiting_reply`
- Pushes `(candidate_id, reply_text)` to Redis `reply_queue`

---

### `backend/orchestrator.py`

```python
async def process_new_candidate(candidate_id: int, db: AsyncSession):
    # 1. Fetch candidate
    # 2. score_candidate() with Grok
    # 3. Update DB score
    # 4. If not must_haves_met → create_pending_approval(action="reject") → return
    # 5. generate_screening_questions() with Grok
    # 6. send_screening_questions() via gmail_service
    # 7. Update status to "awaiting_reply"
    # 8. log to audit_log

async def process_candidate_reply(candidate_id: int, reply_text: str, db: AsyncSession):
    # 1. Fetch candidate + original score
    # 2. analyze_reply() with Grok
    # 3. Update candidate reply + final score
    # 4. create_pending_approval(action="advance")
    # 5. log to audit_log

async def run_orchestrator():
    # Use asyncio.gather() to consume screening_queue and reply_queue concurrently
    # Use brpop(timeout=1) for non-blocking loop
```

---

### `backend/daily_digest.py`

`send_daily_digest(db)`:
- Fetch all candidates from past 24 hours
- Group by status
- Use Grok `grok-3-mini` agent to write 3-sentence executive summary
- Call `gmail_service.send_daily_digest()` to HIRING_MANAGER_EMAIL
- Schedule with APScheduler at 8:00 AM daily

---

### `backend/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(run_orchestrator())
    asyncio.create_task(GmailApplicationWatcher().run())
    asyncio.create_task(ReplyWatcher().run())
    setup_scheduler()
    yield

app = FastAPI(title="Candidate Screening Agent", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

### `backend/routers/candidates.py`

- `GET /candidates` — all candidates with score and status
- `GET /candidates/{id}` — full candidate detail
- `GET /candidates/by-status/{status}` — filter by pipeline status
- `GET /candidates/{id}/brief` — one-page brief (score, strengths, weaknesses, Q&A summary)

---

### `backend/routers/approvals.py`

- `GET /approvals/pending` — all pending approvals
- `POST /approvals/{id}/approve` — body: `{ "approved_by": "email" }` → triggers interview invite
- `POST /approvals/{id}/reject` — body: `{ "approved_by": "email", "reason": "..." }` → triggers rejection email

---

### `backend/routers/jobs.py`

- `GET /jobs` — list all jobs
- `POST /jobs` — create job with title, slug, rubric_path
- `GET /jobs/{id}` — job detail with candidate count by status

---

### `backend/rubrics/Senior_Backend_Engineer.md`

```markdown
---
job_id: 1
role: Senior Backend Engineer
updated: 2026-01-15
---

## Must-Have (Automatic Disqualification if Missing)
- 3+ years Python or Go experience
- REST API design and implementation
- At least one cloud platform (AWS / GCP / Azure)

## Scoring Weights
| Category               | Weight |
|------------------------|--------|
| Technical skill match  |   40%  |
| Relevant experience    |   25%  |
| Project quality        |   20%  |
| Communication clarity  |   15%  |

## Nice-to-Have (Bonus Points)
- FastAPI or Gin framework: +5 pts
- PostgreSQL specifically: +3 pts
- Open source contributions: +5 pts
- Kubernetes / container orchestration: +4 pts
- System design experience: +3 pts

## Red Flags (Score Penalty)
- Job-hopping (< 1 year at 3+ companies): -15 pts
- No mention of testing or CI/CD: -10 pts
- Resume > 3 pages with no substance: -5 pts
- Only tutorial/bootcamp projects: -10 pts

## Screening Questions Template
1. Describe your most complex API design decision and trade-offs made.
2. How have you handled database performance issues at scale?
3. Walk me through how you would design a job queue system.
4. What is your approach to testing in a fast-moving team?
5. Why are you interested in this role specifically?
```

---

### `frontend/app/page.tsx`

Main dashboard:
- Fetch `GET /candidates` and `GET /approvals/pending` every 30 seconds
- Show `DigestBanner` at top with today's stats
- Show `PipelineBoard` with 4 columns: Applied | Screening | Shortlisted | Pending Approval
- Each candidate as a `CandidateCard`
- Pending approval count badge in nav

---

### `frontend/app/candidates/[id]/page.tsx`

Candidate detail page:
- Fetch `GET /candidates/{id}` and `GET /candidates/{id}/brief`
- Show: name, email, job role, status badge
- Show `ScoreBar` with total + breakdown
- Show strengths, weaknesses, red flags as labeled lists
- Show screening Q&A
- Show `ApprovalPanel` if status is `pending_approval`
- Approve → `POST /approvals/{id}/approve`
- Reject → reason input → `POST /approvals/{id}/reject`

---

### `frontend/app/components/CandidateCard.tsx`

Shows: name, score badge (green ≥80, amber 60–79, red <60), status pill,
recommendation, created time. Clicking navigates to `/candidates/{id}`.

---

### `frontend/app/components/ScoreBar.tsx`

Total score as filled bar (0–100). Four sub-bars below for skill/experience/project/communication.

---

### `frontend/app/components/ApprovalPanel.tsx`

- AI recommendation + confidence
- Brief summary
- Green "Approve — Send Interview Invite" button
- Red "Reject" button → expands reason input → confirm
- Both call API endpoints, show success/error state

---

### `frontend/app/components/PipelineBoard.tsx`

Kanban board: 4 columns (Applied, Screening, Shortlisted, Pending Approval).
Each column: candidate count + scrollable `CandidateCard` list.

---

### `frontend/app/components/DigestBanner.tsx`

Top banner: total new applications, pending approvals (urgent badge if >0),
shortlisted today, "View Digest" button.

---

### `docker-compose.yml`

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: screening_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

### `.gitignore`

```
__pycache__/
*.pyc
.env
.env.local
*.egg-info/
.venv/
venv/
node_modules/
.next/
.DS_Store
processed_ids.json
*.log
```

---

## Data Flow Diagram

```
Gmail Inbox (new application email + PDF)
        │
        ▼
GmailApplicationWatcher  (polls every 2 min)
        │  extract PDF → pdfplumber → insert DB → push Redis
        ▼
Redis: screening_queue
        │
        ▼
Orchestrator: process_new_candidate()
        │
        ├─► Grok grok-3:     score_candidate()       → update DB
        ├─► if disqualified: create_pending_approval(reject) → HITL
        ├─► Grok grok-3-mini: generate_questions()
        └─► Gmail:           send screening questions
                    │
                    ▼
          Candidate replies to email
                    │
                    ▼
          ReplyWatcher  (polls every 1 min)
                    │  push Redis
                    ▼
          Redis: reply_queue
                    │
                    ▼
          Orchestrator: process_candidate_reply()
                    │
                    ├─► Grok grok-3: analyze_reply()
                    └─► create_pending_approval(advance) → HITL
                                │
                                ▼
                      Next.js Dashboard
                      Hiring Manager: Approve / Reject
                                │
                    ┌───────────┴────────────┐
                    ▼                        ▼
             Gmail: interview          Gmail: rejection
             invite sent               email sent
                    │                        │
                    └───────────┬────────────┘
                                ▼
                         audit_log (PostgreSQL)

  Daily at 8am:
  APScheduler → send_daily_digest() → Grok summary → Gmail to manager
```

---

## Grok + OpenAI Agents SDK — Rules for Claude Code

Apply these rules everywhere in the codebase:

1. **Always `OpenAIChatCompletionsModel`** — never `OpenAIResponsesModel`. Grok does not support the Responses API.

2. **Always `set_tracing_disabled(True)`** at the top of `screening_agent.py` and `main.py`.

3. **Model selection:**
   - `grok-3` → CV scoring, reply analysis (deep reasoning)
   - `grok-3-mini` → question generation, digest summary, triage (fast + cheap)

4. **Always `Runner.run(agent, prompt)`** — not `Runner.run_sync()` in async context.

5. **Always wrap `json.loads(result.final_output)` in try/except.** On fail → retry once with `"Return ONLY valid JSON. No markdown, no prose."` If still fails → raise and log.

6. **`DRY_RUN=true` by default** — in `gmail_service.py`, check env before every real send. In DRY_RUN, print to console and return fake ID.

```python
# The one pattern used everywhere:
def get_grok_model(model_name: str = "grok-3"):
    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )
```

---

## Error Handling Rules

| Error Type | Strategy |
|---|---|
| Gmail API timeout | Exponential backoff: 2s → 4s → 8s, max 3 retries |
| Grok API error | Retry once → mark candidate `manual_review` → log |
| JSON parse error | Retry with stricter prompt once → raise |
| PDF extraction empty | Flag `scanned_pdf=true` → notify manager |
| Redis unavailable | Fall back to in-memory list → log warning |
| DB unavailable | Raise loudly — never silently lose data |

```python
# Retry decorator — use in watchers and services:
def with_retry(max_attempts=3, base_delay=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(base_delay * (2 ** attempt))
        return wrapper
    return decorator
```

---

## HITL Permission Boundaries

| Action | Autonomous | Requires Human |
|---|---|---|
| Parse CV | ✅ | — |
| Score candidate | ✅ | — |
| Generate questions | ✅ | — |
| Send screening email | ✅ (template only) | — |
| Advance to interview | ❌ | Manager clicks Approve |
| Send interview invite | ❌ | After approval POST |
| Reject candidate | ❌ | Manager clicks Reject |
| Send rejection email | ❌ | After rejection POST |
| Delete candidate data | ❌ | Never automated |

---

## Database Schema Reference

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY, title VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, rubric_path VARCHAR(300) NOT NULL,
    status VARCHAR(20) DEFAULT 'open', created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY, job_id INTEGER REFERENCES jobs(id),
    email VARCHAR(200) NOT NULL, name VARCHAR(200), cv_text TEXT,
    status VARCHAR(50) DEFAULT 'queued', total_score FLOAT,
    must_haves_met BOOLEAN, score_breakdown JSONB, strengths JSONB,
    weaknesses JSONB, red_flags JSONB, recommendation VARCHAR(20),
    confidence VARCHAR(20), score_summary TEXT, screening_questions JSONB,
    candidate_reply TEXT, reply_analysis JSONB, gmail_message_id VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pending_approvals (
    id SERIAL PRIMARY KEY, candidate_id INTEGER REFERENCES candidates(id),
    job_id INTEGER REFERENCES jobs(id), action VARCHAR(20) NOT NULL,
    score FLOAT, recommendation TEXT, brief_summary TEXT,
    status VARCHAR(20) DEFAULT 'pending', approved_by VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '48 hours')
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY, candidate_id INTEGER REFERENCES candidates(id),
    action_type VARCHAR(50) NOT NULL, actor VARCHAR(100) NOT NULL,
    input_summary TEXT, output_summary TEXT, approval_status VARCHAR(20),
    approved_by VARCHAR(200), result VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_job_id ON candidates(job_id);
CREATE INDEX idx_approvals_status ON pending_approvals(status);
CREATE INDEX idx_audit_candidate ON audit_log(candidate_id);
```

---

## How to Run After Building

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Backend
cd backend
uv sync
cp .env.example .env        # fill in your API keys
uv run uvicorn main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                 # http://localhost:3000

# 4. Test
# Send an email with a PDF CV to JOBS_INBOX_EMAIL
# Watch terminal logs
# Open http://localhost:3000 — candidate should appear in dashboard
# Open http://localhost:8000/docs — FastAPI Swagger UI
```


---

## Test Cases

Claude Code must create a `backend/tests/` folder and implement all test cases below.
Use `pytest` with `pytest-asyncio` for async tests. Add these to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "pytest-mock>=3.14.0",
]
```

Install dev dependencies with:
```bash
uv add --dev pytest pytest-asyncio httpx pytest-mock
```

Run all tests with:
```bash
uv run pytest tests/ -v
```

---

### Folder Structure for Tests

```
backend/tests/
├── __init__.py
├── conftest.py
├── test_screening_agent.py
├── test_pdf_service.py
├── test_gmail_service.py
├── test_orchestrator.py
├── test_routers_candidates.py
├── test_routers_approvals.py
├── test_watchers.py
└── test_crud.py
```

---

### `backend/tests/conftest.py`

Create shared fixtures used across all test files:

```python
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.models import Base
from db.database import get_db
from main import app

# Use in-memory SQLite for tests — no real Postgres needed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def client(db_session):
    """FastAPI test client with DB override."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def sample_cv_text():
    return """
    John Doe | john.doe@gmail.com
    Senior Backend Engineer

    Experience:
    - 5 years Python (FastAPI, Django)
    - Built REST APIs serving 10M requests/day
    - AWS Certified Solutions Architect
    - PostgreSQL, Redis, Docker, Kubernetes
    - CI/CD with GitHub Actions

    Projects:
    - Payment processing system (Python, FastAPI, Stripe)
    - Real-time analytics pipeline (Kafka, PostgreSQL)

    Education: BS Computer Science
    """

@pytest.fixture
def sample_rubric_path(tmp_path):
    rubric = tmp_path / "test_rubric.md"
    rubric.write_text("""
---
job_id: 1
role: Senior Backend Engineer
---

## Must-Have
- 3+ years Python or Go experience
- REST API design
- At least one cloud platform

## Scoring Weights
| Category              | Weight |
|-----------------------|--------|
| Technical skill match |   40%  |
| Relevant experience   |   25%  |
| Project quality       |   20%  |
| Communication clarity |   15%  |

## Nice-to-Have
- FastAPI: +5 pts
- PostgreSQL: +3 pts
- Kubernetes: +4 pts

## Red Flags
- Job-hopping: -15 pts
- No testing mention: -10 pts
    """)
    return str(rubric)

@pytest.fixture
def sample_score():
    return {
        "total_score": 82,
        "must_haves_met": True,
        "disqualification_reason": None,
        "skill_score": 35,
        "experience_score": 22,
        "project_score": 16,
        "communication_score": 9,
        "bonuses_applied": ["FastAPI (+5)", "PostgreSQL (+3)", "Kubernetes (+4)"],
        "red_flags": [],
        "strengths": ["Strong Python", "Cloud certified", "Real-world projects"],
        "weaknesses": ["No open source contributions"],
        "recommendation": "advance",
        "confidence": "high",
        "summary": "Strong backend engineer with 5 years Python experience. Exceeds most requirements."
    }

@pytest.fixture
def sample_questions():
    return [
        "Your CV mentions a payment system — what was the biggest scaling challenge?",
        "How did you handle database performance at 10M requests/day?",
        "Walk me through your CI/CD setup with GitHub Actions.",
        "How do you approach testing in a fast-moving team?",
        "Why are you interested in this specific role?"
    ]

@pytest.fixture
def disqualified_score():
    return {
        "total_score": 20,
        "must_haves_met": False,
        "disqualification_reason": "No Python or Go experience found in CV",
        "skill_score": 5,
        "experience_score": 5,
        "project_score": 5,
        "communication_score": 5,
        "bonuses_applied": [],
        "red_flags": ["No cloud experience", "No API design experience"],
        "strengths": [],
        "weaknesses": ["Missing all must-have requirements"],
        "recommendation": "reject",
        "confidence": "high",
        "summary": "Candidate does not meet the minimum requirements for this role."
    }
```

---

### `backend/tests/test_screening_agent.py`

Test the 3 Grok agents with mocked `Runner.run()` — never call real Grok API in tests.

```python
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from screening_agent import score_candidate, generate_screening_questions, analyze_reply

class MockRunResult:
    def __init__(self, output: str):
        self.final_output = output

# ── score_candidate ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_score_candidate_returns_valid_dict(sample_cv_text, sample_rubric_path, sample_score):
    """score_candidate() returns a parsed dict when Grok returns valid JSON."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(sample_score))
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert isinstance(result, dict)
    assert result["total_score"] == 82
    assert result["must_haves_met"] is True
    assert result["recommendation"] == "advance"
    assert "strengths" in result
    assert "red_flags" in result

@pytest.mark.asyncio
async def test_score_candidate_retries_on_invalid_json(sample_cv_text, sample_rubric_path, sample_score):
    """score_candidate() retries once when Grok returns invalid JSON, succeeds on retry."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            MockRunResult("```json\nNot valid JSON```"),  # first call fails
            MockRunResult(json.dumps(sample_score)),       # retry succeeds
        ]
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert mock_run.call_count == 2
    assert result["total_score"] == 82

@pytest.mark.asyncio
async def test_score_candidate_raises_after_two_failures(sample_cv_text, sample_rubric_path):
    """score_candidate() raises after two consecutive JSON parse failures."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult("This is not JSON at all")
        with pytest.raises(Exception):
            await score_candidate(sample_cv_text, sample_rubric_path)

@pytest.mark.asyncio
async def test_score_candidate_disqualified(sample_cv_text, sample_rubric_path, disqualified_score):
    """score_candidate() correctly returns must_haves_met=False for weak candidates."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(disqualified_score))
        result = await score_candidate(sample_cv_text, sample_rubric_path)

    assert result["must_haves_met"] is False
    assert result["recommendation"] == "reject"
    assert result["disqualification_reason"] is not None

# ── generate_screening_questions ───────────────────────────────────

@pytest.mark.asyncio
async def test_generate_questions_returns_five(sample_cv_text, sample_rubric_path, sample_questions):
    """generate_screening_questions() always returns exactly 5 questions."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(sample_questions))
        result = await generate_screening_questions(sample_cv_text, sample_rubric_path)

    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(q, str) for q in result)

@pytest.mark.asyncio
async def test_generate_questions_uses_mini_model(sample_cv_text, sample_rubric_path, sample_questions):
    """generate_screening_questions() uses grok-3-mini not grok-3."""
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        with patch("screening_agent.get_grok_model") as mock_model:
            mock_run.return_value = MockRunResult(json.dumps(sample_questions))
            await generate_screening_questions(sample_cv_text, sample_rubric_path)
            mock_model.assert_called_with("grok-3-mini")

# ── analyze_reply ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_reply_returns_valid_dict(sample_questions, sample_score):
    """analyze_reply() returns parsed dict with expected keys."""
    reply_text = "Great questions! Here are my answers: ..."
    mock_analysis = {
        "reply_score_delta": 6,
        "final_score": 88,
        "answer_quality": "high",
        "notable_answers": ["Excellent answer on Q1 about scaling"],
        "updated_recommendation": "advance",
        "brief_summary": "Candidate answered all questions with depth and clarity."
    }
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(mock_analysis))
        result = await analyze_reply(sample_questions, reply_text, sample_score)

    assert result["final_score"] == 88
    assert result["answer_quality"] == "high"
    assert result["updated_recommendation"] == "advance"
    assert "brief_summary" in result

@pytest.mark.asyncio
async def test_analyze_reply_score_delta_applied(sample_questions, sample_score):
    """final_score = original_score + reply_score_delta."""
    mock_analysis = {
        "reply_score_delta": -5,
        "final_score": 77,
        "answer_quality": "medium",
        "notable_answers": [],
        "updated_recommendation": "review",
        "brief_summary": "Answers were vague and lacked depth."
    }
    with patch("screening_agent.Runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MockRunResult(json.dumps(mock_analysis))
        result = await analyze_reply(sample_questions, "Short vague answers", sample_score)

    assert result["reply_score_delta"] == -5
    assert result["updated_recommendation"] == "review"
```

---

### `backend/tests/test_pdf_service.py`

```python
import pytest
import io
from unittest.mock import patch, MagicMock
from services.pdf_service import extract_text_from_pdf

def make_fake_pdf_bytes(text: str) -> bytes:
    """Helper — returns minimal fake PDF bytes for mocking."""
    return b"%PDF-1.4 fake content"

def test_extract_text_returns_string():
    """extract_text_from_pdf() always returns a string."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "John Doe\n5 years Python experience"

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert isinstance(result, str)
    assert "John Doe" in result

def test_extract_text_joins_multiple_pages():
    """extract_text_from_pdf() joins text from all pages."""
    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1 content"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2 content"

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [page1, page2]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert "Page 1 content" in result
    assert "Page 2 content" in result

def test_extract_text_handles_scanned_pdf():
    """extract_text_from_pdf() returns fallback message for scanned/empty PDFs."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None  # scanned PDF returns None

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake scanned pdf")

    assert "manual review required" in result.lower()

def test_extract_text_strips_whitespace():
    """extract_text_from_pdf() strips excess whitespace from output."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "  John Doe  \n\n\n  Python  "

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert not result.startswith("  ")
    assert "\n\n\n" not in result
```

---

### `backend/tests/test_gmail_service.py`

```python
import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from services.gmail_service import GmailService

@pytest.fixture
def gmail(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "fake-secret")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "fake-token")
    monkeypatch.setenv("DRY_RUN", "true")
    with patch("services.gmail_service.build"):
        return GmailService()

def test_send_email_dry_run_does_not_call_api(gmail):
    """In DRY_RUN mode, send_email() never calls the Gmail API."""
    with patch.object(gmail, "_send_real_email") as mock_send:
        result = gmail.send_email("test@test.com", "Subject", "Body")
    mock_send.assert_not_called()
    assert isinstance(result, str)  # returns fake message ID

def test_send_email_dry_run_returns_fake_id(gmail):
    """In DRY_RUN mode, send_email() returns a non-empty fake message ID."""
    result = gmail.send_email("test@test.com", "Subject", "Body")
    assert result is not None
    assert len(result) > 0

def test_send_screening_questions_formats_correctly(gmail):
    """send_screening_questions() includes all 5 questions in the email body."""
    questions = [f"Question {i}" for i in range(1, 6)]
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_screening_questions(
            to="candidate@test.com",
            candidate_name="John",
            job_title="Backend Engineer",
            questions=questions
        )
    call_args = mock_send.call_args
    body = call_args[0][2] if call_args[0] else call_args[1]["body"]
    for q in questions:
        assert q in body

def test_send_interview_invite_uses_correct_recipient(gmail):
    """send_interview_invite() sends to the correct email address."""
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_interview_invite("john@test.com", "John Doe", "Backend Engineer")
    assert mock_send.call_args[0][0] == "john@test.com"

def test_send_rejection_email_uses_correct_recipient(gmail):
    """send_rejection_email() sends to the correct candidate email."""
    with patch.object(gmail, "send_email", return_value="fake-id") as mock_send:
        gmail.send_rejection_email("john@test.com", "John", "Backend Engineer", "Missing Python experience")
    assert mock_send.call_args[0][0] == "john@test.com"

def test_real_send_blocked_in_dry_run(gmail, monkeypatch):
    """Verify the Gmail API send() method is never called in DRY_RUN mode."""
    monkeypatch.setenv("DRY_RUN", "true")
    mock_service = MagicMock()
    gmail.service = mock_service
    gmail.send_email("to@test.com", "Subject", "Body")
    mock_service.users().messages().send.assert_not_called()
```

---

### `backend/tests/test_crud.py`

```python
import pytest
from db import crud
from db.models import Candidate, Job, PendingApproval

@pytest.mark.asyncio
async def test_create_candidate(db_session):
    """create_candidate() inserts a candidate and returns it with an ID."""
    job = Job(title="Backend Engineer", slug="backend-eng",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id,
        email="john@test.com", name="John Doe",
        cv_text="5 years Python", gmail_message_id="msg_123"
    )
    assert candidate.id is not None
    assert candidate.email == "john@test.com"
    assert candidate.status == "queued"

@pytest.mark.asyncio
async def test_get_candidate(db_session):
    """get_candidate() returns the correct candidate by ID."""
    job = Job(title="Backend Engineer", slug="backend-eng-2",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    created = await crud.create_candidate(
        db_session, job_id=job.id, email="jane@test.com",
        name="Jane Doe", cv_text="3 years Go", gmail_message_id="msg_456"
    )
    fetched = await crud.get_candidate(db_session, created.id)
    assert fetched.email == "jane@test.com"
    assert fetched.id == created.id

@pytest.mark.asyncio
async def test_update_candidate_status(db_session):
    """update_candidate_status() correctly updates the status field."""
    job = Job(title="Frontend Dev", slug="frontend-dev",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="bob@test.com",
        name="Bob", cv_text="React dev", gmail_message_id="msg_789"
    )
    updated = await crud.update_candidate_status(db_session, candidate.id, "scored")
    assert updated.status == "scored"

@pytest.mark.asyncio
async def test_update_candidate_score(db_session, sample_score):
    """update_candidate_score() stores score breakdown correctly."""
    job = Job(title="DevOps", slug="devops",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="alice@test.com",
        name="Alice", cv_text="AWS expert", gmail_message_id="msg_abc"
    )
    updated = await crud.update_candidate_score(db_session, candidate.id, sample_score)
    assert updated.total_score == 82
    assert updated.must_haves_met is True
    assert updated.recommendation == "advance"

@pytest.mark.asyncio
async def test_create_and_get_pending_approval(db_session):
    """create_pending_approval() and get_pending_approvals() work correctly."""
    job = Job(title="SRE", slug="sre",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="sre@test.com",
        name="SRE Candidate", cv_text="Kubernetes expert", gmail_message_id="msg_sre"
    )
    approval = await crud.create_pending_approval(
        db_session, candidate_id=candidate.id, job_id=job.id,
        action="advance", score=85.0,
        recommendation="Strong candidate", brief_summary="Excellent Kubernetes experience"
    )
    assert approval.id is not None
    assert approval.status == "pending"

    pending = await crud.get_pending_approvals(db_session)
    assert len(pending) >= 1
    assert any(p.id == approval.id for p in pending)

@pytest.mark.asyncio
async def test_approve_candidate(db_session):
    """approve_candidate() sets status to approved and records approver."""
    job = Job(title="ML Eng", slug="ml-eng",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="ml@test.com",
        name="ML Candidate", cv_text="PyTorch expert", gmail_message_id="msg_ml"
    )
    approval = await crud.create_pending_approval(
        db_session, candidate_id=candidate.id, job_id=job.id,
        action="advance", score=90.0,
        recommendation="Top candidate", brief_summary="Excellent ML background"
    )
    approved = await crud.approve_candidate(
        db_session, approval.id, "manager@company.com"
    )
    assert approved.status == "approved"
    assert approved.approved_by == "manager@company.com"
```

---

### `backend/tests/test_routers_candidates.py`

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /health returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_get_all_candidates_empty(client):
    """GET /candidates returns empty list when no candidates exist."""
    response = await client.get("/candidates")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_candidate_not_found(client):
    """GET /candidates/9999 returns 404 for non-existent candidate."""
    response = await client.get("/candidates/9999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_candidates_by_status(client, db_session):
    """GET /candidates/by-status/queued returns only queued candidates."""
    response = await client.get("/candidates/by-status/queued")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

### `backend/tests/test_routers_approvals.py`

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_get_pending_approvals_empty(client):
    """GET /approvals/pending returns empty list when none exist."""
    response = await client.get("/approvals/pending")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_approve_nonexistent_approval(client):
    """POST /approvals/9999/approve returns 404."""
    response = await client.post(
        "/approvals/9999/approve",
        json={"approved_by": "manager@company.com"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_reject_nonexistent_approval(client):
    """POST /approvals/9999/reject returns 404."""
    response = await client.post(
        "/approvals/9999/reject",
        json={"approved_by": "manager@company.com", "reason": "Not qualified"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_approve_triggers_interview_invite(client, db_session):
    """POST /approvals/{id}/approve calls gmail_service.send_interview_invite()."""
    from db import crud
    from db.models import Job

    job = Job(title="Test Role", slug="test-role",
              rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="test@test.com",
        name="Test Candidate", cv_text="Python dev", gmail_message_id="msg_test"
    )
    approval = await crud.create_pending_approval(
        db_session, candidate_id=candidate.id, job_id=job.id,
        action="advance", score=80.0,
        recommendation="Good fit", brief_summary="Strong candidate"
    )

    with patch("routers.approvals.gmail_service.send_interview_invite",
               new_callable=AsyncMock) as mock_invite:
        response = await client.post(
            f"/approvals/{approval.id}/approve",
            json={"approved_by": "manager@company.com"}
        )

    assert response.status_code == 200
    mock_invite.assert_called_once()
```

---

### `backend/tests/test_orchestrator.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from orchestrator import process_new_candidate, process_candidate_reply

@pytest.mark.asyncio
async def test_process_new_candidate_full_flow(db_session, sample_cv_text, sample_rubric_path, sample_score, sample_questions):
    """process_new_candidate() runs full pipeline for a qualified candidate."""
    from db import crud
    from db.models import Job

    job = Job(title="Backend Eng", slug="backend-eng-orch",
              rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="orch@test.com",
        name="Orch Test", cv_text=sample_cv_text, gmail_message_id="msg_orch"
    )

    with patch("orchestrator.score_candidate", new_callable=AsyncMock, return_value=sample_score),          patch("orchestrator.generate_screening_questions", new_callable=AsyncMock, return_value=sample_questions),          patch("orchestrator.gmail_service.send_screening_questions", new_callable=AsyncMock, return_value="msg_sent"),          patch("orchestrator.audit_service.log_action", new_callable=AsyncMock):
        await process_new_candidate(candidate.id, db_session)

    updated = await crud.get_candidate(db_session, candidate.id)
    assert updated.status == "awaiting_reply"
    assert updated.screening_questions is not None

@pytest.mark.asyncio
async def test_process_new_candidate_disqualified(db_session, sample_cv_text, sample_rubric_path, disqualified_score):
    """process_new_candidate() creates rejection approval for disqualified candidates."""
    from db import crud
    from db.models import Job

    job = Job(title="Backend Eng", slug="backend-eng-disq",
              rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="disq@test.com",
        name="Disq Candidate", cv_text="No experience", gmail_message_id="msg_disq"
    )

    with patch("orchestrator.score_candidate", new_callable=AsyncMock, return_value=disqualified_score),          patch("orchestrator.gmail_service.send_screening_questions", new_callable=AsyncMock) as mock_send,          patch("orchestrator.audit_service.log_action", new_callable=AsyncMock):
        await process_new_candidate(candidate.id, db_session)

    # Screening questions should NOT be sent to disqualified candidates
    mock_send.assert_not_called()

    # A rejection pending approval should exist
    pending = await crud.get_pending_approvals(db_session)
    rejection = [p for p in pending if p.candidate_id == candidate.id and p.action == "reject"]
    assert len(rejection) == 1

@pytest.mark.asyncio
async def test_process_candidate_reply(db_session, sample_cv_text, sample_rubric_path, sample_score, sample_questions):
    """process_candidate_reply() analyzes reply and creates advance approval."""
    from db import crud
    from db.models import Job

    job = Job(title="Backend Eng", slug="backend-eng-reply",
              rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session, job_id=job.id, email="reply@test.com",
        name="Reply Test", cv_text=sample_cv_text, gmail_message_id="msg_reply"
    )
    await crud.update_candidate_score(db_session, candidate.id, sample_score)
    await crud.update_candidate_questions(db_session, candidate.id, sample_questions)

    mock_analysis = {
        "reply_score_delta": 5,
        "final_score": 87,
        "answer_quality": "high",
        "notable_answers": ["Excellent answer on scaling"],
        "updated_recommendation": "advance",
        "brief_summary": "Strong candidate with excellent answers."
    }

    with patch("orchestrator.analyze_reply", new_callable=AsyncMock, return_value=mock_analysis),          patch("orchestrator.audit_service.log_action", new_callable=AsyncMock):
        await process_candidate_reply(candidate.id, "My detailed answers here...", db_session)

    pending = await crud.get_pending_approvals(db_session)
    advance = [p for p in pending if p.candidate_id == candidate.id and p.action == "advance"]
    assert len(advance) == 1
    assert advance[0].score == 87
```

---

### `backend/tests/test_watchers.py`

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from watchers.gmail_watcher import GmailApplicationWatcher
from watchers.reply_watcher import ReplyWatcher

@pytest.mark.asyncio
async def test_gmail_watcher_skips_processed_ids():
    """GmailApplicationWatcher skips emails already in processed_ids set."""
    with patch("watchers.gmail_watcher.build"),          patch("watchers.gmail_watcher.Credentials"):
        watcher = GmailApplicationWatcher.__new__(GmailApplicationWatcher)
        watcher.processed_ids = {"msg_already_done"}
        watcher.logger = MagicMock()

        mock_messages = [{"id": "msg_already_done"}, {"id": "msg_new"}]
        watcher.service = MagicMock()
        watcher.service.users().messages().list().execute.return_value = {
            "messages": mock_messages
        }

        result = await watcher.check_for_updates()
        # Only the new message should be returned
        assert all(m["id"] != "msg_already_done" for m in result)

@pytest.mark.asyncio
async def test_gmail_watcher_skips_no_pdf_attachment():
    """GmailApplicationWatcher skips emails without PDF attachments."""
    with patch("watchers.gmail_watcher.build"),          patch("watchers.gmail_watcher.Credentials"):
        watcher = GmailApplicationWatcher.__new__(GmailApplicationWatcher)
        watcher.processed_ids = set()
        watcher.logger = MagicMock()
        watcher.redis = AsyncMock()
        watcher.db = AsyncMock()

        # Message with no PDF attachment
        msg_no_pdf = {
            "id": "msg_no_pdf",
            "payload": {
                "headers": [
                    {"name": "From", "value": "applicant@test.com"},
                    {"name": "Subject", "value": "Application"}
                ],
                "parts": [
                    {"filename": "cover_letter.txt", "body": {"data": ""}}
                ]
            },
            "snippet": "Please find my application"
        }
        watcher.service = MagicMock()
        watcher.service.users().messages().get().execute.return_value = msg_no_pdf

        await watcher.handle_item({"id": "msg_no_pdf"})
        watcher.redis.lpush.assert_not_called()

@pytest.mark.asyncio
async def test_base_watcher_continues_on_error():
    """BaseWatcher.run() logs errors and continues the loop instead of crashing."""
    from watchers.base_watcher import BaseWatcher

    class TestWatcher(BaseWatcher):
        call_count = 0

        async def check_for_updates(self):
            self.call_count += 1
            if self.call_count == 1:
                raise ConnectionError("Simulated network error")
            return []

        async def handle_item(self, item):
            pass

    watcher = TestWatcher(check_interval=0)
    watcher.logger = MagicMock()

    # Run 2 iterations then stop
    import asyncio
    async def run_briefly():
        task = asyncio.create_task(watcher.run())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await run_briefly()
    watcher.logger.error.assert_called_once()
    assert watcher.call_count >= 2  # continued after error
```

---

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ -v --cov=. --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_screening_agent.py -v

# Run a specific test
uv run pytest tests/test_screening_agent.py::test_score_candidate_returns_valid_dict -v

# Run only fast tests (exclude slow integration tests)
uv run pytest tests/ -v -m "not slow"
```

### Test Coverage Targets

| Module | Min Coverage |
|---|---|
| `screening_agent.py` | 90% |
| `db/crud.py` | 95% |
| `services/pdf_service.py` | 95% |
| `services/gmail_service.py` | 85% |
| `orchestrator.py` | 85% |
| `routers/` | 80% |
| `watchers/` | 75% |

---

## Claude Code — Final Build Instructions

Read this spec fully, then execute in this order:

1. Run `uv init backend` inside `candidate-screening-agent/` to scaffold the backend uv project
2. Create folder structure exactly as defined
3. `backend/db/models.py` → `backend/db/database.py` → `backend/db/crud.py`
3. `backend/screening_agent.py` (all 3 agent functions)
4. `backend/services/` (pdf, gmail, audit)
5. `backend/watchers/` (base, gmail, reply)
6. `backend/orchestrator.py`
7. `backend/daily_digest.py`
8. `backend/main.py` + all routers
9. Complete Next.js frontend (all components + pages)
10. `docker-compose.yml`, `.gitignore`, `README.md`, `.env.example`
11. Run `docker-compose up -d`
12. Run `uv sync`
13. Run `uv run uvicorn main:app --reload` → verify `/health` returns `{"status": "ok"}`
14. Run `uv run pytest tests/ -v` → all tests must pass before considering the build complete
15. Report any issues and fix them

**Do not ask clarifying questions. Build everything. If something is ambiguous,
make a reasonable engineering decision, implement it, and note it in a comment.**

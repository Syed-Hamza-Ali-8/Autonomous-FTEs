# Candidate Screening Agent Constitution

## Core Principles

### I. Human-in-the-Loop (HITL) Boundaries (NON-NEGOTIABLE)

**The agent never sends final candidate decisions without explicit human approval.**

- ✅ **Autonomous Actions**: Parse CVs, score candidates, generate screening questions, send screening emails (template-based), analyze replies, create pending approvals
- ❌ **Requires Human Approval**: Send interview invites, send rejection emails, delete candidate data, advance candidates to interview stage
- All sensitive actions must go through the `pending_approvals` table
- Hiring manager must explicitly click "Approve" or "Reject" in the dashboard
- Audit log must record both the AI recommendation AND the human decision

**Rationale**: Hiring decisions have legal, ethical, and reputational consequences. AI provides recommendations; humans make final decisions.

### II. Async-First Architecture

**All I/O operations must be async/await. No blocking calls in the event loop.**

- FastAPI with async route handlers
- SQLAlchemy with `asyncpg` driver and `AsyncSession`
- Redis with `redis.asyncio`
- All watchers, orchestrators, and services use `async def`
- Use `asyncio.gather()` for concurrent operations
- Use `asyncio.create_task()` for background tasks in lifespan

**Rationale**: The agent handles multiple concurrent candidates, email polling, and AI API calls. Blocking I/O would create bottlenecks.

### III. AI-First with Grok (OpenAI Agents SDK)

**All AI reasoning uses Grok API via OpenAI-compatible interface.**

**Model Selection Rules:**
- `grok-3` → CV scoring, reply analysis (deep reasoning, high accuracy)
- `grok-3-mini` → question generation, digest summaries, triage (fast, cheap)

**Implementation Requirements:**
- Always use `OpenAIChatCompletionsModel` (NOT `OpenAIResponsesModel`)
- Always call `set_tracing_disabled(True)` at module top (no OpenAI key for tracing)
- Always use `Runner.run(agent, prompt)` (NOT `Runner.run_sync()` in async context)
- Always wrap `json.loads(result.final_output)` in try/except
- On JSON parse failure → retry once with stricter prompt → if still fails, raise and log

**Standard Pattern:**
```python
def get_grok_model(model_name: str = "grok-3"):
    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
```

### IV. Error Handling & Resilience

**Never lose data. Fail loudly on critical errors. Retry gracefully on transient errors.**

| Error Type | Strategy |
|---|---|
| Gmail API timeout | Exponential backoff: 2s → 4s → 8s, max 3 retries |
| Grok API error | Retry once → mark candidate `manual_review` → log |
| JSON parse error | Retry with stricter prompt once → raise |
| PDF extraction empty | Flag `scanned_pdf=true` → notify manager |
| Redis unavailable | Fall back to in-memory list → log warning |
| DB unavailable | **Raise loudly** — never silently lose data |

**Retry Decorator Pattern:**
```python
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

### V. DRY_RUN by Default (Safety-First)

**No real emails sent until explicitly enabled in production.**

- `DRY_RUN=true` in `.env` by default
- In DRY_RUN mode: log email content to console, return fake message ID
- In `gmail_service.py`, check `os.getenv("DRY_RUN")` before every real send
- Never skip this check — accidental emails to candidates are unacceptable

**Example:**
```python
def send_email(self, to, subject, body):
    if os.getenv("DRY_RUN", "true").lower() == "true":
        logger.info(f"[DRY_RUN] Email to {to}: {subject}")
        return f"fake_msg_id_{uuid.uuid4().hex[:8]}"
    return self._send_real_email(to, subject, body)
```

### VI. Audit Everything

**Every AI decision and human action must be logged to `audit_log` table.**

**Required Fields:**
- `action_type` (score_candidate, generate_questions, analyze_reply, approve, reject)
- `actor` (system, grok-3, grok-3-mini, manager@company.com)
- `input_summary` (CV snippet, questions sent, reply received)
- `output_summary` (score, recommendation, email sent)
- `approval_status` (pending, approved, rejected)
- `approved_by` (email of approver)
- `result` (success, failure, manual_review)

**Audit failures must never crash the main pipeline** — use try/except in `audit_service.log_action()`.

### VII. Test Coverage Requirements (NON-NEGOTIABLE)

**All tests must pass before build is considered complete.**

| Module | Min Coverage |
|---|---|
| `screening_agent.py` | 90% |
| `db/crud.py` | 95% |
| `services/pdf_service.py` | 95% |
| `services/gmail_service.py` | 85% |
| `orchestrator.py` | 85% |
| `routers/` | 80% |
| `watchers/` | 75% |

**Testing Requirements:**
- Use `pytest` with `pytest-asyncio` for async tests
- Use in-memory SQLite (`sqlite+aiosqlite:///:memory:`) for tests — no real Postgres
- Mock all external APIs (Grok, Gmail) — never call real APIs in tests
- Use `conftest.py` for shared fixtures
- Run tests with: `uv run pytest tests/ -v`

## Security & Secrets Management

### Never Commit Secrets

- All API keys, tokens, passwords in `.env` files
- `.env` files in `.gitignore`
- Provide `.env.example` with placeholder values
- Use `python-dotenv` and `os.getenv()` for all secrets
- OAuth2 for Gmail authentication (never hardcode credentials)

### Git Safety Protocol

- NEVER update git config
- NEVER run destructive git commands (push --force, hard reset) unless explicitly requested
- NEVER skip hooks (--no-verify, --no-gpg-sign)
- NEVER force push to main/master
- Avoid `git commit --amend` unless ALL conditions met:
  1. User explicitly requested amend, OR commit succeeded but pre-commit hook auto-modified files
  2. HEAD commit was created by you in this conversation
  3. Commit has NOT been pushed to remote

## Technology Stack (Fixed)

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

**No substitutions allowed without explicit approval.**

## Code Quality Standards

### Smallest Viable Change

- Only make changes directly requested or clearly necessary
- Don't add features, refactor code, or make "improvements" beyond what was asked
- A bug fix doesn't need surrounding code cleaned up
- Don't add docstrings, comments, or type annotations to code you didn't change
- Don't create helpers, utilities, or abstractions for one-time operations
- Three similar lines of code is better than a premature abstraction

### No Backwards-Compatibility Hacks

- If something is unused, delete it completely
- No renaming unused `_vars`
- No re-exporting types
- No `// removed` comments for removed code
- No feature flags or compatibility shims when you can just change the code

### Code References

- When referencing code, use format: `file_path:line_number`
- Example: "Clients are marked as failed in `src/services/process.ts:712`"

## Development Workflow

### Build Order (Must Follow)

1. Run `uv init backend` to scaffold backend project
2. Create folder structure exactly as defined in blueprint
3. `backend/db/models.py` → `backend/db/database.py` → `backend/db/crud.py`
4. `backend/screening_agent.py` (all 3 agent functions)
5. `backend/services/` (pdf, gmail, audit)
6. `backend/watchers/` (base, gmail, reply)
7. `backend/orchestrator.py`
8. `backend/daily_digest.py`
9. `backend/main.py` + all routers
10. Complete Next.js frontend (all components + pages)
11. `docker-compose.yml`, `.gitignore`, `README.md`, `.env.example`
12. Run `docker-compose up -d`
13. Run `uv sync`
14. Run `uv run uvicorn main:app --reload` → verify `/health` returns `{"status": "ok"}`
15. Run `uv run pytest tests/ -v` → **all tests must pass**
16. Report any issues and fix them

### No Clarifying Questions

- If something is ambiguous, make a reasonable engineering decision
- Implement it and note the decision in a code comment
- The blueprint is the source of truth

## Governance

This constitution supersedes all other practices and preferences. All code, PRs, and reviews must verify compliance with these principles.

**Amendments require:**
1. Documentation of the change and rationale
2. User approval
3. Migration plan for existing code (if applicable)

**Complexity must be justified** — default to simplicity and YAGNI principles.

**Version**: 1.0.0 | **Ratified**: 2026-04-27 | **Last Amended**: 2026-04-27

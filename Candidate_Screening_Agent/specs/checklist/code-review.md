# Code Review Checklist

**Feature**: Candidate Screening Agent
**Purpose**: Ensure code quality and adherence to constitution before merging
**Last Updated**: 2026-04-27

---

## Constitution Compliance

### I. Human-in-the-Loop (HITL) Boundaries

- [ ] No interview invites sent without explicit human approval
- [ ] No rejection emails sent without explicit human approval
- [ ] All sensitive actions go through `pending_approvals` table
- [ ] Screening questions can be sent autonomously (template-based only)
- [ ] Audit log records both AI recommendation AND human decision

### II. Async-First Architecture

- [ ] All I/O operations use `async def` and `await`
- [ ] No blocking calls in event loop (no `time.sleep()`, use `asyncio.sleep()`)
- [ ] FastAPI routes use async handlers
- [ ] SQLAlchemy uses `AsyncSession` and `asyncpg`
- [ ] Redis uses `redis.asyncio`
- [ ] `asyncio.gather()` used for concurrent operations
- [ ] `asyncio.create_task()` used for background tasks

### III. AI-First with Grok

- [ ] `set_tracing_disabled(True)` called at module top
- [ ] `OpenAIChatCompletionsModel` used (NOT `OpenAIResponsesModel`)
- [ ] `Runner.run()` used (NOT `Runner.run_sync()`)
- [ ] `grok-3` used for deep reasoning (CV scoring, reply analysis)
- [ ] `grok-3-mini` used for fast tasks (questions, digest)
- [ ] JSON parsing wrapped in try/except with retry logic
- [ ] Retry once on JSON parse failure with stricter prompt

### IV. Error Handling & Resilience

- [ ] Gmail API timeouts use exponential backoff (2s → 4s → 8s)
- [ ] Grok API errors retry once, then mark `manual_review`
- [ ] JSON parse errors retry once, then raise
- [ ] Scanned PDFs flagged with `scanned_pdf=true`
- [ ] Redis unavailable falls back to in-memory queue
- [ ] Database unavailable raises loudly (no silent failures)
- [ ] Audit failures never crash pipeline (try/except in audit_service)

### V. DRY_RUN by Default

- [ ] `DRY_RUN=true` in `.env.example`
- [ ] Every `send_email()` call checks `os.getenv("DRY_RUN")`
- [ ] DRY_RUN logs to console and returns fake message ID
- [ ] No real emails sent unless `DRY_RUN=false` explicitly set

### VI. Audit Everything

- [ ] Every AI decision logged to `audit_log`
- [ ] Every human action logged to `audit_log`
- [ ] All required fields populated (action_type, actor, result)
- [ ] Input/output summaries included (not full data)
- [ ] Approval status and approver email captured

### VII. Test Coverage Requirements

- [ ] All new code has corresponding tests
- [ ] Tests use `pytest-asyncio` for async functions
- [ ] Tests use in-memory SQLite (not real Postgres)
- [ ] All external APIs mocked (Grok, Gmail)
- [ ] Coverage meets minimum targets (75-95%)

---

## Code Quality

### General

- [ ] Code follows PEP 8 style guide
- [ ] No unused imports
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] No hardcoded values (use environment variables)
- [ ] No secrets in code
- [ ] Meaningful variable and function names
- [ ] Functions are single-purpose and focused

### Smallest Viable Change

- [ ] Only changes directly requested or clearly necessary
- [ ] No unnecessary refactoring of unrelated code
- [ ] No added features beyond requirements
- [ ] No docstrings/comments added to unchanged code
- [ ] No premature abstractions or helpers for one-time operations

### No Backwards-Compatibility Hacks

- [ ] Unused code deleted completely (no `_unused` variables)
- [ ] No re-exporting types
- [ ] No `# removed` comments
- [ ] No feature flags for simple changes

### Type Hints

- [ ] All function parameters have type hints
- [ ] All function return types specified
- [ ] Use `| None` for optional types (not `Optional[]`)
- [ ] Use `list[str]` not `List[str]` (Python 3.11+)

### Error Handling

- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Error messages are descriptive
- [ ] Errors logged with context
- [ ] Critical errors raise loudly
- [ ] Transient errors retry gracefully

---

## Database

### Models

- [ ] All fields have correct types
- [ ] Foreign keys defined with `ON DELETE` behavior
- [ ] Indexes defined for frequently queried fields
- [ ] JSON columns used for flexible data
- [ ] Timestamps use `TIMESTAMPTZ` (timezone-aware)
- [ ] Enums use CHECK constraints

### CRUD Operations

- [ ] All CRUD functions are async
- [ ] Transactions used where appropriate
- [ ] No N+1 query problems
- [ ] Eager loading used for relationships
- [ ] Queries use indexes effectively

### Migrations

- [ ] Schema changes have migration scripts
- [ ] Migrations are reversible
- [ ] Migrations tested before deployment

---

## API

### Endpoints

- [ ] RESTful design (correct HTTP methods)
- [ ] Async route handlers
- [ ] Dependency injection for DB session
- [ ] Pydantic models for request/response validation
- [ ] Appropriate HTTP status codes (200, 201, 404, 500)
- [ ] Error responses include helpful messages

### CORS

- [ ] CORS configured with specific origins (not `*`)
- [ ] Allowed methods specified
- [ ] Allowed headers specified

### Documentation

- [ ] Swagger UI accessible at `/docs`
- [ ] All endpoints documented
- [ ] Request/response schemas defined

---

## AI Integration

### Grok API

- [ ] API key from environment variable
- [ ] Base URL set to `https://api.x.ai/v1`
- [ ] Correct model selected (grok-3 vs grok-3-mini)
- [ ] Prompts are clear and specific
- [ ] JSON-only output requested
- [ ] Retry logic implemented

### Prompt Engineering

- [ ] Prompts reference rubric explicitly
- [ ] Prompts request structured output
- [ ] Prompts avoid ambiguity
- [ ] Prompts include examples where helpful

---

## Services

### PDF Service

- [ ] Uses `pdfplumber` library
- [ ] Handles multi-page PDFs
- [ ] Handles scanned PDFs gracefully
- [ ] Strips excess whitespace
- [ ] Returns clean text

### Gmail Service

- [ ] OAuth2 authentication
- [ ] DRY_RUN mode implemented
- [ ] Email templates professional and empathetic
- [ ] Rate limiting respected (20 emails/hour)
- [ ] Message IDs tracked for reply matching

### Audit Service

- [ ] Never raises exceptions
- [ ] Logs errors silently
- [ ] All required fields captured

---

## Watchers

### Base Watcher

- [ ] Abstract base class with required methods
- [ ] Infinite loop with error recovery
- [ ] Configurable check interval
- [ ] Logging for all actions

### Gmail Watcher

- [ ] Polls Gmail API at correct interval
- [ ] Tracks processed message IDs
- [ ] Skips emails without PDF
- [ ] Extracts PDF and creates candidate
- [ ] Pushes to Redis queue

### Reply Watcher

- [ ] Polls Gmail API at correct interval
- [ ] Matches replies using headers
- [ ] Queries candidates with status `awaiting_reply`
- [ ] Pushes to Redis queue

---

## Orchestrator

### Process New Candidate

- [ ] Fetches candidate from DB
- [ ] Calls `score_candidate()` with Grok
- [ ] Updates DB with score
- [ ] Creates rejection approval if disqualified
- [ ] Generates screening questions if qualified
- [ ] Sends screening questions via Gmail
- [ ] Updates status to `awaiting_reply`
- [ ] Logs to audit_log

### Process Candidate Reply

- [ ] Fetches candidate and original score
- [ ] Calls `analyze_reply()` with Grok
- [ ] Updates DB with reply and final score
- [ ] Creates advance approval
- [ ] Logs to audit_log

### Main Loop

- [ ] Consumes both queues concurrently
- [ ] Uses `brpop(timeout=1)` for non-blocking
- [ ] Handles exceptions gracefully
- [ ] Logs errors

---

## Frontend

### Components

- [ ] TypeScript types defined
- [ ] Props validated
- [ ] Error states handled
- [ ] Loading states shown
- [ ] Responsive design (mobile, tablet, desktop)

### API Integration

- [ ] Fetch from correct backend URL
- [ ] Error handling for failed requests
- [ ] Loading indicators during fetch
- [ ] Optimistic UI updates where appropriate

### Styling

- [ ] Tailwind CSS classes used consistently
- [ ] No inline styles
- [ ] Responsive breakpoints used
- [ ] Accessible color contrast

---

## Testing

### Unit Tests

- [ ] All new functions have tests
- [ ] Tests use descriptive names
- [ ] Tests are independent (no shared state)
- [ ] Tests use fixtures for setup
- [ ] Tests mock external dependencies
- [ ] Tests assert expected behavior

### Integration Tests

- [ ] End-to-end flows tested
- [ ] Database integration tested
- [ ] Redis integration tested
- [ ] API integration tested

### Test Coverage

- [ ] Coverage meets minimum targets
- [ ] Critical paths have 100% coverage
- [ ] Edge cases tested

---

## Security

### Secrets Management

- [ ] No secrets in code
- [ ] No secrets in git history
- [ ] Secrets in environment variables
- [ ] `.env` in `.gitignore`

### Input Validation

- [ ] All user inputs validated
- [ ] SQL injection prevented (use ORM)
- [ ] XSS prevented (escape output)
- [ ] Email addresses validated

### Authentication & Authorization

- [ ] OAuth2 implemented correctly
- [ ] Tokens refreshed automatically
- [ ] No credentials in logs

---

## Documentation

### Code Comments

- [ ] Complex logic explained
- [ ] Non-obvious decisions documented
- [ ] No redundant comments (code is self-documenting)

### README

- [ ] Setup instructions clear
- [ ] Environment variables documented
- [ ] How to run tests documented
- [ ] How to deploy documented

### API Documentation

- [ ] All endpoints documented in Swagger
- [ ] Request/response examples provided

---

## Performance

### Database

- [ ] Queries use indexes
- [ ] No N+1 queries
- [ ] Connection pooling configured
- [ ] Transactions used appropriately

### API

- [ ] Response times acceptable
- [ ] No unnecessary data fetched
- [ ] Pagination used for large lists

### Memory

- [ ] No memory leaks
- [ ] Large files streamed (not loaded into memory)
- [ ] Resources cleaned up properly

---

## Git

### Commits

- [ ] Commit messages descriptive
- [ ] Commits atomic (one logical change)
- [ ] No merge commits (use rebase)
- [ ] No WIP commits in PR

### Pull Request

- [ ] PR title descriptive
- [ ] PR description explains changes
- [ ] PR linked to issue/task
- [ ] PR size reasonable (<500 lines)
- [ ] No unrelated changes

---

## Sign-off

- [ ] Code reviewed by: _________________ Date: _______
- [ ] All checklist items verified
- [ ] Approved for merge: ☐ Yes ☐ No

**Notes**:

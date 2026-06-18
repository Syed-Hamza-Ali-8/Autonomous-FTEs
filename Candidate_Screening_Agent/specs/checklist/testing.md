# Testing Checklist

**Feature**: Candidate Screening Agent
**Purpose**: Verify comprehensive test coverage before deployment
**Last Updated**: 2026-04-27

---

## Unit Tests

### Screening Agent Tests (`test_screening_agent.py`)

- [ ] `test_score_candidate_returns_valid_dict` - CV scoring returns structured JSON
- [ ] `test_score_candidate_retries_on_invalid_json` - Retry logic on JSON parse failure
- [ ] `test_score_candidate_raises_after_two_failures` - Raises after retry exhausted
- [ ] `test_score_candidate_disqualified` - Handles disqualified candidates correctly
- [ ] `test_generate_questions_returns_five` - Always returns exactly 5 questions
- [ ] `test_generate_questions_uses_mini_model` - Uses grok-3-mini not grok-3
- [ ] `test_analyze_reply_returns_valid_dict` - Reply analysis returns expected fields
- [ ] `test_analyze_reply_score_delta_applied` - Score delta calculation correct
- [ ] Coverage: ≥90%

### PDF Service Tests (`test_pdf_service.py`)

- [ ] `test_extract_text_returns_string` - Always returns string
- [ ] `test_extract_text_joins_multiple_pages` - Joins all pages correctly
- [ ] `test_extract_text_handles_scanned_pdf` - Returns fallback message for scanned PDFs
- [ ] `test_extract_text_strips_whitespace` - Removes excess whitespace
- [ ] Coverage: ≥95%

### Gmail Service Tests (`test_gmail_service.py`)

- [ ] `test_send_email_dry_run_does_not_call_api` - DRY_RUN prevents real API calls
- [ ] `test_send_email_dry_run_returns_fake_id` - Returns fake message ID in DRY_RUN
- [ ] `test_send_screening_questions_formats_correctly` - Email template includes all questions
- [ ] `test_send_interview_invite_uses_correct_recipient` - Sends to correct email
- [ ] `test_send_rejection_email_uses_correct_recipient` - Sends to correct email
- [ ] `test_real_send_blocked_in_dry_run` - Gmail API never called in DRY_RUN
- [ ] Coverage: ≥85%

### CRUD Tests (`test_crud.py`)

- [ ] `test_create_candidate` - Inserts candidate with all fields
- [ ] `test_get_candidate` - Retrieves correct candidate by ID
- [ ] `test_update_candidate_status` - Updates status field
- [ ] `test_update_candidate_score` - Stores score breakdown correctly
- [ ] `test_update_candidate_questions` - Stores screening questions
- [ ] `test_update_candidate_reply` - Stores reply and analysis
- [ ] `test_create_pending_approval` - Creates approval record
- [ ] `test_get_pending_approvals` - Retrieves pending approvals
- [ ] `test_approve_candidate` - Sets status and approver
- [ ] `test_reject_candidate` - Sets status and approver
- [ ] `test_create_audit_log` - Logs action with all fields
- [ ] Coverage: ≥95%

### Orchestrator Tests (`test_orchestrator.py`)

- [ ] `test_process_new_candidate_full_flow` - Complete flow for qualified candidate
- [ ] `test_process_new_candidate_disqualified` - Creates rejection approval for disqualified
- [ ] `test_process_candidate_reply` - Analyzes reply and creates advance approval
- [ ] `test_orchestrator_handles_errors` - Error handling and recovery
- [ ] Coverage: ≥85%

### Router Tests (`test_routers_*.py`)

- [ ] `test_health_endpoint` - Returns 200 with status ok
- [ ] `test_get_all_candidates_empty` - Returns empty list when no candidates
- [ ] `test_get_candidate_not_found` - Returns 404 for non-existent
- [ ] `test_get_candidates_by_status` - Filters by status correctly
- [ ] `test_get_pending_approvals_empty` - Returns empty list when none exist
- [ ] `test_approve_nonexistent_approval` - Returns 404
- [ ] `test_reject_nonexistent_approval` - Returns 404
- [ ] `test_approve_triggers_interview_invite` - Calls gmail_service correctly
- [ ] Coverage: ≥80%

### Watcher Tests (`test_watchers.py`)

- [ ] `test_gmail_watcher_skips_processed_ids` - Doesn't reprocess emails
- [ ] `test_gmail_watcher_skips_no_pdf_attachment` - Skips emails without PDF
- [ ] `test_base_watcher_continues_on_error` - Error recovery works
- [ ] Coverage: ≥75%

---

## Integration Tests

### End-to-End Flow

- [ ] Test: New application → scoring → questions → reply → approval → interview invite
- [ ] Test: New application → scoring → disqualified → rejection approval
- [ ] Test: Candidate reply → analysis → advance approval
- [ ] Test: Hiring manager approval → interview invite sent
- [ ] Test: Hiring manager rejection → rejection email sent

### Database Integration

- [ ] Test: All CRUD operations with real PostgreSQL (not SQLite)
- [ ] Test: Foreign key constraints enforced
- [ ] Test: Cascade deletes work correctly
- [ ] Test: JSON columns store and retrieve correctly
- [ ] Test: Indexes improve query performance

### Redis Integration

- [ ] Test: Push to screening_queue and pop successfully
- [ ] Test: Push to reply_queue and pop successfully
- [ ] Test: Concurrent queue consumption works
- [ ] Test: Fallback to in-memory queue when Redis unavailable

### Gmail API Integration

- [ ] Test: OAuth2 authentication works
- [ ] Test: Fetch unread emails with label "jobs"
- [ ] Test: Download PDF attachments
- [ ] Test: Match replies using message headers
- [ ] Test: Send email (DRY_RUN mode)

### Grok API Integration

- [ ] Test: CV scoring with real API (manual test, not automated)
- [ ] Test: Question generation with real API
- [ ] Test: Reply analysis with real API
- [ ] Test: Error handling for API failures
- [ ] Test: JSON parsing with retry logic

---

## Manual Testing

### Happy Path

- [ ] Send test email with PDF CV to jobs inbox
- [ ] Verify candidate appears in dashboard within 2 minutes
- [ ] Verify CV text extracted correctly
- [ ] Verify score calculated and stored
- [ ] Verify screening questions sent (check DRY_RUN logs)
- [ ] Reply to screening email
- [ ] Verify reply detected within 1 minute
- [ ] Verify reply analysis completed
- [ ] Verify pending approval created
- [ ] Open dashboard and view candidate detail
- [ ] Click "Approve" button
- [ ] Verify interview invite sent (check DRY_RUN logs)
- [ ] Verify audit log captures all actions

### Error Scenarios

- [ ] Test: Email without PDF attachment (should skip)
- [ ] Test: Scanned PDF (should flag for manual review)
- [ ] Test: Grok API timeout (should retry and mark manual review)
- [ ] Test: Invalid JSON from Grok (should retry with stricter prompt)
- [ ] Test: Database connection failure (should fail loudly)
- [ ] Test: Redis connection failure (should fall back to in-memory)
- [ ] Test: Gmail API rate limit (should retry with backoff)

### Edge Cases

- [ ] Test: Candidate applies to multiple jobs simultaneously
- [ ] Test: Candidate replies multiple times
- [ ] Test: Approval expires after 48 hours
- [ ] Test: Duplicate email (same candidate applies twice)
- [ ] Test: Very long CV (>10 pages)
- [ ] Test: CV with special characters or non-ASCII
- [ ] Test: Empty email body
- [ ] Test: Email with multiple PDF attachments (should use first)

### UI/UX Testing

- [ ] Test: Dashboard loads within 2 seconds
- [ ] Test: Pipeline board displays all 4 columns
- [ ] Test: Candidate cards show correct information
- [ ] Test: Score badges color-coded correctly (green ≥80, amber 60-79, red <60)
- [ ] Test: Status pills display correct status
- [ ] Test: Candidate detail page shows all information
- [ ] Test: Approval panel displays AI recommendation
- [ ] Test: Approve button triggers confirmation
- [ ] Test: Reject button shows reason input
- [ ] Test: Real-time updates work (30s polling)
- [ ] Test: Responsive design on mobile
- [ ] Test: Responsive design on tablet
- [ ] Test: Responsive design on desktop

---

## Performance Testing

### Load Testing

- [ ] Test: 10 concurrent candidates processed successfully
- [ ] Test: 50 concurrent candidates processed successfully
- [ ] Test: 100 concurrent candidates processed successfully
- [ ] Test: API response times < 500ms for list endpoints
- [ ] Test: API response times < 1s for detail endpoints
- [ ] Test: CV scoring completes within 30 seconds
- [ ] Test: Question generation completes within 15 seconds
- [ ] Test: Reply analysis completes within 30 seconds

### Database Performance

- [ ] Test: Query candidates by status < 10ms
- [ ] Test: Query pending approvals < 20ms
- [ ] Test: Query daily digest data < 50ms
- [ ] Test: Insert candidate < 5ms
- [ ] Test: Update candidate < 5ms

### Memory Usage

- [ ] Test: Backend memory usage < 512MB under normal load
- [ ] Test: No memory leaks after 1000 candidates processed
- [ ] Test: Redis memory usage < 100MB

---

## Security Testing

### Authentication & Authorization

- [ ] Test: Gmail OAuth2 token refresh works
- [ ] Test: Invalid API keys rejected
- [ ] Test: CORS blocks unauthorized origins

### Input Validation

- [ ] Test: SQL injection attempts blocked
- [ ] Test: XSS attempts blocked
- [ ] Test: Invalid email addresses rejected
- [ ] Test: Invalid status values rejected
- [ ] Test: Score out of range (0-100) rejected

### Data Protection

- [ ] Test: Secrets not exposed in logs
- [ ] Test: Secrets not exposed in error messages
- [ ] Test: Secrets not exposed in API responses
- [ ] Test: CV text not exposed in audit log (only summary)

---

## Regression Testing

### After Each Code Change

- [ ] Run full test suite: `uv run pytest tests/ -v`
- [ ] Verify all tests pass
- [ ] Verify test coverage meets targets
- [ ] Run linter: `ruff check .`
- [ ] Run type checker: `mypy .`

### Before Each Deployment

- [ ] Run full test suite
- [ ] Run integration tests
- [ ] Run manual smoke tests
- [ ] Verify no regressions in existing functionality

---

## Test Coverage Targets

| Module | Target | Actual | Status |
|--------|--------|--------|--------|
| screening_agent.py | 90% | ___ % | ⬜ |
| db/crud.py | 95% | ___ % | ⬜ |
| services/pdf_service.py | 95% | ___ % | ⬜ |
| services/gmail_service.py | 85% | ___ % | ⬜ |
| orchestrator.py | 85% | ___ % | ⬜ |
| routers/ | 80% | ___ % | ⬜ |
| watchers/ | 75% | ___ % | ⬜ |

**Overall Target**: ≥85%
**Overall Actual**: ___ %

---

## Test Execution

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Specific Test File
```bash
uv run pytest tests/test_screening_agent.py -v
```

### Run With Coverage
```bash
uv run pytest tests/ -v --cov=. --cov-report=term-missing
```

### Run Only Fast Tests
```bash
uv run pytest tests/ -v -m "not slow"
```

---

**Sign-off**:
- [ ] QA Lead: _________________ Date: _______
- [ ] Tech Lead: _________________ Date: _______

**Notes**:

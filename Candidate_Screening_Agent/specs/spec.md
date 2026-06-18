# Candidate Screening Agent - Feature Specification

**Feature**: Autonomous Candidate Screening Digital FTE
**Status**: Draft
**Owner**: Development Team
**Created**: 2026-04-27
**Last Updated**: 2026-04-27

---

## Problem Statement

Early-stage hiring pipelines are time-consuming and repetitive. Hiring managers spend hours:
- Manually reviewing CVs against job requirements
- Crafting personalized screening questions for each candidate
- Analyzing candidate responses
- Scheduling interviews or sending rejection emails

This creates bottlenecks in the hiring process and delays time-to-hire for qualified candidates.

## Solution Overview

Build an **autonomous AI agent** that manages the full early-stage hiring pipeline without human intervention, except for final approval decisions. The agent:

1. Monitors Gmail inbox for job applications with PDF CVs
2. Extracts and scores CVs against job-specific rubrics using Grok AI
3. Generates and sends personalized screening questions
4. Analyzes candidate replies and adjusts scores
5. Creates pending approval records for hiring manager review
6. Sends interview invites (on approval) or rejection emails (on rejection)
7. Provides daily talent digest emails with pipeline summary

**Core Principle**: The agent never sends final candidate decisions without explicit human approval (HITL).

---

## Functional Requirements

### FR-1: CV Processing Pipeline

**FR-1.1**: Monitor Gmail inbox for new job applications
- Poll Gmail API every 2 minutes for unread emails with label `jobs`
- Track processed message IDs to avoid duplicates
- Extract sender email and name from headers

**FR-1.2**: Extract text from PDF CVs
- Download PDF attachments from application emails
- Use `pdfplumber` to extract text from all pages
- Handle scanned PDFs (no extractable text) by flagging for manual review
- Store extracted CV text in database

**FR-1.3**: Score candidates against job rubrics
- Load job-specific rubric from Markdown file
- Use Grok `grok-3` model to score candidate objectively
- Return structured JSON with:
  - Total score (0-100)
  - Must-haves met (boolean)
  - Skill/experience/project/communication breakdown
  - Strengths, weaknesses, red flags
  - Recommendation (advance/reject/review)
  - Confidence level (high/medium/low)

### FR-2: Screening Questions Workflow

**FR-2.1**: Generate personalized screening questions
- Use Grok `grok-3-mini` to generate exactly 5 questions
- Questions must reference specific items from candidate's CV
- Questions must align with job rubric requirements

**FR-2.2**: Send screening questions via Gmail
- Format questions in professional email template
- Include candidate name and job title
- Store Gmail message ID for reply tracking
- Respect DRY_RUN mode (log only, don't send)

**FR-2.3**: Monitor for candidate replies
- Poll Gmail API every 1 minute for replies to screening emails
- Match replies using `In-Reply-To` and `References` headers
- Extract reply text and associate with candidate record

**FR-2.4**: Analyze candidate replies
- Use Grok `grok-3` to analyze reply quality
- Calculate score delta (-20 to +20 points)
- Determine final score and updated recommendation
- Generate brief summary of notable answers

### FR-3: Human-in-the-Loop Approval

**FR-3.1**: Create pending approval records
- Automatically create approval record when:
  - Candidate fails must-have requirements (reject action)
  - Candidate completes screening questions (advance action)
- Include: score, recommendation, brief summary, expiration (48 hours)

**FR-3.2**: Dashboard approval interface
- Display all pending approvals with candidate details
- Show AI recommendation and confidence level
- Provide "Approve" and "Reject" buttons
- Require approver email for audit trail

**FR-3.3**: Execute approved actions
- On approval: send interview invite email via Gmail
- On rejection: send empathetic rejection email via Gmail
- Update candidate status in database
- Log action to audit log with approver identity

### FR-4: Audit and Reporting

**FR-4.1**: Comprehensive audit logging
- Log every AI decision (scoring, question generation, reply analysis)
- Log every human action (approve, reject)
- Store: action type, actor, input/output summaries, timestamps
- Never crash pipeline on audit log failures

**FR-4.2**: Daily talent digest
- Run at 8:00 AM daily via APScheduler
- Fetch all candidates from past 24 hours
- Group by status (applied, screening, shortlisted, rejected)
- Use Grok `grok-3-mini` to generate 3-sentence executive summary
- Send digest email to hiring manager

### FR-5: Dashboard and API

**FR-5.1**: Candidate management API
- `GET /candidates` - list all candidates with scores
- `GET /candidates/{id}` - full candidate detail
- `GET /candidates/by-status/{status}` - filter by pipeline status
- `GET /candidates/{id}/brief` - one-page candidate brief

**FR-5.2**: Approval management API
- `GET /approvals/pending` - list pending approvals
- `POST /approvals/{id}/approve` - approve candidate
- `POST /approvals/{id}/reject` - reject candidate with reason

**FR-5.3**: Job management API
- `GET /jobs` - list all jobs
- `POST /jobs` - create job with rubric
- `GET /jobs/{id}` - job detail with candidate counts

**FR-5.4**: Next.js dashboard
- Pipeline board with 4 columns (Applied, Screening, Shortlisted, Pending Approval)
- Candidate cards with score badges and status pills
- Candidate detail pages with full scoring breakdown
- Approval panel with AI recommendation
- Real-time updates every 30 seconds

---

## Non-Functional Requirements

### NFR-1: Performance

- Gmail polling: max 2-minute delay for new applications
- Reply polling: max 1-minute delay for candidate responses
- CV scoring: complete within 30 seconds
- Question generation: complete within 15 seconds
- Reply analysis: complete within 30 seconds
- Dashboard API responses: < 500ms for list endpoints, < 1s for detail endpoints

### NFR-2: Reliability

- System uptime: 99.5% (excluding planned maintenance)
- Zero data loss on candidate records
- Graceful degradation when Redis unavailable (fall back to in-memory queue)
- Automatic retry with exponential backoff for transient failures
- All background tasks must recover from crashes and resume

### NFR-3: Security

- All API keys and secrets in environment variables (never hardcoded)
- OAuth2 for Gmail authentication
- No secrets committed to git repository
- Audit log for all sensitive actions
- DRY_RUN mode by default to prevent accidental emails

### NFR-4: Scalability

- Support up to 100 candidates per day
- Support up to 20 concurrent job postings
- Rate limit: max 20 emails per hour (configurable)
- Database queries optimized with indexes on status and job_id

### NFR-5: Maintainability

- Async/await throughout (no blocking I/O)
- Comprehensive test coverage (75-95% depending on module)
- All tests must pass before deployment
- Clear separation of concerns (watchers, orchestrator, services, routers)
- Structured logging with context

---

## Success Criteria

### Must Have (MVP)

1. ✅ Agent successfully monitors Gmail and processes new applications
2. ✅ CV scoring produces accurate, structured results matching rubric
3. ✅ Screening questions are personalized and relevant to candidate CV
4. ✅ Reply analysis correctly adjusts candidate scores
5. ✅ Pending approvals require explicit human action (no auto-advance)
6. ✅ Interview invites and rejection emails sent only after approval
7. ✅ Audit log captures all AI decisions and human actions
8. ✅ Dashboard displays pipeline with real-time updates
9. ✅ All tests pass with minimum coverage targets met
10. ✅ DRY_RUN mode prevents accidental emails during testing

### Should Have (Post-MVP)

- Bulk approval actions (approve/reject multiple candidates)
- Candidate comparison view (side-by-side scoring)
- Custom rubric editor in dashboard
- Email template customization
- Webhook notifications for pending approvals
- Advanced analytics (time-to-hire, conversion rates)

### Could Have (Future)

- Multi-language support for international hiring
- Video interview scheduling integration
- ATS (Applicant Tracking System) integration
- Candidate self-service portal
- AI-powered interview question generation based on CV gaps

---

## Constraints

### Technical Constraints

- Must use Grok API (xAI) via OpenAI Agents SDK
- Must use `grok-3` for deep reasoning, `grok-3-mini` for fast tasks
- Must use PostgreSQL (no NoSQL alternatives)
- Must use Redis for job queues (no alternative queue systems)
- Must use FastAPI with async/await (no Flask or Django)
- Must use Next.js 14 App Router (no Pages Router)

### Business Constraints

- No candidate data may be deleted automatically (GDPR compliance requires manual deletion)
- All rejection emails must be empathetic and professional
- Hiring manager must approve within 48 hours or approval expires
- Maximum 20 emails per hour to avoid Gmail rate limits

### Regulatory Constraints

- GDPR compliance: candidates can request data deletion
- Equal opportunity: AI scoring must be bias-free and auditable
- Data retention: audit logs must be kept for 2 years minimum

---

## Assumptions

1. Gmail API credentials are available and configured
2. Grok API key is available with sufficient quota
3. Job rubrics are pre-written in Markdown format
4. Hiring manager has access to dashboard URL
5. Candidates reply to screening emails (not all will)
6. PDF CVs are text-based (not scanned images)
7. PostgreSQL and Redis are available via Docker Compose
8. Deployment targets are Railway (backend) and Vercel (frontend)

---

## Out of Scope

- Automated interview scheduling (requires calendar integration)
- Background checks or reference verification
- Salary negotiation or offer letter generation
- Onboarding workflow after hire
- Integration with existing ATS systems
- Mobile app (web dashboard only)
- Real-time chat with candidates
- Video interview recording or analysis

---

## Dependencies

### External Services

- **Gmail API**: Email monitoring and sending
- **Grok API (xAI)**: AI reasoning for scoring and analysis
- **PostgreSQL**: Primary data store
- **Redis**: Job queue and caching

### Internal Dependencies

- `.specify/memory/constitution.md`: Project principles and standards
- `backend/rubrics/*.md`: Job-specific scoring rubrics
- `.env`: Environment variables and secrets

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Grok API rate limits exceeded | High | Medium | Implement exponential backoff, use grok-3-mini for non-critical tasks |
| Gmail API quota exceeded | High | Low | Rate limit to 20 emails/hour, monitor quota usage |
| Scanned PDFs (no text extraction) | Medium | Medium | Flag for manual review, notify hiring manager |
| Candidate never replies to screening | Low | High | Set expiration on pending approvals, send reminder after 3 days |
| Bias in AI scoring | High | Low | Audit log all decisions, allow manual override, regular bias audits |
| Database connection failures | High | Low | Fail loudly, implement connection pooling, health checks |
| Redis unavailable | Medium | Low | Fall back to in-memory queue, log warning |

---

## Open Questions

1. **Q**: What happens if a candidate applies to multiple jobs simultaneously?
   **A**: Each application is treated independently with separate scoring.

2. **Q**: Can hiring managers customize screening questions?
   **A**: Not in MVP. Questions are AI-generated based on rubric. Post-MVP feature.

3. **Q**: How are expired approvals handled?
   **A**: Status changes to "expired", hiring manager notified in daily digest.

4. **Q**: Can candidates withdraw their application?
   **A**: Not in MVP. They can email hiring manager directly.

5. **Q**: What if CV is in non-English language?
   **A**: Out of scope for MVP. Grok may handle some languages, but not guaranteed.

---

## References

- [Candidate_Screening_Agent_Blueprint_2026.md](../Candidate_Screening_Agent_Blueprint_2026.md) - Detailed technical blueprint
- [.specify/memory/constitution.md](../.specify/memory/constitution.md) - Project constitution
- [Grok API Documentation](https://docs.x.ai/) - xAI Grok API reference
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-sdk) - Agent framework documentation
- [Gmail API v1](https://developers.google.com/gmail/api) - Gmail integration reference

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | [Pending] | [Pending] | [Pending] |
| Tech Lead | [Pending] | [Pending] | [Pending] |
| Security Review | [Pending] | [Pending] | [Pending] |

---

**Next Steps**: Proceed to `plan.md` for architectural design and implementation strategy.

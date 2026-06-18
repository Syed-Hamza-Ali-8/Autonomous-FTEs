# Candidate Screening Agent - Data Model

**Feature**: Autonomous Candidate Screening Digital FTE
**Status**: Final
**Created**: 2026-04-27
**Last Updated**: 2026-04-27

---

## Overview

This document defines the complete data model for the Candidate Screening Agent, including database schema, entity relationships, data types, constraints, and indexes.

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│       jobs          │
│─────────────────────│
│ id (PK)             │
│ title               │
│ slug (UNIQUE)       │
│ rubric_path         │
│ status              │
│ created_at          │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                      candidates                              │
│──────────────────────────────────────────────────────────────│
│ id (PK)                                                      │
│ job_id (FK → jobs.id)                                       │
│ email                                                        │
│ name                                                         │
│ cv_text                                                      │
│ status                                                       │
│ total_score                                                  │
│ must_haves_met                                              │
│ score_breakdown (JSONB)                                     │
│ strengths (JSONB)                                           │
│ weaknesses (JSONB)                                          │
│ red_flags (JSONB)                                           │
│ recommendation                                               │
│ confidence                                                   │
│ score_summary                                                │
│ screening_questions (JSONB)                                 │
│ candidate_reply                                              │
│ reply_analysis (JSONB)                                      │
│ gmail_message_id                                             │
│ created_at                                                   │
│ updated_at                                                   │
└──────────┬──────────────────────────────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                  pending_approvals                           │
│──────────────────────────────────────────────────────────────│
│ id (PK)                                                      │
│ candidate_id (FK → candidates.id)                           │
│ job_id (FK → jobs.id)                                       │
│ action                                                       │
│ score                                                        │
│ recommendation                                               │
│ brief_summary                                                │
│ status                                                       │
│ approved_by                                                  │
│ created_at                                                   │
│ expires_at                                                   │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      audit_log                               │
│──────────────────────────────────────────────────────────────│
│ id (PK)                                                      │
│ candidate_id (FK → candidates.id, nullable)                 │
│ action_type                                                  │
│ actor                                                        │
│ input_summary                                                │
│ output_summary                                               │
│ approval_status                                              │
│ approved_by                                                  │
│ result                                                       │
│ created_at                                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Table Definitions

### Table: `jobs`

**Purpose**: Stores job postings with associated rubrics.

**Schema**:
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    rubric_path VARCHAR(300) NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'paused')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_slug ON jobs(slug);
```

**Fields**:
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | SERIAL | No | Auto | Primary key |
| title | VARCHAR(200) | No | - | Job title (e.g., "Senior Backend Engineer") |
| slug | VARCHAR(100) | No | - | URL-friendly identifier (e.g., "senior-backend-engineer") |
| rubric_path | VARCHAR(300) | No | - | Path to rubric file (e.g., "rubrics/Senior_Backend_Engineer.md") |
| status | VARCHAR(20) | No | 'open' | Job status: open, closed, paused |
| created_at | TIMESTAMPTZ | No | NOW() | Job creation timestamp |

**Constraints**:
- `slug` must be unique
- `status` must be one of: 'open', 'closed', 'paused'

**Sample Data**:
```sql
INSERT INTO jobs (title, slug, rubric_path, status) VALUES
('Senior Backend Engineer', 'senior-backend-engineer', 'rubrics/Senior_Backend_Engineer.md', 'open'),
('Frontend Developer', 'frontend-developer', 'rubrics/Frontend_Developer.md', 'open'),
('DevOps Engineer', 'devops-engineer', 'rubrics/DevOps_Engineer.md', 'paused');
```

---

### Table: `candidates`

**Purpose**: Stores candidate applications with CV data, scores, and pipeline status.

**Schema**:
```sql
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    email VARCHAR(200) NOT NULL,
    name VARCHAR(200),
    cv_text TEXT,
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN (
        'queued', 'scoring', 'scored', 'questions_sent', 'awaiting_reply',
        'replied', 'shortlisted', 'rejected', 'hired', 'manual_review'
    )),
    total_score FLOAT,
    must_haves_met BOOLEAN,
    score_breakdown JSONB,
    strengths JSONB,
    weaknesses JSONB,
    red_flags JSONB,
    recommendation VARCHAR(20) CHECK (recommendation IN ('advance', 'reject', 'review')),
    confidence VARCHAR(20) CHECK (confidence IN ('high', 'medium', 'low')),
    score_summary TEXT,
    screening_questions JSONB,
    candidate_reply TEXT,
    reply_analysis JSONB,
    gmail_message_id VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_job_id ON candidates(job_id);
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_created_at ON candidates(created_at DESC);
```

**Fields**:
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | SERIAL | No | Auto | Primary key |
| job_id | INTEGER | No | - | Foreign key to jobs table |
| email | VARCHAR(200) | No | - | Candidate email address |
| name | VARCHAR(200) | Yes | NULL | Candidate full name |
| cv_text | TEXT | Yes | NULL | Extracted CV text from PDF |
| status | VARCHAR(50) | No | 'queued' | Pipeline status (see status values below) |
| total_score | FLOAT | Yes | NULL | Total score (0-100) |
| must_haves_met | BOOLEAN | Yes | NULL | Whether candidate meets must-have requirements |
| score_breakdown | JSONB | Yes | NULL | Detailed score breakdown (see JSON schema below) |
| strengths | JSONB | Yes | NULL | Array of candidate strengths |
| weaknesses | JSONB | Yes | NULL | Array of candidate weaknesses |
| red_flags | JSONB | Yes | NULL | Array of red flags |
| recommendation | VARCHAR(20) | Yes | NULL | AI recommendation: advance, reject, review |
| confidence | VARCHAR(20) | Yes | NULL | AI confidence: high, medium, low |
| score_summary | TEXT | Yes | NULL | Human-readable score summary |
| screening_questions | JSONB | Yes | NULL | Array of 5 screening questions |
| candidate_reply | TEXT | Yes | NULL | Candidate's reply to screening questions |
| reply_analysis | JSONB | Yes | NULL | Analysis of candidate's reply (see JSON schema below) |
| gmail_message_id | VARCHAR(200) | Yes | NULL | Gmail message ID for tracking replies |
| created_at | TIMESTAMPTZ | No | NOW() | Application received timestamp |
| updated_at | TIMESTAMPTZ | No | NOW() | Last update timestamp |

**Status Values**:
- `queued`: Application received, waiting for scoring
- `scoring`: CV scoring in progress
- `scored`: CV scored, ready for questions
- `questions_sent`: Screening questions sent to candidate
- `awaiting_reply`: Waiting for candidate reply
- `replied`: Candidate replied, analysis in progress
- `shortlisted`: Candidate passed screening, pending approval
- `rejected`: Candidate rejected (after approval)
- `hired`: Candidate hired (after approval)
- `manual_review`: Requires manual review (AI error or edge case)

**JSON Schemas**:

**score_breakdown**:
```json
{
  "skill_score": 35,
  "experience_score": 22,
  "project_score": 16,
  "communication_score": 9,
  "bonuses_applied": ["FastAPI (+5)", "PostgreSQL (+3)", "Kubernetes (+4)"]
}
```

**strengths** (array of strings):
```json
["Strong Python experience", "Cloud certified", "Real-world projects at scale"]
```

**weaknesses** (array of strings):
```json
["No open source contributions", "Limited testing experience"]
```

**red_flags** (array of strings):
```json
["Job-hopping (3 jobs in 2 years)", "No mention of CI/CD"]
```

**screening_questions** (array of 5 strings):
```json
[
  "Your CV mentions a payment system — what was the biggest scaling challenge?",
  "How did you handle database performance at 10M requests/day?",
  "Walk me through your CI/CD setup with GitHub Actions.",
  "How do you approach testing in a fast-moving team?",
  "Why are you interested in this specific role?"
]
```

**reply_analysis**:
```json
{
  "reply_score_delta": 6,
  "final_score": 88,
  "answer_quality": "high",
  "notable_answers": [
    "Excellent answer on Q1 about scaling with Redis caching",
    "Strong understanding of database indexing strategies"
  ],
  "updated_recommendation": "advance",
  "brief_summary": "Candidate answered all questions with depth and clarity. Strong technical knowledge."
}
```

**Sample Data**:
```sql
INSERT INTO candidates (job_id, email, name, cv_text, status, total_score, must_haves_met, recommendation, confidence) VALUES
(1, 'john.doe@example.com', 'John Doe', 'Senior Backend Engineer with 5 years Python...', 'shortlisted', 82.0, true, 'advance', 'high'),
(1, 'jane.smith@example.com', 'Jane Smith', 'Backend developer with 2 years experience...', 'rejected', 45.0, false, 'reject', 'high'),
(2, 'bob.jones@example.com', 'Bob Jones', 'Frontend developer specializing in React...', 'awaiting_reply', 75.0, true, 'advance', 'medium');
```

---

### Table: `pending_approvals`

**Purpose**: Stores pending human approval decisions (HITL).

**Schema**:
```sql
CREATE TABLE pending_approvals (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN ('advance', 'reject')),
    score FLOAT,
    recommendation TEXT,
    brief_summary TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'expired')),
    approved_by VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '48 hours')
);

CREATE INDEX idx_approvals_status ON pending_approvals(status);
CREATE INDEX idx_approvals_candidate_id ON pending_approvals(candidate_id);
CREATE INDEX idx_approvals_expires_at ON pending_approvals(expires_at);
```

**Fields**:
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | SERIAL | No | Auto | Primary key |
| candidate_id | INTEGER | No | - | Foreign key to candidates table |
| job_id | INTEGER | No | - | Foreign key to jobs table |
| action | VARCHAR(20) | No | - | Requested action: advance (send interview invite) or reject (send rejection email) |
| score | FLOAT | Yes | NULL | Candidate's final score |
| recommendation | TEXT | Yes | NULL | AI recommendation text |
| brief_summary | TEXT | Yes | NULL | Brief summary for hiring manager |
| status | VARCHAR(20) | No | 'pending' | Approval status: pending, approved, rejected, expired |
| approved_by | VARCHAR(200) | Yes | NULL | Email of approver |
| created_at | TIMESTAMPTZ | No | NOW() | Approval request created timestamp |
| expires_at | TIMESTAMPTZ | No | NOW() + 48h | Expiration timestamp (48 hours) |

**Business Rules**:
- Approval expires after 48 hours if not acted upon
- Only one pending approval per candidate at a time
- Approved/rejected approvals are immutable (no updates)

**Sample Data**:
```sql
INSERT INTO pending_approvals (candidate_id, job_id, action, score, recommendation, brief_summary, status) VALUES
(1, 1, 'advance', 88.0, 'Strong candidate with excellent technical skills', 'Scored 88/100. Answered screening questions with depth. Recommend interview.', 'pending'),
(2, 1, 'reject', 45.0, 'Does not meet minimum requirements', 'Scored 45/100. Missing must-have Python experience. Recommend rejection.', 'approved');
```

---

### Table: `audit_log`

**Purpose**: Immutable audit trail of all AI decisions and human actions.

**Schema**:
```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    approval_status VARCHAR(20),
    approved_by VARCHAR(200),
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'failure', 'manual_review')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_candidate ON audit_log(candidate_id);
CREATE INDEX idx_audit_action_type ON audit_log(action_type);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
```

**Fields**:
| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | SERIAL | No | Auto | Primary key |
| candidate_id | INTEGER | Yes | NULL | Foreign key to candidates table (nullable for system-level actions) |
| action_type | VARCHAR(50) | No | - | Type of action (see action types below) |
| actor | VARCHAR(100) | No | - | Who performed the action (system, grok-3, grok-3-mini, user email) |
| input_summary | TEXT | Yes | NULL | Summary of input (first 500 chars of CV, questions sent, etc.) |
| output_summary | TEXT | Yes | NULL | Summary of output (score, recommendation, email sent, etc.) |
| approval_status | VARCHAR(20) | Yes | NULL | Approval status if applicable (pending, approved, rejected) |
| approved_by | VARCHAR(200) | Yes | NULL | Email of approver if applicable |
| result | VARCHAR(20) | No | - | Result: success, failure, manual_review |
| created_at | TIMESTAMPTZ | No | NOW() | Action timestamp |

**Action Types**:
- `score_candidate`: CV scoring by Grok
- `generate_questions`: Screening question generation by Grok
- `send_screening_questions`: Screening questions sent via Gmail
- `analyze_reply`: Reply analysis by Grok
- `create_pending_approval`: Pending approval created
- `approve_candidate`: Candidate approved by hiring manager
- `reject_candidate`: Candidate rejected by hiring manager
- `send_interview_invite`: Interview invite sent via Gmail
- `send_rejection_email`: Rejection email sent via Gmail
- `send_daily_digest`: Daily digest sent via Gmail

**Sample Data**:
```sql
INSERT INTO audit_log (candidate_id, action_type, actor, input_summary, output_summary, result) VALUES
(1, 'score_candidate', 'grok-3', 'John Doe | john.doe@example.com | Senior Backend Engineer with 5 years Python...', '{"total_score": 82, "recommendation": "advance"}', 'success'),
(1, 'generate_questions', 'grok-3-mini', 'CV: John Doe, 5 years Python, FastAPI, AWS...', '["Your CV mentions a payment system...", "How did you handle database performance..."]', 'success'),
(1, 'approve_candidate', 'manager@company.com', 'Candidate: John Doe, Score: 88', 'Interview invite sent', 'success');
```

---

## Data Flow

### Flow 1: New Application Processing

```
1. GmailApplicationWatcher receives email
   ↓
2. INSERT INTO candidates (job_id, email, name, cv_text, status='queued', gmail_message_id)
   ↓
3. Push candidate_id to Redis screening_queue
   ↓
4. Orchestrator pops from queue
   ↓
5. Call score_candidate() → Grok API
   ↓
6. UPDATE candidates SET total_score=X, must_haves_met=Y, score_breakdown=Z, status='scored'
   ↓
7. INSERT INTO audit_log (action_type='score_candidate', actor='grok-3', result='success')
   ↓
8. IF must_haves_met = false:
     INSERT INTO pending_approvals (action='reject')
     RETURN
   ↓
9. Call generate_screening_questions() → Grok API
   ↓
10. UPDATE candidates SET screening_questions=Q, status='questions_sent'
    ↓
11. Call gmail_service.send_screening_questions()
    ↓
12. INSERT INTO audit_log (action_type='send_screening_questions', actor='system', result='success')
    ↓
13. UPDATE candidates SET status='awaiting_reply'
```

### Flow 2: Candidate Reply Processing

```
1. ReplyWatcher receives reply email
   ↓
2. Push (candidate_id, reply_text) to Redis reply_queue
   ↓
3. Orchestrator pops from queue
   ↓
4. SELECT * FROM candidates WHERE id=candidate_id
   ↓
5. Call analyze_reply() → Grok API
   ↓
6. UPDATE candidates SET candidate_reply=R, reply_analysis=A, total_score=S, status='replied'
   ↓
7. INSERT INTO audit_log (action_type='analyze_reply', actor='grok-3', result='success')
   ↓
8. INSERT INTO pending_approvals (action='advance', score=S, recommendation=R)
   ↓
9. UPDATE candidates SET status='shortlisted'
```

### Flow 3: Human Approval

```
1. Hiring manager clicks "Approve" in dashboard
   ↓
2. POST /approvals/{id}/approve with {approved_by: "manager@company.com"}
   ↓
3. UPDATE pending_approvals SET status='approved', approved_by='manager@company.com'
   ↓
4. SELECT candidate_id FROM pending_approvals WHERE id=approval_id
   ↓
5. Call gmail_service.send_interview_invite()
   ↓
6. UPDATE candidates SET status='hired'
   ↓
7. INSERT INTO audit_log (action_type='approve_candidate', actor='manager@company.com', result='success')
```

---

## Data Retention Policy

| Table | Retention | Rationale |
|-------|-----------|-----------|
| jobs | Indefinite | Historical job postings |
| candidates | 2 years | GDPR compliance (can be deleted on request) |
| pending_approvals | 2 years | Audit trail |
| audit_log | 2 years minimum | Legal compliance |

**GDPR Compliance**:
- Candidates can request data deletion via email
- Deletion cascades: candidates → pending_approvals
- Audit log retains candidate_id but sets to NULL on deletion
- CV text and personal data removed, but anonymized audit trail remains

---

## Performance Considerations

### Indexes

**Primary Indexes** (automatically created):
- `jobs.id` (PRIMARY KEY)
- `candidates.id` (PRIMARY KEY)
- `pending_approvals.id` (PRIMARY KEY)
- `audit_log.id` (PRIMARY KEY)

**Secondary Indexes** (manually created):
- `candidates.status` - for pipeline board queries
- `candidates.job_id` - for job-specific candidate lists
- `candidates.email` - for duplicate detection
- `candidates.created_at DESC` - for daily digest queries
- `pending_approvals.status` - for pending approval queries
- `pending_approvals.expires_at` - for expiration cleanup
- `audit_log.candidate_id` - for candidate audit trail
- `audit_log.action_type` - for action-specific queries
- `audit_log.created_at DESC` - for recent activity queries

### Query Optimization

**Common Queries**:

**Dashboard: Get all candidates by status**:
```sql
SELECT id, name, email, total_score, recommendation, created_at
FROM candidates
WHERE status = 'shortlisted'
ORDER BY created_at DESC;
```
- Uses index: `idx_candidates_status`
- Expected rows: 10-50
- Expected time: <10ms

**Dashboard: Get pending approvals**:
```sql
SELECT pa.*, c.name, c.email, c.total_score, j.title
FROM pending_approvals pa
JOIN candidates c ON pa.candidate_id = c.id
JOIN jobs j ON pa.job_id = j.id
WHERE pa.status = 'pending'
ORDER BY pa.created_at DESC;
```
- Uses index: `idx_approvals_status`
- Expected rows: 5-20
- Expected time: <20ms

**Daily Digest: Get candidates from past 24 hours**:
```sql
SELECT status, COUNT(*) as count
FROM candidates
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;
```
- Uses index: `idx_candidates_created_at`
- Expected rows: 10-100
- Expected time: <50ms

---

## Data Validation Rules

### Application Level (Pydantic)

```python
from pydantic import BaseModel, EmailStr, Field

class CandidateCreate(BaseModel):
    job_id: int
    email: EmailStr
    name: str | None = None
    cv_text: str | None = None
    gmail_message_id: str | None = None

class CandidateUpdate(BaseModel):
    status: str | None = Field(None, pattern='^(queued|scoring|scored|questions_sent|awaiting_reply|replied|shortlisted|rejected|hired|manual_review)$')
    total_score: float | None = Field(None, ge=0, le=100)
    must_haves_met: bool | None = None
    recommendation: str | None = Field(None, pattern='^(advance|reject|review)$')
    confidence: str | None = Field(None, pattern='^(high|medium|low)$')
```

### Database Level (Constraints)

- Email format validation (application level only)
- Status enum validation (CHECK constraint)
- Score range validation (0-100, application level)
- Foreign key integrity (CASCADE on delete)
- Unique constraints (jobs.slug)

---

## Migration Strategy

### Initial Schema Creation

```sql
-- Run on first deployment
CREATE TABLE jobs (...);
CREATE TABLE candidates (...);
CREATE TABLE pending_approvals (...);
CREATE TABLE audit_log (...);

-- Create all indexes
CREATE INDEX idx_candidates_status ON candidates(status);
-- ... (all other indexes)
```

### Future Migrations

**Example: Add new candidate status**:
```sql
-- Migration: 2026-05-01-add-interview-scheduled-status.sql
ALTER TABLE candidates DROP CONSTRAINT candidates_status_check;
ALTER TABLE candidates ADD CONSTRAINT candidates_status_check
  CHECK (status IN ('queued', 'scoring', 'scored', 'questions_sent',
                    'awaiting_reply', 'replied', 'shortlisted', 'rejected',
                    'hired', 'manual_review', 'interview_scheduled'));
```

**Example: Add candidate phone number**:
```sql
-- Migration: 2026-06-01-add-candidate-phone.sql
ALTER TABLE candidates ADD COLUMN phone VARCHAR(20);
CREATE INDEX idx_candidates_phone ON candidates(phone);
```

---

## Backup and Recovery

### Backup Strategy

**PostgreSQL**:
- Daily full backup at 2:00 AM UTC
- Continuous WAL archiving for point-in-time recovery
- Retention: 30 days

**Redis**:
- RDB snapshots every 6 hours
- AOF (Append-Only File) for durability
- Retention: 7 days

### Recovery Procedures

**Database Corruption**:
1. Stop application
2. Restore from latest backup
3. Replay WAL logs to recover recent transactions
4. Restart application

**Data Loss (Accidental Deletion)**:
1. Identify deletion timestamp from audit_log
2. Restore from backup before deletion
3. Extract deleted records
4. Re-insert into production database

---

## References

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [SQLAlchemy Async ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [GDPR Data Retention Guidelines](https://gdpr.eu/data-retention/)

---

**Next Steps**: Use this data model to implement database models in `backend/db/models.py`

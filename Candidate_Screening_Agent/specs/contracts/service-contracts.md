# Service Contracts

**Feature**: Candidate Screening Agent
**Purpose**: Define contracts for external service integrations
**Last Updated**: 2026-04-27

---

## Grok AI Service Contract

### Base Configuration

**Provider**: xAI (X.AI)
**Base URL**: `https://api.x.ai/v1`
**Authentication**: Bearer token in `Authorization` header
**API Key**: `GROQ_API_KEY` environment variable

### Models

| Model | Use Case | Speed | Cost | Context Window |
|-------|----------|-------|------|----------------|
| grok-3 | CV scoring, reply analysis | Slow | High | 128K tokens |
| grok-3-mini | Question generation, digest | Fast | Low | 128K tokens |

### CV Scoring Contract

**Function**: `score_candidate(cv_text: str, rubric_path: str) -> dict`

**Input**:
```python
{
    "cv_text": "John Doe | john.doe@gmail.com\nSenior Backend Engineer\n...",
    "rubric_path": "rubrics/Senior_Backend_Engineer.md"
}
```

**Prompt Template**:
```
You are an expert technical recruiter. Score this CV objectively based ONLY on the rubric provided.

RUBRIC:
{rubric_content}

CV:
{cv_text}

Return ONLY valid JSON with no markdown, no prose, no explanations.

Required fields:
- total_score (integer 0-100)
- must_haves_met (boolean)
- disqualification_reason (string or null)
- skill_score (integer)
- experience_score (integer)
- project_score (integer)
- communication_score (integer)
- bonuses_applied (array of strings)
- red_flags (array of strings)
- strengths (array of strings)
- weaknesses (array of strings)
- recommendation (string: "advance" | "reject" | "review")
- confidence (string: "high" | "medium" | "low")
- summary (string)
```

**Expected Output**:
```json
{
  "total_score": 82,
  "must_haves_met": true,
  "disqualification_reason": null,
  "skill_score": 35,
  "experience_score": 22,
  "project_score": 16,
  "communication_score": 9,
  "bonuses_applied": ["FastAPI (+5)", "PostgreSQL (+3)", "Kubernetes (+4)"],
  "red_flags": [],
  "strengths": ["Strong Python experience", "Cloud certified", "Real-world projects"],
  "weaknesses": ["No open source contributions"],
  "recommendation": "advance",
  "confidence": "high",
  "summary": "Strong backend engineer with 5 years Python experience. Exceeds most requirements."
}
```

**Error Handling**:
- Timeout (>30s): Retry once, then mark `manual_review`
- Invalid JSON: Retry once with stricter prompt, then raise
- API Error (500): Retry once, then mark `manual_review`
- Rate Limit (429): Exponential backoff, max 3 retries

**SLA**:
- Response time: <30 seconds (p95)
- Success rate: >95%

---

### Question Generation Contract

**Function**: `generate_screening_questions(cv_text: str, rubric_path: str) -> list[str]`

**Input**:
```python
{
    "cv_text": "John Doe | john.doe@gmail.com\nSenior Backend Engineer\n...",
    "rubric_path": "rubrics/Senior_Backend_Engineer.md"
}
```

**Prompt Template**:
```
You are an expert technical recruiter. Generate exactly 5 personalized screening questions for this candidate.

RUBRIC:
{rubric_content}

CV:
{cv_text}

Requirements:
- Reference specific items from the candidate's CV
- Align with rubric requirements
- Ask about technical depth, not just surface knowledge
- Include at least one behavioral question
- Keep questions concise (1-2 sentences each)

Return ONLY a JSON array of 5 strings. No markdown, no prose.
```

**Expected Output**:
```json
[
  "Your CV mentions a payment system — what was the biggest scaling challenge?",
  "How did you handle database performance at 10M requests/day?",
  "Walk me through your CI/CD setup with GitHub Actions.",
  "How do you approach testing in a fast-moving team?",
  "Why are you interested in this specific role?"
]
```

**Error Handling**:
- Same as CV scoring
- Validate exactly 5 questions returned

**SLA**:
- Response time: <15 seconds (p95)
- Success rate: >95%

---

### Reply Analysis Contract

**Function**: `analyze_reply(questions: list[str], reply_text: str, original_score: dict) -> dict`

**Input**:
```python
{
    "questions": ["Question 1", "Question 2", ...],
    "reply_text": "Thank you for the questions. Here are my answers...",
    "original_score": {"total_score": 82, ...}
}
```

**Prompt Template**:
```
You are an expert technical recruiter. Analyze the candidate's replies to screening questions.

ORIGINAL SCORE: {original_score}

QUESTIONS:
{questions}

CANDIDATE REPLY:
{reply_text}

Evaluate:
- Answer quality (depth, clarity, relevance)
- Technical knowledge demonstrated
- Communication skills
- Red flags or concerns

Return ONLY valid JSON with:
- reply_score_delta (integer -20 to +20)
- final_score (integer 0-100)
- answer_quality (string: "high" | "medium" | "low")
- notable_answers (array of strings)
- updated_recommendation (string: "advance" | "reject" | "review")
- brief_summary (string)
```

**Expected Output**:
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

**Error Handling**:
- Same as CV scoring

**SLA**:
- Response time: <30 seconds (p95)
- Success rate: >95%

---

## Gmail API Service Contract

### Base Configuration

**Provider**: Google
**API Version**: v1
**Base URL**: `https://gmail.googleapis.com/gmail/v1`
**Authentication**: OAuth2 with refresh token
**Scopes**: `https://www.googleapis.com/auth/gmail.modify`, `https://www.googleapis.com/auth/gmail.send`

### Environment Variables

```env
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
JOBS_INBOX_EMAIL=jobs@yourdomain.com
HIRING_MANAGER_EMAIL=manager@yourdomain.com
```

### List Unread Emails Contract

**Endpoint**: `GET /users/me/messages`

**Query Parameters**:
```
q=is:unread label:jobs
maxResults=10
```

**Response**:
```json
{
  "messages": [
    {
      "id": "msg_abc123",
      "threadId": "thread_xyz789"
    }
  ],
  "resultSizeEstimate": 1
}
```

**Rate Limits**:
- 250 quota units per user per second
- 1 billion quota units per day

---

### Get Message Contract

**Endpoint**: `GET /users/me/messages/{id}`

**Query Parameters**:
```
format=full
```

**Response**:
```json
{
  "id": "msg_abc123",
  "threadId": "thread_xyz789",
  "labelIds": ["UNREAD", "INBOX"],
  "snippet": "Please find my application attached...",
  "payload": {
    "headers": [
      {"name": "From", "value": "john.doe@example.com"},
      {"name": "Subject", "value": "Application for Senior Backend Engineer"},
      {"name": "Message-ID", "value": "<msg_abc123@mail.gmail.com>"}
    ],
    "parts": [
      {
        "filename": "John_Doe_CV.pdf",
        "mimeType": "application/pdf",
        "body": {
          "attachmentId": "attach_123",
          "size": 245678
        }
      }
    ]
  }
}
```

---

### Get Attachment Contract

**Endpoint**: `GET /users/me/messages/{messageId}/attachments/{attachmentId}`

**Response**:
```json
{
  "size": 245678,
  "data": "base64_encoded_pdf_data..."
}
```

**Processing**:
```python
import base64
pdf_bytes = base64.urlsafe_b64decode(attachment_data)
```

---

### Send Email Contract

**Endpoint**: `POST /users/me/messages/send`

**Request Body**:
```json
{
  "raw": "base64_encoded_email_message"
}
```

**Email Format** (before base64 encoding):
```
From: jobs@yourdomain.com
To: john.doe@example.com
Subject: Screening Questions - Senior Backend Engineer
Content-Type: text/html; charset=utf-8

<html>
<body>
<p>Dear John,</p>
<p>Thank you for applying...</p>
</body>
</html>
```

**Response**:
```json
{
  "id": "msg_sent_123",
  "threadId": "thread_xyz789",
  "labelIds": ["SENT"]
}
```

**DRY_RUN Mode**:
```python
if os.getenv("DRY_RUN", "true").lower() == "true":
    logger.info(f"[DRY_RUN] Email to {to}: {subject}")
    return f"fake_msg_id_{uuid.uuid4().hex[:8]}"
```

---

### Email Templates

**Screening Questions Template**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {{candidate_name}},</p>

    <p>Thank you for applying for the <strong>{{job_title}}</strong> position. We've reviewed your CV and would like to learn more about your experience.</p>

    <p>Please answer the following questions:</p>

    <ol>
        {{#each questions}}
        <li>{{this}}</li>
        {{/each}}
    </ol>

    <p>Please reply to this email with your answers at your earliest convenience.</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>
```

**Interview Invite Template**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {{candidate_name}},</p>

    <p>Congratulations! We're impressed with your application for the <strong>{{job_title}}</strong> position and would like to invite you for an interview.</p>

    <p>Our hiring manager will reach out shortly to schedule a time that works for you.</p>

    <p>We look forward to speaking with you!</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>
```

**Rejection Email Template**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {{candidate_name}},</p>

    <p>Thank you for your interest in the <strong>{{job_title}}</strong> position and for taking the time to apply.</p>

    <p>After careful consideration, we've decided to move forward with other candidates whose experience more closely aligns with our current needs.</p>

    <p>We appreciate your interest in our company and wish you the best in your job search.</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>
```

---

## Redis Service Contract

### Base Configuration

**Provider**: Redis
**Version**: 7+
**Connection**: `redis://localhost:6379`
**Database**: 0 (default)

### Queue Operations

**Push to Queue**:
```python
await redis.lpush("screening_queue", candidate_id)
```

**Pop from Queue** (blocking):
```python
result = await redis.brpop("screening_queue", timeout=1)
if result:
    queue_name, candidate_id = result
```

**Queue Names**:
- `screening_queue`: New candidates ready for scoring
- `reply_queue`: Candidate replies ready for analysis

**Data Format**:
- `screening_queue`: Integer candidate ID
- `reply_queue`: JSON string `{"candidate_id": 1, "reply_text": "..."}`

**Fallback Strategy**:
```python
try:
    await redis.lpush("screening_queue", candidate_id)
except redis.ConnectionError:
    logger.warning("Redis unavailable, using in-memory queue")
    in_memory_queue.append(candidate_id)
```

---

## PostgreSQL Service Contract

### Base Configuration

**Provider**: PostgreSQL
**Version**: 15+
**Connection**: `postgresql+asyncpg://user:password@localhost:5432/screening_db`
**Driver**: asyncpg

### Connection Pooling

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)
```

### Transaction Management

**Auto-commit** (default):
```python
async with AsyncSessionLocal() as session:
    session.add(candidate)
    await session.commit()
```

**Manual transaction**:
```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        session.add(candidate)
        session.add(audit_log)
        # Commits automatically at end of block
```

**Rollback on error**:
```python
async with AsyncSessionLocal() as session:
    try:
        async with session.begin():
            session.add(candidate)
            # Error occurs here
    except Exception:
        # Automatic rollback
        raise
```

---

## PDF Processing Service Contract

### Library

**Provider**: pdfplumber
**Version**: 0.11.0+

### Extract Text Contract

**Function**: `extract_text_from_pdf(pdf_bytes: bytes) -> str`

**Input**: PDF file as bytes

**Output**: Extracted text as string

**Processing**:
```python
import pdfplumber
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        return "Scanned PDF — manual review required"

    return " ".join(text_parts).strip()
```

**Edge Cases**:
- Scanned PDF (no text): Return fallback message
- Password-protected PDF: Raise exception
- Corrupted PDF: Raise exception
- Very large PDF (>100 pages): Process all pages (may be slow)

---

## Service Level Agreements (SLAs)

| Service | Availability | Response Time | Error Rate |
|---------|--------------|---------------|------------|
| Grok API | 99.5% | <30s (p95) | <5% |
| Gmail API | 99.9% | <2s (p95) | <1% |
| Redis | 99.9% | <10ms (p95) | <0.1% |
| PostgreSQL | 99.9% | <100ms (p95) | <0.1% |

---

## Monitoring & Alerting

### Health Checks

**Grok API**:
- Monitor: API response time, error rate
- Alert: If error rate >10% for 5 minutes

**Gmail API**:
- Monitor: API response time, quota usage
- Alert: If quota >80% or error rate >5%

**Redis**:
- Monitor: Connection status, memory usage
- Alert: If connection fails or memory >90%

**PostgreSQL**:
- Monitor: Connection status, query time, connection pool
- Alert: If connection fails or pool exhausted

---

## References

- [Grok API Documentation](https://docs.x.ai/)
- [Gmail API v1 Reference](https://developers.google.com/gmail/api/reference/rest)
- [Redis Commands](https://redis.io/commands/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)

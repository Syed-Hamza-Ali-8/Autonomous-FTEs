# API Contracts

**Feature**: Candidate Screening Agent
**Purpose**: Define all REST API endpoint contracts
**Last Updated**: 2026-04-27

---

## Base URL

**Development**: `http://localhost:8000`
**Production**: `https://your-backend.railway.app`

---

## Health Check

### GET /health

**Description**: Health check endpoint for monitoring.

**Request**: None

**Response**: 200 OK
```json
{
  "status": "ok"
}
```

---

## Candidates Endpoints

### GET /candidates

**Description**: List all candidates with scores and status.

**Request**: None

**Response**: 200 OK
```json
[
  {
    "id": 1,
    "job_id": 1,
    "email": "john.doe@example.com",
    "name": "John Doe",
    "status": "shortlisted",
    "total_score": 82.0,
    "must_haves_met": true,
    "recommendation": "advance",
    "confidence": "high",
    "created_at": "2026-04-27T10:30:00Z",
    "updated_at": "2026-04-27T11:45:00Z"
  }
]
```

**Status Codes**:
- 200: Success
- 500: Internal server error

---

### GET /candidates/{id}

**Description**: Get full candidate detail including scores, questions, and replies.

**Request Parameters**:
- `id` (path, integer, required): Candidate ID

**Response**: 200 OK
```json
{
  "id": 1,
  "job_id": 1,
  "email": "john.doe@example.com",
  "name": "John Doe",
  "cv_text": "Senior Backend Engineer with 5 years Python...",
  "status": "shortlisted",
  "total_score": 82.0,
  "must_haves_met": true,
  "score_breakdown": {
    "skill_score": 35,
    "experience_score": 22,
    "project_score": 16,
    "communication_score": 9,
    "bonuses_applied": ["FastAPI (+5)", "PostgreSQL (+3)"]
  },
  "strengths": [
    "Strong Python experience",
    "Cloud certified"
  ],
  "weaknesses": [
    "No open source contributions"
  ],
  "red_flags": [],
  "recommendation": "advance",
  "confidence": "high",
  "score_summary": "Strong backend engineer with 5 years Python experience.",
  "screening_questions": [
    "Your CV mentions a payment system — what was the biggest scaling challenge?",
    "How did you handle database performance at 10M requests/day?",
    "Walk me through your CI/CD setup with GitHub Actions.",
    "How do you approach testing in a fast-moving team?",
    "Why are you interested in this specific role?"
  ],
  "candidate_reply": "Thank you for the questions. Here are my answers...",
  "reply_analysis": {
    "reply_score_delta": 6,
    "final_score": 88,
    "answer_quality": "high",
    "notable_answers": [
      "Excellent answer on Q1 about scaling"
    ],
    "updated_recommendation": "advance",
    "brief_summary": "Strong answers with depth."
  },
  "gmail_message_id": "msg_abc123",
  "created_at": "2026-04-27T10:30:00Z",
  "updated_at": "2026-04-27T11:45:00Z"
}
```

**Status Codes**:
- 200: Success
- 404: Candidate not found
- 500: Internal server error

---

### GET /candidates/by-status/{status}

**Description**: Filter candidates by pipeline status.

**Request Parameters**:
- `status` (path, string, required): One of: queued, scoring, scored, questions_sent, awaiting_reply, replied, shortlisted, rejected, hired, manual_review

**Response**: 200 OK
```json
[
  {
    "id": 1,
    "job_id": 1,
    "email": "john.doe@example.com",
    "name": "John Doe",
    "status": "shortlisted",
    "total_score": 82.0,
    "recommendation": "advance",
    "created_at": "2026-04-27T10:30:00Z"
  }
]
```

**Status Codes**:
- 200: Success
- 400: Invalid status value
- 500: Internal server error

---

### GET /candidates/{id}/brief

**Description**: Get one-page candidate brief for quick review.

**Request Parameters**:
- `id` (path, integer, required): Candidate ID

**Response**: 200 OK
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "job_title": "Senior Backend Engineer",
  "total_score": 88,
  "recommendation": "advance",
  "confidence": "high",
  "strengths": [
    "Strong Python experience",
    "Cloud certified"
  ],
  "weaknesses": [
    "No open source contributions"
  ],
  "red_flags": [],
  "screening_qa": [
    {
      "question": "Your CV mentions a payment system — what was the biggest scaling challenge?",
      "answer": "The biggest challenge was handling 10M requests/day..."
    }
  ],
  "brief_summary": "Strong backend engineer with excellent technical skills. Recommend interview."
}
```

**Status Codes**:
- 200: Success
- 404: Candidate not found
- 500: Internal server error

---

## Approvals Endpoints

### GET /approvals/pending

**Description**: List all pending approvals requiring human decision.

**Request**: None

**Response**: 200 OK
```json
[
  {
    "id": 1,
    "candidate_id": 1,
    "job_id": 1,
    "action": "advance",
    "score": 88.0,
    "recommendation": "Strong candidate with excellent technical skills",
    "brief_summary": "Scored 88/100. Answered screening questions with depth. Recommend interview.",
    "status": "pending",
    "approved_by": null,
    "created_at": "2026-04-27T11:45:00Z",
    "expires_at": "2026-04-29T11:45:00Z",
    "candidate": {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "total_score": 88.0
    },
    "job": {
      "id": 1,
      "title": "Senior Backend Engineer"
    }
  }
]
```

**Status Codes**:
- 200: Success
- 500: Internal server error

---

### POST /approvals/{id}/approve

**Description**: Approve candidate and send interview invite.

**Request Parameters**:
- `id` (path, integer, required): Approval ID

**Request Body**:
```json
{
  "approved_by": "manager@company.com"
}
```

**Response**: 200 OK
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 1,
  "action": "advance",
  "status": "approved",
  "approved_by": "manager@company.com",
  "created_at": "2026-04-27T11:45:00Z",
  "message": "Interview invite sent to john.doe@example.com"
}
```

**Status Codes**:
- 200: Success
- 404: Approval not found
- 400: Approval already processed or expired
- 500: Internal server error

---

### POST /approvals/{id}/reject

**Description**: Reject candidate and send rejection email.

**Request Parameters**:
- `id` (path, integer, required): Approval ID

**Request Body**:
```json
{
  "approved_by": "manager@company.com",
  "reason": "Missing required Python experience"
}
```

**Response**: 200 OK
```json
{
  "id": 1,
  "candidate_id": 2,
  "job_id": 1,
  "action": "reject",
  "status": "rejected",
  "approved_by": "manager@company.com",
  "created_at": "2026-04-27T11:45:00Z",
  "message": "Rejection email sent to jane.smith@example.com"
}
```

**Status Codes**:
- 200: Success
- 404: Approval not found
- 400: Approval already processed or expired
- 500: Internal server error

---

## Jobs Endpoints

### GET /jobs

**Description**: List all jobs with candidate counts.

**Request**: None

**Response**: 200 OK
```json
[
  {
    "id": 1,
    "title": "Senior Backend Engineer",
    "slug": "senior-backend-engineer",
    "rubric_path": "rubrics/Senior_Backend_Engineer.md",
    "status": "open",
    "created_at": "2026-04-01T00:00:00Z",
    "candidate_counts": {
      "total": 25,
      "queued": 2,
      "scoring": 1,
      "scored": 0,
      "questions_sent": 3,
      "awaiting_reply": 5,
      "replied": 2,
      "shortlisted": 8,
      "rejected": 3,
      "hired": 1
    }
  }
]
```

**Status Codes**:
- 200: Success
- 500: Internal server error

---

### POST /jobs

**Description**: Create a new job posting with rubric.

**Request Body**:
```json
{
  "title": "Senior Backend Engineer",
  "slug": "senior-backend-engineer",
  "rubric_path": "rubrics/Senior_Backend_Engineer.md",
  "status": "open"
}
```

**Response**: 201 Created
```json
{
  "id": 1,
  "title": "Senior Backend Engineer",
  "slug": "senior-backend-engineer",
  "rubric_path": "rubrics/Senior_Backend_Engineer.md",
  "status": "open",
  "created_at": "2026-04-27T12:00:00Z"
}
```

**Status Codes**:
- 201: Created
- 400: Invalid request body or slug already exists
- 500: Internal server error

---

### GET /jobs/{id}

**Description**: Get job detail with candidate counts by status.

**Request Parameters**:
- `id` (path, integer, required): Job ID

**Response**: 200 OK
```json
{
  "id": 1,
  "title": "Senior Backend Engineer",
  "slug": "senior-backend-engineer",
  "rubric_path": "rubrics/Senior_Backend_Engineer.md",
  "status": "open",
  "created_at": "2026-04-01T00:00:00Z",
  "candidate_counts": {
    "total": 25,
    "queued": 2,
    "scoring": 1,
    "scored": 0,
    "questions_sent": 3,
    "awaiting_reply": 5,
    "replied": 2,
    "shortlisted": 8,
    "rejected": 3,
    "hired": 1
  },
  "recent_candidates": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "status": "shortlisted",
      "total_score": 88.0,
      "created_at": "2026-04-27T10:30:00Z"
    }
  ]
}
```

**Status Codes**:
- 200: Success
- 404: Job not found
- 500: Internal server error

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes**:
- 400: Bad Request (invalid input)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error (unexpected error)

---

## CORS Configuration

**Allowed Origins**:
- Development: `http://localhost:3000`
- Production: `https://your-frontend.vercel.app`

**Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

**Allowed Headers**: `*`

---

## Rate Limiting

**Not implemented in MVP**. Future consideration:
- 100 requests per minute per IP
- 1000 requests per hour per IP

---

## Authentication

**Not implemented in MVP**. All endpoints are public. Future consideration:
- JWT-based authentication
- API key authentication for external integrations

---

## Pagination

**Not implemented in MVP**. All list endpoints return full results. Future consideration:
- Query parameters: `?page=1&limit=20`
- Response includes: `total`, `page`, `limit`, `results`

---

## Versioning

**Current Version**: v1 (implicit, no version prefix in URL)

Future versions will use URL prefix: `/v2/candidates`

---

## WebSocket Endpoints

**Not implemented in MVP**. Future consideration:
- `ws://localhost:8000/ws/candidates` - Real-time candidate updates
- `ws://localhost:8000/ws/approvals` - Real-time approval notifications

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Best Practices](https://restfulapi.net/)

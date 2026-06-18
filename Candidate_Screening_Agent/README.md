# Candidate Screening Agent

AI-powered candidate screening system with human-in-the-loop approval, built with Grok AI, FastAPI, and Next.js.

## Features

- **Automated CV Screening**: AI-powered CV analysis using Grok (xAI)
- **Intelligent Scoring**: Multi-criteria evaluation based on customizable rubrics
- **Screening Questions**: Automatically generated follow-up questions
- **Reply Analysis**: AI analysis of candidate responses
- **Human-in-the-Loop**: All final decisions require explicit human approval
- **Daily Digest**: Automated daily summary emails for hiring managers
- **Audit Trail**: Complete logging of all AI decisions and human actions
- **DRY_RUN Mode**: Safe testing without sending real emails

## Architecture

- **Backend**: FastAPI + Python 3.11+ (async-first)
- **AI Brain**: Grok API (xAI) via OpenAI Agents SDK
- **Database**: PostgreSQL 15 with SQLAlchemy async
- **Queue**: Redis 7 for job queuing
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Email**: Gmail API with OAuth2
- **CV Parsing**: pdfplumber for PDF text extraction

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Gmail account with API access
- Grok API key (from xAI)

## Quick Start

### 1. Clone and Setup

```bash
cd Candidate_Screening_Agent
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify containers are running
docker-compose ps
```

### 3. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Edit .env and add your credentials:
# - GROQ_API_KEY (from xAI)
# - Gmail OAuth2 credentials
# - Database connection string
nano .env

# Run database migrations (creates tables)
uv run python -c "import asyncio; from db.database import init_db; asyncio.run(init_db())"

# Start the backend server
uv run uvicorn main:app --reload
```

The backend will be available at http://localhost:8000

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local

# Start the development server
npm run dev
```

The frontend will be available at http://localhost:3000

## Configuration

### Environment Variables

#### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/screening_db

# Redis
REDIS_URL=redis://localhost:6379

# Grok AI (xAI)
GROQ_API_KEY=your_grok_api_key_here

# Gmail API OAuth2
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Safety
DRY_RUN=true  # Set to false in production to send real emails

# Application
PORT=8000
HIRING_MANAGER_EMAIL=manager@company.com
```

#### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop app)
5. Download credentials.json to backend/
6. Run the OAuth flow:

```bash
cd backend
uv run python -c "from services.gmail_service import gmail_service; gmail_service.authenticate()"
```

### Creating a Job Posting

1. Create a rubric file in `rubrics/` (see `rubrics/Senior_Backend_Engineer.md` for example)
2. Use the API or frontend to create a job:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "description": "We are looking for an experienced backend engineer...",
    "rubric_path": "rubrics/Senior_Backend_Engineer.md",
    "hiring_manager_email": "manager@company.com"
  }'
```

## Usage

### Workflow

1. **Candidate Applies**: Send CV as PDF attachment to the monitored Gmail address
2. **AI Screening**: System automatically:
   - Extracts text from PDF
   - Scores candidate against rubric
   - Generates screening questions
   - Sends questions to candidate (if must-haves met)
3. **Candidate Replies**: System analyzes reply and creates pending approval
4. **Human Decision**: Hiring manager reviews in dashboard and approves/rejects
5. **Final Email**: System sends interview invite or rejection email
6. **Daily Digest**: Hiring manager receives daily summary at 8:00 AM

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /api/candidates` - List all candidates
- `GET /api/candidates/{id}` - Get candidate details
- `GET /api/candidates/by-status/{status}` - Filter by status
- `GET /api/approvals/pending` - Get pending approvals
- `POST /api/approvals/{id}/approve` - Approve candidate
- `POST /api/approvals/{id}/reject` - Reject candidate
- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get job details

### Frontend Pages

- `/` - Dashboard with stats and recent activity
- `/approvals` - Pending approvals requiring human decision
- `/candidates` - All candidates with filtering
- `/candidates/{id}` - Detailed candidate profile
- `/jobs` - Job postings and pipelines

## Development

### Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

### Code Quality

The project follows these principles (see `.specify/memory/constitution.md`):

- **Human-in-the-Loop**: AI never sends final decisions without approval
- **Async-First**: All I/O operations use async/await
- **AI-First with Grok**: All reasoning uses Grok API
- **DRY_RUN by Default**: No real emails until explicitly enabled
- **Audit Everything**: Complete logging of all actions
- **Test Coverage**: 75-95% coverage required

### Project Structure

```
Candidate_Screening_Agent/
├── backend/
│   ├── db/                 # Database models and CRUD
│   ├── services/           # PDF, Gmail, Audit services
│   ├── watchers/           # Gmail and reply watchers
│   ├── routers/            # FastAPI routers
│   ├── screening_agent.py  # Grok AI integration
│   ├── orchestrator.py     # Queue consumer
│   ├── daily_digest.py     # Daily summary
│   └── main.py             # FastAPI app
├── frontend/
│   ├── app/                # Next.js pages
│   ├── components/         # React components
│   └── lib/                # API client
├── rubrics/                # Scoring rubrics
├── specs/                  # SpecKit Plus documentation
└── docker-compose.yml      # Infrastructure
```

## Troubleshooting

### Backend won't start

- Check PostgreSQL is running: `docker-compose ps`
- Verify .env file has correct DATABASE_URL
- Check logs: `docker-compose logs postgres`

### Gmail authentication fails

- Ensure credentials.json is in backend/
- Check OAuth2 scopes include Gmail API
- Delete token.json and re-authenticate

### AI scoring fails

- Verify GROQ_API_KEY is set correctly
- Check Grok API quota and rate limits
- Review logs for JSON parsing errors

### No emails being sent

- Check DRY_RUN=true in .env (expected behavior)
- Set DRY_RUN=false for production
- Verify Gmail OAuth2 token is valid

## Production Deployment

### Backend (Railway)

1. Create new Railway project
2. Add PostgreSQL and Redis services
3. Set environment variables
4. Deploy from GitHub
5. Set DRY_RUN=false

### Frontend (Vercel)

1. Import GitHub repository
2. Set NEXT_PUBLIC_API_URL to backend URL
3. Deploy

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.

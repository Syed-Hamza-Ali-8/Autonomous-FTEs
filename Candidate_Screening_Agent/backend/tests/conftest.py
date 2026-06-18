import asyncio
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Ensure backend package root is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("GROQ_MODEL", "test-model")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from db.models import Base

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
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from db.database import get_db
    from routers import approvals_router, candidates_router, jobs_router

    @asynccontextmanager
    async def test_lifespan(app):
        yield

    test_app = FastAPI(lifespan=test_lifespan)
    test_app.include_router(candidates_router, prefix="/api/candidates", tags=["candidates"])
    test_app.include_router(approvals_router, prefix="/api/approvals", tags=["approvals"])
    test_app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])

    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac

    test_app.dependency_overrides.clear()


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
        "summary": "Strong backend engineer with 5 years Python experience. Exceeds most requirements.",
    }


@pytest.fixture
def sample_questions():
    return [
        "Your CV mentions a payment system — what was the biggest scaling challenge?",
        "How did you handle database performance at 10M requests/day?",
        "Walk me through your CI/CD setup with GitHub Actions.",
        "How do you approach testing in a fast-moving team?",
        "Why are you interested in this specific role?",
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
        "summary": "Candidate does not meet the minimum requirements for this role.",
    }

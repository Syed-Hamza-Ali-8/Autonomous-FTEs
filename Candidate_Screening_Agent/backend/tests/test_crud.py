import pytest

from db import crud
from db.models import Job


@pytest.mark.asyncio
async def test_create_candidate(db_session):
    job = Job(title="Backend Engineer", slug="backend-eng", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="john@test.com",
        name="John Doe",
        cv_text="5 years Python",
        gmail_message_id="msg_123",
    )
    assert candidate.id is not None
    assert candidate.email == "john@test.com"
    assert candidate.status == "queued"


@pytest.mark.asyncio
async def test_get_candidate(db_session):
    job = Job(title="Backend Engineer", slug="backend-eng-2", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    created = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="jane@test.com",
        name="Jane Doe",
        cv_text="3 years Go",
        gmail_message_id="msg_456",
    )
    fetched = await crud.get_candidate(db_session, created.id)
    assert fetched.email == "jane@test.com"
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_update_candidate_status(db_session):
    job = Job(title="Frontend Dev", slug="frontend-dev", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="bob@test.com",
        name="Bob",
        cv_text="React dev",
        gmail_message_id="msg_789",
    )
    updated = await crud.update_candidate_status(db_session, candidate.id, "scored")
    assert updated.status == "scored"


@pytest.mark.asyncio
async def test_update_candidate_score(db_session, sample_score):
    job = Job(title="DevOps", slug="devops", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="alice@test.com",
        name="Alice",
        cv_text="AWS expert",
        gmail_message_id="msg_abc",
    )
    updated = await crud.update_candidate_score(db_session, candidate.id, sample_score)
    assert updated.total_score == 82
    assert updated.must_haves_met is True
    assert updated.recommendation == "advance"


@pytest.mark.asyncio
async def test_create_and_get_pending_approval(db_session):
    job = Job(title="SRE", slug="sre", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="sre@test.com",
        name="SRE Candidate",
        cv_text="Kubernetes expert",
        gmail_message_id="msg_sre",
    )
    approval = await crud.create_pending_approval(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        action="advance",
        score=85.0,
        recommendation="Strong candidate",
        brief_summary="Excellent Kubernetes experience",
    )
    assert approval.id is not None
    assert approval.status == "pending"

    pending = await crud.get_pending_approvals(db_session)
    assert len(pending) >= 1
    assert any(p.id == approval.id for p in pending)


@pytest.mark.asyncio
async def test_approve_candidate(db_session):
    job = Job(title="ML Eng", slug="ml-eng", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="ml@test.com",
        name="ML Candidate",
        cv_text="PyTorch expert",
        gmail_message_id="msg_ml",
    )
    approval = await crud.create_pending_approval(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        action="advance",
        score=90.0,
        recommendation="Top candidate",
        brief_summary="Excellent ML background",
    )
    approved = await crud.approve_candidate(db_session, approval.id, "manager@company.com")
    assert approved.status == "approved"
    assert approved.approved_by == "manager@company.com"

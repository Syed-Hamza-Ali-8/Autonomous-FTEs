from unittest.mock import AsyncMock, patch

import pytest

from db import crud
from db.models import Job


@pytest.mark.asyncio
async def test_get_pending_approvals_empty(client):
    response = await client.get("/api/approvals/pending")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_approve_nonexistent_approval(client):
    response = await client.post("/api/approvals/9999/approve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_nonexistent_approval(client):
    response = await client.post("/api/approvals/9999/reject")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_triggers_scheduling(client, db_session):
    job = Job(title="Test Role", slug="test-role", rubric_path="rubrics/test.md", status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="test@test.com",
        name="Test Candidate",
        cv_text="Python dev",
        gmail_message_id="msg_test",
    )
    approval = await crud.create_pending_approval(
        db_session,
        candidate_id=candidate.id,
        job_id=job.id,
        action="advance",
        score=80.0,
        recommendation="Good fit",
        brief_summary="Strong candidate",
    )

    with patch(
        "services.scheduling_agent.scheduling_agent.initiate_scheduling",
        new_callable=AsyncMock,
        return_value="msg_scheduled",
    ):
        response = await client.post(f"/api/approvals/{approval.id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db import crud
from db.models import Job
from orchestrator import process_candidate_reply, process_new_candidate


@pytest.mark.asyncio
async def test_process_new_candidate_full_flow(
    db_session, sample_cv_text, sample_rubric_path, sample_score, sample_questions
):
    job = Job(title="Backend Eng", slug="backend-eng-orch", rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="orch@test.com",
        name="Orch Test",
        cv_text=sample_cv_text,
        gmail_message_id="msg_orch",
    )

    with (
        patch("orchestrator.score_candidate", new_callable=AsyncMock, return_value=sample_score),
        patch("orchestrator.generate_screening_questions", new_callable=AsyncMock, return_value=sample_questions),
        patch("orchestrator.gmail_service.send_screening_questions", return_value="msg_sent"),
        patch("orchestrator.audit_service.log_action", new_callable=AsyncMock),
    ):
        await process_new_candidate(candidate.id, db_session)

    updated = await crud.get_candidate(db_session, candidate.id)
    assert updated.status == "awaiting_reply"
    assert updated.screening_questions is not None


@pytest.mark.asyncio
async def test_process_new_candidate_disqualified(
    db_session, sample_cv_text, sample_rubric_path, disqualified_score
):
    job = Job(title="Backend Eng", slug="backend-eng-disq", rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="disq@test.com",
        name="Disq Candidate",
        cv_text="No experience",
        gmail_message_id="msg_disq",
    )

    with (
        patch("orchestrator.score_candidate", new_callable=AsyncMock, return_value=disqualified_score),
        patch("orchestrator.gmail_service.send_screening_questions") as mock_send,
        patch("orchestrator.audit_service.log_action", new_callable=AsyncMock),
    ):
        await process_new_candidate(candidate.id, db_session)

    mock_send.assert_not_called()

    pending = await crud.get_pending_approvals(db_session)
    rejection = [p for p in pending if p.candidate_id == candidate.id and p.action == "reject"]
    assert len(rejection) == 1


@pytest.mark.asyncio
async def test_process_candidate_reply(
    db_session, sample_cv_text, sample_rubric_path, sample_score, sample_questions
):
    job = Job(title="Backend Eng", slug="backend-eng-reply", rubric_path=sample_rubric_path, status="open")
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    candidate = await crud.create_candidate(
        db_session,
        job_id=job.id,
        email="reply@test.com",
        name="Reply Test",
        cv_text=sample_cv_text,
        gmail_message_id="msg_reply",
    )
    await crud.update_candidate_score(db_session, candidate.id, sample_score)
    await crud.update_candidate_questions(db_session, candidate.id, sample_questions)

    mock_analysis = {
        "reply_score_delta": 5,
        "final_score": 87,
        "answer_quality": "high",
        "notable_answers": ["Excellent answer on scaling"],
        "updated_recommendation": "advance",
        "brief_summary": "Strong candidate with excellent answers.",
    }

    with (
        patch("orchestrator.analyze_reply", new_callable=AsyncMock, return_value=mock_analysis),
        patch("orchestrator.audit_service.log_action", new_callable=AsyncMock),
    ):
        await process_candidate_reply(candidate.id, "My detailed answers here...", db_session)

    pending = await crud.get_pending_approvals(db_session)
    advance = [p for p in pending if p.candidate_id == candidate.id and p.action == "advance"]
    assert len(advance) == 1
    assert advance[0].score == 87

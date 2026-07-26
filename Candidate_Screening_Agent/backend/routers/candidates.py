from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from db.models import SchedulingConversation, InterviewSlot
from auth import get_current_user, TokenPayload
from typing import List, Optional

router = APIRouter()


@router.get("/")
async def get_all_candidates(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
    job_id: Optional[int] = Query(None, description="Filter candidates by job ID"),
):
    """Get all candidates for the current company. Optionally filter by job_id."""
    if job_id is not None:
        candidates = await crud.get_candidates_by_job(db, job_id, company_id=user.company_id)
    else:
        candidates = await crud.get_all_candidates(db, company_id=user.company_id)

    return [
        {
            "id": c.id,
            "job_id": c.job_id,
            "email": c.email,
            "name": c.name,
            "status": c.status,
            "total_score": c.total_score,
            "must_haves_met": c.must_haves_met,
            "recommendation": c.recommendation,
            "confidence": c.confidence,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in candidates
    ]


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Get full candidate detail (current company only)."""
    candidate = await crud.get_candidate(db, candidate_id, company_id=user.company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {
        "id": candidate.id,
        "job_id": candidate.job_id,
        "email": candidate.email,
        "name": candidate.name,
        "cv_text": candidate.cv_text,
        "status": candidate.status,
        "total_score": candidate.total_score,
        "must_haves_met": candidate.must_haves_met,
        "score_breakdown": candidate.score_breakdown,
        "strengths": candidate.strengths,
        "weaknesses": candidate.weaknesses,
        "red_flags": candidate.red_flags,
        "recommendation": candidate.recommendation,
        "confidence": candidate.confidence,
        "score_summary": candidate.score_summary,
        "screening_questions": candidate.screening_questions,
        "candidate_reply": candidate.candidate_reply,
        "reply_analysis": candidate.reply_analysis,
        "gmail_message_id": candidate.gmail_message_id,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
    }


@router.get("/by-status/{status}")
async def get_candidates_by_status(
    status: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Filter candidates by pipeline status (current company only)."""
    valid_statuses = [
        "queued", "scoring", "scored", "questions_sent", "awaiting_reply",
        "replied", "shortlisted", "rejected", "hired", "manual_review"
    ]

    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    candidates = await crud.get_candidates_by_status(db, status, company_id=user.company_id)
    return [
        {
            "id": c.id,
            "job_id": c.job_id,
            "email": c.email,
            "name": c.name,
            "status": c.status,
            "total_score": c.total_score,
            "recommendation": c.recommendation,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in candidates
    ]


@router.get("/{candidate_id}/interview")
async def get_candidate_interview(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Return confirmed interview slot for a candidate (current company only)."""
    candidate = await crud.get_candidate(db, candidate_id, company_id=user.company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    conv = (await db.execute(
        select(SchedulingConversation).where(SchedulingConversation.candidate_id == candidate_id)
    )).scalar_one_or_none()

    if not conv or not conv.confirmed_slot_id:
        return None

    slot = (await db.execute(
        select(InterviewSlot).where(InterviewSlot.id == conv.confirmed_slot_id)
    )).scalar_one_or_none()

    if not slot:
        return None

    return {
        "conversation_state": conv.conversation_state,
        "slot_id": slot.id,
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "timezone": slot.timezone,
        "candidate_timezone": candidate.timezone,
        "status": slot.status,
        "meeting_link": slot.meeting_link,
    }


@router.get("/{candidate_id}/brief")
async def get_candidate_brief(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Get one-page candidate brief for quick review (current company only)."""
    candidate = await crud.get_candidate(db, candidate_id, company_id=user.company_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = await crud.get_job(db, candidate.job_id, company_id=user.company_id)

    screening_qa = []
    if candidate.screening_questions and candidate.candidate_reply:
        for i, question in enumerate(candidate.screening_questions):
            screening_qa.append({
                "question": question,
                "answer": f"See full reply for answer {i+1}",
            })

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "job_title": job.title if job else "Unknown",
        "total_score": candidate.total_score,
        "recommendation": candidate.recommendation,
        "confidence": candidate.confidence,
        "strengths": candidate.strengths or [],
        "weaknesses": candidate.weaknesses or [],
        "red_flags": candidate.red_flags or [],
        "screening_qa": screening_qa,
        "brief_summary": candidate.score_summary or "No summary available",
    }

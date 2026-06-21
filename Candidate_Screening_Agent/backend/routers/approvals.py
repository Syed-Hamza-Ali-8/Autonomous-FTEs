from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from auth import get_current_user, TokenPayload
from services.gmail_service import gmail_service
from services import audit_service
from typing import List

router = APIRouter()


@router.get("/pending")
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Get all pending approvals for the current company."""
    approvals = await crud.get_pending_approvals(db, company_id=user.company_id)

    result = []
    for approval in approvals:
        candidate = await crud.get_candidate(db, approval.candidate_id, company_id=user.company_id)
        job = await crud.get_job(db, approval.job_id, company_id=user.company_id)

        result.append({
            "id": approval.id,
            "candidate_id": approval.candidate_id,
            "candidate_name": candidate.name if candidate else "Unknown",
            "candidate_email": candidate.email if candidate else "Unknown",
            "job_id": approval.job_id,
            "job_title": job.title if job else "Unknown",
            "action": approval.action,
            "score": approval.score,
            "recommendation": approval.recommendation,
            "brief_summary": approval.brief_summary,
            "created_at": approval.created_at.isoformat() if approval.created_at else None,
        })

    return result


@router.post("/{approval_id}/approve")
async def approve_candidate(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Approve a candidate and initiate intelligent interview scheduling."""
    approval = await crud.get_approval(db, approval_id, company_id=user.company_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    candidate = await crud.get_candidate(db, approval.candidate_id, company_id=user.company_id)
    job = await crud.get_job(db, approval.job_id, company_id=user.company_id)

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    await crud.approve_candidate(db, approval_id, user.email)

    try:
        from services.scheduling_agent import scheduling_agent

        message_id = await scheduling_agent.initiate_scheduling(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id,
        )

        success_message = f"Approved and initiated scheduling conversation with {candidate.email}"

    except Exception as e:
        await audit_service.log_action(
            db=db,
            action_type="initiate_scheduling",
            actor=user.email,
            result="failure",
            candidate_id=candidate.id,
            company_id=user.company_id,
            output_summary=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Approval succeeded but scheduling failed: {e}")

    await audit_service.log_action(
        db=db,
        action_type="approve_candidate",
        actor=user.email,
        result="success",
        candidate_id=candidate.id,
        company_id=user.company_id,
        output_summary=success_message,
    )

    return {
        "status": "approved",
        "candidate_id": candidate.id,
        "message": success_message,
    }


@router.post("/{approval_id}/reject")
async def reject_candidate(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Reject a candidate and send rejection email."""
    approval = await crud.get_approval(db, approval_id, company_id=user.company_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    candidate = await crud.get_candidate(db, approval.candidate_id, company_id=user.company_id)
    job = await crud.get_job(db, approval.job_id, company_id=user.company_id)

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    await crud.reject_candidate(db, approval_id, user.email)

    try:
        message_id = gmail_service.send_rejection_email(
            to=candidate.email,
            candidate_name=candidate.name or candidate.email,
            job_title=job.title,
        )

        candidate.rejection_message_id = message_id
        await db.commit()

    except Exception as e:
        await audit_service.log_action(
            db=db,
            action_type="send_rejection_email",
            actor=user.email,
            result="failure",
            candidate_id=candidate.id,
            company_id=user.company_id,
            output_summary=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Rejection succeeded but email failed: {e}")

    await audit_service.log_action(
        db=db,
        action_type="reject_candidate",
        actor=user.email,
        result="success",
        candidate_id=candidate.id,
        company_id=user.company_id,
        output_summary=f"Rejected and sent rejection email to {candidate.email}",
    )

    return {
        "status": "rejected",
        "candidate_id": candidate.id,
        "message": f"Candidate rejected and rejection email sent to {candidate.email}",
    }

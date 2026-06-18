from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from services.gmail_service import gmail_service
from services import audit_service
from typing import List

router = APIRouter()


@router.get("/pending")
async def get_pending_approvals(db: AsyncSession = Depends(get_db)):
    """Get all pending approvals with candidate details."""
    approvals = await crud.get_pending_approvals(db)

    result = []
    for approval in approvals:
        candidate = await crud.get_candidate(db, approval.candidate_id)
        job = await crud.get_job(db, approval.job_id)

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
async def approve_candidate(approval_id: int, db: AsyncSession = Depends(get_db)):
    """Approve a candidate and initiate intelligent interview scheduling."""
    # Get approval
    approval = await crud.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Get candidate and job
    candidate = await crud.get_candidate(db, approval.candidate_id)
    job = await crud.get_job(db, approval.job_id)

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    # Approve candidate
    await crud.approve_candidate(db, approval_id, "hiring_manager")

    # Initiate intelligent scheduling conversation
    try:
        from services.scheduling_agent import scheduling_agent

        message_id = await scheduling_agent.initiate_scheduling(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id
        )

        success_message = f"Approved and initiated scheduling conversation with {candidate.email}"

    except Exception as e:
        # Log error but don't fail the approval
        await audit_service.log_action(
            db=db,
            action_type="initiate_scheduling",
            actor="hiring_manager",
            result="failure",
            candidate_id=candidate.id,
            output_summary=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Approval succeeded but scheduling failed: {e}")

    # Log to audit
    await audit_service.log_action(
        db=db,
        action_type="approve_candidate",
        actor="hiring_manager",
        result="success",
        candidate_id=candidate.id,
        output_summary=success_message
    )

    return {
        "status": "approved",
        "candidate_id": candidate.id,
        "message": success_message
    }


@router.post("/{approval_id}/reject")
async def reject_candidate(approval_id: int, db: AsyncSession = Depends(get_db)):
    """Reject a candidate and send rejection email."""
    # Get approval
    approval = await crud.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Get candidate and job
    candidate = await crud.get_candidate(db, approval.candidate_id)
    job = await crud.get_job(db, approval.job_id)

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    # Reject candidate
    await crud.reject_candidate(db, approval_id, "hiring_manager")

    # Send rejection email
    try:
        message_id = gmail_service.send_rejection_email(
            to=candidate.email,
            candidate_name=candidate.name or candidate.email,
            job_title=job.title
        )

        # Store rejection message ID for tracking replies
        candidate.rejection_message_id = message_id
        await db.commit()

    except Exception as e:
        # Log error but don't fail the rejection
        await audit_service.log_action(
            db=db,
            action_type="send_rejection_email",
            actor="hiring_manager",
            result="failure",
            candidate_id=candidate.id,
            output_summary=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Rejection succeeded but email failed: {e}")

    # Log to audit
    await audit_service.log_action(
        db=db,
        action_type="reject_candidate",
        actor="hiring_manager",
        result="success",
        candidate_id=candidate.id,
        output_summary=f"Rejected and sent rejection email to {candidate.email}"
    )

    return {
        "status": "rejected",
        "candidate_id": candidate.id,
        "message": f"Candidate rejected and rejection email sent to {candidate.email}"
    }

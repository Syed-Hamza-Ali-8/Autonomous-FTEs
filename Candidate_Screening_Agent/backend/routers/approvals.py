from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from auth import get_current_user, TokenPayload
from services.gmail_service import gmail_service
from services import audit_service
from typing import List
from datetime import datetime

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
    """Approve a candidate and send interview invitation with screening questions."""
    approval = await crud.get_approval(db, approval_id, company_id=user.company_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    candidate = await crud.get_candidate(db, approval.candidate_id, company_id=user.company_id)
    job = await crud.get_job(db, approval.job_id, company_id=user.company_id)

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    await crud.approve_candidate(db, approval_id, user.email)

    try:
        # Interview invitation is sent WITHOUT screening questions.
        from services.scheduling_agent import scheduling_agent

        # Create scheduling conversation
        from services.calendar_service import calendar_service
        available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)
        if not available_slots:
            available_slots = await scheduling_agent._create_default_slots(db, job.id, company_id=user.company_id)

        slot_ids = [slot.id for slot in available_slots]
        proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

        from db.models import SchedulingConversation
        conversation = SchedulingConversation(
            candidate_id=candidate.id,
            job_id=job.id,
            company_id=user.company_id,
            conversation_state="awaiting_questions_reply",
            proposed_slots=slot_ids,
            conversation_history=[]
        )
        db.add(conversation)

        # Format slots for email
        formatted_slots = []
        for i, slot in enumerate(available_slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

        # Generate interview invitation email (time slots only, no screening questions)
        email_body = await scheduling_agent._generate_approval_email_no_questions(
            candidate_name=candidate.name or candidate.email,
            job_title=job.title,
            slots_text="\n".join(formatted_slots)
        )

        # Send email and get Gmail's actual Message-ID
        gmail_message_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=email_body
        )

        # Save GMAIL's actual Message-ID to conversation for threading
        conversation.conversation_history.append({
            "role": "assistant",
            "content": email_body,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": gmail_message_id
        })
        conversation.last_message_id = gmail_message_id

        candidate.gmail_message_id = gmail_message_id
        await db.commit()

        success_message = f"Approved! Interview invitation sent to {candidate.email}"

    except Exception as e:
        await audit_service.log_action(
            db=db,
            action_type="approve_candidate",
            actor=user.email,
            result="failure",
            candidate_id=candidate.id,
            company_id=user.company_id,
            output_summary=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Approval failed: {e}")

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

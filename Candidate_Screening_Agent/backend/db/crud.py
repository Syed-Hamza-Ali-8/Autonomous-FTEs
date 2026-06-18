from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Job, Candidate, PendingApproval, AuditLog
from datetime import datetime


# ============================================================================
# Candidate CRUD Operations
# ============================================================================

async def create_candidate(
    db: AsyncSession,
    job_id: int,
    email: str,
    name: str,
    cv_text: str,
    gmail_message_id: str
) -> Candidate:
    """Create a new candidate record."""
    candidate = Candidate(
        job_id=job_id,
        email=email,
        name=name,
        cv_text=cv_text,
        gmail_message_id=gmail_message_id,
        status="queued"
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def get_candidate(db: AsyncSession, candidate_id: int) -> Candidate | None:
    """Get candidate by ID."""
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    return result.scalar_one_or_none()


async def update_candidate_status(
    db: AsyncSession,
    candidate_id: int,
    status: str
) -> Candidate:
    """Update candidate status."""
    candidate = await get_candidate(db, candidate_id)
    if candidate:
        candidate.status = status
        candidate.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(candidate)
    return candidate


async def update_candidate_score(
    db: AsyncSession,
    candidate_id: int,
    score_data: dict
) -> Candidate:
    """Update candidate score and related fields."""
    candidate = await get_candidate(db, candidate_id)
    if candidate:
        candidate.total_score = score_data.get("total_score")
        candidate.must_haves_met = score_data.get("must_haves_met")
        candidate.score_breakdown = score_data.get("score_breakdown")
        candidate.strengths = score_data.get("strengths")
        candidate.weaknesses = score_data.get("weaknesses")
        candidate.red_flags = score_data.get("red_flags")
        candidate.recommendation = score_data.get("recommendation")
        candidate.confidence = score_data.get("confidence")
        candidate.score_summary = score_data.get("summary")
        candidate.status = "scored"
        candidate.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(candidate)
    return candidate


async def update_candidate_questions(
    db: AsyncSession,
    candidate_id: int,
    questions: list
) -> Candidate:
    """Update candidate screening questions."""
    candidate = await get_candidate(db, candidate_id)
    if candidate:
        candidate.screening_questions = questions
        candidate.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(candidate)
    return candidate


async def update_candidate_reply(
    db: AsyncSession,
    candidate_id: int,
    reply_text: str,
    analysis: dict
) -> Candidate:
    """Update candidate reply and analysis."""
    candidate = await get_candidate(db, candidate_id)
    if candidate:
        candidate.candidate_reply = reply_text
        candidate.reply_analysis = analysis
        candidate.total_score = analysis.get("final_score", candidate.total_score)
        candidate.recommendation = analysis.get("updated_recommendation", candidate.recommendation)
        candidate.status = "replied"
        candidate.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(candidate)
    return candidate


async def get_candidates_by_status(db: AsyncSession, status: str) -> list[Candidate]:
    """Get all candidates with a specific status."""
    result = await db.execute(
        select(Candidate).where(Candidate.status == status).order_by(Candidate.created_at.desc())
    )
    return result.scalars().all()


async def get_all_candidates(db: AsyncSession) -> list[Candidate]:
    """Get all candidates."""
    result = await db.execute(
        select(Candidate).order_by(Candidate.created_at.desc())
    )
    return result.scalars().all()


async def get_candidates_by_job(db: AsyncSession, job_id: int) -> list[Candidate]:
    """Get all candidates for a specific job."""
    result = await db.execute(
        select(Candidate).where(Candidate.job_id == job_id).order_by(Candidate.created_at.desc())
    )
    return result.scalars().all()


# ============================================================================
# Pending Approval CRUD Operations
# ============================================================================

async def create_pending_approval(
    db: AsyncSession,
    candidate_id: int,
    job_id: int,
    action: str,
    score: float,
    recommendation: str,
    brief_summary: str
) -> PendingApproval:
    """Create a new pending approval record."""
    approval = PendingApproval(
        candidate_id=candidate_id,
        job_id=job_id,
        action=action,
        score=score,
        recommendation=recommendation,
        brief_summary=brief_summary,
        status="pending"
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


async def get_pending_approvals(db: AsyncSession) -> list[PendingApproval]:
    """Get all pending approvals."""
    result = await db.execute(
        select(PendingApproval)
        .where(PendingApproval.status == "pending")
        .order_by(PendingApproval.created_at.desc())
    )
    return result.scalars().all()


async def get_approval(db: AsyncSession, approval_id: int) -> PendingApproval | None:
    """Get approval by ID."""
    result = await db.execute(
        select(PendingApproval).where(PendingApproval.id == approval_id)
    )
    return result.scalar_one_or_none()


async def approve_candidate(
    db: AsyncSession,
    approval_id: int,
    approved_by: str
) -> PendingApproval:
    """Approve a candidate."""
    approval = await get_approval(db, approval_id)
    if approval:
        approval.status = "approved"
        approval.approved_by = approved_by
        await db.commit()
        await db.refresh(approval)
    return approval


async def reject_candidate(
    db: AsyncSession,
    approval_id: int,
    approved_by: str
) -> PendingApproval:
    """Reject a candidate."""
    approval = await get_approval(db, approval_id)
    if approval:
        approval.status = "rejected"
        approval.approved_by = approved_by

        # Also update the candidate status to rejected
        candidate = await get_candidate(db, approval.candidate_id)
        if candidate:
            candidate.status = "rejected"
            candidate.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(approval)
    return approval


# ============================================================================
# Job CRUD Operations
# ============================================================================

async def create_job(
    db: AsyncSession,
    title: str,
    description: str,
    rubric_path: str,
    hiring_manager_email: str = None,
    status: str = "open"
) -> Job:
    """Create a new job posting."""
    # Generate slug from title
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    # Ensure slug is unique
    counter = 1
    original_slug = slug
    while True:
        result = await db.execute(select(Job).where(Job.slug == slug))
        if result.scalar_one_or_none() is None:
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    job = Job(
        title=title,
        description=description,
        slug=slug,
        rubric_path=rubric_path,
        hiring_manager_email=hiring_manager_email,
        status=status
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: int) -> Job | None:
    """Get job by ID."""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    return result.scalar_one_or_none()


async def get_all_jobs(db: AsyncSession) -> list[Job]:
    """Get all jobs."""
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc())
    )
    return result.scalars().all()


# ============================================================================
# Audit Log CRUD Operations
# ============================================================================

async def create_audit_log(
    db: AsyncSession,
    action_type: str,
    actor: str,
    result: str,
    candidate_id: int | None = None,
    input_summary: str | None = None,
    output_summary: str | None = None,
    approval_status: str | None = None,
    approved_by: str | None = None
) -> AuditLog:
    """Create an audit log entry."""
    audit_log = AuditLog(
        candidate_id=candidate_id,
        action_type=action_type,
        actor=actor,
        input_summary=input_summary,
        output_summary=output_summary,
        approval_status=approval_status,
        approved_by=approved_by,
        result=result
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    return audit_log


async def get_audit_logs_by_candidate(
    db: AsyncSession,
    candidate_id: int
) -> list[AuditLog]:
    """Get all audit logs for a specific candidate."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.candidate_id == candidate_id)
        .order_by(AuditLog.created_at.desc())
    )
    return result.scalars().all()

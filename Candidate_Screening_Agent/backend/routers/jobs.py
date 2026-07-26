from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from auth import get_current_user, TokenPayload
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class JobCreate(BaseModel):
    title: str
    description: str
    rubric_path: str
    hiring_manager_email: Optional[str] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rubric_path: Optional[str] = None
    hiring_manager_email: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: str


@router.get("/")
async def get_all_jobs(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Get all jobs for the current company (authenticated)."""
    jobs = await crud.get_all_jobs(db, company_id=user.company_id)

    result = []
    for job in jobs:
        candidates = await crud.get_candidates_by_job(db, job.id, company_id=user.company_id)
        result.append({
            "id": job.id, "title": job.title, "slug": job.slug,
            "description": job.description, "rubric_path": job.rubric_path,
            "hiring_manager_email": job.hiring_manager_email,
            "status": job.status, "created_at": job.created_at.isoformat(),
            "candidate_count": len(candidates),
        })
    return result


@router.get("/public")
async def get_public_jobs(db: AsyncSession = Depends(get_db)):
    """Get all open and paused jobs (no auth required - for candidate-facing frontend).
    Closed jobs are fully hidden. Paused jobs are visible but applications are disabled."""
    from sqlalchemy import select
    from db.models import Job, Candidate, Company
    result_db = await db.execute(
        select(Job, Company.name.label('company_name'))
        .join(Company, Job.company_id == Company.id)
        .where(Job.status.in_(['open', 'paused']))
        .order_by(Job.created_at.desc())
    )
    jobs_with_company = result_db.all()
    result = []
    for job, company_name in jobs_with_company:
        candidates_result = await db.execute(select(Candidate).where(Candidate.job_id == job.id))
        candidates = candidates_result.scalars().all()
        result.append({
            "id": job.id, "title": job.title, "slug": job.slug,
            "description": job.description, "rubric_path": job.rubric_path,
            "hiring_manager_email": job.hiring_manager_email,
            "status": job.status, "created_at": job.created_at.isoformat(),
            "candidate_count": len(candidates), "company_name": company_name,
        })
    return result


@router.post("/")
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Create a new job posting for the current company."""
    try:
        job = await crud.create_job(
            db=db,
            title=job_data.title,
            description=job_data.description,
            rubric_path=job_data.rubric_path,
            hiring_manager_email=job_data.hiring_manager_email,
            company_id=user.company_id,
        )

        return {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "rubric_path": job.rubric_path,
            "hiring_manager_email": job.hiring_manager_email,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {e}")


@router.put("/{job_id}")
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Update job details (title, description, rubric, hiring manager)."""
    job = await crud.update_job(
        db=db,
        job_id=job_id,
        company_id=user.company_id,
        title=job_data.title,
        description=job_data.description,
        rubric_path=job_data.rubric_path,
        hiring_manager_email=job_data.hiring_manager_email,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id, "title": job.title, "slug": job.slug,
        "description": job.description, "rubric_path": job.rubric_path,
        "hiring_manager_email": job.hiring_manager_email,
        "status": job.status, "created_at": job.created_at.isoformat(),
    }


@router.patch("/{job_id}/status")
async def update_job_status(
    job_id: int,
    status_data: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Change job status (open/closed/paused)."""
    if status_data.status not in ("open", "closed", "paused"):
        raise HTTPException(status_code=400, detail="Status must be one of: open, closed, paused")
    job = await crud.update_job_status(
        db=db,
        job_id=job_id,
        company_id=user.company_id,
        status=status_data.status,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id, "title": job.title, "status": job.status,
    }


@router.get("/public/{job_id}")
async def get_public_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get public job details (no auth required)."""
    from sqlalchemy import select
    from db.models import Job, Company
    result = await db.execute(
        select(Job, Company.name.label('company_name'))
        .join(Company, Job.company_id == Company.id)
        .where(Job.id == job_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    job, company_name = row
    return {
        "id": job.id, "title": job.title, "slug": job.slug,
        "description": job.description, "rubric_path": job.rubric_path,
        "hiring_manager_email": job.hiring_manager_email,
        "status": job.status, "created_at": job.created_at.isoformat(),
        "company_name": company_name,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """Get job details with full candidate list (current company only)."""
    job = await crud.get_job(db, job_id, company_id=user.company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = await crud.get_candidates_by_job(db, job_id, company_id=user.company_id)

    candidate_summaries = []
    for c in candidates:
        candidate_summaries.append({
            "id": c.id,
            "email": c.email,
            "name": c.name,
            "status": c.status,
            "total_score": c.total_score,
            "recommendation": c.recommendation,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "rubric_path": job.rubric_path,
        "hiring_manager_email": job.hiring_manager_email,
        "status": job.status,
        "candidates": candidate_summaries,
        "total_candidates": len(candidates),
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }

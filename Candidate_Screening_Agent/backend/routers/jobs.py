from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class JobCreate(BaseModel):
    """Request model for creating a new job."""
    title: str
    description: str
    rubric_path: str
    hiring_manager_email: Optional[str] = None


@router.get("/")
async def get_all_jobs(db: AsyncSession = Depends(get_db)):
    """Get all jobs with candidate counts."""
    jobs = await crud.get_all_jobs(db)

    result = []
    for job in jobs:
        # Get candidate counts by status
        candidates = await crud.get_candidates_by_job(db, job.id)

        status_counts = {}
        for candidate in candidates:
            status = candidate.status
            status_counts[status] = status_counts.get(status, 0) + 1

        result.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "rubric_path": job.rubric_path,
            "hiring_manager_email": job.hiring_manager_email,
            "total_candidates": len(candidates),
            "status_counts": status_counts,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        })

    return result


@router.post("/")
async def create_job(job_data: JobCreate, db: AsyncSession = Depends(get_db)):
    """Create a new job posting."""
    try:
        job = await crud.create_job(
            db=db,
            title=job_data.title,
            description=job_data.description,
            rubric_path=job_data.rubric_path,
            hiring_manager_email=job_data.hiring_manager_email
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


@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get job details with full candidate list."""
    job = await crud.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get all candidates for this job
    candidates = await crud.get_candidates_by_job(db, job_id)

    # Build candidate summaries
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
        "candidates": candidate_summaries,
        "total_candidates": len(candidates),
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }

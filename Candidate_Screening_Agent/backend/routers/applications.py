from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud
from services.pdf_service import extract_text_from_pdf
from services import audit_service
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.post("/submit")
async def submit_application(
    name: str = Form(...),
    email: str = Form(...),
    job_id: int = Form(...),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle candidate application submission.

    Accepts:
    - name: Candidate's full name
    - email: Candidate's email address
    - job_id: ID of the job being applied to
    - resume: PDF file of candidate's resume

    Returns:
    - candidate_id: ID of created candidate
    - status: Current status (queued)
    - message: Success message
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Application submission: name={name}, email={email}, job_id={job_id}, resume={resume.filename}")
    except Exception as e:
        logger.error(f"Error logging submission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    # Validate job exists
    try:
        logger.info(f"Validating job {job_id} exists...")
        job = await crud.get_job(db, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")
        logger.info(f"Job {job_id} found: {job.title}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating job: {str(e)}")

    # Validate file is PDF
    logger.info(f"Validating PDF file: {resume.filename}")
    if not resume.filename.endswith('.pdf'):
        logger.error(f"Invalid file type: {resume.filename}")
        raise HTTPException(status_code=400, detail="Resume must be a PDF file")

    # Check file size (max 10MB)
    logger.info("Reading resume file...")
    resume_bytes = await resume.read()
    logger.info(f"Resume file size: {len(resume_bytes)} bytes")
    if len(resume_bytes) > 10 * 1024 * 1024:
        logger.error(f"Resume file too large: {len(resume_bytes)} bytes")
        raise HTTPException(status_code=400, detail="Resume file too large (max 10MB)")

    # Extract text from PDF
    try:
        logger.info("Extracting text from PDF...")
        cv_text = extract_text_from_pdf(resume_bytes)
        logger.info(f"Extracted {len(cv_text)} characters from PDF")

        if not cv_text or len(cv_text.strip()) < 100:
            logger.error(f"Insufficient text extracted: {len(cv_text.strip()) if cv_text else 0} characters")
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. Please ensure your resume contains readable text."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process PDF: {str(e)}"
        )

    # Check for duplicate application (same email + job)
    # Block ALL duplicate applications regardless of status
    logger.info(f"Checking for duplicate applications for {email} on job {job_id}...")
    existing_candidates = await crud.get_candidates_by_job(db, job_id)
    logger.info(f"Found {len(existing_candidates)} existing candidates for job {job_id}")
    for candidate in existing_candidates:
        if candidate.email.lower() == email.lower():
            logger.error(f"Duplicate application detected: {email} already applied for job {job_id} with status {candidate.status}")
            raise HTTPException(
                status_code=400,
                detail="You have already applied for this position. Multiple applications for the same job are not allowed."
            )
    logger.info("No duplicate application found, proceeding with candidate creation...")

    # Create candidate record
    try:
        candidate = await crud.create_candidate(
            db=db,
            job_id=job_id,
            email=email,
            name=name,
            cv_text=cv_text,
            gmail_message_id=f"web_upload_{job_id}_{email}"
        )

        # Log to audit
        await audit_service.log_action(
            db=db,
            action_type="application_submitted",
            actor="candidate",
            result="success",
            candidate_id=candidate.id,
            input_summary=f"Web application from {email} for job {job_id}",
            output_summary=f"Created candidate {candidate.id}, extracted {len(cv_text)} chars from CV"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create candidate record: {str(e)}"
        )

    # Push to Redis screening queue
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = await redis.from_url(redis_url)
        await redis_client.lpush("screening_queue", str(candidate.id))
        await redis_client.close()

        # Log queue push
        await audit_service.log_action(
            db=db,
            action_type="queue_candidate",
            actor="system",
            result="success",
            candidate_id=candidate.id,
            output_summary=f"Pushed candidate {candidate.id} to screening queue"
        )

    except Exception as e:
        # Don't fail the request if queue push fails
        # The candidate is still created and can be processed manually
        await audit_service.log_action(
            db=db,
            action_type="queue_candidate",
            actor="system",
            result="failure",
            candidate_id=candidate.id,
            output_summary=f"Failed to push to queue: {str(e)}"
        )

    return {
        "candidate_id": candidate.id,
        "status": candidate.status,
        "message": f"Application submitted successfully! You'll receive screening questions at {email} if your profile matches our requirements."
    }


@router.get("/status/{candidate_id}")
async def get_application_status(
    candidate_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Allow candidates to check their application status.

    Requires candidate_id and email for verification.
    """
    candidate = await crud.get_candidate(db, candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify email matches (security check)
    if candidate.email.lower() != email.lower():
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Get job details
    job = await crud.get_job(db, candidate.job_id)

    # Map internal status to user-friendly message
    status_messages = {
        "queued": "Your application is in the queue for review",
        "scoring": "Our AI is currently reviewing your resume",
        "scored": "Your resume has been reviewed",
        "questions_sent": "Screening questions have been sent to your email",
        "awaiting_reply": "Waiting for your response to screening questions",
        "replied": "We've received your responses and are reviewing them",
        "shortlisted": "Your application is under review by our hiring team",
        "rejected": "Thank you for your interest. Unfortunately, we've decided to move forward with other candidates",
        "hired": "Congratulations! You've been selected for this position",
        "manual_review": "Your application requires additional review"
    }

    return {
        "candidate_id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "job_title": job.title if job else "Unknown",
        "status": candidate.status,
        "status_message": status_messages.get(candidate.status, "Application in progress"),
        "total_score": candidate.total_score,
        "submitted_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "last_updated": candidate.updated_at.isoformat() if candidate.updated_at else None
    }

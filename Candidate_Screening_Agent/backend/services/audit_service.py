import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db import crud

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    action_type: str,
    actor: str,
    result: str,
    candidate_id: int | None = None,
    input_summary: str | None = None,
    output_summary: str | None = None,
    approval_status: str | None = None,
    approved_by: str | None = None
) -> None:
    """
    Log an action to the audit log.

    This function wraps crud.create_audit_log and catches any errors
    to ensure audit failures never crash the main pipeline.

    Args:
        db: Database session
        action_type: Type of action (e.g., "score_candidate", "approve_candidate")
        actor: Who performed the action (e.g., "grok-3", "manager@company.com")
        result: Result of the action ("success", "failure", "manual_review")
        candidate_id: Optional candidate ID
        input_summary: Optional summary of input (first 500 chars)
        output_summary: Optional summary of output
        approval_status: Optional approval status
        approved_by: Optional approver email
    """
    try:
        await crud.create_audit_log(
            db=db,
            action_type=action_type,
            actor=actor,
            result=result,
            candidate_id=candidate_id,
            input_summary=input_summary,
            output_summary=output_summary,
            approval_status=approval_status,
            approved_by=approved_by
        )
        logger.debug(f"Audit log created: {action_type} by {actor} -> {result}")
    except Exception as e:
        # Log error but never raise - audit failures should not crash the pipeline
        logger.error(f"Failed to create audit log: {e}")
        logger.error(f"Action: {action_type}, Actor: {actor}, Result: {result}")

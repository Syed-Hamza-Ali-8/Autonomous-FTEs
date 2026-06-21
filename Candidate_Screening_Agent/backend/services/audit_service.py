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
    company_id: int | None = None,
    input_summary: str | None = None,
    output_summary: str | None = None,
    approval_status: str | None = None,
    approved_by: str | None = None,
) -> None:
    try:
        await crud.create_audit_log(
            db=db,
            action_type=action_type,
            actor=actor,
            result=result,
            candidate_id=candidate_id,
            company_id=company_id,
            input_summary=input_summary,
            output_summary=output_summary,
            approval_status=approval_status,
            approved_by=approved_by,
        )
        logger.debug(f"Audit log created: {action_type} by {actor} -> {result}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        logger.error(f"Action: {action_type}, Actor: {actor}, Result: {result}")

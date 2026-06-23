import asyncio
import json
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import AsyncSessionLocal
from db import crud
from screening_agent import score_candidate, generate_screening_questions, analyze_reply
from services.gmail_service import gmail_service
from services import audit_service
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def process_new_candidate(candidate_id: int, db: AsyncSession):
    """
    Process a new candidate: score CV, generate questions, send email.

    Args:
        candidate_id: ID of candidate to process
        db: Database session
    """
    try:
        # 1. Fetch candidate
        candidate = await crud.get_candidate(db, candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return

        logger.info(f"Processing candidate {candidate_id}: {candidate.email}")

        # Update status to scoring
        await crud.update_candidate_status(db, candidate_id, "scoring")

        # 2. Get job and rubric path
        job = await crud.get_job(db, candidate.job_id)
        if not job:
            logger.error(f"Job {candidate.job_id} not found")
            return

        rubric_path = job.rubric_path

        # 3. Score candidate with Grok
        logger.info(f"Scoring candidate {candidate_id} with Grok grok-3")
        try:
            score_data = await score_candidate(candidate.cv_text, rubric_path)
            logger.info(f"Candidate {candidate_id} scored: {score_data.get('total_score')}/100")
        except Exception as e:
            logger.error(f"Error scoring candidate {candidate_id}: {e}")
            await crud.update_candidate_status(db, candidate_id, "manual_review")
            await audit_service.log_action(
                db=db,
                action_type="score_candidate",
                actor="grok-3",
                result="failure",
                candidate_id=candidate_id,
                input_summary=candidate.cv_text[:500] if candidate.cv_text else None,
                output_summary=str(e)
            )
            return

        # 4. Update DB with score
        await crud.update_candidate_score(db, candidate_id, score_data)

        # Log scoring to audit
        await audit_service.log_action(
            db=db,
            action_type="score_candidate",
            actor="grok-3",
            result="success",
            candidate_id=candidate_id,
            input_summary=candidate.cv_text[:500] if candidate.cv_text else None,
            output_summary=json.dumps({
                "total_score": score_data.get("total_score"),
                "recommendation": score_data.get("recommendation")
            })
        )

        # 5. Create pending approval immediately after scoring
        if score_data.get("must_haves_met"):
            action = "advance"
            recommendation = score_data.get("recommendation", "advance")
        else:
            action = "reject"
            recommendation = score_data.get("disqualification_reason") or "Does not meet requirements"

        await crud.create_pending_approval(
            db=db,
            candidate_id=candidate_id,
            job_id=candidate.job_id,
            action=action,
            score=score_data.get("total_score"),
            recommendation=recommendation,
            brief_summary=score_data.get("summary") or f"Scored {score_data.get('total_score')}/100. {recommendation}."
        )

        await crud.update_candidate_status(db, candidate_id, "shortlisted")

        await audit_service.log_action(
            db=db,
            action_type="create_pending_approval",
            actor="system",
            result="success",
            candidate_id=candidate_id,
            output_summary=f"Created {action} approval with score {score_data.get('total_score')}"
        )

        logger.info(f"Successfully processed candidate {candidate_id} - {action} approval created")

    except Exception as e:
        logger.error(f"Unexpected error processing candidate {candidate_id}: {e}")


async def process_candidate_reply(candidate_id: int, reply_text: str, db: AsyncSession):
    """
    Process a candidate's reply: analyze with Grok, create approval.

    Args:
        candidate_id: ID of candidate
        reply_text: Candidate's reply text
        db: Database session
    """
    try:
        # 1. Fetch candidate and original score
        candidate = await crud.get_candidate(db, candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found")
            return

        logger.info(f"Processing reply from candidate {candidate_id}: {candidate.email}")

        if not candidate.screening_questions:
            logger.error(f"Candidate {candidate_id} has no screening questions")
            return

        # Build original score dict
        original_score = {
            "total_score": candidate.total_score,
            "recommendation": candidate.recommendation
        }

        # 2. Analyze reply with Grok
        logger.info(f"Analyzing reply from candidate {candidate_id} with Grok grok-3")
        try:
            analysis = await analyze_reply(
                questions=candidate.screening_questions,
                reply_text=reply_text,
                original_score=original_score
            )
            logger.info(f"Reply analyzed for candidate {candidate_id}: final score {analysis.get('final_score')}")
        except Exception as e:
            logger.error(f"Error analyzing reply for candidate {candidate_id}: {e}")
            await crud.update_candidate_status(db, candidate_id, "manual_review")
            await audit_service.log_action(
                db=db,
                action_type="analyze_reply",
                actor="grok-3",
                result="failure",
                candidate_id=candidate_id,
                input_summary=reply_text[:500],
                output_summary=str(e)
            )
            return

        # 3. Update candidate with reply and final score
        await crud.update_candidate_reply(db, candidate_id, reply_text, analysis)

        # Log to audit
        await audit_service.log_action(
            db=db,
            action_type="analyze_reply",
            actor="grok-3",
            result="success",
            candidate_id=candidate_id,
            input_summary=reply_text[:500],
            output_summary=json.dumps({
                "final_score": analysis.get("final_score"),
                "updated_recommendation": analysis.get("updated_recommendation")
            })
        )

        # 4. Create pending approval for advance
        job = await crud.get_job(db, candidate.job_id)

        await crud.create_pending_approval(
            db=db,
            candidate_id=candidate_id,
            job_id=candidate.job_id,
            action="advance",
            score=analysis.get("final_score"),
            recommendation=analysis.get("updated_recommendation"),
            brief_summary=analysis.get("brief_summary")
        )

        await crud.update_candidate_status(db, candidate_id, "shortlisted")

        await audit_service.log_action(
            db=db,
            action_type="create_pending_approval",
            actor="system",
            result="success",
            candidate_id=candidate_id,
            output_summary="Advance approval created after reply analysis"
        )

        logger.info(f"Successfully processed reply from candidate {candidate_id}")

    except Exception as e:
        logger.error(f"Unexpected error processing reply for candidate {candidate_id}: {e}")


async def run_orchestrator():
    """
    Main orchestrator loop: consume screening_queue, reply_queue, scheduling_reply_queue, and rejection_reply_queue concurrently.

    Runs indefinitely, processing candidates, replies, scheduling conversations, and rejection replies from Redis queues.
    """
    logger.info("Starting orchestrator")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = await redis.from_url(redis_url)

    async def consume_screening_queue():
        """Consume screening_queue and process new candidates."""
        logger.info("Starting screening queue consumer")

        while True:
            try:
                # Pop from queue (blocking with 1 second timeout)
                result = await redis_client.brpop("screening_queue", timeout=1)

                if result:
                    queue_name, candidate_id_bytes = result
                    candidate_id = int(candidate_id_bytes.decode())

                    logger.info(f"Popped candidate {candidate_id} from screening queue")

                    # Process candidate
                    async with AsyncSessionLocal() as db:
                        await process_new_candidate(candidate_id, db)

            except Exception as e:
                logger.error(f"Error in screening queue consumer: {e}")
                await asyncio.sleep(1)

    async def consume_reply_queue():
        """Consume reply_queue and process candidate replies."""
        logger.info("Starting reply queue consumer")

        while True:
            try:
                # Pop from queue (blocking with 1 second timeout)
                result = await redis_client.brpop("reply_queue", timeout=1)

                if result:
                    queue_name, reply_data_bytes = result
                    reply_data = json.loads(reply_data_bytes.decode())

                    candidate_id = reply_data["candidate_id"]
                    reply_text = reply_data["reply_text"]

                    logger.info(f"Popped reply for candidate {candidate_id} from reply queue")

                    # Process reply
                    async with AsyncSessionLocal() as db:
                        await process_candidate_reply(candidate_id, reply_text, db)

            except Exception as e:
                logger.error(f"Error in reply queue consumer: {e}")
                await asyncio.sleep(1)

    async def consume_scheduling_reply_queue():
        """Consume scheduling_reply_queue and process scheduling conversation replies."""
        logger.info("Starting scheduling reply queue consumer")

        # Import here to avoid circular dependency
        from services.scheduling_agent import scheduling_agent

        while True:
            try:
                # Pop from queue (blocking with 1 second timeout)
                result = await redis_client.brpop("scheduling_reply_queue", timeout=1)

                if result:
                    queue_name, reply_data_bytes = result
                    reply_data = json.loads(reply_data_bytes.decode())

                    candidate_id = reply_data["candidate_id"]
                    reply_text = reply_data["reply_text"]
                    reply_message_id = reply_data["reply_message_id"]

                    logger.info(f"Popped scheduling reply for candidate {candidate_id} from scheduling queue")

                    # Process scheduling reply
                    async with AsyncSessionLocal() as db:
                        await scheduling_agent.handle_scheduling_reply(
                            db, candidate_id, reply_text, reply_message_id
                        )

            except Exception as e:
                logger.error(f"Error in scheduling reply queue consumer: {e}")
                await asyncio.sleep(1)

    async def consume_rejection_reply_queue():
        """Consume rejection_reply_queue and process rejection email replies."""
        logger.info("Starting rejection reply queue consumer")

        # Import here to avoid circular dependency
        from services.rejection_reply_handler import rejection_reply_handler

        while True:
            try:
                # Pop from queue (blocking with 1 second timeout)
                result = await redis_client.brpop("rejection_reply_queue", timeout=1)

                if result:
                    queue_name, reply_data_bytes = result
                    reply_data = json.loads(reply_data_bytes.decode())

                    candidate_id = reply_data["candidate_id"]
                    reply_text = reply_data["reply_text"]
                    reply_message_id = reply_data["reply_message_id"]

                    logger.info(f"Popped rejection reply for candidate {candidate_id} from rejection queue")

                    # Process rejection reply
                    async with AsyncSessionLocal() as db:
                        await rejection_reply_handler.handle_rejection_reply(
                            db, candidate_id, reply_text, reply_message_id
                        )

            except Exception as e:
                logger.error(f"Error in rejection reply queue consumer: {e}")
                await asyncio.sleep(1)

    # Run all four consumers concurrently
    await asyncio.gather(
        consume_screening_queue(),
        consume_reply_queue(),
        consume_scheduling_reply_queue(),
        consume_rejection_reply_queue()
    )


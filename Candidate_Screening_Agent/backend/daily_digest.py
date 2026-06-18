import os
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import AsyncSessionLocal
from db.models import Candidate
from services.gmail_service import gmail_service
from services import audit_service
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_groq_model():
    """Get Groq model for fast summarization."""
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"),
    )
    return OpenAIChatCompletionsModel(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        openai_client=client,
    )


async def send_daily_digest(db: AsyncSession):
    """
    Generate and send daily talent digest to hiring manager.

    Fetches candidates from past 24 hours, groups by status,
    generates AI summary, and sends email.
    """
    try:
        logger.info("Generating daily talent digest")

        # Get hiring manager email
        hiring_manager_email = os.getenv("HIRING_MANAGER_EMAIL", "manager@yourdomain.com")

        # Fetch candidates from past 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)

        result = await db.execute(
            select(Candidate).where(Candidate.created_at >= yesterday)
        )
        recent_candidates = result.scalars().all()

        # Group by status
        status_counts = {}
        for candidate in recent_candidates:
            status = candidate.status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate stats
        stats = {
            "new_applications": status_counts.get("queued", 0) + status_counts.get("scoring", 0) + status_counts.get("scored", 0),
            "questions_sent": status_counts.get("questions_sent", 0) + status_counts.get("awaiting_reply", 0),
            "replies_received": status_counts.get("replied", 0),
            "pending_approvals": status_counts.get("shortlisted", 0),
            "shortlisted": status_counts.get("shortlisted", 0),
            "rejected": status_counts.get("rejected", 0),
        }

        logger.info(f"Daily digest stats: {stats}")

        # Generate AI summary with Grok mini
        if recent_candidates:
            # Build context for AI
            context = f"""Past 24 hours:
- {stats['new_applications']} new applications received
- {stats['questions_sent']} screening questions sent
- {stats['replies_received']} replies received
- {stats['pending_approvals']} pending approvals
- {stats['rejected']} rejected

Total candidates in past 24h: {len(recent_candidates)}"""

            agent = Agent(
                name="Digest Summarizer",
                model=get_groq_model(),
                instructions=f"""You are a hiring assistant. Generate a concise 3-sentence executive summary of the hiring pipeline activity.

{context}

Focus on:
1. Overall activity level (busy, moderate, quiet)
2. Key highlights or concerns
3. Action items for hiring manager

Keep it professional, concise, and actionable. Return ONLY the 3-sentence summary, no formatting."""
            )

            try:
                result = await Runner.run(agent, "Generate the 3-sentence executive summary.")
                summary = result.final_output.strip()
                logger.info(f"Generated AI summary: {summary}")
            except Exception as e:
                logger.error(f"Error generating AI summary: {e}")
                summary = f"Received {stats['new_applications']} new applications in the past 24 hours. {stats['pending_approvals']} candidates are awaiting your approval. Please review the dashboard for details."

        else:
            summary = "No new candidate activity in the past 24 hours. The pipeline is quiet today."

        # Prepare digest data
        digest_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "stats": stats,
            "summary": summary
        }

        # Send digest email
        message_id = gmail_service.send_daily_digest(
            to=hiring_manager_email,
            digest_data=digest_data
        )

        logger.info(f"Daily digest sent to {hiring_manager_email} (message ID: {message_id})")

        # Log to audit
        await audit_service.log_action(
            db=db,
            action_type="send_daily_digest",
            actor="system",
            result="success",
            output_summary=f"Sent digest to {hiring_manager_email}: {stats['new_applications']} new applications"
        )

    except Exception as e:
        logger.error(f"Error sending daily digest: {e}")
        await audit_service.log_action(
            db=db,
            action_type="send_daily_digest",
            actor="system",
            result="failure",
            output_summary=str(e)
        )


async def schedule_daily_digest():
    """
    Scheduled task to send daily digest at 8:00 AM.

    This function is called by APScheduler.
    """
    async with AsyncSessionLocal() as db:
        await send_daily_digest(db)

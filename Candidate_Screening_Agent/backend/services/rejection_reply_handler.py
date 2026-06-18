import logging
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import OpenAI
from db.models import Candidate, Job
from services.gmail_service import gmail_service
from services import audit_service
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RejectionReplyHandler:
    """
    Handles replies to rejection emails with empathy and professionalism.

    Limits responses to 3 per candidate to prevent endless conversations.
    Uses LLM to generate contextual, empathetic responses.
    """

    MAX_RESPONSES = 3  # Maximum number of responses to rejection replies

    def __init__(self):
        # Initialize OpenAI client (works with Grok via XAI_API_KEY)
        self.client = OpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-beta"

    async def handle_rejection_reply(
        self,
        db: AsyncSession,
        candidate_id: int,
        reply_text: str,
        reply_message_id: str
    ):
        """
        Handle a candidate's reply to a rejection email.

        Limits responses to MAX_RESPONSES (3) per candidate.

        Args:
            db: Database session
            candidate_id: Candidate ID
            reply_text: Candidate's reply text
            reply_message_id: Gmail message ID of reply
        """
        try:
            # Get candidate and job info
            candidate = await self._get_candidate(db, candidate_id)
            if not candidate:
                logger.error(f"Candidate {candidate_id} not found")
                return

            # Check if we've already responded too many times
            if candidate.rejection_reply_count >= self.MAX_RESPONSES:
                logger.info(f"Candidate {candidate_id} has reached max responses ({self.MAX_RESPONSES}). Not responding.")
                await audit_service.log_action(
                    db=db,
                    action_type="rejection_reply_limit_reached",
                    actor="ai_agent",
                    result="success",
                    candidate_id=candidate.id,
                    output_summary=f"Candidate reached {self.MAX_RESPONSES} response limit. Reply ignored."
                )
                return

            job = await self._get_job(db, candidate.job_id)
            if not job:
                logger.error(f"Job {candidate.job_id} not found")
                return

            logger.info(f"Processing rejection reply from candidate {candidate_id}: {candidate.email} (reply #{candidate.rejection_reply_count + 1})")

            # Analyze the reply to understand intent
            intent = await self._analyze_rejection_reply(
                reply_text=reply_text,
                candidate_name=candidate.name or candidate.email,
                job_title=job.title
            )

            logger.info(f"Rejection reply intent: {intent['type']}")

            # Generate appropriate response based on intent and reply count
            response = await self._generate_response(
                intent=intent,
                candidate_name=candidate.name or candidate.email,
                job_title=job.title,
                reply_text=reply_text,
                reply_count=candidate.rejection_reply_count,
                is_final_response=(candidate.rejection_reply_count + 1 >= self.MAX_RESPONSES)
            )

            # Send response email
            message_id = gmail_service.send_email(
                to=candidate.email,
                subject=f"Re: Application Update - {job.title}",
                body=response
            )

            # Increment rejection reply count
            candidate.rejection_reply_count += 1
            await db.commit()

            # Log to audit
            await audit_service.log_action(
                db=db,
                action_type="handle_rejection_reply",
                actor="ai_agent",
                result="success",
                candidate_id=candidate.id,
                input_summary=reply_text[:500],
                output_summary=f"Responded to rejection reply #{candidate.rejection_reply_count} with {intent['type']} intent"
            )

            logger.info(f"Sent rejection reply response to {candidate.email} (message ID: {message_id}, reply #{candidate.rejection_reply_count}/{self.MAX_RESPONSES})")

        except Exception as e:
            logger.error(f"Error handling rejection reply for candidate {candidate_id}: {e}")
            await audit_service.log_action(
                db=db,
                action_type="handle_rejection_reply",
                actor="ai_agent",
                result="failure",
                candidate_id=candidate_id,
                output_summary=str(e)
            )

    async def _analyze_rejection_reply(
        self,
        reply_text: str,
        candidate_name: str,
        job_title: str
    ) -> dict:
        """
        Analyze the candidate's reply to understand their intent.

        Returns:
            Dict with type and details
        """
        prompt = f"""Analyze this candidate's reply to a job rejection email.

Candidate: {candidate_name}
Job: {job_title}

Candidate's Reply:
{reply_text}

Determine the candidate's intent. Possible types:
1. reconsideration - Asking for another chance, mentioning hardship, requesting reconsideration
2. feedback - Asking why they were rejected or for feedback
3. question - Asking a question about the process or decision
4. gratitude - Thanking for the opportunity
5. disappointment - Expressing disappointment but accepting
6. other - Other type of response

Respond in JSON format:
{{
    "type": "reconsideration|feedback|question|gratitude|disappointment|other",
    "tone": "desperate|professional|grateful|disappointed|angry|neutral",
    "key_points": ["point1", "point2"],
    "requires_empathy": true|false
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        import json
        intent = json.loads(response.choices[0].message.content)
        return intent

    async def _generate_response(
        self,
        intent: dict,
        candidate_name: str,
        job_title: str,
        reply_text: str,
        reply_count: int,
        is_final_response: bool
    ) -> str:
        """
        Generate an empathetic, professional response based on intent.

        Args:
            intent: Intent analysis from _analyze_rejection_reply
            candidate_name: Candidate's name
            job_title: Job title
            reply_text: Original reply text
            reply_count: Current reply count (0-indexed)
            is_final_response: Whether this is the final response (3rd response)

        Returns:
            Email body text
        """
        intent_type = intent.get("type", "other")
        tone = intent.get("tone", "neutral")

        # Add final response note if this is the last one
        final_note = ""
        if is_final_response:
            final_note = "\n\nNote: This will be my final response on this matter, but I wish you all the best in your job search."

        # Build context-aware prompt based on intent type
        if intent_type == "reconsideration":
            prompt = f"""Generate an empathetic, professional response to a candidate who is asking for reconsideration after being rejected.

Candidate: {candidate_name}
Job: {job_title}
Tone detected: {tone}
This is response #{reply_count + 1} of 3 maximum.

Candidate's message:
{reply_text}

Guidelines:
- Be extremely empathetic and understanding
- Acknowledge their situation with compassion
- Explain that the decision was based on fit with current requirements, not personal circumstances
- Be firm but kind - the decision stands
- Offer to keep their resume on file for future opportunities
- Encourage them to apply for other positions
- Be warm but honest - don't give false hope
- Keep it professional but human
{final_note}

Sign as "AI Recruiting Assistant"."""

        elif intent_type == "feedback":
            prompt = f"""Generate a helpful response to a candidate asking for feedback on why they were rejected.

Candidate: {candidate_name}
Job: {job_title}
This is response #{reply_count + 1} of 3 maximum.

Candidate's message:
{reply_text}

Guidelines:
- Thank them for their interest in feedback
- Explain that we look for specific experience alignment with job requirements
- Mention that competition was strong
- Offer general encouragement
- Suggest they continue developing their skills
- Be constructive and supportive
{final_note}

Sign as "AI Recruiting Assistant"."""

        elif intent_type == "question":
            prompt = f"""Generate a helpful response to a candidate's question about the rejection.

Candidate: {candidate_name}
Job: {job_title}
This is response #{reply_count + 1} of 3 maximum.

Candidate's message:
{reply_text}

Guidelines:
- Answer their question professionally
- Be transparent but tactful
- Provide helpful information
- Maintain a supportive tone
{final_note}

Sign as "AI Recruiting Assistant"."""

        elif intent_type == "gratitude":
            prompt = f"""Generate a warm response to a candidate who is thanking you despite being rejected.

Candidate: {candidate_name}
Job: {job_title}
This is response #{reply_count + 1} of 3 maximum.

Candidate's message:
{reply_text}

Guidelines:
- Thank them for their graciousness
- Wish them well in their search
- Keep the door open for future opportunities
- Be brief but warm
{final_note}

Sign as "AI Recruiting Assistant"."""

        else:
            # General empathetic response
            prompt = f"""Generate an empathetic, professional response to a candidate who replied to their rejection email.

Candidate: {candidate_name}
Job: {job_title}
Tone: {tone}
This is response #{reply_count + 1} of 3 maximum.

Candidate's message:
{reply_text}

Guidelines:
- Be empathetic and understanding
- Acknowledge their response
- Be professional but human
- Keep the door open for future opportunities
- Be brief but warm
{final_note}

Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    async def _get_candidate(self, db: AsyncSession, candidate_id: int) -> Optional[Candidate]:
        """Get candidate by ID."""
        query = select(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_job(self, db: AsyncSession, job_id: int) -> Optional[Job]:
        """Get job by ID."""
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Global instance
rejection_reply_handler = RejectionReplyHandler()

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from openai import OpenAI
from db.models import Candidate, Job, InterviewSlot, SchedulingConversation
from services.calendar_service import calendar_service
from services.gmail_service import gmail_service
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SchedulingAgent:
    """
    Intelligent scheduling agent that handles interview scheduling conversations.

    Uses LLM (Grok/OpenAI) to generate creative, contextual responses instead of templates.
    Manages the full scheduling workflow autonomously.
    """

    def __init__(self):
        # Initialize OpenAI client using Groq (OpenAI-compatible)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
        )
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    async def initiate_scheduling(
        self,
        db: AsyncSession,
        candidate_id: int,
        job_id: int
    ) -> str:
        """
        Initiate scheduling conversation after candidate is approved.

        Args:
            db: Database session
            candidate_id: Candidate ID
            job_id: Job ID

        Returns:
            Message ID of sent email
        """
        # Get candidate and job info
        candidate = await self._get_candidate(db, candidate_id)
        job = await self._get_job(db, job_id)

        if not candidate or not job:
            raise ValueError(f"Candidate {candidate_id} or Job {job_id} not found")

        # Get available slots
        available_slots = await calendar_service.get_available_slots(db, job_id, limit=5)

        if not available_slots:
            logger.warning(f"No available slots for job {job_id}")
            # Send email saying we'll reach out when slots are available
            message_id = gmail_service.send_email(
                to=candidate.email,
                subject=f"Interview Invitation - {job.title}",
                body=self._generate_no_slots_message(candidate.name or candidate.email, job.title)
            )
            return message_id

        # Propose slots to candidate
        slot_ids = [slot.id for slot in available_slots]
        proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate_id)

        # Create scheduling conversation record
        conversation = SchedulingConversation(
            candidate_id=candidate_id,
            job_id=job_id,
            conversation_state="proposing_times",
            proposed_slots=slot_ids,
            conversation_history=[]
        )
        db.add(conversation)
        await db.commit()

        # Generate creative email using LLM
        email_body = await self._generate_initial_scheduling_email(
            candidate_name=candidate.name or candidate.email,
            job_title=job.title,
            slots=proposed_slots
        )

        # Send email
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=email_body
        )

        # Update conversation with message ID
        conversation.last_message_id = message_id
        conversation.conversation_history.append({
            "role": "assistant",
            "content": email_body,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        await db.commit()

        logger.info(f"Initiated scheduling for candidate {candidate_id}, message ID: {message_id}")
        return message_id

    def _build_threading_headers(self, conversation, reply_message_id: str) -> tuple[str, str]:
        """Build In-Reply-To and References headers for proper Gmail threading.

        Gmail threads emails based on the FIRST Message-ID in the References chain.
        All replies must reference the ORIGINAL invite's Message-ID as the anchor.
        """
        # Find the original invite's Message-ID from conversation history (first assistant message)
        original_msg_id = ""
        for msg in conversation.conversation_history:
            mid = msg.get("message_id", "")
            if mid and mid.startswith("<") and mid.endswith(">"):
                original_msg_id = mid
                break  # Use the FIRST one (original invite)

        # In-Reply-To: always the original invite ID (Gmail's threading anchor)
        in_reply_to = original_msg_id

        # References: full chain - original invite + all intermediate messages + current reply
        references_parts = []
        if original_msg_id:
            references_parts.append(original_msg_id)
        for msg in conversation.conversation_history:
            mid = msg.get("message_id", "")
            if mid and mid.startswith("<") and mid.endswith(">") and mid != original_msg_id:
                references_parts.append(mid)
        # Add the reply ID
        if reply_message_id:
            rid = reply_message_id if reply_message_id.startswith("<") else f"<{reply_message_id}>"
            if rid not in references_parts:
                references_parts.append(rid)

        # Deduplicate while preserving order
        seen = set()
        unique_refs = []
        for ref in references_parts:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)

        references = " ".join(unique_refs) if unique_refs else in_reply_to

        return in_reply_to, references

    async def handle_scheduling_reply(
        self,
        db: AsyncSession,
        candidate_id: int,
        reply_text: str,
        reply_message_id: str
    ):
        """
        Handle candidate's reply in scheduling conversation.

        Args:
            db: Database session
            candidate_id: Candidate ID
            reply_text: Candidate's reply text
            reply_message_id: Gmail message ID of reply
        """
        # Get conversation
        query = select(SchedulingConversation).where(
            and_(
                SchedulingConversation.candidate_id == candidate_id,
                SchedulingConversation.conversation_state.in_([
                    "proposing_times", "awaiting_confirmation", "rescheduling"
                ])
            )
        ).order_by(SchedulingConversation.updated_at.desc())
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            logger.warning(f"No active scheduling conversation for candidate {candidate_id}")
            return

        # Get candidate and job
        candidate = await self._get_candidate(db, candidate_id)
        job = await self._get_job(db, conversation.job_id)

        # Add candidate reply to conversation history
        conversation.conversation_history.append({
            "role": "user",
            "content": reply_text,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": reply_message_id
        })

        # Analyze reply using LLM to understand intent
        intent = await self._analyze_candidate_intent(
            reply_text=reply_text,
            conversation_history=conversation.conversation_history,
            proposed_slots=conversation.proposed_slots
        )

        logger.info(f"Candidate {candidate_id} intent: {intent['action']}")

        # Handle based on intent
        if intent["action"] == "accept_slot":
            # Ensure slot_number is int
            slot_num = intent.get("slot_number")
            if isinstance(slot_num, str):
                try:
                    slot_num = int(slot_num)
                except (ValueError, TypeError):
                    slot_num = None
            intent["slot_number"] = slot_num
            await self._handle_slot_acceptance(
                db, conversation, candidate, job, intent, reply_message_id
            )
        elif intent["action"] == "request_alternative":
            await self._handle_alternative_request(
                db, conversation, candidate, job, intent, reply_message_id
            )
        elif intent["action"] == "ask_question":
            await self._handle_question(
                db, conversation, candidate, job, intent, reply_message_id
            )
        elif intent["action"] == "decline":
            await self._handle_decline(
                db, conversation, candidate, job, reply_message_id
            )
        else:
            # Unclear intent - ask for clarification
            await self._handle_unclear_intent(
                db, conversation, candidate, job, reply_message_id
            )

        await db.commit()

    async def _generate_initial_scheduling_email(
        self,
        candidate_name: str,
        job_title: str,
        slots: List[InterviewSlot]
    ) -> str:
        """
        Generate creative initial scheduling email using LLM.

        Args:
            candidate_name: Candidate's name
            job_title: Job title
            slots: List of available slots

        Returns:
            Email body text
        """
        # Format slots for display
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

        slots_text = "\n".join(formatted_slots)

        prompt = f"""You are an AI recruiting assistant. Generate a warm, professional, and creative email inviting a candidate for an interview.

Candidate Name: {candidate_name}
Job Title: {job_title}

Available Time Slots:
{slots_text}

Requirements:
- Be warm and enthusiastic (they were approved!)
- Present the time slots clearly
- Ask them to choose one or suggest an alternative
- Keep it concise but friendly
- Don't use generic phrases like "we'll reach out shortly"
- Be specific and actionable
- Sign off as "AI Recruiting Assistant"

Generate the email body (no subject line):"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        email_body = response.choices[0].message.content.strip()
        return email_body

    async def _analyze_candidate_intent(
        self,
        reply_text: str,
        conversation_history: List[Dict],
        proposed_slots: List[int]
    ) -> Dict:
        """
        Analyze candidate's reply to understand their intent using LLM.

        Args:
            reply_text: Candidate's reply
            conversation_history: Previous conversation
            proposed_slots: Slot IDs that were proposed

        Returns:
            Dict with action and extracted info
        """
        # Build conversation context
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:200]}"
            for msg in conversation_history[-3:]  # Last 3 messages
        ])

        prompt = f"""Analyze this candidate's reply to an interview scheduling email.

Conversation History:
{history_text}

Candidate's Latest Reply:
{reply_text}

Determine the candidate's intent and extract relevant information.

Possible intents:
1. accept_slot - They're accepting one of the proposed times (extract which slot number)
2. request_alternative - They want different times (extract reason if mentioned)
3. ask_question - They have a question (extract the question)
4. decline - They're declining the interview
5. unclear - Intent is not clear

Respond in JSON format:
{{
    "action": "accept_slot|request_alternative|ask_question|decline|unclear",
    "slot_number": <number if accepting, else null>,
    "reason": "<reason if declining or requesting alternative>",
    "question": "<question if asking>",
    "confidence": "high|medium|low"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        intent = json.loads(response.choices[0].message.content)
        return intent

    async def _handle_slot_acceptance(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        intent: Dict,
        reply_message_id: str = ""
    ):
        """Handle candidate accepting a time slot."""
        slot_number = intent.get("slot_number")
        if not slot_number or slot_number < 1 or slot_number > len(conversation.proposed_slots):
            # Invalid slot number - ask for clarification
            await self._handle_unclear_intent(db, conversation, candidate, job)
            return

        # Get the slot ID
        slot_id = conversation.proposed_slots[slot_number - 1]

        # Book the slot
        booked_slot = await calendar_service.book_slot(
            db, slot_id, candidate.id, meeting_link="https://meet.google.com/xyz-abc-def"  # TODO: Generate real link
        )

        if not booked_slot:
            # Slot no longer available
            response = await self._generate_slot_unavailable_response(candidate.name or candidate.email, job.title)
        else:
            # Generate confirmation email
            slot_info = calendar_service.format_slot_for_display(booked_slot)
            response = await self._generate_confirmation_email(
                candidate.name or candidate.email,
                job.title,
                slot_info
            )

            # Update conversation state
            conversation.conversation_state = "confirmed"
            conversation.confirmed_slot_id = booked_slot.id

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Confirmed - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        # Update conversation history
        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        conversation.last_message_id = message_id

        logger.info(f"Confirmed interview slot {slot_id} for candidate {candidate.id}")

    async def _handle_alternative_request(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        intent: Dict,
        reply_message_id: str = ""
    ):
        """Handle candidate requesting alternative times."""
        # Release previously proposed slots
        await calendar_service.release_proposed_slots(db, candidate.id)

        # Get new available slots
        available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)

        if not available_slots:
            response = self._generate_no_slots_message(candidate.name or candidate.email, job.title)
        else:
            # Propose new slots
            slot_ids = [slot.id for slot in available_slots]
            proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

            # Generate response with new slots
            response = await self._generate_alternative_slots_email(
                candidate.name or candidate.email,
                job.title,
                proposed_slots,
                intent.get("reason")
            )

            # Update conversation
            conversation.proposed_slots = slot_ids
            conversation.conversation_state = "proposing_times"

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Alternative Interview Times - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        conversation.last_message_id = message_id

    async def _handle_question(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        intent: Dict,
        reply_message_id: str = ""
    ):
        """Handle candidate asking a question."""
        question = intent.get("question", "")

        # Generate answer using LLM
        response = await self._generate_question_response(
            candidate.name or candidate.email,
            job.title,
            question,
            conversation.conversation_history
        )

        # Build threading headers
        in_reply_to, references = self._build_threading_headers(conversation, "")

        # Send email with threading
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Re: Interview - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        conversation.last_message_id = message_id

    async def _handle_decline(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        reply_message_id: str = ""
    ):
        """Handle candidate declining the interview."""
        # Release proposed slots
        await calendar_service.release_proposed_slots(db, candidate.id)

        # Generate polite response
        response = await self._generate_decline_response(candidate.name or candidate.email, job.title)

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Re: Interview - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        # Update conversation
        conversation.conversation_state = "cancelled"
        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        conversation.last_message_id = message_id

        logger.info(f"Candidate {candidate.id} declined interview")

    async def _handle_unclear_intent(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        reply_message_id: str = ""
    ):
        """Handle unclear candidate response."""
        # Generate clarification request
        response = await self._generate_clarification_request(
            candidate.name or candidate.email,
            job.title,
            conversation.proposed_slots
        )

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        message_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Re: Interview - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        conversation.last_message_id = message_id

    async def _generate_confirmation_email(
        self,
        candidate_name: str,
        job_title: str,
        slot_info: Dict
    ) -> str:
        """Generate creative confirmation email."""
        prompt = f"""Generate a warm, professional interview confirmation email.

Candidate: {candidate_name}
Job: {job_title}
Confirmed Time: {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}

Include:
- Confirmation of the time
- What to expect (45-minute technical interview)
- Meeting link will be sent separately
- Encourage them to prepare questions
- Warm, enthusiastic tone

Keep it concise. Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    async def _generate_alternative_slots_email(
        self,
        candidate_name: str,
        job_title: str,
        slots: List[InterviewSlot],
        reason: Optional[str]
    ) -> str:
        """Generate email with alternative time slots."""
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot)
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

        slots_text = "\n".join(formatted_slots)

        prompt = f"""Generate a friendly email offering alternative interview times.

Candidate: {candidate_name}
Job: {job_title}
Reason for alternatives: {reason or "Previous times didn't work"}

New Available Times:
{slots_text}

Be understanding and flexible. Ask them to choose or suggest another time.
Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    async def _generate_question_response(
        self,
        candidate_name: str,
        job_title: str,
        question: str,
        conversation_history: List[Dict]
    ) -> str:
        """Generate response to candidate's question."""
        prompt = f"""Generate a helpful response to a candidate's question about their interview.

Candidate: {candidate_name}
Job: {job_title}
Question: {question}

Provide a helpful, professional answer. If you don't have specific information, acknowledge that and say the hiring manager will provide details.
Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content.strip()

    async def _generate_decline_response(
        self,
        candidate_name: str,
        job_title: str
    ) -> str:
        """Generate polite response to candidate declining."""
        prompt = f"""Generate a gracious response to a candidate who declined an interview.

Candidate: {candidate_name}
Job: {job_title}

Be understanding, thank them for their time, and leave the door open for future opportunities.
Keep it brief and warm. Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    async def _generate_clarification_request(
        self,
        candidate_name: str,
        job_title: str,
        proposed_slots: List[int]
    ) -> str:
        """Generate clarification request when intent is unclear."""
        prompt = f"""Generate a polite clarification request for a candidate whose response wasn't clear.

Candidate: {candidate_name}
Job: {job_title}

Politely ask them to:
- Choose one of the numbered time slots
- Or suggest an alternative time
- Or let you know if they have questions

Be friendly and helpful. Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    def _generate_no_slots_message(self, candidate_name: str, job_title: str) -> str:
        """Generate message when no slots are available."""
        return f"""Dear {candidate_name},

Thank you for your interest in the {job_title} position. We're currently coordinating interview schedules and will reach out within 24-48 hours with available time slots.

We appreciate your patience!

Best regards,
AI Recruiting Assistant"""

    async def _generate_slot_unavailable_response(self, candidate_name: str, job_title: str) -> str:
        """Generate response when selected slot is no longer available."""
        prompt = f"""Generate an apologetic email explaining that the time slot they selected was just booked by another candidate.

Candidate: {candidate_name}
Job: {job_title}

Apologize for the inconvenience and say you'll send alternative times shortly.
Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
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
scheduling_agent = SchedulingAgent()

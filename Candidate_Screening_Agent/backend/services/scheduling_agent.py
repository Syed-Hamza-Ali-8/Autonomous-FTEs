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
from datetime import datetime, timedelta

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
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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

        # Get available slots - create defaults if none exist
        available_slots = await calendar_service.get_available_slots(db, job_id, limit=5)

        if not available_slots:
            # Auto-create default interview slots (next 5 weekdays, 10am-2pm)
            available_slots = await self._create_default_slots(db, job_id)
            logger.info(f"Created {len(available_slots)} default slots for job {job_id}")

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
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=email_body
        )

        # Update conversation with message ID
        conversation.last_message_id = gmail_msg_id
        conversation.conversation_history.append({
            "role": "assistant",
            "content": email_body,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": gmail_msg_id
        })
        await db.commit()

        logger.info(f"Initiated scheduling for candidate {candidate_id}, message ID: {message_id}")
        return message_id

    async def _create_default_slots(self, db, job_id: int, company_id: int = 1) -> list:
        """Create default interview slots for next 5 weekdays."""
        from sqlalchemy import select
        slots = []
        now = datetime.utcnow()
        times = ["10:00", "11:00", "14:00", "15:00", "16:00"]
        day = 1
        slot_time_idx = 0
        created = []
        while len(created) < 5 and day < 14:
            candidate_date = now + timedelta(days=day)
            if candidate_date.weekday() < 5:  # Weekday
                time_str = times[slot_time_idx % len(times)]
                hour, minute = map(int, time_str.split(":"))
                start = candidate_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end = start + timedelta(minutes=45)
                slot = InterviewSlot(
                    company_id=company_id,
                    job_id=job_id,
                    start_time=start,
                    end_time=end,
                    status="available",
                    timezone="UTC",
                    interviewer_name="Hiring Manager",
                )
                db.add(slot)
                created.append(slot)
                slot_time_idx += 1
            day += 1
        await db.commit()
        # Refresh to get IDs
        for slot in created:
            await db.refresh(slot)
        return created

    def _build_threading_headers(self, conversation, reply_message_id: str) -> tuple[str, str]:
        """Build In-Reply-To and References headers for proper Gmail threading.

        For proper thread continuation:
        - In-Reply-To should be the IMMEDIATE parent message (candidate's latest reply)
        - References should contain the full chain starting with original invite
        """
        # Find the original invite's Message-ID from conversation history (first assistant message)
        original_msg_id = ""
        for msg in conversation.conversation_history:
            mid = msg.get("message_id", "")
            if mid and mid.startswith("<") and mid.endswith(">"):
                original_msg_id = mid
                break

        # Build References: full chain starting with original invite
        references_parts = []
        if original_msg_id:
            references_parts.append(original_msg_id)
        for msg in conversation.conversation_history:
            mid = msg.get("message_id", "")
            if mid and mid.startswith("<") and mid.endswith(">") and mid != original_msg_id:
                references_parts.append(mid)

        # In-Reply-To: reply to the IMMEDIATE parent (candidate's latest reply if available)
        if reply_message_id:
            rid = reply_message_id if reply_message_id.startswith("<") else f"<{reply_message_id}>"
            in_reply_to = rid
            # Add candidate's reply to references if not already there
            if rid not in references_parts:
                references_parts.append(rid)
        else:
            # No reply_message_id - reply to last message in chain
            in_reply_to = references_parts[-1] if references_parts else original_msg_id

        # References must start with original invite for proper Gmail threading
        # Reorder so original is first
        final_refs = []
        if original_msg_id and original_msg_id not in final_refs:
            final_refs.append(original_msg_id)
        for ref in references_parts:
            if ref != original_msg_id and ref not in final_refs:
                final_refs.append(ref)

        references = " ".join(final_refs) if final_refs else in_reply_to

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
                    "awaiting_questions_reply", "proposing_times", "awaiting_confirmation", "rescheduling", "confirmed"
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

        # FAIL-SAFE: Keyword check BEFORE any processing
        decline_phrases = [
            "not interested", "no longer interested", "decline",
            "withdraw", "not pursuing", "remove me", "unsubscribe",
            "going with another", "accepted another", "don't want"
        ]
        reply_lower = reply_text.lower()
        if any(phrase in reply_lower for phrase in decline_phrases):
            logger.info(f"Candidate {candidate_id} matched decline keyword - bypassing LLM")
            await self._handle_decline(db, conversation, candidate, job, reply_message_id)
            return

        # Check if awaiting questions reply
        if conversation.conversation_state == "awaiting_questions_reply":
            # Analyze questions reply and send time slots
            await self._handle_questions_reply(db, conversation, candidate, job, reply_text, reply_message_id)
            return

        # Get slot details for intent analysis
        slots = []
        if conversation.proposed_slots:
            slot_query = select(InterviewSlot).where(InterviewSlot.id.in_(conversation.proposed_slots))
            slot_result = await db.execute(slot_query)
            slots = slot_result.scalars().all()

        # FAIL-SAFE: Keyword check BEFORE LLM (if LLM fails, this catches it)
        decline_phrases = [
            "not interested", "no longer interested", "decline",
            "withdraw", "not pursuing", "remove me", "unsubscribe",
            "going with another", "accepted another", "don't want"
        ]
        reply_lower = reply_text.lower()
        if any(phrase in reply_lower for phrase in decline_phrases):
            logger.info(f"Candidate {candidate_id} matched decline keyword - bypassing LLM")
            await self._handle_decline(db, conversation, candidate, job, reply_message_id)
            return

        # Analyze reply using LLM to understand intent
        intent = await self._analyze_intent_after_questions(
            reply_text=reply_text,
            conversation_history=conversation.conversation_history,
            proposed_slots=conversation.proposed_slots,
            slots=slots
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

    async def _generate_approval_email_with_questions(
        self,
        candidate_name: str,
        job_title: str,
        questions: List[str],
        slots_text: str
    ) -> str:
        """Generate email with interview invitation + screening questions."""

        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        prompt = f"""You are an AI recruiting assistant. Generate a warm, professional email inviting a candidate for an interview AND include screening questions they need to answer.

Candidate Name: {candidate_name}
Job Title: {job_title}

Available Time Slots:
{slots_text}

Screening Questions (include these in the email):
{questions_text}

Requirements:
- Start with congratulations on being selected for interview
- Present the time slots clearly and ask them to choose one OR suggest alternative
- Include the screening questions they need to answer via email reply
- Tell them to reply to this email with: (1) preferred time slot, (2) answers to screening questions
- Be warm and enthusiastic
- Keep it professional but friendly
- Sign off as "AI Recruiting Assistant"

Generate the email body (no subject line):"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )

        email_body = response.choices[0].message.content.strip()
        return email_body

    async def _handle_questions_reply(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        reply_text: str,
        reply_message_id: str = ""
    ):
        """Handle reply to screening questions - check for slot selection, book if found."""
        from db import crud

        # Update candidate reply
        await crud.update_candidate_reply(db, conversation.candidate_id, reply_text, {"questions_analyzed": True})

        # Get slot details
        slots = []
        if conversation.proposed_slots:
            slot_query = select(InterviewSlot).where(InterviewSlot.id.in_(conversation.proposed_slots))
            slot_result = await db.execute(slot_query)
            slots = slot_result.scalars().all()

        # Check if reply also contains a slot selection
        intent = await self._analyze_intent_after_questions(
            reply_text=reply_text,
            conversation_history=conversation.conversation_history,
            proposed_slots=conversation.proposed_slots,
            slots=slots
        )

        # If candidate explicitly selected a slot, book it directly
        if intent.get("action") == "accept_slot":
            slot_num = intent.get("slot_number")
            if isinstance(slot_num, str):
                try:
                    slot_num = int(slot_num)
                except (ValueError, TypeError):
                    slot_num = None

            if slot_num and 1 <= slot_num <= len(conversation.proposed_slots):
                logger.info(f"Candidate also selected slot {slot_num} with screening answers - booking directly")
                await self._handle_slot_acceptance(
                    db, conversation, candidate, job, intent, reply_message_id
                )
                return

        # No slot selection found - send time slots email as before
        # Format slots for email
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

        slots_text = "\n".join(formatted_slots)

        # Generate time slots email
        prompt = f"""You are an AI recruiting assistant. Thank the candidate for answering screening questions and provide available interview time slots.

Candidate Name: {candidate.name or candidate.email}
Job Title: {job.title}

Available Time Slots:
{slots_text}

Requirements:
- Thank them for answering the screening questions
- Present the time slots clearly
- Ask them to reply with their preferred slot number (1-5) or suggest alternative time
- Be warm and appreciative
- Sign off as "AI Recruiting Assistant"

Generate the email body (no subject line):"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        email_body = response.choices[0].message.content.strip()

        # Send email
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Time Slots - {job.title}",
            body=email_body
        )

        # Update conversation state
        conversation.conversation_state = "proposing_times"
        await db.commit()

        logger.info(f"Sent time slots to {candidate.email} for candidate {candidate.id}")

    async def _analyze_intent_after_questions(
        self,
        reply_text: str,
        conversation_history: List[Dict],
        proposed_slots: List[int],
        slots: List[InterviewSlot] = None
    ) -> Dict:
        """
        Analyze candidate's reply to understand their intent using LLM.

        Args:
            reply_text: Candidate's reply
            conversation_history: Previous conversation
            proposed_slots: Slot IDs that were proposed
            slots: Slot details for matching

        Returns:
            Dict with action and extracted info
        """
        # Build conversation context
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:200]}"
            for msg in conversation_history[-3:]  # Last 3 messages
        ])

        # Format slots for the prompt
        slots_text = ""
        if slots:
            slots_text = "\nProposed Time Slots:\n"
            for i, slot in enumerate(slots, 1):
                slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
                slots_text += f"  Slot {i}: {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}\n"

        prompt = f"""You are analyzing a candidate's reply to an interview scheduling email.

{slots_text}
Candidate's Latest Reply:
---
{reply_text}
---

## CRITICAL RULE: DECLINE Detection
If the candidate says ANYTHING like:
- "I am not interested" or "not interested" or "not interested in this position"
- "I am no longer interested" or "no longer interested"
- "I decline" or "declining" or "I withdraw"
- "I am going with another company" or "accepted another offer"
- "Please remove me" or "unsubscribe"
- "I don't want to proceed" or "not moving forward"

Then you MUST return: action="decline"

## ACCEPT_SLOT Detection
Only if the candidate explicitly selects a time slot:
- "Option 1" or "Slot 1" or "first option"
- "I prefer option 2" or "I'll take slot 3"
- "I will be available at [time]" or "Monday works" or "Friday at 9am"
- "Option 5" or "the last one"

## IMPORTANT EXAMPLES:
- "I am not interested in this position" → decline
- "I will be available at Monday 9am" → accept_slot
- "No thanks, I found another job" → decline
- "Option 3 works for me" → accept_slot
- "I am no longer interested, thanks" → decline

Respond ONLY with JSON:
{{"action": "decline|accept_slot|request_alternative|ask_question|unclear", "slot_number": null or 1-5, "reason": null or "string", "confidence": "high|medium|low"}}

Respond in JSON format:
{{
    "action": "decline|accept_slot|request_alternative|ask_question|unclear",
    "slot_number": <slot number (1-5) if accepting, null otherwise>,
    "reason": "<reason if declining or requesting alternative>",
    "question": "<question if asking>",
    "confidence": "high|medium|low"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        intent = json.loads(content)
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
            # Slot no longer available - get NEW available slots and propose them
            # Release the proposed slots first
            await calendar_service.release_proposed_slots(db, candidate.id)

            # Get fresh available slots
            available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)

            if available_slots:
                # Propose the new available slots
                slot_ids = [slot.id for slot in available_slots]
                proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

                # Generate response with new slots
                response = await self._generate_alternative_slots_email(
                    candidate.name or candidate.email,
                    job.title,
                    proposed_slots,
                    "The slot you selected was just booked. Here are other available times:"
                )

                # Update conversation
                conversation.proposed_slots = slot_ids
                conversation.conversation_state = "proposing_times"
            else:
                # No slots available at all
                response = await self._generate_no_slots_message(candidate.name or candidate.email, job.title)
                conversation.conversation_state = "awaiting_slots"
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

        # Send email with threading - use same subject as original for proper threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        # Use same subject as original email for Gmail threading
        original_subject = "Interview Invitation - " + job.title

        # DEBUG LOGGING
        logger.info(f"[THREAD_DEBUG] reply_message_id: {reply_message_id}")
        logger.info(f"[THREAD_DEBUG] in_reply_to: {in_reply_to}")
        logger.info(f"[THREAD_DEBUG] references: {references}")
        logger.info(f"[THREAD_DEBUG] subject: {original_subject}")

        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=original_subject,
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        # Update conversation history
        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": gmail_msg_id
        })
        conversation.last_message_id = gmail_msg_id

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
        gmail_msg_id, thread_id = gmail_service.send_email(
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
            "message_id": gmail_msg_id
        })
        conversation.last_message_id = gmail_msg_id

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
        gmail_msg_id, thread_id = gmail_service.send_email(
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
            "message_id": gmail_msg_id
        })
        conversation.last_message_id = gmail_msg_id

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
        gmail_msg_id, thread_id = gmail_service.send_email(
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
            "message_id": gmail_msg_id
        })
        conversation.last_message_id = gmail_msg_id

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
        gmail_msg_id, thread_id = gmail_service.send_email(
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
            "message_id": gmail_msg_id
        })
        conversation.last_message_id = gmail_msg_id

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

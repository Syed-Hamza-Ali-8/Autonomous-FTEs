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
import pytz

load_dotenv()
logger = logging.getLogger(__name__)


def _ensure_msg_id_format(msg_id: str) -> str:
    """Ensure Message-ID has angle brackets for proper threading."""
    if not msg_id:
        return ""
    return msg_id if msg_id.startswith("<") else f"<{msg_id}>"


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

        # Detect candidate's timezone
        candidate_timezone = candidate.timezone
        if not candidate_timezone:
            candidate_timezone = calendar_service.detect_timezone_from_email(candidate.email)
            # Store detected timezone
            candidate.timezone = candidate_timezone
            await db.commit()

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

        # Generate creative email using LLM with timezone-aware slots
        email_body = await self._generate_initial_scheduling_email(
            candidate_name=candidate.name or candidate.email,
            job_title=job.title,
            slots=proposed_slots,
            candidate_timezone=candidate_timezone
        )

        # Send email
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=email_body
        )

        # Update conversation with message ID (ensure angle brackets for threading)
        msg_id = gmail_msg_id if gmail_msg_id.startswith("<") else f"<{gmail_msg_id}>"
        conversation.last_message_id = msg_id
        conversation.conversation_history.append({
            "role": "assistant",
            "content": email_body,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": msg_id
        })
        await db.commit()

        logger.info(f"Initiated scheduling for candidate {candidate_id}, timezone: {candidate_timezone}, message ID: {gmail_msg_id}")
        return gmail_msg_id

    async def _create_default_slots(self, db, job_id: int, company_id: int = 1) -> list:
        """Create default interview slots for next 5 weekdays."""
        from sqlalchemy import select
        slots = []
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)  # Make timezone-aware
        times = ["10:00", "11:00", "14:00", "15:00", "16:00"]
        day = 1
        slot_time_idx = 0
        created = []
        while len(created) < 5 and day < 14:
            candidate_date = now + timedelta(days=day)
            if candidate_date.weekday() < 5:  # Weekday
                time_str = times[slot_time_idx % len(times)]
                hour, minute = map(int, time_str.split(":"))
                # Create timezone-aware datetime
                start = candidate_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                end = start + timedelta(minutes=45)
                # Store as UTC
                slot = InterviewSlot(
                    company_id=company_id,
                    job_id=job_id,
                    start_time=start.astimezone(pytz.UTC),
                    end_time=end.astimezone(pytz.UTC),
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

    async def _fetch_ordered_slots(self, db: AsyncSession, proposed_slots: list) -> list:
        """
        Fetch InterviewSlot rows for the given IDs, preserving the exact order of
        `proposed_slots`.

        SQL `IN (...)` does NOT guarantee result order, but the slot NUMBER shown to
        the candidate, the number the intent LLM reasons about, and the index used in
        `proposed_slots[slot_number - 1]` must all refer to the same slot. Sorting the
        fetched rows back into `proposed_slots` order keeps them consistent.
        """
        if not proposed_slots:
            return []
        slot_query = select(InterviewSlot).where(InterviewSlot.id.in_(proposed_slots))
        slot_result = await db.execute(slot_query)
        slots_by_id = {slot.id: slot for slot in slot_result.scalars().all()}
        # Preserve proposed_slots order; skip any IDs that no longer exist.
        return [slots_by_id[sid] for sid in proposed_slots if sid in slots_by_id]

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
                    "awaiting_timezone", "awaiting_questions_reply", "proposing_times", "awaiting_confirmation", "rescheduling", "confirmed"
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

        # Detect/update candidate timezone
        candidate_timezone = candidate.timezone
        if not candidate_timezone:
            candidate_timezone = calendar_service.detect_timezone_from_email(candidate.email)
            candidate.timezone = candidate_timezone
            await db.commit()

        # Also check if candidate mentioned their timezone in the reply
        detected_tz = calendar_service.extract_timezone_from_text(reply_text)
        if detected_tz and detected_tz != candidate_timezone:
            candidate_timezone = detected_tz
            candidate.timezone = detected_tz
            await db.commit()
            logger.info(f"Updated candidate {candidate_id} timezone to {detected_tz} based on reply text")

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

        # Check if awaiting timezone (first step)
        if conversation.conversation_state == "awaiting_timezone":
            # Extract timezone from reply and send time slots
            await self._handle_timezone_reply(db, conversation, candidate, job, reply_text, reply_message_id)
            return

        # Check if awaiting questions reply
        if conversation.conversation_state == "awaiting_questions_reply":
            # Analyze questions reply and send time slots
            await self._handle_questions_reply(db, conversation, candidate, job, reply_text, reply_message_id)
            return

        # Get slot details for intent analysis (in proposed_slots order)
        slots = await self._fetch_ordered_slots(db, conversation.proposed_slots)

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

        # Analyze reply using LLM to understand intent (with timezone awareness)
        intent = await self._analyze_intent_after_questions(
            reply_text=reply_text,
            conversation_history=conversation.conversation_history,
            proposed_slots=conversation.proposed_slots,
            slots=slots,
            candidate_timezone=candidate_timezone
        )

        # Update timezone if detected from LLM analysis
        if intent.get("detected_timezone"):
            candidate.timezone = intent["detected_timezone"]
            candidate_timezone = intent["detected_timezone"]
            await db.commit()

        logger.info(f"Candidate {candidate_id} intent: {intent['action']}, timezone: {candidate_timezone}")

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
                db, conversation, candidate, job, intent, reply_message_id, reply_text
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
        slots: List[InterviewSlot],
        candidate_timezone: str = "UTC"
    ) -> str:
        """
        Generate creative initial scheduling email using LLM.

        Args:
            candidate_name: Candidate's name
            job_title: Job title
            slots: List of available slots
            candidate_timezone: Candidate's timezone for display

        Returns:
            Email body text
        """
        # Format slots for display in candidate's local timezone
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone=candidate_timezone)
            tz_abbr = slot.start_time.astimezone(pytz.timezone(candidate_timezone)).tzname()
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {tz_abbr}")

        slots_text = "\n".join(formatted_slots)

        prompt = f"""You are an AI recruiting assistant. Generate a warm, professional, and creative email inviting a candidate for an interview.

Candidate Name: {candidate_name}
Job Title: {job_title}

Available Time Slots (shown in your local timezone):
{slots_text}

Requirements:
- Be warm and enthusiastic (they were approved!)
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them. Slot 1 must stay slot 1, etc.
- Present the time slots clearly in their local timezone
- Ask them to choose one of the listed times by its option number (e.g., "Option 1")
- Do NOT invite them to suggest a different/custom time. Interviews can only be booked at one of the listed times, so ask them to pick from the options above.
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

    async def _generate_approval_email_no_questions(
        self,
        candidate_name: str,
        job_title: str,
        slots_text: str
    ) -> str:
        """Generate interview-invitation email with time slots only (no screening questions)."""

        prompt = f"""You are an AI recruiting assistant. Generate a warm, professional email inviting a candidate for an interview.

Candidate Name: {candidate_name}
Job Title: {job_title}

Available Time Slots (shown in your local timezone):
{slots_text}

Requirements:
- Start with congratulations on being selected for interview
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them. Slot 1 must stay slot 1, etc.
- Present the time slots clearly - these are shown in UTC
- IMPORTANT: The times above are shown in UTC. If this is not the candidate's local timezone, ask them to tell us their timezone in their reply (e.g., "I'm in IST", "I'm in PKT", "I'm in EST", "I'm in PST")
- Ask them to choose one of the listed times by its option number (Option 1, Option 2, etc.)
- Tell them to reply with: (1) their timezone if different from UTC, (2) their preferred time slot number
- Do NOT include or ask any screening questions
- Do NOT invite them to suggest a different/custom time. Interviews can only be booked at one of the listed times, so ask them to pick from the options above.
- Be warm and enthusiastic
- Keep it professional but friendly
- Sign off as "AI Recruiting Assistant"

Generate the email body (no subject line):"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()

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

Available Time Slots (shown in your local timezone):
{slots_text}

Screening Questions (include these in the email):
{questions_text}

Requirements:
- Start with congratulations on being selected for interview
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them. Slot 1 must stay slot 1, etc.
- Present the time slots clearly - these are shown in your local timezone
- IMPORTANT: The times above are shown in UTC. If this is not your local timezone, please tell us your timezone in your reply (e.g., "I'm in IST", "I'm in PKT", "I'm in EST", "I'm in PST")
- Ask them to choose one of the listed times by its option number (Option 1, Option 2, etc.)
- Include the screening questions they need to answer via email reply
- Tell them to reply with: (1) their timezone if different from UTC, (2) their preferred time slot number, (3) answers to screening questions
- Do NOT invite them to suggest a different/custom time. Interviews can only be booked at one of the listed times, so ask them to pick from the options above.
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

    async def _generate_timezone_request_email(
        self,
        candidate_name: str,
        job_title: str,
        questions: List[str]
    ) -> str:
        """Generate email asking for candidate's timezone before showing times."""

        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        prompt = f"""You are an AI recruiting assistant. Generate a warm, professional email that:

1. Congratulates the candidate on being selected for an interview
2. Asks them to tell us their timezone FIRST (before we show interview times)
3. Includes screening questions they need to answer

Candidate Name: {candidate_name}
Job Title: {job_title}

Screening Questions:
{questions_text}

Requirements:
- Be warm and enthusiastic
- IMPORTANT: Tell them we want to show interview times in THEIR local timezone
- Ask them to reply with: (1) their timezone (e.g., "I'm in PKT", "I'm in EST", "I'm in IST"), (2) answers to screening questions
- Don't show any time slots yet - we need their timezone first
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

    async def _handle_timezone_reply(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        reply_text: str,
        reply_message_id: str = ""
    ):
        """Handle candidate's reply with their timezone - send time slots in their timezone."""
        import pytz

        # Extract timezone from reply
        detected_tz = calendar_service.extract_timezone_from_text(reply_text)

        if not detected_tz:
            # No timezone found - ask again
            logger.info(f"No timezone detected from reply for candidate {candidate.id}")
            response = await self._generate_ask_timezone_again_email(
                candidate.name or candidate.email,
                job.title
            )
            in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
            gmail_service.send_email(
                to=candidate.email,
                subject=f"Interview Invitation - {job.title}",
                body=response,
                in_reply_to=in_reply_to,
                references=references
            )
            return

        # Update candidate timezone
        candidate.timezone = detected_tz
        await db.commit()
        logger.info(f"Detected timezone {detected_tz} for candidate {candidate.id}")

        # Get slot details (in proposed_slots order)
        slots = await self._fetch_ordered_slots(db, conversation.proposed_slots)

        # Format slots in candidate's timezone
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone=detected_tz)
            tz_abbr = slot.start_time.astimezone(pytz.timezone(detected_tz)).tzname()
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {tz_abbr}")

        slots_text = "\n".join(formatted_slots)

        # Generate email with slots in candidate's timezone
        response = await self._generate_slots_in_timezone_email(
            candidate_name=candidate.name or candidate.email,
            job_title=job.title,
            slots_text=slots_text,
            timezone=detected_tz
        )

        # Update conversation state
        conversation.conversation_state = "awaiting_confirmation"

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)

        # Debug logging
        logger.info(f"[THREADING] In-Reply-To: {in_reply_to}")
        logger.info(f"[THREADING] References: {references[:100]}...")

        gmail_msg_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        # Update conversation history (ensure angle brackets for threading)
        msg_id = _ensure_msg_id_format(gmail_msg_id)
        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": msg_id
        })
        conversation.last_message_id = msg_id
        await db.commit()

        logger.info(f"Sent timezone-aware slots to candidate {candidate.id}")

    async def _generate_ask_timezone_again_email(
        self,
        candidate_name: str,
        job_title: str
    ) -> str:
        """Generate email asking for timezone again."""
        prompt = f"""Generate a friendly email asking for the candidate's timezone.

Candidate: {candidate_name}
Job: {job_title}

Requirements:
- Apologize that we couldn't detect their timezone
- Ask them to simply reply with their timezone (e.g., "I'm in PKT", "I'm in EST", "I'm in IST")
- Tell them we want to show interview times in their local timezone
- Be warm and helpful
- Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()

    async def _generate_slots_in_timezone_email(
        self,
        candidate_name: str,
        job_title: str,
        slots_text: str,
        timezone: str
    ) -> str:
        """Generate email with time slots in candidate's timezone."""
        prompt = f"""Generate a warm, professional email showing interview time slots.

Candidate: {candidate_name}
Job: {job_title}

Time Slots (shown in {timezone}):
{slots_text}

Requirements:
- Thank them for providing their timezone
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them. Slot 1 must stay slot 1, etc.
- Show the time slots clearly in their local timezone ({timezone})
- Ask them to choose one of the listed times by its option number (Option 1, Option 2, etc.)
- Do NOT invite them to suggest a different/custom time. Interviews can only be booked at one of the listed times.
- Be warm and professional
- Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()

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

        # Get slot details (in proposed_slots order)
        slots = await self._fetch_ordered_slots(db, conversation.proposed_slots)

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

        # Get candidate timezone (may have been updated from reply)
        candidate_timezone = candidate.timezone or "UTC"

        # No slot selection found - send time slots email
        # Format slots for email in candidate's timezone
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone=candidate_timezone)
            tz_abbr = slot.start_time.astimezone(pytz.timezone(candidate_timezone)).tzname()
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {tz_abbr}")

        slots_text = "\n".join(formatted_slots)

        # Generate time slots email
        prompt = f"""You are an AI recruiting assistant. Thank the candidate for answering screening questions and provide available interview time slots.

Candidate Name: {candidate.name or candidate.email}
Job Title: {job.title}

Available Time Slots (shown in your local timezone):
{slots_text}

Requirements:
- Thank them for answering the screening questions
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them. Slot 1 must stay slot 1, etc.
- Present the time slots clearly in their local timezone
- If the times are in UTC, remind them to tell us their timezone if different
- Ask them to reply with their preferred slot number (1-5)
- Do NOT invite them to suggest a different/custom time. Interviews can only be booked at one of the listed times.
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

        # Build threading headers to keep emails in same thread
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)

        # Send email with proper threading
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=email_body,
            in_reply_to=in_reply_to,
            references=references
        )

        # Update conversation with new message
        msg_id = gmail_msg_id if gmail_msg_id.startswith("<") else f"<{gmail_msg_id}>"
        conversation.conversation_history.append({
            "role": "assistant",
            "content": email_body[:500],
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": msg_id
        })
        conversation.last_message_id = msg_id

        # Update conversation state
        conversation.conversation_state = "proposing_times"
        await db.commit()

        logger.info(f"Sent time slots to {candidate.email} for candidate {candidate.id}")

    async def _analyze_intent_after_questions(
        self,
        reply_text: str,
        conversation_history: List[Dict],
        proposed_slots: List[int],
        slots: List[InterviewSlot] = None,
        candidate_timezone: str = "UTC"
    ) -> Dict:
        """
        Analyze candidate's reply to understand their intent using LLM.

        Args:
            reply_text: Candidate's reply
            conversation_history: Previous conversation
            proposed_slots: Slot IDs that were proposed
            slots: Slot details for matching
            candidate_timezone: Candidate's timezone for time display

        Returns:
            Dict with action and extracted info
        """
        # Build conversation context
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:200]}"
            for msg in conversation_history[-3:]  # Last 3 messages
        ])

        # Format slots for the prompt in candidate's timezone
        slots_text = ""
        if slots:
            slots_text = "\nProposed Time Slots:\n"
            for i, slot in enumerate(slots, 1):
                slot_info = calendar_service.format_slot_for_display(slot, display_timezone=candidate_timezone)
                tz_abbr = slot.start_time.astimezone(pytz.timezone(candidate_timezone)).tzname()
                slots_text += f"  Slot {i}: {slot_info['date']} at {slot_info['time']} {tz_abbr}\n"

        # Detect if candidate mentioned a specific time/day
        suggested_time = calendar_service.parse_candidate_suggested_time(reply_text)
        timezone_detected = calendar_service.extract_timezone_from_text(reply_text)

        suggested_time_text = ""
        if suggested_time:
            suggested_time_text = f"\nCandidate suggested time: {suggested_time['start_time'].strftime('%A, %B %d at %I:%M %p')} UTC"
        if timezone_detected:
            suggested_time_text += f"\nTimezone detected from text: {timezone_detected}"

        prompt = f"""You are analyzing a candidate's reply to an interview scheduling email.

{slots_text}
Candidate's Latest Reply:
---
{reply_text}
---{suggested_time_text}

## CRITICAL RULE: DECLINE Detection
If the candidate says ANYTHING like:
- "I am not interested" or "not interested" or "not interested in this position"
- "I am no longer interested" or "no longer interested"
- "I decline" or "declining" or "I withdraw"
- "I am going with another company" or "accepted another offer"
- "Please remove me" or "unsubscribe"
- "I don't want to proceed" or "not moving forward"

Then you MUST return: action="decline"

## ACCEPT_SLOT Detection - CRITICAL MATCHING RULES
A candidate is accepting a slot if EITHER:
1. They explicitly reference a slot number: "Option 1", "Slot 3", "the second one", "number 5"
2. They mention a date/time that EXACTLY MATCHES one of the proposed slots above

MATCHING RULES:
- Compare the candidate's stated day (Monday, Tuesday, etc.) and time (3:00 PM, 5:00 PM, etc.)
- If it matches ANY of the proposed slots, that's an acceptance → return accept_slot with the matching slot_number
- Ignore minor time format differences (3PM vs 03:00 PM vs 15:00)
- If they say "Tuesday at 5PM" and Slot 5 is "Tuesday at 05:00 PM", that's a MATCH

EXAMPLES OF SLOT ACCEPTANCE:
- "Option 3 works" → accept_slot (slot_number: 3)
- "I'll take slot 2" → accept_slot (slot_number: 2)
- "Tuesday, July 21 at 05:00 PM" (matches Slot 5) → accept_slot (slot_number: 5)
- "Monday at 3PM" (matches Slot 1) → accept_slot (slot_number: 1)
- "I want Wednesday at 7PM" (matches Slot 3) → accept_slot (slot_number: 3)

## ASK_QUESTION Detection
If the candidate is ASKING for information rather than choosing/suggesting a time, return action="ask_question".
This includes any interrogative that is not about picking a slot:
- "What type of questions will be asked in the interview?" → ask_question
- "Who will I be interviewing with?" → ask_question
- "How long is the interview?" / "Is it technical?" → ask_question
- "Can you tell me more about the role?" → ask_question
A message with a question mark and NO specific day/time is almost always ask_question, NOT request_alternative.

## REQUEST_ALTERNATIVE Detection
Only if the candidate suggests a SPECIFIC time that does NOT match any proposed slot:
- "Friday 3pm" (not in the list) → request_alternative
- "Tuesday at 2pm" (if no slot at 2pm) → request_alternative
- "Next week Monday" (vague, not specific match) → request_alternative
Do NOT use request_alternative for questions that contain no day/time.

## IMPORTANT EXAMPLES:
- "I am not interested in this position" → decline
- "Option 3 works for me" → accept_slot (slot_number: 3)
- "What type of questions will be asked?" → ask_question
- "Tuesday, July 21 at 5:00 PM - 5:45 PM" (if this matches Slot 5) → accept_slot (slot_number: 5)
- "No thanks, I found another job" → decline
- "Can we do Friday afternoon?" (not in slots) → request_alternative
- "I prefer Monday morning" (vague, not specific slot match) → request_alternative
- "What about Tuesday at 2pm?" (if no 2pm slot) → request_alternative
- "I am no longer interested, thanks" → decline

Respond ONLY with valid JSON:
{{
    "action": "decline|accept_slot|request_alternative|ask_question|unclear",
    "slot_number": <slot number (1-5) if accepting, null otherwise>,
    "reason": "<reason if declining or requesting alternative>",
    "question": "<question if asking>",
    "suggested_time": "<candidate's suggested time if any>",
    "confidence": "high|medium|low"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = (response.choices[0].message.content or "").strip()
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            intent = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # The LLM returned empty or non-JSON content. Don't crash and silently
            # drop the candidate's reply — fall back to "unclear" so they get a
            # clarification email and the reply is still handled.
            logger.error(
                f"Intent analysis returned unparseable content (len={len(content)}): "
                f"{content[:300]!r}. Falling back to 'unclear'."
            )
            intent = {
                "action": "unclear",
                "slot_number": None,
                "reason": "Could not parse intent from reply",
                "question": None,
                "suggested_time": None,
                "confidence": "low",
            }

        # If timezone was detected from text, add it to intent
        if timezone_detected:
            intent["detected_timezone"] = timezone_detected

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
            # No explicit slot number in the reply. If the candidate is ALREADY
            # confirmed (e.g. a bare "ok sure sounds good" after we sent the
            # confirmation), don't ask them to pick again - treat it as an
            # acknowledgement of their existing booking and default to that slot.
            if conversation.confirmed_slot_id:
                slot_number = None
                # Resolve the confirmed slot's option number so the rest of the
                # flow (which indexes proposed_slots) stays consistent.
                if conversation.confirmed_slot_id in (conversation.proposed_slots or []):
                    slot_number = conversation.proposed_slots.index(conversation.confirmed_slot_id) + 1
                if slot_number:
                    logger.info(
                        f"Candidate {candidate.id} sent a bare affirmation while already "
                        f"confirmed on slot {conversation.confirmed_slot_id}; re-confirming it."
                    )
                    intent["slot_number"] = slot_number
                else:
                    # Confirmed slot isn't in the proposed list anymore - just clarify.
                    await self._handle_unclear_intent(db, conversation, candidate, job)
                    return
            else:
                # Invalid slot number - ask for clarification
                await self._handle_unclear_intent(db, conversation, candidate, job)
                return

        # Get the slot ID
        slot_id = conversation.proposed_slots[slot_number - 1]

        # If the candidate had already confirmed a different slot (re-accept /
        # reschedule onto another listed slot), release the old booking first so
        # it doesn't stay orphaned as 'booked'.
        if conversation.confirmed_slot_id and conversation.confirmed_slot_id != slot_id:
            await calendar_service.cancel_slot(db, conversation.confirmed_slot_id)
            logger.info(
                f"Released previously confirmed slot {conversation.confirmed_slot_id} "
                f"for candidate {candidate.id} before booking slot {slot_id}"
            )
            conversation.confirmed_slot_id = None

        # Book the slot
        booked_slot = await calendar_service.book_slot(
            db, slot_id, candidate.id
        )

        if not booked_slot:
            # Slot no longer available - get NEW available slots (excluding currently proposed ones)
            candidate_timezone = candidate.timezone or "UTC"

            # Get available slots excluding the ones currently proposed to this candidate
            all_available = await calendar_service.get_available_slots(db, job.id, limit=20)

            # Filter out slots that are currently proposed to this candidate
            new_available_slots = [
                slot for slot in all_available
                if slot.id not in conversation.proposed_slots
            ][:5]  # Take top 5

            if new_available_slots:
                # NOW release the old proposed slots before proposing new ones
                await calendar_service.release_proposed_slots(db, candidate.id)

                # Propose the new available slots
                slot_ids = [slot.id for slot in new_available_slots]
                proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

                # Generate response with new slots
                response = await self._generate_alternative_slots_email(
                    candidate.name or candidate.email,
                    job.title,
                    proposed_slots,
                    "The slot you selected was just booked. Here are other available times:",
                    candidate_timezone
                )

                # Update conversation
                conversation.proposed_slots = slot_ids
                conversation.conversation_state = "proposing_times"
            else:
                # No NEW slots available - apologize
                response = self._generate_no_slots_message(candidate.name or candidate.email, job.title)
                conversation.conversation_state = "rescheduling"
        else:
            # Reuse an existing meeting link if this slot was already booked (idempotent
            # re-accept) - otherwise create a real Google Meet link via the Calendar API.
            # Without this guard, a repeated "yes/ok" would create a duplicate calendar event.
            if booked_slot.meeting_link:
                meeting_link = booked_slot.meeting_link
            else:
                meeting_link = calendar_service.generate_google_meet_link(
                    booked_slot,
                    candidate_email=candidate.email,
                    candidate_name=candidate.name,
                    job_title=job.title,
                )
                if not meeting_link:
                    # Meet link creation failed - fall back to a placeholder note so the
                    # candidate still gets confirmation; recruiter can send a link manually.
                    logger.error(
                        f"Could not create Meet link for candidate {candidate.id}; "
                        "sending confirmation without a link."
                    )
                    meeting_link = "A meeting link will follow shortly."
                booked_slot.meeting_link = meeting_link
                await db.commit()

            # Get candidate timezone for display
            candidate_timezone = candidate.timezone or "UTC"

            # Generate confirmation email with meeting link
            slot_info = calendar_service.format_slot_for_display(booked_slot, display_timezone=candidate_timezone)
            response = await self._generate_confirmation_email(
                candidate.name or candidate.email,
                job.title,
                slot_info,
                meeting_link
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

        # Update conversation history (ensure angle brackets for threading)
        msg_id = _ensure_msg_id_format(gmail_msg_id)
        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": msg_id
        })
        conversation.last_message_id = msg_id

        logger.info(f"Confirmed interview slot {slot_id} for candidate {candidate.id}")

    async def _handle_alternative_request(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        intent: Dict,
        reply_message_id: str = "",
        reply_text: str = ""
    ):
        """
        Handle candidate requesting alternative times.

        If candidate suggests a time, check if it's within working hours.
        If YES: Try to create a slot at their suggested time.
        If NO: Show their suggested time + alternatives that ARE within working hours.
        """
        # Get candidate timezone
        candidate_timezone = candidate.timezone or "UTC"

        # Try to parse candidate's suggested time from their reply text.
        # Parse in the candidate's own timezone so "4 PM" means 4 PM PKT, not UTC.
        # IMPORTANT: only parse from the candidate's ACTUAL reply text - never from
        # the LLM's `reason` field, which can hallucinate a time the candidate never
        # mentioned (that produced bogus "accommodated" slots on misclassified replies).
        suggested_time = calendar_service.parse_candidate_suggested_time(
            reply_text or "", company_timezone=candidate_timezone
        )

        # Fetch the slots we ACTUALLY offered this candidate, in the order shown.
        # The candidate may ONLY choose from these times - we never create a slot at
        # an arbitrary time they invent (e.g. "Friday at 5 PM" when that was never
        # offered). If their suggestion matches one of the offered slots, book it;
        # otherwise re-present the same offered slots and ask them to pick one.
        shown_slots = await self._fetch_ordered_slots(db, conversation.proposed_slots)

        # If the candidate's suggested time coincides with one of the offered slots,
        # treat it as an acceptance of that slot (they typed the time instead of the
        # option number). _handle_slot_acceptance handles releasing any previously
        # confirmed slot, booking, the Meet link, and the confirmation email.
        if suggested_time and shown_slots:
            for idx, slot in enumerate(shown_slots, 1):
                # Match within 15 minutes of an offered slot's start time (both UTC).
                if abs((slot.start_time - suggested_time["start_time"]).total_seconds()) < 900:
                    logger.info(
                        f"Candidate {candidate.id} suggested a time matching offered "
                        f"slot {slot.id} (option {idx}); booking it."
                    )
                    intent["slot_number"] = idx
                    await self._handle_slot_acceptance(
                        db, conversation, candidate, job, intent, reply_message_id
                    )
                    return

        # The requested time is NOT one of the offered slots. Do NOT accept or
        # fabricate it. Re-present the offered slots and ask them to choose one.
        # We deliberately leave any existing confirmed_slot_id booking intact so the
        # candidate doesn't lose a confirmed interview by asking about an unavailable time.
        if shown_slots:
            # Keep the offered slots reserved for this candidate (re-propose any that
            # were released; already-proposed/booked ones are left untouched).
            reservable_ids = [s.id for s in shown_slots if s.status == "available"]
            if reservable_ids:
                await calendar_service.propose_slots(db, reservable_ids, candidate.id)

            response = await self._generate_alternative_slots_email(
                candidate.name or candidate.email,
                job.title,
                shown_slots,
                intent.get("reason"),
                candidate_timezone,
                suggested_time
            )

            conversation.proposed_slots = [s.id for s in shown_slots]
            conversation.conversation_state = "proposing_times"
        else:
            # No record of previously offered slots - fall back to current availability.
            available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)
            if not available_slots:
                response = self._generate_no_slots_message(candidate.name or candidate.email, job.title)
            else:
                slot_ids = [slot.id for slot in available_slots]
                proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)
                response = await self._generate_alternative_slots_email(
                    candidate.name or candidate.email,
                    job.title,
                    proposed_slots,
                    intent.get("reason"),
                    candidate_timezone,
                    suggested_time
                )
                conversation.proposed_slots = slot_ids
                conversation.conversation_state = "proposing_times"

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": _ensure_msg_id_format(gmail_msg_id)
        })
        conversation.last_message_id = _ensure_msg_id_format(gmail_msg_id)
        await db.commit()

        logger.info(f"Offered alternative slots to candidate {candidate.id} (suggested time not in offered slots)")

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
            subject=f"Interview Invitation - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": _ensure_msg_id_format(gmail_msg_id)
        })
        conversation.last_message_id = _ensure_msg_id_format(gmail_msg_id)

    async def _handle_decline(
        self,
        db: AsyncSession,
        conversation: SchedulingConversation,
        candidate: Candidate,
        job: Job,
        reply_message_id: str = ""
    ):
        """Handle candidate declining the interview."""
        # If the candidate had already confirmed a slot, cancel that booked slot so
        # it frees up again (release_proposed_slots only touches status == "proposed",
        # so a booked slot would otherwise stay booked on a decline).
        if conversation.confirmed_slot_id:
            await calendar_service.cancel_slot(db, conversation.confirmed_slot_id)
            logger.info(
                f"Released previously confirmed slot {conversation.confirmed_slot_id} "
                f"on decline for candidate {candidate.id}"
            )
            conversation.confirmed_slot_id = None

        # Release proposed slots
        await calendar_service.release_proposed_slots(db, candidate.id)

        # Generate polite response
        response = await self._generate_decline_response(candidate.name or candidate.email, job.title)

        # Send email with threading
        in_reply_to, references = self._build_threading_headers(conversation, reply_message_id)
        gmail_msg_id, thread_id = gmail_service.send_email(
            to=candidate.email,
            subject=f"Interview Invitation - {job.title}",
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
            "message_id": _ensure_msg_id_format(gmail_msg_id)
        })
        conversation.last_message_id = _ensure_msg_id_format(gmail_msg_id)

        # Persist the cancellation. The decline keyword-bypass paths in
        # handle_scheduling_reply `return` before the trailing db.commit(), so
        # without this commit the state change ("cancelled") would be rolled back.
        await db.commit()

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
            subject=f"Interview Invitation - {job.title}",
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

        conversation.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": _ensure_msg_id_format(gmail_msg_id)
        })
        conversation.last_message_id = _ensure_msg_id_format(gmail_msg_id)

    async def _generate_confirmation_email(
        self,
        candidate_name: str,
        job_title: str,
        slot_info: Dict,
        meeting_link: str = None
    ) -> str:
        """Generate creative confirmation email with meeting link."""
        meeting_section = ""
        if meeting_link:
            meeting_section = f"""
Meeting Link: {meeting_link}

Note: You can join the interview using this link at the scheduled time."""

        prompt = f"""Generate a warm, professional interview confirmation email.

Candidate: {candidate_name}
Job: {job_title}
Confirmed Time: {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}{meeting_section}

Include:
- Confirmation of the time
- What to expect (45-minute technical interview)
- Meeting link (include it prominently)
- Remind them to join 5 minutes early
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
        reason: Optional[str],
        candidate_timezone: str = "UTC",
        suggested_time: Optional[Dict] = None
    ) -> str:
        """Generate email with alternative time slots."""
        # Format slots in candidate's timezone
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            slot_info = calendar_service.format_slot_for_display(slot, display_timezone=candidate_timezone)
            tz_abbr = slot.start_time.astimezone(pytz.timezone(candidate_timezone)).tzname()
            formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {tz_abbr}")

        slots_text = "\n".join(formatted_slots)

        # Format candidate's suggestion if provided
        suggestion_text = ""
        if suggested_time:
            tz = pytz.timezone(candidate_timezone)
            local_time = suggested_time["start_time"].astimezone(tz)
            suggestion_text = f"\n\nYou requested: {local_time.strftime('%A, %B %d at %I:%M %p')} {local_time.tzname()}"

        prompt = f"""Generate a polite email explaining that the candidate's requested time is not available, and asking them to pick from our offered interview times.

Candidate: {candidate_name}
Job: {job_title}
{suggestion_text}

Our Available Interview Times (shown in your timezone):
{slots_text}

Guidelines:
- Warmly thank them for their response{" and acknowledge the time they requested" if suggested_time else ""}.
- Clearly but politely explain that the requested time is unfortunately NOT available, and that interviews can only be scheduled at one of the specific times listed above.
- Ask them to reply with the OPTION NUMBER of whichever listed time works best for them.
- Do NOT invite them to propose a different/custom time, and do NOT imply we can create a new time outside the list.
- CRITICAL: List the time slots in the EXACT SAME ORDER and with the EXACT SAME NUMBERS as shown above. Do NOT reorder, sort, or renumber them.
- Sign as "AI Recruiting Assistant"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    async def _generate_accommodate_request_email(
        self,
        candidate_name: str,
        job_title: str,
        slots: List[InterviewSlot],
        candidate_timezone: str,
        suggested_time: Dict
    ) -> str:
        """Generate email when we CAN accommodate candidate's preferred time."""
        # Format the slot in candidate's timezone
        slot = slots[0]
        slot_info = calendar_service.format_slot_for_display(slot, display_timezone=candidate_timezone)
        tz_abbr = slot.start_time.astimezone(pytz.timezone(candidate_timezone)).tzname()
        confirmed_time = f"{slot_info['date']} at {slot_info['time']} {tz_abbr}"

        prompt = f"""Generate an enthusiastic email confirming we can accommodate the candidate's preferred time!

Candidate: {candidate_name}
Job: {job_title}
Their preferred time: {confirmed_time}

Requirements:
- Be excited that we can accommodate their schedule!
- Confirm the exact time in their timezone
- Ask them to reply confirming "Yes" to lock in the time
- Keep it warm and professional
- Sign as "AI Recruiting Assistant"."""

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
- Choose one of the numbered time slots by its option number
- Or let you know if they have questions

Note: interviews can only be booked at one of the listed times, so do NOT invite them to propose a different/custom time.
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

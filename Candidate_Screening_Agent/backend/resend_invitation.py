"""
Resend interview invitation email to candidate.
Run: cd backend && source .venv/bin/activate && python resend_invitation.py
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Candidate, SchedulingConversation
from db.database import AsyncSessionLocal
from db import crud
from services.gmail_service import gmail_service
from services.scheduling_agent import scheduling_agent
from services.calendar_service import calendar_service
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def resend_invitation(email: str):
    """Resend interview invitation to candidate."""
    async with AsyncSessionLocal() as db:
        # Find candidate
        query = select(Candidate).where(Candidate.email == email)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            print(f"❌ No candidate found with email: {email}")
            return False

        # Get job
        job = await crud.get_job(db, candidate.job_id)
        if not job:
            print(f"❌ Job not found for candidate")
            return False

        print(f"Candidate: {candidate.name} (ID: {candidate.id})")
        print(f"Job: {job.title}")

        try:
            # Get or create interview slots
            available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)
            if not available_slots:
                available_slots = await scheduling_agent._create_default_slots(
                    db, job.id, company_id=candidate.company_id
                )
                print(f"Created {len(available_slots)} default slots")

            slot_ids = [slot.id for slot in available_slots]
            proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

            # Get or create scheduling conversation
            conv_query = select(SchedulingConversation).where(
                SchedulingConversation.candidate_id == candidate.id,
                SchedulingConversation.conversation_state == "awaiting_questions_reply"
            ).order_by(SchedulingConversation.created_at.desc()).limit(1)
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                conversation = SchedulingConversation(
                    candidate_id=candidate.id,
                    job_id=job.id,
                    company_id=candidate.company_id,
                    conversation_state="awaiting_questions_reply",
                    proposed_slots=slot_ids,
                    conversation_history=[]
                )
                db.add(conversation)
                await db.commit()
                print("Created new scheduling conversation")
            else:
                conversation.proposed_slots = slot_ids
                await db.commit()
                print("Updated existing scheduling conversation")

            # Format slots for email
            formatted_slots = []
            for i, slot in enumerate(available_slots, 1):
                slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
                formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

            slots_text = "\n".join(formatted_slots)

            # Get screening questions
            questions = candidate.screening_questions or []

            # Generate email
            email_body = await scheduling_agent._generate_approval_email_with_questions(
                candidate_name=candidate.name or candidate.email,
                job_title=job.title,
                questions=questions,
                slots_text=slots_text
            )

            # Send email
            print(f"Sending email to {candidate.email}...")
            message_id = gmail_service.send_email(
                to=candidate.email,
                subject=f"Interview Invitation - {job.title}",
                body=email_body
            )

            candidate.gmail_message_id = message_id
            await db.commit()

            print(f"\n✅ SUCCESS! Email sent to {candidate.email}")
            print(f"   Message ID: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    email = "ha5755420@gmail.com"
    print(f"Resending invitation to: {email}\n")
    asyncio.run(resend_invitation(email))

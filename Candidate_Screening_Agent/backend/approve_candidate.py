"""
Approve a candidate and send interview invitation with screening questions.
Run: cd backend && source .venv/bin/activate && python approve_candidate.py
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Candidate, PendingApproval, Job, Company
from db.database import AsyncSessionLocal
from db import crud
from services.gmail_service import gmail_service
from screening_agent import generate_screening_questions
from services.scheduling_agent import scheduling_agent
from services import calendar_service
from db.models import SchedulingConversation
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def approve_and_invite(email: str):
    """Approve candidate and send interview invitation with screening questions."""
    async with AsyncSessionLocal() as db:
        # Find candidate
        query = select(Candidate).where(Candidate.email == email)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            print(f"❌ No candidate found with email: {email}")
            return False

        print(f"Found candidate: {candidate.name} (ID: {candidate.id})")
        print(f"  Status: {candidate.status}")
        print(f"  Score: {candidate.total_score}")

        # Find pending approval
        approval_query = select(PendingApproval).where(
            PendingApproval.candidate_id == candidate.id,
            PendingApproval.status == "pending"
        )
        approval_result = await db.execute(approval_query)
        approval = approval_result.scalar_one_or_none()

        if not approval:
            print(f"❌ No pending approval found for candidate {candidate.id}")
            return False

        print(f"Found pending approval ID: {approval.id}")

        # Get job
        job = await crud.get_job(db, candidate.job_id)
        company = await crud.get_company(db, candidate.company_id)
        print(f"Job: {job.title if job else 'Unknown'}")
        print(f"Company: {company.name if company else 'Unknown'}")

        # Approve the candidate
        await crud.approve_candidate(db, approval.id, "system@admin.com")
        print("✅ Candidate approved")

        try:
            # Generate screening questions
            questions = await generate_screening_questions(candidate.cv_text or "", job.rubric_path or "")
            await crud.update_candidate_questions(db, candidate.id, questions)
            print(f"✅ Generated {len(questions)} screening questions")

            # Create/get interview slots
            available_slots = await calendar_service.get_available_slots(db, job.id, limit=5)
            if not available_slots:
                available_slots = await scheduling_agent._create_default_slots(
                    db, job.id, company_id=candidate.company_id
                )
                print(f"✅ Created {len(available_slots)} default interview slots")
            else:
                print(f"✅ Found {len(available_slots)} existing interview slots")

            slot_ids = [slot.id for slot in available_slots]
            proposed_slots = await calendar_service.propose_slots(db, slot_ids, candidate.id)

            # Create scheduling conversation
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
            print("✅ Created scheduling conversation")

            # Format slots for email
            formatted_slots = []
            for i, slot in enumerate(available_slots, 1):
                slot_info = calendar_service.format_slot_for_display(slot, display_timezone="UTC")
                formatted_slots.append(f"{i}. {slot_info['date']} at {slot_info['time']} {slot_info['timezone']}")

            slots_text = "\n".join(formatted_slots)

            # Generate email with interview invitation + screening questions
            email_body = await scheduling_agent._generate_approval_email_with_questions(
                candidate_name=candidate.name or candidate.email,
                job_title=job.title,
                questions=questions,
                slots_text=slots_text
            )

            # Send email
            message_id = gmail_service.send_email(
                to=candidate.email,
                subject=f"Interview Invitation - {job.title}",
                body=email_body
            )

            candidate.gmail_message_id = message_id
            await db.commit()

            print(f"\n✅ SUCCESS! Interview invitation sent to {candidate.email}")
            print(f"   Message ID: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Error during approval: {e}")
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    email = "ha5755420@gmail.com"
    print(f"Approving candidate: {email}\n")
    asyncio.run(approve_and_invite(email))

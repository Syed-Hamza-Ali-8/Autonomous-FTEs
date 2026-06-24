"""
Delete test candidate data for cleanup purposes.
Run: cd backend && uv run python delete_test_candidate.py
"""
import asyncio
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Candidate, PendingApproval, SchedulingConversation, InterviewSlot, AuditLog
from dotenv import load_dotenv

load_dotenv()
import os

DATABASE_URL = os.getenv("DATABASE_URL")

async def delete_candidate_by_email(email: str):
    """Delete candidate and all related records by email."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find candidate
        query = select(Candidate).where(Candidate.email == email)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            print(f"❌ No candidate found with email: {email}")
            return False

        candidate_id = candidate.id
        candidate_name = candidate.name
        company_id = candidate.company_id
        job_id = candidate.job_id
        print(f"Found candidate: {candidate_name} (ID: {candidate_id})")
        print(f"  Company ID: {company_id}, Job ID: {job_id}")
        print(f"  Status: {candidate.status}")

        # Delete in order (respecting foreign keys)
        deletions = []

        # 1. Delete scheduling conversations
        sched_query = delete(SchedulingConversation).where(
            SchedulingConversation.candidate_id == candidate_id
        )
        result = await db.execute(sched_query)
        deletions.append(f"SchedulingConversations: {result.rowcount}")

        # 2. Delete pending approvals
        approval_query = delete(PendingApproval).where(
            PendingApproval.candidate_id == candidate_id
        )
        result = await db.execute(approval_query)
        deletions.append(f"PendingApprovals: {result.rowcount}")

        # 3. Delete interview slots for this candidate
        slots_query = delete(InterviewSlot).where(
            InterviewSlot.candidate_id == candidate_id
        )
        result = await db.execute(slots_query)
        deletions.append(f"InterviewSlots: {result.rowcount}")

        # 4. Delete audit logs for this candidate
        audit_query = delete(AuditLog).where(
            AuditLog.candidate_id == candidate_id
        )
        result = await db.execute(audit_query)
        deletions.append(f"AuditLogs: {result.rowcount}")

        # 5. Delete the candidate
        cand_query = delete(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(cand_query)
        deletions.append(f"Candidate: {result.rowcount}")

        await db.commit()

        print("\n✅ Deleted records:")
        for d in deletions:
            print(f"  - {d}")

        print(f"\n🗑️  Candidate {candidate_name} ({email}) has been removed!")
        return True

    await engine.dispose()

if __name__ == "__main__":
    email = "ha5755420@gmail.com"
    print(f"Deleting all data for email: {email}\n")
    asyncio.run(delete_candidate_by_email(email))

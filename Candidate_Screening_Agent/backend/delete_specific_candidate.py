"""
Delete specific candidate with company verification.
Usage: cd backend && uv run python delete_specific_candidate.py
"""
import asyncio
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Candidate, PendingApproval, SchedulingConversation, InterviewSlot, AuditLog, Company
from dotenv import load_dotenv

load_dotenv()
import os

DATABASE_URL = os.getenv("DATABASE_URL")

async def delete_candidate_with_company_check(candidate_email: str, company_name: str):
    """Delete candidate after verifying company association."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find company by name
        company_query = select(Company).where(
            and_(
                Company.name == company_name,
                Company.is_active == True
            )
        )
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            print(f"❌ No active company found with name: {company_name}")
            return False

        print(f"✓ Found company: {company.name} (ID: {company.id})")

        # Find candidate by email and company
        candidate_query = select(Candidate).where(
            and_(
                Candidate.email == candidate_email,
                Candidate.company_id == company.id
            )
        )
        result = await db.execute(candidate_query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            print(f"❌ No candidate found with email '{candidate_email}' in company '{company.name}'")
            return False

        candidate_id = candidate.id
        candidate_name = candidate.name or "N/A"
        job_id = candidate.job_id

        print(f"\n✓ Found candidate:")
        print(f"  Name: {candidate_name}")
        print(f"  Email: {candidate.email}")
        print(f"  ID: {candidate_id}")
        print(f"  Company: {company.name}")
        print(f"  Job ID: {job_id}")
        print(f"  Status: {candidate.status}")

        # Count related records before deletion
        print(f"\n🔍 Checking related records...")

        sched_count_query = select(SchedulingConversation).where(
            SchedulingConversation.candidate_id == candidate_id
        )
        sched_result = await db.execute(sched_count_query)
        sched_count = len(sched_result.scalars().all())

        approval_count_query = select(PendingApproval).where(
            PendingApproval.candidate_id == candidate_id
        )
        approval_result = await db.execute(approval_count_query)
        approval_count = len(approval_result.scalars().all())

        slots_count_query = select(InterviewSlot).where(
            InterviewSlot.candidate_id == candidate_id
        )
        slots_result = await db.execute(slots_count_query)
        slots_count = len(slots_result.scalars().all())

        audit_count_query = select(AuditLog).where(
            AuditLog.candidate_id == candidate_id
        )
        audit_result = await db.execute(audit_count_query)
        audit_count = len(audit_result.scalars().all())

        print(f"  - Scheduling conversations: {sched_count}")
        print(f"  - Pending approvals: {approval_count}")
        print(f"  - Interview slots: {slots_count}")
        print(f"  - Audit logs: {audit_count}")

        # Confirm deletion
        print(f"\n⚠️  About to delete candidate and all related records.")
        print(f"   This action cannot be undone.")

        # Delete in order (respecting foreign keys)
        deletions = []

        # 1. Delete scheduling conversations
        sched_delete_query = delete(SchedulingConversation).where(
            SchedulingConversation.candidate_id == candidate_id
        )
        result = await db.execute(sched_delete_query)
        deletions.append(f"SchedulingConversations: {result.rowcount}")

        # 2. Delete pending approvals
        approval_delete_query = delete(PendingApproval).where(
            PendingApproval.candidate_id == candidate_id
        )
        result = await db.execute(approval_delete_query)
        deletions.append(f"PendingApprovals: {result.rowcount}")

        # 3. Delete interview slots for this candidate
        slots_delete_query = delete(InterviewSlot).where(
            InterviewSlot.candidate_id == candidate_id
        )
        result = await db.execute(slots_delete_query)
        deletions.append(f"InterviewSlots: {result.rowcount}")

        # 4. Delete audit logs for this candidate
        audit_delete_query = delete(AuditLog).where(
            AuditLog.candidate_id == candidate_id
        )
        result = await db.execute(audit_delete_query)
        deletions.append(f"AuditLogs: {result.rowcount}")

        # 5. Delete the candidate
        cand_delete_query = delete(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(cand_delete_query)
        deletions.append(f"Candidate: {result.rowcount}")

        await db.commit()

        print(f"\n✅ Successfully deleted:")
        for d in deletions:
            print(f"  - {d}")

        print(f"\n🗑️  Candidate '{candidate_name}' ({candidate_email}) has been removed from '{company.name}'!")
        return True

    await engine.dispose()

if __name__ == "__main__":
    # Target candidate and company
    candidate_email = "hanifatima147@gmail.com"
    company_name = "New Test Company"

    print(f"🎯 Target:")
    print(f"   Candidate: {candidate_email}")
    print(f"   Company: {company_name}\n")

    asyncio.run(delete_candidate_with_company_check(candidate_email, company_name))

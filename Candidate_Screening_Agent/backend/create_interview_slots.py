"""
Script to create initial interview slots for testing the scheduling system.
"""
import asyncio
from datetime import datetime, timedelta
from db.database import AsyncSessionLocal
from services.calendar_service import calendar_service


async def create_initial_slots():
    """Create interview slots for the next 7 days."""
    async with AsyncSessionLocal() as db:
        # Create slots for job ID 1 (adjust if needed)
        job_id = 1

        # Start from tomorrow
        start_date = datetime.utcnow() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)

        print(f"Creating interview slots from {start_date.date()} to {end_date.date()}...")

        slots = await calendar_service.create_available_slots(
            db=db,
            job_id=job_id,
            start_date=start_date,
            end_date=end_date,
            slot_duration_minutes=45,
            working_hours_start=9,  # 9 AM
            working_hours_end=17,   # 5 PM
            timezone="UTC",
            interviewer_name="Hiring Manager",
            interviewer_email="hiring@company.com",
            exclude_weekends=True
        )

        print(f"✓ Created {len(slots)} interview slots")
        print(f"  Job ID: {job_id}")
        print(f"  Duration: 45 minutes")
        print(f"  Working hours: 9 AM - 5 PM UTC")
        print(f"  Weekends excluded")

        # Show first 5 slots as examples
        if slots:
            print("\nFirst 5 slots:")
            for i, slot in enumerate(slots[:5], 1):
                print(f"  {i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%H:%M')} UTC")


if __name__ == "__main__":
    asyncio.run(create_initial_slots())

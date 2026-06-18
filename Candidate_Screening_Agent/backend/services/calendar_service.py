import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from db.models import InterviewSlot, SchedulingConversation
import pytz

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Service for managing interview slots and availability.

    Handles:
    - Creating available time slots
    - Checking for conflicts
    - Booking slots for candidates
    - Managing timezones
    """

    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone

    async def create_available_slots(
        self,
        db: AsyncSession,
        job_id: int,
        start_date: datetime,
        end_date: datetime,
        slot_duration_minutes: int = 45,
        working_hours_start: int = 9,  # 9 AM
        working_hours_end: int = 17,  # 5 PM
        timezone: str = "UTC",
        interviewer_name: Optional[str] = None,
        interviewer_email: Optional[str] = None,
        exclude_weekends: bool = True
    ) -> List[InterviewSlot]:
        """
        Generate available interview slots for a date range.

        Args:
            db: Database session
            job_id: Job ID
            start_date: Start date for slot generation
            end_date: End date for slot generation
            slot_duration_minutes: Duration of each interview slot
            working_hours_start: Start of working hours (24h format)
            working_hours_end: End of working hours (24h format)
            timezone: Timezone for the slots
            interviewer_name: Name of interviewer
            interviewer_email: Email of interviewer
            exclude_weekends: Skip Saturday and Sunday

        Returns:
            List of created InterviewSlot objects
        """
        slots = []
        current_date = start_date.date()
        end = end_date.date()

        tz = pytz.timezone(timezone)

        while current_date <= end:
            # Skip weekends if requested
            if exclude_weekends and current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
                continue

            # Generate slots for this day
            current_hour = working_hours_start
            while current_hour < working_hours_end:
                # Create slot start time
                slot_start = tz.localize(datetime.combine(
                    current_date,
                    datetime.min.time().replace(hour=current_hour)
                ))
                slot_end = slot_start + timedelta(minutes=slot_duration_minutes)

                # Check if slot end is within working hours
                if slot_end.hour >= working_hours_end:
                    break

                # Check for conflicts with existing slots
                conflict = await self.check_slot_conflict(db, slot_start, slot_end)
                if not conflict:
                    slot = InterviewSlot(
                        job_id=job_id,
                        start_time=slot_start.astimezone(pytz.UTC),  # Store in UTC
                        end_time=slot_end.astimezone(pytz.UTC),
                        status="available",
                        timezone=timezone,
                        interviewer_name=interviewer_name,
                        interviewer_email=interviewer_email
                    )
                    db.add(slot)
                    slots.append(slot)

                # Move to next slot
                current_hour += slot_duration_minutes // 60
                if slot_duration_minutes % 60 != 0:
                    current_hour += 1

            current_date += timedelta(days=1)

        await db.commit()
        logger.info(f"Created {len(slots)} available interview slots for job {job_id}")
        return slots

    async def check_slot_conflict(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if a time slot conflicts with existing booked/proposed slots.

        Args:
            db: Database session
            start_time: Slot start time
            end_time: Slot end time

        Returns:
            True if conflict exists, False otherwise
        """
        query = select(InterviewSlot).where(
            and_(
                InterviewSlot.status.in_(["booked", "proposed"]),
                or_(
                    # New slot starts during existing slot
                    and_(
                        InterviewSlot.start_time <= start_time,
                        InterviewSlot.end_time > start_time
                    ),
                    # New slot ends during existing slot
                    and_(
                        InterviewSlot.start_time < end_time,
                        InterviewSlot.end_time >= end_time
                    ),
                    # New slot completely contains existing slot
                    and_(
                        InterviewSlot.start_time >= start_time,
                        InterviewSlot.end_time <= end_time
                    )
                )
            )
        )
        result = await db.execute(query)
        conflict = result.scalar_one_or_none()
        return conflict is not None

    async def get_available_slots(
        self,
        db: AsyncSession,
        job_id: int,
        limit: int = 5,
        from_date: Optional[datetime] = None
    ) -> List[InterviewSlot]:
        """
        Get available interview slots for a job.

        Args:
            db: Database session
            job_id: Job ID
            limit: Maximum number of slots to return
            from_date: Only return slots after this date (default: now)

        Returns:
            List of available InterviewSlot objects
        """
        if from_date is None:
            from_date = datetime.utcnow()

        query = select(InterviewSlot).where(
            and_(
                InterviewSlot.job_id == job_id,
                InterviewSlot.status == "available",
                InterviewSlot.start_time >= from_date
            )
        ).order_by(InterviewSlot.start_time).limit(limit)

        result = await db.execute(query)
        slots = result.scalars().all()
        return list(slots)

    async def propose_slots(
        self,
        db: AsyncSession,
        slot_ids: List[int],
        candidate_id: int
    ) -> List[InterviewSlot]:
        """
        Mark slots as proposed to a candidate.

        Args:
            db: Database session
            slot_ids: List of slot IDs to propose
            candidate_id: Candidate ID

        Returns:
            List of proposed InterviewSlot objects
        """
        proposed_slots = []
        for slot_id in slot_ids:
            query = select(InterviewSlot).where(
                and_(
                    InterviewSlot.id == slot_id,
                    InterviewSlot.status == "available"
                )
            )
            result = await db.execute(query)
            slot = result.scalar_one_or_none()

            if slot:
                slot.status = "proposed"
                slot.candidate_id = candidate_id
                proposed_slots.append(slot)

        await db.commit()
        logger.info(f"Proposed {len(proposed_slots)} slots to candidate {candidate_id}")
        return proposed_slots

    async def book_slot(
        self,
        db: AsyncSession,
        slot_id: int,
        candidate_id: int,
        meeting_link: Optional[str] = None
    ) -> Optional[InterviewSlot]:
        """
        Book a slot for a candidate.

        Args:
            db: Database session
            slot_id: Slot ID to book
            candidate_id: Candidate ID
            meeting_link: Optional meeting link (Zoom, Google Meet, etc.)

        Returns:
            Booked InterviewSlot or None if not available
        """
        query = select(InterviewSlot).where(
            and_(
                InterviewSlot.id == slot_id,
                InterviewSlot.status.in_(["available", "proposed"]),
                or_(
                    InterviewSlot.candidate_id == candidate_id,
                    InterviewSlot.candidate_id.is_(None)
                )
            )
        )
        result = await db.execute(query)
        slot = result.scalar_one_or_none()

        if not slot:
            logger.warning(f"Slot {slot_id} not available for booking")
            return None

        slot.status = "booked"
        slot.candidate_id = candidate_id
        if meeting_link:
            slot.meeting_link = meeting_link

        # Release other proposed slots for this candidate
        await self.release_proposed_slots(db, candidate_id, exclude_slot_id=slot_id)

        await db.commit()
        logger.info(f"Booked slot {slot_id} for candidate {candidate_id}")
        return slot

    async def release_proposed_slots(
        self,
        db: AsyncSession,
        candidate_id: int,
        exclude_slot_id: Optional[int] = None
    ):
        """
        Release all proposed slots for a candidate (make them available again).

        Args:
            db: Database session
            candidate_id: Candidate ID
            exclude_slot_id: Optional slot ID to exclude from release
        """
        query = select(InterviewSlot).where(
            and_(
                InterviewSlot.candidate_id == candidate_id,
                InterviewSlot.status == "proposed"
            )
        )

        if exclude_slot_id:
            query = query.where(InterviewSlot.id != exclude_slot_id)

        result = await db.execute(query)
        slots = result.scalars().all()

        for slot in slots:
            slot.status = "available"
            slot.candidate_id = None

        await db.commit()
        logger.info(f"Released {len(slots)} proposed slots for candidate {candidate_id}")

    async def cancel_slot(
        self,
        db: AsyncSession,
        slot_id: int
    ) -> Optional[InterviewSlot]:
        """
        Cancel a booked slot.

        Args:
            db: Database session
            slot_id: Slot ID to cancel

        Returns:
            Cancelled InterviewSlot or None if not found
        """
        query = select(InterviewSlot).where(InterviewSlot.id == slot_id)
        result = await db.execute(query)
        slot = result.scalar_one_or_none()

        if slot:
            slot.status = "cancelled"
            await db.commit()
            logger.info(f"Cancelled slot {slot_id}")

        return slot

    def format_slot_for_display(
        self,
        slot: InterviewSlot,
        display_timezone: str = "UTC"
    ) -> Dict[str, str]:
        """
        Format a slot for display to candidate.

        Args:
            slot: InterviewSlot object
            display_timezone: Timezone to display in

        Returns:
            Dict with formatted date, time, and timezone
        """
        tz = pytz.timezone(display_timezone)
        start_local = slot.start_time.astimezone(tz)
        end_local = slot.end_time.astimezone(tz)

        return {
            "id": slot.id,
            "date": start_local.strftime("%A, %B %d, %Y"),
            "time": f"{start_local.strftime('%I:%M %p')} - {end_local.strftime('%I:%M %p')}",
            "timezone": display_timezone,
            "full_datetime": start_local.isoformat()
        }


# Global instance
calendar_service = CalendarService()

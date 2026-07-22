import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from db.models import InterviewSlot, SchedulingConversation
import pytz

logger = logging.getLogger(__name__)

# Common timezone mappings for email domains
EMAIL_DOMAIN_TIMEZONES = {
    "gmail.com": "America/New_York",  # Will be overridden by actual detection
    "yahoo.com": "America/New_York",
    "hotmail.com": "America/New_York",
    "outlook.com": "America/New_York",
    "icloud.com": "America/Los_Angeles",
    # Asian timezones
    "qq.com": "Asia/Shanghai",
    "163.com": "Asia/Shanghai",
    "126.com": "Asia/Shanghai",
    "outlook.co.in": "Asia/Kolkata",
    "yahoo.co.in": "Asia/Kolkata",
    "hotmail.co.in": "Asia/Kolkata",
}

# Working hours per timezone (company's business hours)
WORKING_HOURS = {
    "start": 9,   # 9 AM
    "end": 18,    # 6 PM
}


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
            "full_datetime": start_local.isoformat(),
            "utc_time": slot.start_time.strftime("%H:%M"),
            "utc_date": slot.start_time.strftime("%Y-%m-%d")
        }

    def detect_timezone_from_email(self, email: str) -> str:
        """
        Detect candidate's timezone from email domain.

        Args:
            email: Candidate's email address

        Returns:
            Detected timezone string or default UTC
        """
        if not email:
            return "UTC"

        domain = email.split("@")[-1].lower()

        # Check for known domain → timezone mapping
        for email_domain, tz in EMAIL_DOMAIN_TIMEZONES.items():
            if domain.endswith(email_domain):
                logger.info(f"Detected timezone {tz} from email domain {domain}")
                return tz

        return "UTC"

    def extract_timezone_from_text(self, text: str) -> Optional[str]:
        """
        Extract timezone mentioned in candidate's reply text.

        Args:
            text: Candidate's reply text

        Returns:
            Detected timezone string or None
        """
        import re
        text_lower = text.lower()

        # Common timezone patterns (order matters - more specific first)
        timezone_patterns = [
            # Asian timezones (specific patterns first)
            (r"\bpakistan\b", "Asia/Karachi"),
            (r"\bpkt\b", "Asia/Karachi"),
            (r"\bpkst\b", "Asia/Karachi"),
            (r"\bist\b", "Asia/Kolkata"),
            (r"\bindia\b", "Asia/Kolkata"),
            (r"\bbst\b", "Asia/Dhaka"),
            (r"\bbangladesh\b", "Asia/Dhaka"),
            (r"\bjst\b", "Asia/Tokyo"),
            (r"\bkst\b", "Asia/Seoul"),
            (r"\bsgt\b", "Asia/Singapore"),
            (r"\baest\b", "Australia/Sydney"),
            (r"\bnzst\b", "Pacific/Auckland"),

            # European timezones
            (r"\bbst\s+uk\b", "Europe/London"),
            (r"\bcet\b", "Europe/Paris"),
            (r"\bcest\b", "Europe/Paris"),

            # US timezones (check PST AFTER PKT to avoid conflict)
            (r"\bpdt\b", "America/Los_Angeles"),
            (r"\bedt\b", "America/New_York"),
            (r"\bcdt\b", "America/Chicago"),
            (r"\bmdt\b", "America/Denver"),
            (r"\bpst\b", "America/Los_Angeles"),
            (r"\best\b", "America/New_York"),
            (r"\bcst\b", "America/Chicago"),
            (r"\bmst\b", "America/Denver"),

            # UTC
            (r"\butc\b", "UTC"),
            (r"\bgmt\b", "UTC"),
        ]

        for pattern, tz in timezone_patterns:
            if re.search(pattern, text_lower):
                return tz

        return None

    def parse_candidate_suggested_time(
        self,
        text: str,
        company_timezone: str = "UTC"
    ) -> Optional[Dict[str, datetime]]:
        """
        Parse candidate's suggested time from text.

        Examples:
        - "friday 3pm" → returns datetime for Friday 3pm
        - "Monday at 10am" → returns datetime for Monday 10am
        - "June 30 at 6am" → returns datetime for June 30 6am

        Args:
            text: Candidate's reply text
            company_timezone: Company's working hours timezone

        Returns:
            Dict with start_time and end_time, or None if can't parse
        """
        import re
        from dateutil import parser as dateutil_parser

        text_lower = text.lower()

        # Try to extract time. Order matters: match the fuller "H:MM am/pm" form
        # BEFORE the bare "H am/pm" form so "04:00 PM" isn't half-matched, and require
        # the am/pm marker to sit adjacent to the number so a date like "July 23" or a
        # bare "5" isn't mistaken for a time.
        time_patterns = [
            r"(\d{1,2})\s*:\s*(\d{2})\s*(am|pm)",   # 4:00 pm
            r"(\d{1,2})\s*(am|pm)",                  # 4 pm
        ]

        time_info = None
        match_span = None
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                match_span = match.span()
                groups = match.groups()
                if len(groups) == 3:
                    hour = int(groups[0])
                    minute = int(groups[1])
                    am_pm = groups[2]
                else:
                    hour = int(groups[0])
                    minute = 0
                    am_pm = groups[1]
                time_info = {"hour": hour, "minute": minute, "am_pm": am_pm}
                break

        if not time_info:
            return None

        # Try to extract day/date
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        target_date = None
        for day in day_names:
            if day in text_lower:
                # Find next occurrence of this day
                today = datetime.now(pytz.timezone(company_timezone))
                days_ahead = day_names.index(day) - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                break

        # Try to extract a specific calendar date ONLY if no weekday was found.
        # (A matched weekday like "Friday" is authoritative; don't let a date regex
        # overwrite it by mis-reading the time, e.g. "at 5 PM" -> "July 05".)
        if target_date is None:
            # Strip the matched time span so patterns can't parse the time as a date
            # (e.g. "at 5 pm" being read as day 5).
            text_wo_time = text[:match_span[0]] + " " + text[match_span[1]:] if match_span else text
            date_patterns = [
                r"(\d{1,2})[/\-](\d{1,2})(?:\s*[/\-]\s*(\d{2,4}))?",  # 6/30 or 30-06-2026
                # Month name + day, e.g. "June 30" / "July 24, 2026". Requires a real
                # month name so "at 5" can't match.
                r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:,?\s*(\d{4}))?",
            ]
            for pattern in date_patterns:
                m = re.search(pattern, text_wo_time, re.IGNORECASE)
                if m:
                    try:
                        parsed = dateutil_parser.parse(m.group(0), fuzzy=True)
                        if parsed:
                            target_date = parsed
                            break
                    except Exception:
                        pass

        if not target_date:
            # Default to next occurrence of the day
            return None

        # Convert hour to 24h format
        hour = time_info["hour"]
        if time_info["am_pm"] == "pm" and hour < 12:
            hour += 12
        elif time_info["am_pm"] == "am" and hour == 12:
            hour = 0

        # Validate hour is in valid range (0-23)
        if not (0 <= hour <= 23):
            logger.warning(f"Invalid hour extracted: {hour}. Cannot parse time from text.")
            return None

        # Validate minute is in valid range (0-59)
        if not (0 <= time_info["minute"] <= 59):
            logger.warning(f"Invalid minute extracted: {time_info['minute']}. Cannot parse time from text.")
            return None

        # Set time
        target_date = target_date.replace(
            hour=hour,
            minute=time_info["minute"],
            second=0,
            microsecond=0
        )

        # Make timezone aware
        tz = pytz.timezone(company_timezone)
        if target_date.tzinfo is None:
            target_date = tz.localize(target_date)
        else:
            target_date = target_date.astimezone(tz)

        # Calculate end time (45 min interview)
        end_time = target_date + timedelta(minutes=45)

        return {
            "start_time": target_date.astimezone(pytz.UTC),
            "end_time": end_time.astimezone(pytz.UTC)
        }

    def is_within_working_hours(
        self,
        start_time: datetime,
        end_time: datetime,
        timezone: str = "UTC"
    ) -> bool:
        """
        Check if suggested time is within company's working hours.

        Args:
            start_time: Interview start time
            end_time: Interview end time
            timezone: Company's timezone

        Returns:
            True if within working hours, False otherwise
        """
        tz = pytz.timezone(timezone)
        start_local = start_time.astimezone(tz)
        end_local = end_time.astimezone(tz)

        start_hour = start_local.hour
        end_hour = end_local.hour

        # Check if within working hours (9 AM - 6 PM)
        if start_hour < WORKING_HOURS["start"]:
            return False
        if end_hour > WORKING_HOURS["end"]:
            return False

        # Check if on weekday (Monday = 0, Sunday = 6)
        if start_local.weekday() >= 5:  # Saturday or Sunday
            return False

        return True

    def get_nearest_available_slots(
        self,
        db: AsyncSession,
        job_id: int,
        around_time: datetime,
        limit: int = 3
    ) -> List[InterviewSlot]:
        """
        Get available slots nearest to the suggested time.

        Args:
            db: Database session
            job_id: Job ID
            around_time: Time to find slots around
            limit: Number of slots to return

        Returns:
            List of available InterviewSlots
        """
        from sqlalchemy import select, and_

        # Find slots within ±2 hours of suggested time
        time_range_start = around_time - timedelta(hours=2)
        time_range_end = around_time + timedelta(hours=2)

        query = select(InterviewSlot).where(
            and_(
                InterviewSlot.job_id == job_id,
                InterviewSlot.status == "available",
                InterviewSlot.start_time >= time_range_start,
                InterviewSlot.start_time <= time_range_end
            )
        ).order_by(
            InterviewSlot.start_time
        ).limit(limit)

        # Sync execution for this helper method
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(db.execute(query))
        slots = result.scalars().all()
        return list(slots)

    def generate_google_meet_link(
        self,
        slot: InterviewSlot,
        candidate_email: Optional[str] = None,
        candidate_name: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a real Google Meet link by inserting a Google Calendar event
        with a conferenceData request, then reading back the Meet URL.

        A Meet link cannot be created by guessing a code - Google must mint it.
        This calls Calendar API events.insert with conferenceDataVersion=1 so
        Google attaches a genuine, joinable Meet room to the event.

        Requires the OAuth token to include the calendar.events scope
        (re-run authenticate_gmail.py after adding that scope).

        Args:
            slot: InterviewSlot object (provides start/end time)
            candidate_email: Candidate email to invite as an attendee
            candidate_name: Candidate name for the event summary
            job_title: Job title for the event summary

        Returns:
            Real Google Meet URL, or None if creation failed.
        """
        try:
            event = self._create_calendar_event_with_meet(
                slot, candidate_email, candidate_name, job_title
            )
            meet_link = self._extract_meet_link(event)
            if meet_link:
                logger.info(f"Created Google Meet link for slot {slot.id}: {meet_link}")
                return meet_link
            logger.error(
                f"Calendar event created for slot {slot.id} but no Meet link was returned"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to create Google Meet link for slot {slot.id}: {e}")
            return None

    def _get_calendar_service(self):
        """Build an authenticated Google Calendar API client from env credentials."""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        credentials = Credentials(
            token=None,
            refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GMAIL_CLIENT_ID"),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        )
        return build("calendar", "v3", credentials=credentials)

    def _create_calendar_event_with_meet(
        self,
        slot: InterviewSlot,
        candidate_email: Optional[str],
        candidate_name: Optional[str],
        job_title: Optional[str],
    ) -> Dict:
        """Insert a Calendar event that requests a Google Meet conference."""
        service = self._get_calendar_service()

        who = candidate_name or candidate_email or "Candidate"
        role = job_title or "Interview"
        summary = f"Interview: {who} - {role}"

        event_body = {
            "summary": summary,
            "description": f"Interview for the {role} position.",
            "start": {
                "dateTime": slot.start_time.isoformat(),
                "timeZone": slot.timezone or "UTC",
            },
            "end": {
                "dateTime": slot.end_time.isoformat(),
                "timeZone": slot.timezone or "UTC",
            },
            "conferenceData": {
                "createRequest": {
                    # Unique per-event request id so Google mints a fresh room
                    "requestId": f"slot-{slot.id}-{uuid.uuid4().hex[:8]}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        if candidate_email:
            event_body["attendees"] = [{"email": candidate_email}]

        return (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
                conferenceDataVersion=1,
                sendUpdates="all" if candidate_email else "none",
            )
            .execute()
        )

    @staticmethod
    def _extract_meet_link(event: Dict) -> Optional[str]:
        """Pull the Meet URL from a created Calendar event."""
        # hangoutLink is the direct Meet URL on the event
        if event.get("hangoutLink"):
            return event["hangoutLink"]
        # Fall back to conferenceData entry points
        for entry in event.get("conferenceData", {}).get("entryPoints", []):
            if entry.get("entryPointType") == "video" and entry.get("uri"):
                return entry["uri"]
        return None

    def generate_zoom_link(self, slot: InterviewSlot) -> str:
        """
        Generate a Zoom meeting link.

        Args:
            slot: InterviewSlot object

        Returns:
            Zoom meeting URL
        """
        # Generate random meeting ID (10 digits for Zoom)
        meeting_id = ''.join([str(uuid.uuid4().int % 10) for _ in range(10)])

        return f"https://zoom.us/j/{meeting_id}"

    def generate_microsoft_teams_link(self, slot: InterviewSlot) -> str:
        """
        Generate a Microsoft Teams meeting link.

        Args:
            slot: InterviewSlot object

        Returns:
            Microsoft Teams meeting URL
        """
        # Generate random meeting code
        meeting_code = uuid.uuid4().hex[:24].upper()

        return f"https://teams.microsoft.com/l/meetup-join/{meeting_code}"

    def format_slots_for_candidate(
        self,
        slots: List[InterviewSlot],
        candidate_timezone: str
    ) -> str:
        """
        Format multiple slots for display in email with candidate's local timezone.

        Args:
            slots: List of InterviewSlots
            candidate_timezone: Candidate's timezone

        Returns:
            Formatted string with times in candidate's local timezone
        """
        formatted = []
        for i, slot in enumerate(slots, 1):
            # Get time in candidate's timezone
            tz = pytz.timezone(candidate_timezone)
            start_local = slot.start_time.astimezone(tz)
            end_local = slot.end_time.astimezone(tz)

            # Format nicely
            date_str = start_local.strftime("%A, %B %d, %Y")
            time_str = f"{start_local.strftime('%I:%M %p')} - {end_local.strftime('%I:%M %p')}"

            # Get timezone abbreviation
            tz_abbr = start_local.tzname()

            formatted.append(f"{i}. {date_str} at {time_str} {tz_abbr}")

        return "\n".join(formatted)


# Global instance
calendar_service = CalendarService()

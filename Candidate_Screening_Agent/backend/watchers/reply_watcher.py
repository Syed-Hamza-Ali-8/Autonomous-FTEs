import json
import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from watchers.base_watcher import BaseWatcher
from db.database import AsyncSessionLocal
from db import crud
from db.models import SchedulingConversation
from sqlalchemy import select, and_
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


class ReplyWatcher(BaseWatcher):
    """
    Watcher that polls Gmail for candidate replies to:
    1. Screening question emails
    2. Interview scheduling emails
    3. Rejection emails

    Polls every 1 minute and routes replies appropriately.
    """

    def __init__(self):
        super().__init__(check_interval=30)

        # Gmail OAuth2 setup
        self.credentials = Credentials(
            token=None,
            refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GMAIL_CLIENT_ID"),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

        # Track processed message IDs in Redis (persists across restarts)
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = None
        self._processed_cache: set = set()  # In-memory cache for quick checks

    async def _get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def _is_processed(self, msg_id: str) -> bool:
        """Check if message was already processed (Redis + cache)."""
        if msg_id in self._processed_cache:
            return True
        r = await self._get_redis()
        if await r.sismember("processed_emails", msg_id):
            self._processed_cache.add(msg_id)
            return True
        return False

    async def _mark_processed(self, msg_id: str) -> None:
        """Mark message as processed in Redis and cache."""
        self._processed_cache.add(msg_id)
        r = await self._get_redis()
        await r.sadd("processed_emails", msg_id)

    async def check_for_updates(self) -> list:
        """
        Check Gmail for candidate replies.
        Uses thread-based matching since Gmail overrides Message-ID headers.
        """
        try:
            async with AsyncSessionLocal() as db:
                # Get candidates awaiting screening reply
                screening_candidates = await crud.get_candidates_by_status(db, "awaiting_reply")

                # Get candidates in active scheduling conversations
                scheduling_query = select(SchedulingConversation).where(
                    SchedulingConversation.conversation_state.in_([
                        "proposing_times", "awaiting_confirmation", "awaiting_questions_reply", "awaiting_timezone", "rescheduling", "confirmed"
                    ])
                )
                result = await db.execute(scheduling_query)
                scheduling_conversations = result.scalars().all()

            if not screening_candidates and not scheduling_conversations:
                return []

            replies = []

            # For each candidate awaiting reply, search for their response
            for candidate in screening_candidates:
                # Search for replies FROM this candidate (exclude sent to avoid loops)
                query = f"from:{candidate.email} -in:sent newer_than:1h"
                results = self.service.users().messages().list(
                    userId="me", q=query, maxResults=5
                ).execute()

                messages = results.get("messages", [])
                for msg in messages:
                    # Skip already processed messages
                    if await self._is_processed(msg["id"]):
                        continue

                    full_msg = self.service.users().messages().get(
                        userId="me", id=msg["id"], format="full"
                    ).execute()

                    headers = full_msg["payload"].get("headers", [])
                    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
                    # Make sure it's FROM the candidate (not TO them)
                    if candidate.email.lower() not in sender.lower():
                        continue

                    in_reply_to = next((h["value"] for h in headers if h["name"] == "In-Reply-To"), "")

                    # If this email has In-Reply-To, it's a reply to something we sent
                    if in_reply_to:
                        reply_text = self._extract_body(full_msg)
                        if reply_text and len(reply_text) > 20:  # Minimum reply length
                            await self._mark_processed(msg["id"])
                            replies.append((msg["id"], candidate.id, reply_text, "screening"))
                            self.logger.info(f"Found screening reply from {candidate.email} (candidate {candidate.id})")

            # Also check for scheduling replies
            for conv in scheduling_conversations:
                # Get candidate email
                async with AsyncSessionLocal() as db2:
                    from db.models import Candidate
                    cand = await db2.get(Candidate, conv.candidate_id)
                    if not cand:
                        continue

                query = f"from:{cand.email} -in:sent newer_than:1h"
                results = self.service.users().messages().list(
                    userId="me", q=query, maxResults=5
                ).execute()

                for msg in results.get("messages", []):
                    # Skip already processed messages
                    if await self._is_processed(msg["id"]):
                        continue

                    full_msg = self.service.users().messages().get(
                        userId="me", id=msg["id"], format="full"
                    ).execute()
                    headers = full_msg["payload"].get("headers", [])
                    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
                    # Make sure it's FROM the candidate (not TO them)
                    if cand.email.lower() not in sender.lower():
                        continue

                    in_reply_to = next((h["value"] for h in headers if h["name"] == "In-Reply-To"), "")

                    if in_reply_to:
                        reply_text = self._extract_body(full_msg)
                        if reply_text and len(reply_text) > 10:
                            await self._mark_processed(msg["id"])
                            replies.append((msg["id"], conv.candidate_id, reply_text, "scheduling"))
                            self.logger.info(f"Found scheduling reply from {cand.email}")

            return replies

        except Exception as e:
            self.logger.error(f"Error checking for replies: {e}")
            return []

    def _extract_body(self, message) -> str:
        """Extract plain text body from Gmail message (quoted history stripped)."""
        raw = ""
        try:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                        raw = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                raw = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        except Exception:
            pass
        return self._strip_quoted(raw)

    @staticmethod
    def _strip_quoted(text: str) -> str:
        """Remove quoted reply history so only the candidate's new message is analyzed.

        Gmail replies embed the prior thread ("On <date> <name> wrote:" followed by
        '>'-quoted lines). Those contain dates/times/keywords that were mis-parsed as
        the candidate's own input (e.g. a quote header "at 2:20 AM" booked 2:20 AM).
        """
        import re
        if not text:
            return ""
        lines = text.splitlines()
        kept = []
        # Matches "On Wed, Jul 22, 2026 at 2:20 AM Hacher <..> wrote:" (incl. NBSP)
        on_wrote = re.compile(r"^\s*On .+wrote:\s*$")
        for line in lines:
            stripped = line.strip()
            if on_wrote.match(stripped):
                break
            if stripped.startswith(">"):
                break
            # Common client separators
            if stripped in ("--", "----------") or stripped.startswith("-----Original Message"):
                break
            kept.append(line)
        cleaned = "\n".join(kept).strip()
        # Fall back to the raw text if stripping removed everything.
        return cleaned or text.strip()

    async def handle_item(self, item) -> None:
        """Process a reply and push to the appropriate Redis queue."""
        message_id, candidate_id, reply_text, reply_type = item

        try:
            r = await self._get_redis()

            if reply_type == "screening":
                await r.lpush("reply_queue", json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "message_id": message_id,
                }))
                self.logger.info(f"Pushed screening reply for candidate {candidate_id}")
            elif reply_type == "scheduling":
                await r.lpush("scheduling_reply_queue", json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "reply_message_id": message_id,
                }))
                self.logger.info(f"Pushed scheduling reply for candidate {candidate_id}")

        except Exception as e:
            self.logger.error(f"Error handling reply for candidate {candidate_id}: {e}")

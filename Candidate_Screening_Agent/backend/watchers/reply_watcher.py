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
        super().__init__(check_interval=60)

        # Gmail OAuth2 setup
        self.credentials = Credentials(
            token=None,
            refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GMAIL_CLIENT_ID"),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

        # Redis connection
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = None

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
                        "proposing_times", "awaiting_confirmation", "rescheduling"
                    ])
                )
                result = await db.execute(scheduling_query)
                scheduling_conversations = result.scalars().all()

            if not screening_candidates and not scheduling_conversations:
                return []

            replies = []

            # For each candidate awaiting reply, search for their response
            for candidate in screening_candidates:
                # Search for replies FROM this candidate
                query = f"from:{candidate.email} newer_than:1d"
                results = self.service.users().messages().list(
                    userId="me", q=query, maxResults=5
                ).execute()

                messages = results.get("messages", [])
                for msg in messages:
                    full_msg = self.service.users().messages().get(
                        userId="me", id=msg["id"], format="full"
                    ).execute()

                    headers = full_msg["payload"].get("headers", [])
                    in_reply_to = next((h["value"] for h in headers if h["name"] == "In-Reply-To"), "")

                    # If this email has In-Reply-To, it's a reply to something we sent
                    # Since candidate only has one active screening thread, this is their reply
                    if in_reply_to:
                        reply_text = self._extract_body(full_msg)
                        if reply_text and len(reply_text) > 20:  # Minimum reply length
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

                query = f"from:{cand.email} newer_than:1d"
                results = self.service.users().messages().list(
                    userId="me", q=query, maxResults=5
                ).execute()

                for msg in results.get("messages", []):
                    full_msg = self.service.users().messages().get(
                        userId="me", id=msg["id"], format="full"
                    ).execute()
                    headers = full_msg["payload"].get("headers", [])
                    in_reply_to = next((h["value"] for h in headers if h["name"] == "In-Reply-To"), "")

                    if in_reply_to:
                        reply_text = self._extract_body(full_msg)
                        if reply_text and len(reply_text) > 10:
                            replies.append((msg["id"], conv.candidate_id, reply_text, "scheduling"))
                            self.logger.info(f"Found scheduling reply from {cand.email}")

            return replies

        except Exception as e:
            self.logger.error(f"Error checking for replies: {e}")
            return []

    def _extract_body(self, message) -> str:
        """Extract plain text body from Gmail message."""
        try:
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                return base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        except Exception:
            pass
        return ""

    async def handle_item(self, item) -> None:
        """Process a reply and push to the appropriate Redis queue."""
        message_id, candidate_id, reply_text, reply_type = item

        try:
            if not self.redis:
                self.redis = redis.from_url(self.redis_url)

            if reply_type == "screening":
                await self.redis.lpush("reply_queue", json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "message_id": message_id,
                }))
                self.logger.info(f"Pushed screening reply for candidate {candidate_id}")
            elif reply_type == "scheduling":
                await self.redis.lpush("scheduling_reply_queue", json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "reply_message_id": message_id,
                }))
                self.logger.info(f"Pushed scheduling reply for candidate {candidate_id}")

        except Exception as e:
            self.logger.error(f"Error handling reply for candidate {candidate_id}: {e}")

import json
import os
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
        super().__init__(check_interval=60)  # 1 minute

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
        Check Gmail for replies to screening questions, scheduling emails, and rejection emails.

        Returns:
            List of (message_id, candidate_id, reply_text, reply_type) tuples
            reply_type is "screening", "scheduling", or "rejection"
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

                # Get rejected candidates who have rejection_message_id
                rejected_candidates = await crud.get_candidates_by_status(db, "rejected")

            # Build maps for matching
            screening_map = {
                c.gmail_message_id: c.id
                for c in screening_candidates
                if c.gmail_message_id
            }

            scheduling_map = {
                conv.last_message_id: conv.candidate_id
                for conv in scheduling_conversations
                if conv.last_message_id
            }

            rejection_map = {
                c.rejection_message_id: c.id
                for c in rejected_candidates
                if c.rejection_message_id
            }

            if not screening_map and not scheduling_map and not rejection_map:
                return []

            # Query for recent emails (last 24 hours)
            results = self.service.users().messages().list(
                userId="me",
                q="newer_than:1d",
                maxResults=50
            ).execute()

            messages = results.get("messages", [])
            replies = []

            # Check each message for reply headers
            for msg in messages:
                try:
                    full_msg = self.service.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="full"
                    ).execute()

                    headers = full_msg["payload"]["headers"]

                    # Get In-Reply-To and References headers
                    in_reply_to = next((h["value"] for h in headers if h["name"] == "In-Reply-To"), None)
                    references = next((h["value"] for h in headers if h["name"] == "References"), None)

                    # Check if this is a reply to any of our emails
                    matched_candidate_id = None
                    reply_type = None

                    if in_reply_to:
                        # Check screening map
                        for original_msg_id, candidate_id in screening_map.items():
                            if original_msg_id in in_reply_to:
                                matched_candidate_id = candidate_id
                                reply_type = "screening"
                                break

                        # Check scheduling map if not found
                        if not matched_candidate_id:
                            for original_msg_id, candidate_id in scheduling_map.items():
                                if original_msg_id in in_reply_to:
                                    matched_candidate_id = candidate_id
                                    reply_type = "scheduling"
                                    break

                        # Check rejection map if not found
                        if not matched_candidate_id:
                            for original_msg_id, candidate_id in rejection_map.items():
                                if original_msg_id in in_reply_to:
                                    matched_candidate_id = candidate_id
                                    reply_type = "rejection"
                                    break

                    if not matched_candidate_id and references:
                        # Check screening map
                        for original_msg_id, candidate_id in screening_map.items():
                            if original_msg_id in references:
                                matched_candidate_id = candidate_id
                                reply_type = "screening"
                                break

                        # Check scheduling map if not found
                        if not matched_candidate_id:
                            for original_msg_id, candidate_id in scheduling_map.items():
                                if original_msg_id in references:
                                    matched_candidate_id = candidate_id
                                    reply_type = "scheduling"
                                    break

                        # Check rejection map if not found
                        if not matched_candidate_id:
                            for original_msg_id, candidate_id in rejection_map.items():
                                if original_msg_id in references:
                                    matched_candidate_id = candidate_id
                                    reply_type = "rejection"
                                    break

                    if matched_candidate_id and reply_type:
                        # Extract reply text
                        reply_text = self._extract_text(full_msg)
                        if reply_text:
                            replies.append((msg["id"], matched_candidate_id, reply_text, reply_type))
                            self.logger.info(f"Found {reply_type} reply from candidate {matched_candidate_id}")

                except Exception as e:
                    self.logger.error(f"Error processing message {msg['id']}: {e}")
                    continue

            return replies

        except Exception as e:
            self.logger.error(f"Error checking for replies: {e}")
            return []

    def _get_message_id_header(self, message_id: str) -> str:
        """Fetch the actual Message-ID header from a Gmail message."""
        try:
            msg = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["Message-ID"]
            ).execute()
            for h in msg.get("payload", {}).get("headers", []):
                if h["name"] == "Message-ID":
                    return h["value"]
        except Exception as e:
            self.logger.error(f"Error fetching Message-ID header: {e}")
        return ""

    def _extract_text(self, message: dict) -> str:
        """Extract text content from Gmail message."""
        try:
            payload = message["payload"]

            # Try to get plain text part
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"].get("data", "")
                        if data:
                            import base64
                            return base64.urlsafe_b64decode(data).decode("utf-8")

            # Fallback to body data
            if "body" in payload and "data" in payload["body"]:
                import base64
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

            # Fallback to snippet
            return message.get("snippet", "")

        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""

    async def handle_item(self, item: tuple) -> None:
        """
        Process a reply: route to appropriate queue based on reply type.

        Args:
            item: Tuple of (message_id, candidate_id, reply_text, reply_type)
        """
        message_id, candidate_id, reply_text, reply_type = item

        try:
            if not self.redis:
                self.redis = await redis.from_url(self.redis_url)

            # Fetch the actual Message-ID header from the email for proper threading
            actual_message_id = self._get_message_id_header(message_id)

            if reply_type == "screening":
                # Push to screening reply queue (existing flow)
                reply_data = json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text
                })
                await self.redis.lpush("reply_queue", reply_data)
                self.logger.info(f"Pushed screening reply for candidate {candidate_id} to reply queue")

            elif reply_type == "scheduling":
                # Push to scheduling reply queue with actual Message-ID for threading
                reply_data = json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "reply_message_id": actual_message_id or message_id
                })
                await self.redis.lpush("scheduling_reply_queue", reply_data)
                self.logger.info(f"Pushed scheduling reply for candidate {candidate_id} to scheduling queue")

            elif reply_type == "rejection":
                # Push to rejection reply queue
                reply_data = json.dumps({
                    "candidate_id": candidate_id,
                    "reply_text": reply_text,
                    "reply_message_id": message_id
                })
                await self.redis.lpush("rejection_reply_queue", reply_data)
                self.logger.info(f"Pushed rejection reply for candidate {candidate_id} to rejection queue")

        except Exception as e:
            self.logger.error(f"Error handling reply for candidate {candidate_id}: {e}")

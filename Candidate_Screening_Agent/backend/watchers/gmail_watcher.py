import json
import base64
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from watchers.base_watcher import BaseWatcher
from services.pdf_service import extract_text_from_pdf
from db.database import AsyncSessionLocal
from db import crud
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


class GmailApplicationWatcher(BaseWatcher):
    """
    Watcher that polls Gmail for new job applications with PDF CVs.

    Polls every 2 minutes for unread emails with label "jobs".
    Tracks processed message IDs to avoid duplicates.
    """

    def __init__(self):
        super().__init__(check_interval=120)  # 2 minutes

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

        # Track processed message IDs
        self.processed_ids_file = Path("processed_ids.json")
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load processed message IDs from file."""
        if self.processed_ids_file.exists():
            try:
                data = json.loads(self.processed_ids_file.read_text())
                return set(data)
            except Exception as e:
                self.logger.warning(f"Failed to load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed message IDs to file."""
        try:
            self.processed_ids_file.write_text(json.dumps(list(self.processed_ids)))
        except Exception as e:
            self.logger.error(f"Failed to save processed IDs: {e}")

    async def check_for_updates(self) -> list:
        """
        Check Gmail for new unread emails with label "jobs".

        Returns:
            List of message dicts with id and threadId
        """
        try:
            # Query for unread emails with label "jobs"
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread label:jobs",
                maxResults=10
            ).execute()

            messages = results.get("messages", [])

            # Filter out already processed messages
            new_messages = [
                msg for msg in messages
                if msg["id"] not in self.processed_ids
            ]

            if new_messages:
                self.logger.info(f"Found {len(new_messages)} new application emails")

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    async def handle_item(self, item: dict) -> None:
        """
        Process a single email: extract PDF, create candidate, push to queue.

        Args:
            item: Message dict with id and threadId
        """
        message_id = item["id"]

        try:
            # Get full message
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            # Extract sender email and name
            headers = message["payload"]["headers"]
            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")

            # Parse sender email
            if "<" in sender and ">" in sender:
                email = sender.split("<")[1].split(">")[0]
                name = sender.split("<")[0].strip()
            else:
                email = sender
                name = sender

            self.logger.info(f"Processing application from {email}: {subject}")

            # Find PDF attachment
            pdf_bytes = None
            parts = message["payload"].get("parts", [])

            for part in parts:
                if part.get("filename", "").endswith(".pdf"):
                    attachment_id = part["body"].get("attachmentId")
                    if attachment_id:
                        attachment = self.service.users().messages().attachments().get(
                            userId="me",
                            messageId=message_id,
                            id=attachment_id
                        ).execute()

                        pdf_bytes = base64.urlsafe_b64decode(attachment["data"])
                        break

            if not pdf_bytes:
                self.logger.warning(f"No PDF attachment found in email {message_id}")
                self.processed_ids.add(message_id)
                self._save_processed_ids()
                return

            # Extract text from PDF
            cv_text = extract_text_from_pdf(pdf_bytes)
            self.logger.info(f"Extracted {len(cv_text)} characters from CV")

            # Create candidate in database
            async with AsyncSessionLocal() as db:
                # Assume job_id = 1 for now (TODO: match job from subject/label)
                candidate = await crud.create_candidate(
                    db=db,
                    job_id=1,
                    email=email,
                    name=name,
                    cv_text=cv_text,
                    gmail_message_id=message_id
                )

                self.logger.info(f"Created candidate {candidate.id} for {email}")

                # Push to Redis screening queue
                if not self.redis:
                    self.redis = await redis.from_url(self.redis_url)

                await self.redis.lpush("screening_queue", str(candidate.id))
                self.logger.info(f"Pushed candidate {candidate.id} to screening queue")

            # Mark as processed
            self.processed_ids.add(message_id)
            self._save_processed_ids()

        except Exception as e:
            self.logger.error(f"Error processing email {message_id}: {e}")
            # Don't mark as processed so we can retry

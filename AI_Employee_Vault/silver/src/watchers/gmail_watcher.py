"""
Gmail watcher for monitoring Gmail inbox.

This module implements Gmail monitoring using the Gmail API with OAuth2 authentication.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
import os
from dotenv import load_dotenv

from .base_watcher import BaseWatcher
from ..utils import get_logger, serialize_frontmatter, write_file

# Gmail API imports (will be installed via pip)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


class GmailWatcher(BaseWatcher):
    """
    Watcher for Gmail inbox using Gmail API.

    Monitors Gmail inbox for unread messages and creates action files.
    """

    def __init__(self, vault_path: str, config_path: str):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            config_path: Path to watcher configuration file

        Raises:
            ImportError: If Gmail API libraries not installed
            ValueError: If Gmail credentials not configured
        """
        super().__init__(vault_path, config_path, "gmail")

        if not GMAIL_AVAILABLE:
            raise ImportError(
                "Gmail API libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        # Load environment variables
        env_path = self.vault_path / "silver" / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Get Gmail credentials
        self.client_id = os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError(
                "Gmail credentials not configured. "
                "Run: python silver/scripts/setup_gmail.py"
            )

        # Initialize Gmail service
        self.service = None
        self._initialize_service()

        self.logger.info("Gmail watcher initialized successfully")

    def _initialize_service(self) -> None:
        """
        Initialize Gmail API service with OAuth2 credentials.

        Raises:
            Exception: If service initialization fails
        """
        try:
            # Create credentials from refresh token
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )

            # Refresh token if needed
            if not creds.valid:
                creds.refresh(Request())

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API service initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            raise

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail inbox for unread messages.

        Returns:
            List of message dictionaries

        Raises:
            HttpError: If Gmail API request fails
        """
        try:
            # Build query from config filters
            filters = self.config["gmail"]["filters"]
            query = " ".join(filters)
            max_results = self.config["gmail"]["max_results"]

            self.logger.debug(f"Querying Gmail with: {query}")

            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} messages matching query")

            # Fetch full message details
            message_list = []
            for msg in messages:
                try:
                    message = self._fetch_message(msg['id'])
                    if message:
                        message_list.append(message)
                except Exception as e:
                    self.logger.error(f"Failed to fetch message {msg['id']}: {e}")

            return message_list

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            raise

    def _fetch_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full message details from Gmail API.

        Args:
            message_id: Gmail message ID

        Returns:
            Message dictionary or None if fetch fails
        """
        try:
            # Get message
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {
                header['name']: header['value']
                for header in message['payload']['headers']
            }

            # Extract body
            body = self._extract_body(message['payload'])

            # Parse timestamp
            timestamp = datetime.fromtimestamp(
                int(message['internalDate']) / 1000
            ).isoformat()

            return {
                "id": message_id,
                "sender": headers.get('From', 'Unknown'),
                "subject": headers.get('Subject', '(No Subject)'),
                "body": body,
                "timestamp": timestamp,
                "labels": message.get('labelIds', []),
                "thread_id": message.get('threadId'),
                "metadata": {
                    "message_id": headers.get('Message-ID'),
                    "to": headers.get('To'),
                    "cc": headers.get('Cc'),
                    "has_attachments": self._has_attachments(message['payload'])
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch message {message_id}: {e}")
            return None

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract message body from Gmail payload.

        Args:
            payload: Gmail message payload

        Returns:
            Message body text
        """
        # Check if body is in payload
        if 'body' in payload and 'data' in payload['body']:
            return self._decode_body(payload['body']['data'])

        # Check parts for multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return self._decode_body(part['body']['data'])

                # Recursively check nested parts
                if 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        return body

        return "(No body content)"

    def _decode_body(self, data: str) -> str:
        """
        Decode base64-encoded message body.

        Args:
            data: Base64-encoded body data

        Returns:
            Decoded body text
        """
        try:
            # Gmail uses URL-safe base64 encoding
            decoded = base64.urlsafe_b64decode(data).decode('utf-8')
            return decoded
        except Exception as e:
            self.logger.error(f"Failed to decode body: {e}")
            return "(Failed to decode body)"

    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """
        Check if message has attachments.

        Args:
            payload: Gmail message payload

        Returns:
            True if message has attachments
        """
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
                if 'parts' in part:
                    if self._has_attachments(part):
                        return True
        return False

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create markdown action file for Gmail message.

        Args:
            item: Message data dictionary

        Returns:
            Path to created action file

        Raises:
            IOError: If file cannot be created
        """
        # Generate unique filename
        message_id = self._generate_message_id(item)
        filename = f"{message_id}.md"
        file_path = self.output_folder / filename

        # Create frontmatter
        frontmatter = {
            "id": message_id,
            "source": "gmail",
            "channel": "email",
            "sender": item["sender"],
            "subject": item["subject"],
            "timestamp": item["timestamp"],
            "status": "pending",
            "priority": "normal",
            "gmail_message_id": item["id"],
            "gmail_thread_id": item["thread_id"],
            "labels": item["labels"],
        }

        # Create body
        body = f"""# Message from {item['sender']}

**Subject**: {item['subject']}

**Received**: {datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %I:%M %p')}

## Content

{item['body']}

## Suggested Actions

- [ ] Reply to sender
- [ ] Add to task list
- [ ] File in appropriate folder
- [ ] Mark as done

## Metadata

- **Source**: gmail
- **Channel**: email
- **Message ID**: {item['id']}
- **Thread ID**: {item['thread_id']}
- **Labels**: {', '.join(item['labels'])}
- **Has Attachments**: {'Yes' if item['metadata']['has_attachments'] else 'No'}
"""

        # Serialize and write file
        content = serialize_frontmatter(frontmatter, body)
        write_file(file_path, content)

        self.logger.info(f"Created action file: {file_path}")
        return file_path


def main():
    """Main entry point for Gmail watcher."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path from environment or use default
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )
    config_path = f"{vault_path}/silver/config/watcher_config.yaml"

    try:
        # Initialize watcher
        watcher = GmailWatcher(vault_path, config_path)

        # Run check
        watcher.run()

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

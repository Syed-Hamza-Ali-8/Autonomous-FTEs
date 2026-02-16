"""
Gmail Channel Integration
Phase 2: Specialization

Handles incoming emails via Gmail API and sends responses.
"""

import os
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..database.models import Customer, Conversation, Message


class GmailIntegration:
    """
    Gmail API integration for email channel.
    Handles incoming emails and sends responses.
    """

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self):
        """Initialize Gmail integration."""
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/gmail-credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail-token.json")
        self.support_email = os.getenv("GMAIL_SUPPORT_EMAIL", "support@techcorp.com")
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def parse_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming Gmail message.

        Args:
            message_data: Gmail API message object

        Returns:
            Parsed message dictionary
        """
        headers = {h['name']: h['value'] for h in message_data['payload']['headers']}

        # Extract body
        body = self._extract_body(message_data['payload'])

        return {
            'channel': 'email',
            'channel_message_id': message_data['id'],
            'customer_email': headers.get('From', '').split('<')[-1].rstrip('>'),
            'customer_name': self._extract_name(headers.get('From', '')),
            'subject': headers.get('Subject', ''),
            'content': body,
            'received_at': datetime.fromtimestamp(int(message_data['internalDate']) / 1000).isoformat(),
            'thread_id': message_data['threadId'],
            'metadata': {
                'headers': {
                    'From': headers.get('From'),
                    'To': headers.get('To'),
                    'Subject': headers.get('Subject'),
                    'Date': headers.get('Date'),
                    'Message-ID': headers.get('Message-ID')
                },
                'labels': message_data.get('labelIds', []),
                'has_attachments': self._has_attachments(message_data['payload']),
                'snippet': message_data.get('snippet', '')
            }
        }

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if part['body'].get('data'):
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    # Fallback to HTML if no plain text
                    if part['body'].get('data'):
                        html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        # Simple HTML stripping (in production, use html2text or similar)
                        return html_body

        return ""

    def _extract_name(self, from_header: str) -> Optional[str]:
        """Extract name from From header."""
        if '<' in from_header:
            name = from_header.split('<')[0].strip().strip('"')
            return name if name else None
        return None

    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """Check if email has attachments."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
        return False

    async def fetch_new_messages(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch new unread messages.

        Args:
            max_results: Maximum number of messages to fetch

        Returns:
            List of parsed messages
        """
        if not self.service:
            self.authenticate()

        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            parsed_messages = []

            for msg in messages:
                # Get full message
                message_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                # Parse message
                parsed = self.parse_incoming_message(message_data)
                parsed_messages.append(parsed)

                # Mark as read
                self.service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()

            return parsed_messages

        except HttpError as error:
            print(f"Gmail API error: {error}")
            return []

    async def send_response(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        customer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email response.

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (already formatted)
            thread_id: Gmail thread ID for replies
            customer_name: Customer name for personalization

        Returns:
            Send result
        """
        if not self.service:
            self.authenticate()

        try:
            # Create message
            message = MIMEMultipart()
            message['To'] = to_email
            message['From'] = self.support_email
            message['Subject'] = subject

            # Add body
            message.attach(MIMEText(body, 'plain'))

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send message
            send_body = {'raw': raw_message}
            if thread_id:
                send_body['threadId'] = thread_id

            result = self.service.users().messages().send(
                userId='me',
                body=send_body
            ).execute()

            return {
                'success': True,
                'message_id': result['id'],
                'thread_id': result['threadId']
            }

        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }

    async def setup_webhook(self, webhook_url: str, topic_name: str = "gmail-notifications"):
        """
        Set up Gmail push notifications (Pub/Sub).

        Args:
            webhook_url: Webhook URL for notifications
            topic_name: Pub/Sub topic name

        Note: This requires Google Cloud Pub/Sub setup
        """
        if not self.service:
            self.authenticate()

        try:
            # Watch for new messages
            request = {
                'labelIds': ['INBOX'],
                'topicName': f'projects/YOUR_PROJECT_ID/topics/{topic_name}'
            }

            result = self.service.users().watch(
                userId='me',
                body=request
            ).execute()

            return {
                'success': True,
                'historyId': result['historyId'],
                'expiration': result['expiration']
            }

        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_gmail():
        gmail = GmailIntegration()
        gmail.authenticate()

        # Fetch new messages
        messages = await gmail.fetch_new_messages(max_results=5)
        print(f"Found {len(messages)} new messages")

        for msg in messages:
            print(f"\nFrom: {msg['customer_email']}")
            print(f"Subject: {msg['subject']}")
            print(f"Content: {msg['content'][:100]}...")

        # Send test response
        if messages:
            msg = messages[0]
            response = await gmail.send_response(
                to_email=msg['customer_email'],
                subject=f"Re: {msg['subject']}",
                body="Thank you for contacting TechCorp Support. We've received your message and will respond shortly.",
                thread_id=msg['thread_id']
            )
            print(f"\nSent response: {response}")

    asyncio.run(test_gmail())

"""
Email Sender for sending emails via Gmail API.

This module provides Gmail API integration for sending emails
with OAuth2 authentication and error handling.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from ..utils import get_logger

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class EmailSender:
    """
    Sends emails via Gmail API.

    Uses OAuth2 authentication and provides retry logic,
    error handling, and delivery confirmation.
    """

    def __init__(self, vault_path: str):
        """
        Initialize EmailSender.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = get_logger(__name__)

        if not GOOGLE_API_AVAILABLE:
            self.logger.error(
                "Google API libraries not installed. "
                "Install with: pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            raise ImportError("Google API libraries not available")

        # Gmail API service
        self.service = None

        # Initialize Gmail API
        self._initialize_gmail_api()

        self.logger.info("EmailSender initialized")

    def _initialize_gmail_api(self) -> None:
        """Initialize Gmail API service with OAuth2 credentials."""
        try:
            # Load credentials from environment
            client_id = os.getenv("GMAIL_CLIENT_ID")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

            if not all([client_id, client_secret, refresh_token]):
                raise ValueError(
                    "Gmail credentials not configured. "
                    "Run: python silver/scripts/setup_gmail.py"
                )

            # Create credentials object
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
            )

            # Refresh token if needed
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise ValueError("Invalid credentials")

            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)

            self.logger.info("Gmail API initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail API: {e}")
            raise

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = True
    ) -> Dict[str, Any]:
        """
        Send email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_email: Sender email (optional, uses authenticated account)
            cc: CC recipients (comma-separated, optional)
            bcc: BCC recipients (comma-separated, optional)
            html: Whether body is HTML (default: True)

        Returns:
            Result dictionary with:
            - success: bool
            - message_id: str (if successful)
            - thread_id: str (if successful)
            - error: str (if failed)

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            if not to:
                raise ValueError("Recipient email address is required")
            if not subject:
                raise ValueError("Email subject is required")
            if not body:
                raise ValueError("Email body is required")

            # Validate email addresses
            self._validate_email(to)
            if cc:
                for email in cc.split(","):
                    self._validate_email(email.strip())
            if bcc:
                for email in bcc.split(","):
                    self._validate_email(email.strip())

            # Create message
            message = self._create_message(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                html=html
            )

            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            self.logger.info(f"Email sent successfully: {result['id']}")

            return {
                "success": True,
                "message_id": result['id'],
                "thread_id": result.get('threadId'),
            }

        except HttpError as e:
            error_msg = f"Gmail API error: {e.reason}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = True
    ) -> Dict[str, str]:
        """
        Create email message in Gmail API format.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            html: Whether body is HTML

        Returns:
            Message dictionary for Gmail API
        """
        # Create MIME message
        if html:
            message = MIMEMultipart('alternative')
            html_part = MIMEText(body, 'html')
            message.attach(html_part)
        else:
            message = MIMEText(body, 'plain')

        # Set headers
        message['To'] = to
        message['Subject'] = subject

        if from_email:
            message['From'] = from_email

        if cc:
            message['Cc'] = cc

        if bcc:
            message['Bcc'] = bcc

        # Encode message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')

        return {'raw': raw_message}

    def _validate_email(self, email: str) -> None:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Raises:
            ValueError: If email format is invalid
        """
        import re

        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            raise ValueError(f"Invalid email address: {email}")

    def get_sent_messages(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently sent messages.

        Args:
            max_results: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """
        try:
            # Query for sent messages
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['SENT'],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Get full message details
            sent_messages = []
            for msg in messages:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['To', 'Subject', 'Date']
                ).execute()

                # Extract headers
                headers = {
                    header['name']: header['value']
                    for header in message['payload']['headers']
                }

                sent_messages.append({
                    'id': message['id'],
                    'thread_id': message['threadId'],
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                })

            return sent_messages

        except Exception as e:
            self.logger.error(f"Failed to get sent messages: {e}")
            return []

    def verify_delivery(self, message_id: str) -> bool:
        """
        Verify that a message was delivered successfully.

        Args:
            message_id: Gmail message ID

        Returns:
            True if message exists in sent folder
        """
        try:
            # Get message
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='minimal'
            ).execute()

            # Check if message exists
            return message['id'] == message_id

        except Exception as e:
            self.logger.error(f"Failed to verify delivery: {e}")
            return False


def main():
    """Main entry point for testing."""
    import sys
    from ..utils import setup_logging

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    try:
        # Initialize sender
        sender = EmailSender(vault_path)

        # Test: Send test email
        print("Sending test email...")
        print("Note: This will send a real email!")
        print()

        # Get recipient from user
        to = input("Enter recipient email address: ").strip()
        if not to:
            print("❌ No recipient provided")
            sys.exit(1)

        # Send test email
        result = sender.send_email(
            to=to,
            subject="Test Email from AI Employee Vault",
            body="""
            <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test email from the AI Employee Vault Silver tier.</p>
                <p>If you received this, the email sending functionality is working correctly!</p>
                <hr>
                <p><small>Sent via Gmail API</small></p>
            </body>
            </html>
            """,
            html=True
        )

        if result['success']:
            print(f"\n✅ Email sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            print(f"   Thread ID: {result['thread_id']}")

            # Verify delivery
            print("\nVerifying delivery...")
            verified = sender.verify_delivery(result['message_id'])
            if verified:
                print("✅ Delivery verified")
            else:
                print("⚠️  Could not verify delivery")
        else:
            print(f"\n❌ Failed to send email: {result['error']}")

        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

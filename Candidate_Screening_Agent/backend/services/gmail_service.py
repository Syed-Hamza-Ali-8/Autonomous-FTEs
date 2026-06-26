import os
import base64
import uuid
import logging
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class GmailService:
    """Gmail service for sending emails via Gmail API with OAuth2."""

    def __init__(self):
        """Initialize Gmail service with OAuth2 credentials."""
        self.client_id = os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
        self.jobs_inbox_email = os.getenv("JOBS_INBOX_EMAIL", "jobs@yourdomain.com")

        # Create credentials
        self.credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        # Build Gmail service
        self.service = build("gmail", "v1", credentials=self.credentials)

    def _create_message(self, to: str, subject: str, body: str,
                         in_reply_to: str = None, references: str = None) -> tuple[dict, str]:
        """Create email message in Gmail API format with optional threading headers.

        Uses raw email construction because Python's MIMEText rejects
        Gmail's Message-ID format (contains '=' character).

        Returns:
            Tuple of (message dict, Message-ID header value)
        """
        message_id = f"<csa-{uuid.uuid4().hex}@mail.gmail.com>"

        # Build raw email manually to preserve threading headers
        headers = []
        headers.append("MIME-Version: 1.0")
        headers.append('Content-Type: text/html; charset="utf-8"')
        headers.append(f"To: {to}")
        headers.append(f"From: {self.jobs_inbox_email}")
        headers.append(f"Subject: {subject}")
        headers.append(f"Message-ID: {message_id}")

        # Threading headers
        if in_reply_to:
            headers.append(f"In-Reply-To: {in_reply_to}")
        if references:
            headers.append(f"References: {references}")
        elif in_reply_to:
            headers.append(f"References: {in_reply_to}")

        # Combine headers and body
        raw_email = "\r\n".join(headers) + "\r\n\r\n" + body

        raw_message = base64.urlsafe_b64encode(raw_email.encode("utf-8")).decode()
        return {"raw": raw_message}, message_id

    def send_email(self, to: str, subject: str, body: str,
                    in_reply_to: str = None, references: str = None) -> str:
        """
        Send email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML)
            in_reply_to: Message-ID this reply references (for threading)
            references: Full References chain (for threading)

        Returns:
            Message-ID header value (for reply matching)
        """
        # Check DRY_RUN mode
        if os.getenv("DRY_RUN", "true").lower() == "true":
            logger.info(f"[DRY_RUN] Email to {to}: {subject}")
            logger.info(f"[DRY_RUN] Body preview: {body[:200]}...")
            return f"fake_msg_id_{uuid.uuid4().hex[:8]}"

        # Send real email
        try:
            message, our_message_id = self._create_message(
                to, subject, body,
                in_reply_to=in_reply_to,
                references=references
            )
            result = self.service.users().messages().send(
                userId="me",
                body=message
            ).execute()

            # Fetch Gmail's actual Message-ID (Gmail overrides our custom Message-ID)
            sent_msg = self.service.users().messages().get(
                userId="me",
                id=result["id"],
                format="metadata",
                metadataHeaders=["Message-ID"]
            ).execute()
            thread_id = result.get("threadId", "")
            gmail_message_id = our_message_id
            for h in sent_msg.get("payload", {}).get("headers", []):
                # Gmail returns "Message-Id" (lowercase 'i')
                if h["name"].lower() == "message-id":
                    gmail_message_id = h["value"]
                    break

            logger.info(f"Email sent to {to}: {subject} (Gmail-ID: {gmail_message_id})")
            # Return tuple: (gmail_actual_id, thread_id)
            return gmail_message_id, thread_id

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise Exception(f"Gmail API error: {e}")

    def send_screening_questions(
        self,
        to: str,
        candidate_name: str,
        job_title: str,
        questions: list[str]
    ) -> str:
        """
        Send screening questions to candidate.

        Args:
            to: Candidate email address
            candidate_name: Candidate's name
            job_title: Job title
            questions: List of 5 screening questions

        Returns:
            Gmail message ID
        """
        subject = f"Screening Questions - {job_title}"

        # Format questions as HTML list
        questions_html = "<ol>\n"
        for question in questions:
            questions_html += f"    <li>{question}</li>\n"
        questions_html += "</ol>"

        body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {candidate_name},</p>

    <p>Thank you for applying for the <strong>{job_title}</strong> position. We've reviewed your CV and would like to learn more about your experience.</p>

    <p>Please answer the following questions:</p>

    {questions_html}

    <p>Please reply to this email with your answers at your earliest convenience.</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>"""

        return self.send_email(to, subject, body)

    def send_interview_invite(
        self,
        to: str,
        candidate_name: str,
        job_title: str
    ) -> str:
        """
        Send interview invite to candidate.

        Args:
            to: Candidate email address
            candidate_name: Candidate's name
            job_title: Job title

        Returns:
            Gmail message ID
        """
        subject = f"Interview Invitation - {job_title}"

        body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {candidate_name},</p>

    <p>Congratulations! We're impressed with your application for the <strong>{job_title}</strong> position and would like to invite you for an interview.</p>

    <p>Our hiring manager will reach out shortly to schedule a time that works for you.</p>

    <p>We look forward to speaking with you!</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>"""

        return self.send_email(to, subject, body)

    def send_rejection_email(
        self,
        to: str,
        candidate_name: str,
        job_title: str,
        reason: str = None
    ) -> str:
        """
        Send empathetic rejection email to candidate.

        Args:
            to: Candidate email address
            candidate_name: Candidate's name
            job_title: Job title
            reason: Optional rejection reason (not included in email)

        Returns:
            Gmail message ID
        """
        subject = f"Application Update - {job_title}"

        body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Dear {candidate_name},</p>

    <p>Thank you for your interest in the <strong>{job_title}</strong> position and for taking the time to apply.</p>

    <p>After careful consideration, we've decided to move forward with other candidates whose experience more closely aligns with our current needs.</p>

    <p>We appreciate your interest in our company and wish you the best in your job search.</p>

    <p>Best regards,<br>
    Hiring Team</p>
</body>
</html>"""

        return self.send_email(to, subject, body)

    def send_daily_digest(
        self,
        to: str,
        digest_data: dict
    ) -> str:
        """
        Send daily talent digest to hiring manager.

        Args:
            to: Hiring manager email address
            digest_data: Dict with candidate counts and summary

        Returns:
            Gmail message ID
        """
        subject = f"Daily Talent Digest - {digest_data.get('date', 'Today')}"

        # Format stats
        stats = digest_data.get("stats", {})
        summary = digest_data.get("summary", "No new activity today.")

        body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>Daily Talent Digest</h2>

    <h3>Summary</h3>
    <p>{summary}</p>

    <h3>Pipeline Stats (Last 24 Hours)</h3>
    <ul>
        <li><strong>New Applications:</strong> {stats.get('new_applications', 0)}</li>
        <li><strong>Screening Questions Sent:</strong> {stats.get('questions_sent', 0)}</li>
        <li><strong>Replies Received:</strong> {stats.get('replies_received', 0)}</li>
        <li><strong>Pending Approvals:</strong> {stats.get('pending_approvals', 0)}</li>
        <li><strong>Shortlisted:</strong> {stats.get('shortlisted', 0)}</li>
        <li><strong>Rejected:</strong> {stats.get('rejected', 0)}</li>
    </ul>

    <p><a href="http://localhost:3000" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Dashboard</a></p>

    <p>Best regards,<br>
    Candidate Screening Agent</p>
</body>
</html>"""

        return self.send_email(to, subject, body)


# Create singleton instance
gmail_service = GmailService()

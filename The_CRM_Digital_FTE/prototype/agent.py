"""
Basic Message Processing Prototype
Phase: Incubation (TASK-004)

This is a simple prototype to test the core message processing loop.
It accepts messages from any channel and generates basic responses.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import json


class MessageProcessor:
    """
    Basic message processor for Customer Success AI agent.
    Handles messages from email, WhatsApp, and web form channels.
    """

    def __init__(self):
        """Initialize the message processor."""
        self.supported_channels = ["email", "whatsapp", "web_form"]

    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response.

        Args:
            message: Dictionary containing:
                - channel: str (email, whatsapp, web_form)
                - from: str (email or phone)
                - customer_name: str (optional)
                - subject: str (optional, for email/web)
                - body: str (message content)
                - category: str (optional)
                - priority: str (optional)

        Returns:
            Dictionary containing:
                - success: bool
                - response: str (generated response)
                - channel: str
                - should_escalate: bool
                - escalation_reason: str (if applicable)
                - processing_time_ms: int
        """
        start_time = datetime.now()

        # Validate message
        validation_result = self._validate_message(message)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "processing_time_ms": self._get_elapsed_ms(start_time)
            }

        # Extract message details
        channel = message.get("channel")
        customer_name = message.get("customer_name", "there")
        body = message.get("body", "")
        subject = message.get("subject", "")

        # Check for escalation triggers
        escalation_check = self._check_escalation(message)

        if escalation_check["should_escalate"]:
            response = self._generate_escalation_response(
                customer_name,
                escalation_check["reason"],
                channel
            )
            return {
                "success": True,
                "response": response,
                "channel": channel,
                "should_escalate": True,
                "escalation_reason": escalation_check["reason"],
                "processing_time_ms": self._get_elapsed_ms(start_time)
            }

        # Generate response based on message content
        response = self._generate_response(message)

        return {
            "success": True,
            "response": response,
            "channel": channel,
            "should_escalate": False,
            "processing_time_ms": self._get_elapsed_ms(start_time)
        }

    def _validate_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming message structure."""
        if not isinstance(message, dict):
            return {"valid": False, "error": "Message must be a dictionary"}

        if "channel" not in message:
            return {"valid": False, "error": "Missing required field: channel"}

        if message["channel"] not in self.supported_channels:
            return {
                "valid": False,
                "error": f"Unsupported channel: {message['channel']}"
            }

        if "body" not in message or not message["body"]:
            return {"valid": False, "error": "Missing required field: body"}

        return {"valid": True}

    def _check_escalation(self, message: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check if message should be escalated to human agent.
        Simple keyword-based detection for prototype.
        """
        body = message.get("body", "").lower()
        subject = message.get("subject", "").lower()
        combined = f"{subject} {body}"

        # Billing/financial keywords
        billing_keywords = [
            "refund", "charged twice", "billing error", "double charge",
            "cancel subscription", "invoice", "payment"
        ]
        if any(keyword in combined for keyword in billing_keywords):
            return {"should_escalate": True, "reason": "billing_issue"}

        # Sales opportunity keywords
        sales_keywords = [
            "enterprise pricing", "custom pricing", "200 users", "100 users",
            "partnership", "reseller"
        ]
        if any(keyword in combined for keyword in sales_keywords):
            return {"should_escalate": True, "reason": "sales_opportunity"}

        # Negative sentiment keywords
        negative_keywords = [
            "frustrated", "angry", "unacceptable", "ridiculous",
            "switching to", "terrible"
        ]
        if any(keyword in combined for keyword in negative_keywords):
            return {"should_escalate": True, "reason": "negative_sentiment"}

        # Data loss/critical bugs
        critical_keywords = [
            "data loss", "tasks disappeared", "all gone", "deleted",
            "security breach"
        ]
        if any(keyword in combined for keyword in critical_keywords):
            return {"should_escalate": True, "reason": "critical_issue"}

        return {"should_escalate": False}

    def _generate_response(self, message: Dict[str, Any]) -> str:
        """
        Generate response based on message content.
        For prototype: Simple template-based responses.
        """
        channel = message.get("channel")
        customer_name = message.get("customer_name", "there")
        body = message.get("body", "").lower()

        # Detect issue type and generate appropriate response
        if "password" in body and "reset" in body:
            return self._password_reset_response(customer_name, channel)
        elif "export" in body and "data" in body:
            return self._data_export_response(customer_name, channel)
        elif "slack" in body or "integration" in body:
            return self._integration_help_response(customer_name, channel)
        elif "recurring task" in body:
            return self._recurring_task_response(customer_name, channel)
        elif "dark mode" in body:
            return self._feature_request_response(customer_name, channel)
        elif "api" in body:
            return self._api_documentation_response(customer_name, channel)
        elif "thank" in body or "thanks" in body:
            return self._thank_you_response(customer_name, channel)
        else:
            return self._general_help_response(customer_name, channel)

    def _password_reset_response(self, name: str, channel: str) -> str:
        """Generate password reset help response."""
        if channel == "email":
            return f"""Dear {name},

Thank you for reaching out about the password reset issue.

I understand how frustrating it can be when you can't access your account. Let me help you resolve this right away.

Password reset links expire after 1 hour for security reasons. Here's how to successfully reset your password:

1. Go to www.techcorp.com/login
2. Click "Forgot Password?"
3. Enter your email address
4. Check your inbox for the reset link (it may take 2-3 minutes)
5. Click the link within 1 hour
6. Create a new password (minimum 8 characters, with 1 uppercase, 1 lowercase, and 1 number)

If you don't receive the email within 5 minutes, please check your spam/junk folder. If you're still having trouble, reply to this email and I'll assist you further.

Is there anything else I can help you with today?

Best regards,
TechCorp AI Support Team

---
This response was generated by our AI assistant."""

        elif channel == "whatsapp":
            return f"""Hi {name}! 👋

Password reset links expire after 1 hour. Here's what to do:

1. Go to techcorp.com/login
2. Click "Forgot Password"
3. Use the new link within 1 hour
4. Create password (8+ chars, mix of upper/lower/numbers)

Check spam folder if you don't see the email in 5 mins.

Need more help? Just ask! 😊"""

        else:  # web_form
            return f"""Thank you for contacting TechCorp Support, {name}!

I can help you reset your password. Password reset links expire after 1 hour for security. Here's how to get a new one:

**Steps to Reset:**
1. Visit www.techcorp.com/login
2. Click "Forgot Password?"
3. Enter your email address
4. Check your inbox (and spam folder)
5. Click the link within 1 hour
6. Create a new password (8+ characters, including uppercase, lowercase, and numbers)

**Helpful Resources:**
- Password Security Best Practices: help.techcorp.com/security
- Account Troubleshooting Guide: help.techcorp.com/account

If you continue to experience issues, please reply to this ticket and I'll be happy to assist further.

---
This response was generated by our AI assistant."""

    def _data_export_response(self, name: str, channel: str) -> str:
        """Generate data export help response."""
        if channel == "email":
            return f"""Dear {name},

Thank you for reaching out about exporting your project data.

I'd be happy to guide you through the data export process. Here's how to export all your project data including tasks, time entries, and comments:

**Steps to Export Project Data:**

1. Go to Settings > Data Export
2. Select the data you want to export:
   - Tasks and projects
   - Time tracking data
   - Team members
   - Files and attachments
3. Choose your preferred format:
   - JSON (for developers)
   - CSV (for spreadsheets)
   - Excel (formatted workbook)
4. Click "Export"
5. You'll receive a download link via email within 5-30 minutes (depending on data size)
6. The download link will be available for 7 days

**Note:** The export includes all data from your workspace. If you only need specific project data, you can export individual projects from the project settings menu.

**Helpful Resources:**
- Data Export Guide: help.techcorp.com/data-export
- Data Import Guide: help.techcorp.com/data-import

Is there anything else I can help you with?

Best regards,
TechCorp AI Support Team

---
This response was generated by our AI assistant."""

        elif channel == "whatsapp":
            return f"""Hi {name}! 📊

To export project data:

1. Go to Settings > Data Export
2. Select what to export (tasks, time, files)
3. Choose format (JSON, CSV, Excel)
4. Click "Export"
5. Check email for download link (5-30 mins)

Link valid for 7 days!

Need help with anything else? 😊"""

        else:  # web_form
            return f"""Thank you for contacting TechCorp Support, {name}!

Here's how to export your project data:

**Export Steps:**
1. Navigate to Settings > Data Export
2. Select data types (tasks, time entries, comments, files)
3. Choose format: JSON, CSV, or Excel
4. Click "Export"
5. Download link sent to your email (5-30 minutes)

**Helpful Resources:**
- Complete Data Export Guide: help.techcorp.com/data-export
- Data Formats Explained: help.techcorp.com/export-formats

The download link will be available for 7 days. If you need help with a specific export format, let me know!

---
This response was generated by our AI assistant."""

    def _integration_help_response(self, name: str, channel: str) -> str:
        """Generate integration troubleshooting response."""
        if channel == "whatsapp":
            return f"""Hi {name}! 🔧

For Slack integration issues:

1. Go to Settings > Integrations
2. Disconnect Slack
3. Reconnect and authorize
4. Select the right channel
5. Test with a task update

Still not working? Let me know! 😊"""
        else:
            return f"""Hi {name},

I can help you troubleshoot the integration issue. Here are the steps to reconnect:

1. Go to Settings > Integrations
2. Find the integration and click "Disconnect"
3. Click "Connect" again
4. Authorize the integration
5. Configure notification settings
6. Test with a sample action

If the issue persists after reconnecting, please let me know and I'll escalate to our technical team.

---
This response was generated by our AI assistant."""

    def _recurring_task_response(self, name: str, channel: str) -> str:
        """Generate recurring task setup response."""
        if channel == "whatsapp":
            return f"""Hi {name}! 🔄

To create recurring tasks:

1. Create a task
2. Click the task to open
3. Click "Recurrence" icon
4. Set frequency (daily/weekly/monthly)
5. Choose days (e.g., every Monday)
6. Save!

Easy! 😊"""
        else:
            return f"""Hi {name},

Here's how to set up recurring tasks:

1. Create a new task or open an existing one
2. Click the "Recurrence" icon (circular arrow)
3. Select frequency: Daily, Weekly, or Monthly
4. For weekly: Choose specific days (e.g., every Monday)
5. Set end date (optional) or leave it to repeat indefinitely
6. Save the task

The task will automatically create new instances based on your schedule!

Learn more: help.techcorp.com/recurring-tasks

---
This response was generated by our AI assistant."""

    def _feature_request_response(self, name: str, channel: str) -> str:
        """Generate feature request acknowledgment."""
        if channel == "whatsapp":
            return f"""Hi {name}! 💡

Thanks for the suggestion! I've forwarded your request to our product team.

Track feature requests at community.techcorp.com

Anything else I can help with? 😊"""
        else:
            return f"""Hi {name},

Thank you for the feature suggestion! We love hearing ideas from our users.

I've forwarded your request to our product team for consideration. While we can't guarantee when or if this feature will be implemented, we do review all feedback carefully.

You can track feature requests and vote on ideas at community.techcorp.com.

Is there anything else I can help you with today?

---
This response was generated by our AI assistant."""

    def _api_documentation_response(self, name: str, channel: str) -> str:
        """Generate API documentation response."""
        if channel == "whatsapp":
            return f"""Hi {name}! 🔌

API docs: api.techcorp.com/docs

Get your API key:
Settings > API > Generate Key

Rate limits vary by plan!

Need more help? 😊"""
        else:
            return f"""Hi {name},

You can find our comprehensive API documentation at: https://api.techcorp.com/docs

**To get your API key:**
1. Go to Settings > API
2. Click "Generate API Key"
3. Copy and save the key securely
4. Use it in your API requests

**Rate Limits by Plan:**
- Free: 100 requests/hour
- Starter: 1,000 requests/hour
- Professional: 10,000 requests/hour
- Enterprise: Unlimited

The documentation includes code examples, authentication guides, and endpoint references.

---
This response was generated by our AI assistant."""

    def _thank_you_response(self, name: str, channel: str) -> str:
        """Generate thank you acknowledgment."""
        if channel == "whatsapp":
            return f"""Thank you, {name}! 😊 We're always here if you need anything else. Happy task managing! 👍"""
        else:
            return f"""Thank you so much for the kind words, {name}! Feedback like this makes our day. We're always here if you need anything else. Happy task managing! 😊

---
This response was generated by our AI assistant."""

    def _general_help_response(self, name: str, channel: str) -> str:
        """Generate general help response."""
        if channel == "whatsapp":
            return f"""Hi {name}! 👋

I'd be happy to help! Could you provide a bit more detail about what you need assistance with?

You can also check our help center: help.techcorp.com

I'm here to help! 😊"""
        else:
            return f"""Hi {name},

Thank you for contacting TechCorp Support!

I'd be happy to help you. To provide the best assistance, could you please provide more details about your question or issue?

In the meantime, you might find these resources helpful:
- Help Center: help.techcorp.com
- Video Tutorials: help.techcorp.com/videos
- Community Forum: community.techcorp.com

I'm here to assist you!

---
This response was generated by our AI assistant."""

    def _generate_escalation_response(self, name: str, reason: str, channel: str) -> str:
        """Generate escalation notification response."""
        reason_messages = {
            "billing_issue": "This requires attention from our billing team",
            "sales_opportunity": "This requires attention from our sales team",
            "negative_sentiment": "This requires specialized attention",
            "critical_issue": "This requires immediate attention from our technical team"
        }

        reason_msg = reason_messages.get(reason, "This requires specialized attention")

        if channel == "whatsapp":
            return f"""Hi {name}!

{reason_msg}. I'm connecting you with our team who will reach out within 2-4 hours.

You'll get an email confirmation shortly.

Anything else I can help with? 😊"""
        else:
            return f"""Hi {name},

I understand this is important. {reason_msg}. I'm escalating your request to them now, and they'll reach out to you within 4 hours.

You'll receive an email confirmation with your ticket reference shortly.

Is there anything else I can assist you with in the meantime?

---
This response was generated by our AI assistant."""

    def _get_elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed time in milliseconds."""
        elapsed = datetime.now() - start_time
        return int(elapsed.total_seconds() * 1000)


# Example usage
if __name__ == "__main__":
    processor = MessageProcessor()

    # Test with a sample message
    test_message = {
        "channel": "email",
        "from": "john.doe@example.com",
        "customer_name": "John Doe",
        "subject": "Password reset link not working",
        "body": "I've been trying to reset my password but the link expired.",
        "priority": "high",
        "category": "technical"
    }

    result = processor.process_message(test_message)

    print("=" * 80)
    print("MESSAGE PROCESSING RESULT")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print(f"Channel: {result['channel']}")
    print(f"Should Escalate: {result['should_escalate']}")
    print(f"Processing Time: {result['processing_time_ms']}ms")
    print("\nRESPONSE:")
    print("-" * 80)
    print(result['response'])
    print("=" * 80)

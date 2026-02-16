"""
WhatsApp Channel Integration
Phase 2: Specialization

Handles incoming WhatsApp messages via Twilio and sends responses.
"""

import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from twilio.rest import Client
from twilio.request_validator import RequestValidator


class WhatsAppIntegration:
    """
    Twilio WhatsApp integration for WhatsApp channel.
    Handles incoming messages and sends responses.
    """

    def __init__(self):
        """Initialize WhatsApp integration."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

        if not self.account_sid or not self.auth_token:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set")

        self.client = Client(self.account_sid, self.auth_token)
        self.validator = RequestValidator(self.auth_token)

    def validate_webhook(self, url: str, params: Dict[str, Any], signature: str) -> bool:
        """
        Validate Twilio webhook signature.

        Args:
            url: Full webhook URL
            params: POST parameters
            signature: X-Twilio-Signature header

        Returns:
            True if signature is valid
        """
        return self.validator.validate(url, params, signature)

    def parse_incoming_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming Twilio WhatsApp webhook.

        Args:
            webhook_data: Twilio webhook POST data

        Returns:
            Parsed message dictionary
        """
        # Extract phone number (remove 'whatsapp:' prefix)
        from_number = webhook_data.get('From', '')
        phone = self._normalize_phone(from_number)

        # Extract customer name if provided
        profile_name = webhook_data.get('ProfileName', '')

        # Extract message content
        body = webhook_data.get('Body', '')

        # Extract media information
        num_media = int(webhook_data.get('NumMedia', 0))
        media_urls = []
        media_types = []

        for i in range(num_media):
            media_url = webhook_data.get(f'MediaUrl{i}')
            media_type = webhook_data.get(f'MediaContentType{i}')
            if media_url:
                media_urls.append(media_url)
                media_types.append(media_type)

        return {
            'channel': 'whatsapp',
            'channel_message_id': webhook_data.get('MessageSid'),
            'customer_phone': phone,
            'customer_name': profile_name if profile_name else None,
            'content': body,
            'received_at': datetime.now().isoformat(),
            'metadata': {
                'from': webhook_data.get('From'),
                'to': webhook_data.get('To'),
                'message_sid': webhook_data.get('MessageSid'),
                'account_sid': webhook_data.get('AccountSid'),
                'num_media': num_media,
                'media_urls': media_urls,
                'media_types': media_types,
                'profile_name': profile_name,
                'wa_id': webhook_data.get('WaId'),  # WhatsApp ID
                'has_media': num_media > 0
            }
        }

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number.

        Args:
            phone: Phone number (may include 'whatsapp:' prefix)

        Returns:
            Normalized phone number (E.164 format)
        """
        # Remove 'whatsapp:' prefix if present
        phone = phone.replace('whatsapp:', '').strip()

        # Remove all non-digit characters except '+'
        phone = re.sub(r'[^\d+]', '', phone)

        # Ensure it starts with '+'
        if not phone.startswith('+'):
            # Assume US number if no country code
            phone = '+1' + phone

        return phone

    async def send_response(
        self,
        to_phone: str,
        body: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message response.

        Args:
            to_phone: Recipient phone number (E.164 format)
            body: Message body (already formatted for WhatsApp)
            media_url: Optional media URL to send

        Returns:
            Send result
        """
        try:
            # Ensure phone has 'whatsapp:' prefix
            if not to_phone.startswith('whatsapp:'):
                to_phone = f'whatsapp:{to_phone}'

            # Prepare message parameters
            message_params = {
                'from_': self.whatsapp_number,
                'to': to_phone,
                'body': body
            }

            # Add media if provided
            if media_url:
                message_params['media_url'] = [media_url]

            # Send message
            message = self.client.messages.create(**message_params)

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': to_phone
            }

        except Exception as error:
            return {
                'success': False,
                'error': str(error)
            }

    async def send_template_message(
        self,
        to_phone: str,
        template_sid: str,
        content_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message (for approved templates).

        Args:
            to_phone: Recipient phone number
            template_sid: Twilio Content Template SID
            content_variables: Template variables

        Returns:
            Send result
        """
        try:
            # Ensure phone has 'whatsapp:' prefix
            if not to_phone.startswith('whatsapp:'):
                to_phone = f'whatsapp:{to_phone}'

            # Prepare message parameters
            message_params = {
                'from_': self.whatsapp_number,
                'to': to_phone,
                'content_sid': template_sid
            }

            # Add content variables if provided
            if content_variables:
                message_params['content_variables'] = content_variables

            # Send message
            message = self.client.messages.create(**message_params)

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': to_phone
            }

        except Exception as error:
            return {
                'success': False,
                'error': str(error)
            }

    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get message delivery status.

        Args:
            message_sid: Twilio message SID

        Returns:
            Message status information
        """
        try:
            message = self.client.messages(message_sid).fetch()

            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent.isoformat() if message.date_sent else None,
                'date_updated': message.date_updated.isoformat() if message.date_updated else None
            }

        except Exception as error:
            return {
                'success': False,
                'error': str(error)
            }

    def parse_status_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Twilio status callback.

        Args:
            callback_data: Twilio status callback POST data

        Returns:
            Parsed status information
        """
        return {
            'message_sid': callback_data.get('MessageSid'),
            'message_status': callback_data.get('MessageStatus'),
            'error_code': callback_data.get('ErrorCode'),
            'error_message': callback_data.get('ErrorMessage'),
            'to': callback_data.get('To'),
            'from': callback_data.get('From'),
            'account_sid': callback_data.get('AccountSid'),
            'timestamp': datetime.now().isoformat()
        }

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media from Twilio.

        Args:
            media_url: Twilio media URL

        Returns:
            Media content as bytes, or None if failed
        """
        try:
            # Twilio media URLs require authentication
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    media_url,
                    auth=(self.account_sid, self.auth_token)
                )

                if response.status_code == 200:
                    return response.content
                else:
                    return None

        except Exception:
            return None

    def format_phone_display(self, phone: str) -> str:
        """
        Format phone number for display.

        Args:
            phone: Phone number (E.164 format)

        Returns:
            Formatted phone number
        """
        # Remove '+' and 'whatsapp:' prefix
        phone = phone.replace('whatsapp:', '').replace('+', '').strip()

        # Format US numbers as (XXX) XXX-XXXX
        if len(phone) == 11 and phone.startswith('1'):
            return f"({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
        elif len(phone) == 10:
            return f"({phone[0:3]}) {phone[3:6]}-{phone[6:]}"
        else:
            # International format
            return f"+{phone}"


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test_whatsapp():
        whatsapp = WhatsAppIntegration()

        # Simulate incoming webhook
        webhook_data = {
            'MessageSid': 'SM1234567890abcdef',
            'AccountSid': 'AC1234567890abcdef',
            'From': 'whatsapp:+15551234567',
            'To': 'whatsapp:+14155238886',
            'Body': 'Hi, I need help resetting my password',
            'ProfileName': 'John Doe',
            'WaId': '15551234567',
            'NumMedia': '0'
        }

        # Parse message
        parsed = whatsapp.parse_incoming_message(webhook_data)
        print(f"\nParsed message:")
        print(f"From: {parsed['customer_phone']}")
        print(f"Name: {parsed['customer_name']}")
        print(f"Content: {parsed['content']}")
        print(f"Has media: {parsed['metadata']['has_media']}")

        # Send response
        response = await whatsapp.send_response(
            to_phone=parsed['customer_phone'],
            body="Hi John! 👋 I can help you reset your password. Check your email for a reset link, or reply with your email address and I'll send you one."
        )
        print(f"\nSent response: {response}")

        # Check message status
        if response['success']:
            status = await whatsapp.get_message_status(response['message_sid'])
            print(f"\nMessage status: {status}")

    asyncio.run(test_whatsapp())

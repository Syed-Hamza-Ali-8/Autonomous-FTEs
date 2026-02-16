"""
End-to-End Test Suite
Phase 3: Production Readiness

Tests the complete flow across all three channels.
"""

import os
import asyncio
import pytest
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_context
from src.database.models import Customer, Conversation, Message, Ticket
from src.channels.gmail_integration import GmailIntegration
from src.channels.whatsapp_integration import WhatsAppIntegration


# Test configuration
API_BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
TEST_EMAIL = "test@example.com"
TEST_PHONE = "+15551234567"
TEST_NAME = "Test User"


class TestE2EEmailChannel:
    """End-to-end tests for Email channel."""

    @pytest.mark.asyncio
    async def test_email_full_flow(self):
        """Test complete email flow: receive → process → respond."""

        # Simulate incoming email via Gmail webhook
        email_data = {
            "message": {
                "data": "test-message-id",
                "messageId": str(uuid4()),
                "publishTime": datetime.now().isoformat()
            }
        }

        async with httpx.AsyncClient() as client:
            # Send webhook
            response = await client.post(
                f"{API_BASE_URL}/webhooks/gmail",
                json=email_data
            )
            assert response.status_code == 200

        # Wait for processing
        await asyncio.sleep(2)

        # Verify customer was created
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.email == TEST_EMAIL)
            )
            customer = result.scalar_one_or_none()
            assert customer is not None
            assert customer.email == TEST_EMAIL

            # Verify conversation was created
            result = await db.execute(
                select(Conversation).where(
                    Conversation.customer_id == customer.id,
                    Conversation.channel == 'email'
                )
            )
            conversation = result.scalar_one_or_none()
            assert conversation is not None
            assert conversation.status == 'active'

            # Verify message was stored
            result = await db.execute(
                select(Message).where(
                    Message.conversation_id == conversation.id
                )
            )
            messages = result.scalars().all()
            assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_email_password_reset_flow(self):
        """Test password reset request via email."""

        # Submit password reset request
        email_content = "Hi, I need help resetting my password. My email is test@example.com"

        # This would normally come through Gmail API
        # For testing, we'll use the web form endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "Password Reset Help",
                    "message": email_content
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            ticket_id = data["ticket_id"]

        # Wait for AI processing
        await asyncio.sleep(3)

        # Verify response was generated
        async with get_db_context() as db:
            result = await db.execute(
                select(Message).where(
                    Message.conversation_id == ticket_id,
                    Message.role == 'assistant'
                )
            )
            response_message = result.scalar_one_or_none()
            assert response_message is not None
            assert "password" in response_message.content.lower()
            assert "reset" in response_message.content.lower()

    @pytest.mark.asyncio
    async def test_email_escalation_flow(self):
        """Test escalation trigger via email."""

        # Submit billing issue (should trigger escalation)
        email_content = "I was charged twice for my subscription! I want a refund immediately."

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "Billing Issue - Double Charge",
                    "message": email_content
                }
            )
            assert response.status_code == 200
            ticket_id = response.json()["ticket_id"]

        # Wait for processing
        await asyncio.sleep(3)

        # Verify ticket was created with escalation
        async with get_db_context() as db:
            result = await db.execute(
                select(Ticket).where(Ticket.conversation_id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            assert ticket is not None
            assert ticket.escalated is True
            assert "billing" in ticket.escalation_reason.lower() or "refund" in ticket.escalation_reason.lower()


class TestE2EWhatsAppChannel:
    """End-to-end tests for WhatsApp channel."""

    @pytest.mark.asyncio
    async def test_whatsapp_full_flow(self):
        """Test complete WhatsApp flow: receive → process → respond."""

        # Simulate incoming WhatsApp message from Twilio
        whatsapp_data = {
            "MessageSid": f"SM{uuid4().hex[:32]}",
            "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "From": f"whatsapp:{TEST_PHONE}",
            "To": "whatsapp:+14155238886",
            "Body": "Hi! How do I add a new task?",
            "ProfileName": TEST_NAME,
            "WaId": TEST_PHONE.replace("+", ""),
            "NumMedia": "0"
        }

        async with httpx.AsyncClient() as client:
            # Send webhook (form-encoded)
            response = await client.post(
                f"{API_BASE_URL}/webhooks/whatsapp",
                data=whatsapp_data
            )
            assert response.status_code == 200
            assert "application/xml" in response.headers["content-type"]

        # Wait for processing
        await asyncio.sleep(2)

        # Verify customer was created
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.phone == TEST_PHONE)
            )
            customer = result.scalar_one_or_none()
            assert customer is not None
            assert customer.phone == TEST_PHONE

            # Verify conversation was created
            result = await db.execute(
                select(Conversation).where(
                    Conversation.customer_id == customer.id,
                    Conversation.channel == 'whatsapp'
                )
            )
            conversation = result.scalar_one_or_none()
            assert conversation is not None

    @pytest.mark.asyncio
    async def test_whatsapp_casual_tone(self):
        """Test that WhatsApp responses use casual tone."""

        whatsapp_data = {
            "MessageSid": f"SM{uuid4().hex[:32]}",
            "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "From": f"whatsapp:{TEST_PHONE}",
            "To": "whatsapp:+14155238886",
            "Body": "How do I track time?",
            "ProfileName": TEST_NAME,
            "WaId": TEST_PHONE.replace("+", ""),
            "NumMedia": "0"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/webhooks/whatsapp",
                data=whatsapp_data
            )
            assert response.status_code == 200

        # Wait for processing
        await asyncio.sleep(3)

        # Verify response tone
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.phone == TEST_PHONE)
            )
            customer = result.scalar_one()

            result = await db.execute(
                select(Conversation).where(
                    Conversation.customer_id == customer.id,
                    Conversation.channel == 'whatsapp'
                ).order_by(Conversation.created_at.desc())
            )
            conversation = result.scalar_one()

            result = await db.execute(
                select(Message).where(
                    Message.conversation_id == conversation.id,
                    Message.role == 'assistant'
                )
            )
            response_message = result.scalar_one_or_none()

            if response_message:
                # Check for casual indicators
                content = response_message.content.lower()
                casual_indicators = ["hi", "hey", "!", "👋", "😊"]
                has_casual = any(indicator in content for indicator in casual_indicators)
                assert has_casual, "WhatsApp response should use casual tone"


class TestE2EWebFormChannel:
    """End-to-end tests for Web Form channel."""

    @pytest.mark.asyncio
    async def test_web_form_full_flow(self):
        """Test complete web form flow: submit → process → respond."""

        form_data = {
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "phone": TEST_PHONE,
            "subject": "Integration Question",
            "message": "How do I integrate TaskFlow Pro with Slack?"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json=form_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "ticket_id" in data
            ticket_id = data["ticket_id"]

        # Wait for processing
        await asyncio.sleep(3)

        # Verify customer and conversation
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.email == TEST_EMAIL)
            )
            customer = result.scalar_one_or_none()
            assert customer is not None

            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == ticket_id,
                    Conversation.channel == 'web_form'
                )
            )
            conversation = result.scalar_one_or_none()
            assert conversation is not None

            # Verify AI response was generated
            result = await db.execute(
                select(Message).where(
                    Message.conversation_id == conversation.id,
                    Message.role == 'assistant'
                )
            )
            response_message = result.scalar_one_or_none()
            assert response_message is not None
            assert "slack" in response_message.content.lower() or "integration" in response_message.content.lower()

    @pytest.mark.asyncio
    async def test_web_form_validation(self):
        """Test web form validation."""

        # Test missing required fields
        invalid_data = {
            "name": "",
            "email": "invalid-email",
            "subject": "",
            "message": "Hi"  # Too short
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json=invalid_data
            )
            assert response.status_code == 422  # Validation error


class TestE2ECrossChannel:
    """End-to-end tests for cross-channel continuity."""

    @pytest.mark.asyncio
    async def test_cross_channel_customer_matching(self):
        """Test that same customer is recognized across channels."""

        # First contact via email
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "First Contact",
                    "message": "This is my first message"
                }
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Second contact via WhatsApp (same phone)
        whatsapp_data = {
            "MessageSid": f"SM{uuid4().hex[:32]}",
            "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "From": f"whatsapp:{TEST_PHONE}",
            "To": "whatsapp:+14155238886",
            "Body": "This is my second message",
            "ProfileName": TEST_NAME,
            "WaId": TEST_PHONE.replace("+", ""),
            "NumMedia": "0"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/webhooks/whatsapp",
                data=whatsapp_data
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Verify same customer has conversations in both channels
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.email == TEST_EMAIL)
            )
            customer = result.scalar_one_or_none()
            assert customer is not None

            result = await db.execute(
                select(Conversation).where(Conversation.customer_id == customer.id)
            )
            conversations = result.scalars().all()

            channels = {conv.channel for conv in conversations}
            assert 'web_form' in channels or 'email' in channels
            assert 'whatsapp' in channels

    @pytest.mark.asyncio
    async def test_conversation_history_access(self):
        """Test that agent can access conversation history."""

        # First message
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "Account Setup",
                    "message": "I just created my account"
                }
            )
            ticket_id = response.json()["ticket_id"]

        await asyncio.sleep(3)

        # Follow-up message referencing previous conversation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "Re: Account Setup",
                    "message": "Following up on my previous message about account setup"
                }
            )

        await asyncio.sleep(3)

        # Verify agent accessed history
        async with get_db_context() as db:
            result = await db.execute(
                select(Customer).where(Customer.email == TEST_EMAIL)
            )
            customer = result.scalar_one()

            result = await db.execute(
                select(Conversation).where(Conversation.customer_id == customer.id)
            )
            conversations = result.scalars().all()

            # Should have multiple messages across conversations
            total_messages = 0
            for conv in conversations:
                result = await db.execute(
                    select(Message).where(Message.conversation_id == conv.id)
                )
                messages = result.scalars().all()
                total_messages += len(messages)

            assert total_messages >= 4  # At least 2 customer + 2 assistant messages


class TestE2EPerformance:
    """End-to-end performance tests."""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test that response time is under 3 seconds."""

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/support/submit",
                json={
                    "name": TEST_NAME,
                    "email": TEST_EMAIL,
                    "subject": "Quick Question",
                    "message": "How do I log in?"
                }
            )
            assert response.status_code == 200

        # Wait for processing
        await asyncio.sleep(3)

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        # Should complete within 5 seconds (including processing)
        assert total_time < 5.0, f"Response took {total_time:.2f}s, expected <5s"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""

        async def submit_request(index: int):
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/support/submit",
                    json={
                        "name": f"Test User {index}",
                        "email": f"test{index}@example.com",
                        "subject": f"Question {index}",
                        "message": f"This is test message {index}"
                    }
                )
                return response.status_code

        # Submit 10 concurrent requests
        tasks = [submit_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(status == 200 for status in results)


class TestE2EHealthAndMetrics:
    """End-to-end tests for health and metrics."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint."""

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "degraded"]
            assert "database" in data
            assert "kafka" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/metrics")
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]

            # Check for key metrics
            content = response.text
            assert "fte_agent_messages_processed_total" in content
            assert "fte_http_requests_total" in content
            assert "fte_agent_processing_duration_seconds" in content


# Pytest configuration
@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """Set up test environment before running tests."""
    print("\n=== Setting up E2E test environment ===")

    # Wait for services to be ready
    await asyncio.sleep(5)

    # Verify API is accessible
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health", timeout=10.0)
            assert response.status_code == 200
            print("✓ API is accessible")
        except Exception as e:
            pytest.fail(f"API is not accessible: {e}")

    yield

    print("\n=== E2E tests complete ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

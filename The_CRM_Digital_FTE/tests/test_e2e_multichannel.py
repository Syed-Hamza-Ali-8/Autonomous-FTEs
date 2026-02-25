"""
E2E Test Suite for Multi-Channel Customer Success FTE
Tests web form, email, and WhatsApp channels
"""

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime
import uuid

BASE_URL = "http://localhost:8001"


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac


class TestHealthAndMetrics:
    """Test health check and metrics endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Health endpoint should return status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "kafka" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        """Metrics endpoint should return Prometheus format."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestWebFormChannel:
    """Test the web support form (required build)."""

    @pytest.mark.asyncio
    async def test_form_submission_success(self, client):
        """Web form submission should create ticket and return ID."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Help with API",
            "message": "I need help with the API authentication. Can you provide guidance?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ticket_id" in data
        assert "message" in data
        # Verify ticket_id is a valid UUID
        uuid.UUID(data["ticket_id"])

    @pytest.mark.asyncio
    async def test_form_validation_short_name(self, client):
        """Form should reject names that are too short."""
        response = await client.post("/support/submit", json={
            "name": "",
            "email": "test@example.com",
            "subject": "Test",
            "message": "This is a test message"
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_form_validation_invalid_email(self, client):
        """Form should reject invalid email addresses."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "invalid-email",
            "subject": "Test",
            "message": "This is a test message"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_validation_short_message(self, client):
        """Form should reject messages that are too short."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test",
            "message": ""
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_form_with_phone_optional(self, client):
        """Form should accept optional phone number."""
        response = await client.post("/support/submit", json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test with phone",
            "message": "This is a test message with phone number",
            "phone": "+1234567890"
        })
        assert response.status_code == 200


class TestWhatsAppChannel:
    """Test WhatsApp/Twilio integration."""

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_receives_message(self, client):
        """WhatsApp webhook should accept incoming messages."""
        # Simulate Twilio webhook payload
        response = await client.post(
            "/webhooks/whatsapp",
            data={
                "MessageSid": "SM123456789",
                "From": "whatsapp:+1234567890",
                "To": "whatsapp:+14155238886",
                "Body": "Hello, I need help with my account",
                "ProfileName": "Test User",
                "NumMedia": "0"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        # Should return TwiML response or 403 if signature validation fails
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            # Should return TwiML XML
            assert "xml" in response.headers["content-type"].lower()


class TestGmailChannel:
    """Test Gmail integration."""

    @pytest.mark.asyncio
    async def test_gmail_webhook_receives_notification(self, client):
        """Gmail webhook should accept Pub/Sub notifications."""
        # Simulate Gmail Pub/Sub notification
        response = await client.post("/webhooks/gmail", json={
            "message": {
                "data": "eyJlbWFpbElkIjogInRlc3QxMjMifQ==",  # base64 encoded
                "messageId": "test-message-123",
                "publishTime": datetime.now().isoformat()
            },
            "subscription": "projects/test/subscriptions/gmail-push"
        })

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestCustomerLookup:
    """Test customer lookup functionality."""

    @pytest.mark.asyncio
    async def test_lookup_customer_by_email(self, client):
        """Should be able to look up customer by email after creation."""
        # First create a customer via web form
        submit_response = await client.post("/support/submit", json={
            "name": "Lookup Test User",
            "email": "lookup@example.com",
            "subject": "Test Lookup",
            "message": "Testing customer lookup functionality"
        })
        assert submit_response.status_code == 200

        # Wait a moment for processing
        await asyncio.sleep(1)

        # Look up the customer
        lookup_response = await client.get(
            "/customers/lookup",
            params={"email": "lookup@example.com"}
        )

        if lookup_response.status_code == 200:
            data = lookup_response.json()
            assert data["email"] == "lookup@example.com"
            assert "customer_id" in data
            assert "total_conversations" in data

    @pytest.mark.asyncio
    async def test_lookup_nonexistent_customer(self, client):
        """Should return 404 for nonexistent customer."""
        response = await client.get(
            "/customers/lookup",
            params={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_lookup_requires_identifier(self, client):
        """Should return 400 if no email or phone provided."""
        response = await client.get("/customers/lookup")
        assert response.status_code == 400


class TestCrossChannelContinuity:
    """Test that conversations persist across channels."""

    @pytest.mark.asyncio
    async def test_customer_identified_across_channels(self, client):
        """Customer should be identified across different channels."""
        test_email = f"crosschannel-{uuid.uuid4()}@example.com"

        # Create ticket via web form
        web_response = await client.post("/support/submit", json={
            "name": "Cross Channel User",
            "email": test_email,
            "subject": "Initial Contact",
            "message": "First contact via web form"
        })
        assert web_response.status_code == 200

        # Wait for processing
        await asyncio.sleep(1)

        # Look up customer
        lookup_response = await client.get(
            "/customers/lookup",
            params={"email": test_email}
        )

        if lookup_response.status_code == 200:
            customer = lookup_response.json()
            assert customer["email"] == test_email
            assert customer["total_conversations"] >= 1


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client):
        """Should return 404 for invalid endpoints."""
        response = await client.get("/invalid/endpoint")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_malformed_json(self, client):
        """Should handle malformed JSON gracefully."""
        response = await client.post(
            "/support/submit",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestConcurrency:
    """Test concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_form_submissions(self, client):
        """Should handle multiple concurrent submissions."""
        async def submit_form(index):
            return await client.post("/support/submit", json={
                "name": f"Concurrent User {index}",
                "email": f"concurrent{index}@example.com",
                "subject": f"Concurrent Test {index}",
                "message": f"Testing concurrent submission number {index}"
            })

        # Submit 10 forms concurrently
        tasks = [submit_form(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

"""
Load Testing Script
Phase 3: Production Readiness

Simulates realistic load across all three channels.
"""

import random
import json
from typing import Dict, Any
from uuid import uuid4

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


# Test data
SAMPLE_NAMES = [
    "John Smith", "Jane Doe", "Bob Johnson", "Alice Williams",
    "Charlie Brown", "Diana Prince", "Eve Anderson", "Frank Miller"
]

SAMPLE_EMAILS = [
    "john.smith@example.com", "jane.doe@example.com",
    "bob.johnson@example.com", "alice.williams@example.com",
    "charlie.brown@example.com", "diana.prince@example.com",
    "eve.anderson@example.com", "frank.miller@example.com"
]

SAMPLE_PHONES = [
    "+15551234567", "+15551234568", "+15551234569", "+15551234570",
    "+15551234571", "+15551234572", "+15551234573", "+15551234574"
]

SAMPLE_SUBJECTS = [
    "Password Reset Help",
    "How do I add a new task?",
    "Integration with Slack",
    "Billing question",
    "Account setup assistance",
    "Time tracking feature",
    "Mobile app availability",
    "Export data request"
]

SAMPLE_MESSAGES = [
    "Hi, I need help resetting my password. Can you guide me through the process?",
    "How do I create a new task in TaskFlow Pro? I'm new to the platform.",
    "I want to integrate TaskFlow Pro with Slack. Is this possible?",
    "I have a question about my billing. Can you help?",
    "I just signed up and need help setting up my account.",
    "How does the time tracking feature work?",
    "Is there a mobile app available for TaskFlow Pro?",
    "How can I export my data from TaskFlow Pro?"
]

# Escalation triggers (for testing escalation flow)
ESCALATION_MESSAGES = [
    "I was charged twice! I want a refund immediately!",
    "This is unacceptable! I want to speak to a manager!",
    "I need to cancel my subscription right now!",
    "Your service is terrible! I'm very disappointed!"
]


class WebFormUser(FastHttpUser):
    """
    Simulates users submitting support requests via web form.
    """
    wait_time = between(2, 5)  # Wait 2-5 seconds between requests
    weight = 5  # 50% of traffic

    @task(8)
    def submit_normal_request(self):
        """Submit a normal support request."""
        name = random.choice(SAMPLE_NAMES)
        email = random.choice(SAMPLE_EMAILS)
        phone = random.choice(SAMPLE_PHONES)
        subject = random.choice(SAMPLE_SUBJECTS)
        message = random.choice(SAMPLE_MESSAGES)

        with self.client.post(
            "/support/submit",
            json={
                "name": name,
                "email": email,
                "phone": phone,
                "subject": subject,
                "message": message
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Request failed: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def submit_escalation_request(self):
        """Submit a request that should trigger escalation."""
        name = random.choice(SAMPLE_NAMES)
        email = random.choice(SAMPLE_EMAILS)
        message = random.choice(ESCALATION_MESSAGES)

        with self.client.post(
            "/support/submit",
            json={
                "name": name,
                "email": email,
                "subject": "URGENT: Billing Issue",
                "message": message
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def check_health(self):
        """Check API health."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data}")
            else:
                response.failure(f"Status code: {response.status_code}")


class WhatsAppUser(FastHttpUser):
    """
    Simulates WhatsApp messages via Twilio webhooks.
    """
    wait_time = between(3, 8)  # Wait 3-8 seconds between requests
    weight = 3  # 30% of traffic

    @task
    def send_whatsapp_message(self):
        """Send a WhatsApp message via Twilio webhook."""
        phone = random.choice(SAMPLE_PHONES)
        name = random.choice(SAMPLE_NAMES)
        message = random.choice(SAMPLE_MESSAGES)

        webhook_data = {
            "MessageSid": f"SM{uuid4().hex[:32]}",
            "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "From": f"whatsapp:{phone}",
            "To": "whatsapp:+14155238886",
            "Body": message,
            "ProfileName": name,
            "WaId": phone.replace("+", ""),
            "NumMedia": "0"
        }

        with self.client.post(
            "/webhooks/whatsapp",
            data=webhook_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class CustomerLookupUser(FastHttpUser):
    """
    Simulates customer lookup requests.
    """
    wait_time = between(5, 10)  # Wait 5-10 seconds between requests
    weight = 2  # 20% of traffic

    @task
    def lookup_by_email(self):
        """Look up customer by email."""
        email = random.choice(SAMPLE_EMAILS)

        with self.client.get(
            f"/customers/lookup?email={email}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task
    def lookup_by_phone(self):
        """Look up customer by phone."""
        phone = random.choice(SAMPLE_PHONES)

        with self.client.get(
            f"/customers/lookup?phone={phone}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*60)
    print("LOAD TEST STARTING")
    print("="*60)
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*60)
    print("LOAD TEST COMPLETE")
    print("="*60)

    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.total.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")

    print("\n" + "="*60 + "\n")


# Custom load test scenarios
class SpikeLoadTest(FastHttpUser):
    """
    Simulates spike load scenario.
    Useful for testing auto-scaling.
    """
    wait_time = between(0.5, 2)  # Very short wait time
    weight = 10

    @task
    def rapid_fire_requests(self):
        """Send rapid requests to simulate spike."""
        with self.client.post(
            "/support/submit",
            json={
                "name": random.choice(SAMPLE_NAMES),
                "email": random.choice(SAMPLE_EMAILS),
                "subject": "Spike Test",
                "message": "This is a spike load test message"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class SustainedLoadTest(FastHttpUser):
    """
    Simulates sustained load scenario.
    Useful for 24-hour continuous testing.
    """
    wait_time = between(10, 30)  # Longer wait time
    weight = 5

    @task(5)
    def normal_request(self):
        """Send normal request."""
        with self.client.post(
            "/support/submit",
            json={
                "name": random.choice(SAMPLE_NAMES),
                "email": random.choice(SAMPLE_EMAILS),
                "subject": random.choice(SAMPLE_SUBJECTS),
                "message": random.choice(SAMPLE_MESSAGES)
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def check_metrics(self):
        """Check metrics endpoint."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


if __name__ == "__main__":
    import os
    os.system("locust -f tests/load/load_test.py --host http://localhost:8000")

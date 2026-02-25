"""
Load Testing Suite for Customer Success Digital FTE
Uses Locust to simulate concurrent users across all channels
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid
from datetime import datetime


class WebFormUser(HttpUser):
    """
    Simulate users submitting support forms.
    This is the most common channel (60% of traffic).
    """
    wait_time = between(2, 10)
    weight = 6  # 60% of users

    @task(10)
    def submit_support_form(self):
        """Submit a support request via web form."""
        categories = ['general', 'technical', 'billing', 'feedback', 'bug_report']
        subjects = [
            "How do I reset my password?",
            "API authentication not working",
            "Billing question about invoice",
            "Feature request for dashboard",
            "Bug: Cannot upload files"
        ]
        messages = [
            "I'm having trouble accessing my account. Can you help me reset my password?",
            "The API keeps returning 401 errors even with valid credentials. What am I doing wrong?",
            "I was charged twice this month. Can you please check my billing?",
            "It would be great if you could add dark mode to the dashboard.",
            "When I try to upload a file larger than 10MB, the upload fails without any error message."
        ]

        user_id = random.randint(1, 1000)

        with self.client.post(
            "/support/submit",
            json={
                "name": f"Load Test User {user_id}",
                "email": f"loadtest{user_id}@example.com",
                "subject": random.choice(subjects),
                "message": random.choice(messages),
                "phone": f"+1555{random.randint(1000000, 9999999)}" if random.random() > 0.5 else None
            },
            catch_response=True,
            name="/support/submit"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "ticket_id" in data:
                    response.success()
                else:
                    response.failure("No ticket_id in response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def check_health(self):
        """Check API health."""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data.get('status')}")
            else:
                response.failure(f"Got status code {response.status_code}")


class WhatsAppUser(HttpUser):
    """
    Simulate WhatsApp messages via Twilio webhook.
    Represents 25% of traffic.
    """
    wait_time = between(5, 15)
    weight = 2.5  # 25% of users

    @task
    def send_whatsapp_message(self):
        """Simulate incoming WhatsApp message."""
        messages = [
            "Hi, I need help",
            "How do I cancel my subscription?",
            "What are your business hours?",
            "I want to speak to a human",
            "My account is locked"
        ]

        phone = f"+1555{random.randint(1000000, 9999999)}"

        with self.client.post(
            "/webhooks/whatsapp",
            data={
                "MessageSid": f"SM{uuid.uuid4().hex[:32]}",
                "From": f"whatsapp:{phone}",
                "To": "whatsapp:+14155238886",
                "Body": random.choice(messages),
                "ProfileName": f"Test User {random.randint(1, 1000)}",
                "NumMedia": "0"
            },
            catch_response=True,
            name="/webhooks/whatsapp"
        ) as response:
            # WhatsApp webhook returns 200 or 403 (signature validation)
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class GmailUser(HttpUser):
    """
    Simulate Gmail Pub/Sub notifications.
    Represents 15% of traffic.
    """
    wait_time = between(10, 30)
    weight = 1.5  # 15% of users

    @task
    def send_gmail_notification(self):
        """Simulate Gmail Pub/Sub notification."""
        with self.client.post(
            "/webhooks/gmail",
            json={
                "message": {
                    "data": "eyJlbWFpbElkIjogInRlc3QxMjMifQ==",  # base64: {"emailId": "test123"}
                    "messageId": f"msg-{uuid.uuid4().hex[:16]}",
                    "publishTime": datetime.now().isoformat()
                },
                "subscription": "projects/test/subscriptions/gmail-push"
            },
            catch_response=True,
            name="/webhooks/gmail"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class CustomerLookupUser(HttpUser):
    """
    Simulate customer lookup requests.
    Background traffic from support dashboard.
    """
    wait_time = between(15, 45)
    weight = 1  # 10% of users

    @task
    def lookup_customer(self):
        """Look up customer by email."""
        user_id = random.randint(1, 1000)
        email = f"loadtest{user_id}@example.com"

        with self.client.get(
            "/customers/lookup",
            params={"email": email},
            catch_response=True,
            name="/customers/lookup"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class MetricsUser(HttpUser):
    """
    Simulate monitoring systems scraping metrics.
    Constant background traffic.
    """
    wait_time = between(5, 15)
    weight = 0.5  # 5% of users

    @task
    def scrape_metrics(self):
        """Scrape Prometheus metrics."""
        with self.client.get("/metrics", catch_response=True, name="/metrics") as response:
            if response.status_code == 200:
                if "http_requests_total" in response.text:
                    response.success()
                else:
                    response.failure("Metrics format invalid")
            else:
                response.failure(f"Got status code {response.status_code}")


# Event handlers for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*80)
    print("🚀 Starting Load Test for Customer Success Digital FTE")
    print("="*80)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("Channels: Web Form (60%), WhatsApp (25%), Gmail (15%)")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*80)
    print("✅ Load Test Complete")
    print("="*80)

    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"P95 Response Time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99 Response Time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*80 + "\n")


# Custom shape for ramping load test
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that gradually increases load.

    Step 1: 10 users for 2 minutes (warm-up)
    Step 2: 50 users for 5 minutes (normal load)
    Step 3: 100 users for 5 minutes (peak load)
    Step 4: 200 users for 3 minutes (stress test)
    Step 5: 10 users for 2 minutes (cool-down)
    """

    step_time = 60  # seconds per step
    step_load = [
        (10, 1),    # 10 users, 1 spawn rate
        (10, 1),    # Hold at 10 users
        (50, 2),    # Ramp to 50 users
        (50, 2),    # Hold at 50 users
        (50, 2),    # Hold at 50 users
        (50, 2),    # Hold at 50 users
        (50, 2),    # Hold at 50 users
        (100, 5),   # Ramp to 100 users
        (100, 5),   # Hold at 100 users
        (100, 5),   # Hold at 100 users
        (100, 5),   # Hold at 100 users
        (100, 5),   # Hold at 100 users
        (200, 10),  # Ramp to 200 users (stress)
        (200, 10),  # Hold at 200 users
        (200, 10),  # Hold at 200 users
        (10, 5),    # Cool down
        (10, 5),    # Cool down
    ]

    def tick(self):
        run_time = self.get_run_time()

        if run_time > len(self.step_load) * self.step_time:
            return None

        current_step = int(run_time // self.step_time)
        return self.step_load[current_step]


if __name__ == "__main__":
    import os
    import sys

    # Run locust with default settings
    os.system(f"locust -f {__file__} --host=http://localhost:8001")

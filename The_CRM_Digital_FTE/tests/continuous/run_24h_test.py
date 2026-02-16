"""
24-Hour Continuous Operation Test
Phase 3: Production Readiness

Runs the system continuously for 24 hours with realistic traffic patterns.
Monitors performance, escalation rate, cost, and system health.
"""

import asyncio
import httpx
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'24h_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_DURATION_HOURS = 24
REQUESTS_PER_HOUR = 50  # Average 50 requests per hour
ESCALATION_RATE_TARGET = 0.25  # 25% max
RESPONSE_TIME_TARGET = 3.0  # 3 seconds max (P95)
DAILY_COST_TARGET = 3.0  # $3 per day max


# Test data
SAMPLE_NAMES = [
    "John Smith", "Jane Doe", "Bob Johnson", "Alice Williams",
    "Charlie Brown", "Diana Prince", "Eve Anderson", "Frank Miller",
    "Grace Lee", "Henry Davis", "Ivy Chen", "Jack Wilson"
]

SAMPLE_EMAILS = [f"{name.lower().replace(' ', '.')}@example.com" for name in SAMPLE_NAMES]
SAMPLE_PHONES = [f"+1555{i:07d}" for i in range(1000000, 1000012)]

SAMPLE_QUESTIONS = [
    "How do I reset my password?",
    "How do I create a new task?",
    "Can I integrate with Slack?",
    "How does time tracking work?",
    "Is there a mobile app?",
    "How do I export my data?",
    "How do I invite team members?",
    "What are the pricing plans?",
    "How do I upgrade my account?",
    "How do I cancel my subscription?",
    "How do I change my email address?",
    "How do I delete my account?",
    "How do I set up two-factor authentication?",
    "How do I create recurring tasks?",
    "How do I use the calendar view?",
    "How do I set task priorities?",
    "How do I add attachments to tasks?",
    "How do I use task templates?",
    "How do I filter tasks by status?",
    "How do I generate reports?"
]

ESCALATION_QUESTIONS = [
    "I was charged twice! I want a refund immediately!",
    "This is unacceptable! I want to speak to a manager!",
    "I need to cancel my subscription right now!",
    "Your service is terrible! I'm very disappointed!"
]


class ContinuousOperationTest:
    """24-hour continuous operation test."""

    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=TEST_DURATION_HOURS)
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
            "hourly_stats": {}
        }
        self.running = True

    async def run(self):
        """Run the 24-hour test."""
        logger.info("="*80)
        logger.info("24-HOUR CONTINUOUS OPERATION TEST STARTING")
        logger.info("="*80)
        logger.info(f"Start time: {self.start_time}")
        logger.info(f"End time: {self.end_time}")
        logger.info(f"Target requests per hour: {REQUESTS_PER_HOUR}")
        logger.info(f"Total expected requests: {REQUESTS_PER_HOUR * TEST_DURATION_HOURS}")
        logger.info("="*80)

        # Start monitoring task
        monitor_task = asyncio.create_task(self.monitor_metrics())

        # Start traffic generation tasks
        traffic_tasks = [
            asyncio.create_task(self.generate_web_form_traffic()),
            asyncio.create_task(self.generate_whatsapp_traffic()),
            asyncio.create_task(self.generate_customer_lookup_traffic())
        ]

        # Wait for test duration
        try:
            await asyncio.sleep(TEST_DURATION_HOURS * 3600)
        except KeyboardInterrupt:
            logger.warning("Test interrupted by user")

        # Stop all tasks
        self.running = False
        monitor_task.cancel()
        for task in traffic_tasks:
            task.cancel()

        # Generate final report
        await self.generate_report()

    async def generate_web_form_traffic(self):
        """Generate web form traffic (60% of total)."""
        requests_per_hour = int(REQUESTS_PER_HOUR * 0.6)
        interval = 3600 / requests_per_hour  # Seconds between requests

        while self.running and datetime.now() < self.end_time:
            try:
                # 90% normal questions, 10% escalation triggers
                if random.random() < 0.9:
                    question = random.choice(SAMPLE_QUESTIONS)
                    subject = "Support Question"
                else:
                    question = random.choice(ESCALATION_QUESTIONS)
                    subject = "URGENT: Issue"

                await self.submit_web_form_request(
                    name=random.choice(SAMPLE_NAMES),
                    email=random.choice(SAMPLE_EMAILS),
                    phone=random.choice(SAMPLE_PHONES),
                    subject=subject,
                    message=question
                )

                # Wait before next request
                await asyncio.sleep(interval + random.uniform(-5, 5))

            except Exception as e:
                logger.error(f"Error in web form traffic: {e}")
                await asyncio.sleep(60)

    async def generate_whatsapp_traffic(self):
        """Generate WhatsApp traffic (30% of total)."""
        requests_per_hour = int(REQUESTS_PER_HOUR * 0.3)
        interval = 3600 / requests_per_hour

        while self.running and datetime.now() < self.end_time:
            try:
                question = random.choice(SAMPLE_QUESTIONS)

                await self.submit_whatsapp_message(
                    phone=random.choice(SAMPLE_PHONES),
                    name=random.choice(SAMPLE_NAMES),
                    message=question
                )

                await asyncio.sleep(interval + random.uniform(-5, 5))

            except Exception as e:
                logger.error(f"Error in WhatsApp traffic: {e}")
                await asyncio.sleep(60)

    async def generate_customer_lookup_traffic(self):
        """Generate customer lookup traffic (10% of total)."""
        requests_per_hour = int(REQUESTS_PER_HOUR * 0.1)
        interval = 3600 / requests_per_hour

        while self.running and datetime.now() < self.end_time:
            try:
                if random.random() < 0.5:
                    await self.lookup_customer_by_email(random.choice(SAMPLE_EMAILS))
                else:
                    await self.lookup_customer_by_phone(random.choice(SAMPLE_PHONES))

                await asyncio.sleep(interval + random.uniform(-5, 5))

            except Exception as e:
                logger.error(f"Error in customer lookup traffic: {e}")
                await asyncio.sleep(60)

    async def submit_web_form_request(self, name: str, email: str, phone: str, subject: str, message: str):
        """Submit a web form request."""
        start_time = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/support/submit",
                    json={
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "subject": subject,
                        "message": message
                    }
                )

                response_time = asyncio.get_event_loop().time() - start_time

                self.stats["total_requests"] += 1
                self.stats["response_times"].append(response_time)

                if response.status_code == 200:
                    self.stats["successful_requests"] += 1
                    logger.debug(f"Web form request successful: {response_time:.2f}s")
                else:
                    self.stats["failed_requests"] += 1
                    self.stats["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "web_form",
                        "status_code": response.status_code,
                        "error": response.text
                    })
                    logger.warning(f"Web form request failed: {response.status_code}")

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            self.stats["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "type": "web_form",
                "error": str(e)
            })
            logger.error(f"Web form request error: {e}")

    async def submit_whatsapp_message(self, phone: str, name: str, message: str):
        """Submit a WhatsApp message."""
        start_time = asyncio.get_event_loop().time()

        try:
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

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/webhooks/whatsapp",
                    data=webhook_data
                )

                response_time = asyncio.get_event_loop().time() - start_time

                self.stats["total_requests"] += 1
                self.stats["response_times"].append(response_time)

                if response.status_code == 200:
                    self.stats["successful_requests"] += 1
                    logger.debug(f"WhatsApp request successful: {response_time:.2f}s")
                else:
                    self.stats["failed_requests"] += 1
                    logger.warning(f"WhatsApp request failed: {response.status_code}")

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            logger.error(f"WhatsApp request error: {e}")

    async def lookup_customer_by_email(self, email: str):
        """Look up customer by email."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{API_BASE_URL}/customers/lookup?email={email}"
                )

                self.stats["total_requests"] += 1

                if response.status_code in [200, 404]:
                    self.stats["successful_requests"] += 1
                else:
                    self.stats["failed_requests"] += 1

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            logger.error(f"Customer lookup error: {e}")

    async def lookup_customer_by_phone(self, phone: str):
        """Look up customer by phone."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{API_BASE_URL}/customers/lookup?phone={phone}"
                )

                self.stats["total_requests"] += 1

                if response.status_code in [200, 404]:
                    self.stats["successful_requests"] += 1
                else:
                    self.stats["failed_requests"] += 1

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            logger.error(f"Customer lookup error: {e}")

    async def monitor_metrics(self):
        """Monitor system metrics every 5 minutes."""
        while self.running and datetime.now() < self.end_time:
            try:
                await asyncio.sleep(300)  # 5 minutes

                # Fetch metrics
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{API_BASE_URL}/metrics")

                    if response.status_code == 200:
                        metrics = response.text
                        await self.analyze_metrics(metrics)
                    else:
                        logger.warning(f"Failed to fetch metrics: {response.status_code}")

            except Exception as e:
                logger.error(f"Error monitoring metrics: {e}")

    async def analyze_metrics(self, metrics: str):
        """Analyze Prometheus metrics."""
        current_hour = (datetime.now() - self.start_time).seconds // 3600

        # Parse key metrics
        escalation_total = self.parse_metric(metrics, "fte_agent_escalations_total")
        messages_total = self.parse_metric(metrics, "fte_agent_messages_processed_total")
        cost_total = self.parse_metric(metrics, "fte_estimated_cost_dollars")

        # Calculate escalation rate
        if messages_total > 0:
            escalation_rate = escalation_total / messages_total
        else:
            escalation_rate = 0

        # Log metrics
        logger.info(f"Hour {current_hour} Metrics:")
        logger.info(f"  Messages processed: {messages_total}")
        logger.info(f"  Escalations: {escalation_total}")
        logger.info(f"  Escalation rate: {escalation_rate * 100:.2f}%")
        logger.info(f"  Estimated cost: ${cost_total:.2f}")

        # Check thresholds
        if escalation_rate > ESCALATION_RATE_TARGET:
            logger.warning(f"⚠️  Escalation rate ({escalation_rate * 100:.2f}%) exceeds target ({ESCALATION_RATE_TARGET * 100}%)")

        if cost_total > DAILY_COST_TARGET:
            logger.warning(f"⚠️  Cost (${cost_total:.2f}) exceeds daily target (${DAILY_COST_TARGET})")

    def parse_metric(self, metrics: str, metric_name: str) -> float:
        """Parse a metric value from Prometheus text format."""
        for line in metrics.split('\n'):
            if line.startswith(metric_name) and not line.startswith('#'):
                try:
                    value = float(line.split()[-1])
                    return value
                except (ValueError, IndexError):
                    pass
        return 0.0

    async def generate_report(self):
        """Generate final test report."""
        duration = datetime.now() - self.start_time
        duration_hours = duration.total_seconds() / 3600

        # Calculate statistics
        success_rate = (self.stats["successful_requests"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        failure_rate = (self.stats["failed_requests"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0

        response_times = sorted(self.stats["response_times"])
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p50_response_time = response_times[len(response_times) // 2]
            p95_response_time = response_times[int(len(response_times) * 0.95)]
            p99_response_time = response_times[int(len(response_times) * 0.99)]
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = 0

        # Fetch final metrics
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE_URL}/metrics")
                final_metrics = response.text if response.status_code == 200 else ""

            escalation_total = self.parse_metric(final_metrics, "fte_agent_escalations_total")
            messages_total = self.parse_metric(final_metrics, "fte_agent_messages_processed_total")
            cost_total = self.parse_metric(final_metrics, "fte_estimated_cost_dollars")

            escalation_rate = (escalation_total / messages_total * 100) if messages_total > 0 else 0

        except Exception as e:
            logger.error(f"Failed to fetch final metrics: {e}")
            escalation_rate = 0
            cost_total = 0

        # Generate report
        logger.info("\n" + "="*80)
        logger.info("24-HOUR CONTINUOUS OPERATION TEST COMPLETE")
        logger.info("="*80)
        logger.info(f"\nTest Duration: {duration_hours:.2f} hours")
        logger.info(f"Start Time: {self.start_time}")
        logger.info(f"End Time: {datetime.now()}")

        logger.info(f"\n{'REQUEST STATISTICS':-^80}")
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful Requests: {self.stats['successful_requests']} ({success_rate:.2f}%)")
        logger.info(f"Failed Requests: {self.stats['failed_requests']} ({failure_rate:.2f}%)")
        logger.info(f"Requests per Hour: {self.stats['total_requests'] / duration_hours:.2f}")

        logger.info(f"\n{'RESPONSE TIME STATISTICS':-^80}")
        logger.info(f"Average Response Time: {avg_response_time:.2f}s")
        logger.info(f"P50 Response Time: {p50_response_time:.2f}s")
        logger.info(f"P95 Response Time: {p95_response_time:.2f}s")
        logger.info(f"P99 Response Time: {p99_response_time:.2f}s")

        logger.info(f"\n{'AGENT PERFORMANCE':-^80}")
        logger.info(f"Messages Processed: {messages_total}")
        logger.info(f"Escalations: {escalation_total}")
        logger.info(f"Escalation Rate: {escalation_rate:.2f}%")

        logger.info(f"\n{'COST ANALYSIS':-^80}")
        logger.info(f"Total Cost: ${cost_total:.2f}")
        logger.info(f"Cost per Hour: ${cost_total / duration_hours:.2f}")
        logger.info(f"Projected Monthly Cost: ${cost_total / duration_hours * 24 * 30:.2f}")

        logger.info(f"\n{'PERFORMANCE TARGETS':-^80}")
        logger.info(f"Success Rate: {success_rate:.2f}% (Target: >99%)")
        logger.info(f"  {'✅ PASS' if success_rate > 99 else '❌ FAIL'}")
        logger.info(f"P95 Response Time: {p95_response_time:.2f}s (Target: <3s)")
        logger.info(f"  {'✅ PASS' if p95_response_time < 3 else '❌ FAIL'}")
        logger.info(f"Escalation Rate: {escalation_rate:.2f}% (Target: <25%)")
        logger.info(f"  {'✅ PASS' if escalation_rate < 25 else '❌ FAIL'}")
        logger.info(f"Daily Cost: ${cost_total / duration_hours * 24:.2f} (Target: <$3)")
        logger.info(f"  {'✅ PASS' if (cost_total / duration_hours * 24) < 3 else '❌ FAIL'}")

        if self.stats["errors"]:
            logger.info(f"\n{'ERRORS ({len(self.stats['errors'])})':-^80}")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                logger.info(f"  {error['timestamp']}: {error.get('type', 'unknown')} - {error.get('error', 'unknown')}")

        logger.info("\n" + "="*80)

        # Save report to file
        report_file = f"24h_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "duration_hours": duration_hours,
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "escalation_rate": escalation_rate,
                "total_cost": cost_total,
                "errors": self.stats["errors"]
            }, f, indent=2)

        logger.info(f"\nReport saved to: {report_file}")


async def main():
    """Main entry point."""
    test = ContinuousOperationTest()
    await test.run()


if __name__ == "__main__":
    asyncio.run(main())

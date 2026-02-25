"""
Kafka Consumer Worker
Phase 2: Specialization

Consumes messages from Kafka and processes them with the AI agent.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db_context
from ..database.models import Customer, Conversation, Message, Ticket
from ..agent.customer_success_agent import CustomerSuccessAgent
from ..channels.gmail_integration import GmailIntegration
from ..channels.whatsapp_integration import WhatsAppIntegration
from ..api.kafka_producer import KafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KafkaWorker:
    """
    Kafka consumer worker that processes incoming tickets.
    """

    def __init__(self):
        """Initialize Kafka worker."""
        self.bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        ).split(",")
        self.group_id = os.getenv("KAFKA_CONSUMER_GROUP", "fte-workers")
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer = KafkaProducer()
        self.gmail = GmailIntegration()

        # Initialize WhatsApp only if credentials are available
        try:
            self.whatsapp = WhatsAppIntegration()
            logger.info("WhatsApp integration initialized")
        except ValueError as e:
            logger.warning(f"WhatsApp integration disabled: {e}")
            self.whatsapp = None

        self.running = False

    async def start(self):
        """Start the Kafka consumer."""
        try:
            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                "fte.tickets.incoming",
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=10
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started: {self.bootstrap_servers}")

            # Start Kafka producer
            await self.producer.start()

            # Authenticate Gmail
            try:
                self.gmail.authenticate()
                logger.info("Gmail authenticated")
            except Exception as e:
                logger.warning(f"Gmail authentication failed: {e}")

            self.running = True
            logger.info("Kafka worker ready to process messages")

        except Exception as e:
            logger.error(f"Failed to start Kafka worker: {e}")
            raise

    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
        await self.producer.stop()

    async def process_messages(self):
        """
        Main processing loop.
        Consumes messages and processes them with the AI agent.
        """
        logger.info("Starting message processing loop...")

        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                try:
                    # Parse message
                    message_data = msg.value
                    logger.info(f"Processing message: {message_data.get('message_id')}")

                    # Process with agent
                    await self._process_ticket(message_data)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Send to DLQ
                    await self.producer.send_to_dlq(
                        original_topic=msg.topic,
                        message=msg.value,
                        error=str(e)
                    )

        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}", exc_info=True)
            raise

    async def _process_ticket(self, message_data: Dict[str, Any]):
        """
        Process a single ticket with the AI agent.

        Args:
            message_data: Message data from Kafka
        """
        start_time = datetime.now()

        customer_id = UUID(message_data['customer_id'])
        conversation_id = UUID(message_data['conversation_id'])
        message_id = UUID(message_data['message_id'])
        channel = message_data['channel']
        content = message_data['content']
        metadata = message_data.get('metadata', {})

        try:
            # Get database session
            async with get_db_context() as db:
                # Initialize agent
                agent = CustomerSuccessAgent(db)

                # Process message with agent
                result = await agent.process_message(
                    customer_id=customer_id,
                    conversation_id=conversation_id,
                    message_content=content,
                    channel=channel,
                    metadata=metadata
                )

                if not result['success']:
                    logger.error(f"Agent processing failed: {result.get('error')}")
                    return

                # Get response
                response_text = result.get('response')
                tool_calls = result.get('tool_calls', [])
                escalated = result.get('escalated', False)

                logger.info(f"Agent response generated: {len(response_text) if response_text else 0} chars")
                logger.info(f"Tool calls: {len(tool_calls)}")
                logger.info(f"Escalated: {escalated}")

                # Send response via appropriate channel
                if response_text and not escalated:
                    await self._send_response(
                        db=db,
                        customer_id=customer_id,
                        conversation_id=conversation_id,
                        channel=channel,
                        response_text=response_text,
                        metadata=metadata
                    )

                # Send escalation notification if escalated
                if escalated:
                    # Find ticket ID from tool calls
                    ticket_id = None
                    escalation_reason = None
                    escalation_urgency = "normal"

                    for tool_call in tool_calls:
                        if tool_call['function'] == 'escalate_to_human':
                            ticket_id = tool_call['arguments'].get('ticket_id')
                            escalation_reason = tool_call['arguments'].get('reason')
                            escalation_urgency = tool_call['arguments'].get('urgency', 'normal')
                            break

                    if ticket_id:
                        await self.producer.send_escalation(
                            ticket_id=ticket_id,
                            customer_id=str(customer_id),
                            reason=escalation_reason or "unknown",
                            urgency=escalation_urgency,
                            channel=channel
                        )

                # Record metrics
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                await self.producer.send_metric(
                    metric_type="performance",
                    metric_name="ticket_processing_time_ms",
                    metric_value=processing_time,
                    channel=channel,
                    metadata={
                        "escalated": escalated,
                        "tool_calls": len(tool_calls)
                    }
                )

                logger.info(f"Ticket processed successfully in {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"Error processing ticket: {e}", exc_info=True)
            raise

    async def _send_response(
        self,
        db: AsyncSession,
        customer_id: UUID,
        conversation_id: UUID,
        channel: str,
        response_text: str,
        metadata: Dict[str, Any]
    ):
        """
        Send response via appropriate channel.

        Args:
            db: Database session
            customer_id: Customer UUID
            conversation_id: Conversation UUID
            channel: Channel name
            response_text: Response text
            metadata: Message metadata
        """
        try:
            # Get customer info
            from sqlalchemy import select
            result = await db.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one()

            if channel == 'email':
                await self._send_email_response(
                    customer=customer,
                    response_text=response_text,
                    metadata=metadata
                )
            elif channel == 'whatsapp':
                await self._send_whatsapp_response(
                    customer=customer,
                    response_text=response_text
                )
            elif channel == 'web_form':
                # For web form, we send email response
                await self._send_email_response(
                    customer=customer,
                    response_text=response_text,
                    metadata=metadata
                )

            logger.info(f"Response sent via {channel} to customer {customer_id}")

        except Exception as e:
            logger.error(f"Error sending response: {e}", exc_info=True)
            raise

    async def _send_email_response(
        self,
        customer: Customer,
        response_text: str,
        metadata: Dict[str, Any]
    ):
        """Send email response via Gmail."""
        if not customer.email:
            logger.warning(f"Customer {customer.id} has no email address")
            return

        # Get subject from metadata or use default
        subject = metadata.get('subject', 'Re: Your Support Request')
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"

        # Get thread ID if available
        thread_id = metadata.get('thread_id')

        # Send email
        result = await self.gmail.send_response(
            to_email=customer.email,
            subject=subject,
            body=response_text,
            thread_id=thread_id,
            customer_name=customer.name
        )

        if not result['success']:
            logger.error(f"Failed to send email: {result.get('error')}")
            raise Exception(f"Email send failed: {result.get('error')}")

    async def _send_whatsapp_response(
        self,
        customer: Customer,
        response_text: str
    ):
        """Send WhatsApp response via Twilio."""
        if not self.whatsapp:
            logger.warning("WhatsApp integration not available, skipping WhatsApp response")
            return

        if not customer.phone:
            logger.warning(f"Customer {customer.id} has no phone number")
            return
            return

        # Send WhatsApp message
        result = await self.whatsapp.send_response(
            to_phone=customer.phone,
            body=response_text
        )

        if not result['success']:
            logger.error(f"Failed to send WhatsApp: {result.get('error')}")
            raise Exception(f"WhatsApp send failed: {result.get('error')}")


async def main():
    """Main entry point for the worker."""
    worker = KafkaWorker()

    try:
        # Start worker
        await worker.start()

        # Process messages
        await worker.process_messages()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

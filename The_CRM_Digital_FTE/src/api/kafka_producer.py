"""
Kafka Producer
Phase 2: Specialization

Produces messages to Kafka topics for async processing.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Kafka producer for sending messages to topics.
    """

    def __init__(self):
        """Initialize Kafka producer."""
        self.bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        ).split(",")
        self.producer: Optional[AIOKafkaProducer] = None
        self._connected = False

    async def start(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5
            )
            await self.producer.start()
            self._connected = True
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self._connected = False
            raise

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self._connected = False
            logger.info("Kafka producer stopped")

    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._connected

    async def send_message(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Send message to Kafka topic.

        Args:
            topic: Kafka topic name
            message: Message payload (will be JSON serialized)
            key: Optional message key for partitioning

        Returns:
            True if sent successfully
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False

        try:
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()

            # Send message
            await self.producer.send_and_wait(
                topic=topic,
                value=message,
                key=key
            )

            logger.debug(f"Sent message to {topic}: {key}")
            return True

        except KafkaError as e:
            logger.error(f"Kafka error sending message to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to {topic}: {e}")
            return False

    async def send_incoming_ticket(
        self,
        customer_id: str,
        conversation_id: str,
        message_id: str,
        channel: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send incoming ticket to processing queue.

        Args:
            customer_id: Customer UUID
            conversation_id: Conversation UUID
            message_id: Message UUID
            channel: Channel name
            content: Message content
            metadata: Optional metadata

        Returns:
            True if sent successfully
        """
        return await self.send_message(
            topic="fte.tickets.incoming",
            message={
                "customer_id": customer_id,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "channel": channel,
                "content": content,
                "metadata": metadata or {}
            },
            key=conversation_id  # Partition by conversation for ordering
        )

    async def send_escalation(
        self,
        ticket_id: str,
        customer_id: str,
        reason: str,
        urgency: str,
        channel: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Send escalation notification.

        Args:
            ticket_id: Ticket UUID
            customer_id: Customer UUID
            reason: Escalation reason
            urgency: Urgency level
            channel: Source channel
            notes: Optional notes

        Returns:
            True if sent successfully
        """
        return await self.send_message(
            topic="fte.escalations",
            message={
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "reason": reason,
                "urgency": urgency,
                "channel": channel,
                "notes": notes,
                "escalated_at": datetime.now().isoformat()
            },
            key=ticket_id
        )

    async def send_metric(
        self,
        metric_type: str,
        metric_name: str,
        metric_value: float,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send metric to metrics topic.

        Args:
            metric_type: Metric type (e.g., 'performance', 'quality')
            metric_name: Metric name (e.g., 'response_time_ms')
            metric_value: Metric value
            channel: Optional channel filter
            metadata: Optional metadata

        Returns:
            True if sent successfully
        """
        return await self.send_message(
            topic="fte.metrics",
            message={
                "metric_type": metric_type,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "channel": channel,
                "metadata": metadata or {},
                "recorded_at": datetime.now().isoformat()
            }
        )

    async def send_to_dlq(
        self,
        original_topic: str,
        message: Dict[str, Any],
        error: str
    ) -> bool:
        """
        Send failed message to dead letter queue.

        Args:
            original_topic: Original topic name
            message: Original message
            error: Error description

        Returns:
            True if sent successfully
        """
        return await self.send_message(
            topic="fte.dlq",
            message={
                "original_topic": original_topic,
                "original_message": message,
                "error": error,
                "failed_at": datetime.now().isoformat()
            }
        )

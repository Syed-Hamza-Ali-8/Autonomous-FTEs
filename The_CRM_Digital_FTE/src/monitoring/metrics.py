"""
Monitoring and Metrics
Phase 2: Specialization

Prometheus metrics collection for the Customer Success Digital FTE.
"""

import time
from typing import Callable
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Application info
app_info = Info('fte_app', 'Customer Success Digital FTE application info')
app_info.info({
    'version': '1.0.0',
    'name': 'Customer Success Digital FTE'
})

# HTTP metrics
http_requests_total = Counter(
    'fte_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'fte_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Agent metrics
agent_messages_processed_total = Counter(
    'fte_agent_messages_processed_total',
    'Total messages processed by agent',
    ['channel', 'status']
)

agent_processing_duration_seconds = Histogram(
    'fte_agent_processing_duration_seconds',
    'Agent message processing duration in seconds',
    ['channel'],
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0]
)

agent_escalations_total = Counter(
    'fte_agent_escalations_total',
    'Total escalations to human support',
    ['channel', 'reason']
)

agent_tool_calls_total = Counter(
    'fte_agent_tool_calls_total',
    'Total agent tool calls',
    ['tool_name', 'status']
)

# Knowledge base metrics
kb_searches_total = Counter(
    'fte_kb_searches_total',
    'Total knowledge base searches',
    ['channel']
)

kb_search_relevance = Histogram(
    'fte_kb_search_relevance',
    'Knowledge base search relevance scores',
    ['channel'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Channel metrics
channel_messages_received_total = Counter(
    'fte_channel_messages_received_total',
    'Total messages received per channel',
    ['channel']
)

channel_messages_sent_total = Counter(
    'fte_channel_messages_sent_total',
    'Total messages sent per channel',
    ['channel', 'status']
)

# Database metrics
db_queries_total = Counter(
    'fte_db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'fte_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Kafka metrics
kafka_messages_produced_total = Counter(
    'fte_kafka_messages_produced_total',
    'Total Kafka messages produced',
    ['topic', 'status']
)

kafka_messages_consumed_total = Counter(
    'fte_kafka_messages_consumed_total',
    'Total Kafka messages consumed',
    ['topic', 'status']
)

kafka_consumer_lag = Gauge(
    'fte_kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic', 'partition']
)

# Ticket metrics
tickets_created_total = Counter(
    'fte_tickets_created_total',
    'Total tickets created',
    ['channel', 'priority']
)

tickets_resolved_total = Counter(
    'fte_tickets_resolved_total',
    'Total tickets resolved',
    ['channel', 'resolution_type']
)

ticket_resolution_duration_seconds = Histogram(
    'fte_ticket_resolution_duration_seconds',
    'Ticket resolution duration in seconds',
    ['channel'],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400]
)

# Customer metrics
customers_total = Gauge(
    'fte_customers_total',
    'Total number of customers'
)

active_conversations_total = Gauge(
    'fte_active_conversations_total',
    'Total number of active conversations',
    ['channel']
)

# Cost metrics
openai_api_calls_total = Counter(
    'fte_openai_api_calls_total',
    'Total OpenAI API calls',
    ['model', 'operation']
)

openai_tokens_used_total = Counter(
    'fte_openai_tokens_used_total',
    'Total OpenAI tokens used',
    ['model', 'token_type']
)

estimated_cost_dollars = Counter(
    'fte_estimated_cost_dollars',
    'Estimated cost in dollars',
    ['service']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        # Record request
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status = response.status_code

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        return response


def track_agent_processing(channel: str):
    """
    Decorator to track agent message processing.

    Usage:
        @track_agent_processing(channel='email')
        async def process_message(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time

                agent_messages_processed_total.labels(
                    channel=channel,
                    status=status
                ).inc()

                agent_processing_duration_seconds.labels(
                    channel=channel
                ).observe(duration)

        return wrapper
    return decorator


def track_db_query(operation: str, table: str):
    """
    Decorator to track database queries.

    Usage:
        @track_db_query(operation='select', table='customers')
        async def get_customer(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time

                db_queries_total.labels(
                    operation=operation,
                    table=table
                ).inc()

                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)

        return wrapper
    return decorator


def record_escalation(channel: str, reason: str):
    """Record an escalation event."""
    agent_escalations_total.labels(
        channel=channel,
        reason=reason
    ).inc()


def record_tool_call(tool_name: str, status: str = 'success'):
    """Record an agent tool call."""
    agent_tool_calls_total.labels(
        tool_name=tool_name,
        status=status
    ).inc()


def record_kb_search(channel: str, relevance_score: float):
    """Record a knowledge base search."""
    kb_searches_total.labels(channel=channel).inc()
    kb_search_relevance.labels(channel=channel).observe(relevance_score)


def record_message_received(channel: str):
    """Record a message received."""
    channel_messages_received_total.labels(channel=channel).inc()


def record_message_sent(channel: str, status: str = 'success'):
    """Record a message sent."""
    channel_messages_sent_total.labels(
        channel=channel,
        status=status
    ).inc()


def record_kafka_produced(topic: str, status: str = 'success'):
    """Record a Kafka message produced."""
    kafka_messages_produced_total.labels(
        topic=topic,
        status=status
    ).inc()


def record_kafka_consumed(topic: str, status: str = 'success'):
    """Record a Kafka message consumed."""
    kafka_messages_consumed_total.labels(
        topic=topic,
        status=status
    ).inc()


def record_ticket_created(channel: str, priority: str):
    """Record a ticket created."""
    tickets_created_total.labels(
        channel=channel,
        priority=priority
    ).inc()


def record_ticket_resolved(channel: str, resolution_type: str, duration_seconds: float):
    """Record a ticket resolved."""
    tickets_resolved_total.labels(
        channel=channel,
        resolution_type=resolution_type
    ).inc()

    ticket_resolution_duration_seconds.labels(
        channel=channel
    ).observe(duration_seconds)


def record_openai_call(model: str, operation: str, prompt_tokens: int, completion_tokens: int):
    """Record an OpenAI API call."""
    openai_api_calls_total.labels(
        model=model,
        operation=operation
    ).inc()

    openai_tokens_used_total.labels(
        model=model,
        token_type='prompt'
    ).inc(prompt_tokens)

    openai_tokens_used_total.labels(
        model=model,
        token_type='completion'
    ).inc(completion_tokens)

    # Estimate cost (approximate pricing)
    if model == 'gpt-4o-mini':
        cost = (prompt_tokens * 0.00015 / 1000) + (completion_tokens * 0.0006 / 1000)
    elif model == 'gpt-4o':
        cost = (prompt_tokens * 0.0025 / 1000) + (completion_tokens * 0.01 / 1000)
    else:
        cost = 0

    estimated_cost_dollars.labels(service='openai').inc(cost)


def update_customer_count(count: int):
    """Update total customer count."""
    customers_total.set(count)


def update_active_conversations(channel: str, count: int):
    """Update active conversation count."""
    active_conversations_total.labels(channel=channel).set(count)

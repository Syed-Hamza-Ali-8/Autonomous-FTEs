"""
FastAPI Application - Customer Success Digital FTE
Phase 2: Specialization

Main API application with webhook handlers and endpoints.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, Request, Response, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ..database.connection import get_db, check_db_health
from ..database.models import Customer, CustomerIdentifier, Conversation, Message, Ticket
from ..channels.gmail_integration import GmailIntegration
from ..channels.whatsapp_integration import WhatsAppIntegration
from .kafka_producer import KafkaProducer
from ..monitoring.metrics import MetricsMiddleware, record_message_received

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Customer Success Digital FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web Form",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics middleware
app.add_middleware(MetricsMiddleware)

# Initialize integrations
gmail = GmailIntegration()
whatsapp = WhatsAppIntegration()
kafka_producer = KafkaProducer()


# Pydantic models for request/response validation
class WebFormSubmission(BaseModel):
    """Web form submission model."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1, max_length=5000)
    phone: Optional[str] = Field(None, max_length=50)


class CustomerLookupResponse(BaseModel):
    """Customer lookup response model."""
    customer_id: str
    email: Optional[str]
    phone: Optional[str]
    name: Optional[str]
    created_at: str
    total_conversations: int
    total_tickets: int


class TicketResponse(BaseModel):
    """Ticket response model."""
    id: str
    customer_id: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    subject: str
    status: str
    priority: str
    category: str
    channel: str
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    escalated_at: Optional[str]
    escalation_reason: Optional[str]
    assigned_to: Optional[str]


class TicketDetailResponse(BaseModel):
    """Detailed ticket response with conversation history."""
    ticket: TicketResponse
    messages: list[Dict[str, Any]]


class TicketUpdateRequest(BaseModel):
    """Ticket update request model."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    escalation_reason: Optional[str] = None


class TicketStatsResponse(BaseModel):
    """Ticket statistics response model."""
    total: int
    open: int
    in_progress: int
    resolved: int
    escalated: int
    by_priority: Dict[str, int]
    by_channel: Dict[str, int]
    by_category: Dict[str, int]


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    database: str
    kafka: str


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Customer Success Digital FTE API...")

    # Initialize Kafka producer
    await kafka_producer.start()
    logger.info("Kafka producer initialized")

    # Authenticate Gmail (if credentials available)
    try:
        gmail.authenticate()
        logger.info("Gmail integration authenticated")
    except Exception as e:
        logger.warning(f"Gmail authentication failed: {e}")

    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Customer Success Digital FTE API...")

    # Close Kafka producer
    await kafka_producer.stop()
    logger.info("Kafka producer closed")

    logger.info("API shutdown complete")


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status of all services
    """
    # Check database
    db_healthy = await check_db_health()

    # Check Kafka
    kafka_healthy = kafka_producer.is_connected()

    overall_status = "healthy" if (db_healthy and kafka_healthy) else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "database": "healthy" if db_healthy else "unhealthy",
        "kafka": "healthy" if kafka_healthy else "unhealthy"
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Gmail webhook handler
@app.post("/webhooks/gmail")
async def gmail_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Gmail webhook handler (for Pub/Sub notifications).

    Note: This is a placeholder for Gmail push notifications.
    In production, you would verify the Pub/Sub message signature.
    """
    try:
        # Parse Pub/Sub message
        body = await request.json()
        logger.info(f"Received Gmail webhook: {body}")

        # In production, you would:
        # 1. Verify Pub/Sub signature
        # 2. Decode the message
        # 3. Fetch the actual email using Gmail API
        # 4. Process the email

        # For now, return success
        return {"status": "received"}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WhatsApp webhook handler
@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    WhatsApp webhook handler (Twilio).

    Receives incoming WhatsApp messages and queues them for processing.
    """
    try:
        # Get form data (Twilio sends form-encoded data)
        form_data = await request.form()
        webhook_data = dict(form_data)

        logger.info(f"Received WhatsApp message from {webhook_data.get('From')}")

        # Validate Twilio signature
        if x_twilio_signature:
            url = str(request.url)
            is_valid = whatsapp.validate_webhook(url, webhook_data, x_twilio_signature)
            if not is_valid:
                logger.warning("Invalid Twilio signature")
                raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse incoming message
        parsed_message = whatsapp.parse_incoming_message(webhook_data)

        # Look up or create customer
        customer = await get_or_create_customer(
            db=db,
            phone=parsed_message['customer_phone'],
            name=parsed_message.get('customer_name'),
            channel='whatsapp'
        )

        # Create or get active conversation
        conversation = await get_or_create_conversation(
            db=db,
            customer_id=customer.id,
            channel='whatsapp'
        )

        # Store incoming message
        message = Message(
            conversation_id=conversation.id,
            role="customer",
            content=parsed_message['content'],
            channel='whatsapp',
            channel_message_id=parsed_message['channel_message_id'],
            metadata=parsed_message['metadata']
        )
        db.add(message)
        await db.commit()

        # Send to Kafka for async processing
        await kafka_producer.send_message(
            topic="fte.tickets.incoming",
            message={
                "customer_id": str(customer.id),
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "channel": "whatsapp",
                "content": parsed_message['content'],
                "metadata": parsed_message['metadata']
            }
        )

        logger.info(f"WhatsApp message queued for processing: {message.id}")

        # Return TwiML response (empty response, we'll reply async)
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Web form submission endpoint
@app.post("/support/submit")
async def submit_support_request(
    submission: WebFormSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Web form submission endpoint.

    Receives support requests from the web form and queues them for processing.
    """
    try:
        logger.info(f"Received web form submission from {submission.email}")

        # Look up or create customer
        customer = await get_or_create_customer(
            db=db,
            email=submission.email,
            phone=submission.phone,
            name=submission.name,
            channel='web_form'
        )

        # Create new conversation
        conversation = await get_or_create_conversation(
            db=db,
            customer_id=customer.id,
            channel='web_form'
        )

        # Store incoming message
        message = Message(
            conversation_id=conversation.id,
            role="customer",
            content=submission.message,
            channel='web_form',
            metadata={
                'subject': submission.subject,
                'submitted_at': datetime.now().isoformat()
            }
        )
        db.add(message)
        await db.commit()

        # Send to Kafka for async processing
        await kafka_producer.send_message(
            topic="fte.tickets.incoming",
            message={
                "customer_id": str(customer.id),
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "channel": "web_form",
                "content": submission.message,
                "metadata": {
                    'subject': submission.subject,
                    'name': submission.name,
                    'email': submission.email
                }
            }
        )

        logger.info(f"Web form submission queued for processing: {message.id}")

        return {
            "success": True,
            "message": "Your support request has been received. We'll respond shortly.",
            "ticket_id": str(conversation.id)
        }

    except Exception as e:
        logger.error(f"Web form submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Customer lookup endpoint
@app.get("/customers/lookup", response_model=CustomerLookupResponse)
async def lookup_customer(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Look up customer by email or phone.

    Args:
        email: Customer email
        phone: Customer phone

    Returns:
        Customer information
    """
    try:
        if not email and not phone:
            raise HTTPException(status_code=400, detail="Either email or phone is required")

        # Look up customer
        query = select(Customer)
        if email:
            query = query.where(Customer.email == email)
        elif phone:
            query = query.where(Customer.phone == phone)

        result = await db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Count conversations and tickets
        from ..database.models import Conversation, Ticket

        conv_result = await db.execute(
            select(Conversation).where(Conversation.customer_id == customer.id)
        )
        conversations = conv_result.scalars().all()

        ticket_result = await db.execute(
            select(Ticket).where(Ticket.customer_id == customer.id)
        )
        tickets = ticket_result.scalars().all()

        return {
            "customer_id": str(customer.id),
            "email": customer.email,
            "phone": customer.phone,
            "name": customer.name,
            "created_at": customer.created_at.isoformat(),
            "total_conversations": len(conversations),
            "total_tickets": len(tickets)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ticket management endpoints
@app.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    channel: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tickets with optional filtering.

    Args:
        status: Filter by status (open, in_progress, resolved, escalated)
        priority: Filter by priority (low, medium, high)
        channel: Filter by channel (email, whatsapp, web_form)
        category: Filter by category
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of tickets
    """
    try:
        from sqlalchemy import desc, and_

        # Build query with joins
        query = select(Ticket, Customer).join(
            Customer, Ticket.customer_id == Customer.id
        )

        # Apply filters
        filters = []
        if status:
            filters.append(Ticket.status == status)
        if priority:
            filters.append(Ticket.priority == priority)
        if channel:
            filters.append(Ticket.channel == channel)
        if category:
            filters.append(Ticket.category == category)

        if filters:
            query = query.where(and_(*filters))

        # Order by created_at descending
        query = query.order_by(desc(Ticket.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        rows = result.all()

        # Format response
        tickets = []
        for ticket, customer in rows:
            tickets.append({
                "id": str(ticket.id),
                "customer_id": str(ticket.customer_id),
                "customer_name": customer.name,
                "customer_email": customer.email,
                "subject": ticket.subject,
                "status": ticket.status,
                "priority": ticket.priority,
                "category": ticket.category,
                "channel": ticket.channel,
                "created_at": ticket.created_at.isoformat(),
                "updated_at": ticket.updated_at.isoformat(),
                "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                "escalated_at": ticket.escalated_at.isoformat() if ticket.escalated_at else None,
                "escalation_reason": ticket.escalation_reason,
                "assigned_to": ticket.assigned_to
            })

        return tickets

    except Exception as e:
        logger.error(f"List tickets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/stats", response_model=TicketStatsResponse)
async def get_ticket_stats(db: AsyncSession = Depends(get_db)):
    """
    Get ticket statistics.

    Returns:
        Ticket statistics including counts by status, priority, channel, and category
    """
    try:
        from sqlalchemy import func

        # Total tickets
        total_result = await db.execute(select(func.count(Ticket.id)))
        total = total_result.scalar()

        # By status
        status_result = await db.execute(
            select(Ticket.status, func.count(Ticket.id))
            .group_by(Ticket.status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # By priority
        priority_result = await db.execute(
            select(Ticket.priority, func.count(Ticket.id))
            .group_by(Ticket.priority)
        )
        priority_counts = {row[0]: row[1] for row in priority_result.all()}

        # By channel
        channel_result = await db.execute(
            select(Ticket.channel, func.count(Ticket.id))
            .group_by(Ticket.channel)
        )
        channel_counts = {row[0]: row[1] for row in channel_result.all()}

        # By category
        category_result = await db.execute(
            select(Ticket.category, func.count(Ticket.id))
            .group_by(Ticket.category)
        )
        category_counts = {row[0]: row[1] for row in category_result.all()}

        return {
            "total": total,
            "open": status_counts.get("open", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "resolved": status_counts.get("resolved", 0),
            "escalated": status_counts.get("escalated", 0),
            "by_priority": priority_counts,
            "by_channel": channel_counts,
            "by_category": category_counts
        }

    except Exception as e:
        logger.error(f"Get ticket stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed ticket information including conversation history.

    Args:
        ticket_id: Ticket UUID

    Returns:
        Detailed ticket information with messages
    """
    try:
        # Get ticket with customer info
        query = select(Ticket, Customer).join(
            Customer, Ticket.customer_id == Customer.id
        ).where(Ticket.id == UUID(ticket_id))

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket, customer = row

        # Get conversation messages
        messages_query = select(Message).where(
            Message.conversation_id == ticket.conversation_id
        ).order_by(Message.timestamp)

        messages_result = await db.execute(messages_query)
        messages = messages_result.scalars().all()

        # Format response as plain dictionaries
        ticket_data = {
            "id": str(ticket.id),
            "customer_id": str(ticket.customer_id),
            "customer_name": customer.name,
            "customer_email": customer.email,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "channel": ticket.channel,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "escalated_at": ticket.escalated_at.isoformat() if ticket.escalated_at else None,
            "escalation_reason": ticket.escalation_reason,
            "assigned_to": ticket.assigned_to
        }

        messages_data = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "channel": msg.channel,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata_ if msg.metadata_ else {}
            }
            for msg in messages
        ]

        # Return plain dict, let FastAPI handle serialization
        return {
            "ticket": ticket_data,
            "messages": messages_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ticket error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    update: TicketUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update ticket status, priority, or assignment.

    Args:
        ticket_id: Ticket UUID
        update: Update request with fields to change

    Returns:
        Updated ticket information
    """
    try:
        # Get ticket
        query = select(Ticket).where(Ticket.id == UUID(ticket_id))
        result = await db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Update fields
        if update.status is not None:
            ticket.status = update.status
            if update.status == "resolved":
                ticket.resolved_at = datetime.now()
            elif update.status == "escalated":
                ticket.escalated_at = datetime.now()

        if update.priority is not None:
            ticket.priority = update.priority

        if update.assigned_to is not None:
            ticket.assigned_to = update.assigned_to

        if update.escalation_reason is not None:
            ticket.escalation_reason = update.escalation_reason

        await db.commit()
        await db.refresh(ticket)

        return {
            "success": True,
            "message": "Ticket updated successfully",
            "ticket_id": str(ticket.id),
            "status": ticket.status,
            "priority": ticket.priority
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update ticket error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def get_or_create_customer(
    db: AsyncSession,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    channel: str = None
) -> Customer:
    """
    Get existing customer or create new one.

    Args:
        db: Database session
        email: Customer email
        phone: Customer phone
        name: Customer name
        channel: Source channel

    Returns:
        Customer object
    """
    # Try to find existing customer
    query = select(Customer)
    if email:
        query = query.where(Customer.email == email)
    elif phone:
        query = query.where(Customer.phone == phone)
    else:
        raise ValueError("Either email or phone is required")

    result = await db.execute(query)
    customer = result.scalar_one_or_none()

    if customer:
        # Update name if provided and not set
        if name and not customer.name:
            customer.name = name
            await db.commit()
        return customer

    # Create new customer
    customer = Customer(
        email=email,
        phone=phone,
        name=name,
        metadata={'source_channel': channel}
    )
    db.add(customer)
    await db.flush()

    # Create customer identifier
    if email:
        identifier = CustomerIdentifier(
            customer_id=customer.id,
            identifier_type='email',
            identifier_value=email,
            verified=False
        )
        db.add(identifier)

    if phone:
        identifier = CustomerIdentifier(
            customer_id=customer.id,
            identifier_type='phone',
            identifier_value=phone,
            verified=False
        )
        db.add(identifier)

    await db.commit()
    logger.info(f"Created new customer: {customer.id}")

    return customer


async def get_or_create_conversation(
    db: AsyncSession,
    customer_id: UUID,
    channel: str
) -> Conversation:
    """
    Get active conversation or create new one.

    Args:
        db: Database session
        customer_id: Customer UUID
        channel: Channel name

    Returns:
        Conversation object
    """
    # Look for active conversation in this channel
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.customer_id == customer_id,
            Conversation.channel == channel,
            Conversation.status == 'active'
        )
        .order_by(Conversation.created_at.desc())
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        return conversation

    # Create new conversation
    conversation = Conversation(
        customer_id=customer_id,
        channel=channel,
        status='active'
    )
    db.add(conversation)
    await db.commit()

    logger.info(f"Created new conversation: {conversation.id}")

    return conversation


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

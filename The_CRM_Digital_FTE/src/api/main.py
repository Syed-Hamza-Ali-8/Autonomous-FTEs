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
from ..database.models import Customer, CustomerIdentifier, Conversation, Message
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

"""
Database Models
Phase 2: Specialization

SQLAlchemy models corresponding to the database schema.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, DateTime,
    ForeignKey, CheckConstraint, Index, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, VECTOR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .connection import Base


class Customer(Base):
    """Customer model - unified across all channels."""
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    identifiers: Mapped[List["CustomerIdentifier"]] = relationship("CustomerIdentifier", back_populates="customer", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="customers_email_or_phone_required"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Customer(id={self.id}, email={self.email}, name={self.name})>"


class CustomerIdentifier(Base):
    """Customer identifier for cross-channel matching."""
    __tablename__ = "customer_identifiers"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(255), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="identifiers")

    __table_args__ = (
        Index("idx_customer_identifiers_customer_id", "customer_id"),
        Index("idx_customer_identifiers_type_value", "identifier_type", "identifier_value"),
    )

    def __repr__(self):
        return f"<CustomerIdentifier(type={self.identifier_type}, value={self.identifier_value})>"


class Conversation(Base):
    """Conversation thread."""
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("channel IN ('email', 'whatsapp', 'web_form')", name="conversations_channel_check"),
        CheckConstraint("status IN ('active', 'resolved', 'escalated')", name="conversations_status_check"),
        Index("idx_conversations_customer_id", "customer_id"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_created_at", "created_at"),
        Index("idx_conversations_channel", "channel"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, channel={self.channel}, status={self.status})>"


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('customer', 'agent', 'system')", name="messages_role_check"),
        CheckConstraint("channel IN ('email', 'whatsapp', 'web_form')", name="messages_channel_check"),
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_timestamp", "timestamp"),
        Index("idx_messages_channel_message_id", "channel_message_id"),
        Index("idx_messages_role", "role"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, channel={self.channel})>"


class Ticket(Base):
    """Support ticket."""
    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    escalation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="tickets")

    __table_args__ = (
        CheckConstraint("status IN ('open', 'in_progress', 'resolved', 'escalated')", name="tickets_status_check"),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="tickets_priority_check"),
        CheckConstraint("channel IN ('email', 'whatsapp', 'web_form')", name="tickets_channel_check"),
        Index("idx_tickets_customer_id", "customer_id"),
        Index("idx_tickets_conversation_id", "conversation_id"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_priority", "priority"),
        Index("idx_tickets_category", "category"),
        Index("idx_tickets_created_at", "created_at"),
        Index("idx_tickets_channel", "channel"),
    )

    def __repr__(self):
        return f"<Ticket(id={self.id}, subject={self.subject}, status={self.status})>"


class KnowledgeBase(Base):
    """Knowledge base article with vector embedding."""
    __tablename__ = "knowledge_base"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    embedding = Column(VECTOR(1536))  # OpenAI text-embedding-3-small
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("idx_knowledge_base_category", "category"),
    )

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title={self.title})>"


class ChannelConfig(Base):
    """Channel-specific configuration."""
    __tablename__ = "channel_configs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("channel IN ('email', 'whatsapp', 'web_form')", name="channel_configs_channel_check"),
    )

    def __repr__(self):
        return f"<ChannelConfig(channel={self.channel}, enabled={self.enabled})>"


class AgentMetric(Base):
    """Agent performance metrics."""
    __tablename__ = "agent_metrics"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("idx_agent_metrics_type", "metric_type"),
        Index("idx_agent_metrics_name", "metric_name"),
        Index("idx_agent_metrics_timestamp", "timestamp"),
        Index("idx_agent_metrics_channel", "channel"),
    )

    def __repr__(self):
        return f"<AgentMetric(type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"

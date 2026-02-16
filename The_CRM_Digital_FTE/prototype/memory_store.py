"""
Memory and State Management
Phase: Incubation (TASK-008)

Simple in-memory state management for tracking conversations and customer context.
For prototype: Uses dictionaries and JSON files.
Production version will use PostgreSQL with proper persistence.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class Customer:
    """Customer record."""
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    created_at: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Conversation:
    """Conversation thread."""
    id: str
    customer_id: str
    channel: str
    status: str  # active, resolved, escalated
    created_at: str = None
    updated_at: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Message:
    """Individual message in a conversation."""
    id: str
    conversation_id: str
    role: str  # customer, agent, system
    content: str
    channel: str
    timestamp: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Ticket:
    """Support ticket."""
    id: str
    customer_id: str
    conversation_id: str
    subject: str
    status: str  # open, in_progress, resolved, escalated
    priority: str  # low, medium, high
    category: str
    channel: str
    created_at: str = None
    updated_at: str = None
    resolved_at: Optional[str] = None
    escalated_at: Optional[str] = None
    escalation_reason: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.metadata is None:
            self.metadata = {}


class MemoryStore:
    """
    In-memory state management for prototype.
    Tracks customers, conversations, messages, and tickets.
    """

    def __init__(self, persistence_path: str = None):
        """
        Initialize memory store.

        Args:
            persistence_path: Optional path to save/load state
        """
        self.customers: Dict[str, Customer] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.messages: Dict[str, List[Message]] = {}  # conversation_id -> messages
        self.tickets: Dict[str, Ticket] = {}

        # Indexes for fast lookup
        self.customer_by_email: Dict[str, str] = {}  # email -> customer_id
        self.customer_by_phone: Dict[str, str] = {}  # phone -> customer_id
        self.conversations_by_customer: Dict[str, List[str]] = {}  # customer_id -> conversation_ids
        self.tickets_by_customer: Dict[str, List[str]] = {}  # customer_id -> ticket_ids

        self.persistence_path = persistence_path
        if persistence_path and os.path.exists(persistence_path):
            self.load_state()

    def find_or_create_customer(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None
    ) -> Customer:
        """
        Find existing customer or create new one.

        Args:
            email: Customer email
            phone: Customer phone
            name: Customer name

        Returns:
            Customer object
        """
        # Try to find by email
        if email and email in self.customer_by_email:
            customer_id = self.customer_by_email[email]
            customer = self.customers[customer_id]

            # Update phone if provided and not set
            if phone and not customer.phone:
                customer.phone = phone
                self.customer_by_phone[phone] = customer_id

            # Update name if provided and not set
            if name and not customer.name:
                customer.name = name

            return customer

        # Try to find by phone
        if phone and phone in self.customer_by_phone:
            customer_id = self.customer_by_phone[phone]
            customer = self.customers[customer_id]

            # Update email if provided and not set
            if email and not customer.email:
                customer.email = email
                self.customer_by_email[email] = customer_id

            # Update name if provided and not set
            if name and not customer.name:
                customer.name = name

            return customer

        # Create new customer
        customer_id = str(uuid4())
        customer = Customer(
            id=customer_id,
            email=email,
            phone=phone,
            name=name
        )

        self.customers[customer_id] = customer

        if email:
            self.customer_by_email[email] = customer_id
        if phone:
            self.customer_by_phone[phone] = customer_id

        self.conversations_by_customer[customer_id] = []
        self.tickets_by_customer[customer_id] = []

        return customer

    def create_conversation(
        self,
        customer_id: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create new conversation."""
        conversation_id = str(uuid4())
        conversation = Conversation(
            id=conversation_id,
            customer_id=customer_id,
            channel=channel,
            status='active',
            metadata=metadata or {}
        )

        self.conversations[conversation_id] = conversation
        self.messages[conversation_id] = []
        self.conversations_by_customer[customer_id].append(conversation_id)

        return conversation

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add message to conversation."""
        message_id = str(uuid4())
        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            channel=channel,
            metadata=metadata or {}
        )

        if conversation_id not in self.messages:
            self.messages[conversation_id] = []

        self.messages[conversation_id].append(message)

        # Update conversation timestamp
        if conversation_id in self.conversations:
            self.conversations[conversation_id].updated_at = datetime.now().isoformat()

        return message

    def create_ticket(
        self,
        customer_id: str,
        conversation_id: str,
        subject: str,
        category: str,
        priority: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Ticket:
        """Create support ticket."""
        ticket_id = str(uuid4())
        ticket = Ticket(
            id=ticket_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            subject=subject,
            status='open',
            priority=priority,
            category=category,
            channel=channel,
            metadata=metadata or {}
        )

        self.tickets[ticket_id] = ticket
        self.tickets_by_customer[customer_id].append(ticket_id)

        return ticket

    def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        escalation_reason: Optional[str] = None
    ):
        """Update ticket status."""
        if ticket_id not in self.tickets:
            return

        ticket = self.tickets[ticket_id]
        ticket.status = status
        ticket.updated_at = datetime.now().isoformat()

        if status == 'resolved':
            ticket.resolved_at = datetime.now().isoformat()
        elif status == 'escalated':
            ticket.escalated_at = datetime.now().isoformat()
            ticket.escalation_reason = escalation_reason

    def get_customer_history(
        self,
        customer_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get customer's conversation history.

        Args:
            customer_id: Customer ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries
        """
        if customer_id not in self.conversations_by_customer:
            return []

        conversation_ids = self.conversations_by_customer[customer_id]
        history = []

        for conv_id in conversation_ids[-limit:]:
            if conv_id not in self.conversations:
                continue

            conversation = self.conversations[conv_id]
            messages = self.messages.get(conv_id, [])

            # Find associated ticket
            ticket = None
            for t_id in self.tickets_by_customer.get(customer_id, []):
                if self.tickets[t_id].conversation_id == conv_id:
                    ticket = self.tickets[t_id]
                    break

            history.append({
                'conversation_id': conv_id,
                'channel': conversation.channel,
                'status': conversation.status,
                'created_at': conversation.created_at,
                'message_count': len(messages),
                'ticket': asdict(ticket) if ticket else None
            })

        return history

    def get_conversation_messages(
        self,
        conversation_id: str
    ) -> List[Message]:
        """Get all messages in a conversation."""
        return self.messages.get(conversation_id, [])

    def save_state(self):
        """Save state to disk."""
        if not self.persistence_path:
            return

        state = {
            'customers': {k: asdict(v) for k, v in self.customers.items()},
            'conversations': {k: asdict(v) for k, v in self.conversations.items()},
            'messages': {
                k: [asdict(m) for m in v]
                for k, v in self.messages.items()
            },
            'tickets': {k: asdict(v) for k, v in self.tickets.items()},
            'indexes': {
                'customer_by_email': self.customer_by_email,
                'customer_by_phone': self.customer_by_phone,
                'conversations_by_customer': self.conversations_by_customer,
                'tickets_by_customer': self.tickets_by_customer
            }
        }

        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        with open(self.persistence_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load state from disk."""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return

        with open(self.persistence_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Load customers
        self.customers = {
            k: Customer(**v) for k, v in state.get('customers', {}).items()
        }

        # Load conversations
        self.conversations = {
            k: Conversation(**v) for k, v in state.get('conversations', {}).items()
        }

        # Load messages
        self.messages = {
            k: [Message(**m) for m in v]
            for k, v in state.get('messages', {}).items()
        }

        # Load tickets
        self.tickets = {
            k: Ticket(**v) for k, v in state.get('tickets', {}).items()
        }

        # Load indexes
        indexes = state.get('indexes', {})
        self.customer_by_email = indexes.get('customer_by_email', {})
        self.customer_by_phone = indexes.get('customer_by_phone', {})
        self.conversations_by_customer = indexes.get('conversations_by_customer', {})
        self.tickets_by_customer = indexes.get('tickets_by_customer', {})

    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        return {
            'total_customers': len(self.customers),
            'total_conversations': len(self.conversations),
            'total_messages': sum(len(msgs) for msgs in self.messages.values()),
            'total_tickets': len(self.tickets),
            'active_conversations': sum(
                1 for c in self.conversations.values() if c.status == 'active'
            ),
            'open_tickets': sum(
                1 for t in self.tickets.values() if t.status == 'open'
            ),
            'escalated_tickets': sum(
                1 for t in self.tickets.values() if t.status == 'escalated'
            )
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("MEMORY STORE TESTING")
    print("=" * 80)
    print()

    # Initialize memory store
    store = MemoryStore(persistence_path='../data/memory_state.json')

    # Test 1: Create customers
    print("Test 1: Creating customers")
    print("-" * 80)
    customer1 = store.find_or_create_customer(
        email="john.doe@example.com",
        name="John Doe"
    )
    print(f"Created customer: {customer1.id} - {customer1.name} ({customer1.email})")

    customer2 = store.find_or_create_customer(
        phone="+14155551234",
        name="Jane Smith"
    )
    print(f"Created customer: {customer2.id} - {customer2.name} ({customer2.phone})")

    # Test finding existing customer
    customer1_again = store.find_or_create_customer(email="john.doe@example.com")
    print(f"Found existing customer: {customer1_again.id == customer1.id}")
    print()

    # Test 2: Create conversations
    print("Test 2: Creating conversations")
    print("-" * 80)
    conv1 = store.create_conversation(
        customer_id=customer1.id,
        channel='email',
        metadata={'subject': 'Password reset help'}
    )
    print(f"Created conversation: {conv1.id} for customer {customer1.name}")

    conv2 = store.create_conversation(
        customer_id=customer2.id,
        channel='whatsapp'
    )
    print(f"Created conversation: {conv2.id} for customer {customer2.name}")
    print()

    # Test 3: Add messages
    print("Test 3: Adding messages")
    print("-" * 80)
    msg1 = store.add_message(
        conversation_id=conv1.id,
        role='customer',
        content='I need help resetting my password',
        channel='email'
    )
    print(f"Added customer message: {msg1.id}")

    msg2 = store.add_message(
        conversation_id=conv1.id,
        role='agent',
        content='I can help you with that. Here are the steps...',
        channel='email'
    )
    print(f"Added agent message: {msg2.id}")
    print()

    # Test 4: Create tickets
    print("Test 4: Creating tickets")
    print("-" * 80)
    ticket1 = store.create_ticket(
        customer_id=customer1.id,
        conversation_id=conv1.id,
        subject='Password reset help',
        category='technical',
        priority='high',
        channel='email'
    )
    print(f"Created ticket: {ticket1.id} - {ticket1.subject}")
    print()

    # Test 5: Update ticket status
    print("Test 5: Updating ticket status")
    print("-" * 80)
    store.update_ticket_status(ticket1.id, 'resolved')
    print(f"Updated ticket {ticket1.id} to resolved")
    print()

    # Test 6: Get customer history
    print("Test 6: Getting customer history")
    print("-" * 80)
    history = store.get_customer_history(customer1.id)
    print(f"Customer {customer1.name} has {len(history)} conversations:")
    for h in history:
        print(f"  - {h['channel']} conversation ({h['message_count']} messages)")
    print()

    # Test 7: Get statistics
    print("Test 7: Memory store statistics")
    print("-" * 80)
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    # Test 8: Save state
    print("Test 8: Saving state")
    print("-" * 80)
    store.save_state()
    print(f"State saved to: {store.persistence_path}")
    print()

    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

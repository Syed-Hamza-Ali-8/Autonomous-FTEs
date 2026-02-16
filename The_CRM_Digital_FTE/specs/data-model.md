# Customer Success FTE - Data Model

**Feature:** Customer Success Digital FTE
**Version:** 1.0.0
**Status:** Draft
**Created:** 2026-02-15
**Last Updated:** 2026-02-15

---

## Overview

This document defines the complete data model for the Customer Success FTE system, including database schema, data types, relationships, and constraints.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│    customers    │
│─────────────────│
│ id (PK)         │
│ email           │◄──────┐
│ phone           │       │
│ name            │       │
│ created_at      │       │
│ metadata        │       │
└─────────────────┘       │
         △                │
         │                │
         │                │
┌────────┴────────────────┴──────┐
│    customer_identifiers        │
│────────────────────────────────│
│ id (PK)                        │
│ customer_id (FK)               │
│ identifier_type                │
│ identifier_value               │
│ verified                       │
│ created_at                     │
└────────────────────────────────┘
         △
         │
         │
┌────────┴────────────┐
│   conversations     │
│─────────────────────│
│ id (PK)             │
│ customer_id (FK)    │
│ initial_channel     │
│ started_at          │
│ ended_at            │
│ status              │
│ sentiment_score     │
│ resolution_type     │
│ escalated_to        │
│ metadata            │
└─────────────────────┘
         △
         │
         ├──────────────────┐
         │                  │
┌────────┴────────┐  ┌──────┴──────┐
│    messages     │  │   tickets   │
│─────────────────│  │─────────────│
│ id (PK)         │  │ id (PK)     │
│ conversation_id │  │ conversation│
│ channel         │  │ customer_id │
│ direction       │  │ source_ch.. │
│ role            │  │ category    │
│ content         │  │ priority    │
│ created_at      │  │ status      │
│ tokens_used     │  │ created_at  │
│ latency_ms      │  │ resolved_at │
│ tool_calls      │  │ resolution..│
│ channel_msg_id  │  └─────────────┘
│ delivery_status │
└─────────────────┘

┌─────────────────────┐
│   knowledge_base    │
│─────────────────────│
│ id (PK)             │
│ title               │
│ content             │
│ category            │
│ embedding (vector)  │
│ created_at          │
│ updated_at          │
└─────────────────────┘

┌─────────────────────┐
│  channel_configs    │
│─────────────────────│
│ id (PK)             │
│ channel             │
│ enabled             │
│ config              │
│ response_template   │
│ max_response_length │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│   agent_metrics     │
│─────────────────────│
│ id (PK)             │
│ metric_name         │
│ metric_value        │
│ channel             │
│ dimensions          │
│ recorded_at         │
└─────────────────────┘
```

---

## Table Definitions

### 1. customers

**Purpose:** Store unified customer records across all channels

**Schema:**
```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key, auto-generated |
| email | VARCHAR(255) | YES | Primary email address (unique) |
| phone | VARCHAR(50) | YES | Primary phone number |
| name | VARCHAR(255) | YES | Customer name |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Record creation timestamp |
| metadata | JSONB | NO | Additional customer data (preferences, tags, etc.) |

**Constraints:**
- `email` must be unique (case-insensitive)
- At least one of `email` or `phone` must be provided
- `email` format validated at application layer
- `phone` normalized at application layer

**Sample Data:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "name": "John Doe",
  "created_at": "2026-02-15T10:30:00Z",
  "metadata": {
    "company": "Acme Corp",
    "plan": "professional",
    "timezone": "America/New_York"
  }
}
```

---

### 2. customer_identifiers

**Purpose:** Track multiple identifiers per customer for cross-channel matching

**Schema:**
```sql
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| customer_id | UUID | NO | Foreign key to customers table |
| identifier_type | VARCHAR(50) | NO | Type: 'email', 'phone', 'whatsapp' |
| identifier_value | VARCHAR(255) | NO | The actual identifier value |
| verified | BOOLEAN | NO | Whether identifier is verified |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Record creation timestamp |

**Constraints:**
- `UNIQUE(identifier_type, identifier_value)` - No duplicate identifiers
- `identifier_type` must be one of: 'email', 'phone', 'whatsapp'
- `identifier_value` normalized before storage

**Sample Data:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "identifier_type": "email",
    "identifier_value": "john.doe@example.com",
    "verified": true,
    "created_at": "2026-02-15T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "identifier_type": "whatsapp",
    "identifier_value": "+15551234567",
    "verified": true,
    "created_at": "2026-02-15T11:45:00Z"
  }
]
```

---

### 3. conversations

**Purpose:** Track conversation threads across channels

**Schema:**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_channel ON conversations(initial_channel);
CREATE INDEX idx_conversations_started ON conversations(started_at);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| customer_id | UUID | NO | Foreign key to customers |
| initial_channel | VARCHAR(50) | NO | Channel where conversation started |
| started_at | TIMESTAMP WITH TIME ZONE | NO | Conversation start time |
| ended_at | TIMESTAMP WITH TIME ZONE | YES | Conversation end time |
| status | VARCHAR(50) | NO | 'active', 'resolved', 'escalated' |
| sentiment_score | DECIMAL(3,2) | YES | Average sentiment (0.00-1.00) |
| resolution_type | VARCHAR(50) | YES | How conversation was resolved |
| escalated_to | VARCHAR(255) | YES | Human agent email if escalated |
| metadata | JSONB | NO | Additional conversation data |

**Constraints:**
- `initial_channel` must be one of: 'email', 'whatsapp', 'web_form'
- `status` must be one of: 'active', 'resolved', 'escalated'
- `sentiment_score` range: 0.00 to 1.00
- `ended_at` must be >= `started_at`

**Sample Data:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "initial_channel": "email",
  "started_at": "2026-02-15T10:30:00Z",
  "ended_at": "2026-02-15T10:45:00Z",
  "status": "resolved",
  "sentiment_score": 0.85,
  "resolution_type": "answered",
  "escalated_to": null,
  "metadata": {
    "channels_used": ["email", "whatsapp"],
    "messages_count": 5,
    "resolution_time_seconds": 900
  }
}
```

---

### 4. messages

**Purpose:** Store all messages in conversations with channel metadata

**Schema:**
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),
    delivery_status VARCHAR(50) DEFAULT 'pending'
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_channel_msg_id ON messages(channel_message_id);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| conversation_id | UUID | NO | Foreign key to conversations |
| channel | VARCHAR(50) | NO | Channel: 'email', 'whatsapp', 'web_form' |
| direction | VARCHAR(20) | NO | 'inbound' or 'outbound' |
| role | VARCHAR(20) | NO | 'customer', 'agent', 'system' |
| content | TEXT | NO | Message content |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Message timestamp |
| tokens_used | INTEGER | YES | OpenAI tokens used (agent messages only) |
| latency_ms | INTEGER | YES | Processing latency (agent messages only) |
| tool_calls | JSONB | NO | Array of tool calls made |
| channel_message_id | VARCHAR(255) | YES | External message ID (Gmail, Twilio) |
| delivery_status | VARCHAR(50) | NO | 'pending', 'sent', 'delivered', 'failed' |

**Constraints:**
- `channel` must be one of: 'email', 'whatsapp', 'web_form'
- `direction` must be one of: 'inbound', 'outbound'
- `role` must be one of: 'customer', 'agent', 'system'
- `delivery_status` must be one of: 'pending', 'sent', 'delivered', 'failed'

**Sample Data:**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440004",
    "conversation_id": "770e8400-e29b-41d4-a716-446655440003",
    "channel": "email",
    "direction": "inbound",
    "role": "customer",
    "content": "How do I reset my password?",
    "created_at": "2026-02-15T10:30:00Z",
    "tokens_used": null,
    "latency_ms": null,
    "tool_calls": [],
    "channel_message_id": "18d5e2f3a4b6c7d8",
    "delivery_status": "delivered"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440005",
    "conversation_id": "770e8400-e29b-41d4-a716-446655440003",
    "channel": "email",
    "direction": "outbound",
    "role": "agent",
    "content": "To reset your password, go to Settings > Security > Reset Password...",
    "created_at": "2026-02-15T10:30:15Z",
    "tokens_used": 450,
    "latency_ms": 1200,
    "tool_calls": [
      {"tool": "search_knowledge_base", "query": "password reset"},
      {"tool": "send_response", "channel": "email"}
    ],
    "channel_message_id": "18d5e2f3a4b6c7d9",
    "delivery_status": "sent"
  }
]
```

---

### 5. tickets

**Purpose:** Track support tickets linked to conversations

**Schema:**
```sql
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_created ON tickets(created_at);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key (ticket ID) |
| conversation_id | UUID | NO | Foreign key to conversations |
| customer_id | UUID | NO | Foreign key to customers |
| source_channel | VARCHAR(50) | NO | Channel where ticket originated |
| category | VARCHAR(100) | YES | Ticket category |
| priority | VARCHAR(20) | NO | 'low', 'medium', 'high' |
| status | VARCHAR(50) | NO | 'open', 'processing', 'resolved', 'escalated' |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Ticket creation time |
| resolved_at | TIMESTAMP WITH TIME ZONE | YES | Ticket resolution time |
| resolution_notes | TEXT | YES | Notes on how ticket was resolved |

**Constraints:**
- `source_channel` must be one of: 'email', 'whatsapp', 'web_form'
- `priority` must be one of: 'low', 'medium', 'high'
- `status` must be one of: 'open', 'processing', 'resolved', 'escalated'
- `resolved_at` must be >= `created_at`

**Sample Data:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440006",
  "conversation_id": "770e8400-e29b-41d4-a716-446655440003",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_channel": "email",
  "category": "authentication",
  "priority": "medium",
  "status": "resolved",
  "created_at": "2026-02-15T10:30:00Z",
  "resolved_at": "2026-02-15T10:45:00Z",
  "resolution_notes": "Provided password reset instructions from knowledge base"
}
```

---

### 6. knowledge_base

**Purpose:** Store product documentation with vector embeddings for semantic search

**Schema:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_embedding ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| title | VARCHAR(500) | NO | Document title |
| content | TEXT | NO | Document content |
| category | VARCHAR(100) | YES | Category (authentication, billing, etc.) |
| embedding | VECTOR(1536) | YES | OpenAI embedding vector |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | Last update timestamp |

**Constraints:**
- `embedding` dimension must be 1536 (text-embedding-3-small)
- `content` should be chunked to <2000 characters for optimal embedding

**Sample Data:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440007",
  "title": "How to Reset Your Password",
  "content": "To reset your password: 1. Go to Settings > Security. 2. Click 'Reset Password'. 3. Enter your email address. 4. Check your email for reset link. 5. Click link and create new password.",
  "category": "authentication",
  "embedding": [0.023, -0.015, 0.042, ...], // 1536 dimensions
  "created_at": "2026-02-15T09:00:00Z",
  "updated_at": "2026-02-15T09:00:00Z"
}
```

---

### 7. channel_configs

**Purpose:** Store channel-specific configuration

**Schema:**
```sql
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB NOT NULL,
    response_template TEXT,
    max_response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_channel_configs_channel ON channel_configs(channel);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| channel | VARCHAR(50) | NO | Channel name (unique) |
| enabled | BOOLEAN | NO | Whether channel is active |
| config | JSONB | NO | Channel-specific configuration |
| response_template | TEXT | YES | Default response template |
| max_response_length | INTEGER | YES | Max response length in characters |
| created_at | TIMESTAMP WITH TIME ZONE | NO | Creation timestamp |

**Constraints:**
- `channel` must be unique
- `channel` must be one of: 'email', 'whatsapp', 'web_form'

**Sample Data:**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440008",
  "channel": "whatsapp",
  "enabled": true,
  "config": {
    "twilio_account_sid": "AC...",
    "twilio_whatsapp_number": "whatsapp:+14155238886",
    "webhook_url": "https://api.techcorp.com/webhooks/whatsapp"
  },
  "response_template": "{message}\n\n📱 Reply for more help or type 'human' for live support.",
  "max_response_length": 1600,
  "created_at": "2026-02-15T08:00:00Z"
}
```

---

### 8. agent_metrics

**Purpose:** Store performance metrics for monitoring and reporting

**Schema:**
```sql
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50),
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_metrics_name ON agent_metrics(metric_name);
CREATE INDEX idx_agent_metrics_channel ON agent_metrics(channel);
CREATE INDEX idx_agent_metrics_recorded ON agent_metrics(recorded_at);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NO | Primary key |
| metric_name | VARCHAR(100) | NO | Metric name |
| metric_value | DECIMAL(10,4) | NO | Metric value |
| channel | VARCHAR(50) | YES | Channel (if channel-specific) |
| dimensions | JSONB | NO | Additional dimensions (tags) |
| recorded_at | TIMESTAMP WITH TIME ZONE | NO | Timestamp |

**Sample Data:**
```json
[
  {
    "id": "cc0e8400-e29b-41d4-a716-446655440009",
    "metric_name": "response_time_ms",
    "metric_value": 1250.0,
    "channel": "email",
    "dimensions": {"customer_id": "550e8400-...", "escalated": false},
    "recorded_at": "2026-02-15T10:30:15Z"
  },
  {
    "id": "cc0e8400-e29b-41d4-a716-44665544000a",
    "metric_name": "escalation_rate",
    "metric_value": 0.22,
    "channel": null,
    "dimensions": {"time_window": "1h"},
    "recorded_at": "2026-02-15T11:00:00Z"
  }
]
```

---

## Data Types & Enums

### Channel Types
```typescript
enum Channel {
  EMAIL = 'email',
  WHATSAPP = 'whatsapp',
  WEB_FORM = 'web_form'
}
```

### Message Direction
```typescript
enum Direction {
  INBOUND = 'inbound',
  OUTBOUND = 'outbound'
}
```

### Message Role
```typescript
enum Role {
  CUSTOMER = 'customer',
  AGENT = 'agent',
  SYSTEM = 'system'
}
```

### Conversation Status
```typescript
enum ConversationStatus {
  ACTIVE = 'active',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated'
}
```

### Ticket Status
```typescript
enum TicketStatus {
  OPEN = 'open',
  PROCESSING = 'processing',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated'
}
```

### Priority Levels
```typescript
enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high'
}
```

### Delivery Status
```typescript
enum DeliveryStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  FAILED = 'failed'
}
```

---

## Relationships

### One-to-Many Relationships
- `customers` → `customer_identifiers` (1:N)
- `customers` → `conversations` (1:N)
- `customers` → `tickets` (1:N)
- `conversations` → `messages` (1:N)
- `conversations` → `tickets` (1:N)

### Referential Integrity
- All foreign keys use `ON DELETE CASCADE`
- Deleting a customer deletes all related data
- Deleting a conversation deletes all messages and tickets

---

## Indexes Strategy

### Primary Indexes (Automatic)
- All `id` columns (primary keys)

### Foreign Key Indexes
- `customer_identifiers.customer_id`
- `conversations.customer_id`
- `messages.conversation_id`
- `tickets.conversation_id`
- `tickets.customer_id`

### Query Optimization Indexes
- `customers.email` - Customer lookup by email
- `customers.phone` - Customer lookup by phone
- `customer_identifiers.identifier_value` - Cross-channel matching
- `conversations.status` - Active conversation queries
- `conversations.started_at` - Time-based queries
- `messages.channel` - Channel-specific queries
- `messages.created_at` - Chronological ordering
- `tickets.status` - Open ticket queries
- `knowledge_base.category` - Category filtering

### Vector Index
- `knowledge_base.embedding` - IVFFlat index for cosine similarity search

---

## Data Retention Policy

### Production Data
- **Messages:** Retain indefinitely (audit trail)
- **Conversations:** Retain indefinitely
- **Tickets:** Retain indefinitely
- **Customers:** Retain until deletion requested (GDPR)
- **Metrics:** Retain 90 days, then aggregate to daily summaries

### Development/Testing Data
- Clear all data between test runs
- Use separate database for testing
- Never use production data in development

---

## Data Migration Strategy

### Initial Migration
1. Create all tables in dependency order
2. Create indexes
3. Seed knowledge base with product documentation
4. Create channel configs

### Future Migrations
1. Use numbered migration files (001, 002, etc.)
2. Always include rollback script
3. Test on staging before production
4. Backup database before migration

---

## Data Validation Rules

### Email Validation
- Format: RFC 5322 compliant
- Normalize: Lowercase, trim whitespace
- Example: `john.doe@example.com`

### Phone Validation
- Format: E.164 international format
- Normalize: Remove spaces, dashes, parentheses
- Example: `+15551234567`

### Content Validation
- Max length: 10,000 characters per message
- Sanitize: Remove SQL injection attempts
- Escape: HTML entities for display

### Sentiment Score Validation
- Range: 0.00 to 1.00
- Precision: 2 decimal places
- Example: `0.85`

---

## Performance Considerations

### Query Optimization
- Use prepared statements for all queries
- Limit result sets (default: 20 messages per conversation)
- Use connection pooling (10-20 connections)
- Cache frequently accessed data (Redis future enhancement)

### Vector Search Optimization
- Pre-compute embeddings for knowledge base
- Use IVFFlat index for fast similarity search
- Limit results to top 5 for performance

### Write Optimization
- Batch insert metrics (every 10 seconds)
- Use async writes for non-critical data
- Avoid transactions for independent operations

---

**Version:** 1.0.0 | **Created:** 2026-02-15 | **Last Updated:** 2026-02-15

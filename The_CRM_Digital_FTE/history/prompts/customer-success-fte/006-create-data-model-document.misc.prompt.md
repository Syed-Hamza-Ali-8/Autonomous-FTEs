---
id: 006
title: Create Data Model Document
stage: misc
date: 2026-02-15
surface: agent
model: claude-sonnet-4-5
feature: customer-success-fte
branch: main
user: developer
command: data-model create
labels: ["database", "schema", "data-model"]
links:
  spec: specs/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/data-model.md
tests: []
---

## Prompt

Create specs/data-model.md with complete database schema and data model for the Customer Success FTE project.

## Context

User requested creation of comprehensive data model document. The document needs to define the complete database schema, entity relationships, data types, constraints, and validation rules for the PostgreSQL database that serves as the CRM system.

## Response

Created comprehensive data model document (specs/data-model.md) with the following sections:

**Entity Relationship Diagram:**
- Visual representation of all 8 tables and their relationships
- Clear foreign key relationships shown
- One-to-many relationships documented

**Table Definitions (8 tables):**

1. **customers** - Unified customer records across all channels
   - Columns: id (UUID PK), email (unique), phone, name, created_at, metadata (JSONB)
   - Indexes: email, phone
   - Sample data provided

2. **customer_identifiers** - Multiple identifiers per customer for cross-channel matching
   - Columns: id (UUID PK), customer_id (FK), identifier_type, identifier_value, verified, created_at
   - Unique constraint: (identifier_type, identifier_value)
   - Indexes: identifier_value, customer_id
   - Sample data showing email and WhatsApp identifiers

3. **conversations** - Conversation threads across channels
   - Columns: id (UUID PK), customer_id (FK), initial_channel, started_at, ended_at, status, sentiment_score, resolution_type, escalated_to, metadata (JSONB)
   - Indexes: customer_id, status, initial_channel, started_at
   - Sample data with cross-channel metadata

4. **messages** - All messages with channel metadata
   - Columns: id (UUID PK), conversation_id (FK), channel, direction, role, content, created_at, tokens_used, latency_ms, tool_calls (JSONB), channel_message_id, delivery_status
   - Indexes: conversation_id, channel, created_at, channel_message_id
   - Sample data showing inbound and outbound messages

5. **tickets** - Support tickets linked to conversations
   - Columns: id (UUID PK), conversation_id (FK), customer_id (FK), source_channel, category, priority, status, created_at, resolved_at, resolution_notes
   - Indexes: conversation_id, customer_id, status, source_channel, created_at
   - Sample data with resolution

6. **knowledge_base** - Product documentation with vector embeddings
   - Columns: id (UUID PK), title, content, category, embedding (VECTOR(1536)), created_at, updated_at
   - Indexes: category, embedding (IVFFlat for cosine similarity)
   - Sample data with embedding vector

7. **channel_configs** - Channel-specific configuration
   - Columns: id (UUID PK), channel (unique), enabled, config (JSONB), response_template, max_response_length, created_at
   - Index: channel
   - Sample data for WhatsApp configuration

8. **agent_metrics** - Performance metrics for monitoring
   - Columns: id (UUID PK), metric_name, metric_value, channel, dimensions (JSONB), recorded_at
   - Indexes: metric_name, channel, recorded_at
   - Sample data showing response time and escalation rate metrics

**Data Types & Enums:**
- Channel: email, whatsapp, web_form
- Direction: inbound, outbound
- Role: customer, agent, system
- ConversationStatus: active, resolved, escalated
- TicketStatus: open, processing, resolved, escalated
- Priority: low, medium, high
- DeliveryStatus: pending, sent, delivered, failed

**Relationships:**
- One-to-many: customers → customer_identifiers, customers → conversations, customers → tickets, conversations → messages, conversations → tickets
- Referential integrity: All foreign keys use ON DELETE CASCADE

**Indexes Strategy:**
- Primary indexes on all id columns
- Foreign key indexes for joins
- Query optimization indexes for common queries
- Vector index (IVFFlat) for semantic search

**Data Retention Policy:**
- Production: Messages, conversations, tickets, customers retained indefinitely
- Metrics: 90 days, then aggregate to daily summaries
- Development: Clear between test runs

**Data Validation Rules:**
- Email: RFC 5322 compliant, lowercase, trim whitespace
- Phone: E.164 format, remove spaces/dashes/parentheses
- Content: Max 10,000 chars, sanitize SQL injection, escape HTML
- Sentiment: 0.00 to 1.00 range, 2 decimal places

**Performance Considerations:**
- Query optimization: Prepared statements, limit results, connection pooling
- Vector search: Pre-compute embeddings, IVFFlat index, limit to top 5
- Write optimization: Batch insert metrics, async writes, avoid unnecessary transactions

## Outcome

Complete data model document created with detailed schema definitions, relationships, constraints, validation rules, and performance considerations. Document serves as authoritative reference for database design and implementation.

## Evaluation

- ✅ All 8 tables fully defined
- ✅ Entity relationship diagram provided
- ✅ Sample data for each table
- ✅ All enums and data types documented
- ✅ Relationships clearly mapped
- ✅ Indexes strategy defined
- ✅ Data retention policy specified
- ✅ Validation rules comprehensive
- ✅ Performance considerations included

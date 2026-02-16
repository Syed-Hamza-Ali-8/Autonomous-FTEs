# Customer Success FTE - Implementation Plan

**Feature:** Customer Success Digital FTE
**Version:** 1.0.0
**Status:** Draft
**Created:** 2026-02-15
**Last Updated:** 2026-02-15

---

## Executive Summary

This plan outlines the technical architecture and implementation strategy for building a production-ready 24/7 AI customer support agent across three channels (Email, WhatsApp, Web Form).

**Implementation Approach:** Two-stage evolution following the Agent Maturity Model
- **Stage 1 (Hours 1-16):** Incubation with Claude Code - Explore, prototype, discover requirements
- **Stage 2 (Hours 17-40):** Specialization with OpenAI SDK - Build production-grade infrastructure
- **Stage 3 (Hours 41-48):** Integration & Testing - Validate production readiness

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-CHANNEL INTAKE LAYER                    │
│                                                                  │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │  Gmail   │      │ WhatsApp │      │ Web Form │              │
│  │  Webhook │      │  Webhook │      │   API    │              │
│  └────┬─────┘      └────┬─────┘      └────┬─────┘              │
│       │                 │                  │                    │
│       └─────────────────┼──────────────────┘                    │
│                         ▼                                        │
│                  ┌─────────────┐                                │
│                  │    Kafka    │                                │
│                  │   Topics    │                                │
│                  └──────┬──────┘                                │
│                         │                                        │
├─────────────────────────┼────────────────────────────────────────┤
│                    PROCESSING LAYER                              │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │  Message Processor   │                           │
│              │     (Workers)        │                           │
│              └──────────┬───────────┘                           │
│                         │                                        │
│                         ▼                                        │
│              ┌──────────────────────┐                           │
│              │  Customer Success    │                           │
│              │    Agent (OpenAI)    │                           │
│              └──────────┬───────────┘                           │
│                         │                                        │
│         ┌───────────────┼───────────────┐                       │
│         ▼               ▼               ▼                        │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│   │PostgreSQL│   │  OpenAI  │   │  Kafka   │                   │
│   │   (CRM)  │   │   API    │   │ (Events) │                   │
│   └──────────┘   └──────────┘   └──────────┘                   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    RESPONSE LAYER                                │
│                                                                  │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │  Gmail   │      │ Twilio   │      │  Email   │              │
│  │   API    │      │   API    │      │  Notify  │              │
│  └──────────┘      └──────────┘      └──────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Channel Intake Layer
**Purpose:** Receive messages from all three channels and normalize them

**Components:**
- **Gmail Webhook Handler** (`src/channels/gmail_handler.py`)
  - Receives Pub/Sub notifications
  - Fetches email via Gmail API
  - Extracts: sender email, subject, body, thread_id
  - Publishes to Kafka: `fte.tickets.incoming`

- **WhatsApp Webhook Handler** (`src/channels/whatsapp_handler.py`)
  - Receives Twilio webhook POST
  - Validates signature
  - Extracts: phone, message body, profile name
  - Publishes to Kafka: `fte.tickets.incoming`

- **Web Form Handler** (`src/channels/web_form_handler.py`)
  - FastAPI endpoint: POST /support/submit
  - Validates form data with Pydantic
  - Extracts: name, email, subject, category, message
  - Publishes to Kafka: `fte.tickets.incoming`

**Design Decisions:**
- **Unified Queue:** All channels publish to same Kafka topic for consistent processing
- **Async Processing:** Webhooks return immediately, processing happens in background
- **Channel Metadata:** Every message includes `channel` field for formatting responses

#### 2. Event Streaming Layer (Kafka)
**Purpose:** Decouple intake from processing, enable scalability

**Topics:**
```
fte.tickets.incoming     - All incoming messages (unified)
fte.escalations          - Escalation events for human agents
fte.metrics              - Performance metrics
fte.dlq                  - Dead letter queue for failed messages
```

**Design Decisions:**
- **Single Partition:** Start with 1 partition per topic (can increase later)
- **Retention:** 7 days for audit and replay
- **Consumer Groups:** `fte-message-processor` group for workers
- **At-Least-Once:** Kafka guarantees, idempotent processing in workers

#### 3. Processing Layer
**Purpose:** Process messages with AI agent and manage state

**Components:**
- **Message Processor Worker** (`src/workers/message_processor.py`)
  - Consumes from `fte.tickets.incoming`
  - Resolves customer (create or lookup)
  - Creates/retrieves conversation
  - Loads conversation history
  - Runs OpenAI agent
  - Stores response
  - Publishes metrics

- **Customer Success Agent** (`src/agent/customer_success_agent.py`)
  - OpenAI Agents SDK implementation
  - Model: gpt-4o
  - Tools: search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response
  - Channel-aware system prompt
  - Conversation memory management

**Design Decisions:**
- **Stateless Workers:** All state in PostgreSQL, workers can scale horizontally
- **Tool-Based Architecture:** Agent uses function tools for all actions
- **Channel Context:** Agent receives channel in context, formats responses accordingly
- **Error Handling:** Try/catch on all tools, graceful fallbacks, DLQ for failures

#### 4. Data Layer (PostgreSQL)
**Purpose:** Store all customer data, conversations, tickets, knowledge base

**Schema Design:**
```sql
customers
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── phone (VARCHAR)
├── name (VARCHAR)
├── created_at (TIMESTAMP)
└── metadata (JSONB)

customer_identifiers
├── id (UUID, PK)
├── customer_id (UUID, FK -> customers)
├── identifier_type (VARCHAR) -- 'email', 'phone', 'whatsapp'
├── identifier_value (VARCHAR)
├── verified (BOOLEAN)
└── UNIQUE(identifier_type, identifier_value)

conversations
├── id (UUID, PK)
├── customer_id (UUID, FK -> customers)
├── initial_channel (VARCHAR) -- 'email', 'whatsapp', 'web_form'
├── started_at (TIMESTAMP)
├── ended_at (TIMESTAMP)
├── status (VARCHAR) -- 'active', 'resolved', 'escalated'
├── sentiment_score (DECIMAL)
└── metadata (JSONB)

messages
├── id (UUID, PK)
├── conversation_id (UUID, FK -> conversations)
├── channel (VARCHAR) -- 'email', 'whatsapp', 'web_form'
├── direction (VARCHAR) -- 'inbound', 'outbound'
├── role (VARCHAR) -- 'customer', 'agent', 'system'
├── content (TEXT)
├── created_at (TIMESTAMP)
├── tokens_used (INTEGER)
├── latency_ms (INTEGER)
├── tool_calls (JSONB)
└── channel_message_id (VARCHAR) -- External ID

tickets
├── id (UUID, PK)
├── conversation_id (UUID, FK -> conversations)
├── customer_id (UUID, FK -> customers)
├── source_channel (VARCHAR)
├── category (VARCHAR)
├── priority (VARCHAR)
├── status (VARCHAR) -- 'open', 'processing', 'resolved', 'escalated'
├── created_at (TIMESTAMP)
├── resolved_at (TIMESTAMP)
└── resolution_notes (TEXT)

knowledge_base
├── id (UUID, PK)
├── title (VARCHAR)
├── content (TEXT)
├── category (VARCHAR)
├── embedding (VECTOR(1536)) -- pgvector
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

**Design Decisions:**
- **UUID Primary Keys:** Distributed-friendly, no collisions
- **JSONB Metadata:** Flexible storage for channel-specific data
- **pgvector Extension:** Semantic search with cosine similarity
- **Indexes:** On email, phone, conversation_id, customer_id, channel
- **Normalization:** 3NF for data integrity

#### 5. API Layer (FastAPI)
**Purpose:** Expose endpoints for webhooks and queries

**Endpoints:**
```
POST   /webhooks/gmail              - Gmail Pub/Sub webhook
POST   /webhooks/whatsapp           - Twilio WhatsApp webhook
POST   /webhooks/whatsapp/status    - Twilio status callback
POST   /support/submit              - Web form submission
GET    /support/ticket/{ticket_id}  - Ticket status
GET    /customers/lookup            - Customer lookup by email/phone
GET    /metrics/channels            - Channel-specific metrics
GET    /health                      - Health check
```

**Design Decisions:**
- **Async FastAPI:** All endpoints use async/await for performance
- **Pydantic Validation:** All inputs validated with Pydantic models
- **Background Tasks:** Webhooks use BackgroundTasks for async processing
- **CORS:** Enabled for web form (configure origins in production)
- **Rate Limiting:** TODO - Add rate limiting middleware

#### 6. Kubernetes Deployment
**Purpose:** Production-grade orchestration and scaling

**Resources:**
```
Namespace: customer-success-fte

ConfigMap: fte-config
- Environment variables (non-sensitive)

Secret: fte-secrets
- OPENAI_API_KEY
- POSTGRES_PASSWORD
- GMAIL_CREDENTIALS
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN

Deployment: fte-api
- Replicas: 3 (min), 20 (max)
- HPA: CPU > 70%
- Image: customer-success-fte:latest
- Command: uvicorn api.main:app
- Ports: 8000
- Resources: 512Mi/250m (request), 1Gi/500m (limit)
- Probes: liveness (/health), readiness (/health)

Deployment: fte-message-processor
- Replicas: 3 (min), 30 (max)
- HPA: CPU > 70%
- Image: customer-success-fte:latest
- Command: python workers/message_processor.py
- Resources: 512Mi/250m (request), 1Gi/500m (limit)

Service: customer-success-fte
- Type: ClusterIP
- Port: 80 -> 8000

Ingress: customer-success-fte
- Host: support-api.yourdomain.com
- TLS: cert-manager (Let's Encrypt)
- Backend: customer-success-fte:80
```

**Design Decisions:**
- **Horizontal Scaling:** Both API and workers scale independently
- **Resource Limits:** Prevent resource exhaustion
- **Health Checks:** Automatic restart on failure
- **TLS Termination:** At ingress level
- **Secrets Management:** Kubernetes Secrets (consider Vault for production)

---

## Implementation Phases

### Phase 1: Incubation (Hours 1-16)

**Objective:** Explore problem space, build prototype, discover requirements

#### Hour 1-3: Setup & Exploration
**Tasks:**
1. Create project structure
2. Set up development dossier (context files)
3. Prompt Claude Code to analyze sample tickets
4. Identify patterns across channels

**Deliverables:**
- `context/company-profile.md`
- `context/product-docs.md`
- `context/sample-tickets.json` (50+ tickets)
- `context/escalation-rules.md`
- `context/brand-voice.md`
- `specs/discovery-log.md` (initial)

#### Hour 4-8: Prototype Core Loop
**Tasks:**
1. Build basic message processing loop
2. Implement knowledge base search (simple)
3. Add channel-aware response formatting
4. Test with sample tickets from all channels

**Deliverables:**
- `prototype/agent.py` - Basic agent logic
- `prototype/knowledge_search.py` - Simple search
- `prototype/formatters.py` - Channel formatters
- Test results on 20+ tickets

#### Hour 9-12: Add Memory & State
**Tasks:**
1. Implement conversation memory (in-memory)
2. Add customer identification logic
3. Track sentiment across messages
4. Implement escalation decision logic

**Deliverables:**
- `prototype/memory.py` - Conversation state
- `prototype/customer.py` - Customer matching
- `prototype/sentiment.py` - Sentiment analysis
- Updated discovery log with edge cases

#### Hour 13-16: Build MCP Server & Crystallize
**Tasks:**
1. Create MCP server with tools
2. Define agent skills manifest
3. Document all edge cases found
4. Write crystallized specification

**Deliverables:**
- `prototype/mcp_server.py` - MCP implementation
- `specs/agent-skills.md` - Skills manifest
- `specs/customer-success-fte-spec.md` - Final spec
- `specs/discovery-log.md` - Complete

**Gate 1 Criteria:**
- [ ] Prototype handles all 3 channels
- [ ] 60+ edge cases documented
- [ ] MCP server with 5+ tools working
- [ ] Specification crystallized

---

### Phase 2: Specialization (Hours 17-40)

**Objective:** Build production-grade infrastructure

#### Hour 17-18: Transition Planning
**Tasks:**
1. Create `specs/transition-checklist.md`
2. Extract working prompts from incubation
3. Map prototype code to production components
4. Create production folder structure

**Deliverables:**
- Production folder structure
- Transition checklist
- Extracted prompts in `src/agent/prompts.py`

#### Hour 19-22: Database Setup
**Tasks:**
1. Write `database/schema.sql`
2. Create migration scripts
3. Write database access functions
4. Seed knowledge base with sample data

**Deliverables:**
- `database/schema.sql`
- `database/migrations/001_initial.sql`
- `database/queries.py`
- `database/seed_knowledge.py`

#### Hour 23-27: Channel Integrations
**Tasks:**
1. Implement Gmail handler with Pub/Sub
2. Implement WhatsApp handler with Twilio
3. Build Web Support Form (React/Next.js)
4. Test each channel independently

**Deliverables:**
- `src/channels/gmail_handler.py`
- `src/channels/whatsapp_handler.py`
- `src/channels/web_form_handler.py`
- `src/web-form/SupportForm.jsx`

#### Hour 28-32: OpenAI Agent Implementation
**Tasks:**
1. Convert MCP tools to @function_tool
2. Implement agent with OpenAI SDK
3. Add channel-aware formatting
4. Write transition tests

**Deliverables:**
- `src/agent/customer_success_agent.py`
- `src/agent/tools.py`
- `src/agent/formatters.py`
- `tests/test_transition.py`

#### Hour 33-36: Kafka & Workers
**Tasks:**
1. Set up Kafka topics
2. Implement message processor worker
3. Add error handling and DLQ
4. Test end-to-end flow

**Deliverables:**
- `src/kafka_client.py`
- `src/workers/message_processor.py`
- `tests/test_e2e.py`

#### Hour 37-40: Kubernetes Deployment
**Tasks:**
1. Write Kubernetes manifests
2. Create Dockerfile
3. Build and push image
4. Deploy to cluster
5. Verify health checks

**Deliverables:**
- `k8s/*.yaml` (all manifests)
- `Dockerfile`
- `docker-compose.yml` (local dev)
- Deployment documentation

**Gate 2 Criteria:**
- [ ] All transition tests passing
- [ ] All 3 channels working
- [ ] Web form built and tested
- [ ] Kubernetes deployment successful
- [ ] Health checks passing

---

### Phase 3: Integration & Testing (Hours 41-48)

**Objective:** Validate production readiness

#### Hour 41-44: E2E Testing
**Tasks:**
1. Write multi-channel E2E tests
2. Test cross-channel continuity
3. Test escalation scenarios
4. Fix any issues found

**Deliverables:**
- `tests/test_multichannel_e2e.py`
- All tests passing

#### Hour 45-46: Load Testing
**Tasks:**
1. Write Locust load test
2. Run load test (100 web + 50 email + 50 WhatsApp)
3. Analyze results
4. Optimize bottlenecks

**Deliverables:**
- `tests/load_test.py`
- Load test report

#### Hour 47-48: 24-Hour Test & Documentation
**Tasks:**
1. Start 24-hour continuous operation test
2. Monitor metrics
3. Write deployment documentation
4. Write operations runbook

**Deliverables:**
- 24-hour test results
- `docs/deployment.md`
- `docs/operations-runbook.md`
- `docs/api-documentation.md`

**Gate 3 Criteria:**
- [ ] 24-hour test passed
- [ ] Uptime >99.9%
- [ ] P95 latency <3s
- [ ] Escalation rate <25%
- [ ] Documentation complete

---

## Key Design Decisions

### Decision 1: Unified Kafka Queue vs. Channel-Specific Queues
**Options Considered:**
- A) Single queue `fte.tickets.incoming` for all channels
- B) Separate queues per channel: `fte.email.incoming`, `fte.whatsapp.incoming`, `fte.webform.incoming`

**Decision:** Option A - Unified queue

**Rationale:**
- Simpler architecture (one consumer group)
- Easier to maintain cross-channel continuity
- Channel metadata included in message
- Can add channel-specific processing later if needed

**Trade-offs:**
- Cannot scale channels independently
- Cannot prioritize one channel over another
- Acceptable for initial implementation

### Decision 2: PostgreSQL as CRM vs. External CRM Integration
**Options Considered:**
- A) Build custom CRM in PostgreSQL
- B) Integrate with Salesforce/HubSpot

**Decision:** Option A - PostgreSQL CRM

**Rationale:**
- Hackathon scope - no external CRM required
- Full control over schema and queries
- Faster development (no API integration)
- Teaches fundamentals of customer data management
- Can add CRM sync later if needed

**Trade-offs:**
- No enterprise CRM features (workflows, reporting)
- Manual data management
- Acceptable for hackathon, may need CRM sync for production

### Decision 3: Synchronous vs. Asynchronous Agent Execution
**Options Considered:**
- A) Synchronous: Webhook waits for agent response
- B) Asynchronous: Webhook returns immediately, agent processes in background

**Decision:** Option B - Asynchronous

**Rationale:**
- Webhooks have timeout limits (30 seconds)
- Agent processing may take >30 seconds
- Better scalability (workers can scale independently)
- Kafka provides reliable message delivery

**Trade-offs:**
- More complex architecture
- Requires Kafka infrastructure
- Worth it for production-grade system

### Decision 4: OpenAI Agents SDK vs. LangChain
**Options Considered:**
- A) OpenAI Agents SDK
- B) LangChain
- C) Custom implementation

**Decision:** Option A - OpenAI Agents SDK

**Rationale:**
- Hackathon requirement (must use OpenAI SDK)
- Native integration with OpenAI models
- Simpler than LangChain for this use case
- Better performance (fewer abstractions)

**Trade-offs:**
- Locked into OpenAI ecosystem
- Less flexibility than LangChain
- Acceptable for this project

### Decision 5: Kubernetes vs. Serverless
**Options Considered:**
- A) Kubernetes deployment
- B) AWS Lambda / Cloud Functions
- C) Docker Compose on VMs

**Decision:** Option A - Kubernetes

**Rationale:**
- Hackathon requirement (must use Kubernetes)
- Better for long-running workers (Kafka consumers)
- Horizontal scaling with HPA
- Production-grade orchestration

**Trade-offs:**
- More complex than serverless
- Higher operational overhead
- Worth it for learning and production readiness

---

## Risk Mitigation Strategies

### Risk: OpenAI API Rate Limits
**Mitigation:**
- Implement exponential backoff retry logic
- Monitor rate limit headers
- Queue messages in Kafka during rate limit
- Alert on repeated rate limit errors

### Risk: Kafka Message Loss
**Mitigation:**
- Use at-least-once delivery semantics
- Implement idempotent message processing
- Store message_id in database to detect duplicates
- Monitor consumer lag

### Risk: Database Connection Pool Exhaustion
**Mitigation:**
- Use asyncpg connection pool with limits
- Set max_connections in PostgreSQL config
- Monitor active connections
- Implement connection timeout

### Risk: Cross-Channel Customer Matching Failures
**Mitigation:**
- Use case-insensitive email matching
- Normalize phone numbers (remove spaces, dashes)
- Log matching failures for analysis
- Provide manual merge tool for support team

### Risk: Escalation Rate Too High
**Mitigation:**
- Continuously improve knowledge base
- Analyze escalation reasons weekly
- Adjust escalation thresholds based on data
- Add more training examples to agent

---

## Performance Optimization Strategy

### Database Optimization
1. **Indexes:** Create indexes on frequently queried columns
2. **Connection Pooling:** Use asyncpg pool with 10-20 connections
3. **Query Optimization:** Use EXPLAIN ANALYZE to optimize slow queries
4. **Caching:** Cache knowledge base embeddings in Redis (future)

### Agent Optimization
1. **Prompt Caching:** Use OpenAI prompt caching for system prompt
2. **Parallel Tool Calls:** Enable parallel function calling
3. **Streaming:** Use streaming responses for faster perceived latency
4. **Context Window:** Limit conversation history to last 20 messages

### API Optimization
1. **Async Endpoints:** All endpoints use async/await
2. **Background Tasks:** Webhooks use BackgroundTasks
3. **Connection Pooling:** Reuse HTTP connections to external APIs
4. **Compression:** Enable gzip compression on responses

### Kubernetes Optimization
1. **Resource Limits:** Set appropriate CPU/memory limits
2. **HPA:** Auto-scale based on CPU >70%
3. **Pod Disruption Budget:** Ensure minimum replicas during updates
4. **Readiness Probes:** Prevent traffic to unhealthy pods

---

## Monitoring & Observability

### Metrics to Track
1. **Channel Metrics:**
   - Messages received per channel
   - Response time per channel
   - Escalation rate per channel
   - Customer satisfaction per channel

2. **Agent Metrics:**
   - Tool call success rate
   - Knowledge base search accuracy
   - Sentiment scores distribution
   - Escalation reasons breakdown

3. **Infrastructure Metrics:**
   - API endpoint latency (P50, P95, P99)
   - Database query time
   - Kafka consumer lag
   - Pod CPU/memory usage

4. **Business Metrics:**
   - Total conversations
   - Resolution rate
   - Average conversation length
   - Cost per conversation

### Alerting Rules
1. **Critical:**
   - API health check failing
   - Database connection failures
   - Kafka consumer lag >1000 messages
   - Escalation rate >50%

2. **Warning:**
   - P95 latency >5 seconds
   - Escalation rate >30%
   - OpenAI API errors >5%
   - Pod restarts >3 in 10 minutes

### Logging Strategy
1. **Structured Logging:** JSON format with correlation IDs
2. **Log Levels:** DEBUG (dev), INFO (prod), ERROR (always)
3. **PII Redaction:** Mask email addresses and phone numbers
4. **Retention:** 30 days in production

---

## Testing Strategy

### Unit Tests
- All tool functions
- Channel handlers
- Database queries
- Response formatters
- Target: >80% code coverage

### Integration Tests
- Channel integrations (Gmail, Twilio)
- Database operations
- Kafka producer/consumer
- Agent tool execution

### E2E Tests
- Full flow: webhook -> agent -> response
- Cross-channel continuity
- Escalation scenarios
- Error handling

### Load Tests
- 100 web form submissions in 1 hour
- 50 email messages in 1 hour
- 50 WhatsApp messages in 1 hour
- Concurrent: 100 simultaneous conversations

### 24-Hour Test
- Continuous operation for 24 hours
- Random pod kills every 2 hours
- Metrics validation:
  - Uptime >99.9%
  - P95 latency <3s
  - Escalation rate <25%
  - Zero message loss

---

## Deployment Strategy

### Local Development
1. Use docker-compose for dependencies (PostgreSQL, Kafka)
2. Run API and workers locally with hot reload
3. Use ngrok for webhook testing
4. Use Twilio WhatsApp Sandbox

### Staging Environment
1. Deploy to minikube or cloud Kubernetes
2. Use test Gmail account and Twilio sandbox
3. Run E2E tests and load tests
4. Validate metrics and alerting

### Production Deployment
1. Use managed Kubernetes (GKE, EKS, AKS)
2. Use managed PostgreSQL (Cloud SQL, RDS)
3. Use Confluent Cloud for Kafka
4. Set up monitoring and alerting
5. Configure TLS with Let's Encrypt
6. Run 24-hour test before launch

### Rollback Strategy
1. Keep previous deployment version
2. Use Kubernetes rollout undo if issues
3. Monitor metrics for 1 hour after deployment
4. Have runbook for common issues

---

## Success Metrics

### Technical Metrics
- [ ] Response time: P95 <3 seconds
- [ ] Uptime: >99.9%
- [ ] Escalation rate: <25%
- [ ] Cross-channel identification: >95%
- [ ] Message loss: 0%

### Business Metrics
- [ ] Cost: <$1,000/year operational
- [ ] Customer satisfaction: >85%
- [ ] Resolution rate: >70% without escalation
- [ ] 24/7 availability: 100%

### Quality Metrics
- [ ] Code coverage: >80%
- [ ] All tests passing: 100%
- [ ] Documentation complete: 100%
- [ ] Zero critical bugs in production

---

## Appendix

### Technology Stack Summary
- **Language:** Python 3.11+
- **Agent:** OpenAI Agents SDK (gpt-4o)
- **API:** FastAPI with async
- **Database:** PostgreSQL 16 + pgvector
- **Streaming:** Apache Kafka
- **Orchestration:** Kubernetes
- **Frontend:** React/Next.js (web form only)
- **Testing:** pytest, httpx, Locust

### External Dependencies
- OpenAI API (~$0.01/conversation)
- Gmail API (free within limits)
- Twilio WhatsApp API ($0.005/message)
- Confluent Cloud Kafka (~$100/month)
- Managed PostgreSQL (~$50/month)

### Timeline Summary
- Phase 1 (Incubation): 16 hours
- Phase 2 (Specialization): 24 hours
- Phase 3 (Integration): 8 hours
- **Total:** 48 hours

---

**Version:** 1.0.0 | **Created:** 2026-02-15 | **Last Updated:** 2026-02-15

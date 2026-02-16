# Customer Success FTE Constitution
<!-- CRM Digital FTE Factory - Hackathon 5 -->

## Core Principles

### I. Multi-Channel First
Every feature must support all three communication channels from the start:
- **Email (Gmail)**: Formal, detailed responses (max 500 words) with proper greeting/signature
- **WhatsApp (Twilio)**: Concise, conversational responses (prefer 160 chars, max 1600)
- **Web Form**: Semi-formal, helpful responses (max 300 words)

Channel-specific formatting is mandatory. Cross-channel customer identification must be maintained at >95% accuracy.

### II. Agent Maturity Model (NON-NEGOTIABLE)
Development follows the two-stage evolution:
- **Stage 1 - Incubation**: Use Claude Code for exploration, prototyping, and requirement discovery
- **Stage 2 - Specialization**: Transform to production-grade Custom Agent using OpenAI Agents SDK

General Agents (Claude Code) build Custom Agents (OpenAI SDK). This progression is the core learning objective.

### III. 24/7 Autonomous Operation
The FTE must operate continuously without human intervention:
- No single points of failure
- Graceful degradation under load
- Automatic recovery from pod failures
- Health checks and monitoring required
- Target uptime: >99.9%

### IV. Cross-Channel Continuity
Customer context must persist across all channels:
- Unified customer identification (email, phone, WhatsApp ID)
- Conversation history accessible regardless of current channel
- Acknowledge previous interactions: "I see you contacted us previously about X..."
- Database schema must support channel tracking on all entities

### V. Production-Ready Infrastructure
All components must be production-grade from deployment:
- PostgreSQL with pgvector for semantic search (this IS the CRM)
- Kafka for event streaming with channel-specific topics
- Kubernetes deployment with HPA (3-20 API pods, 3-30 workers)
- Docker containers with health checks
- Structured logging and metrics collection

### VI. Intelligent Escalation
Agent must know its limits and escalate appropriately:
- **Immediate escalation**: Pricing, refunds, legal mentions
- **Sentiment-based**: Negative sentiment (<0.3), profanity, aggressive language
- **Capability-based**: Cannot find information after 2 search attempts
- **Explicit request**: Customer asks for human help
- Target escalation rate: <25%

### VII. Test-Driven Quality
Testing is mandatory at all stages:
- Edge case documentation during incubation (20+ per channel)
- Transition tests verify prototype → production parity
- Multi-channel E2E test suite required
- Load testing with Locust (100+ web, 50+ email, 50+ WhatsApp)
- 24-hour continuous operation test before completion

## Performance Standards

### Response Quality
- **Accuracy**: >85% on test dataset
- **Latency**: P95 <3 seconds processing, <30 seconds delivery
- **Escalation Rate**: <25% of conversations
- **Customer Identification**: >95% accuracy across channels
- **Message Loss**: Zero tolerance

### Channel-Specific Requirements
| Channel | Max Length | Style | Required Elements |
|---------|-----------|-------|-------------------|
| Email | 500 words | Formal | Greeting, signature, ticket reference |
| WhatsApp | 1600 chars | Conversational | Concise, emoji acceptable, help prompt |
| Web Form | 300 words | Semi-formal | Clear next steps, portal link |

### Infrastructure Targets
- **Cost**: <$1,000/year operational cost (vs $75,000 human FTE)
- **Scaling**: Auto-scale based on 70% CPU utilization
- **Recovery**: <30 seconds pod restart time
- **Monitoring**: Channel-specific metrics dashboard required

## Technology Stack (MANDATORY)

### Core Components
- **Agent Framework**: OpenAI Agents SDK (gpt-4o model)
- **API Layer**: FastAPI with async support
- **Database**: PostgreSQL 16 with pgvector extension
- **Event Streaming**: Apache Kafka (Confluent Cloud acceptable)
- **Orchestration**: Kubernetes (minikube for local, any cloud for production)
- **Containerization**: Docker

### Channel Integrations
- **Email**: Gmail API with Pub/Sub push notifications
- **WhatsApp**: Twilio WhatsApp API with webhook validation
- **Web Form**: React/Next.js component (REQUIRED BUILD)

### Development Tools
- **Incubation**: Claude Code (General Agent)
- **Code Editor**: VS Code or equivalent
- **Testing**: pytest, httpx, Locust
- **Version Control**: Git

## Development Workflow

### Phase 1: Incubation (Hours 1-16)
**Objective**: Explore and prototype with Claude Code

**Required Deliverables**:
- Working prototype handling multi-channel queries
- `specs/discovery-log.md` documenting requirements found
- `specs/customer-success-fte-spec.md` crystallized specification
- MCP server with 5+ channel-aware tools
- Agent skills manifest
- Channel-specific response templates
- Test dataset (20+ edge cases per channel)

**Success Criteria**:
- Prototype demonstrates all three channels
- Edge cases documented with handling strategies
- Escalation rules finalized
- Performance baseline measured

### Phase 2: Specialization (Hours 17-40)
**Objective**: Build production-grade Custom Agent

**Required Deliverables**:
- PostgreSQL schema with multi-channel support
- OpenAI Agents SDK implementation with @function_tool decorators
- FastAPI service with all channel endpoints
- Gmail integration (webhook handler + send)
- WhatsApp/Twilio integration (webhook handler + send)
- **Web Support Form (React/Next.js) - REQUIRED**
- Kafka event streaming with channel topics
- Kubernetes manifests (namespace, configmap, secrets, deployments, services, ingress, HPA)
- Monitoring configuration

**Success Criteria**:
- All transition tests passing
- Channel handlers validate webhooks
- Database supports cross-channel queries
- Kubernetes deployment successful
- Health checks passing

### Phase 3: Integration & Testing (Hours 41-48)
**Objective**: Validate production readiness

**Required Deliverables**:
- Multi-channel E2E test suite (all passing)
- Load test results (Locust)
- 24-hour continuous operation test results
- Deployment documentation
- Operations runbook

**Success Criteria**:
- 24-hour test passes all metrics
- Load test shows linear scaling
- Documentation complete
- Runbook covers incident response

## Quality Gates

### Gate 1: Incubation Complete
- [ ] Prototype handles queries from all 3 channels
- [ ] Discovery log shows iterative exploration
- [ ] MCP server tools tested and working
- [ ] Edge cases documented (minimum 10 per channel)
- [ ] Specification crystallized

**Cannot proceed to Phase 2 without passing Gate 1**

### Gate 2: Specialization Complete
- [ ] All transition tests passing
- [ ] Database schema deployed
- [ ] All three channel integrations working
- [ ] Web Support Form built and tested
- [ ] Kubernetes deployment successful
- [ ] Kafka topics created and tested

**Cannot proceed to Phase 3 without passing Gate 2**

### Gate 3: Production Ready
- [ ] Multi-channel E2E tests passing
- [ ] Load test results meet targets
- [ ] 24-hour continuous operation test passed
- [ ] Documentation complete
- [ ] Metrics dashboard operational

**Project incomplete without passing Gate 3**

## Security & Compliance

### Data Protection
- No PII in logs or error messages
- Customer data encrypted at rest (PostgreSQL)
- API keys and secrets in Kubernetes Secrets (never in code)
- Webhook signature validation required (Gmail, Twilio)

### Guardrails (NEVER Violate)
- NEVER discuss competitor products
- NEVER promise features not in documentation
- NEVER process refunds or pricing changes
- NEVER share internal processes or system details
- NEVER respond without using send_response tool
- NEVER exceed channel response limits

### Error Handling
- All tool functions must have try/catch with graceful fallbacks
- Failed messages go to Dead Letter Queue (DLQ)
- Apologetic response sent to customer on processing errors
- Human escalation triggered for repeated failures

## Governance

### Constitution Authority
This constitution supersedes all other development practices. Any deviation requires:
1. Documented justification
2. Risk assessment
3. Approval from project lead
4. Amendment to this document

### Compliance Verification
Every deliverable must be verified against:
- Relevant core principles
- Performance standards
- Technology stack requirements
- Quality gate criteria

### Amendment Process
1. Propose change with rationale
2. Assess impact on existing deliverables
3. Create migration plan if needed
4. Update version and last amended date
5. Communicate to all team members

### Continuous Improvement
After 24-hour test completion:
- Document lessons learned
- Identify optimization opportunities
- Propose constitution amendments
- Plan for production scaling

**Version**: 1.0.0 | **Ratified**: 2026-02-15 | **Last Amended**: 2026-02-15

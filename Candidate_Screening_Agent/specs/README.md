# Candidate Screening Agent - Specification Documentation

**Project**: Autonomous Candidate Screening Digital FTE
**Status**: Ready for Implementation
**Created**: 2026-04-27
**Last Updated**: 2026-04-27

---

## Overview

This directory contains comprehensive specification documentation for the Candidate Screening Agent project, following SpecKit Plus methodology. All documents are structured to support spec-driven development with clear requirements, implementation plans, and acceptance criteria.

---

## Document Structure

### Core Specifications

#### 📋 [spec.md](./spec.md)
**Feature Specification** - Complete functional and non-functional requirements

**Contents**:
- Problem statement and solution overview
- Functional requirements (FR-1 to FR-5)
- Non-functional requirements (performance, reliability, security, scalability)
- Success criteria (must have, should have, could have)
- Constraints and assumptions
- Out of scope items
- Dependencies and risks

**When to read**: Start here to understand what we're building and why.

---

#### 🏗️ [plan.md](./plan.md)
**Implementation Plan** - Architectural design and technical strategy

**Contents**:
- System architecture with diagrams
- Component design (database, AI agents, services, watchers, orchestrator, API, frontend)
- Data flow diagrams
- Technology stack rationale
- Error handling strategy
- Security considerations
- Testing strategy
- Performance optimization
- Deployment strategy
- Rollout plan

**When to read**: After understanding requirements, before implementation.

---

#### ✅ [tasks.md](./tasks.md)
**Implementation Tasks** - Actionable, dependency-ordered tasks

**Contents**:
- 42 tasks organized in 12 phases
- Task dependencies clearly marked
- Acceptance criteria for each task
- Effort estimates (S/M/L/XL)
- Critical path identified
- Parallel work opportunities

**When to read**: During implementation to track progress.

---

#### 🔬 [research.md](./research.md)
**Technical Research** - Research findings and technical decisions

**Contents**:
- 12 research areas (R-001 to R-012)
- Technology evaluations and comparisons
- Decision rationale with trade-offs
- Open questions for future research
- References to external documentation

**When to read**: When making technical decisions or evaluating alternatives.

---

#### 🗄️ [data-model.md](./data-model.md)
**Data Model** - Complete database schema and entity relationships

**Contents**:
- Entity relationship diagram
- Table definitions (jobs, candidates, pending_approvals, audit_log)
- Field specifications with types and constraints
- JSON schemas for flexible data
- Indexes and performance considerations
- Data flow diagrams
- Migration strategy
- Backup and recovery procedures

**When to read**: Before implementing database layer or when querying data.

---

### Checklists

#### ✓ [checklist/pre-deployment.md](./checklist/pre-deployment.md)
**Pre-Deployment Checklist** - Verify readiness before deployment

**Sections**:
- Infrastructure (PostgreSQL, Redis, environment variables)
- Backend (dependencies, API, error handling)
- AI Integration (Grok API, model selection)
- Gmail Integration (OAuth2, DRY_RUN mode)
- Watchers and Orchestrator
- Frontend (Next.js, API connection)
- Testing (all tests pass, coverage targets met)
- Security (no secrets in code, CORS configured)
- Documentation (README, API docs)
- Compliance (HITL boundaries, audit logging)
- Performance (response times, query optimization)
- Monitoring (logs, health checks)
- Deployment (Railway, Vercel)
- Post-deployment verification
- Rollback plan

**When to use**: Before deploying to production.

---

#### ✓ [checklist/testing.md](./checklist/testing.md)
**Testing Checklist** - Comprehensive test coverage verification

**Sections**:
- Unit tests (screening agent, PDF service, Gmail service, CRUD, orchestrator, routers, watchers)
- Integration tests (end-to-end flow, database, Redis, Gmail API, Grok API)
- Manual testing (happy path, error scenarios, edge cases, UI/UX)
- Performance testing (load testing, database performance, memory usage)
- Security testing (authentication, input validation, data protection)
- Regression testing
- Test coverage targets (75-95% by module)

**When to use**: Throughout development and before each deployment.

---

#### ✓ [checklist/code-review.md](./checklist/code-review.md)
**Code Review Checklist** - Ensure code quality and constitution compliance

**Sections**:
- Constitution compliance (HITL, async-first, AI-first, error handling, DRY_RUN, audit, test coverage)
- Code quality (PEP 8, smallest viable change, type hints, error handling)
- Database (models, CRUD, migrations)
- API (endpoints, CORS, documentation)
- AI integration (Grok API, prompt engineering)
- Services (PDF, Gmail, audit)
- Watchers and orchestrator
- Frontend (components, API integration, styling)
- Testing (unit tests, integration tests, coverage)
- Security (secrets management, input validation, authentication)
- Documentation (code comments, README, API docs)
- Performance (database queries, API response times, memory)
- Git (commits, pull requests)

**When to use**: Before merging any pull request.

---

#### ✓ [checklist/security.md](./checklist/security.md)
**Security Checklist** - Verify security measures before deployment

**Sections**:
- Secrets management (no hardcoded secrets, environment variables)
- Authentication & authorization (OAuth2, API keys)
- Input validation (email, file uploads, API inputs)
- Data protection (PII, audit log, database encryption)
- Network security (HTTPS/TLS, CORS, rate limiting)
- Application security (dependencies, code security, session security)
- Infrastructure security (Docker, cloud deployment, monitoring)
- HITL security (approval process, email sending)
- Compliance (GDPR, equal opportunity, data retention)
- Incident response (security incident plan, backup & recovery)
- Penetration testing (manual testing, automated scanning)
- Security headers (HTTP headers, CORS headers)
- Logging & monitoring (security logging, monitoring)
- Third-party security (Grok API, Gmail API, Railway, Vercel)
- Security training

**When to use**: Before deploying to production and during security audits.

---

### Contracts

#### 📜 [contracts/api-contracts.md](./contracts/api-contracts.md)
**API Contracts** - REST API endpoint specifications

**Endpoints**:
- Health check: `GET /health`
- Candidates: `GET /candidates`, `GET /candidates/{id}`, `GET /candidates/by-status/{status}`, `GET /candidates/{id}/brief`
- Approvals: `GET /approvals/pending`, `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject`
- Jobs: `GET /jobs`, `POST /jobs`, `GET /jobs/{id}`

**Includes**:
- Request/response schemas
- Status codes
- Error responses
- CORS configuration
- Rate limiting (future)
- Authentication (future)

**When to use**: When implementing or consuming API endpoints.

---

#### 📜 [contracts/service-contracts.md](./contracts/service-contracts.md)
**Service Contracts** - External service integration specifications

**Services**:
- Grok AI Service (CV scoring, question generation, reply analysis)
- Gmail API Service (list emails, get messages, get attachments, send emails)
- Redis Service (queue operations)
- PostgreSQL Service (connection pooling, transaction management)
- PDF Processing Service (text extraction)

**Includes**:
- Configuration details
- Input/output schemas
- Error handling strategies
- SLAs (availability, response time, error rate)
- Monitoring & alerting

**When to use**: When integrating with external services.

---

## Quick Navigation

### By Role

**Product Owner**:
1. Read [spec.md](./spec.md) - Understand requirements and success criteria
2. Review [plan.md](./plan.md) - Understand implementation approach
3. Use [checklist/pre-deployment.md](./checklist/pre-deployment.md) - Verify readiness

**Tech Lead / Architect**:
1. Read [spec.md](./spec.md) - Understand requirements
2. Read [plan.md](./plan.md) - Review architecture and design decisions
3. Read [research.md](./research.md) - Understand technical decisions
4. Read [data-model.md](./data-model.md) - Review database schema
5. Use [checklist/code-review.md](./checklist/code-review.md) - Review code quality

**Developer**:
1. Read [spec.md](./spec.md) - Understand what to build
2. Read [plan.md](./plan.md) - Understand how to build it
3. Read [tasks.md](./tasks.md) - Follow implementation tasks
4. Read [data-model.md](./data-model.md) - Understand database schema
5. Read [contracts/api-contracts.md](./contracts/api-contracts.md) - Implement API endpoints
6. Read [contracts/service-contracts.md](./contracts/service-contracts.md) - Integrate services
7. Use [checklist/testing.md](./checklist/testing.md) - Verify test coverage

**QA Engineer**:
1. Read [spec.md](./spec.md) - Understand requirements and acceptance criteria
2. Use [checklist/testing.md](./checklist/testing.md) - Execute test plan
3. Use [checklist/pre-deployment.md](./checklist/pre-deployment.md) - Verify deployment readiness

**Security Engineer**:
1. Read [spec.md](./spec.md) - Understand security requirements
2. Read [plan.md](./plan.md) - Review security considerations
3. Use [checklist/security.md](./checklist/security.md) - Conduct security audit
4. Use [checklist/code-review.md](./checklist/code-review.md) - Review security aspects

**DevOps Engineer**:
1. Read [plan.md](./plan.md) - Understand deployment strategy
2. Read [data-model.md](./data-model.md) - Understand database requirements
3. Read [contracts/service-contracts.md](./contracts/service-contracts.md) - Understand infrastructure needs
4. Use [checklist/pre-deployment.md](./checklist/pre-deployment.md) - Deploy to production

---

### By Phase

**Phase 1: Planning**
1. [spec.md](./spec.md) - Define requirements
2. [plan.md](./plan.md) - Design architecture
3. [research.md](./research.md) - Make technical decisions
4. [data-model.md](./data-model.md) - Design database schema
5. [tasks.md](./tasks.md) - Break down into tasks

**Phase 2: Implementation**
1. [tasks.md](./tasks.md) - Follow task order
2. [contracts/api-contracts.md](./contracts/api-contracts.md) - Implement APIs
3. [contracts/service-contracts.md](./contracts/service-contracts.md) - Integrate services
4. [checklist/code-review.md](./checklist/code-review.md) - Review code

**Phase 3: Testing**
1. [checklist/testing.md](./checklist/testing.md) - Execute tests
2. [checklist/security.md](./checklist/security.md) - Security testing

**Phase 4: Deployment**
1. [checklist/pre-deployment.md](./checklist/pre-deployment.md) - Pre-deployment verification
2. [plan.md](./plan.md) - Follow deployment strategy
3. [checklist/security.md](./checklist/security.md) - Final security check

---

## Document Conventions

### Status Labels
- **Draft**: Work in progress, subject to change
- **Review**: Ready for review, awaiting approval
- **Final**: Approved and locked
- **Ready for Implementation**: Approved and ready to build

### Priority Labels
- **Must Have**: Required for MVP
- **Should Have**: Important but not critical
- **Could Have**: Nice to have, future consideration
- **Won't Have**: Explicitly out of scope

### Task Effort Estimates
- **S (Small)**: <4 hours
- **M (Medium)**: 4-8 hours
- **L (Large)**: 8-16 hours
- **XL (Extra Large)**: 16+ hours

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-04-27 | Development Team | Initial specification documentation |

---

## Related Documents

### Project Root
- [README.md](../README.md) - Project overview and setup instructions
- [CLAUDE.md](../CLAUDE.md) - Claude Code rules and guidelines
- [Candidate_Screening_Agent_Blueprint_2026.md](../Candidate_Screening_Agent_Blueprint_2026.md) - Original blueprint

### Constitution
- [.specify/memory/constitution.md](../.specify/memory/constitution.md) - Project principles and standards

---

## Feedback and Updates

This documentation is living and should be updated as the project evolves. To suggest changes:

1. Create an issue describing the proposed change
2. Update the relevant document(s)
3. Submit a pull request with clear description
4. Get approval from Tech Lead and Product Owner
5. Update version history

---

## Contact

**Tech Lead**: [Name] - [Email]
**Product Owner**: [Name] - [Email]
**Security Lead**: [Name] - [Email]

---

**Last Updated**: 2026-04-27
**Next Review**: Before Phase 2 (Implementation)

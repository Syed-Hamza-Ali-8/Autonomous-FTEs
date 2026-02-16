# Customer Success Digital FTE

A 24/7 AI-powered Customer Success agent that handles customer inquiries across multiple channels (Email, WhatsApp, Web Form) using the Agent Maturity Model.

## Overview

This project implements a production-grade Digital FTE (Full-Time Equivalent) that:
- Handles customer support inquiries 24/7 without breaks
- Accepts tickets from Gmail, WhatsApp (Twilio), and Web Forms
- Provides intelligent responses using knowledge base search
- Escalates complex issues to human agents when needed
- Tracks all interactions in PostgreSQL-based CRM
- Operates at <$1,000/year vs $75,000/year human FTE

## Architecture

```
┌─────────────────────────────────────────┐
│     MULTI-CHANNEL INTAKE LAYER          │
│  Gmail → WhatsApp → Web Form            │
│           ↓                             │
│        Kafka Topics                     │
│           ↓                             │
│    Message Processor Workers            │
│           ↓                             │
│  Customer Success Agent (OpenAI)        │
│           ↓                             │
│  PostgreSQL + OpenAI API + Kafka        │
└─────────────────────────────────────────┘
```

## Technology Stack

- **Agent Framework:** OpenAI Agents SDK
- **API Layer:** FastAPI (async)
- **Database:** PostgreSQL 16 with pgvector
- **Message Queue:** Apache Kafka
- **Orchestration:** Kubernetes with HPA
- **Channels:** Gmail API, Twilio WhatsApp API, Next.js Web Form
- **Development:** Claude Code (incubation phase)

## Project Structure

```
.
├── context/              # Development dossier (incubation phase)
├── src/                  # Source code
│   ├── channels/         # Channel integrations (Gmail, WhatsApp, Web)
│   ├── agent/            # Core agent logic
│   └── web-form/         # Support form frontend
├── tests/                # Test suites
├── specs/                # Specifications and contracts
├── k8s/                  # Kubernetes manifests
└── history/              # PHRs and ADRs
```

## Development Phases

### Phase 1: Incubation (Hours 1-16)
- Use Claude Code for exploration and prototyping
- Create development dossier with company context
- Build and test prototype with sample tickets
- Document edge cases and requirements

### Phase 2: Specialization (Hours 17-40)
- Transform prototype to production agent using OpenAI SDK
- Implement all three channel integrations
- Set up PostgreSQL, Kafka, and Kubernetes
- Build complete web form UI
- Implement monitoring and metrics

### Phase 3: Production Readiness (Hours 41-48)
- End-to-end testing across all channels
- Load testing and performance optimization
- 24-hour continuous operation test
- Documentation and deployment

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16
- Apache Kafka
- Kubernetes (minikube or cloud)
- OpenAI API key
- Gmail API credentials
- Twilio account with WhatsApp enabled

### Installation

```bash
# Clone repository
git clone <repo-url>
cd The_CRM_Digital_FTE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Start infrastructure
docker-compose up -d

# Run database migrations
python src/db/migrate.py

# Start the agent
python src/main.py
```

## Configuration

See `.env.example` for required environment variables:
- OpenAI API key
- Gmail API credentials
- Twilio credentials
- PostgreSQL connection
- Kafka brokers

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run E2E tests
pytest tests/e2e/

# Run 24-hour continuous test
python tests/continuous/run_24h_test.py
```

## Monitoring

- Prometheus metrics: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3000`
- Kafka UI: `http://localhost:8080`

## Documentation

- [Specification](specs/spec.md)
- [Implementation Plan](specs/plan.md)
- [Tasks](specs/tasks.md)
- [Data Model](specs/data-model.md)
- [API Contracts](specs/contracts/)

## Performance Targets

- Response time: P95 < 3 seconds
- Uptime: > 99.9%
- Escalation rate: < 25%
- Cross-channel accuracy: > 95%
- Operating cost: < $1,000/year

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please open a GitHub issue.

# Cross-Domain Reasoner API Contract

**Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Active

## Overview

This document defines the API contract for the Cross-Domain Reasoner, which analyzes events and generates actions across personal and business domains for the Gold Tier autonomous employee.

## Base Configuration

The Cross-Domain Reasoner is implemented as a Python module, not an MCP server.

**Module Path**: `gold/src/intelligence/cross_domain_reasoner.py`

**Dependencies**:
- `gold/src/core/audit_logger.py`
- `gold/src/actions/action_executor.py`
- `gold/src/utils/yaml_parser.py`

---

## API Methods

### 1. createContext

Create a new cross-domain context from an event.

**Function Signature**:
```python
def create_context(
    trigger_event: str,
    trigger_domain: str,
    event_type: str,
    event_source: str,
    event_data: dict
) -> dict
```

**Input**:
```python
{
    "trigger_event": "Payment received from Client A ($1,500)",
    "trigger_domain": "personal",
    "event_type": "payment_received",
    "event_source": "gmail",
    "event_data": {
        "amount": 1500.00,
        "currency": "USD",
        "from": "client-a@example.com",
        "subject": "Payment for Invoice INV-2026-001"
    }
}
```

**Output**:
```python
{
    "context_id": "ctx_personal_20260115_103000",
    "file_path": "/Vault/Context/ctx_personal_20260115_103000.md",
    "status": "analyzing"
}
```

**Raises**:
- `ValueError`: Invalid domain or event type
- `IOError`: Failed to create context file

---

### 2. analyzeEvent

Analyze an event and determine cross-domain impacts.

**Function Signature**:
```python
def analyze_event(context_id: str) -> dict
```

**Input**:
```python
{
    "context_id": "ctx_personal_20260115_103000"
}
```

**Output**:
```python
{
    "context_id": "ctx_personal_20260115_103000",
    "personal_impact": {
        "affected": True,
        "impact_level": "high",
        "description": "Payment received increases personal cash flow",
        "suggested_actions": [
            "Send thank you message to client",
            "Update personal budget tracker"
        ]
    },
    "business_impact": {
        "affected": True,
        "impact_level": "high",
        "description": "Revenue recorded, invoice marked paid",
        "suggested_actions": [
            "Update Xero invoice status to PAID",
            "Record revenue in monthly tracking",
            "Update CEO Briefing metrics"
        ]
    },
    "actions_generated": 3
}
```

**Raises**:
- `ValueError`: Context not found
- `RuntimeError`: Analysis failed

---

### 3. generateActions

Generate actions from impact analysis.

**Function Signature**:
```python
def generate_actions(context_id: str) -> list[dict]
```

**Input**:
```python
{
    "context_id": "ctx_personal_20260115_103000"
}
```

**Output**:
```python
[
    {
        "action_id": "act_20260115_103001",
        "domain": "personal",
        "action_type": "send_message",
        "description": "Send thank you message to Client A via Gmail",
        "priority": "high",
        "status": "pending",
        "requires_approval": False
    },
    {
        "action_id": "act_20260115_103002",
        "domain": "business",
        "action_type": "xero_update",
        "description": "Mark invoice INV-2026-001 as PAID in Xero",
        "priority": "critical",
        "status": "pending",
        "requires_approval": False
    },
    {
        "action_id": "act_20260115_103003",
        "domain": "business",
        "action_type": "revenue_tracking",
        "description": "Record $1,500 revenue in monthly tracking",
        "priority": "high",
        "status": "pending",
        "requires_approval": False
    }
]
```

**Raises**:
- `ValueError`: Context not found or not analyzed
- `RuntimeError`: Action generation failed

---

### 4. executeActions

Execute all actions for a context.

**Function Signature**:
```python
def execute_actions(context_id: str) -> dict
```

**Input**:
```python
{
    "context_id": "ctx_personal_20260115_103000"
}
```

**Output**:
```python
{
    "context_id": "ctx_personal_20260115_103000",
    "total_actions": 3,
    "completed": 3,
    "failed": 0,
    "results": [
        {
            "action_id": "act_20260115_103001",
            "status": "completed",
            "result": "Message sent successfully",
            "duration_ms": 1234.56
        },
        {
            "action_id": "act_20260115_103002",
            "status": "completed",
            "result": "Invoice updated successfully",
            "duration_ms": 2345.67
        },
        {
            "action_id": "act_20260115_103003",
            "status": "completed",
            "result": "Revenue recorded for January 2026",
            "duration_ms": 890.12
        }
    ]
}
```

**Raises**:
- `ValueError`: Context not found or no actions to execute
- `RuntimeError`: Action execution failed

---

### 5. getContext

Retrieve a context by ID.

**Function Signature**:
```python
def get_context(context_id: str) -> dict
```

**Input**:
```python
{
    "context_id": "ctx_personal_20260115_103000"
}
```

**Output**:
```python
{
    "context_id": "ctx_personal_20260115_103000",
    "trigger_event": "Payment received from Client A ($1,500)",
    "trigger_domain": "personal",
    "status": "completed",
    "created_at": "2026-01-15T10:00:00Z",
    "completed_at": "2026-01-15T10:00:30Z",
    "actions": [...],
    "personal_impact": {...},
    "business_impact": {...}
}
```

**Raises**:
- `ValueError`: Context not found
- `IOError`: Failed to read context file

---

### 6. listContexts

List all contexts, optionally filtered.

**Function Signature**:
```python
def list_contexts(
    domain: str = None,
    status: str = None,
    since: str = None,
    limit: int = 100
) -> list[dict]
```

**Input**:
```python
{
    "domain": "personal",
    "status": "completed",
    "since": "2026-01-01T00:00:00Z",
    "limit": 50
}
```

**Output**:
```python
[
    {
        "context_id": "ctx_personal_20260115_103000",
        "trigger_event": "Payment received from Client A ($1,500)",
        "trigger_domain": "personal",
        "status": "completed",
        "created_at": "2026-01-15T10:00:00Z",
        "actions_count": 3
    },
    {
        "context_id": "ctx_business_20260114_150000",
        "trigger_event": "Expense recorded in Xero ($500)",
        "trigger_domain": "business",
        "status": "completed",
        "created_at": "2026-01-14T15:00:00Z",
        "actions_count": 2
    }
]
```

**Raises**:
- `ValueError`: Invalid filter parameters
- `IOError`: Failed to read context directory

---

## Event Types

### Personal Domain Events

| Event Type | Source | Description |
|------------|--------|-------------|
| `payment_received` | gmail, whatsapp | Payment notification received |
| `message_received` | gmail, whatsapp | Important message received |
| `task_completed` | vault | Personal task completed |
| `calendar_event` | calendar | Calendar event occurred |

### Business Domain Events

| Event Type | Source | Description |
|------------|--------|-------------|
| `expense_recorded` | xero | Expense transaction synced |
| `invoice_created` | xero | New invoice created |
| `invoice_paid` | xero | Invoice marked as paid |
| `social_post_published` | social | Social media post published |
| `engagement_milestone` | social | Engagement milestone reached |

---

## Impact Levels

| Level | Description | Action Priority |
|-------|-------------|-----------------|
| `none` | No impact | N/A |
| `low` | Minor impact, informational | low |
| `medium` | Moderate impact, action recommended | medium |
| `high` | Significant impact, action required | high |

---

## Action Types

### Personal Domain Actions

| Action Type | Description | Approval Required |
|-------------|-------------|-------------------|
| `send_message` | Send email or WhatsApp message | No (< 100 chars) |
| `create_task` | Create task in vault | No |
| `update_budget` | Update personal budget | No |
| `send_notification` | Send notification to user | No |

### Business Domain Actions

| Action Type | Description | Approval Required |
|-------------|-------------|-------------------|
| `xero_update` | Update Xero transaction/invoice | No |
| `revenue_tracking` | Record revenue | No |
| `expense_tracking` | Record expense | No |
| `create_report` | Generate financial report | No |
| `social_post` | Create social media post | Yes |
| `send_invoice` | Send invoice to client | Yes (> $500) |

---

## Error Handling

### Error Types

| Error Type | Description | Recoverable |
|------------|-------------|-------------|
| `ValueError` | Invalid input parameters | No |
| `IOError` | File system error | Yes |
| `RuntimeError` | Processing error | Yes |
| `TimeoutError` | Operation timeout | Yes |

### Error Response

```python
{
    "error": {
        "type": "RuntimeError",
        "message": "Failed to analyze event",
        "context_id": "ctx_personal_20260115_103000",
        "recoverable": True
    }
}
```

---

## Usage Examples

### Example 1: Payment Received

```python
from gold.src.intelligence.cross_domain_reasoner import CrossDomainReasoner

reasoner = CrossDomainReasoner(vault_path="/Vault")

# Create context
context = reasoner.create_context(
    trigger_event="Payment received from Client A ($1,500)",
    trigger_domain="personal",
    event_type="payment_received",
    event_source="gmail",
    event_data={
        "amount": 1500.00,
        "currency": "USD",
        "from": "client-a@example.com"
    }
)

# Analyze event
analysis = reasoner.analyze_event(context["context_id"])

# Generate actions
actions = reasoner.generate_actions(context["context_id"])

# Execute actions
results = reasoner.execute_actions(context["context_id"])

print(f"Completed {results['completed']} of {results['total_actions']} actions")
```

### Example 2: Expense Recorded

```python
# Create context for business expense
context = reasoner.create_context(
    trigger_event="Expense recorded in Xero ($500)",
    trigger_domain="business",
    event_type="expense_recorded",
    event_source="xero",
    event_data={
        "amount": -500.00,
        "currency": "USD",
        "category": "software_subscription",
        "vendor": "Adobe Inc"
    }
)

# Analyze and execute
analysis = reasoner.analyze_event(context["context_id"])
actions = reasoner.generate_actions(context["context_id"])
results = reasoner.execute_actions(context["context_id"])
```

---

## Integration Points

### Watchers
- All watchers trigger cross-domain analysis for significant events
- Gmail/WhatsApp watchers for personal domain events
- Xero watcher for business domain events
- Social watchers for engagement events

### Actions
- ActionExecutor executes generated actions
- Approval workflow for actions requiring HITL

### Intelligence
- CEO Briefing uses cross-domain insights
- Business analytics tracks cross-domain patterns

---

## Performance

### Benchmarks

| Operation | Average Time | Max Time |
|-----------|--------------|----------|
| Create Context | 50ms | 200ms |
| Analyze Event | 500ms | 2000ms |
| Generate Actions | 200ms | 1000ms |
| Execute Actions | 1000ms | 5000ms |

### Optimization

- Context files cached in memory
- Parallel action execution
- Async I/O for file operations

---

**API Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-17

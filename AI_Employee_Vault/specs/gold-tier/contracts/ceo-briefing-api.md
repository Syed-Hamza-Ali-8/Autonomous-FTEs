# CEO Briefing Generator API Contract

**Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Active

## Overview

This document defines the API contract for the CEO Briefing Generator, which creates weekly business intelligence reports every Sunday at 7:00 AM for the Gold Tier autonomous employee.

## Base Configuration

The CEO Briefing Generator is implemented as a Python module with scheduled execution.

**Module Path**: `gold/src/intelligence/ceo_briefing.py`

**Schedule**: Every Sunday at 7:00 AM (cron: `0 7 * * 0`)

**Output Path**: `Briefings/{YYYY-MM-DD}_Monday_Briefing.md`

---

## API Methods

### 1. generateBriefing

Generate a CEO Briefing for a specified period.

**Function Signature**:
```python
def generate_briefing(
    period_start: str,
    period_end: str,
    auto_save: bool = True
) -> dict
```

**Input**:
```python
{
    "period_start": "2026-01-12",
    "period_end": "2026-01-18",
    "auto_save": True
}
```

**Output**:
```python
{
    "briefing_id": "briefing_20260119",
    "file_path": "/Vault/Briefings/2026-01-19_Monday_Briefing.md",
    "generated_at": "2026-01-19T07:00:00Z",
    "metrics": {
        "revenue_this_week": 2450.00,
        "revenue_mtd": 4500.00,
        "revenue_target": 10000.00,
        "tasks_completed": 12,
        "bottlenecks_count": 2,
        "suggestions_count": 3,
        "social_posts": 8,
        "outstanding_invoices": 3500.00
    }
}
```

**Raises**:
- `ValueError`: Invalid date range
- `IOError`: Failed to create briefing file
- `RuntimeError`: Data collection failed

---

### 2. collectRevenue

Collect revenue data from Xero for the period.

**Function Signature**:
```python
def collect_revenue(
    period_start: str,
    period_end: str
) -> dict
```

**Input**:
```python
{
    "period_start": "2026-01-12",
    "period_end": "2026-01-18"
}
```

**Output**:
```python
{
    "revenue_this_week": 2450.00,
    "revenue_mtd": 4500.00,
    "revenue_target": 10000.00,
    "revenue_percentage": 45.0,
    "trend": "on_track",
    "invoices_paid": [
        {
            "invoice_id": "INV-2026-001",
            "client": "Client A",
            "amount": 1500.00,
            "paid_date": "2026-01-15"
        }
    ]
}
```

---

### 3. collectTasks

Collect completed tasks from vault for the period.

**Function Signature**:
```python
def collect_tasks(
    period_start: str,
    period_end: str
) -> dict
```

**Input**:
```python
{
    "period_start": "2026-01-12",
    "period_end": "2026-01-18"
}
```

**Output**:
```python
{
    "tasks_completed": 12,
    "tasks": [
        {
            "task_id": "task_001",
            "title": "Client A invoice sent and paid",
            "completed_at": "2026-01-15T10:00:00Z",
            "duration_hours": 2.5
        }
    ],
    "total_hours": 30.0,
    "avg_hours_per_task": 2.5
}
```

---

### 4. identifyBottlenecks

Identify tasks that took longer than expected.

**Function Signature**:
```python
def identify_bottlenecks(
    tasks: list[dict],
    threshold_percent: float = 50.0
) -> dict
```

**Input**:
```python
{
    "tasks": [...],
    "threshold_percent": 50.0
}
```

**Output**:
```python
{
    "bottlenecks_count": 2,
    "bottlenecks": [
        {
            "task": "Client B proposal",
            "expected_hours": 2.0,
            "actual_hours": 5.0,
            "delay_hours": 3.0,
            "delay_percent": 150.0,
            "reason": "Multiple revision rounds required"
        },
        {
            "task": "Code review",
            "expected_hours": 1.0,
            "actual_hours": 3.0,
            "delay_hours": 2.0,
            "delay_percent": 200.0,
            "reason": "Complex changes requiring detailed review"
        }
    ]
}
```

---

### 5. generateSuggestions

Generate proactive suggestions for cost optimization and deadlines.

**Function Signature**:
```python
def generate_suggestions() -> dict
```

**Output**:
```python
{
    "suggestions_count": 3,
    "cost_optimization": [
        {
            "service": "Notion",
            "issue": "No team activity in 45 days",
            "cost_monthly": 15.00,
            "cost_annual": 180.00,
            "action": "Cancel subscription?",
            "priority": "medium"
        },
        {
            "service": "Slack Premium",
            "issue": "Only 2 active users",
            "cost_monthly": 16.00,
            "cost_annual": 192.00,
            "action": "Downgrade to free plan?",
            "priority": "low"
        }
    ],
    "upcoming_deadlines": [
        {
            "item": "Project Alpha final delivery",
            "due_date": "2026-01-25",
            "days_remaining": 6,
            "priority": "high"
        }
    ]
}
```

---

### 6. collectSocialMetrics

Collect social media performance metrics.

**Function Signature**:
```python
def collect_social_metrics(
    period_start: str,
    period_end: str
) -> dict
```

**Input**:
```python
{
    "period_start": "2026-01-12",
    "period_end": "2026-01-18"
}
```

**Output**:
```python
{
    "social_posts": 8,
    "platforms": {
        "linkedin": {
            "posts": 3,
            "total_engagement": 65,
            "avg_engagement_rate": 5.2
        },
        "twitter": {
            "posts": 4,
            "total_engagement": 28,
            "avg_engagement_rate": 3.1
        },
        "facebook": {
            "posts": 1,
            "total_engagement": 12,
            "avg_engagement_rate": 4.0
        }
    },
    "top_post": {
        "platform": "linkedin",
        "post_id": "post_linkedin_20260115_103000",
        "engagement": 65,
        "content_preview": "Excited to share our latest project milestone..."
    }
}
```

---

### 7. collectFinancialHealth

Collect financial health metrics from Xero.

**Function Signature**:
```python
def collect_financial_health() -> dict
```

**Output**:
```python
{
    "outstanding_invoices": 3500.00,
    "overdue_invoices": 0.00,
    "cash_flow_status": "positive",
    "invoices": [
        {
            "invoice_id": "INV-2026-002",
            "client": "Client C",
            "amount": 2000.00,
            "due_date": "2026-01-25",
            "days_until_due": 6
        },
        {
            "invoice_id": "INV-2026-003",
            "client": "Client D",
            "amount": 1500.00,
            "due_date": "2026-02-01",
            "days_until_due": 13
        }
    ]
}
```

---

### 8. formatBriefing

Format all collected data into markdown briefing.

**Function Signature**:
```python
def format_briefing(
    revenue: dict,
    tasks: dict,
    bottlenecks: dict,
    suggestions: dict,
    social: dict,
    financial: dict
) -> str
```

**Output**:
```markdown
# Monday Morning CEO Briefing

## Executive Summary
Strong week with revenue ahead of target. Two bottlenecks identified in client proposals.

## Revenue
- **This Week**: $2,450
- **MTD**: $4,500 (45% of $10,000 target)
- **Trend**: On track

## Completed Tasks
- [x] Client A invoice sent and paid ($1,500)
- [x] Project Alpha milestone 2 delivered
...

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |
...

## Proactive Suggestions
### Cost Optimization
- **Notion**: No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription?
...

## Social Media Performance
- **LinkedIn**: 3 posts, 65 engagements (avg 21.7/post)
...

## Financial Health
- **Outstanding invoices**: $3,500
...

---
*Generated by AI Employee Gold Tier v1.0*
```

---

### 9. scheduleBriefing

Schedule automatic briefing generation.

**Function Signature**:
```python
def schedule_briefing(
    schedule: str = "0 7 * * 0"
) -> dict
```

**Input**:
```python
{
    "schedule": "0 7 * * 0"  # Every Sunday at 7:00 AM
}
```

**Output**:
```python
{
    "scheduled": True,
    "schedule": "0 7 * * 0",
    "next_run": "2026-01-19T07:00:00Z",
    "scheduler_id": "ceo_briefing_scheduler"
}
```

---

### 10. validateBriefing

Validate briefing against schema.

**Function Signature**:
```python
def validate_briefing(briefing_file: str) -> dict
```

**Input**:
```python
{
    "briefing_file": "/Vault/Briefings/2026-01-19_Monday_Briefing.md"
}
```

**Output**:
```python
{
    "valid": True,
    "errors": [],
    "warnings": [
        "Revenue target not set in Business_Goals.md"
    ]
}
```

---

## Data Sources

### Xero API
- Revenue data (paid invoices)
- Outstanding invoices
- Expense transactions
- Financial reports

### Vault Files
- `/Vault/Done/` - Completed tasks
- `/Vault/Needs_Action/` - Pending tasks
- `/Vault/Social_Media/Posts/` - Social media posts
- `/Vault/Business_Goals.md` - Revenue targets

### Social Media APIs
- LinkedIn engagement metrics
- Twitter engagement metrics
- Facebook engagement metrics
- Instagram engagement metrics

---

## Scheduling

### Cron Configuration

**Linux/macOS**:
```bash
0 7 * * 0 cd /path/to/vault && python3 gold/src/intelligence/ceo_briefing.py
```

**Windows Task Scheduler**:
```xml
<Task>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-19T07:00:00</StartBoundary>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Sunday />
        </DaysOfWeek>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>gold/src/intelligence/ceo_briefing.py</Arguments>
      <WorkingDirectory>C:\path\to\vault</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

---

## Error Handling

### Error Types

| Error Type | Description | Recovery |
|------------|-------------|----------|
| `DataCollectionError` | Failed to collect data from source | Retry with exponential backoff |
| `ValidationError` | Briefing validation failed | Log error, notify user |
| `IOError` | Failed to write briefing file | Retry, use backup location |
| `TimeoutError` | Data collection timeout | Use cached data, mark incomplete |

### Error Response

```python
{
    "error": {
        "type": "DataCollectionError",
        "message": "Failed to collect Xero revenue data",
        "source": "xero_api",
        "recoverable": True,
        "retry_count": 2
    }
}
```

---

## Performance

### Benchmarks

| Operation | Average Time | Max Time |
|-----------|--------------|----------|
| Collect Revenue | 500ms | 2000ms |
| Collect Tasks | 200ms | 1000ms |
| Identify Bottlenecks | 100ms | 500ms |
| Generate Suggestions | 1000ms | 3000ms |
| Collect Social Metrics | 800ms | 2500ms |
| Collect Financial Health | 400ms | 1500ms |
| Format Briefing | 50ms | 200ms |
| **Total** | **3050ms** | **10700ms** |

### Optimization

- Parallel data collection
- Cached data for non-critical metrics
- Async I/O for file operations
- Incremental updates during week

---

## Testing

### Test Cases

1. **Revenue Calculation**
   - Test with multiple invoices
   - Test with different currencies
   - Test with partial month

2. **Task Analysis**
   - Test with various task durations
   - Test bottleneck identification
   - Test with missing metadata

3. **Suggestion Generation**
   - Test cost optimization logic
   - Test deadline detection
   - Test priority assignment

4. **Social Metrics**
   - Test with multiple platforms
   - Test engagement calculations
   - Test top post selection

5. **Briefing Format**
   - Test markdown generation
   - Test schema validation
   - Test file creation

---

## Integration Points

### Watchers
- Xero watcher provides transaction data
- Social watchers provide engagement data

### Actions
- No direct action execution
- Generates approval requests for suggestions

### Intelligence
- Cross-domain reasoner provides context
- Business analytics provides trends

---

**API Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-17

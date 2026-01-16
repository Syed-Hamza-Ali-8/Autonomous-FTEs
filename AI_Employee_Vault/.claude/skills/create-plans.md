---
name: create-plans
description: Generate execution plans from pending action requests and break them down into tasks
version: 1.0.0
author: AI Employee Vault - Silver Tier
tags: [planning, reasoning, automation]
---

# Create Plans Skill

This skill orchestrates the planning and reasoning workflow for the Silver tier AI assistant.

## Purpose

Analyze pending action requests in the `Needs_Action/` folder, generate structured execution plans with complexity assessment, and break them down into discrete, actionable tasks.

## Workflow

1. **Scan for Pending Actions**: Check `Needs_Action/` folder for unprocessed action requests
2. **Generate Plans**: For each action, create a structured execution plan with:
   - Complexity assessment (simple/moderate/complex)
   - Step-by-step execution plan
   - Prerequisites and dependencies
   - Risk assessment and mitigation strategies
3. **Break Down into Tasks**: Convert plan steps into discrete tasks with:
   - Clear acceptance criteria
   - Dependency tracking
   - Status management (ready/blocked/in_progress/completed)
4. **Track Progress**: Monitor plan and task execution status

## Usage

```bash
# Generate plans for all pending actions
/create-plans

# Generate plan for specific action
/create-plans --action <action_id>

# Show plan status
/create-plans --status

# Show ready tasks
/create-plans --ready-tasks
```

## Implementation

When this skill is invoked, you should:

1. **Initialize Planning Components**:
   ```python
   from silver.src.planning import PlanGenerator, TaskAnalyzer, PlanTracker

   vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
   generator = PlanGenerator(vault_path)
   analyzer = TaskAnalyzer(vault_path)
   tracker = PlanTracker(vault_path)
   ```

2. **Generate Plans**:
   ```python
   # Generate plans for all pending actions
   plan_ids = generator.generate_plans_for_pending_actions()

   print(f"Generated {len(plan_ids)} plans")
   for plan_id in plan_ids:
       print(f"  - {plan_id}")
   ```

3. **Break Down Plans into Tasks**:
   ```python
   # Break down all pending plans
   results = analyzer.break_down_all_plans()

   for plan_id, task_ids in results.items():
       print(f"\nPlan: {plan_id}")
       print(f"Tasks: {len(task_ids)}")
       for task_id in task_ids:
           print(f"  - {task_id}")
   ```

4. **Show Status** (if --status flag):
   ```python
   # Get all active plans
   active_plans = tracker.get_all_active_plans()

   for plan in active_plans:
       print(f"\nPlan: {plan['plan_id']}")
       print(f"Status: {plan['status']}")
       print(f"Progress: {plan['completed_tasks']}/{plan['total_tasks']} "
             f"({plan['progress_percent']:.0f}%)")
   ```

5. **Show Ready Tasks** (if --ready-tasks flag):
   ```python
   # Get all ready tasks
   ready_tasks = tracker.get_ready_tasks()

   for task in ready_tasks:
       print(f"\nTask: {task['id']}")
       print(f"Plan: {task['plan_id']}")
       print(f"Action: {task['action_type']}")
       print(f"Step: {task['step_number']}")
   ```

## Output

The skill creates the following artifacts:

1. **Plan Files** (`Plans/<plan_id>.md`):
   - Structured execution plan with steps
   - Complexity assessment
   - Risk analysis
   - Prerequisites

2. **Task Files** (`Tasks/<task_id>.md`):
   - Individual actionable tasks
   - Acceptance criteria
   - Dependency information
   - Status tracking

## Example Output

```
=== Create Plans Skill ===

Scanning for pending actions...
Found 3 pending actions

Generating plans...
✅ Generated plan: plan_20260114_143022_send_email
✅ Generated plan: plan_20260114_143023_research
✅ Generated plan: plan_20260114_143024_create_plan

Breaking down plans into tasks...
✅ Plan plan_20260114_143022_send_email → 5 tasks
✅ Plan plan_20260114_143023_research → 4 tasks
✅ Plan plan_20260114_143024_create_plan → 4 tasks

Summary:
- Plans generated: 3
- Tasks created: 13
- Ready to execute: 3 tasks

Next steps:
1. Review plans in Plans/ folder
2. Check ready tasks with: /create-plans --ready-tasks
3. Execute tasks with: /execute-actions
```

## Integration

This skill integrates with:
- **Watchers**: Processes actions created by Gmail/WhatsApp watchers
- **Approval Workflow**: Plans requiring approval will create approval requests
- **Action Executor**: Ready tasks can be executed by the execute-actions skill
- **Dashboard**: Plan and task status updates the dashboard

## Error Handling

- If no pending actions found, reports "No pending actions to process"
- If plan generation fails, logs error and continues with next action
- If task breakdown fails, logs error but plan is still created
- All errors are logged to `Logs/planning.log`

## Notes

- Plans are automatically generated based on action complexity
- Simple actions (≤3 steps) get streamlined plans
- Complex actions (8+ steps) get detailed plans with risk assessment
- Tasks are created with dependency tracking (sequential execution)
- First task in each plan is marked "ready", others are "blocked"
- As tasks complete, subsequent tasks are automatically unblocked

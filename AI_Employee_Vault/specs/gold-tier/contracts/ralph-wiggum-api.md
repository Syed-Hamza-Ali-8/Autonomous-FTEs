# Ralph Wiggum Loop API Contract

**Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Active

## Overview

This document defines the API contract for the Ralph Wiggum Loop, which enables autonomous multi-step task completion using Claude Code stop hooks for the Gold Tier autonomous employee.

## Base Configuration

The Ralph Wiggum Loop is implemented as a Python module with a stop hook integration.

**Module Path**: `gold/src/core/ralph_wiggum.py`

**Hook Path**: `.claude/hooks/stop.sh`

**State Storage**: `Ralph_State/{task_id}.json`

---

## Core Concept

The Ralph Wiggum Loop prevents Claude from exiting until a task is fully complete by:
1. Intercepting stop/exit attempts via stop hook
2. Checking if task file moved to `/Done/` folder
3. Re-injecting prompt if task incomplete
4. Tracking iterations and enforcing limits

**Named after**: Ralph Wiggum's "I'm helping!" persistence

---

## API Methods

### 1. startTask

Initialize a new Ralph Wiggum task.

**Function Signature**:
```python
def start_task(
    task_file: str,
    max_iterations: int = 10,
    timeout_minutes: int = 30
) -> dict
```

**Input**:
```python
{
    "task_file": "/Vault/Needs_Action/task_client_proposal_20260115.md",
    "max_iterations": 10,
    "timeout_minutes": 30
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "state_file": "Ralph_State/task_client_proposal_20260115.json",
    "status": "initializing",
    "started_at": "2026-01-15T10:00:00Z",
    "timeout_at": "2026-01-15T10:30:00Z"
}
```

**Raises**:
- `ValueError`: Task file not found
- `IOError`: Failed to create state file

---

### 2. checkTaskComplete

Check if task is complete (file in /Done/ folder).

**Function Signature**:
```python
def check_task_complete(task_id: str) -> bool
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115"
}
```

**Output**:
```python
True  # Task file found in /Done/ folder
```

**Raises**:
- `ValueError`: Task not found

---

### 3. incrementIteration

Increment iteration counter and update state.

**Function Signature**:
```python
def increment_iteration(
    task_id: str,
    action: str,
    result: str,
    duration_seconds: float
) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "action": "Draft proposal outline",
    "result": "success",
    "duration_seconds": 120.5
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "iteration": 2,
    "max_iterations": 10,
    "status": "in_progress",
    "should_continue": True
}
```

**Raises**:
- `ValueError`: Task not found
- `RuntimeError`: Max iterations reached

---

### 4. getTaskState

Retrieve current task state.

**Function Signature**:
```python
def get_task_state(task_id: str) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115"
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "task_file": "/Vault/Needs_Action/task_client_proposal_20260115.md",
    "status": "in_progress",
    "iteration": 3,
    "max_iterations": 10,
    "started_at": "2026-01-15T10:00:00Z",
    "last_updated": "2026-01-15T10:05:30Z",
    "timeout_at": "2026-01-15T10:30:00Z",
    "progress": {
        "steps_total": 5,
        "steps_completed": 2,
        "current_step": "Writing proposal sections",
        "percentage": 40.0
    },
    "iterations_history": [
        {
            "iteration": 1,
            "timestamp": "2026-01-15T10:00:00Z",
            "action": "Read task requirements",
            "result": "success",
            "duration_seconds": 45.2
        },
        {
            "iteration": 2,
            "timestamp": "2026-01-15T10:03:00Z",
            "action": "Draft proposal outline",
            "result": "success",
            "duration_seconds": 120.5
        }
    ]
}
```

**Raises**:
- `ValueError`: Task not found
- `IOError`: Failed to read state file

---

### 5. updateProgress

Update task progress information.

**Function Signature**:
```python
def update_progress(
    task_id: str,
    steps_total: int,
    steps_completed: int,
    current_step: str
) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "steps_total": 5,
    "steps_completed": 3,
    "current_step": "Review and refine proposal"
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "progress": {
        "steps_total": 5,
        "steps_completed": 3,
        "current_step": "Review and refine proposal",
        "percentage": 60.0
    }
}
```

---

### 6. completeTask

Mark task as complete and cleanup state.

**Function Signature**:
```python
def complete_task(
    task_id: str,
    exit_reason: str = "completed"
) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "exit_reason": "completed"
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "status": "completed",
    "completed_at": "2026-01-15T10:15:30Z",
    "exit_reason": "completed",
    "metrics": {
        "total_duration_seconds": 930.0,
        "iterations": 5,
        "api_calls": 12,
        "files_created": 1,
        "files_modified": 3
    }
}
```

**Raises**:
- `ValueError`: Task not found

---

### 7. handleTimeout

Handle task timeout gracefully.

**Function Signature**:
```python
def handle_timeout(task_id: str) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115"
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "status": "timeout",
    "exit_reason": "timeout",
    "completed_at": "2026-01-15T10:30:00Z",
    "message": "Task exceeded 30 minute timeout. Progress saved."
}
```

---

### 8. handleMaxIterations

Handle max iterations reached gracefully.

**Function Signature**:
```python
def handle_max_iterations(task_id: str) -> dict
```

**Input**:
```python
{
    "task_id": "task_client_proposal_20260115"
}
```

**Output**:
```python
{
    "task_id": "task_client_proposal_20260115",
    "status": "max_iterations_reached",
    "exit_reason": "max_iterations",
    "completed_at": "2026-01-15T10:20:00Z",
    "message": "Task reached maximum 10 iterations. Manual intervention required."
}
```

---

## Stop Hook Integration

### Hook Script (.claude/hooks/stop.sh)

```bash
#!/bin/bash

# Ralph Wiggum Stop Hook
# Prevents exit until task is complete

TASK_ID=$1
VAULT_PATH="/Vault"

# Check if task is complete
python3 gold/src/core/ralph_wiggum.py check-complete "$TASK_ID"

if [ $? -eq 0 ]; then
    # Task complete, allow exit
    echo "✅ Task complete! File found in /Done/ folder."
    exit 0
else
    # Task incomplete, prevent exit
    echo "⚠️  Task not complete. File not in /Done/ folder."
    echo "🔄 Continuing work on task..."
    exit 1
fi
```

### Hook Configuration

```json
{
  "hooks": {
    "stop": {
      "command": ".claude/hooks/stop.sh",
      "args": ["${TASK_ID}"],
      "blocking": true
    }
  }
}
```

---

## Task Lifecycle

### State Transitions

```
initializing → in_progress → completed
                ↓
                waiting_approval
                ↓
                in_progress → failed
                           → timeout
                           → max_iterations_reached
```

### Iteration Flow

1. **Start**: Task initialized, state file created
2. **Iterate**: Claude works on task, state updated
3. **Check**: Stop hook checks if task in /Done/
4. **Continue**: If not complete, re-inject prompt
5. **Complete**: Task in /Done/, cleanup state

---

## Configuration

### Default Settings

```python
DEFAULT_CONFIG = {
    "max_iterations": 10,
    "timeout_minutes": 30,
    "state_dir": "Ralph_State",
    "done_folder": "/Vault/Done",
    "check_interval_seconds": 5
}
```

### Environment Variables

```bash
RALPH_MAX_ITERATIONS=10
RALPH_TIMEOUT_MINUTES=30
RALPH_STATE_DIR=Ralph_State
RALPH_DONE_FOLDER=/Vault/Done
```

---

## Error Handling

### Error Types

| Error Type | Description | Recovery |
|------------|-------------|----------|
| `MaxIterationsError` | Max iterations reached | Manual intervention |
| `TimeoutError` | Task timeout | Save progress, notify user |
| `TaskNotFoundError` | Task file not found | Abort task |
| `StateCorruptedError` | State file corrupted | Recreate state |

### Error Response

```python
{
    "error": {
        "type": "MaxIterationsError",
        "message": "Task reached maximum 10 iterations",
        "task_id": "task_client_proposal_20260115",
        "recoverable": False,
        "action_required": "manual_review"
    }
}
```

---

## Usage Examples

### Example 1: Simple Task

```python
from gold.src.core.ralph_wiggum import RalphWiggum

ralph = RalphWiggum(vault_path="/Vault")

# Start task
task = ralph.start_task(
    task_file="/Vault/Needs_Action/task_simple.md",
    max_iterations=5,
    timeout_minutes=15
)

# Work on task (Claude iterations)
while not ralph.check_task_complete(task["task_id"]):
    # Claude performs work
    ralph.increment_iteration(
        task_id=task["task_id"],
        action="Current action",
        result="success",
        duration_seconds=60.0
    )

    # Update progress
    ralph.update_progress(
        task_id=task["task_id"],
        steps_total=3,
        steps_completed=1,
        current_step="Working on step 1"
    )

# Complete task
result = ralph.complete_task(task["task_id"])
print(f"Task completed in {result['metrics']['iterations']} iterations")
```

### Example 2: Complex Multi-Step Task

```python
# Start complex task
task = ralph.start_task(
    task_file="/Vault/Needs_Action/task_complex.md",
    max_iterations=10,
    timeout_minutes=30
)

# Monitor progress
state = ralph.get_task_state(task["task_id"])
print(f"Progress: {state['progress']['percentage']}%")

# Handle timeout
if state["status"] == "timeout":
    ralph.handle_timeout(task["task_id"])
```

---

## Performance

### Benchmarks

| Metric | Average | Max |
|--------|---------|-----|
| Iteration Duration | 60s | 300s |
| State File Size | 5KB | 50KB |
| Check Overhead | 10ms | 50ms |

### Optimization

- State file cached in memory
- Async I/O for state updates
- Minimal overhead per iteration

---

## Integration Points

### Watchers
- All watchers can trigger Ralph Wiggum tasks
- Task files created in /Needs_Action/

### Actions
- ActionExecutor integrates with Ralph Wiggum
- Multi-step actions tracked automatically

### Intelligence
- CEO Briefing tracks Ralph Wiggum task completion
- Cross-domain reasoner can trigger Ralph tasks

---

**API Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-17

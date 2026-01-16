---
name: schedule-tasks
description: Manage recurring task schedules for automated execution
version: 1.0.0
author: AI Employee Vault - Silver Tier
tags: [scheduling, automation, recurring]
---

# Schedule Tasks Skill

This skill manages recurring task schedules for automated execution in the Silver tier AI assistant.

## Purpose

Create, manage, and monitor recurring task schedules including:
- Daily tasks (e.g., morning reports, daily summaries)
- Weekly tasks (e.g., weekly reviews, status updates)
- Monthly tasks (e.g., monthly reports, billing reminders)
- Interval-based tasks (e.g., every 30 minutes, every 2 hours)

## Workflow

1. **Create Schedules**: Define recurring tasks with schedule configuration
2. **Manage Schedules**: Enable, disable, update, or remove schedules
3. **Monitor Execution**: Track schedule execution and statistics
4. **Persist Configuration**: Save schedules to configuration file

## Usage

```bash
# List all schedules
/schedule-tasks --list

# Add new schedule
/schedule-tasks --add

# Remove schedule
/schedule-tasks --remove <task_id>

# Enable/disable schedule
/schedule-tasks --enable <task_id>
/schedule-tasks --disable <task_id>

# Show schedule statistics
/schedule-tasks --stats

# Start scheduler
/schedule-tasks --start

# Stop scheduler
/schedule-tasks --stop
```

## Implementation

When this skill is invoked, you should:

1. **Initialize Scheduling Components**:
   ```python
   from silver.src.scheduling import Scheduler, ScheduleManager

   vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

   scheduler = Scheduler(vault_path)
   manager = ScheduleManager(vault_path)
   ```

2. **List Schedules** (if --list flag):
   ```python
   schedules = manager.get_all_schedules()

   print(f"Scheduled Tasks ({len(schedules)} total):")
   for schedule in schedules:
       status = "✅ Enabled" if schedule['enabled'] else "❌ Disabled"
       print(f"\n  {schedule['task_id']}")
       print(f"  Description: {schedule['description']}")
       print(f"  Type: {schedule['schedule_type']}")
       print(f"  Status: {status}")
       print(f"  Config: {schedule['schedule_config']}")
   ```

3. **Add Schedule** (if --add flag):
   ```python
   # Prompt user for schedule details
   task_id = input("Task ID: ")
   description = input("Description: ")
   schedule_type = input("Schedule type (daily/weekly/monthly/interval): ")

   # Get schedule config based on type
   if schedule_type == "daily":
       time = input("Time (HH:MM): ")
       schedule_config = {"time": time}
   elif schedule_type == "weekly":
       day = input("Day (monday-sunday): ")
       time = input("Time (HH:MM): ")
       schedule_config = {"day": day, "time": time}
   elif schedule_type == "interval":
       interval = int(input("Interval: "))
       unit = input("Unit (seconds/minutes/hours): ")
       schedule_config = {"interval": interval, "unit": unit}

   # Get task config
   action_type = input("Action type (send_email/send_whatsapp): ")
   # ... collect action-specific parameters

   task_config = {
       "action_type": action_type,
       # ... action parameters
   }

   # Add schedule
   manager.add_schedule(
       task_id=task_id,
       schedule_type=schedule_type,
       schedule_config=schedule_config,
       task_config=task_config,
       description=description
   )

   print(f"✅ Schedule added: {task_id}")
   ```

4. **Remove Schedule** (if --remove flag):
   ```python
   task_id = args.get('task_id')

   if manager.remove_schedule(task_id):
       print(f"✅ Schedule removed: {task_id}")
   else:
       print(f"❌ Schedule not found: {task_id}")
   ```

5. **Show Statistics** (if --stats flag):
   ```python
   # Manager stats
   manager_stats = manager.get_stats()
   print(f"Schedule Statistics:")
   print(f"  Total: {manager_stats['total']}")
   print(f"  Enabled: {manager_stats['enabled']}")
   print(f"  Disabled: {manager_stats['disabled']}")
   print(f"  By type: {manager_stats['by_type']}")

   # Scheduler stats (if running)
   if scheduler.running:
       scheduler_stats = scheduler.get_stats()
       print(f"\nScheduler Statistics:")
       print(f"  Running: {scheduler_stats['running']}")
       print(f"  Total runs: {scheduler_stats['total_runs']}")
       print(f"  Total errors: {scheduler_stats['total_errors']}")
       print(f"  Next run: {scheduler_stats['next_run']}")
   ```

6. **Start Scheduler** (if --start flag):
   ```python
   # Load schedules from manager
   schedules = manager.get_all_schedules(enabled_only=True)

   # Register each schedule with scheduler
   for schedule in schedules:
       # Create task function
       def create_task_func(task_config):
           def task_func():
               # Execute task based on task_config
               action_type = task_config['action_type']
               # ... execute action
               print(f"Executing scheduled task: {action_type}")
           return task_func

       task_func = create_task_func(schedule['task_config'])

       # Schedule task
       scheduler.schedule_task(
           task_id=schedule['task_id'],
           task_func=task_func,
           schedule_type=schedule['schedule_type'],
           schedule_config=schedule['schedule_config'],
           description=schedule['description']
       )

   # Start scheduler
   scheduler.start()
   print(f"✅ Scheduler started with {len(schedules)} tasks")
   ```

## Output

The skill manages the following artifacts:

1. **Schedule Configuration** (`silver/config/schedules/schedules.yaml`):
   - Persistent schedule definitions
   - Schedule metadata and status
   - Task configuration

2. **Scheduler State**:
   - Active scheduled jobs
   - Execution statistics
   - Next run times

## Example Output

```
=== Schedule Tasks Skill ===

Listing scheduled tasks...

Scheduled Tasks (3 total):

  daily_morning_report
  Description: Send morning report email at 9 AM
  Type: daily
  Status: ✅ Enabled
  Config: {'time': '09:00'}
  Next run: 2026-01-15 09:00:00

  weekly_status_update
  Description: Send weekly status update on Mondays
  Type: weekly
  Status: ✅ Enabled
  Config: {'day': 'monday', 'time': '10:00'}
  Next run: 2026-01-20 10:00:00

  interval_check_inbox
  Description: Check inbox every 5 minutes
  Type: interval
  Status: ❌ Disabled
  Config: {'interval': 5, 'unit': 'minutes'}

Schedule Statistics:
  Total: 3
  Enabled: 2
  Disabled: 1
  By type: {'daily': 1, 'weekly': 1, 'interval': 1}

Scheduler Statistics:
  Running: True
  Total runs: 47
  Total errors: 0
  Next run: 2026-01-15 09:00:00
```

## Schedule Types

### Daily
Runs every day at a specific time.
```yaml
schedule_type: daily
schedule_config:
  time: "09:00"  # HH:MM format
```

### Weekly
Runs on a specific day of the week at a specific time.
```yaml
schedule_type: weekly
schedule_config:
  day: "monday"  # monday-sunday
  time: "10:00"  # HH:MM format
```

### Monthly
Runs on a specific day of the month at a specific time.
```yaml
schedule_type: monthly
schedule_config:
  day: 1  # 1-31
  time: "09:00"  # HH:MM format
```

### Interval
Runs at regular intervals.
```yaml
schedule_type: interval
schedule_config:
  interval: 30  # number
  unit: "minutes"  # seconds/minutes/hours
```

## Integration

This skill integrates with:
- **Action Executor**: Executes scheduled actions
- **Approval Workflow**: Scheduled actions requiring approval
- **Email Sender**: Sends scheduled emails
- **WhatsApp Sender**: Sends scheduled messages
- **Dashboard**: Updates dashboard with schedule status

## Error Handling

- Invalid schedule configurations are rejected with error messages
- Failed task executions are logged and tracked
- Scheduler continues running even if individual tasks fail
- All errors are logged to `Logs/scheduler.log`

## Security

- Schedules are stored in configuration files (not in code)
- Sensitive actions still require approval (HITL workflow)
- Schedule modifications are logged for audit trail
- Only authorized users can modify schedules

## Notes

- Scheduler runs in a background thread
- Schedules persist across restarts
- Disabled schedules are not executed but remain in configuration
- Schedule execution is tracked for monitoring and debugging
- Use `--stats` to monitor scheduler health and performance

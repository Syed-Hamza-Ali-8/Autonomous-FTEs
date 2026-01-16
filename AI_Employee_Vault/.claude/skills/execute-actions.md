---
name: execute-actions
description: Execute approved actions (emails, WhatsApp messages) with retry logic and result tracking
version: 1.0.0
author: AI Employee Vault - Silver Tier
tags: [actions, execution, automation]
---

# Execute Actions Skill

This skill orchestrates the action execution workflow for the Silver tier AI assistant.

## Purpose

Execute approved actions from the `Approved/` folder, including:
- Sending emails via Gmail API
- Sending WhatsApp messages via WhatsApp Web
- Other external actions with retry logic and error handling

## Workflow

1. **Scan for Approved Actions**: Check `Approved/` folder for actions ready to execute
2. **Route to Handlers**: Route each action to the appropriate handler (email, WhatsApp, etc.)
3. **Execute with Retry**: Execute actions with exponential backoff retry logic
4. **Track Results**: Record execution results and move files to `Done/` or `Failed/`
5. **Update Status**: Update action status and notify user of completion

## Usage

```bash
# Execute all approved actions
/execute-actions

# Execute specific action
/execute-actions --action <action_id>

# Show execution statistics
/execute-actions --stats

# Dry run (show what would be executed)
/execute-actions --dry-run
```

## Implementation

When this skill is invoked, you should:

1. **Initialize Action Components**:
   ```python
   from silver.src.actions import ActionExecutor, EmailSender, WhatsAppSender

   vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
   config_path = f"{vault_path}/silver/config/approval_rules.yaml"

   executor = ActionExecutor(vault_path, config_path)
   email_sender = EmailSender(vault_path)
   whatsapp_sender = WhatsAppSender(vault_path)
   ```

2. **Register Action Handlers**:
   ```python
   # Register email handler
   def handle_send_email(action_details):
       return email_sender.send_email(
           to=action_details.get('to'),
           subject=action_details.get('subject'),
           body=action_details.get('body'),
           html=True
       )

   executor.register_handler('send_email', handle_send_email)

   # Register WhatsApp handler
   def handle_send_whatsapp(action_details):
       return whatsapp_sender.send_message(
           to=action_details.get('to'),
           message=action_details.get('message')
       )

   executor.register_handler('send_whatsapp', handle_send_whatsapp)
   ```

3. **Execute Actions**:
   ```python
   # Execute all approved actions
   results = executor.execute_all_approved_actions()

   print(f"Execution Summary:")
   print(f"  Total: {results['total']}")
   print(f"  Successful: {results['successful']}")
   print(f"  Failed: {results['failed']}")

   for result in results['results']:
       if result['success']:
           print(f"  ✅ {result['action_id']}")
       else:
           print(f"  ❌ {result['action_id']}: {result['error']}")
   ```

4. **Show Statistics** (if --stats flag):
   ```python
   # Get execution statistics
   stats = executor.get_execution_stats()

   print(f"Execution Statistics:")
   print(f"  Total Executed: {stats['total_executed']}")
   print(f"  Successful: {stats['successful']}")
   print(f"  Failed: {stats['failed']}")
   print(f"  Pending Approval: {stats['pending_approval']}")
   ```

## Output

The skill performs the following operations:

1. **Execute Actions**: Runs approved actions through registered handlers
2. **Update Files**: Moves completed actions to `Done/` or `Failed/`
3. **Track Results**: Records execution results in action file frontmatter
4. **Log Activity**: Logs all execution activity to `Logs/actions.log`

## Example Output

```
=== Execute Actions Skill ===

Scanning for approved actions...
Found 3 approved actions

Executing actions...
✅ Action: approval_20260114_143022_send_email
   → Email sent to: user@example.com
   → Message ID: 18d4f2a3b5c6d7e8
   → Retry count: 0

✅ Action: approval_20260114_143023_send_whatsapp
   → WhatsApp sent to: John Doe
   → Message ID: whatsapp_1705243823
   → Retry count: 0

❌ Action: approval_20260114_143024_send_email
   → Failed: Gmail API error: Invalid credentials
   → Retry count: 3
   → Moved to Failed/

Execution Summary:
- Total: 3
- Successful: 2
- Failed: 1

Next steps:
1. Check Done/ folder for completed actions
2. Check Failed/ folder for failed actions
3. Review logs for details: Logs/actions.log
```

## Retry Logic

Actions are executed with exponential backoff retry logic:
- **Max Retries**: 3 attempts
- **Retry Delays**: 2s, 4s, 8s (exponential backoff)
- **Failure Handling**: After 3 failed attempts, action is moved to `Failed/`

## Error Handling

- **Gmail API Errors**: Logged with error details, action moved to `Failed/`
- **WhatsApp Errors**: Logged with error details, action moved to `Failed/`
- **Network Errors**: Retried with exponential backoff
- **Invalid Actions**: Logged and skipped
- All errors are logged to `Logs/actions.log`

## Integration

This skill integrates with:
- **Approval Workflow**: Executes actions that have been approved
- **Email Sender**: Sends emails via Gmail API
- **WhatsApp Sender**: Sends messages via WhatsApp Web
- **Dashboard**: Updates dashboard with execution statistics
- **Logging**: Logs all activity for audit trail

## Prerequisites

Before using this skill:
1. Gmail API credentials configured (run `python silver/scripts/setup_gmail.py`)
2. WhatsApp Web session active (run `python silver/scripts/setup_whatsapp.py`)
3. Actions have been approved (status: approved in frontmatter)

## Security

- All actions require prior approval (HITL workflow)
- Credentials stored securely in `.env` file
- Execution results logged for audit trail
- Failed actions preserved in `Failed/` folder for review

## Notes

- Actions are executed sequentially (not in parallel)
- Each action has independent retry logic
- Successful actions are moved to `Done/` folder
- Failed actions are moved to `Failed/` folder with error details
- Execution statistics are available via `--stats` flag

# TaskFlow Pro - Product Documentation

## Table of Contents

1. [Getting Started](#getting-started)
2. [Account Management](#account-management)
3. [Task Management](#task-management)
4. [Time Tracking](#time-tracking)
5. [Team Collaboration](#team-collaboration)
6. [Integrations](#integrations)
7. [Mobile Apps](#mobile-apps)
8. [Reporting & Analytics](#reporting-analytics)
9. [Troubleshooting](#troubleshooting)
10. [API Documentation](#api-documentation)

---

## Getting Started

### Creating Your Account

1. Visit www.techcorp.com/signup
2. Enter your email address and create a password
3. Verify your email (check spam folder if not received within 5 minutes)
4. Complete your profile (name, company, role)
5. Invite team members or start exploring

**Free Trial:** All new accounts get a 14-day free trial of the Professional plan.

### First Steps

1. **Create Your First Project**
   - Click "New Project" in the sidebar
   - Enter project name and description
   - Choose a template or start from scratch
   - Set project visibility (private or team)

2. **Invite Team Members**
   - Go to Settings > Team Members
   - Click "Invite Member"
   - Enter email addresses (comma-separated for multiple)
   - Assign roles: Admin, Member, or Guest

3. **Create Your First Task**
   - Open a project
   - Click "Add Task" or press 'N' key
   - Enter task title and description
   - Assign to team member
   - Set due date and priority

---

## Account Management

### Password Reset

**If you forgot your password:**
1. Go to www.techcorp.com/login
2. Click "Forgot Password?"
3. Enter your email address
4. Check your email for reset link (expires in 1 hour)
5. Click the link and create a new password
6. Password must be at least 8 characters with 1 uppercase, 1 lowercase, and 1 number

**If reset link doesn't work:**
- Link expires after 1 hour - request a new one
- Check spam/junk folder
- Make sure you're using the email associated with your account
- Clear browser cache and try again

### Changing Your Email Address

1. Go to Settings > Account
2. Click "Change Email"
3. Enter new email address
4. Verify new email (check inbox)
5. Confirm change with password

**Note:** You'll be logged out and need to log in with the new email.

### Subscription Management

**Upgrading Your Plan:**
1. Go to Settings > Billing
2. Click "Upgrade Plan"
3. Select desired plan (Starter, Professional, Enterprise)
4. Enter payment information
5. Confirm upgrade

**Downgrading Your Plan:**
1. Go to Settings > Billing
2. Click "Change Plan"
3. Select lower-tier plan
4. Review feature changes
5. Confirm downgrade (takes effect at end of billing cycle)

**Canceling Your Subscription:**
1. Go to Settings > Billing
2. Click "Cancel Subscription"
3. Provide feedback (optional)
4. Confirm cancellation
5. Access continues until end of billing period

**Billing Cycle:** Monthly or annual (annual saves 20%)

**Payment Methods:** Credit card, PayPal, bank transfer (Enterprise only)

### Data Export

**Export Your Data:**
1. Go to Settings > Data Export
2. Select data to export:
   - Tasks and projects
   - Time tracking data
   - Team members
   - Files and attachments
3. Choose format: JSON, CSV, or Excel
4. Click "Export"
5. Download link sent to your email (available for 7 days)

**Export time:** 5-30 minutes depending on data size

---

## Task Management

### Creating Tasks

**Basic Task Creation:**
- Click "Add Task" button
- Keyboard shortcut: 'N'
- Enter task title (required)
- Add description (optional, supports Markdown)
- Assign to team member
- Set due date
- Set priority: Low, Medium, High, Urgent

**Advanced Task Options:**
- **Subtasks:** Break down complex tasks into smaller steps
- **Dependencies:** Link tasks that must be completed in order
- **Recurring Tasks:** Set tasks to repeat daily, weekly, monthly
- **Custom Fields:** Add custom data fields (text, number, dropdown, date)
- **Tags:** Organize tasks with color-coded tags
- **Attachments:** Upload files up to 100MB each

### Task Views

**Kanban Board:**
- Drag-and-drop tasks between columns
- Customize columns (To Do, In Progress, Done, etc.)
- Filter by assignee, tag, or priority
- Keyboard shortcuts: Arrow keys to navigate, Enter to open

**List View:**
- See all tasks in a sortable list
- Group by: Assignee, Priority, Due Date, Status
- Bulk actions: Select multiple tasks to update
- Quick filters in sidebar

**Gantt Chart (Professional plan and above):**
- Timeline view of all tasks
- Visualize dependencies
- Adjust dates by dragging
- Critical path highlighting

**Calendar View:**
- See tasks by due date
- Drag to reschedule
- Color-coded by project or assignee
- Sync with Google Calendar or Outlook

### Task Statuses

Default statuses:
- **To Do:** Not started
- **In Progress:** Currently being worked on
- **In Review:** Awaiting review/approval
- **Done:** Completed
- **Blocked:** Cannot proceed due to dependency or issue

**Custom Statuses (Professional plan):** Create your own workflow statuses

### Task Priorities

- **Low:** Nice to have, no urgency
- **Medium:** Normal priority (default)
- **High:** Important, should be done soon
- **Urgent:** Critical, needs immediate attention

**Priority Indicators:**
- Low: Gray
- Medium: Blue
- High: Orange
- Urgent: Red (with notification)

---

## Time Tracking

### Starting a Timer

**Manual Timer:**
1. Open a task
2. Click the timer icon
3. Timer starts automatically
4. Click "Stop" when done
5. Time entry saved to task

**Automatic Timer:**
1. Enable in Settings > Time Tracking
2. Timer starts when you open a task
3. Timer pauses when you switch tasks
4. Timer stops when you close the task

**Keyboard Shortcut:** Press 'T' to start/stop timer on current task

### Manual Time Entry

1. Open a task
2. Click "Add Time Entry"
3. Enter start time and end time
4. Or enter duration (e.g., "2h 30m")
5. Add notes (optional)
6. Mark as billable (if applicable)
7. Save entry

**Supported Formats:**
- Duration: "2h", "30m", "1h 45m", "90m"
- Time range: "9:00 AM - 11:30 AM"

### Editing Time Entries

1. Go to Time Tracking tab
2. Find the entry to edit
3. Click the edit icon
4. Modify time, notes, or billable status
5. Save changes

**Note:** Only admins and the entry creator can edit time entries.

### Time Reports

**View Time Reports:**
1. Go to Reports > Time Tracking
2. Select date range
3. Filter by:
   - Team member
   - Project
   - Task
   - Billable/Non-billable
4. Export to PDF, Excel, or CSV

**Report Metrics:**
- Total hours tracked
- Billable vs non-billable hours
- Hours by team member
- Hours by project
- Daily/weekly/monthly breakdown

---

## Team Collaboration

### Real-Time Chat

**Starting a Chat:**
1. Click the chat icon in the sidebar
2. Select team member or create group chat
3. Type your message
4. Press Enter to send

**Features:**
- @mentions to notify specific people
- File sharing (drag and drop)
- Emoji reactions
- Message editing and deletion
- Search chat history

### Video Calls

**Starting a Video Call:**
1. Open a chat or task
2. Click the video camera icon
3. Wait for participants to join
4. Share screen if needed

**Requirements:**
- Chrome, Firefox, or Safari browser
- Webcam and microphone
- Stable internet connection (minimum 1 Mbps)

**Features:**
- Up to 25 participants (Professional plan)
- Screen sharing
- Recording (saved to project files)
- Background blur

### Comments and @Mentions

**Adding Comments:**
1. Open a task or project
2. Scroll to comments section
3. Type your comment (supports Markdown)
4. @mention team members to notify them
5. Click "Comment" to post

**@Mention Notifications:**
- Desktop notification (if enabled)
- Email notification (if enabled)
- In-app notification badge

### File Sharing

**Uploading Files:**
1. Open a task or project
2. Click "Attach File" or drag and drop
3. Select file from computer
4. File uploads and attaches to task

**File Limits:**
- Free plan: 1GB total storage
- Starter plan: 10GB total storage
- Professional plan: 100GB total storage
- Enterprise plan: Unlimited storage
- Max file size: 100MB per file

**Supported File Types:** All file types supported

**Version Control:**
- Upload new version of existing file
- Previous versions saved for 30 days
- Download any version from file history

---

## Integrations

### Slack Integration

**Setup:**
1. Go to Settings > Integrations
2. Click "Connect Slack"
3. Authorize TaskFlow Pro in Slack
4. Select Slack channel for notifications

**Features:**
- Task notifications in Slack
- Create tasks from Slack messages
- Update task status from Slack
- Daily digest of tasks

**Commands:**
- `/taskflow create [task name]` - Create new task
- `/taskflow list` - List your tasks
- `/taskflow help` - Show available commands

### Google Workspace Integration

**Setup:**
1. Go to Settings > Integrations
2. Click "Connect Google"
3. Authorize TaskFlow Pro
4. Select which services to sync

**Features:**
- Sync with Google Calendar
- Attach Google Drive files to tasks
- Create tasks from Gmail
- Sign in with Google

### GitHub Integration

**Setup:**
1. Go to Settings > Integrations
2. Click "Connect GitHub"
3. Authorize TaskFlow Pro
4. Select repositories to sync

**Features:**
- Link tasks to GitHub issues
- Automatic task updates from commits
- Pull request status in tasks
- Branch creation from tasks

### API Access

**Getting Your API Key:**
1. Go to Settings > API
2. Click "Generate API Key"
3. Copy and save key securely
4. Use key in API requests

**API Documentation:** https://api.techcorp.com/docs

**Rate Limits:**
- Free: 100 requests/hour
- Starter: 1,000 requests/hour
- Professional: 10,000 requests/hour
- Enterprise: Unlimited

---

## Mobile Apps

### iOS App

**Download:** App Store - Search "TaskFlow Pro"

**Requirements:**
- iOS 14.0 or later
- iPhone, iPad, or iPod touch

**Features:**
- Full task management
- Time tracking with widget
- Offline mode (syncs when online)
- Push notifications
- Face ID / Touch ID login

### Android App

**Download:** Google Play Store - Search "TaskFlow Pro"

**Requirements:**
- Android 8.0 or later

**Features:**
- Full task management
- Time tracking with widget
- Offline mode (syncs when online)
- Push notifications
- Fingerprint login

### Offline Mode

**How It Works:**
- App downloads recent data when online
- You can view and edit tasks offline
- Changes sync automatically when back online
- Conflicts resolved automatically (last edit wins)

**Offline Limitations:**
- Cannot create new projects offline
- Cannot invite team members offline
- File uploads queued until online
- Video calls require internet connection

---

## Reporting & Analytics

### Project Dashboard

**Accessing Dashboard:**
1. Open any project
2. Click "Dashboard" tab
3. View real-time metrics

**Metrics Displayed:**
- Tasks completed vs remaining
- Team member workload
- Project progress (%)
- Upcoming deadlines
- Time spent on project
- Budget tracking (if enabled)

### Custom Reports

**Creating Custom Reports:**
1. Go to Reports > Custom Reports
2. Click "New Report"
3. Select data source (tasks, time, team)
4. Choose metrics and dimensions
5. Apply filters
6. Save report

**Available Metrics:**
- Task completion rate
- Average time to complete
- Team productivity
- Project velocity
- Budget vs actual
- Customer satisfaction (if using feedback feature)

### Exporting Reports

**Export Options:**
- PDF (formatted for printing)
- Excel (with formulas)
- CSV (raw data)
- Google Sheets (live sync)

**Scheduled Reports (Professional plan):**
- Set up automatic report generation
- Email reports daily, weekly, or monthly
- Share with team or stakeholders

---

## Troubleshooting

### Login Issues

**Cannot log in:**
- Verify email and password are correct
- Check Caps Lock is off
- Try password reset
- Clear browser cache and cookies
- Try incognito/private browsing mode
- Check if account is locked (5 failed attempts = 15 min lockout)

**Two-Factor Authentication Issues:**
- Ensure device time is synchronized
- Try backup codes (saved during 2FA setup)
- Contact support to disable 2FA temporarily

### Performance Issues

**App is slow:**
- Check internet connection speed
- Close unnecessary browser tabs
- Clear browser cache
- Disable browser extensions temporarily
- Try different browser (Chrome recommended)
- Check status.techcorp.com for service issues

**Tasks not loading:**
- Refresh the page (F5 or Cmd+R)
- Check internet connection
- Try logging out and back in
- Clear browser cache
- Check if project was deleted or archived

### Integration Issues

**Slack notifications not working:**
- Verify Slack integration is connected
- Check notification settings in TaskFlow Pro
- Check Slack channel permissions
- Reconnect integration (disconnect and reconnect)

**Google Calendar sync issues:**
- Verify Google integration is authorized
- Check calendar permissions
- Refresh sync (Settings > Integrations > Refresh)
- Disconnect and reconnect integration

### Mobile App Issues

**App crashes:**
- Update to latest version
- Restart device
- Clear app cache (Settings > Apps > TaskFlow Pro > Clear Cache)
- Reinstall app (data will sync from cloud)

**Sync not working:**
- Check internet connection
- Force sync (pull down to refresh)
- Log out and log back in
- Check storage space on device

### Data Issues

**Missing tasks or projects:**
- Check if filtered or archived
- Check if you have permission to view
- Check if project was deleted (admins can restore within 30 days)
- Contact support with task/project ID

**Incorrect time entries:**
- Check timezone settings (Settings > Account > Timezone)
- Verify time entry details
- Edit or delete incorrect entries
- Contact support if entries cannot be edited

---

## API Documentation

### Authentication

**API Key Authentication:**
```
Authorization: Bearer YOUR_API_KEY
```

**OAuth 2.0 (Enterprise only):**
- Authorization endpoint: https://api.techcorp.com/oauth/authorize
- Token endpoint: https://api.techcorp.com/oauth/token

### Common Endpoints

**Get Tasks:**
```
GET /api/v1/tasks
Query params: project_id, assignee_id, status, limit, offset
```

**Create Task:**
```
POST /api/v1/tasks
Body: {
  "title": "Task title",
  "description": "Task description",
  "project_id": "project-uuid",
  "assignee_id": "user-uuid",
  "due_date": "2026-02-20",
  "priority": "high"
}
```

**Update Task:**
```
PATCH /api/v1/tasks/{task_id}
Body: { "status": "done" }
```

**Delete Task:**
```
DELETE /api/v1/tasks/{task_id}
```

**Full API Documentation:** https://api.techcorp.com/docs

---

## Support

**Need more help?**
- Email: support@techcorp.com
- WhatsApp: +1-415-555-0199
- Help Center: help.techcorp.com
- Status Page: status.techcorp.com
- Community Forum: community.techcorp.com

**Response Times:**
- Free plan: 48 hours
- Starter plan: 24 hours
- Professional plan: 12 hours
- Enterprise plan: 4 hours (with SLA)

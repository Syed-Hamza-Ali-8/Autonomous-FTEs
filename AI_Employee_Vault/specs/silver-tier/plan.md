# Implementation Plan: Silver Tier - Functional AI Assistant

**Branch**: `silver-tier` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/silver-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Silver tier transforms the Bronze tier file processing system into a functional AI assistant that monitors multiple communication channels (Gmail, WhatsApp, LinkedIn), creates intelligent plans for complex tasks, and executes approved actions through external services. The system implements human-in-the-loop approval for sensitive actions, scheduled automation, and LinkedIn business posting capabilities. All AI functionality is implemented as Agent Skills following the Perception → Reasoning → Action architecture pattern.

**Key Capabilities**:
- Multi-channel communication monitoring (Gmail, WhatsApp, LinkedIn)
- Human-in-the-loop approval workflow for sensitive actions
- Automated LinkedIn business posting with approval
- Claude reasoning loop creating structured Plan.md files
- External action execution through MCP server integration
- Scheduled watcher execution via cron/Task Scheduler
- All functionality implemented as Agent Skills

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- Core: watchdog>=4.0.0, pyyaml>=6.0.1, requests>=2.31.0, python-dotenv>=1.0.0 (from Bronze)
- Gmail: google-auth, google-auth-oauthlib, google-api-python-client
- WhatsApp: playwright (for WhatsApp Web automation)
- LinkedIn: linkedin-api or requests (for LinkedIn API)
- Scheduling: schedule (Python) or system cron/Task Scheduler
- MCP: Node.js v24+ LTS for MCP server implementation

**Storage**: Local Obsidian vault (markdown files with YAML frontmatter)
- `/Inbox` - New files to process
- `/Needs_Action` - Files requiring AI processing
- `/Pending_Approval` - Actions awaiting human approval
- `/Approved` - Approved actions ready for execution
- `/Rejected` - Rejected actions with reasons
- `/Done` - Completed files and actions
- `/Plans` - Structured Plan.md files for complex tasks
- `/Logs` - Daily JSON audit logs (YYYY-MM-DD.json)

**Testing**:
- Manual end-to-end testing (Bronze tier level)
- Integration testing for MCP servers
- HITL approval workflow testing
- Multi-watcher coordination testing
- Scheduled execution testing

**Target Platform**: Linux/Windows (WSL support), macOS
**Project Type**: Single project with multiple watchers and Agent Skills
**Performance Goals**:
- Gmail watcher: detect messages within 5 minutes
- WhatsApp watcher: detect messages within 5 minutes
- LinkedIn watcher: detect messages within 15 minutes
- Approval requests: presented within 1 minute
- LinkedIn posts: published within 5 minutes of approval
- Plan.md generation: within 2 minutes for typical tasks

**Constraints**:
- Local-first architecture (all data in Obsidian vault)
- Privacy-focused (no external API calls except Claude Code and approved integrations)
- HITL required for all sensitive actions (emails, posts, payments)
- Credentials stored securely (.env, environment variables, OS credential managers)
- Watchers must be lightweight (minimal resource consumption)
- System must handle network interruptions gracefully

**Scale/Scope**:
- 2+ communication channels monitored simultaneously
- Continuous operation for 7+ days without manual intervention (excluding approvals)
- 95% message detection rate across all channels
- 100% approval compliance for sensitive actions
- Support for multiple concurrent approval requests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Local-First & Privacy (NON-NEGOTIABLE)
- **Status**: COMPLIANT
- **Evidence**: All data stored in local Obsidian vault. External API calls limited to Claude Code, Gmail API, WhatsApp Web, LinkedIn API (all explicitly approved). Credentials stored in .env files (gitignored).
- **Action**: None required

### ✅ II. Agent Skills Mandatory (NON-NEGOTIABLE)
- **Status**: COMPLIANT
- **Evidence**: All AI functionality implemented as Agent Skills:
  - Communication monitoring skill
  - HITL approval skill
  - LinkedIn posting skill
  - Planning/reasoning skill
  - External action execution skill
- **Action**: None required

### ✅ III. Human-in-the-Loop (HITL) for Sensitive Actions
- **Status**: COMPLIANT
- **Evidence**: HITL approval workflow is a P1 (highest priority) user story. All sensitive actions (emails, posts, payments) require explicit approval. File-based approval system using `/Pending_Approval`, `/Approved`, `/Rejected` folders.
- **Action**: None required

### ✅ IV. Tiered Development Approach
- **Status**: COMPLIANT
- **Evidence**: Bronze tier is 100% complete. Silver tier builds on Bronze foundation with all required features: multiple watchers, HITL, LinkedIn posting, Plan.md creation, MCP server, scheduling.
- **Action**: None required

### ✅ V. Security & Credential Management
- **Status**: COMPLIANT
- **Evidence**: Credentials stored in .env files (gitignored). Environment variables for API keys. Dry-run mode for development. No credentials in code or vault.
- **Action**: Create .env.example template with required credentials

### ✅ VI. Audit Logging & Observability
- **Status**: COMPLIANT
- **Evidence**: JSON logging format specified in spec (FR-029, FR-036). Logs stored in `/Logs/YYYY-MM-DD.json`. All actions logged with timestamp, actor, target, approval status, result.
- **Action**: None required

### ✅ VII. Error Recovery & Graceful Degradation
- **Status**: COMPLIANT
- **Evidence**: Error handling specified in spec (FR-008, FR-030, FR-031, FR-034). Retry logic with exponential backoff. Graceful handling of authentication failures, rate limits, network interruptions.
- **Action**: None required

### ✅ Perception → Reasoning → Action Pattern
- **Status**: COMPLIANT
- **Evidence**: Architecture follows pattern:
  - Perception: Gmail/WhatsApp/LinkedIn watchers
  - Reasoning: Claude Code creates Plan.md files, analyzes actions
  - Action: MCP server executes approved actions
- **Action**: None required

**GATE RESULT**: ✅ PASSED - All constitution requirements met. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/silver-tier/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── watcher-api.md   # Watcher interface contracts
│   ├── approval-api.md  # HITL approval workflow contracts
│   └── mcp-api.md       # MCP server contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
silver/                          # Silver tier implementation
├── src/
│   ├── watchers/                # Communication channel watchers
│   │   ├── base_watcher.py     # Abstract base class for all watchers
│   │   ├── gmail_watcher.py    # Gmail monitoring
│   │   ├── whatsapp_watcher.py # WhatsApp Web monitoring
│   │   └── linkedin_watcher.py # LinkedIn monitoring
│   ├── approval/                # HITL approval workflow
│   │   ├── approval_manager.py # Approval request creation and tracking
│   │   ├── approval_checker.py # Check for user responses
│   │   └── approval_notifier.py # Notify user of pending approvals
│   ├── planning/                # Claude reasoning and planning
│   │   ├── plan_generator.py   # Create structured Plan.md files
│   │   ├── task_analyzer.py    # Analyze complex tasks
│   │   └── plan_tracker.py     # Track plan execution status
│   ├── actions/                 # External action execution
│   │   ├── action_executor.py  # Execute approved actions
│   │   ├── email_sender.py     # Send emails via MCP
│   │   └── linkedin_poster.py  # Post to LinkedIn
│   ├── scheduling/              # Scheduled execution
│   │   ├── scheduler.py         # Schedule watcher execution
│   │   └── cron_config.py       # Cron/Task Scheduler configuration
│   └── utils/                   # Shared utilities (from Bronze)
│       ├── file_utils.py
│       ├── yaml_parser.py
│       ├── logger.py
│       ├── dashboard_updater.py
│       └── obsidian_api.py
├── mcp/                         # MCP server implementation
│   ├── email-server/            # Email MCP server (Node.js)
│   │   ├── package.json
│   │   ├── index.js
│   │   └── README.md
│   └── README.md
├── config/
│   ├── .env.example             # Template for credentials
│   ├── watcher_config.yaml      # Watcher configuration
│   └── approval_rules.yaml      # HITL approval rules
├── tests/
│   ├── integration/
│   │   ├── test_watchers.py
│   │   ├── test_approval_workflow.py
│   │   ├── test_mcp_integration.py
│   │   └── test_scheduling.py
│   └── unit/
│       ├── test_gmail_watcher.py
│       ├── test_approval_manager.py
│       └── test_plan_generator.py
├── scripts/
│   ├── setup_credentials.sh     # Interactive credential setup
│   ├── start_watchers.sh        # Start all watchers
│   └── setup_scheduling.sh      # Configure cron/Task Scheduler
├── pyproject.toml               # Python dependencies
└── README.md                    # Silver tier documentation

.claude/                         # Agent Skills (project root)
└── skills/
    ├── process-files/           # Bronze tier skill (existing)
    ├── monitor-communications/  # Silver tier: Multi-channel monitoring
    ├── manage-approvals/        # Silver tier: HITL approval workflow
    ├── post-linkedin/           # Silver tier: LinkedIn posting
    ├── create-plans/            # Silver tier: Plan.md generation
    └── execute-actions/         # Silver tier: External action execution
```

**Structure Decision**: Single project structure with clear separation of concerns. Silver tier implementation lives in `/silver` directory alongside Bronze tier (`/bronze`). Agent Skills are in project root `.claude/skills/` as required by constitution. MCP server is Node.js-based in `/silver/mcp/email-server/`. This structure supports incremental development, clear module boundaries, and easy testing.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution requirements are met.

## Phase 0: Research & Technology Decisions

### Research Tasks

The following unknowns need research before detailed design:

1. **Gmail API Integration**
   - Research: Best practices for Gmail API authentication (OAuth2 flow)
   - Research: Gmail API rate limits and quota management
   - Research: Efficient message filtering (labels, queries)
   - Decision needed: OAuth2 vs IMAP for email monitoring

2. **WhatsApp Web Automation**
   - Research: Playwright vs Selenium for WhatsApp Web automation
   - Research: WhatsApp Web session persistence and authentication
   - Research: Message extraction patterns and selectors
   - Decision needed: Web automation vs WhatsApp Business API

3. **LinkedIn API Integration**
   - Research: LinkedIn API authentication and permissions
   - Research: LinkedIn posting API endpoints and rate limits
   - Research: LinkedIn messaging API capabilities
   - Decision needed: Official API vs unofficial linkedin-api library

4. **MCP Server Implementation**
   - Research: MCP protocol specification and best practices
   - Research: Email sending via MCP (SMTP vs API)
   - Research: MCP server deployment and lifecycle management
   - Decision needed: Custom MCP server vs existing email MCP server

5. **Scheduling Strategy**
   - Research: Python schedule library vs system cron
   - Research: Cross-platform scheduling (Linux cron vs Windows Task Scheduler)
   - Research: Process management (PM2, supervisord, systemd)
   - Decision needed: Python-based vs system-based scheduling

6. **HITL Approval Workflow**
   - Research: File-based approval patterns
   - Research: Notification mechanisms (desktop notifications, email, Obsidian)
   - Research: Timeout and expiration handling
   - Decision needed: Polling vs event-driven approval checking

7. **Agent Skills Architecture**
   - Research: Claude Agent Skills best practices
   - Research: Skill composition and reusability patterns
   - Research: Error handling and logging in skills
   - Decision needed: Monolithic skills vs granular skills

### Output

Research findings will be documented in `research.md` with:
- Decision: What was chosen
- Rationale: Why chosen
- Alternatives considered: What else was evaluated
- Trade-offs: Pros and cons of the decision

## Phase 1: Design & Contracts

### Data Model

Key entities to be designed in `data-model.md`:

1. **Watcher** - Monitoring script configuration and state
2. **Message** - Communication from monitored channels
3. **ApprovalRequest** - Pending action requiring human approval
4. **Plan** - Structured plan for complex tasks
5. **Action** - External action to be executed
6. **Schedule** - Watcher execution schedule configuration
7. **AuditLog** - Record of all system actions

### API Contracts

Contracts to be defined in `/contracts`:

1. **watcher-api.md** - Watcher interface contracts
   - `check_for_updates()` - Return list of new items
   - `create_action_file(item)` - Create action file in Needs_Action
   - `run()` - Main watcher loop

2. **approval-api.md** - HITL approval workflow contracts
   - `create_approval_request(action)` - Create approval request
   - `check_approval_status(request_id)` - Check if approved/rejected
   - `execute_approved_action(request_id)` - Execute after approval

3. **mcp-api.md** - MCP server contracts
   - Email sending endpoints
   - Error handling and retry logic
   - Authentication and authorization

### Quickstart Guide

`quickstart.md` will provide:
- Prerequisites and dependencies
- Credential setup instructions
- Watcher configuration
- First-time setup walkthrough
- Testing and verification steps

## Phase 2: Task Breakdown

Task breakdown will be created by `/sp.tasks` command (not part of this plan).

## Next Steps

1. ✅ Constitution Check passed
2. 🔄 Phase 0: Create `research.md` with technology decisions
3. ⏳ Phase 1: Create `data-model.md`, `/contracts`, `quickstart.md`
4. ⏳ Phase 1: Update agent context with new technologies
5. ⏳ Phase 2: Run `/sp.tasks` to create task breakdown

## Notes

**Security Considerations**:
- Gmail OAuth2 tokens must be stored securely and refreshed automatically
- WhatsApp Web session cookies must be encrypted
- LinkedIn API credentials must use environment variables
- MCP server must validate all inputs to prevent injection attacks
- Approval workflow must be tamper-proof (no bypassing HITL)

**Performance Considerations**:
- Watchers should use efficient polling intervals (5-15 minutes)
- Message deduplication to prevent processing same message twice
- Approval checking should be event-driven, not polling-based
- Plan generation should be asynchronous to avoid blocking

**User Experience Considerations**:
- Approval notifications should be clear and actionable
- Error messages should suggest remediation steps
- Dashboard should show real-time status of all watchers
- Logs should be human-readable for debugging

**Testing Strategy**:
- Unit tests for each watcher independently
- Integration tests for approval workflow end-to-end
- Integration tests for MCP server communication
- Manual testing for scheduled execution
- Dry-run mode for all external actions during development

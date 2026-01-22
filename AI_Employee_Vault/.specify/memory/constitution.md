# AI Employee Vault Constitution

## Core Principles

### I. Local-First & Privacy (NON-NEGOTIABLE)
**All data must remain local by default. Privacy is paramount.**

- All personal and business data stored in local Obsidian vault
- No external API calls except Claude Code reasoning engine
- Credentials never stored in plain text (use .env, environment variables, or OS credential managers)
- Encryption at rest recommended for sensitive data
- Third-party integrations must be explicitly approved and documented

**Rationale:** Users must maintain full control over their personal and business data. Local-first architecture ensures privacy, reduces attack surface, and enables offline operation.

### II. Agent Skills Mandatory (NON-NEGOTIABLE)
**All AI functionality must be implemented as Claude Agent Skills, not standalone scripts.**

- Every automation workflow must be a proper Agent Skill
- Skills must be documented with clear purpose and usage
- Skills must be composable and reusable
- No "one-off" scripts that bypass the Agent Skills framework

**Rationale:** Agent Skills provide structure, maintainability, and integration with Claude Code's ecosystem. They enable better error handling, logging, and human oversight.

### III. Human-in-the-Loop (HITL) for Sensitive Actions
**Autonomous does not mean unsupervised. Critical actions require human approval.**

**Auto-Approve Thresholds:**
- Email replies to known contacts
- Payments < $50 to recurring payees
- Scheduled social media posts (pre-approved)
- File operations within vault (create, read, update)

**Always Require Approval:**
- Emails to new contacts or bulk sends
- All payments to new payees or > $100
- Social media replies, DMs, or unscheduled posts
- File deletions or moves outside vault
- Any irreversible action

**Implementation:** File-based approval system using `/Pending_Approval`, `/Approved`, `/Rejected` folders.

### IV. Tiered Development Approach
**Build incrementally: Bronze → Silver → Gold. Each tier must be complete before advancing.**

**Bronze Tier (Foundation):**
- Obsidian vault with Dashboard.md and Company_Handbook.md
- Basic folder structure: /Inbox, /Needs_Action, /Done, /Logs
- One working Watcher (File System OR Gmail)
- Claude Code reading/writing vault
- One Agent Skill for file processing

**Silver Tier (Functional Assistant):**
- All Bronze requirements
- Multiple Watchers (Gmail + WhatsApp + LinkedIn)
- Auto-posting on LinkedIn for business
- Claude reasoning loop creating Plan.md files
- One MCP server (email sending)
- HITL approval workflow
- Basic scheduling (cron/Task Scheduler)

**Gold Tier (Autonomous Employee):**
- All Silver requirements
- Full cross-domain integration (Personal + Business)
- Odoo Community accounting integration (self-hosted, local) with MCP server using Odoo's JSON-RPC APIs (Odoo 19+)
- Facebook and Instagram integration with posting and summary generation
- Twitter (X) integration with posting and summary generation
- Multiple MCP servers for different action types
- Weekly Business and Accounting Audit with CEO Briefing generation
- Error recovery & graceful degradation
- Comprehensive audit logging (90-day retention)
- Ralph Wiggum loop for autonomous multi-step task completion
- All AI functionality implemented as Agent Skills
- Comprehensive documentation and architecture guides

**Rationale:** Incremental development ensures solid foundations, reduces risk, and provides clear milestones.

### V. Security & Credential Management
**Security is non-negotiable. Credentials must be protected at all costs.**

**Requirements:**
- Use `.env` files (add to `.gitignore` immediately)
- Environment variables for API keys
- OS credential managers for banking/sensitive credentials
- Rotate credentials monthly
- Never commit credentials to version control
- Implement dry-run mode for all external actions during development

**Credential Storage Hierarchy:**
1. OS Credential Manager (preferred for banking)
2. Environment variables (for API keys)
3. `.env` file (for development, never committed)
4. Never: Plain text in code or vault

### VI. Audit Logging & Observability
**Every action must be logged. Transparency enables trust and debugging.**

**Required Log Format:**
```json
{
  "timestamp": "ISO-8601",
  "action_type": "email_send|payment|file_operation|etc",
  "actor": "claude_code|watcher|human",
  "target": "recipient/file/resource",
  "parameters": {},
  "approval_status": "auto|approved|rejected",
  "approved_by": "human|system",
  "result": "success|failure|pending"
}
```

**Log Storage:**
- Location: `/Logs/YYYY-MM-DD.json`
- Retention: Minimum 90 days
- No sensitive data in logs (mask credentials, PII)

### VII. Error Recovery & Graceful Degradation
**Systems fail. Plan for it. Degrade gracefully, never catastrophically.**

**Error Categories:**
- **Transient:** Network timeout, API rate limit → Exponential backoff retry
- **Authentication:** Expired token → Alert human, pause operations
- **Logic:** Misinterpretation → Human review queue
- **Data:** Corrupted file → Quarantine + alert
- **System:** Crash, disk full → Watchdog + auto-restart

**Graceful Degradation:**
- Gmail API down → Queue emails locally
- Banking API timeout → Never retry payments automatically
- Claude Code unavailable → Watchers continue collecting
- Obsidian vault locked → Write to temp folder, sync later

## Architecture Standards

### Perception → Reasoning → Action Pattern
**All workflows must follow this three-stage pattern:**

1. **Perception (Watchers):** Lightweight Python scripts monitor inputs
   - Gmail Watcher (important/unread emails)
   - WhatsApp Watcher (urgent keywords)
   - File System Watcher (dropped files)
   - Finance Watcher (bank transactions)

2. **Reasoning (Claude Code):** Process inputs and create plans
   - Read from `/Needs_Action`
   - Consult `Company_Handbook.md` for rules
   - Create `Plan.md` with checkboxes
   - Request approval for sensitive actions

3. **Action (MCP Servers):** Execute approved actions
   - Email MCP (send, draft, search)
   - Browser MCP (navigate, click, fill forms)
   - Calendar MCP (create, update events)
   - Social Media MCP (post, reply)

### Technology Stack
**Required:**
- **Vault:** Obsidian (local markdown)
- **Reasoning:** Claude Code (Sonnet 4.5 or via Router)
- **Watchers:** Python 3.13+
- **MCP Servers:** Node.js v24+ LTS
- **Version Control:** Git + GitHub Desktop
- **Skills:** Claude Agent Skills framework

**Optional (Gold Tier):**
- **Process Manager:** PM2 or supervisord
- **Accounting:** Xero with MCP server
- **Persistence:** Ralph Wiggum loop

## Development Workflow

### Feature Development Process
1. **Specify:** Create spec.md in `/specs/<feature>/`
2. **Plan:** Create plan.md with architecture decisions
3. **Tasks:** Break down into testable tasks in tasks.md
4. **Implement:** Build incrementally, test continuously
5. **Document:** Update Dashboard.md and logs
6. **Review:** Manual testing against acceptance criteria

### Testing Requirements
**Bronze Tier:**
- Manual end-to-end testing
- File drop → Detection → Processing → Completion

**Silver Tier:**
- Integration testing for MCP servers
- HITL approval workflow testing
- Multi-Watcher coordination testing

**Gold Tier:**
- Error recovery testing (simulate failures)
- Load testing (multiple concurrent actions)
- Security testing (credential exposure, injection attacks)

### Code Quality Standards
- **Python:** Follow PEP 8, type hints required
- **JavaScript/Node:** ESLint, async/await patterns
- **Markdown:** Consistent frontmatter, clear headings
- **Agent Skills:** Documented purpose, inputs, outputs, error handling

## Submission Requirements

### Deliverables
1. **GitHub Repository** (public or private with judge access)
2. **README.md** with setup instructions and architecture overview
3. **Demo Video** (5-10 minutes) showing key features
4. **Security Disclosure** documenting credential handling
5. **Tier Declaration** (Bronze, Silver, or Gold)

### Judging Criteria
- **Functionality (30%):** Does it work? Core features complete?
- **Innovation (25%):** Creative solutions, novel integrations
- **Practicality (20%):** Would you use this daily?
- **Security (15%):** Proper credential handling, HITL safeguards
- **Documentation (10%):** Clear README, setup, demo

## Governance

### Constitution Authority
- This constitution supersedes all other development practices
- All features must comply with core principles
- Violations must be documented and justified
- Amendments require documentation and approval

### Compliance Verification
- Every PR/commit must verify compliance with principles
- Security requirements are non-negotiable
- HITL thresholds cannot be relaxed without explicit approval
- Agent Skills framework cannot be bypassed

### Amendment Process
1. Propose amendment with rationale
2. Document impact on existing features
3. Create migration plan if needed
4. Update constitution version
5. Notify all stakeholders

**Version**: 1.0.0 | **Ratified**: 2026-01-12 | **Last Amended**: 2026-01-12

# Research & Technology Decisions: Silver Tier

**Feature**: Silver Tier - Functional AI Assistant
**Date**: 2026-01-13
**Status**: Complete

## Overview

This document captures research findings and technology decisions for Silver tier implementation. Each decision includes rationale, alternatives considered, and trade-offs.

---

## 1. Gmail API Integration

### Decision: Gmail API with OAuth2

**Rationale**:
- Official Google API with comprehensive documentation
- OAuth2 provides secure, token-based authentication with automatic refresh
- Supports advanced filtering (labels, queries, metadata)
- Better rate limits than IMAP (250 quota units per user per second)
- Enables future features (send emails, manage labels, search)

**Alternatives Considered**:
- **IMAP**: Simpler protocol, but limited filtering capabilities, no structured metadata, slower for large mailboxes
- **Gmail API with Service Account**: Not suitable for personal email access (requires domain-wide delegation)

**Trade-offs**:
- **Pros**: Secure, feature-rich, well-documented, good rate limits
- **Cons**: Requires OAuth2 consent flow (one-time setup), more complex initial setup than IMAP
- **Mitigation**: Provide setup script for OAuth2 flow, store tokens securely in .env

**Implementation Notes**:
- Use `google-auth`, `google-auth-oauthlib`, `google-api-python-client` libraries
- Store OAuth2 tokens in `.env` file (gitignored)
- Implement automatic token refresh
- Use `q` parameter for efficient filtering: `is:unread is:important`
- Check for new messages every 5 minutes (well within rate limits)

---

## 2. WhatsApp Web Automation

### Decision: Playwright for WhatsApp Web Automation

**Rationale**:
- Modern, actively maintained browser automation framework
- Better performance than Selenium (faster startup, lower resource usage)
- Built-in waiting and retry mechanisms
- Supports headless mode for background operation
- Cross-platform (Linux, Windows, macOS)
- WhatsApp Business API requires business verification and has costs

**Alternatives Considered**:
- **Selenium**: Older, more verbose API, slower performance
- **WhatsApp Business API**: Official API but requires business verification, monthly costs, and is overkill for personal use
- **Unofficial WhatsApp libraries**: Risk of account ban, unstable APIs

**Trade-offs**:
- **Pros**: Free, works with personal WhatsApp, no verification needed, full control
- **Cons**: Requires WhatsApp Web session (QR code scan), fragile to WhatsApp UI changes, risk of account restrictions if detected as bot
- **Mitigation**: Use human-like delays, limit check frequency to 5 minutes, store session persistently, provide clear setup instructions

**Implementation Notes**:
- Use `playwright` library with Chromium browser
- Store session data in persistent directory (not in vault)
- Implement selector-based message extraction with fallbacks
- Use `page.wait_for_selector()` for reliable element detection
- Limit to checking for new messages only (no sending via web automation)
- Provide clear warning about WhatsApp Terms of Service

---

## 3. LinkedIn API Integration

### Decision: Official LinkedIn API for Posting, Unofficial linkedin-api for Messaging

**Rationale**:
- **Posting**: Official LinkedIn API supports posting with proper authentication and rate limits
- **Messaging**: Official API has very limited messaging access (requires partnership), unofficial `linkedin-api` library provides practical solution
- Hybrid approach balances official support for critical features (posting) with practical needs (messaging)

**Alternatives Considered**:
- **Official API only**: Limited messaging capabilities, requires LinkedIn partnership for full access
- **Unofficial library only**: Risk of account restrictions, no official support, but works for both posting and messaging
- **Selenium/Playwright automation**: Too fragile, high risk of account ban

**Trade-offs**:
- **Pros**: Official API for posting is stable and supported, unofficial library fills gaps
- **Cons**: Unofficial library may break with LinkedIn changes, risk of account restrictions
- **Mitigation**: Use official API where possible, implement graceful degradation if unofficial library fails, respect rate limits strictly

**Implementation Notes**:
- Use official LinkedIn API for posting: `POST /ugcPosts` endpoint
- Use `linkedin-api` library for message monitoring (if needed)
- Store LinkedIn credentials in environment variables
- Implement rate limiting: max 1 post per day (per spec FR-021)
- Require HITL approval for all posts (per spec FR-018)
- Provide clear documentation about API limitations and risks

---

## 4. MCP Server Implementation

### Decision: Custom Email MCP Server using Nodemailer

**Rationale**:
- No existing email MCP server meets our needs (most are read-only or Gmail-specific)
- Custom server provides full control over email sending logic
- Nodemailer is mature, well-documented, supports SMTP and API-based sending
- MCP protocol is straightforward to implement in Node.js
- Enables future expansion (calendar, other services)

**Alternatives Considered**:
- **Existing Gmail MCP server**: Read-only, doesn't support sending
- **Direct SMTP in Python**: Bypasses MCP architecture, violates constitution requirement for external actions
- **Third-party email API (SendGrid, Mailgun)**: Adds external dependency, costs, and privacy concerns

**Trade-offs**:
- **Pros**: Full control, privacy-preserving (direct SMTP), no external services, extensible
- **Cons**: Need to implement MCP protocol, maintain server code, handle SMTP configuration
- **Mitigation**: Use MCP SDK for protocol handling, provide clear SMTP setup guide, support multiple providers (Gmail, Outlook, custom SMTP)

**Implementation Notes**:
- Implement in Node.js v24+ LTS
- Use `@modelcontextprotocol/sdk` for MCP protocol
- Use `nodemailer` for email sending
- Support SMTP configuration via environment variables
- Implement retry logic with exponential backoff (per spec FR-031)
- Log all send attempts to audit log (per spec FR-029)
- Run as background process (PM2 or systemd)

---

## 5. Scheduling Strategy

### Decision: Python `schedule` Library with Systemd/PM2 Process Management

**Rationale**:
- Python `schedule` library is simple, Pythonic, and integrates well with watcher code
- Cross-platform (works on Linux, Windows, macOS)
- Easier to manage than system cron (no crontab editing, configuration in code)
- Systemd (Linux) or PM2 (cross-platform) provides process management and auto-restart
- Keeps all scheduling logic in Python codebase (easier to maintain)

**Alternatives Considered**:
- **System cron (Linux) / Task Scheduler (Windows)**: Platform-specific, requires separate configuration, harder to debug
- **APScheduler**: More complex than needed, overkill for simple interval-based scheduling
- **Celery**: Requires message broker (Redis/RabbitMQ), too heavy for this use case

**Trade-offs**:
- **Pros**: Simple, Pythonic, cross-platform, easy to configure, integrates with Python code
- **Cons**: Requires process manager for reliability, not as battle-tested as system cron
- **Mitigation**: Use systemd/PM2 for auto-restart, implement health checks, log all executions

**Implementation Notes**:
- Use `schedule` library: `schedule.every(5).minutes.do(gmail_watcher.run)`
- Create main scheduler script that runs all watchers
- Configure intervals in YAML file: `watcher_config.yaml`
- Use systemd service (Linux) or PM2 (cross-platform) for process management
- Implement graceful shutdown on SIGTERM
- Log all scheduled executions with timestamp (per spec FR-036)
- Provide setup scripts for systemd and PM2

---

## 6. HITL Approval Workflow

### Decision: File-Based Polling with Desktop Notifications

**Rationale**:
- File-based approval aligns with Obsidian vault architecture
- Polling is simple, reliable, and doesn't require event infrastructure
- Desktop notifications provide immediate user awareness
- Obsidian can be used to review and approve (edit YAML frontmatter)
- No external dependencies or services required

**Alternatives Considered**:
- **Event-driven (watchdog)**: More complex, requires file system events, potential race conditions
- **Web interface**: Requires web server, adds complexity, not aligned with local-first principle
- **Email notifications**: Requires email sending (circular dependency), less immediate than desktop notifications

**Trade-offs**:
- **Pros**: Simple, reliable, integrates with Obsidian, no external dependencies
- **Cons**: Polling has slight delay (check every 30 seconds), not real-time
- **Mitigation**: Use 30-second polling interval for responsiveness, implement desktop notifications for immediate awareness

**Implementation Notes**:
- Create approval request files in `/Pending_Approval` folder
- YAML frontmatter structure:
  ```yaml
  ---
  type: approval_request
  action_type: email_send|linkedin_post|payment
  created: ISO-8601 timestamp
  expires: ISO-8601 timestamp (24 hours)
  status: pending|approved|rejected
  approved_by: null|human
  approved_at: null|ISO-8601 timestamp
  ---
  ```
- Poll `/Pending_Approval` every 30 seconds
- Use `plyer` library for cross-platform desktop notifications
- Move approved requests to `/Approved`, rejected to `/Rejected`
- Timeout after 24 hours (per spec FR-015)
- Log all approval decisions (per spec FR-014)

---

## 7. Agent Skills Architecture

### Decision: Granular Skills with Shared Utilities

**Rationale**:
- Granular skills are more reusable and composable
- Each skill has single responsibility (easier to test and maintain)
- Shared utilities avoid code duplication
- Aligns with Claude Agent Skills best practices
- Enables incremental development and testing

**Alternatives Considered**:
- **Monolithic skills**: Single skill for all Silver tier functionality - too complex, hard to test, violates single responsibility
- **Micro-skills**: One skill per function - too granular, overhead of many small skills

**Trade-offs**:
- **Pros**: Reusable, testable, maintainable, composable, clear boundaries
- **Cons**: More files to manage, need to coordinate between skills
- **Mitigation**: Use shared utilities for common code, clear documentation for each skill, consistent error handling

**Implementation Notes**:
- Create 5 Agent Skills for Silver tier:
  1. `monitor-communications` - Multi-channel watcher orchestration
  2. `manage-approvals` - HITL approval workflow
  3. `post-linkedin` - LinkedIn posting with approval
  4. `create-plans` - Plan.md generation
  5. `execute-actions` - External action execution via MCP
- Each skill has:
  - `SKILL.md` - Documentation (purpose, usage, inputs, outputs)
  - `skill.py` - Implementation with error handling
- Shared utilities in `/silver/src/utils/` (reuse from Bronze where possible)
- Consistent error handling: log errors, return structured error responses
- Each skill logs to audit log with action type and result

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Language** | Python | 3.13+ | Existing Bronze tier, mature ecosystem |
| **Gmail** | Gmail API | v1 | Official API, OAuth2, good rate limits |
| **WhatsApp** | Playwright | Latest | Modern automation, better than Selenium |
| **LinkedIn** | Official API + linkedin-api | Latest | Hybrid approach for posting + messaging |
| **MCP Server** | Node.js + Nodemailer | v24 LTS | Custom server, full control, privacy |
| **Scheduling** | schedule library | Latest | Simple, Pythonic, cross-platform |
| **Process Mgmt** | systemd / PM2 | Latest | Auto-restart, reliability |
| **Notifications** | plyer | Latest | Cross-platform desktop notifications |
| **Approval** | File-based polling | N/A | Simple, reliable, Obsidian-integrated |
| **Agent Skills** | Claude Agent Skills | N/A | Granular, reusable, composable |

---

## Dependencies to Add

### Python (pyproject.toml)
```toml
[project]
dependencies = [
    # Bronze tier (existing)
    "watchdog>=4.0.0",
    "pyyaml>=6.0.1",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",

    # Silver tier (new)
    "google-auth>=2.27.0",
    "google-auth-oauthlib>=1.2.0",
    "google-api-python-client>=2.115.0",
    "playwright>=1.41.0",
    "linkedin-api>=2.2.0",
    "schedule>=1.2.0",
    "plyer>=2.1.0",
]
```

### Node.js (mcp/email-server/package.json)
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest",
    "nodemailer": "^6.9.0"
  }
}
```

---

## Security Considerations

1. **Credentials Storage**:
   - Gmail OAuth2 tokens: `.env` file (gitignored)
   - WhatsApp session: Persistent directory outside vault
   - LinkedIn API keys: Environment variables
   - SMTP credentials: Environment variables

2. **Credential Rotation**:
   - Gmail: OAuth2 tokens auto-refresh
   - WhatsApp: Re-scan QR code monthly
   - LinkedIn: Rotate API keys monthly
   - SMTP: Rotate passwords quarterly

3. **Dry-Run Mode**:
   - All external actions support dry-run flag
   - Dry-run logs actions without executing
   - Enable during development and testing

4. **Rate Limiting**:
   - Gmail: 250 quota units/user/second (well within limits)
   - WhatsApp: Check every 5 minutes (avoid detection)
   - LinkedIn: Max 1 post per day (per spec)
   - MCP: Implement exponential backoff on failures

---

## Next Steps

1. ✅ Research complete - all technology decisions made
2. ⏳ Phase 1: Create data-model.md with entity definitions
3. ⏳ Phase 1: Create contracts/ with API contracts
4. ⏳ Phase 1: Create quickstart.md with setup instructions
5. ⏳ Phase 1: Update agent context with new technologies
6. ⏳ Phase 2: Run `/sp.tasks` to create task breakdown

---

**Research Status**: ✅ Complete
**All Decisions Made**: Yes
**Ready for Phase 1**: Yes

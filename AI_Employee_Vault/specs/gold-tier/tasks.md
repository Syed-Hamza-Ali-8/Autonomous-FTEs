# Tasks: Gold Tier Autonomous Employee

**Input**: Design documents from `/specs/gold-tier/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Comprehensive testing required - unit tests, integration tests, end-to-end tests

**Organization**: Tasks are grouped by phase (5 phases) to enable sequential implementation with clear checkpoints.

## Format: `[ID] [P?] [Phase] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Phase]**: Which phase this task belongs to (Phase 1-5)
- Include exact file paths in descriptions

## Path Conventions

- Gold Tier source: `gold/src/`
- MCP servers: `gold/mcp/`
- Tests: `gold/tests/`
- Vault structure: Folders at vault root (Briefings/, Accounting/, Social_Media/, Context/, Ralph_State/)

---

## Phase 1: Foundation - Error Recovery & Audit Logging (Week 1)

**Purpose**: Production-grade error handling and comprehensive audit logging

**Estimated Time**: 8-10 hours

### Setup Tasks

- [ ] T001 Create gold/ directory structure with src/, mcp/, tests/, config/
- [ ] T002 Initialize gold/pyproject.toml with Python 3.13+ and dependencies
- [ ] T003 [P] Create gold/.gitignore excluding __pycache__, .env, *.pyc, config/*.json
- [ ] T004 [P] Create gold/README.md with Gold Tier overview
- [ ] T005 [P] Create gold/src/__init__.py, gold/src/core/, gold/src/watchers/, gold/src/actions/, gold/src/intelligence/

### Error Recovery System

- [ ] T006 [Phase1] Create ErrorCategory enum in gold/src/core/error_recovery.py
- [ ] T007 [Phase1] Implement exponential_backoff_with_jitter() function with base_delay=1, max_delay=60
- [ ] T008 [Phase1] Implement retry_with_backoff() decorator with max_attempts=3
- [ ] T009 [Phase1] Create ErrorClassifier class to categorize errors (transient, auth, logic, data, system)
- [ ] T010 [Phase1] Implement GracefulDegradation manager for service failures
- [ ] T011 [Phase1] Create QueueManager for failed operations (store in Quarantine/)
- [ ] T012 [Phase1] Add unit tests for error recovery in gold/tests/test_error_recovery.py

### Audit Logging System

- [ ] T013 [P] [Phase1] Create AuditLogger class in gold/src/core/audit_logger.py
- [ ] T014 [P] [Phase1] Implement log() method with all required fields (timestamp, action_type, actor, target, etc.)
- [ ] T015 [P] [Phase1] Implement daily log rotation (create new file at midnight)
- [ ] T016 [P] [Phase1] Implement log search functionality (filter by date, action_type, actor)
- [ ] T017 [P] [Phase1] Implement log analysis (daily summary, error rate, performance metrics)
- [ ] T018 [P] [Phase1] Add 90-day retention with automatic cleanup
- [ ] T019 [P] [Phase1] Add unit tests for audit logger in gold/tests/test_audit_logger.py

### Health Monitoring System

- [ ] T020 [Phase1] Create HealthMonitor class in gold/src/core/health_monitor.py
- [ ] T021 [Phase1] Implement check_watcher_health() for all watchers (check PID, last activity)
- [ ] T022 [Phase1] Implement check_mcp_health() for all MCP servers (ping endpoints)
- [ ] T023 [Phase1] Implement generate_dashboard() to create Health_Status.md
- [ ] T024 [Phase1] Add alert system for service failures (log to Needs_Action/)
- [ ] T025 [Phase1] Add unit tests for health monitor in gold/tests/test_health_monitor.py

### Watchdog Process

- [ ] T026 [Phase1] Create Watchdog class in gold/src/core/watchdog.py
- [ ] T027 [Phase1] Implement process monitoring (track PIDs in /tmp/)
- [ ] T028 [Phase1] Implement auto-restart logic (restart crashed processes)
- [ ] T029 [Phase1] Implement notification system (create alert files in Needs_Action/)
- [ ] T030 [Phase1] Add logging for all restart events
- [ ] T031 [Phase1] Add unit tests for watchdog in gold/tests/test_watchdog.py

**Checkpoint Phase 1**: Error recovery, audit logging, health monitoring, and watchdog operational

---

## Phase 2: Accounting - Xero Integration (Week 2)

**Purpose**: Integrate Xero accounting platform for automated financial management

**Estimated Time**: 8-10 hours

### Xero MCP Server Setup

- [ ] T032 [Phase2] Clone Xero MCP server to gold/mcp/xero/
- [ ] T033 [Phase2] Install dependencies (npm install in gold/mcp/xero/)
- [ ] T034 [Phase2] Create gold/mcp/xero/config.json with OAuth credentials
- [ ] T035 [Phase2] Implement OAuth authentication flow in gold/mcp/xero/auth.js
- [ ] T036 [Phase2] Test Xero connection with gold/mcp/xero/test.js
- [ ] T037 [Phase2] Configure Xero MCP in ~/.config/claude-code/mcp.json

### Xero Watcher Implementation

- [ ] T038 [Phase2] Create XeroWatcher class in gold/src/watchers/xero_watcher.py extending BaseWatcher
- [ ] T039 [Phase2] Implement webhook handler for real-time Xero updates
- [ ] T040 [Phase2] Implement check_for_updates() to poll Xero API for new transactions
- [ ] T041 [Phase2] Implement transaction categorization logic (income, expense, transfer)
- [ ] T042 [Phase2] Implement create_action_file() to create transaction files in Accounting/Transactions/
- [ ] T043 [Phase2] Add business vs personal classification
- [ ] T044 [Phase2] Add tax deductibility detection
- [ ] T045 [Phase2] Add integration with audit logger
- [ ] T046 [Phase2] Add unit tests for Xero watcher in gold/tests/test_xero_watcher.py

### Financial Reporting

- [ ] T047 [P] [Phase2] Create FinancialReporter class in gold/src/actions/financial_reporter.py
- [ ] T048 [P] [Phase2] Implement generate_profit_loss() using Xero API
- [ ] T049 [P] [Phase2] Implement generate_balance_sheet() using Xero API
- [ ] T050 [P] [Phase2] Implement generate_cash_flow() using Xero API
- [ ] T051 [P] [Phase2] Implement generate_tax_summary() for tax-deductible expenses
- [ ] T052 [P] [Phase2] Format all reports as markdown files
- [ ] T053 [P] [Phase2] Add unit tests for financial reporter in gold/tests/test_financial_reporter.py

### Invoice Automation

- [ ] T054 [Phase2] Create InvoiceManager class in gold/src/actions/invoice_manager.py
- [ ] T055 [Phase2] Implement generate_invoice() from template
- [ ] T056 [Phase2] Implement send_invoice() via email (with HITL approval)
- [ ] T057 [Phase2] Implement track_payment_status() to monitor invoice payments
- [ ] T058 [Phase2] Implement alert_overdue_invoices() to create alerts in Needs_Action/
- [ ] T059 [Phase2] Add integration with CEO Briefing
- [ ] T060 [Phase2] Add unit tests for invoice manager in gold/tests/test_invoice_manager.py

**Checkpoint Phase 2**: Xero integration operational, transactions syncing, financial reports generating

---

## Phase 3: Social Media - Facebook, Instagram, Twitter (Week 3)

**Purpose**: Automate social media posting and engagement tracking

**Estimated Time**: 12-15 hours

### Social Media MCP Server Setup

- [ ] T061 [Phase3] Create gold/mcp/social/ directory
- [ ] T062 [Phase3] Initialize npm project (npm init -y)
- [ ] T063 [Phase3] Install dependencies (facebook-nodejs-business-sdk, twitter-api-v2)
- [ ] T064 [Phase3] Create gold/mcp/social/config.json with API credentials
- [ ] T065 [Phase3] Implement unified MCP server in gold/mcp/social/server.js
- [ ] T066 [Phase3] Implement Facebook API wrapper in gold/mcp/social/facebook.js
- [ ] T067 [Phase3] Implement Instagram API wrapper in gold/mcp/social/instagram.js
- [ ] T068 [Phase3] Implement Twitter API wrapper in gold/mcp/social/twitter.js
- [ ] T069 [Phase3] Test social MCP server with gold/mcp/social/test.js
- [ ] T070 [Phase3] Configure social MCP in ~/.config/claude-code/mcp.json

### Social Media Watchers

- [ ] T071 [P] [Phase3] Create FacebookWatcher class in gold/src/watchers/facebook_watcher.py
- [ ] T072 [P] [Phase3] Implement monitor_comments() to track Facebook comments
- [ ] T073 [P] [Phase3] Implement monitor_dms() to track Facebook DMs
- [ ] T074 [P] [Phase3] Implement track_engagement() to collect likes, shares, comments
- [ ] T075 [P] [Phase3] Create action files for responses requiring HITL
- [ ] T076 [P] [Phase3] Add unit tests in gold/tests/test_facebook_watcher.py

- [ ] T077 [P] [Phase3] Create InstagramWatcher class in gold/src/watchers/instagram_watcher.py
- [ ] T078 [P] [Phase3] Implement monitor_comments() for Instagram
- [ ] T079 [P] [Phase3] Implement monitor_dms() for Instagram
- [ ] T080 [P] [Phase3] Implement track_engagement() for Instagram
- [ ] T081 [P] [Phase3] Add unit tests in gold/tests/test_instagram_watcher.py

- [ ] T082 [P] [Phase3] Create TwitterWatcher class in gold/src/watchers/twitter_watcher.py
- [ ] T083 [P] [Phase3] Implement monitor_mentions() to track Twitter mentions
- [ ] T084 [P] [Phase3] Implement monitor_replies() to track replies
- [ ] T085 [P] [Phase3] Implement track_engagement() for Twitter
- [ ] T086 [P] [Phase3] Add unit tests in gold/tests/test_twitter_watcher.py

### Social Media Poster

- [ ] T087 [Phase3] Create SocialPoster class in gold/src/actions/social_poster.py
- [ ] T088 [Phase3] Implement post_to_platform() for multi-platform posting
- [ ] T089 [Phase3] Implement schedule_post() for scheduled posting
- [ ] T090 [Phase3] Implement handle_media() for images and videos
- [ ] T091 [Phase3] Implement create_thread() for Twitter threads
- [ ] T092 [Phase3] Add HITL approval integration
- [ ] T093 [Phase3] Add unit tests in gold/tests/test_social_poster.py

### Social Analytics

- [ ] T094 [P] [Phase3] Create SocialAnalytics class in gold/src/actions/social_analytics.py
- [ ] T095 [P] [Phase3] Implement track_engagement() across all platforms
- [ ] T096 [P] [Phase3] Implement track_follower_growth() for each platform
- [ ] T097 [P] [Phase3] Implement analyze_best_times() to identify optimal posting times
- [ ] T098 [P] [Phase3] Implement analyze_content_performance() to rank posts
- [ ] T099 [P] [Phase3] Implement generate_weekly_report() for CEO Briefing
- [ ] T100 [P] [Phase3] Add unit tests in gold/tests/test_social_analytics.py

**Checkpoint Phase 3**: Social media integrations operational, posts publishing, engagement tracking

---

## Phase 4: Intelligence - CEO Briefing & Cross-Domain Reasoning (Week 4)

**Purpose**: Implement autonomous business intelligence and cross-domain reasoning

**Estimated Time**: 6-8 hours

### CEO Briefing Generator

- [ ] T101 [Phase4] Create CEOBriefingGenerator class in gold/src/intelligence/ceo_briefing.py
- [ ] T102 [Phase4] Implement analyze_revenue() to calculate weekly/monthly revenue from Xero
- [ ] T103 [Phase4] Implement analyze_tasks() to review completed tasks from Done/ folder
- [ ] T104 [Phase4] Implement identify_bottlenecks() to find delayed tasks
- [ ] T105 [Phase4] Implement audit_subscriptions() to identify unused subscriptions
- [ ] T106 [Phase4] Implement generate_suggestions() for cost optimization and deadlines
- [ ] T107 [Phase4] Implement analyze_social_media() to include social performance
- [ ] T108 [Phase4] Implement generate_briefing() to create markdown file in Briefings/
- [ ] T109 [Phase4] Add scheduling (cron/Task Scheduler) for Sunday 7:00 AM
- [ ] T110 [Phase4] Add unit tests in gold/tests/test_ceo_briefing.py

### Cross-Domain Reasoner

- [ ] T111 [P] [Phase4] Create CrossDomainReasoner class in gold/src/intelligence/cross_domain_reasoner.py
- [ ] T112 [P] [Phase4] Implement analyze_event() to detect cross-domain impacts
- [ ] T113 [P] [Phase4] Implement identify_affected_domains() (personal, business)
- [ ] T114 [P] [Phase4] Implement generate_actions() for each affected domain
- [ ] T115 [P] [Phase4] Implement calculate_priority() based on impact
- [ ] T116 [P] [Phase4] Implement create_context() to create context files in Context/
- [ ] T117 [P] [Phase4] Implement resolve_context() when all actions complete
- [ ] T118 [P] [Phase4] Add unit tests in gold/tests/test_cross_domain_reasoner.py

### Business Analytics

- [ ] T119 [P] [Phase4] Create BusinessAnalytics class in gold/src/intelligence/business_analytics.py
- [ ] T120 [P] [Phase4] Implement analyze_revenue_trends() for trend analysis
- [ ] T121 [P] [Phase4] Implement analyze_expense_trends() for expense tracking
- [ ] T122 [P] [Phase4] Implement identify_top_clients() by revenue
- [ ] T123 [P] [Phase4] Implement calculate_project_profitability() for active projects
- [ ] T124 [P] [Phase4] Implement generate_insights() for CEO Briefing
- [ ] T125 [P] [Phase4] Add unit tests in gold/tests/test_business_analytics.py

### Subscription Auditor

- [ ] T126 [P] [Phase4] Create SubscriptionAuditor class in gold/src/intelligence/subscription_auditor.py
- [ ] T127 [P] [Phase4] Implement detect_subscriptions() from bank transactions
- [ ] T128 [P] [Phase4] Implement track_usage() (placeholder for future integration)
- [ ] T129 [P] [Phase4] Implement identify_unused() based on activity threshold (30 days)
- [ ] T130 [P] [Phase4] Implement calculate_savings() for potential cost reduction
- [ ] T131 [P] [Phase4] Implement generate_recommendations() for cancellations
- [ ] T132 [P] [Phase4] Add unit tests in gold/tests/test_subscription_auditor.py

**Checkpoint Phase 4**: CEO Briefing generating weekly, cross-domain reasoning operational, business analytics working

---

## Phase 5: Autonomy - Ralph Wiggum Loop & Documentation (Week 5)

**Purpose**: Enable autonomous task completion and comprehensive documentation

**Estimated Time**: 6-8 hours

### Ralph Wiggum Loop Implementation

- [ ] T133 [Phase5] Create RalphWiggumLoop class in gold/src/core/ralph_wiggum.py
- [ ] T134 [Phase5] Implement create_task_state() to create state file in Ralph_State/
- [ ] T135 [Phase5] Implement check_completion() to verify task completion
- [ ] T136 [Phase5] Implement track_progress() to log iteration progress
- [ ] T137 [Phase5] Implement handle_timeout() for max time limit (30 minutes)
- [ ] T138 [Phase5] Implement handle_max_iterations() for iteration limit (10)
- [ ] T139 [Phase5] Add unit tests in gold/tests/test_ralph_wiggum.py

### Claude Code Hook Configuration

- [ ] T140 [Phase5] Create .claude/hooks/ directory
- [ ] T141 [Phase5] Create stop hook in .claude/hooks/stop.sh
- [ ] T142 [Phase5] Implement completion check (look for file in Done/)
- [ ] T143 [Phase5] Implement iteration tracking (increment counter)
- [ ] T144 [Phase5] Implement max iterations check
- [ ] T145 [Phase5] Test hook with sample task
- [ ] T146 [Phase5] Add hook documentation in .claude/hooks/README.md

### Agent Skills Conversion

- [ ] T147 [P] [Phase5] Create .claude/skills/ceo-briefing/ directory
- [ ] T148 [P] [Phase5] Convert CEO Briefing to Agent Skill with skill.md
- [ ] T149 [P] [Phase5] Create .claude/skills/xero-sync/ directory
- [ ] T150 [P] [Phase5] Convert Xero sync to Agent Skill
- [ ] T151 [P] [Phase5] Create .claude/skills/social-post/ directory
- [ ] T152 [P] [Phase5] Convert social posting to Agent Skill
- [ ] T153 [P] [Phase5] Create .claude/skills/cross-domain-reason/ directory
- [ ] T154 [P] [Phase5] Convert cross-domain reasoning to Agent Skill
- [ ] T155 [P] [Phase5] Create .claude/skills/error-recovery/ directory
- [ ] T156 [P] [Phase5] Convert error recovery to Agent Skill
- [ ] T157 [P] [Phase5] Create .claude/skills/audit-log/ directory
- [ ] T158 [P] [Phase5] Convert audit logging to Agent Skill
- [ ] T159 [P] [Phase5] Create .claude/skills/ralph-loop/ directory
- [ ] T160 [P] [Phase5] Convert Ralph Wiggum loop to Agent Skill

### Documentation

- [ ] T161 [P] [Phase5] Create gold/ARCHITECTURE.md with system architecture diagram
- [ ] T162 [P] [Phase5] Create gold/SETUP.md with step-by-step installation guide
- [ ] T163 [P] [Phase5] Create gold/CONFIGURATION.md with all configuration options
- [ ] T164 [P] [Phase5] Create gold/TROUBLESHOOTING.md with common issues and solutions
- [ ] T165 [P] [Phase5] Create gold/LESSONS_LEARNED.md with what worked and what didn't
- [ ] T166 [P] [Phase5] Create gold/SECURITY.md with security best practices
- [ ] T167 [P] [Phase5] Create gold/API_REFERENCE.md with MCP server API documentation

### Demo Video

- [ ] T168 [Phase5] Script demo video (5-10 minutes)
- [ ] T169 [Phase5] Record introduction (30 seconds)
- [ ] T170 [Phase5] Record CEO Briefing generation demo (2 minutes)
- [ ] T171 [Phase5] Record cross-domain reasoning demo (2 minutes)
- [ ] T172 [Phase5] Record social media automation demo (1 minute)
- [ ] T173 [Phase5] Record error recovery demo (1 minute)
- [ ] T174 [Phase5] Record audit logs showcase (1 minute)
- [ ] T175 [Phase5] Record Ralph Wiggum loop demo (1 minute)
- [ ] T176 [Phase5] Record conclusion (30 seconds)
- [ ] T177 [Phase5] Edit and upload video to YouTube/Vimeo

**Checkpoint Phase 5**: Ralph Wiggum loop operational, all features as Agent Skills, documentation complete, demo video recorded

---

## Integration & Testing Tasks

### Integration Tests

- [ ] T178 [P] Create gold/tests/integration/ directory
- [ ] T179 [P] Test Xero → CEO Briefing integration
- [ ] T180 [P] Test Social Media → CEO Briefing integration
- [ ] T181 [P] Test Cross-Domain Context → Action Execution
- [ ] T182 [P] Test Error Recovery → Retry Logic
- [ ] T183 [P] Test HITL Approval → Social Media Posting
- [ ] T184 [P] Test Ralph Wiggum Loop → Multi-Step Task

### End-to-End Tests

- [ ] T185 Create gold/tests/e2e/ directory
- [ ] T186 Test complete invoice flow (WhatsApp → Xero → Email)
- [ ] T187 Test complete social media flow (Draft → Approval → Post → Analytics)
- [ ] T188 Test complete CEO Briefing flow (Data Collection → Analysis → Generation)
- [ ] T189 Test complete cross-domain flow (Payment → Xero → Thank You)

### Performance Tests

- [ ] T190 [P] Measure CEO Briefing generation time (target: <5 minutes)
- [ ] T191 [P] Measure Xero sync time (target: <30 seconds)
- [ ] T192 [P] Measure social media post time (target: <10 seconds)
- [ ] T193 [P] Measure error recovery overhead (target: <2 seconds)

---

## Process Management Tasks

### PM2 Configuration

- [ ] T194 Create gold/ecosystem.config.js with all processes
- [ ] T195 Configure auto-restart for all processes
- [ ] T196 Configure memory limits (500M for watchers, 200M for core)
- [ ] T197 Configure log rotation
- [ ] T198 Test PM2 startup on boot
- [ ] T199 Create PM2 monitoring dashboard

### Health Monitoring

- [ ] T200 Configure health checks for all watchers (every 60 seconds)
- [ ] T201 Configure health checks for all MCP servers (every 60 seconds)
- [ ] T202 Configure alert thresholds (3 consecutive failures)
- [ ] T203 Test watchdog auto-restart functionality
- [ ] T204 Create health monitoring dashboard in Health_Status.md

---

## Deployment Tasks

### Environment Setup

- [ ] T205 Create gold/.env.example with all required variables
- [ ] T206 Document all environment variables in CONFIGURATION.md
- [ ] T207 Create setup script (gold/scripts/setup.sh) for automated setup
- [ ] T208 Test setup on clean system

### Security Audit

- [ ] T209 Verify no credentials in git repository
- [ ] T210 Verify all API keys in environment variables
- [ ] T211 Verify OAuth tokens encrypted at rest
- [ ] T212 Verify audit logs tamper-proof
- [ ] T213 Verify HITL approval enforced for sensitive actions

### Final Verification

- [ ] T214 Run all unit tests (target: 80%+ coverage)
- [ ] T215 Run all integration tests
- [ ] T216 Run all end-to-end tests
- [ ] T217 Verify all 12 Gold Tier requirements met
- [ ] T218 Verify CEO Briefing generates automatically
- [ ] T219 Verify all watchers running (PM2 status)
- [ ] T220 Verify all MCP servers operational
- [ ] T221 Verify complete audit trail
- [ ] T222 Verify Ralph Wiggum loop functional
- [ ] T223 Verify all documentation complete
- [ ] T224 Verify demo video recorded

---

## Task Summary

**Total Tasks**: 224
**Phase 1**: 31 tasks (Foundation)
**Phase 2**: 29 tasks (Accounting)
**Phase 3**: 40 tasks (Social Media)
**Phase 4**: 32 tasks (Intelligence)
**Phase 5**: 45 tasks (Autonomy)
**Integration & Testing**: 17 tasks
**Process Management**: 11 tasks
**Deployment**: 19 tasks

**Estimated Total Time**: 40-50 hours

---

## Dependencies

### Critical Path
```
Phase 1 (Foundation) → Phase 2 (Accounting) → Phase 4 (Intelligence)
                    → Phase 3 (Social Media) → Phase 4 (Intelligence)
                                            → Phase 5 (Autonomy)
```

### Parallel Work Opportunities
- Phase 2 and Phase 3 can be done in parallel after Phase 1
- Documentation (Phase 5) can be written in parallel with implementation
- Agent Skills conversion can be done as features are completed

---

## Success Criteria

Gold Tier is complete when:
- [ ] All 224 tasks completed
- [ ] All tests passing (unit, integration, end-to-end)
- [ ] CEO Briefing generates every Sunday 7:00 AM
- [ ] All 6+ integrations operational
- [ ] 99%+ uptime for critical services
- [ ] Complete audit trail for all actions
- [ ] Ralph Wiggum loop functional
- [ ] All features as Agent Skills
- [ ] Documentation complete
- [ ] Demo video recorded
- [ ] Security audit passed

---

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Status**: Ready for Implementation

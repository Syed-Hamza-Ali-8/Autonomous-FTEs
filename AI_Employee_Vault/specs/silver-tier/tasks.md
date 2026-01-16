# Tasks: Silver Tier - Functional AI Assistant

**Input**: Design documents from `/specs/silver-tier/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT included as they were not explicitly requested in the feature specification. Manual end-to-end testing will be performed per the plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Silver tier**: `silver/` directory at repository root
- **Agent Skills**: `.claude/skills/` at repository root
- **Config**: `silver/config/`
- **Source**: `silver/src/`
- **MCP**: `silver/mcp/email-server/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create silver/ directory structure per implementation plan
- [ ] T002 Initialize Python project with pyproject.toml in silver/
- [ ] T003 [P] Create silver/config/ directory with .env.example template
- [ ] T004 [P] Create silver/src/watchers/ directory
- [ ] T005 [P] Create silver/src/approval/ directory
- [ ] T006 [P] Create silver/src/planning/ directory
- [ ] T007 [P] Create silver/src/actions/ directory
- [ ] T008 [P] Create silver/src/scheduling/ directory
- [ ] T009 [P] Create silver/mcp/email-server/ directory for Node.js MCP server
- [ ] T010 [P] Create silver/scripts/ directory for setup scripts
- [ ] T011 [P] Create silver/tests/integration/ and silver/tests/unit/ directories
- [ ] T012 Add Python dependencies to silver/pyproject.toml (google-auth, playwright, linkedin-api, schedule, plyer)
- [ ] T013 Create silver/mcp/email-server/package.json with MCP SDK and nodemailer dependencies
- [ ] T014 [P] Create Pending_Approval/, Approved/, Rejected/, Plans/ folders in vault root
- [ ] T015 [P] Add silver/config/.env to .gitignore
- [ ] T016 Create silver/README.md with Silver tier overview

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T017 Copy and adapt utility modules from bronze/src/utils/ to silver/src/utils/ (file_utils.py, yaml_parser.py, logger.py, dashboard_updater.py, obsidian_api.py)
- [ ] T018 Create silver/config/watcher_config.yaml template with structure for all watchers
- [ ] T019 Create silver/config/approval_rules.yaml template with HITL rules
- [ ] T020 [P] Create silver/scripts/setup_credentials.sh for interactive credential setup
- [ ] T021 [P] Create silver/scripts/start_watchers.sh to launch all watchers
- [ ] T022 [P] Create silver/scripts/setup_scheduling.sh for cron/Task Scheduler configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-Channel Communication Monitoring (Priority: P1) 🎯 MVP

**Goal**: Monitor Gmail, WhatsApp, and LinkedIn for new messages and create action files in Needs_Action folder

**Independent Test**: Send test messages through Gmail, WhatsApp, and LinkedIn, verify action files are created in Needs_Action/ with proper YAML frontmatter and content

### Implementation for User Story 1

- [ ] T023 [P] [US1] Create BaseWatcher abstract class in silver/src/watchers/base_watcher.py with check_for_updates(), create_action_file(), run() methods
- [ ] T024 [US1] Implement GmailWatcher in silver/src/watchers/gmail_watcher.py with OAuth2 authentication and Gmail API integration
- [ ] T025 [US1] Implement WhatsAppWatcher in silver/src/watchers/whatsapp_watcher.py with Playwright browser automation
- [ ] T026 [US1] Implement LinkedInWatcher in silver/src/watchers/linkedin_watcher.py with LinkedIn API integration
- [ ] T027 [US1] Create silver/scripts/setup_gmail.py for OAuth2 credential setup and token generation
- [ ] T028 [US1] Create silver/scripts/setup_whatsapp.py for WhatsApp Web QR code scanning and session persistence
- [ ] T029 [US1] Create silver/scripts/setup_linkedin.py for LinkedIn authentication and session storage
- [ ] T030 [US1] Update silver/config/watcher_config.yaml with default configurations for all three watchers
- [ ] T031 [US1] Create .claude/skills/monitor-communications/ directory with SKILL.md and skill.py
- [ ] T032 [US1] Implement monitor-communications Agent Skill in .claude/skills/monitor-communications/skill.py to orchestrate all watchers
- [ ] T033 [US1] Update Dashboard.md to show watcher status (running, last check, messages detected)
- [ ] T034 [US1] Create silver/scripts/test_watchers.sh to manually test each watcher independently

**Checkpoint**: At this point, User Story 1 should be fully functional - messages from all 3 channels are detected and action files created

---

## Phase 4: User Story 2 - Human-in-the-Loop Approval Workflow (Priority: P1)

**Goal**: Implement approval workflow for sensitive actions with file-based polling and desktop notifications

**Independent Test**: Create test approval request, verify notification appears, approve via file edit, verify action executes

### Implementation for User Story 2

- [ ] T035 [P] [US2] Create ApprovalManager class in silver/src/approval/approval_manager.py with create_approval_request() method
- [ ] T036 [P] [US2] Create ApprovalChecker class in silver/src/approval/approval_checker.py with poll_for_approvals() and check_approval_status() methods
- [ ] T037 [P] [US2] Create ApprovalNotifier class in silver/src/approval/approval_notifier.py with send_notification() using plyer library
- [ ] T038 [US2] Implement is_sensitive_action() function in silver/src/approval/approval_manager.py to classify actions
- [ ] T039 [US2] Implement execute_approved_action() in silver/src/approval/approval_manager.py with retry logic (max 3 attempts, exponential backoff)
- [ ] T040 [US2] Update silver/config/approval_rules.yaml with sensitive action definitions and auto-approve thresholds
- [ ] T041 [US2] Create .claude/skills/manage-approvals/ directory with SKILL.md and skill.py
- [ ] T042 [US2] Implement manage-approvals Agent Skill in .claude/skills/manage-approvals/skill.py for approval workflow orchestration
- [ ] T043 [US2] Create silver/scripts/test_approval.py to create test approval requests for validation
- [ ] T044 [US2] Update Dashboard.md to show pending approval count and status

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - messages detected, approval workflow functional

---

## Phase 5: User Story 3 - Automated LinkedIn Business Posting (Priority: P2)

**Goal**: Generate LinkedIn post content from vault updates and publish with approval

**Independent Test**: Trigger post generation, verify approval request created, approve, verify post published to LinkedIn

### Implementation for User Story 3

- [ ] T045 [P] [US3] Create LinkedInPoster class in silver/src/actions/linkedin_poster.py with post_to_linkedin() method
- [ ] T046 [US3] Create post content generator in silver/src/planning/post_generator.py to analyze vault and generate post ideas
- [ ] T047 [US3] Integrate LinkedInPoster with ApprovalManager to require approval before posting
- [ ] T048 [US3] Create .claude/skills/post-linkedin/ directory with SKILL.md and skill.py
- [ ] T049 [US3] Implement post-linkedin Agent Skill in .claude/skills/post-linkedin/skill.py for end-to-end LinkedIn posting
- [ ] T050 [US3] Add LinkedIn posting configuration to silver/config/approval_rules.yaml (max 1 post per day)
- [ ] T051 [US3] Create silver/scripts/test_linkedin_post.py to test posting workflow with dry-run mode

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently - monitoring, approval, and LinkedIn posting functional

---

## Phase 6: User Story 4 - Intelligent Planning and Reasoning (Priority: P2)

**Goal**: Create structured Plan.md files for complex tasks with steps, dependencies, and success criteria

**Independent Test**: Present complex task, verify Plan.md created in Plans/ folder with proper structure

### Implementation for User Story 4

- [ ] T052 [P] [US4] Create PlanGenerator class in silver/src/planning/plan_generator.py with generate_plan() method
- [ ] T053 [P] [US4] Create TaskAnalyzer class in silver/src/planning/task_analyzer.py to break down complex tasks
- [ ] T054 [P] [US4] Create PlanTracker class in silver/src/planning/plan_tracker.py to track plan execution status
- [ ] T055 [US4] Create Plan.md template in silver/config/plan_template.md with required sections (objective, steps, dependencies, risks, success criteria)
- [ ] T056 [US4] Create .claude/skills/create-plans/ directory with SKILL.md and skill.py
- [ ] T057 [US4] Implement create-plans Agent Skill in .claude/skills/create-plans/skill.py for plan generation
- [ ] T058 [US4] Update Dashboard.md to show active plans count and status
- [ ] T059 [US4] Create silver/scripts/test_planning.py to test plan generation with sample complex tasks

**Checkpoint**: User Stories 1-4 should all work independently - monitoring, approval, LinkedIn, and planning functional

---

## Phase 7: User Story 5 - External Action Execution (Priority: P3)

**Goal**: Execute approved actions through MCP email server with retry logic and error handling

**Independent Test**: Approve email send action, verify email sent via SMTP, verify audit log entry

### Implementation for User Story 5

- [ ] T060 [P] [US5] Create MCP email server in silver/mcp/email-server/index.js with send-email endpoint
- [ ] T061 [P] [US5] Implement email validation in silver/mcp/email-server/index.js with RFC 5322 format checking
- [ ] T062 [P] [US5] Implement retry logic with exponential backoff in MCP server (max 3 retries, 2s/4s/8s delays)
- [ ] T063 [US5] Create ActionExecutor class in silver/src/actions/action_executor.py to coordinate action execution
- [ ] T064 [US5] Create EmailSender class in silver/src/actions/email_sender.py as MCP client for email sending
- [ ] T065 [US5] Integrate ActionExecutor with ApprovalManager to execute only approved actions
- [ ] T066 [US5] Create .claude/skills/execute-actions/ directory with SKILL.md and skill.py
- [ ] T067 [US5] Implement execute-actions Agent Skill in .claude/skills/execute-actions/skill.py for action execution orchestration
- [ ] T068 [US5] Create silver/mcp/email-server/.env.example with SMTP configuration template
- [ ] T069 [US5] Create silver/scripts/test_smtp.py to test SMTP connection and email sending
- [ ] T070 [US5] Create silver/scripts/test_mcp.py to test MCP server endpoints
- [ ] T071 [US5] Add MCP server startup to silver/scripts/start_watchers.sh or create separate start script
- [ ] T072 [US5] Update Dashboard.md to show MCP server status and action execution count

**Checkpoint**: User Stories 1-5 should all work independently - full perception → reasoning → action loop functional

---

## Phase 8: User Story 6 - Scheduled Automation (Priority: P3)

**Goal**: Run watchers on schedule using Python schedule library with systemd/PM2 process management

**Independent Test**: Configure schedule, wait for scheduled time, verify watcher runs automatically

### Implementation for User Story 6

- [ ] T073 [P] [US6] Create Scheduler class in silver/src/scheduling/scheduler.py using schedule library
- [ ] T074 [US6] Implement schedule configuration loading from silver/config/watcher_config.yaml
- [ ] T075 [US6] Create main scheduler script in silver/src/scheduling/main_scheduler.py to run all watchers on schedule
- [ ] T076 [US6] Add graceful shutdown handling (SIGTERM) to scheduler
- [ ] T077 [US6] Create systemd service file in silver/scripts/silver-watchers.service for Linux
- [ ] T078 [US6] Create PM2 ecosystem file in silver/scripts/ecosystem.config.js for cross-platform process management
- [ ] T079 [US6] Update silver/scripts/setup_scheduling.sh to install systemd service or PM2 configuration
- [ ] T080 [US6] Create silver/scripts/restart_watchers.sh for daily restart (stability)
- [ ] T081 [US6] Add cron job configuration to silver/scripts/setup_scheduling.sh for daily restarts
- [ ] T082 [US6] Update Dashboard.md to show scheduler status and next scheduled run times

**Checkpoint**: All user stories should now be independently functional - full Silver tier feature set complete

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T083 [P] Create comprehensive silver/README.md with architecture overview, setup instructions, and usage guide
- [ ] T084 [P] Validate quickstart.md by following all 14 setup steps end-to-end
- [ ] T085 [P] Create silver/scripts/validate_setup.sh to check all prerequisites and configurations
- [ ] T086 [P] Add error recovery and graceful degradation for all watchers (handle network failures, auth errors, rate limits)
- [ ] T087 [P] Implement comprehensive audit logging for all operations (watchers, approvals, actions, scheduling)
- [ ] T088 [P] Add security hardening (validate all inputs, sanitize outputs, check for injection attacks)
- [ ] T089 [P] Performance optimization (reduce memory usage, optimize polling intervals, cache frequently accessed data)
- [ ] T090 [P] Create troubleshooting guide in silver/docs/TROUBLESHOOTING.md with common issues and solutions
- [ ] T091 [P] Update main project README.md to document Silver tier completion and capabilities
- [ ] T092 [P] Create demo video script showing all 6 user stories in action
- [ ] T093 Verify all Agent Skills are discoverable by Claude Code (test with `claude-code --skill <name>`)
- [ ] T094 Run full end-to-end integration test: send messages → detect → approve actions → execute → verify results
- [ ] T095 Verify constitution compliance (all 7 principles) and document any deviations
- [ ] T096 Final Dashboard.md update with complete Silver tier statistics and status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (but integrates with US1 for message-triggered actions)
- **User Story 3 (P2)**: Depends on User Story 2 (needs approval workflow) - Can start after US2 complete
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P3)**: Depends on User Story 2 (needs approval workflow) - Can start after US2 complete
- **User Story 6 (P3)**: Depends on User Story 1 (schedules watchers) - Can start after US1 complete

### Within Each User Story

- Models/classes before services
- Services before integration
- Core implementation before Agent Skills
- Agent Skills before testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T011, T014-T016)
- All Foundational tasks marked [P] can run in parallel (T020-T022)
- Once Foundational phase completes:
  - User Story 1 (T023-T034) can start immediately
  - User Story 2 (T035-T044) can start immediately (parallel with US1)
  - User Story 4 (T052-T059) can start immediately (parallel with US1/US2)
- Within each story, tasks marked [P] can run in parallel
- All Polish tasks marked [P] can run in parallel (T083-T092)

---

## Parallel Example: User Story 1

```bash
# Launch all watcher implementations together:
Task: "Create BaseWatcher abstract class in silver/src/watchers/base_watcher.py" (T023)

# Then launch all specific watchers in parallel:
Task: "Implement GmailWatcher in silver/src/watchers/gmail_watcher.py" (T024)
Task: "Implement WhatsAppWatcher in silver/src/watchers/whatsapp_watcher.py" (T025)
Task: "Implement LinkedInWatcher in silver/src/watchers/linkedin_watcher.py" (T026)

# Then launch all setup scripts in parallel:
Task: "Create silver/scripts/setup_gmail.py" (T027)
Task: "Create silver/scripts/setup_whatsapp.py" (T028)
Task: "Create silver/scripts/setup_linkedin.py" (T029)
```

---

## Parallel Example: User Story 2

```bash
# Launch all approval classes in parallel:
Task: "Create ApprovalManager class in silver/src/approval/approval_manager.py" (T035)
Task: "Create ApprovalChecker class in silver/src/approval/approval_checker.py" (T036)
Task: "Create ApprovalNotifier class in silver/src/approval/approval_notifier.py" (T037)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T001-T016)
2. Complete Phase 2: Foundational (T017-T022) - CRITICAL
3. Complete Phase 3: User Story 1 (T023-T034) - Multi-channel monitoring
4. Complete Phase 4: User Story 2 (T035-T044) - HITL approval
5. **STOP and VALIDATE**: Test US1 and US2 independently
6. Deploy/demo if ready - this is a functional AI assistant!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (monitoring works!)
3. Add User Story 2 → Test independently → Deploy/Demo (approval works!)
4. Add User Story 3 → Test independently → Deploy/Demo (LinkedIn posting works!)
5. Add User Story 4 → Test independently → Deploy/Demo (planning works!)
6. Add User Story 5 → Test independently → Deploy/Demo (external actions work!)
7. Add User Story 6 → Test independently → Deploy/Demo (scheduling works!)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T022)
2. Once Foundational is done:
   - Developer A: User Story 1 (T023-T034) - Monitoring
   - Developer B: User Story 2 (T035-T044) - Approval
   - Developer C: User Story 4 (T052-T059) - Planning
3. After US2 completes:
   - Developer D: User Story 3 (T045-T051) - LinkedIn (depends on US2)
   - Developer E: User Story 5 (T060-T072) - External Actions (depends on US2)
4. After US1 completes:
   - Developer F: User Story 6 (T073-T082) - Scheduling (depends on US1)
5. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 96
- **Phase 1 (Setup)**: 16 tasks
- **Phase 2 (Foundational)**: 6 tasks (BLOCKING)
- **Phase 3 (US1 - Monitoring)**: 12 tasks
- **Phase 4 (US2 - Approval)**: 10 tasks
- **Phase 5 (US3 - LinkedIn)**: 7 tasks
- **Phase 6 (US4 - Planning)**: 8 tasks
- **Phase 7 (US5 - External Actions)**: 13 tasks
- **Phase 8 (US6 - Scheduling)**: 10 tasks
- **Phase 9 (Polish)**: 14 tasks

**Parallelizable Tasks**: 42 tasks marked with [P]

**MVP Scope** (User Stories 1 & 2): 34 tasks (Setup + Foundational + US1 + US2)

**Independent Test Criteria**:
- US1: Send test messages, verify action files created
- US2: Create approval request, approve, verify execution
- US3: Generate post, approve, verify published
- US4: Request plan, verify Plan.md created
- US5: Approve action, verify external execution
- US6: Configure schedule, verify automatic execution

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included as they were not requested in the specification
- Manual end-to-end testing will be performed per the plan
- All Agent Skills must be in `.claude/skills/` at project root (per constitution)
- Credentials must be stored securely in `.env` files (gitignored)
- All sensitive actions require HITL approval (100% compliance)
- Watchers must check at minimum 5-minute intervals (rate limit compliance)

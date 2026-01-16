# Tasks: Bronze Tier Foundation

**Input**: Design documents from `/specs/bronze-tier/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in specification - Bronze tier uses manual end-to-end testing

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Vault structure: Folders at vault root (Inbox/, Needs_Action/, Done/, Logs/)
- Python source: `src/watcher/`, `src/utils/`
- Agent Skills: `.claude/skills/process-files/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create Python project structure with src/, tests/, .claude/ directories
- [ ] T002 Initialize pyproject.toml with Python 3.13+ and dependencies (watchdog, pyyaml)
- [ ] T003 [P] Create .gitignore file excluding __pycache__, .env, Logs/, *.pyc
- [ ] T004 [P] Create README.md with project overview and setup instructions
- [ ] T005 [P] Create src/__init__.py, src/watcher/__init__.py, src/utils/__init__.py

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that multiple user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement JSON logger utility in src/utils/logger.py with daily log rotation
- [ ] T007 [P] Implement file type detection utility in src/utils/file_utils.py using mimetypes
- [ ] T008 [P] Create YAML frontmatter parser utility in src/utils/yaml_parser.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Vault Structure Setup (Priority: P1) 🎯 MVP

**Goal**: Create organized Obsidian workspace with folders and management files

**Independent Test**: Open vault in Obsidian, verify all folders exist, Dashboard.md and Company_Handbook.md are readable and properly formatted

### Implementation for User Story 1

- [ ] T009 [P] [US1] Create Inbox/ folder at vault root
- [ ] T010 [P] [US1] Create Needs_Action/ folder with Quarantine/ subfolder at vault root
- [ ] T011 [P] [US1] Create Done/ folder at vault root
- [ ] T012 [P] [US1] Create Logs/ folder at vault root
- [ ] T013 [US1] Create Dashboard.md template at vault root with YAML frontmatter and initial sections
- [ ] T014 [US1] Create Company_Handbook.md at vault root with processing rules for all file types
- [ ] T015 [US1] Verify vault structure by opening in Obsidian and checking all folders/files

**Checkpoint**: Vault structure complete and viewable in Obsidian - User Story 1 is fully functional

---

## Phase 4: User Story 2 - Automatic File Detection (Priority: P2)

**Goal**: Python Watcher script that monitors Inbox and creates metadata files in Needs_Action

**Independent Test**: Start Watcher, drop test file in Inbox, verify metadata file created in Needs_Action within 10 seconds and log entry exists

### Implementation for User Story 2

- [ ] T016 [P] [US2] Create MetadataCreator class in src/watcher/metadata_creator.py
- [ ] T017 [P] [US2] Implement create_metadata() method to generate markdown with YAML frontmatter
- [ ] T018 [P] [US2] Implement file size formatting and timestamp generation in MetadataCreator
- [ ] T019 [US2] Create InboxHandler class in src/watcher/file_watcher.py extending FileSystemEventHandler
- [ ] T020 [US2] Implement on_created() event handler with debouncing (1 second wait)
- [ ] T021 [US2] Implement _process_file() method to create metadata and move file to Needs_Action
- [ ] T022 [US2] Add logging for file detection and file movement events
- [ ] T023 [US2] Implement run_watcher() function with Observer setup and signal handling
- [ ] T024 [US2] Add temporary file filtering (.tmp, .swp, ~$, dot files)
- [ ] T025 [US2] Create __main__ entry point for running Watcher with vault path argument
- [ ] T026 [US2] Test Watcher by dropping multiple file types and verifying metadata creation

**Checkpoint**: Watcher script complete and can detect files autonomously - User Story 2 is fully functional

---

## Phase 5: User Story 3 - AI-Powered File Processing (Priority: P3)

**Goal**: Claude Agent Skill that analyzes files, creates summaries, and moves to Done

**Independent Test**: Place test file in Needs_Action, invoke skill, verify summary created and file moved to Done

### Implementation for User Story 3

- [ ] T027 [US3] Create .claude/skills/process-files/ directory structure
- [ ] T028 [US3] Create SKILL.md documentation in .claude/skills/process-files/ with usage and requirements
- [ ] T029 [P] [US3] Implement file reader utility in src/utils/file_reader.py for text, PDF, image files
- [ ] T030 [P] [US3] Implement summary generator logic in src/utils/summarizer.py with file type routing
- [ ] T031 [US3] Create skill.py in .claude/skills/process-files/ with main processing logic
- [ ] T032 [US3] Implement scan_needs_action() function to find pending files
- [ ] T033 [US3] Implement process_file() function to read, analyze, and create summary
- [ ] T034 [US3] Implement update_metadata() function to add summary to metadata file
- [ ] T035 [US3] Implement move_to_done() function to move processed files
- [ ] T036 [US3] Add error handling for corrupted files (move to Quarantine)
- [ ] T037 [US3] Add logging for all processing events (success, failure, quarantine)
- [ ] T038 [US3] Implement Company_Handbook.md rule parsing for file type processing
- [ ] T039 [US3] Test skill with various file types (txt, pdf, image, md, docx)

**Checkpoint**: Agent Skill complete and can process files intelligently - User Story 3 is fully functional

---

## Phase 6: User Story 4 - Real-Time Status Dashboard (Priority: P4)

**Goal**: Dashboard.md updates automatically with system status and recent activity

**Independent Test**: Process several files, open Dashboard.md, verify current counts and recent activity are accurate

### Implementation for User Story 4

- [ ] T040 [P] [US4] Create dashboard_updater.py in src/utils/ with update logic
- [ ] T041 [P] [US4] Implement read_dashboard() function to parse current Dashboard.md state
- [ ] T042 [US4] Implement update_pending_count() function to count files in Needs_Action
- [ ] T043 [US4] Implement add_recent_activity() function to add new entry and trim to 5 items
- [ ] T044 [US4] Implement update_statistics() function to increment today/week/total counters
- [ ] T045 [US4] Implement update_watcher_status() function to set running/stopped status
- [ ] T046 [US4] Implement write_dashboard() function with atomic file write (temp file + rename)
- [ ] T047 [US4] Integrate dashboard updates into Watcher (after file detection)
- [ ] T048 [US4] Integrate dashboard updates into Agent Skill (after file processing)
- [ ] T049 [US4] Add last_updated timestamp to Dashboard.md on every update
- [ ] T050 [US4] Test dashboard updates by processing multiple files and verifying accuracy

**Checkpoint**: Dashboard updates automatically - User Story 4 is fully functional - All user stories complete!

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Add comprehensive docstrings to all Python modules and functions
- [ ] T052 [P] Add type hints to all Python functions per PEP 484
- [ ] T053 [P] Create requirements.txt from pyproject.toml for compatibility
- [ ] T054 Code cleanup: Remove debug print statements, ensure consistent formatting
- [ ] T055 [P] Update README.md with complete setup instructions and usage examples
- [ ] T056 [P] Create CONTRIBUTING.md with development guidelines
- [ ] T057 Verify all log entries follow JSON schema from contracts/log-entry.schema.json
- [ ] T058 Verify all metadata files follow schema from contracts/file-metadata.schema.yaml
- [ ] T059 Verify Dashboard.md follows schema from contracts/dashboard-state.schema.yaml
- [ ] T060 Run manual end-to-end test following quickstart.md validation steps
- [ ] T061 Test 24-hour Watcher uptime requirement (leave running overnight)
- [ ] T062 Test with 10+ files of different types to verify robustness
- [ ] T063 [P] Document known limitations and Silver tier roadmap in README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (needs vault folders)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (needs vault folders) and US2 (needs metadata files)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1 (needs Dashboard.md) and integrates with US2/US3

**Note**: While US2, US3, US4 have logical dependencies on US1, they can be developed in parallel if US1 is completed first (which it should be as P1).

### Within Each User Story

- Setup tasks (Phase 1) can mostly run in parallel
- Foundational utilities (Phase 2) can run in parallel
- US1 tasks (folders and files) can all run in parallel
- US2: MetadataCreator and file utilities can be parallel, then Watcher implementation
- US3: File reader and summarizer can be parallel, then skill implementation
- US4: Dashboard functions can be parallel, then integration tasks
- Polish tasks can mostly run in parallel

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T005 can run in parallel

**Phase 2 (Foundational)**: T007, T008 can run in parallel (T006 logger is used by both)

**Phase 3 (US1)**: T009, T010, T011, T012 can all run in parallel (folder creation)

**Phase 4 (US2)**: T016, T017, T018 can run in parallel (MetadataCreator components)

**Phase 5 (US3)**: T029, T030 can run in parallel (file reader and summarizer)

**Phase 6 (US4)**: T040, T041, T042, T043, T044, T045 can run in parallel (dashboard functions)

**Phase 7 (Polish)**: T051, T052, T053, T055, T056, T063 can run in parallel (documentation)

---

## Parallel Example: User Story 1 (Vault Structure)

```bash
# Launch all folder creation tasks together:
Task: "Create Inbox/ folder at vault root"
Task: "Create Needs_Action/ folder with Quarantine/ subfolder at vault root"
Task: "Create Done/ folder at vault root"
Task: "Create Logs/ folder at vault root"

# These can all be done simultaneously since they're independent folders
```

## Parallel Example: User Story 2 (File Detection)

```bash
# Launch metadata creator components together:
Task: "Create MetadataCreator class in src/watcher/metadata_creator.py"
Task: "Implement create_metadata() method to generate markdown with YAML frontmatter"
Task: "Implement file size formatting and timestamp generation in MetadataCreator"

# These can be developed in parallel as they're in the same class but different methods
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T008)
3. Complete Phase 3: User Story 1 (T009-T015)
4. **STOP and VALIDATE**: Open vault in Obsidian, verify structure
5. This gives you a working vault structure - immediate value!

### Incremental Delivery (Recommended)

1. **Sprint 1**: Setup + Foundational + US1 → Working vault structure
2. **Sprint 2**: US2 → Autonomous file detection
3. **Sprint 3**: US3 → AI-powered processing
4. **Sprint 4**: US4 → Dashboard visibility
5. **Sprint 5**: Polish → Production-ready

Each sprint delivers a complete, testable increment.

### Parallel Team Strategy

With multiple developers:

1. **Week 1**: Team completes Setup + Foundational together (T001-T008)
2. **Week 2**: Once Foundational is done:
   - Developer A: User Story 1 (T009-T015) - 1 day
   - Developer B: User Story 2 (T016-T026) - 3 days
   - Developer C: User Story 3 (T027-T039) - 4 days
3. **Week 3**:
   - Developer A: User Story 4 (T040-T050) - 2 days
   - Developer B: Polish (T051-T063) - 3 days
   - Developer C: Testing and integration

---

## Task Count Summary

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 3 tasks
- **Phase 3 (US1 - Vault Structure)**: 7 tasks
- **Phase 4 (US2 - File Detection)**: 11 tasks
- **Phase 5 (US3 - File Processing)**: 13 tasks
- **Phase 6 (US4 - Dashboard Updates)**: 11 tasks
- **Phase 7 (Polish)**: 13 tasks

**Total**: 63 tasks

**Parallel Opportunities**: 18 tasks marked [P] can run in parallel with others

**Estimated Effort**: 8-12 hours per Bronze tier specification

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No automated tests requested - use manual testing per quickstart.md
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow quickstart.md for setup and testing procedures
- Refer to research.md for technology decision rationale
- Refer to data-model.md for entity schemas
- Refer to contracts/ for data structure validation

---

## Success Criteria (from spec.md)

After completing all tasks, verify:

- ✅ SC-001: Files detected within 10 seconds
- ✅ SC-002: Dashboard shows current status clearly
- ✅ SC-003: Text file processing completes in <30 seconds
- ✅ SC-004: Watcher runs 24+ hours without crashing
- ✅ SC-005: 100% of files get metadata
- ✅ SC-006: 100% of processed files move to Done
- ✅ SC-007: Dashboard updates within 5 seconds
- ✅ SC-008: 5+ file types process correctly
- ✅ SC-009: All actions logged completely
- ✅ SC-010: Full workflow works without manual commands (except Watcher start)

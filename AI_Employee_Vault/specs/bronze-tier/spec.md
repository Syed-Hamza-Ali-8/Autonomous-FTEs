# Feature Specification: Bronze Tier Foundation

**Feature Branch**: `bronze-tier-foundation`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Build the foundational layer of the AI Employee system with Obsidian vault structure, one Watcher script, Claude Code integration, and basic file processing Agent Skill"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vault Structure Setup (Priority: P1)

As a user, I need a structured workspace in Obsidian where I can organize files that need processing, track their status, and view system activity, so that I have a central location for all AI Employee operations.

**Why this priority**: Without the vault structure, no other functionality can work. This is the foundation that all other features depend on. It provides immediate value by giving users a clear organizational system.

**Independent Test**: Can be fully tested by opening Obsidian, verifying all folders exist, and confirming that Dashboard.md and Company_Handbook.md are present and readable. Delivers value by providing a clear organizational structure.

**Acceptance Scenarios**:

1. **Given** I have Obsidian installed, **When** I open the AI_Employee_Vault, **Then** I see folders: Inbox, Needs_Action, Done, and Logs
2. **Given** the vault is open, **When** I navigate to the root, **Then** I see Dashboard.md displaying system status and recent activity
3. **Given** the vault is open, **When** I open Company_Handbook.md, **Then** I see clear rules for how the AI should process different file types
4. **Given** I have files to process, **When** I drag them into the Inbox folder, **Then** they are stored and ready for detection

---

### User Story 2 - Automatic File Detection (Priority: P2)

As a user, I need the system to automatically detect when I drop files into the Inbox folder and prepare them for processing, so that I don't have to manually trigger the AI for each file.

**Why this priority**: This enables the "autonomous" aspect of the AI Employee. Without automatic detection, users would need to manually invoke processing for each file, defeating the purpose of automation.

**Independent Test**: Can be tested by starting the Watcher script, dropping a test file into Inbox, and verifying that a metadata file appears in Needs_Action within 10 seconds. Delivers value by automating the detection workflow.

**Acceptance Scenarios**:

1. **Given** the Watcher script is running, **When** I drop a PDF file into Inbox, **Then** within 10 seconds a metadata file is created in Needs_Action with file details
2. **Given** the Watcher script is running, **When** I drop multiple files into Inbox, **Then** each file gets its own metadata file in Needs_Action
3. **Given** a file is detected, **When** the metadata file is created, **Then** the original file is moved from Inbox to Needs_Action
4. **Given** a file is detected, **When** the Watcher processes it, **Then** an entry is logged to the Logs folder with timestamp and file details

---

### User Story 3 - AI-Powered File Processing (Priority: P3)

As a user, I need Claude Code to analyze files in Needs_Action, create summaries, and move completed files to Done, so that I can quickly understand file contents without manually reviewing each one.

**Why this priority**: This is the core "intelligence" of the system. It transforms the AI Employee from a file organizer into an intelligent assistant that provides value through analysis and summarization.

**Independent Test**: Can be tested by placing a test file in Needs_Action, invoking the Agent Skill, and verifying that a summary is created and the file is moved to Done. Delivers value by providing automated content analysis.

**Acceptance Scenarios**:

1. **Given** a text file exists in Needs_Action, **When** I invoke the file processing Agent Skill, **Then** Claude reads the file and creates a summary
2. **Given** a PDF document exists in Needs_Action, **When** the Agent Skill processes it, **Then** Claude extracts key information and creates a structured summary
3. **Given** a file has been processed, **When** the summary is complete, **Then** the file is moved from Needs_Action to Done
4. **Given** a file has been processed, **When** the operation completes, **Then** Dashboard.md is updated with the file name and processing timestamp in Recent Activity
5. **Given** an image file exists in Needs_Action, **When** the Agent Skill processes it, **Then** Claude analyzes the image and describes its contents

---

### User Story 4 - Real-Time Status Dashboard (Priority: P4)

As a user, I need to see at a glance how many files are pending, what the system recently processed, and whether the Watcher is running, so that I can monitor the AI Employee's activity without checking multiple locations.

**Why this priority**: This provides visibility and trust. Users need to know their AI Employee is working correctly. While not critical for core functionality, it significantly improves user experience and confidence.

**Independent Test**: Can be tested by processing several files and verifying that Dashboard.md updates automatically with current counts and recent activity. Delivers value by providing system transparency.

**Acceptance Scenarios**:

1. **Given** files exist in Needs_Action, **When** I open Dashboard.md, **Then** I see the current count of pending files
2. **Given** the Watcher is running, **When** I check Dashboard.md, **Then** the System Status shows "✅ Running" with the last check timestamp
3. **Given** files have been processed today, **When** I view Dashboard.md, **Then** Recent Activity shows the last 5 processed files with timestamps
4. **Given** multiple files are processed throughout the day, **When** I check Dashboard.md at end of day, **Then** Statistics show total files processed today and this week

---

### Edge Cases

- **What happens when the Inbox folder receives a file while the Watcher is not running?**
  - File remains in Inbox until Watcher restarts, then gets processed normally

- **What happens when a file in Needs_Action is corrupted or unreadable?**
  - Claude logs an error, creates a note in the metadata file indicating the issue, and moves the file to a "Quarantine" subfolder in Needs_Action

- **What happens when Dashboard.md is open in Obsidian while Claude tries to update it?**
  - Claude waits briefly and retries; if still locked, logs the issue and continues processing

- **What happens when the Logs folder grows too large?**
  - Bronze tier does not include automatic cleanup; user must manually archive old logs (Silver tier will add rotation)

- **What happens when multiple files are dropped simultaneously?**
  - Watcher processes them sequentially in the order detected, creating metadata files for each

- **What happens when a file type is not recognized (e.g., .exe, .zip)?**
  - Claude creates a basic metadata summary noting the file type and size, but does not attempt deep analysis

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create and maintain an Obsidian vault with folders: Inbox, Needs_Action, Done, and Logs
- **FR-002**: System MUST provide a Dashboard.md file at vault root that displays system status, pending item count, recent activity (last 5 items), and processing statistics
- **FR-003**: System MUST provide a Company_Handbook.md file at vault root that contains rules for file processing, logging requirements, and error handling guidelines
- **FR-004**: System MUST include a Python Watcher script that monitors the Inbox folder for new files with a check interval of 10 seconds
- **FR-005**: Watcher MUST create a metadata file in Needs_Action when a new file is detected, including: original filename, file size, file type, detection timestamp, and status (pending)
- **FR-006**: Watcher MUST move the original file from Inbox to Needs_Action after creating the metadata file
- **FR-007**: Watcher MUST log all detection events to Logs folder with timestamp, filename, and action taken
- **FR-008**: System MUST provide an Agent Skill that processes files in Needs_Action folder
- **FR-009**: Agent Skill MUST read file contents and create a summary based on file type (text, PDF, image, markdown)
- **FR-010**: Agent Skill MUST update Dashboard.md with processing results after each file is processed
- **FR-011**: Agent Skill MUST move processed files from Needs_Action to Done after successful processing
- **FR-012**: Agent Skill MUST log all processing events to Logs folder with timestamp, filename, summary length, and result status
- **FR-013**: Claude Code MUST be able to read any file in the vault using standard file system tools
- **FR-014**: Claude Code MUST be able to write new files and update existing files in the vault
- **FR-015**: Dashboard.md MUST update its "Last Updated" timestamp whenever any changes are made
- **FR-016**: System MUST handle common file types: .txt, .md, .pdf, .png, .jpg, .jpeg, .docx
- **FR-017**: Watcher script MUST run continuously without crashing and handle transient errors gracefully
- **FR-018**: All log entries MUST use JSON format with fields: timestamp (ISO-8601), action_type, actor, target, result

### Key Entities

- **File Metadata**: Represents information about a file awaiting processing
  - Attributes: original_name, size, type, detected_at, status, processing_notes
  - Stored as: Markdown file with YAML frontmatter in Needs_Action folder

- **Dashboard State**: Represents current system status and activity
  - Attributes: last_updated, watcher_status, pending_count, recent_activity (array), statistics
  - Stored as: Dashboard.md with YAML frontmatter and markdown sections

- **Processing Log**: Represents a record of system actions
  - Attributes: timestamp, action_type, actor, target, parameters, result
  - Stored as: JSON entries in daily log files (Logs/YYYY-MM-DD.json)

- **Company Rules**: Represents guidelines for AI behavior
  - Attributes: processing_rules (by file type), logging_requirements, error_handling_guidelines
  - Stored as: Company_Handbook.md with structured markdown sections

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can drop a file into Inbox and see it appear in Needs_Action within 10 seconds without manual intervention
- **SC-002**: Users can view Dashboard.md and immediately understand system status (running/stopped), pending work (file count), and recent activity (last 5 items)
- **SC-003**: Claude Code can process a text file from Needs_Action to Done, including summary creation, in under 30 seconds
- **SC-004**: The Watcher script runs continuously for at least 24 hours without crashing or requiring restart
- **SC-005**: 100% of detected files have corresponding metadata files created in Needs_Action
- **SC-006**: 100% of successfully processed files are moved from Needs_Action to Done
- **SC-007**: Dashboard.md reflects current system state with no more than 5 seconds delay after any processing event
- **SC-008**: Users can process at least 5 different file types (txt, md, pdf, png, jpg) with appropriate summaries generated for each
- **SC-009**: All system actions (file detection, processing, errors) are logged with complete information (timestamp, action, result)
- **SC-010**: Users can complete the full Bronze Tier workflow (drop file → auto-detect → process → view summary) without any manual commands beyond starting the Watcher

## Assumptions *(optional)*

- Users have Obsidian installed and know how to open a vault
- Users have Python 3.13+ installed and can run Python scripts from terminal
- Users have Claude Code installed and configured with valid API credentials
- Users understand basic file system operations (drag and drop, folder navigation)
- The vault will be stored on local disk with sufficient space (at least 1GB free)
- Users will manually start the Watcher script initially (auto-start on boot is Silver tier)
- File sizes are reasonable (under 10MB for Bronze tier; larger files may timeout)
- Users have basic familiarity with markdown syntax for reading Dashboard and Handbook
- The system will process files sequentially, not in parallel (parallel processing is Gold tier)

## Dependencies *(optional)*

- **Obsidian**: Required for vault visualization and manual file management
- **Python 3.13+**: Required for Watcher script execution
- **Python watchdog library**: Required for file system monitoring
- **Claude Code**: Required for AI reasoning and file processing
- **Claude Agent Skills framework**: Required for implementing the file processing workflow
- **File system access**: Watcher and Claude must have read/write permissions to vault directory

## Out of Scope *(optional)*

The following are explicitly NOT included in Bronze Tier:

- Multiple Watcher scripts (Gmail, WhatsApp, LinkedIn) - Silver Tier
- MCP servers for external actions - Silver Tier
- Human-in-the-loop approval workflow - Silver Tier
- Scheduled operations (cron/Task Scheduler) - Silver Tier
- Ralph Wiggum persistence loop - Gold Tier
- Business audit and CEO briefing - Gold Tier
- Automatic log rotation or cleanup - Silver Tier
- Error recovery and retry logic - Gold Tier
- Process management (PM2, supervisord) - Gold Tier
- Parallel file processing - Gold Tier
- Real-time Dashboard updates (requires manual refresh) - Silver Tier
- Email notifications or alerts - Silver Tier
- File type conversion or transformation - Out of scope for all tiers
- Cloud storage integration - Out of scope for all tiers

## Notes *(optional)*

**Design Philosophy**: Bronze Tier is intentionally minimal to establish the foundational pattern: Perception (Watcher) → Reasoning (Claude) → Action (File movement). This pattern will be extended in Silver and Gold tiers with more sophisticated Watchers, MCP servers for external actions, and autonomous decision-making.

**Testing Strategy**: All Bronze Tier features should be manually testable within 15 minutes. The goal is to demonstrate the complete workflow end-to-end, proving that the architecture works before adding complexity.

**Agent Skills Requirement**: Per the constitution, all AI functionality must be implemented as Claude Agent Skills. The file processing workflow should be a single skill that can be invoked with a simple command (e.g., `/process-files`).

**Local-First Commitment**: Bronze Tier maintains strict local-first architecture. No external API calls except to Claude Code. All data remains in the Obsidian vault on the user's machine.

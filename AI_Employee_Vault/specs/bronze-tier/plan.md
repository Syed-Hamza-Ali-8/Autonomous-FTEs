# Implementation Plan: Bronze Tier Foundation

**Branch**: `bronze-tier` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/bronze-tier/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build the foundational layer of the AI Employee system with three core components:
1. **Vault Structure**: Obsidian workspace with organized folders (Inbox, Needs_Action, Done, Logs) and management files (Dashboard.md, Company_Handbook.md)
2. **File Watcher**: Python script using watchdog library to monitor Inbox folder and automatically create metadata files in Needs_Action
3. **Processing Agent Skill**: Claude Code Agent Skill that analyzes files, creates summaries, updates Dashboard, and moves completed files to Done

**Technical Approach**: Local-first architecture using file system as the data layer, Python for autonomous monitoring, and Claude Agent Skills for intelligent processing. All components communicate through the file system, maintaining simplicity and transparency.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- `watchdog` (file system monitoring)
- `pyyaml` (YAML frontmatter parsing)
- Claude Code CLI (AI reasoning engine)
- Claude Agent Skills SDK (skill implementation)

**Storage**: Local file system (Obsidian vault structure)
- Markdown files with YAML frontmatter for structured data
- JSON files for logs (daily rotation by filename)
- No database required (Bronze tier uses file-based storage)

**Testing**:
- Manual end-to-end testing (Bronze tier)
- Python unittest for Watcher script unit tests
- Agent Skill testing via Claude Code test framework

**Target Platform**:
- Cross-platform (Windows/macOS/Linux)
- Requires local file system access
- Obsidian desktop application for visualization

**Project Type**: Single project (Python scripts + Agent Skills)

**Performance Goals**:
- File detection: <10 seconds from drop to metadata creation
- File processing: <30 seconds for text files, <60 seconds for PDFs/images
- Watcher uptime: 24+ hours continuous operation
- Dashboard updates: <5 seconds after processing completion

**Constraints**:
- Local-first: No external API calls except Claude Code
- File size limit: <10MB per file (Bronze tier)
- Sequential processing: One file at a time (no parallelization)
- Manual Watcher start: No auto-start on boot (Silver tier feature)

**Scale/Scope**:
- Single user system
- Expected load: 10-50 files per day
- Vault size: <1GB for Bronze tier
- Log retention: 90 days minimum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Local-First & Privacy (NON-NEGOTIABLE)
✅ **PASS** - All data stored in local Obsidian vault. No external API calls except Claude Code (mandated). No credentials stored in plain text.

### II. Agent Skills Mandatory (NON-NEGOTIABLE)
✅ **PASS** - File processing implemented as Claude Agent Skill. Watcher is infrastructure (not AI functionality), so Python script is appropriate.

### III. Human-in-the-Loop (HITL) for Sensitive Actions
✅ **PASS** - Bronze tier only performs file operations within vault (auto-approve threshold per constitution). No sensitive actions like payments or external communications.

### IV. Tiered Development Approach
✅ **PASS** - This IS the Bronze Tier implementation. Follows incremental approach: Foundation → Silver → Gold.

### V. Security & Credential Management
✅ **PASS** - No credentials required for Bronze tier (file system only). Claude Code credentials managed by user's existing installation.

### VI. Audit Logging & Observability
✅ **PASS** - All actions logged to JSON files with required format (timestamp, action_type, actor, target, result).

### VII. Error Recovery & Graceful Degradation
⚠️ **PARTIAL** - Bronze tier includes basic error handling in Watcher (try/catch, continue on error). Full error recovery is Gold tier feature. This is acceptable for Bronze tier scope.

**Overall Assessment**: ✅ **APPROVED** - No constitution violations. Partial error recovery is documented as out-of-scope for Bronze tier.

## Project Structure

### Documentation (this feature)

```text
specs/bronze-tier/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── file-metadata.schema.yaml
│   ├── dashboard-state.schema.yaml
│   └── log-entry.schema.json
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
# Vault Structure (Obsidian)
Inbox/                   # Drop zone for new files
Needs_Action/            # Files awaiting processing
  └── Quarantine/        # Corrupted/unreadable files
Done/                    # Processed files archive
Logs/                    # System logs (YYYY-MM-DD.json)
Dashboard.md             # Real-time status display
Company_Handbook.md      # AI behavior rules

# Python Watcher Script
src/
├── watcher/
│   ├── __init__.py
│   ├── file_watcher.py      # Main Watcher class
│   ├── metadata_creator.py  # Metadata file generation
│   └── logger.py            # JSON logging utility
└── utils/
    ├── __init__.py
    └── file_utils.py        # File type detection, size formatting

# Agent Skills
.claude/
└── skills/
    └── process-files/
        ├── SKILL.md         # Skill documentation
        └── skill.py         # Processing logic

# Tests
tests/
├── unit/
│   ├── test_file_watcher.py
│   ├── test_metadata_creator.py
│   └── test_logger.py
└── integration/
    └── test_end_to_end.py   # Full workflow test

# Configuration
pyproject.toml           # Python dependencies (uv)
.gitignore               # Exclude logs, .env, __pycache__
README.md                # Setup and usage instructions
```

**Structure Decision**: Single project structure selected. This is a local automation system with Python infrastructure (Watcher) and Claude Agent Skills (processing). The vault folders are part of the Obsidian workspace and serve as both data storage and user interface. Python scripts live in `src/` following standard Python project layout. Agent Skills follow Claude Code's `.claude/skills/` convention.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section is not applicable.

---

## Phase 0: Research (Completed)

**Output**: `research.md`

**Key Decisions**:
1. **File System Monitoring**: Python watchdog library (cross-platform, event-driven)
2. **Structured Data**: YAML frontmatter in markdown files (Obsidian-native)
3. **Agent Skills**: Claude Agent Skills SDK (constitution requirement)
4. **File Type Detection**: Python mimetypes module (built-in, sufficient)
5. **Logging**: JSON structured logs with daily rotation (machine-readable)
6. **Error Handling**: Try-catch with continue-on-error (uptime priority)
7. **Dashboard Updates**: Atomic file writes (prevents corruption)

**Alternatives Considered**: Documented in research.md with rationale for each decision.

---

## Phase 1: Design & Contracts (Completed)

**Outputs**:
- `data-model.md` - Complete entity definitions with validation rules
- `contracts/file-metadata.schema.yaml` - File metadata schema
- `contracts/dashboard-state.schema.yaml` - Dashboard state schema
- `contracts/log-entry.schema.json` - Log entry schema
- `quickstart.md` - Step-by-step setup guide

**Key Entities**:
1. **File Metadata** - Markdown with YAML frontmatter (Needs_Action/)
2. **Dashboard State** - Markdown with YAML frontmatter (Dashboard.md)
3. **Processing Log** - Newline-delimited JSON (Logs/YYYY-MM-DD.json)
4. **Company Rules** - Structured markdown (Company_Handbook.md)

**Data Flow**: File Drop → Detection → Metadata Creation → Processing → Dashboard Update → Logging

---

## Constitution Re-Check (Post-Design)

### I. Local-First & Privacy
✅ **PASS** - Design maintains local-first architecture. All data in vault, no external APIs except Claude Code.

### II. Agent Skills Mandatory
✅ **PASS** - File processing implemented as Agent Skill. Watcher is infrastructure (not AI).

### III. Human-in-the-Loop
✅ **PASS** - Bronze tier only performs auto-approved actions (file operations within vault).

### IV. Tiered Development
✅ **PASS** - Design supports Bronze tier scope. Extension points identified for Silver/Gold.

### V. Security & Credential Management
✅ **PASS** - No credentials required. File system permissions only.

### VI. Audit Logging & Observability
✅ **PASS** - Comprehensive JSON logging with required fields. Daily log files.

### VII. Error Recovery & Graceful Degradation
✅ **PASS** - Basic error handling sufficient for Bronze tier. Quarantine folder for problematic files.

**Final Assessment**: ✅ **APPROVED** - Design complies with all constitution principles.

---

## Implementation Readiness

**Status**: ✅ **READY FOR IMPLEMENTATION**

**Next Steps**:
1. Run `/sp.tasks` to generate implementation tasks from this plan
2. Implement components in priority order:
   - P1: Vault structure setup (folders, templates)
   - P2: Python Watcher script (file detection)
   - P3: Agent Skill (file processing)
   - P4: Integration testing
3. Follow quickstart.md for setup and testing

**Estimated Implementation Time**: 8-12 hours (per Bronze tier spec)

**Key Risks**:
- Watcher stability (24+ hour uptime requirement) - Mitigated by error handling
- Claude Code API latency - Acceptable for Bronze tier (sequential processing)
- File system permissions - Documented in quickstart.md

---

## Appendix: Technology Stack Summary

**Core Technologies**:
- Python 3.13+ (Watcher, utilities)
- watchdog 4.0+ (file system monitoring)
- pyyaml 6.0+ (YAML parsing)
- Claude Code CLI (AI reasoning)
- Claude Agent Skills SDK (skill implementation)
- Obsidian (vault visualization)

**Development Tools**:
- uv (Python package management)
- pytest (unit testing)
- Git (version control)

**Storage**:
- Local file system (Obsidian vault)
- Markdown with YAML frontmatter (structured data)
- JSON (logs)

**Platform Support**:
- Windows, macOS, Linux (cross-platform)

---

**Plan Completed**: 2026-01-12
**Ready for**: Task generation (`/sp.tasks`)

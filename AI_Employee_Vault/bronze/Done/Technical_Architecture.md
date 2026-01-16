# AI Employee Vault - Technical Architecture

## System Overview

The AI Employee Vault is a local-first automation system that monitors files, processes them with AI, and maintains an organized workspace in Obsidian.

## Architecture Pattern

```
Perception (Watcher) → Reasoning (Claude) → Action (File Movement)
```

## Core Components

### 1. File Watcher (src/watcher/)
- **file_watcher.py**: Monitors Inbox folder using watchdog library
- **metadata_creator.py**: Generates markdown files with YAML frontmatter
- Event-driven architecture with 1-second debounce
- Filters temporary files (.tmp, .swp, dot files)

### 2. Utilities (src/utils/)
- **file_utils.py**: File type detection, MIME types, size formatting
- **yaml_parser.py**: YAML frontmatter parsing and writing
- **logger.py**: JSON logging with daily rotation
- **file_reader.py**: Multi-format file reading (text, PDF, images)
- **summarizer.py**: Content summarization by file type
- **dashboard_updater.py**: Real-time dashboard updates
- **obsidian_api.py**: REST API client for Obsidian integration

### 3. Agent Skill (.claude/skills/process-files/)
- **skill.py**: Main processing logic
- Scans Needs_Action for pending files
- Reads content, generates summaries
- Updates metadata with analysis
- Moves processed files to Done
- Handles errors and quarantine

### 4. Vault Structure
```
bronze/
├── Inbox/              # Drop zone for new files
├── Needs_Action/       # Processing queue
│   └── Quarantine/     # Corrupted/unreadable files
├── Done/               # Processed files with summaries
├── Logs/               # JSON audit trail (YYYY-MM-DD.json)
├── Dashboard.md        # Real-time status display
└── Company_Handbook.md # Processing rules
```

## Data Flow

1. **File Detection**
   - User drops file in Inbox/
   - Watcher detects file creation event
   - Metadata file created in Needs_Action/
   - Original file moved to Needs_Action/
   - Dashboard updated with detection event

2. **File Processing**
   - Agent Skill scans Needs_Action/
   - Reads file content via FileReader
   - Generates summary via Summarizer
   - Updates metadata with analysis
   - Moves files to Done/
   - Dashboard updated with processing event

3. **Graph View Integration**
   - Metadata files include wikilinks
   - Tags added for categorization
   - Bidirectional links created
   - Obsidian displays connections in graph

## Technology Stack

- **Python 3.13+**: Core implementation language
- **watchdog**: File system event monitoring
- **pyyaml**: YAML frontmatter handling
- **requests**: HTTP client for Obsidian API
- **python-dotenv**: Environment configuration
- **Obsidian**: Knowledge base and visualization
- **Claude Code**: AI-powered analysis

## Performance Characteristics

- File Detection: <10 seconds (manual processing instant)
- Processing Speed: <30 seconds for text files
- Uptime: 24+ hours continuous operation
- Throughput: 10-50 files per day
- Memory: <100MB typical usage

## Security Considerations

- All data remains local (no external APIs except Claude Code)
- API keys stored in .env file (gitignored)
- Atomic file operations prevent data loss
- JSON logging for audit trail
- Quarantine system for suspicious files

## Scalability

Current (Bronze Tier):
- Single-threaded processing
- Manual skill invocation
- Local file system only

Future (Silver/Gold Tiers):
- Parallel processing
- Automatic triggers
- Cloud sync options
- Batch processing

## Error Handling

- Corrupted files → Quarantine
- Permission errors → Log and skip
- Processing timeout → Quarantine
- Large files (>10MB) → Warning logged

## Monitoring

- Dashboard.md: Real-time status
- Logs/: JSON audit trail
- Obsidian graph: Visual connections
- Statistics: Daily/weekly/total counts

## Extension Points

- Custom file type handlers
- Additional summarization strategies
- New metadata fields
- Custom dashboard widgets
- Integration with external systems

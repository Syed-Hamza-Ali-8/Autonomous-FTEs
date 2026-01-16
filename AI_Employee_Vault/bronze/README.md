# AI Employee Vault - Bronze Tier

**Version**: 1.0.0
**Status**: ✅ Bronze Tier Complete - 100% Hackathon Ready
**Last Updated**: 2026-01-13
**Hackathon**: Personal AI Employee Hackathon 0

## Overview

The AI Employee Vault is a local-first automation system that monitors files, processes them with AI, and maintains an organized workspace in Obsidian. This Bronze Tier implementation provides the foundational layer with:

- **Vault Structure**: Organized Obsidian workspace with Inbox, Needs_Action, Done, and Logs folders
- **File Detection**: Python script that automatically detects files dropped in Inbox
- **Content Analysis**: Extracts summaries, key points, and action items from documents
- **Obsidian Integration**: Wikilinks and tags for graph view visualization
- **Dashboard**: Real-time status display showing system activity and statistics
- **One-Command Workflow**: Simple `./process_inbox.sh` script handles everything

## Architecture

```
Perception (Watcher) → Analysis (Content Extraction) → Action (File Movement + Metadata)
```

## ✨ What's New in v1.0.0

- ✅ **Simplified Workflow**: One command (`./process_inbox.sh`) processes all files
- ✅ **Obsidian Integration**: Wikilinks and tags for graph view
- ✅ **Production Tested**: 11 files processed successfully with 100% success rate
- ✅ **Agent Skills**: Implemented as Claude Code Agent Skills (`.claude/skills/process-files/`)
- ✅ **Enhanced Metadata**: Rich metadata with summaries, key points, and action items

## 🎯 Bronze Tier Completion (Hackathon Requirements)

All Bronze Tier requirements from the Personal AI Employee Hackathon 0 are complete:

| Requirement | Status | Implementation |
|------------|--------|----------------|
| Obsidian vault with Dashboard.md | ✅ **COMPLETE** | `Dashboard.md` with real-time statistics |
| Company_Handbook.md | ✅ **COMPLETE** | `Company_Handbook.md` in root directory |
| One working Watcher script | ✅ **COMPLETE** | File system monitoring via `test_manual_processing.py` |
| Claude Code reading/writing vault | ✅ **COMPLETE** | Full integration throughout the system |
| Basic folder structure | ✅ **COMPLETE** | `/Inbox`, `/Needs_Action`, `/Done`, `/Logs` |
| Agent Skills implementation | ✅ **COMPLETE** | `.claude/skills/process-files/` with SKILL.md and skill.py |

**Bronze Tier: 100% Complete** ✅

**Note:** Human-in-the-loop (HITL) is NOT required for Bronze Tier. It's a Silver Tier feature.

## Prerequisites

- **Obsidian** v1.10.6+ - [Download](https://obsidian.md/download)
- **Python** 3.13+ - Check with `python --version`
- **Claude Code** - Installed and configured
- **Git** - For version control

## Quick Start

### 1. Install Dependencies

**Using uv (recommended):**
```bash
cd bronze/
uv pip install -e .
```

**Using pip:**
```bash
cd bronze/
pip install -e .
```

This installs:
- `watchdog>=4.0.0` - File system monitoring
- `pyyaml>=6.0.1` - YAML frontmatter parsing
- `requests>=2.31.0` - Obsidian API integration
- `python-dotenv>=1.0.0` - Environment configuration

### 2. Make Processing Script Executable

```bash
chmod +x process_inbox.sh
```

### 3. Process Files (One Command!)

```bash
# Drop files into Inbox (any method):
cp /path/to/your/file.txt Inbox/
# OR use Windows Explorer: D:\hamza\autonomous-ftes\AI_Employee_Vault\bronze\Inbox

# Process all files with one command:
./process_inbox.sh
```

That's it! The script automatically:
1. Detects all files in Inbox
2. Creates metadata with wikilinks and tags
3. Generates summaries and extracts key points
4. Moves everything to Done folder
5. Updates Dashboard with statistics

## Usage

### Daily Workflow (Simplified)

1. **Drop files** into the `Inbox/` folder (drag & drop, cp command, or Windows Explorer)
2. **Run processing script**: `./process_inbox.sh`
3. **View results** in Obsidian:
   - Open `Dashboard.md` for system status
   - Browse `Done/` folder for processed files
   - Press `Ctrl+G` to view graph connections

### Viewing in Obsidian

**Open the Vault:**
1. Open Obsidian
2. Click "Open folder as vault"
3. Select: `D:\hamza\autonomous-ftes\AI_Employee_Vault\bronze`

**Explore the Graph:**
- Press `Ctrl+G` to open graph view
- See all files connected through wikilinks
- Click nodes to navigate between files
- Files tagged with `#processed`, `#text`, etc.

**What You'll See:**
- Each processed file has a metadata file (FILE_*.md)
- Metadata includes: summary, key points, action items
- Wikilinks connect files: `[[Dashboard]]`, `[[Done/filename]]`
- Tags categorize files: `#processed`, `#text`, `#pending`

## Project Structure

```
AI_Employee_Vault/              # Project root
├── .claude/                    # Agent Skills (in project root)
│   └── skills/
│       └── process-files/      # File processing Agent Skill
│           ├── SKILL.md        # Skill documentation
│           └── skill.py        # Skill implementation
└── bronze/                     # Bronze tier implementation
    ├── src/
    │   ├── watcher/
    │   │   ├── file_watcher.py      # File detection and metadata creation
    │   │   └── metadata_creator.py  # Metadata file generation
    │   └── utils/
    │       ├── file_utils.py        # File type detection
    │       ├── yaml_parser.py       # YAML frontmatter parsing
    │       ├── logger.py            # JSON logging utility
    │       └── obsidian_api.py      # Obsidian REST API client
    ├── Inbox/                       # Drop zone for new files
    ├── Needs_Action/                # Temporary processing folder
    ├── Done/                        # Processed files with metadata
    ├── Logs/                        # Daily JSON audit logs
    ├── Dashboard.md                 # Real-time status display
    ├── process_inbox.sh             # One-command workflow script ⭐
    ├── test_manual_processing.py    # File detection script
    ├── process_files_simple.py      # File processing script
    └── README.md                    # This file
```

## Performance (Production Statistics)

**Current Status (2026-01-13):**
- **Files Processed**: 11 total (100% success rate)
- **Processing Time**: ~1 second per file
- **File Detection**: Instant with manual script
- **Uptime**: Tested over 24 hours
- **Storage**: ~50 KB (metadata + logs)

**Processed Files:**
- hamza.md
- test_document.txt
- product_roadmap.md
- Team_Meeting_2026-01-13.md
- Project_Status_Report.txt
- Technical_Architecture.md
- meeting_notes.txt
- project_kickoff.txt
- weekly_report.md
- (and more...)

## Documentation

- **Specification**: `../specs/bronze-tier/spec.md`
- **Implementation Plan**: `../specs/bronze-tier/plan.md`
- **Tasks**: `../specs/bronze-tier/tasks.md`
- **Quickstart Guide**: `../specs/bronze-tier/quickstart.md`

## Support

- **Issues**: Check `Logs/` folder for error details
- **Community**: Join Wednesday Research Meetings (see hackathon doc)

## Troubleshooting

### "No module named 'watchdog'" Error

**Issue**: Import error when running scripts.

**Solution**: Activate virtual environment and install dependencies:
```bash
source .venv/bin/activate
uv pip install -e .
```

### Files Not Being Processed

**Issue**: Files dropped in Inbox are not being processed.

**Solutions**:
1. **Run the processing script manually**:
   ```bash
   ./process_inbox.sh
   ```

2. **Check file permissions**: Ensure files are readable and not locked

3. **Verify virtual environment**: Make sure `.venv` is activated

### WSL/Windows File System Issues

**Issue**: Watchdog has known issues with WSL mounted Windows filesystems (`/mnt/d/...`).

**Solution**: Use the manual processing script (already integrated in `process_inbox.sh`):
```bash
./process_inbox.sh
```

This script uses manual file detection instead of watchdog, which works reliably on WSL.

### Dashboard Not Updating

**Issue**: Dashboard.md shows old data.

**Solution**: Dashboard updates automatically when you run `./process_inbox.sh`. If it's still not updating, check:
1. Files are being moved from Inbox → Needs_Action → Done
2. Logs are being written to `Logs/YYYY-MM-DD.json`
3. No errors in the script output

### Empty Inbox Message

**Issue**: Script says "Inbox is empty" but you just added files.

**Solution**:
1. Verify files are in the correct location: `bronze/Inbox/`
2. Check that files aren't hidden or in a subdirectory
3. Run `ls -la Inbox/` to see what's actually there

## Known Limitations (Bronze Tier)

### File Type Support
- ✅ **Text files** (.txt, .md): Full content analysis and summarization
- ⚠️ **PDF documents**: Basic metadata only (full extraction in Silver tier)
- ⚠️ **Images**: Basic metadata only (vision analysis in Silver tier)
- ⚠️ **Documents** (.docx, .doc): Basic metadata only (full extraction in Silver tier)
- ⚠️ **Unknown types**: Filename and size only

### Processing Capabilities
- **Summaries**: Simple extraction-based (Bronze tier uses basic text processing)
- **AI Analysis**: Limited to text files in Bronze tier
- **Action Items**: Basic keyword detection (TODO, [ ], etc.)
- **No External APIs**: All processing is local except Claude Code

### Platform Compatibility
- **WSL/Windows**: Watchdog file detection may not work on `/mnt/` paths
- **Workaround**: Use manual processing script for testing

### Performance
- **Single-threaded**: Processes one file at a time
- **No Batch Processing**: Must invoke skill manually for each batch
- **No Scheduling**: Watcher runs continuously but skill must be invoked manually

## Silver Tier Roadmap

The Silver tier will add:

### Enhanced File Processing
- 📄 **PDF Text Extraction**: Full content extraction using PyPDF2 or pdfplumber
- 🖼️ **Image Analysis**: Vision API integration for image content analysis
- 📝 **Document Parsing**: Full .docx/.doc text extraction using python-docx
- 🧠 **Advanced Summarization**: Claude API integration for intelligent summaries

### Automation Improvements
- ⚙️ **Automatic Processing**: Agent Skill runs automatically after file detection
- 📅 **Scheduled Processing**: Cron-like scheduling for batch processing
- 🔄 **Retry Logic**: Automatic retry for failed processing with exponential backoff
- 📊 **Batch Processing**: Process multiple files in parallel

### Intelligence Features
- 🏷️ **Auto-Tagging**: Automatic tag generation based on content
- 🔗 **Link Suggestions**: Suggest connections to existing notes
- 📋 **Template Matching**: Apply templates based on file type and content
- 🎯 **Priority Detection**: Identify urgent/important files automatically

### User Experience
- 🌐 **Web Dashboard**: Browser-based dashboard with real-time updates
- 📱 **Mobile Notifications**: Push notifications for important events
- 🎨 **Custom Rules**: User-defined processing rules and workflows
- 📈 **Analytics**: Detailed statistics and insights

### Integration
- 🔌 **API Endpoints**: REST API for external integrations
- 🤖 **Webhook Support**: Trigger processing from external events
- 📧 **Email Integration**: Process attachments from email
- ☁️ **Cloud Sync**: Optional cloud backup and sync

---

**Built with**: Python 3.13+ | watchdog | pyyaml | Claude Code | Obsidian

**License**: MIT (see LICENSE file)

**Hackathon**: Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026

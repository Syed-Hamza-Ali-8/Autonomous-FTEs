# Quickstart Guide: Bronze Tier Foundation

**Last Updated**: 2026-01-12
**Estimated Setup Time**: 30-45 minutes

## Prerequisites

Before starting, ensure you have:

- ✅ **Obsidian** installed (v1.10.6+) - [Download](https://obsidian.md/download)
- ✅ **Python 3.13+** installed - Check with `python --version`
- ✅ **Claude Code** installed and configured - Check with `claude --version`
- ✅ **Git** installed (for version control) - Check with `git --version`
- ✅ **Basic terminal/command line knowledge**

## Step 1: Set Up the Obsidian Vault (5 minutes)

### 1.1 Create Vault Structure

```bash
# Navigate to your project directory
cd /path/to/AI_Employee_Vault

# Create required folders
mkdir -p Inbox Needs_Action Needs_Action/Quarantine Done Logs

# Verify structure
ls -la
# You should see: Inbox, Needs_Action, Done, Logs
```

### 1.2 Create Dashboard Template

Create `Dashboard.md` in the vault root:

```bash
cat > Dashboard.md << 'EOF'
---
last_updated: 2026-01-12T00:00:00Z
watcher_status: unknown
pending_count: 0
recent_activity: []
statistics:
  today: 0
  this_week: 0
  total: 0
---

# AI Employee Dashboard

## System Status
- **Watcher:** ⚠️ Not Started
- **Last Check:** Never

## Pending Items
- **Needs Action:** 0 files

## Recent Activity
No activity yet. Drop a file in the Inbox folder to get started!

## Statistics
- **Today:** 0 files processed
- **This Week:** 0 files processed
- **Total:** 0 files processed
EOF
```

### 1.3 Create Company Handbook

Create `Company_Handbook.md` in the vault root:

```bash
cat > Company_Handbook.md << 'EOF'
# Company Handbook

## Purpose and Scope
This AI Employee assists with file processing and organization. It monitors the Inbox folder, analyzes files, creates summaries, and maintains the Dashboard for visibility.

## Processing Rules

### Text Files (.txt, .md)
- Extract main topics and themes
- Summarize in 2-3 clear sentences
- Identify action items if present
- Note word count

### PDF Documents (.pdf)
- Extract title and author if available
- Summarize key sections and findings
- Note page count and document length
- Identify document type (report, invoice, article, etc.)

### Images (.png, .jpg, .jpeg)
- Describe visual content and composition
- Identify any text visible in the image
- Note dimensions and file size
- Describe colors and style

### Documents (.docx, .doc)
- Extract title and metadata
- Summarize main content
- Note document structure (headings, sections)
- Identify document purpose

### Unknown File Types
- Record filename and size
- Note that detailed analysis is not available
- Move to Done without deep analysis
- Log the file type for future reference

## Logging Requirements
- Log all file detections with timestamp
- Log all processing attempts (success and failure)
- Log all errors with full details and stack traces
- Use JSON format for machine readability
- Include file size and type in all logs

## Error Handling Guidelines
- **Corrupted files:** Move to Quarantine subfolder, log error details
- **Permission errors:** Log error and skip file, notify in Dashboard
- **Unknown file types:** Create basic metadata only, no deep analysis
- **Processing timeout:** Log error, mark as failed, move to Quarantine
- **Large files (>10MB):** Log warning, attempt processing with timeout

## Quality Standards
- Summaries should be concise (2-3 sentences for text, 1-2 for images)
- Always include file metadata (size, type, date)
- Use clear, professional language
- Highlight actionable information when present
- Maintain consistent formatting
EOF
```

### 1.4 Open Vault in Obsidian

1. Launch Obsidian
2. Click "Open folder as vault"
3. Select your `AI_Employee_Vault` directory
4. Verify you see Dashboard.md and Company_Handbook.md

## Step 2: Set Up Python Environment (10 minutes)

### 2.1 Create Python Project

```bash
# Ensure you're in the vault directory
cd /path/to/AI_Employee_Vault

# Initialize uv project (if not already done)
uv init

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "ai-employee-vault"
version = "0.1.0"
description = "Bronze Tier AI Employee - File Processing Automation"
requires-python = ">=3.13"
dependencies = [
    "watchdog>=4.0.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF

# Install dependencies
uv pip install -e .
```

### 2.2 Create Source Directory Structure

```bash
# Create source directories
mkdir -p src/watcher src/utils tests/unit tests/integration

# Create __init__.py files
touch src/__init__.py
touch src/watcher/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py
```

## Step 3: Implement the Watcher Script (15 minutes)

### 3.1 Create File Watcher

Create `src/watcher/file_watcher.py`:

```python
"""
File system watcher for monitoring Inbox folder.
Detects new files and creates metadata in Needs_Action.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .metadata_creator import MetadataCreator
from .logger import JSONLogger


class InboxHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox folder."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.inbox = vault_path / "Inbox"
        self.needs_action = vault_path / "Needs_Action"
        self.metadata_creator = MetadataCreator(vault_path)
        self.logger = JSONLogger(vault_path / "Logs")
        self.processing = set()  # Track files being processed

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Ignore temporary files
        if filepath.name.startswith('.') or filepath.name.startswith('~'):
            return

        # Debounce: wait for file to be fully written
        time.sleep(1)

        # Avoid duplicate processing
        if filepath in self.processing:
            return

        self.processing.add(filepath)

        try:
            self._process_file(filepath)
        except Exception as e:
            self.logger.log_error("file_detection_failed", str(filepath), str(e))
            logging.error(f"Error processing {filepath}: {e}")
        finally:
            self.processing.discard(filepath)

    def _process_file(self, filepath: Path):
        """Process a detected file."""
        # Log detection
        self.logger.log_action(
            action_type="file_detected",
            actor="watcher",
            target=filepath.name,
            parameters={"size": filepath.stat().st_size},
            result="success"
        )

        # Create metadata file
        metadata_path = self.metadata_creator.create_metadata(filepath)

        # Move file to Needs_Action
        dest_path = self.needs_action / filepath.name
        filepath.rename(dest_path)

        # Log completion
        self.logger.log_action(
            action_type="file_moved",
            actor="watcher",
            target=filepath.name,
            parameters={"from": "Inbox", "to": "Needs_Action"},
            result="success"
        )


def run_watcher(vault_path: Path):
    """Run the file watcher continuously."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    handler = InboxHandler(vault_path)
    observer = Observer()
    observer.schedule(handler, str(vault_path / "Inbox"), recursive=False)
    observer.start()

    logging.info(f"Watcher started. Monitoring: {vault_path / 'Inbox'}")

    try:
        while True:
            time.sleep(10)  # Check interval
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Watcher stopped by user")

    observer.join()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m src.watcher.file_watcher <vault_path>")
        sys.exit(1)

    vault_path = Path(sys.argv[1])
    run_watcher(vault_path)
```

**Note**: The complete implementation of `metadata_creator.py` and `logger.py` will be created during the implementation phase (tasks.md).

## Step 4: Create Agent Skill (10 minutes)

### 4.1 Create Skill Directory

```bash
mkdir -p .claude/skills/process-files
```

### 4.2 Create Skill Documentation

Create `.claude/skills/process-files/SKILL.md`:

```markdown
# Process Files Skill

**Purpose**: Analyze files in Needs_Action folder, create summaries, update Dashboard, and move completed files to Done.

## Usage

```bash
claude /process-files
```

## What It Does

1. Scans Needs_Action folder for pending files
2. For each file:
   - Reads the file content
   - Analyzes based on file type (text, PDF, image, etc.)
   - Creates a concise summary
   - Updates the metadata file with summary
   - Moves file to Done folder
3. Updates Dashboard.md with latest activity
4. Logs all actions to daily log file

## Requirements

- Files must be in Needs_Action folder
- Metadata files must exist (created by Watcher)
- Company_Handbook.md must exist for processing rules

## Output

- Summary added to metadata file
- File moved to Done folder
- Dashboard.md updated
- Log entry created

## Error Handling

- Corrupted files moved to Quarantine
- Errors logged with full details
- Processing continues for other files
```

**Note**: The skill implementation (`skill.py`) will be created during the implementation phase.

## Step 5: Test the Setup (5 minutes)

### 5.1 Manual Test

```bash
# 1. Start the Watcher (in one terminal)
python -m src.watcher.file_watcher /path/to/AI_Employee_Vault

# 2. Drop a test file (in another terminal)
echo "This is a test file for the AI Employee system." > /path/to/AI_Employee_Vault/Inbox/test.txt

# 3. Wait 10 seconds and check
ls /path/to/AI_Employee_Vault/Needs_Action/
# You should see: test.txt and FILE_test.txt_*.md

# 4. Check the log
cat /path/to/AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
# You should see JSON log entries

# 5. Process the file with Claude
cd /path/to/AI_Employee_Vault
claude /process-files

# 6. Verify file moved to Done
ls /path/to/AI_Employee_Vault/Done/
# You should see: test.txt

# 7. Check Dashboard in Obsidian
# Open Dashboard.md and verify it shows the processed file
```

## Troubleshooting

### Watcher Not Detecting Files

**Problem**: Files dropped in Inbox are not detected.

**Solutions**:
- Verify Watcher is running: Check terminal for "Watcher started" message
- Check file permissions: Ensure Watcher can read Inbox folder
- Check for errors: Look at terminal output for error messages
- Restart Watcher: Stop (Ctrl+C) and start again

### Claude Code Not Found

**Problem**: `claude` command not recognized.

**Solutions**:
- Verify installation: Run `claude --version`
- Check PATH: Ensure Claude Code is in your system PATH
- Reinstall: Follow Claude Code installation instructions

### Permission Errors

**Problem**: "Permission denied" errors when moving files.

**Solutions**:
- Check folder permissions: Ensure you own the vault directory
- Run as user (not root): Don't use sudo
- Check disk space: Ensure sufficient space available

### Obsidian Not Showing Updates

**Problem**: Dashboard.md doesn't update in Obsidian.

**Solutions**:
- Refresh Obsidian: Close and reopen the file
- Check file: Verify Dashboard.md exists and is readable
- Manual refresh: Click away and back to Dashboard.md

## Next Steps

After completing the Bronze Tier setup:

1. **Test thoroughly**: Process 10-20 different file types
2. **Monitor for 24 hours**: Verify Watcher stability
3. **Review logs**: Check for any errors or issues
4. **Customize Company_Handbook.md**: Adjust processing rules to your needs
5. **Plan Silver Tier**: Add Gmail Watcher, LinkedIn integration, MCP servers

## Support

- **Documentation**: See `specs/bronze-tier/` for detailed specs
- **Issues**: Check logs in `Logs/` folder for error details
- **Community**: Join Wednesday Research Meetings (see hackathon doc)

---

**Congratulations!** You've set up the Bronze Tier Foundation. Your AI Employee is now monitoring files and ready to process them.

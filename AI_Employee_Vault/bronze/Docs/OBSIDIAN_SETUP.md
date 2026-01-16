# Obsidian Setup Guide - Graph View Integration

## Overview

This guide shows you how to connect the Bronze tier AI Employee with Obsidian using the **Local REST API** plugin. This enables:

- ✅ **Real-time updates** - Changes appear instantly in Obsidian
- ✅ **Rich graph view** - Automatic wikilinks between related files
- ✅ **Smart tagging** - Files tagged by type and content
- ✅ **Index pages** - Hub pages that connect to all files
- ✅ **Bidirectional links** - Metadata files link to originals

## Step 1: Open Bronze Folder as Obsidian Vault

1. **Open Obsidian**
2. Click **"Open folder as vault"** (or File → Open another vault)
3. Navigate to: `D:\hamza\autonomous-ftes\AI_Employee_Vault\bronze`
4. Click **"Open"**

Your bronze/ folder is now an Obsidian vault!

## Step 2: Install Local REST API Plugin

1. In Obsidian, go to **Settings** (gear icon)
2. Click **Community plugins** in the left sidebar
3. If you see "Restricted mode is on", click **Turn off restricted mode**
4. Click **Browse** button
5. Search for **"Local REST API"**
6. Click **Install** on the "Local REST API" plugin by coddingtonbear
7. Click **Enable** to activate the plugin

## Step 3: Get Your API Key

1. In Obsidian Settings, scroll down to **Plugin Options**
2. Click **Local REST API**
3. You'll see an **API Key** displayed (looks like: `a1b2c3d4e5f6...`)
4. Click the **Copy** button next to the API key
5. Keep this window open - you'll need the key in the next step

## Step 4: Configure API Key in Bronze Tier

1. Open a terminal in the bronze/ directory
2. Create a `.env` file:

```bash
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/bronze

# Create .env file
cat > .env << 'ENVEOF'
# Obsidian Local REST API Configuration
OBSIDIAN_API_KEY=paste_your_api_key_here
OBSIDIAN_API_URL=http://localhost:27123
OBSIDIAN_VAULT_NAME=bronze
ENVEOF
```

3. Edit the `.env` file and replace `paste_your_api_key_here` with your actual API key

**Security Note:** The `.env` file is already in `.gitignore` and won't be committed to git.

## Step 5: Test the Connection

Run this test script to verify the connection:

```bash
.venv/bin/python3 << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

from utils.obsidian_api import ObsidianAPI

vault_path = Path.cwd()
api = ObsidianAPI(vault_path)

print("Testing Obsidian API connection...")
print(f"API Enabled: {api.enabled}")
print(f"API Available: {api.is_available()}")

if api.is_available():
    print("✅ SUCCESS! Obsidian API is connected and working!")
    print("\nYou can now:")
    print("  - Create notes directly in Obsidian")
    print("  - Add wikilinks for graph view")
    print("  - Tag files automatically")
    print("  - Build rich connections between files")
else:
    print("❌ Connection failed. Check:")
    print("  1. Obsidian is running")
    print("  2. Local REST API plugin is enabled")
    print("  3. API key in .env file is correct")
    print("  4. API URL is http://localhost:27123")
PYEOF
```

## Step 6: Enable Graph View Features

Once connected, the system will automatically:

### 1. Add Wikilinks to Metadata Files

Metadata files will now include wikilinks like:
```markdown
## Related Files
- Original: [[test_document]]
- Dashboard: [[Dashboard]]
- Similar files: [[meeting_notes]], [[report]]
```

### 2. Add Smart Tags

Files are automatically tagged by:
- **Type**: `#text`, `#pdf`, `#image`, `#document`
- **Status**: `#pending`, `#processed`, `#quarantined`
- **Content**: `#meeting`, `#report`, `#invoice`, etc.

### 3. Create Index Pages

The system creates hub pages that link to collections:
- `Index - All Files.md` - Links to all processed files
- `Index - By Type.md` - Grouped by file type
- `Index - By Date.md` - Grouped by processing date

### 4. Link Metadata to Originals

Each metadata file (`FILE_*.md`) will link to its original file in Done/

## Step 7: View the Graph

1. In Obsidian, click the **Graph view** icon in the left sidebar (or press `Ctrl+G`)
2. You'll see a network of connected notes!

### Customize Graph View

Click the settings icon in Graph View to:

**Filters:**
- **Exclude folders**: Add `src/`, `.claude/`, `tests/`, `.venv/` to hide code
- **Show only**: Select specific tags like `#processed` or `#text`

**Display:**
- **Node size**: Adjust based on file size or link count
- **Link thickness**: Make connections more visible
- **Labels**: Show/hide note names
- **Color groups**: Color by folder or tag

**Forces:**
- **Repel**: Spread nodes apart (increase for clarity)
- **Link distance**: Space between connected nodes
- **Center force**: Pull nodes toward center

### Recommended Settings

For the best graph view of your AI Employee vault:

```
Filters:
  Exclude: src/, .claude/, tests/, .venv/, __pycache__/
  
Display:
  Node size: Link count
  Link thickness: 2
  Labels: On
  Color groups: By folder
  
Forces:
  Repel: 150
  Link distance: 100
  Center force: 0.5
```

## Step 8: Understanding the Graph Structure

Your graph will show:

```
                    Dashboard.md (central hub)
                           |
        +------------------+------------------+
        |                  |                  |
    Inbox/          Needs_Action/          Done/
                         |                   |
                    FILE_*.md           FILE_*.md
                    (pending)          (processed)
                         |                   |
                    [[wikilinks]]      [[wikilinks]]
                         |                   |
                    Related files      Original files
```

**Node Types:**
- **Large nodes**: Hub pages (Dashboard, Index pages)
- **Medium nodes**: Metadata files with many connections
- **Small nodes**: Individual processed files

**Connection Types:**
- **Thick lines**: Direct relationships (metadata ↔ original)
- **Thin lines**: Topic-based connections (similar content)
- **Colored lines**: Different relationship types (by folder)

## Step 9: Daily Workflow with Graph View

### Morning Routine
1. Open Obsidian → View Dashboard.md
2. Check pending items count
3. Open Graph View to see recent activity

### Processing Files
1. Drop files in Inbox/ folder
2. Run: `.venv/bin/python3 test_manual_processing.py`
3. Run: `.venv/bin/python3 .claude/skills/process-files/skill.py .`
4. Watch graph update in real-time!

### Exploring Connections
1. Click any node in graph view to open that file
2. Right-click → "Open local graph" to see just that file's connections
3. Use search to find files by content
4. Follow wikilinks to navigate between related files

## Step 10: Advanced Features

### Search with Dataview (Optional)

Install the Dataview plugin to query your vault:

```dataview
TABLE file-type, status, detected-at
FROM "Done"
WHERE type = "file_drop"
SORT detected-at DESC
```

### Create Custom Index Pages

The system auto-generates index pages, but you can create your own:

```markdown
# My Custom Index

## Recent Reports
- [[report_q4_2025]]
- [[financial_analysis]]

## Meeting Notes
- [[team_sync_2026-01-12]]
- [[project_kickoff]]

#index #custom
```

### Tag-Based Views

Click any tag in a file to see all files with that tag:
- `#meeting` - All meeting notes
- `#report` - All reports
- `#urgent` - High-priority items

## Troubleshooting

### Graph View is Empty

**Problem**: No nodes or connections visible

**Solutions**:
1. Make sure you opened bronze/ folder as a vault
2. Process some files first (need content to graph)
3. Check that .md files exist in Done/ folder
4. Verify wikilinks are present in files (open a FILE_*.md and look for `[[links]]`)

### API Connection Failed

**Problem**: Test script shows "Connection failed"

**Solutions**:
1. **Obsidian not running**: Start Obsidian and open the bronze vault
2. **Plugin not enabled**: Settings → Community plugins → Enable "Local REST API"
3. **Wrong API key**: Copy key again from plugin settings
4. **Port conflict**: Check if another app is using port 27123

### Files Not Linking

**Problem**: Files exist but don't show connections in graph

**Solutions**:
1. **No wikilinks**: Files need `[[wikilinks]]` to connect
2. **API not configured**: Set up .env file with API key
3. **Fallback mode**: Without API, system uses basic file writes (limited connections)

### Graph Too Cluttered

**Problem**: Too many nodes, hard to read

**Solutions**:
1. Use filters to exclude code folders (src/, .claude/, tests/)
2. Filter by specific tags (#processed, #text)
3. Increase repel force to spread nodes apart
4. Use local graph view (right-click node → Open local graph)

## Benefits of This Setup

### Without Obsidian API (Basic Mode)
- ✅ Files are created in vault
- ✅ YAML frontmatter works
- ✅ Can view in Obsidian
- ❌ Limited graph connections
- ❌ Manual linking required
- ❌ No real-time updates

### With Obsidian API (Enhanced Mode)
- ✅ All basic features
- ✅ **Rich graph view** with automatic wikilinks
- ✅ **Smart tagging** by content and type
- ✅ **Index pages** as connection hubs
- ✅ **Real-time updates** in Obsidian
- ✅ **Bidirectional links** between files
- ✅ **Topic-based connections** between similar files

## Next Steps

1. ✅ Install Local REST API plugin in Obsidian
2. ✅ Configure .env file with API key
3. ✅ Test connection
4. ✅ Process some files
5. ✅ Open Graph View and explore!

The system will now automatically create rich connections between your files, making it easy to discover relationships and navigate your knowledge base visually.

---

**Need Help?**
- Check Logs/ folder for error details
- Verify .env file has correct API key
- Ensure Obsidian is running with bronze vault open
- Test connection with the script in Step 5

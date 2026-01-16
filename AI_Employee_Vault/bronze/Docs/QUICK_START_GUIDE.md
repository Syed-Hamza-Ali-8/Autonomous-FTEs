# Quick Start Guide - Exploring Your Bronze Tier System

## 🎯 What You Just Accomplished

You successfully processed 3 files through the complete Bronze Tier workflow:
- ✅ Team Meeting Notes (1.3 KB) - 5 action items detected
- ✅ Project Status Report (2.4 KB) - Bronze tier summary
- ✅ Technical Architecture (4.0 KB) - System overview

**Total files processed today: 8**
**Success rate: 100%**

## 📊 View in Obsidian (Step-by-Step)

### 1. Open Obsidian
- Launch Obsidian application
- If bronze vault isn't open: File → Open another vault
- Navigate to: `D:\hamza\autonomous-ftes\AI_Employee_Vault\bronze`
- Click "Open"

### 2. View the Dashboard
- In Obsidian file explorer, click **Dashboard.md**
- You'll see:
  - ⚠️ Watcher status
  - 0 files pending (all processed!)
  - Recent activity (last 5 actions)
  - Statistics: 8 files processed today

### 3. Open Graph View
- Press **`Ctrl + G`** (or click graph icon in left sidebar)
- You'll see a network of connected nodes!

### 4. Configure Graph View (Hide Code Folders)
Click the ⚙️ settings icon in graph view:

**Filters Tab:**
```
Search files (type these):
path:src/
path:.claude/
path:tests/
path:.venv/
path:Logs/
```

**Display Tab:**
- ☑ Show arrows: ON
- Node size: Link count
- Link thickness: 2
- Labels: ON

**Forces Tab:**
- Repel force: 200
- Link distance: 150
- Center force: 0.5

### 5. What You'll See in Graph View

```
                    Dashboard.md
                    (central hub)
                         |
        +----------------+----------------+
        |                |                |
FILE_Team_Meeting   FILE_Project_    FILE_Technical_
    (metadata)      Status (metadata) Architecture (metadata)
        |                |                |
    [[wikilinks]]   [[wikilinks]]    [[wikilinks]]
        |                |                |
Team_Meeting_       Project_Status_  Technical_
2026-01-13.md       Report.txt       Architecture.md
(original file)     (original file)  (original file)
```

**Node Types:**
- 🔵 **Dashboard.md** - Largest node (central hub)
- 📘 **Company_Handbook.md** - Processing rules
- 📄 **FILE_*.md** - Metadata files (3 new ones)
- 📝 **Original files** - Your processed documents (3 new ones)

**Connection Types:**
- **Lines** - Wikilinks between files
- **Tags** - #text, #processed (group similar files)

## 🔍 Explore the Files

### Click on a Metadata File
1. In graph view, click **FILE_Team_Meeting_2026-01-13_*.md**
2. The file opens showing:
   - YAML frontmatter (status, timestamps, summary)
   - File information (name, size, type)
   - Navigation with wikilinks
   - **Graph View Connections section** with:
     - Tags: #processed #text
     - Link to original: [[Done/Team_Meeting_2026-01-13]]
     - Link to Dashboard: [[Dashboard]]
     - Summary of content
     - Key points extracted
     - Action items detected (5 items!)

### Follow a Wikilink
1. Click on **[[Done/Team_Meeting_2026-01-13]]** in the metadata file
2. It opens the original meeting notes file
3. You can see the full content that was processed

### View Local Graph
1. Right-click any file in graph view
2. Select **"Open local graph"**
3. See only connections to/from that specific file

## 📝 Process Your Own Files

### Method 1: Quick Test
```bash
# Navigate to bronze directory
cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/bronze

# Create a test file
echo "Your content here" > Inbox/myfile.txt

# Process it
.venv/bin/python3 test_manual_processing.py
.venv/bin/python3 .claude/skills/process-files/skill.py .

# View in Obsidian (Ctrl+G)
```

### Method 2: Copy Your Files
```bash
# Copy any files you want to process
cp /path/to/your/document.txt Inbox/
cp /path/to/your/notes.md Inbox/

# Process them
.venv/bin/python3 test_manual_processing.py
.venv/bin/python3 .claude/skills/process-files/skill.py .
```

### Method 3: Drag and Drop (Windows)
1. Open File Explorer
2. Navigate to: `D:\hamza\autonomous-ftes\AI_Employee_Vault\bronze\Inbox`
3. Drag and drop files into Inbox folder
4. Run processing commands in terminal

## 🎯 Daily Workflow

### Morning Routine
1. Open Obsidian → View Dashboard.md
2. Check pending items count
3. Open Graph View (Ctrl+G) to see recent activity

### Processing Files
1. Drop files in Inbox/ folder
2. Run processing:
   ```bash
   cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/bronze
   .venv/bin/python3 test_manual_processing.py
   .venv/bin/python3 .claude/skills/process-files/skill.py .
   ```
3. Refresh Obsidian (Ctrl+R) to see updates
4. View graph to see new connections

### Exploring Results
1. Open Dashboard to see statistics
2. Browse Done/ folder for processed files
3. Click metadata files to see summaries
4. Follow wikilinks to navigate between related files
5. Use graph view to discover connections

## 📊 Understanding the Files

### Metadata Files (FILE_*.md)
Located in: `Done/`

Contains:
- **YAML Frontmatter**: Status, timestamps, summary, key points, action items
- **File Information**: Name, size, type
- **Navigation**: Wikilinks to Dashboard and original file
- **Graph View Connections**: Tags, related files, summary
- **Suggested Actions**: Checklist for next steps

### Original Files
Located in: `Done/`

Your original documents, moved from Inbox → Needs_Action → Done

### Dashboard.md
Located in: Root of bronze/

Shows:
- System status (watcher running/stopped)
- Pending items count
- Recent activity (last 5 actions)
- Statistics (today/week/total)
- Last updated timestamp

### Logs
Located in: `Logs/YYYY-MM-DD.json`

JSON audit trail with:
- Timestamp for each action
- Action type (file_detected, file_processed, etc.)
- Actor (watcher, agent_skill, human)
- Target (filename)
- Result (success/failure)
- Parameters (additional details)

## 🔧 Customization

### Modify Processing Rules
Edit `Company_Handbook.md` to change how files are processed:
- Add new file type rules
- Modify summarization guidelines
- Update error handling procedures
- Add quality standards

### Customize Dashboard
Edit `Dashboard.md` to:
- Add custom sections
- Change layout
- Add more statistics
- Include custom wikilinks

### Add More Wikilinks
Edit metadata files to add connections:
- Link to related projects
- Connect similar documents
- Create topic-based hubs
- Build knowledge graph

## 🚀 Next Steps

### Option 1: Test with Real Files
- Process your actual documents
- Explore the graph view
- Discover connections between files
- Build your knowledge base

### Option 2: Enable Real-Time Updates
- Follow `OBSIDIAN_SETUP.md` guide
- Install Local REST API plugin in Obsidian
- Configure .env file with API key
- Get instant updates in Obsidian!

### Option 3: Silver Tier Planning
Start planning next tier features:
- PDF text extraction
- Image analysis with vision API
- Advanced AI summarization
- Automatic processing triggers
- Batch processing

## 💡 Tips & Tricks

### Graph View Tips
- **Zoom**: Scroll to zoom in/out
- **Pan**: Click and drag to move around
- **Focus**: Click a node to open that file
- **Local Graph**: Right-click → "Open local graph"
- **Search**: Use search box to highlight specific files
- **Filter by tags**: Type `#processed` to see only processed files

### Keyboard Shortcuts
- `Ctrl + G` - Open global graph view
- `Ctrl + Shift + G` - Open local graph (for current file)
- `Ctrl + O` - Quick switcher (jump to any file)
- `Ctrl + P` - Command palette
- `Ctrl + R` - Refresh file list

### File Organization
- Keep Inbox empty (files move automatically)
- Check Needs_Action for pending files
- Browse Done/ for processed files
- Review Logs/ for audit trail
- Update Dashboard for status

## 🎊 Congratulations!

You've successfully:
- ✅ Processed 3 realistic test files
- ✅ Created metadata with summaries and wikilinks
- ✅ Built a knowledge graph in Obsidian
- ✅ Established a complete audit trail
- ✅ Set up a production-ready system

Your Bronze Tier AI Employee is now operational and ready for daily use!

---

**Need Help?**
- Check `README.md` for detailed documentation
- Review `OBSIDIAN_SETUP.md` for graph view integration
- Examine `Logs/` folder for troubleshooting
- Open metadata files to see examples

**Ready for More?**
- Process your own files
- Explore the graph view
- Customize processing rules
- Plan Silver Tier features

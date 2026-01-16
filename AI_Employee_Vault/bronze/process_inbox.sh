#!/bin/bash
# Bronze Tier AI Employee - Complete Workflow Script
# This script processes all files from Inbox to Done in one command

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Bronze Tier AI Employee - Processing Inbox         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: Virtual environment not found"
    echo "   Run: uv venv && uv pip install -e ."
    exit 1
fi

# Check if there are files in Inbox
file_count=$(find Inbox -maxdepth 1 -type f | wc -l)

if [ "$file_count" -eq 0 ]; then
    echo "📭 Inbox is empty - no files to process"
    echo ""
    echo "To add files, use one of these methods:"
    echo "  • cp /path/to/file.txt Inbox/"
    echo "  • Windows Explorer: D:\\hamza\\autonomous-ftes\\AI_Employee_Vault\\bronze\\Inbox"
    echo ""
    exit 0
fi

echo "📥 Found $file_count file(s) in Inbox"
echo ""

# Step 1: Detect files and create metadata
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Detecting files and creating metadata..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python test_manual_processing.py
echo ""

# Step 2: Process files and generate summaries
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Processing files and generating summaries..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python process_files_simple.py
echo ""

# Step 3: Show results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Processing Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Current Status:"
echo "  • Inbox:        $(find Inbox -maxdepth 1 -type f | wc -l) files"
echo "  • Needs Action: $(find Needs_Action -maxdepth 1 -type f ! -name 'FILE_*' | wc -l) files"
echo "  • Done:         $(find Done -maxdepth 1 -type f ! -name 'FILE_*' | wc -l) files"
echo ""
echo "📂 View your processed files:"
echo "  • Dashboard:    Dashboard.md"
echo "  • Processed:    Done/"
echo "  • Logs:         Logs/$(date +%Y-%m-%d).json"
echo ""
echo "🔍 Next Steps:"
echo "  • Open Obsidian and view the graph (Ctrl+G)"
echo "  • Check Dashboard.md for system status"
echo "  • Review processed files in Done/"
echo ""

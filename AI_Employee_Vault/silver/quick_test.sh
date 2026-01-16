#!/bin/bash
# Quick test script for Silver Tier functionality
# Run this to test Gmail, WhatsApp, and LinkedIn

set -e  # Exit on error

VAULT_ROOT="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
SILVER_DIR="$VAULT_ROOT/silver"

echo "=========================================="
echo "Silver Tier Quick Test"
echo "=========================================="
echo ""

# Activate virtual environment
cd "$SILVER_DIR"
source .venv/bin/activate

echo "✓ Virtual environment activated"
echo "✓ Python version: $(python --version)"
echo ""

# Test 1: Gmail Watcher
echo "=========================================="
echo "Test 1: Gmail Watcher"
echo "=========================================="
echo "Checking for unread emails..."
echo ""

timeout 30 python -m src.watchers.gmail_watcher 2>&1 | head -20 || {
    echo "Gmail watcher completed (or timed out after 30s)"
}

echo ""
echo "Gmail action files created:"
ls -lh "$VAULT_ROOT/Needs_Action/msg_gmail_"* 2>/dev/null | tail -3 || echo "No Gmail files found"
echo ""

# Test 2: WhatsApp Watcher
echo "=========================================="
echo "Test 2: WhatsApp Watcher"
echo "=========================================="
echo "Checking for WhatsApp messages..."
echo ""

timeout 30 python -m src.watchers.whatsapp_watcher 2>&1 | head -20 || {
    echo "WhatsApp watcher completed (or timed out after 30s)"
}

echo ""
echo "WhatsApp action files created:"
ls -lh "$VAULT_ROOT/Needs_Action/msg_whatsapp_"* 2>/dev/null | tail -3 || echo "No WhatsApp files found"
echo ""

# Test 3: LinkedIn Content Generation
echo "=========================================="
echo "Test 3: LinkedIn Content Generation"
echo "=========================================="
echo "Generating sample LinkedIn post..."
echo ""

python -c "
from src.watchers.linkedin_poster import LinkedInPoster
poster = LinkedInPoster('$VAULT_ROOT')
content = poster.generate_business_post('AI automation')
print('Generated content:')
print('-' * 50)
print(content)
print('-' * 50)
" 2>&1

echo ""

# Test 4: Check Results
echo "=========================================="
echo "Test 4: Summary"
echo "=========================================="
echo ""

GMAIL_COUNT=$(ls -1 "$VAULT_ROOT/Needs_Action/msg_gmail_"* 2>/dev/null | wc -l)
WHATSAPP_COUNT=$(ls -1 "$VAULT_ROOT/Needs_Action/msg_whatsapp_"* 2>/dev/null | wc -l)

echo "Results:"
echo "  - Gmail messages captured: $GMAIL_COUNT"
echo "  - WhatsApp messages captured: $WHATSAPP_COUNT"
echo "  - LinkedIn content generation: ✓ Working"
echo ""

if [ $GMAIL_COUNT -gt 0 ] || [ $WHATSAPP_COUNT -gt 0 ]; then
    echo "✅ SUCCESS: Watchers are working!"
    echo ""
    echo "View action files:"
    echo "  cd $VAULT_ROOT/Needs_Action"
    echo "  ls -lh"
else
    echo "⚠️  WARNING: No messages captured"
    echo ""
    echo "Possible reasons:"
    echo "  1. No unread emails/messages"
    echo "  2. Sessions expired (run setup scripts)"
    echo "  3. Check logs: tail -f $VAULT_ROOT/Logs/*.log"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Test LinkedIn posting (interactive):"
echo "   python -m src.watchers.linkedin_poster"
echo ""
echo "2. Start continuous monitoring:"
echo "   ./scripts/startup.sh"
echo ""
echo "3. View monitoring dashboard:"
echo "   python scripts/dashboard.py"
echo ""
echo "4. Read full guide:"
echo "   cat TEST_GUIDE.md"
echo ""

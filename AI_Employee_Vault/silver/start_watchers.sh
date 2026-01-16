#!/bin/bash
# Start all Silver Tier watchers in background

VAULT_ROOT="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
SILVER_DIR="$VAULT_ROOT/silver"
LOG_DIR="$VAULT_ROOT/Logs"
PID_DIR="$SILVER_DIR/.pids"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

cd "$SILVER_DIR"
source .venv/bin/activate

echo "=========================================="
echo "Starting Silver Tier Watchers"
echo "=========================================="
echo ""

# Start Gmail Watcher
echo "Starting Gmail Watcher..."
nohup python -m src.watchers.gmail_watcher > "$LOG_DIR/gmail_watcher.log" 2>&1 &
GMAIL_PID=$!
echo $GMAIL_PID > "$PID_DIR/gmail_watcher.pid"
echo "  ✓ Gmail Watcher started (PID: $GMAIL_PID)"

# Start WhatsApp Watcher
echo "Starting WhatsApp Watcher..."
nohup python -m src.watchers.whatsapp_watcher > "$LOG_DIR/whatsapp_watcher.log" 2>&1 &
WHATSAPP_PID=$!
echo $WHATSAPP_PID > "$PID_DIR/whatsapp_watcher.pid"
echo "  ✓ WhatsApp Watcher started (PID: $WHATSAPP_PID)"

# Start LinkedIn Scheduler
echo "Starting LinkedIn Scheduler..."
nohup python scripts/linkedin_scheduler.py > "$LOG_DIR/linkedin_scheduler.log" 2>&1 &
LINKEDIN_PID=$!
echo $LINKEDIN_PID > "$PID_DIR/linkedin_scheduler.pid"
echo "  ✓ LinkedIn Scheduler started (PID: $LINKEDIN_PID)"

echo ""
echo "=========================================="
echo "All Watchers Started Successfully"
echo "=========================================="
echo ""
echo "Process IDs:"
echo "  - Gmail Watcher: $GMAIL_PID"
echo "  - WhatsApp Watcher: $WHATSAPP_PID"
echo "  - LinkedIn Scheduler: $LINKEDIN_PID"
echo ""
echo "Log files:"
echo "  - Gmail: $LOG_DIR/gmail_watcher.log"
echo "  - WhatsApp: $LOG_DIR/whatsapp_watcher.log"
echo "  - LinkedIn: $LOG_DIR/linkedin_scheduler.log"
echo ""
echo "To view logs in real-time:"
echo "  tail -f $LOG_DIR/gmail_watcher.log"
echo "  tail -f $LOG_DIR/whatsapp_watcher.log"
echo "  tail -f $LOG_DIR/linkedin_scheduler.log"
echo ""
echo "To stop all watchers:"
echo "  ./stop_watchers.sh"
echo ""

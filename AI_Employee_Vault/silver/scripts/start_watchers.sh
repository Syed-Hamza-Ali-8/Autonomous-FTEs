#!/bin/bash
# Start all Silver tier watchers

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Starting Silver Tier Watchers"
echo "=========================================="
echo ""

# Get vault path
VAULT_PATH="${VAULT_PATH:-/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault}"
cd "$VAULT_PATH"

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "   Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e silver/
else
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python -c "import google.auth" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Gmail API not installed${NC}"
    echo "   Installing dependencies..."
    pip install -e silver/
}

python -c "import playwright" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Playwright not installed${NC}"
    echo "   Installing dependencies..."
    pip install -e silver/
    playwright install chromium
}

echo ""

# Check if .env file exists
if [ ! -f "silver/config/.env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Please create .env file:"
    echo "   cp silver/config/.env.example silver/config/.env"
    echo ""
    echo "   Then configure credentials:"
    echo "   - Gmail: python silver/scripts/setup_gmail.py"
    echo "   - WhatsApp: python silver/scripts/setup_whatsapp.py"
    echo ""
    exit 1
fi

# Create log directory
mkdir -p Logs

# Start Gmail watcher
echo -e "${GREEN}🚀 Starting Gmail watcher...${NC}"
python -m silver.src.watchers.gmail_watcher > Logs/gmail_watcher.log 2>&1 &
GMAIL_PID=$!
echo "   PID: $GMAIL_PID"

# Wait a moment
sleep 2

# Check if Gmail watcher is still running
if ps -p $GMAIL_PID > /dev/null; then
    echo -e "${GREEN}   ✅ Gmail watcher started${NC}"
else
    echo -e "${RED}   ❌ Gmail watcher failed to start${NC}"
    echo "   Check logs: tail -f Logs/gmail_watcher.log"
fi

echo ""

# Start WhatsApp watcher
echo -e "${GREEN}🚀 Starting WhatsApp watcher...${NC}"
python -m silver.src.watchers.whatsapp_watcher > Logs/whatsapp_watcher.log 2>&1 &
WHATSAPP_PID=$!
echo "   PID: $WHATSAPP_PID"

# Wait a moment
sleep 2

# Check if WhatsApp watcher is still running
if ps -p $WHATSAPP_PID > /dev/null; then
    echo -e "${GREEN}   ✅ WhatsApp watcher started${NC}"
else
    echo -e "${RED}   ❌ WhatsApp watcher failed to start${NC}"
    echo "   Check logs: tail -f Logs/whatsapp_watcher.log"
fi

echo ""
echo "=========================================="
echo "Watchers Started"
echo "=========================================="
echo ""
echo "Running watchers:"
echo "   - Gmail watcher (PID: $GMAIL_PID)"
echo "   - WhatsApp watcher (PID: $WHATSAPP_PID)"
echo ""
echo "Logs:"
echo "   - Gmail: tail -f Logs/gmail_watcher.log"
echo "   - WhatsApp: tail -f Logs/whatsapp_watcher.log"
echo ""
echo "To stop watchers:"
echo "   kill $GMAIL_PID $WHATSAPP_PID"
echo ""
echo "Or use:"
echo "   pkill -f gmail_watcher"
echo "   pkill -f whatsapp_watcher"
echo ""

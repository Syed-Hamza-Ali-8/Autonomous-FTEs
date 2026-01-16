#!/bin/bash
# Test Silver tier watchers

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get vault path
VAULT_PATH="${VAULT_PATH:-/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault}"
cd "$VAULT_PATH"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Function to test Gmail watcher
test_gmail() {
    echo "=========================================="
    echo "Testing Gmail Watcher"
    echo "=========================================="
    echo ""

    # Check if credentials are configured
    if ! grep -q "GMAIL_CLIENT_ID=your_client_id" silver/config/.env 2>/dev/null; then
        echo -e "${GREEN}✅ Gmail credentials configured${NC}"
    else
        echo -e "${RED}❌ Gmail credentials not configured${NC}"
        echo "   Run: python silver/scripts/setup_gmail.py"
        return 1
    fi

    # Run Gmail watcher once
    echo "🔍 Running Gmail watcher..."
    python -m silver.src.watchers.gmail_watcher

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Gmail watcher test passed${NC}"
    else
        echo -e "${RED}❌ Gmail watcher test failed${NC}"
        return 1
    fi
}

# Function to test WhatsApp watcher
test_whatsapp() {
    echo "=========================================="
    echo "Testing WhatsApp Watcher"
    echo "=========================================="
    echo ""

    # Check if session exists
    if [ -d "silver/config/whatsapp_session" ]; then
        echo -e "${GREEN}✅ WhatsApp session found${NC}"
    else
        echo -e "${RED}❌ WhatsApp session not found${NC}"
        echo "   Run: python silver/scripts/setup_whatsapp.py"
        return 1
    fi

    # Run WhatsApp watcher once
    echo "🔍 Running WhatsApp watcher..."
    python -m silver.src.watchers.whatsapp_watcher

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ WhatsApp watcher test passed${NC}"
    else
        echo -e "${RED}❌ WhatsApp watcher test failed${NC}"
        return 1
    fi
}

# Function to test all watchers
test_all() {
    echo "=========================================="
    echo "Testing All Watchers"
    echo "=========================================="
    echo ""

    test_gmail
    GMAIL_RESULT=$?

    echo ""

    test_whatsapp
    WHATSAPP_RESULT=$?

    echo ""
    echo "=========================================="
    echo "Test Results"
    echo "=========================================="
    echo ""

    if [ $GMAIL_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ Gmail watcher: PASSED${NC}"
    else
        echo -e "${RED}❌ Gmail watcher: FAILED${NC}"
    fi

    if [ $WHATSAPP_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ WhatsApp watcher: PASSED${NC}"
    else
        echo -e "${RED}❌ WhatsApp watcher: FAILED${NC}"
    fi

    echo ""

    if [ $GMAIL_RESULT -eq 0 ] && [ $WHATSAPP_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Main script
case "${1:-all}" in
    gmail)
        test_gmail
        ;;
    whatsapp)
        test_whatsapp
        ;;
    all)
        test_all
        ;;
    *)
        echo "Usage: $0 {gmail|whatsapp|all}"
        echo ""
        echo "Examples:"
        echo "   $0 gmail      # Test Gmail watcher only"
        echo "   $0 whatsapp   # Test WhatsApp watcher only"
        echo "   $0 all        # Test all watchers (default)"
        exit 1
        ;;
esac

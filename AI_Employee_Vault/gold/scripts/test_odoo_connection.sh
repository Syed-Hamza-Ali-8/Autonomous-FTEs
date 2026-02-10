#!/bin/bash
# Test Odoo MCP Connection
# Usage: ./scripts/test_odoo_connection.sh

set -e

echo "============================================================"
echo "Testing Odoo MCP Connection"
echo "============================================================"
echo ""

# Check if we're in the gold directory
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please run this script from the gold directory"
    exit 1
fi

# Check if Odoo containers are running
echo "1. Checking Odoo containers..."
if docker ps | grep -q "odoo_app"; then
    echo "   ✅ Odoo containers are running"
else
    echo "   ❌ Odoo containers are not running"
    echo "   Start them with: docker-compose -f docker-compose.odoo.yml up -d"
    exit 1
fi

# Check if virtual environment exists
echo ""
echo "2. Checking Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "   ❌ Virtual environment not found"
    echo "   Create it with: uv venv --python 3.13"
    exit 1
fi
echo "   ✅ Virtual environment found"

# Activate virtual environment and run test
echo ""
echo "3. Running Odoo MCP test client..."
echo ""

cd mcp/odoo-mcp-python
source ../../.venv/bin/activate
python test_client.py

echo ""
echo "============================================================"
echo "Test complete!"
echo "============================================================"

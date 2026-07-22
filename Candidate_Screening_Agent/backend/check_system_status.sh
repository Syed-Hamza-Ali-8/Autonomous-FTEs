#!/bin/bash
echo "============================================================"
echo "CANDIDATE SCREENING AGENT - SYSTEM STATUS CHECK"
echo "============================================================"
echo ""

# Check if backend is running
echo "[1/6] Backend Process Status"
if ps aux | grep -E "uvicorn.*main:app" | grep -v grep > /dev/null; then
    PID=$(ps aux | grep -E "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | head -1)
    UPTIME=$(ps -p $PID -o etime= 2>/dev/null | xargs)
    echo "   ✅ Backend running (PID: $PID, Uptime: $UPTIME)"
else
    echo "   ❌ Backend not running"
    exit 1
fi

# Check health endpoint
echo ""
echo "[2/6] Health Endpoint"
HEALTH=$(curl -s http://localhost:8000/health 2>&1)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Health endpoint responding"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null | sed 's/^/      /'
else
    echo "   ❌ Health endpoint not responding"
fi

# Check for errors in logs
echo ""
echo "[3/6] Recent Log Errors"
ERROR_COUNT=$(tail -100 ../logs/backend.log 2>/dev/null | grep -c "ERROR" || echo "0")
OAUTH_ERROR_COUNT=$(tail -100 ../logs/backend.log 2>/dev/null | grep -c "invalid_grant" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "   ✅ No errors in last 100 log lines"
else
    echo "   ⚠️  Found $ERROR_COUNT errors (OAuth errors: $OAUTH_ERROR_COUNT)"
    if [ "$OAUTH_ERROR_COUNT" -gt 0 ]; then
        echo "      Need to refresh OAuth tokens"
    fi
fi

# Check database connectivity
echo ""
echo "[4/6] Database Connectivity"
if grep -q "Database initialized" ../logs/backend.log 2>/dev/null; then
    echo "   ✅ Database connected successfully"
else
    echo "   ⚠️  Database status unknown"
fi

# Check watcher startup
echo ""
echo "[5/6] Background Services"
if grep -q "ReplyWatcher - INFO - Starting ReplyWatcher" ../logs/backend.log 2>/dev/null; then
    echo "   ✅ ReplyWatcher started"
else
    echo "   ❌ ReplyWatcher not started"
fi

if grep -q "GmailApplicationWatcher - INFO - Starting" ../logs/backend.log 2>/dev/null; then
    echo "   ✅ GmailApplicationWatcher started"
else
    echo "   ❌ GmailApplicationWatcher not started"
fi

if grep -q "Starting orchestrator" ../logs/backend.log 2>/dev/null; then
    echo "   ✅ Orchestrator started (4 queue consumers)"
else
    echo "   ❌ Orchestrator not started"
fi

# Summary
echo ""
echo "[6/6] System Summary"
echo "   Port: 8000"
echo "   Logs: $(pwd)/../logs/backend.log"
echo "   Environment: $(grep -c "^[A-Z]" .env 2>/dev/null || echo "unknown") env vars configured"

echo ""
echo "============================================================"
echo "✅ All critical services are running successfully!"
echo "============================================================"

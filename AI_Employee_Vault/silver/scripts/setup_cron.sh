#!/bin/bash
# Silver Tier - Cron Setup Script
# This script helps set up cron jobs for automatic service management

VAULT_PATH="/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
PYTHON_PATH="$VAULT_PATH/silver/.venv/bin/python3"

echo "============================================================"
echo "Silver Tier - Cron Setup"
echo "============================================================"
echo ""

# Check if running on WSL
if grep -qi microsoft /proc/version; then
    echo "⚠️  WARNING: You're running on WSL"
    echo "   Cron on WSL requires special setup"
    echo "   Consider using Windows Task Scheduler instead"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📋 Available cron job options:"
echo ""
echo "1. Start services on boot (@reboot)"
echo "2. Check services every 5 minutes (keep-alive)"
echo "3. Daily briefing at 8:00 AM"
echo "4. LinkedIn post at 9:00 AM daily"
echo "5. All of the above"
echo ""

read -p "Select option (1-5): " option

# Generate crontab entries
CRON_ENTRIES=""

case $option in
    1)
        CRON_ENTRIES="# Silver Tier - Start services on boot
@reboot cd $VAULT_PATH && $VAULT_PATH/silver/scripts/startup.sh >> $VAULT_PATH/Logs/cron.log 2>&1"
        ;;
    2)
        CRON_ENTRIES="# Silver Tier - Keep services alive (check every 5 minutes)
*/5 * * * * cd $VAULT_PATH && $VAULT_PATH/silver/scripts/health_check.py --auto-restart >> $VAULT_PATH/Logs/cron.log 2>&1"
        ;;
    3)
        CRON_ENTRIES="# Silver Tier - Daily briefing at 8:00 AM
0 8 * * * cd $VAULT_PATH && $PYTHON_PATH -c 'from silver.src.planning.plan_generator import generate_daily_briefing; generate_daily_briefing()' >> $VAULT_PATH/Logs/cron.log 2>&1"
        ;;
    4)
        CRON_ENTRIES="# Silver Tier - LinkedIn post at 9:00 AM daily
0 9 * * * cd $VAULT_PATH && $PYTHON_PATH -m silver.src.watchers.linkedin_poster >> $VAULT_PATH/Logs/cron.log 2>&1"
        ;;
    5)
        CRON_ENTRIES="# Silver Tier - Complete cron setup
# Start services on boot
@reboot cd $VAULT_PATH && $VAULT_PATH/silver/scripts/startup.sh >> $VAULT_PATH/Logs/cron.log 2>&1

# Keep services alive (check every 5 minutes)
*/5 * * * * cd $VAULT_PATH && $PYTHON_PATH $VAULT_PATH/silver/scripts/health_check.py --auto-restart >> $VAULT_PATH/Logs/cron.log 2>&1

# Daily briefing at 8:00 AM
0 8 * * * cd $VAULT_PATH && $PYTHON_PATH -c 'from silver.src.planning.plan_generator import generate_daily_briefing; generate_daily_briefing()' >> $VAULT_PATH/Logs/cron.log 2>&1

# LinkedIn post at 9:00 AM daily
0 9 * * * cd $VAULT_PATH && $PYTHON_PATH -m silver.src.watchers.linkedin_poster >> $VAULT_PATH/Logs/cron.log 2>&1"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "📝 Generated cron entries:"
echo "------------------------------------------------------------"
echo "$CRON_ENTRIES"
echo "------------------------------------------------------------"
echo ""

# Save to temporary file
TEMP_CRON=$(mktemp)
crontab -l > "$TEMP_CRON" 2>/dev/null || true
echo "" >> "$TEMP_CRON"
echo "$CRON_ENTRIES" >> "$TEMP_CRON"

echo "🔍 Preview of new crontab:"
echo "------------------------------------------------------------"
cat "$TEMP_CRON"
echo "------------------------------------------------------------"
echo ""

read -p "Install these cron jobs? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    crontab "$TEMP_CRON"
    echo "✅ Cron jobs installed successfully!"
    echo ""
    echo "📋 To view your crontab:"
    echo "   crontab -l"
    echo ""
    echo "📋 To edit your crontab:"
    echo "   crontab -e"
    echo ""
    echo "📋 To remove all cron jobs:"
    echo "   crontab -r"
    echo ""
    echo "📋 To view cron logs:"
    echo "   tail -f $VAULT_PATH/Logs/cron.log"
else
    echo "❌ Installation cancelled"
fi

# Clean up
rm -f "$TEMP_CRON"

echo ""
echo "✅ Cron setup complete!"

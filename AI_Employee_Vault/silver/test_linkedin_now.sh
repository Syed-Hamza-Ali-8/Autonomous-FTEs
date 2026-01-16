#!/bin/bash
# Interactive LinkedIn posting test

cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault/silver
source .venv/bin/activate

echo "=========================================="
echo "LinkedIn Posting Test (Interactive)"
echo "=========================================="
echo ""
echo "This will:"
echo "1. Generate business content"
echo "2. Show you a preview"
echo "3. Ask for confirmation"
echo "4. Post to LinkedIn if you approve"
echo ""
echo "Press Ctrl+C to cancel anytime"
echo ""
read -p "Press Enter to continue..."

python -m src.watchers.linkedin_poster

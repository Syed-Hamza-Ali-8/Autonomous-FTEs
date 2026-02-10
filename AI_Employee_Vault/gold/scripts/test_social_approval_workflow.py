#!/usr/bin/env python3
"""
Test Gold Tier Social Media Approval Workflow

Creates sample approval files to test the HITL workflow.
Similar to Silver Tier's LinkedIn approval workflow.

Usage:
    python gold/scripts/test_social_approval_workflow.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add vault to path
VAULT_PATH = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(VAULT_PATH))


def create_facebook_approval():
    """Create a Facebook post approval file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"approval_{timestamp}_post_facebook.md"
    filepath = VAULT_PATH / "Pending_Approval" / filename

    content = f"""---
type: approval_request
action: post_facebook
platform: facebook
status: pending
created: {datetime.now().isoformat()}
---

## Facebook Post

### Content

🚀 Exciting news from our AI Employee project!

We've just completed Gold Tier implementation with:

✅ Odoo Community Edition integration
✅ Facebook, Instagram & Twitter automation
✅ Weekly CEO Briefing generation
✅ Production-ready error recovery

Building the future of autonomous business operations! 🤖

#AI #Automation #BusinessIntelligence #Innovation

### To Approve

Drag this file to the **Approved/** folder in Obsidian.

The system will automatically post to Facebook and move this file to Done/.
"""

    filepath.write_text(content)
    return filepath


def create_instagram_approval():
    """Create an Instagram post approval file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"approval_{timestamp}_post_instagram.md"
    filepath = VAULT_PATH / "Pending_Approval" / filename

    content = f"""---
type: approval_request
action: post_instagram
platform: instagram
status: pending
created: {datetime.now().isoformat()}
---

## Instagram Post

### Content

✨ Behind the scenes of our AI Employee system! ✨

We're building autonomous agents that:
🤖 Monitor communications 24/7
📊 Generate business intelligence
💰 Track finances with Odoo
📱 Manage social media

The future of work is here! 🚀

#AIEmployee #Automation #TechInnovation #FutureOfWork

### To Approve

Drag this file to the **Approved/** folder in Obsidian.

The system will automatically post to Instagram and move this file to Done/.
"""

    filepath.write_text(content)
    return filepath


def create_twitter_approval():
    """Create a Twitter post approval file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"approval_{timestamp}_post_twitter.md"
    filepath = VAULT_PATH / "Pending_Approval" / filename

    content = f"""---
type: approval_request
action: post_twitter
platform: twitter
status: pending
created: {datetime.now().isoformat()}
---

## Twitter Post

### Content

🤖 Just shipped Gold Tier of our AI Employee system!

✅ Odoo integration for financial tracking
✅ Multi-platform social media automation
✅ Weekly CEO briefings with real insights
✅ Human-in-the-loop approval workflow

Building autonomous business operations with @AnthropicAI Claude Code 🚀

#AI #Automation #BuildInPublic

### To Approve

Drag this file to the **Approved/** folder in Obsidian.

The system will automatically post to Twitter and move this file to Done/.
"""

    filepath.write_text(content)
    return filepath


def main():
    """Main test workflow."""
    print("=" * 70)
    print("🧪 GOLD TIER: SOCIAL MEDIA APPROVAL WORKFLOW TEST")
    print("=" * 70)
    print()
    print("This test demonstrates the HITL approval workflow for Gold Tier")
    print("social media posting - exactly like Silver Tier LinkedIn!")
    print()
    print("=" * 70)
    print()

    # Create Pending_Approval directory if it doesn't exist
    pending_dir = VAULT_PATH / "Pending_Approval"
    pending_dir.mkdir(exist_ok=True)

    print("STEP 1: Creating approval requests...")
    print()

    # Create approval files
    fb_file = create_facebook_approval()
    print(f"   ✅ Facebook: {fb_file.name}")

    ig_file = create_instagram_approval()
    print(f"   ✅ Instagram: {ig_file.name}")

    tw_file = create_twitter_approval()
    print(f"   ✅ Twitter: {tw_file.name}")

    print()
    print("=" * 70)
    print("STEP 2: REVIEW IN OBSIDIAN")
    print("=" * 70)
    print()
    print("📊 Open Obsidian and navigate to:")
    print(f"   {VAULT_PATH}/Pending_Approval/")
    print()
    print("You should see 3 new approval files:")
    print(f"   • {fb_file.name}")
    print(f"   • {ig_file.name}")
    print(f"   • {tw_file.name}")
    print()
    print("=" * 70)
    print("STEP 3: START THE DAEMON")
    print("=" * 70)
    print()
    print("In a NEW terminal window, run:")
    print()
    print("   cd /mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")
    print("   source gold/.venv/bin/activate")
    print("   python gold/scripts/social_media_daemon.py")
    print()
    print("The daemon will watch the Approved/ folder.")
    print()
    print("=" * 70)
    print("STEP 4: APPROVE IN OBSIDIAN")
    print("=" * 70)
    print()
    print("In Obsidian:")
    print("   1. Open one of the approval files")
    print("   2. Review the content")
    print("   3. Drag the file to Approved/ folder")
    print()
    print("The daemon will:")
    print("   ✅ Detect the approved file")
    print("   ✅ Post to the platform (using mock API)")
    print("   ✅ Move file to Done/")
    print()
    print("=" * 70)
    print("STEP 5: VERIFY RESULTS")
    print("=" * 70)
    print()
    print("Check the daemon terminal - you should see:")
    print()
    print("   📝 APPROVED: approval_20260210_post_facebook.md")
    print("      Platform: FACEBOOK")
    print("   🚀 Posting to FACEBOOK...")
    print("      ✅ Posted successfully!")
    print("      📁 Moved to Done/")
    print()
    print("=" * 70)
    print()
    print("✅ TEST SETUP COMPLETE!")
    print()
    print("Next steps:")
    print("   1. Start the daemon (see STEP 3)")
    print("   2. Approve files in Obsidian (see STEP 4)")
    print("   3. Watch the magic happen! ✨")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

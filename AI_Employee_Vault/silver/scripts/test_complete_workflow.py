#!/usr/bin/env python3
"""
Complete AI Employee Workflow Test

Tests the full round-trip:
1. WATCHERS: Monitor Gmail/WhatsApp → Create files in Obsidian
2. OBSIDIAN: Review files in dashboard
3. APPROVAL: Human approves actions
4. ACTIONS: Execute approved actions

This demonstrates the complete autonomous workflow.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import setup_logging, get_logger


def print_header(title):
    """Print section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_step(number, title):
    """Print step header."""
    print()
    print(f"{'─' * 80}")
    print(f"STEP {number}: {title}")
    print(f"{'─' * 80}")
    print()


def run_gmail_watcher(vault_path):
    """Run Gmail watcher to check for new emails."""
    print_step(1, "GMAIL WATCHER - Monitoring Inbox")

    try:
        from src.watchers.gmail_watcher import GmailWatcher

        config_path = str(Path(vault_path) / "silver" / "config" / "watcher_config.yaml")
        watcher = GmailWatcher(vault_path, config_path)

        print("📧 Checking Gmail inbox for new messages...")
        updates = watcher.check_for_updates()

        if updates:
            print(f"✅ Found {len(updates)} new email(s)")
            for i, update in enumerate(updates, 1):
                file_path = watcher.create_action_file(update)
                print(f"   {i}. Created: {file_path.name}")
                print(f"      From: {update['sender']}")
                print(f"      Subject: {update['subject']}")
        else:
            print("📭 No new emails found")

        print()
        print(f"💡 Check Obsidian → Needs_Action/ folder to see email files")

        return len(updates)

    except Exception as e:
        print(f"❌ Gmail watcher failed: {e}")
        print(f"   Make sure Gmail credentials are configured")
        return 0


def run_whatsapp_watcher(vault_path):
    """Run WhatsApp watcher to check for new messages."""
    print_step(2, "WHATSAPP WATCHER - Monitoring Messages")

    try:
        from src.watchers.whatsapp_watcher import WhatsAppWatcher

        config_path = str(Path(vault_path) / "silver" / "config" / "watcher_config.yaml")

        # Check if session exists
        session_path = Path(vault_path) / "silver" / "config" / "whatsapp_session"
        if not session_path.exists():
            print("⚠️  WhatsApp session not found")
            print("   Run: python3 scripts/setup_whatsapp.py")
            print("   Skipping WhatsApp watcher...")
            return 0

        watcher = WhatsAppWatcher(vault_path, config_path)

        print("💬 Checking WhatsApp Web for unread messages...")
        print("   (Browser will open briefly)")
        updates = watcher.check_for_updates()

        if updates:
            print(f"✅ Found {len(updates)} new message(s)")
            for i, update in enumerate(updates, 1):
                file_path = watcher.create_action_file(update)
                print(f"   {i}. Created: {file_path.name}")
                print(f"      From: {update['sender']}")
        else:
            print("📭 No new WhatsApp messages found")

        print()
        print(f"💡 Check Obsidian → Needs_Action/ folder to see message files")

        return len(updates)

    except Exception as e:
        print(f"❌ WhatsApp watcher failed: {e}")
        print(f"   Make sure WhatsApp Web session is set up")
        return 0


def create_linkedin_approval(vault_path):
    """Create LinkedIn post approval request."""
    print_step(3, "LINKEDIN POSTER - Creating Approval Request")

    try:
        from src.watchers.linkedin_poster import LinkedInPoster
        from src.utils import serialize_frontmatter, write_file

        poster = LinkedInPoster(vault_path)

        print("🔵 Generating LinkedIn post content...")
        content = poster.generate_business_post("AI automation")

        print()
        print("📝 Generated post:")
        print("─" * 60)
        print(content)
        print("─" * 60)
        print()

        # Create approval file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"approval_{timestamp}_post_linkedin.md"
        file_path = Path(vault_path) / "Pending_Approval" / filename

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create frontmatter
        frontmatter = {
            "id": f"approval_{timestamp}",
            "type": "linkedin_post",
            "action": "post_to_linkedin",
            "status": "pending_approval",
            "created": datetime.now().isoformat(),
            "priority": "normal"
        }

        # Create body
        body = f"""# LinkedIn Post Approval Request

## 📝 Post Content

```
{content}
```

## 🎯 Action Details

- **Platform**: LinkedIn
- **Type**: Business update post
- **Estimated reach**: Your network
- **Risk level**: Low

## ✅ Approval Instructions

**To approve this post:**
1. Review the content above
2. If you approve, drag this file to `Approved/` folder
3. Run: `python3 silver/scripts/process_linkedin_approval.py`

**To reject:**
- Delete this file or move to `Rejected/` folder

## 📊 What Happens Next

Once approved:
1. System reads file from `Approved/` folder
2. Opens LinkedIn in browser
3. Posts the content
4. Moves this file to `Done/`
5. Creates completion log

---

**Generated by**: AI Employee (LinkedIn Poster)
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
"""

        # Write file
        file_content = serialize_frontmatter(frontmatter, body)
        write_file(file_path, file_content)

        print(f"✅ Created approval request: {filename}")
        print()
        print(f"💡 Check Obsidian → Pending_Approval/ folder")

        return str(file_path)

    except Exception as e:
        print(f"❌ LinkedIn approval creation failed: {e}")
        return None


def show_obsidian_instructions(gmail_count, whatsapp_count, linkedin_file):
    """Show instructions for reviewing in Obsidian."""
    print_step(4, "OBSIDIAN REVIEW - Check Your Dashboard")

    print("📊 Open Obsidian and navigate to AI_Employee_Vault/")
    print()

    if gmail_count > 0:
        print(f"✅ Needs_Action/ folder:")
        print(f"   - {gmail_count} new email file(s) (msg_gmail_*.md)")

    if whatsapp_count > 0:
        print(f"   - {whatsapp_count} new WhatsApp file(s) (msg_whatsapp_*.md)")

    if gmail_count == 0 and whatsapp_count == 0:
        print("📭 Needs_Action/ folder:")
        print("   - No new messages (inbox is empty)")

    print()

    if linkedin_file:
        print(f"✅ Pending_Approval/ folder:")
        print(f"   - 1 LinkedIn post approval request")
        print()
        print("📝 TO APPROVE THE LINKEDIN POST:")
        print("   1. Open the approval file in Obsidian")
        print("   2. Read the post content")
        print("   3. Drag the file to Approved/ folder")

    print()


def wait_for_approval():
    """Wait for user to approve LinkedIn post."""
    print_step(5, "HUMAN APPROVAL - Waiting for Your Decision")

    print("⏳ Waiting for you to approve the LinkedIn post in Obsidian...")
    print()
    print("Instructions:")
    print("  1. Open Obsidian")
    print("  2. Go to Pending_Approval/ folder")
    print("  3. Open the approval_*_linkedin.md file")
    print("  4. Drag it to Approved/ folder")
    print()

    input("Press Enter after you've moved the file to Approved/ folder...")
    print()


def execute_approved_actions(vault_path):
    """Execute approved LinkedIn post."""
    print_step(6, "EXECUTION - Processing Approved Actions")

    try:
        approved_dir = Path(vault_path) / "Approved"
        linkedin_files = list(approved_dir.glob("approval_*_post_linkedin.md"))

        if not linkedin_files:
            print("⚠️  No approved LinkedIn posts found")
            print("   Make sure you moved the file to Approved/ folder")
            return False

        print(f"✅ Found {len(linkedin_files)} approved LinkedIn post(s)")
        print()

        from src.watchers.linkedin_poster import LinkedInPoster
        import yaml

        poster = LinkedInPoster(vault_path)

        for file_path in linkedin_files:
            print(f"📤 Processing: {file_path.name}")

            # Read file
            content = file_path.read_text()

            # Extract content from markdown code block
            if "```" in content:
                parts = content.split("```")
                if len(parts) >= 3:
                    post_content = parts[1].strip()
                else:
                    print("❌ Could not extract post content")
                    continue
            else:
                print("❌ Invalid approval file format")
                continue

            print()
            print("📝 Post content:")
            print("─" * 60)
            print(post_content)
            print("─" * 60)
            print()

            print("🚀 Posting to LinkedIn...")
            print("   (Browser will open - this may take 10-15 seconds)")
            print()

            # Post to LinkedIn
            result = poster.post_update(post_content)

            if result["success"]:
                print("✅ Successfully posted to LinkedIn!")
                print(f"   Timestamp: {result.get('timestamp', 'N/A')}")

                # Move to Done
                done_dir = Path(vault_path) / "Done"
                done_dir.mkdir(exist_ok=True)
                done_path = done_dir / file_path.name
                file_path.rename(done_path)

                print(f"   Moved to: Done/{file_path.name}")
                print()
                print("🔍 Verify: Check your LinkedIn profile to see the post")

                return True
            else:
                print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
                print(f"   {result.get('message', '')}")
                return False

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sending_actions(vault_path):
    """Test sending email and WhatsApp (optional)."""
    print_step(7, "OPTIONAL - Test Sending Actions")

    print("You can also test SENDING messages:")
    print()
    print("📧 Send test email:")
    print("   python3 scripts/test_email.py")
    print()
    print("💬 Send test WhatsApp:")
    print("   python3 scripts/test_whatsapp_simple.py")
    print()

    response = input("Do you want to test sending now? (yes/no): ").strip().lower()

    if response == "yes":
        print()
        print("Choose what to test:")
        print("  1. Email")
        print("  2. WhatsApp")
        print("  3. Both")
        print("  4. Skip")

        choice = input("Enter choice (1-4): ").strip()

        if choice in ["1", "3"]:
            print()
            print("─" * 60)
            print("Testing Email Sending")
            print("─" * 60)

            try:
                from src.actions.email_sender import EmailSender

                sender = EmailSender(vault_path)
                recipient = input("Enter recipient email: ").strip()

                if recipient:
                    result = sender.send_email(
                        to=recipient,
                        subject="Test from AI Employee",
                        body="This is a test email from your AI Employee system."
                    )

                    if result["success"]:
                        print("✅ Email sent successfully!")
                    else:
                        print(f"❌ Email failed: {result.get('error')}")
            except Exception as e:
                print(f"❌ Error: {e}")

        if choice in ["2", "3"]:
            print()
            print("─" * 60)
            print("Testing WhatsApp Sending")
            print("─" * 60)

            try:
                from src.actions.whatsapp_sender import WhatsAppSender

                sender = WhatsAppSender(vault_path)
                recipient = input("Enter recipient (name or number): ").strip()

                if recipient:
                    result = sender.send_message(
                        to=recipient,
                        message="Test message from AI Employee system"
                    )

                    if result["success"]:
                        print("✅ WhatsApp message sent successfully!")
                    else:
                        print(f"❌ WhatsApp failed: {result.get('error')}")
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    print_header("🤖 AI EMPLOYEE - COMPLETE WORKFLOW TEST")

    print("This script will test the FULL autonomous workflow:")
    print()
    print("  Phase 1: WATCHERS - Monitor Gmail/WhatsApp → Create files")
    print("  Phase 2: OBSIDIAN - Review files in dashboard")
    print("  Phase 3: APPROVAL - Human approves actions")
    print("  Phase 4: EXECUTION - System executes approved actions")
    print()
    print("You'll see files appear in Obsidian in real-time!")
    print()

    input("Press Enter to start the complete workflow test...")

    # Phase 1: Run watchers
    print_header("PHASE 1: WATCHERS (Monitoring)")

    gmail_count = run_gmail_watcher(vault_path)
    time.sleep(2)

    whatsapp_count = run_whatsapp_watcher(vault_path)
    time.sleep(2)

    linkedin_file = create_linkedin_approval(vault_path)

    # Phase 2: Show Obsidian instructions
    print_header("PHASE 2: OBSIDIAN (Dashboard Review)")

    show_obsidian_instructions(gmail_count, whatsapp_count, linkedin_file)

    input("Press Enter after you've reviewed the files in Obsidian...")

    # Phase 3: Wait for approval
    print_header("PHASE 3: APPROVAL (Human-in-the-Loop)")

    wait_for_approval()

    # Phase 4: Execute approved actions
    print_header("PHASE 4: EXECUTION (Automated Actions)")

    success = execute_approved_actions(vault_path)

    # Optional: Test sending
    print_header("PHASE 5: OPTIONAL TESTS")

    test_sending_actions(vault_path)

    # Summary
    print_header("✅ WORKFLOW TEST COMPLETE")

    print("Summary:")
    print(f"  📧 Gmail messages found: {gmail_count}")
    print(f"  💬 WhatsApp messages found: {whatsapp_count}")
    print(f"  🔵 LinkedIn post: {'Posted' if success else 'Not posted'}")
    print()
    print("🎉 You've seen the complete AI Employee workflow!")
    print()
    print("Next steps:")
    print("  - Review Done/ folder in Obsidian for completed actions")
    print("  - Check your LinkedIn profile to see the post")
    print("  - Set up continuous monitoring with cron/systemd")
    print()


if __name__ == "__main__":
    main()

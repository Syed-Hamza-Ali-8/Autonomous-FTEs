#!/usr/bin/env python3
"""
AI Employee Daemon - Continuous Autonomous Operation

This daemon runs continuously in the background and:
1. Monitors Gmail/WhatsApp for new messages → Creates files in Needs_Action/
2. Watches Approved/ folder → Auto-executes approved actions
3. Generates periodic LinkedIn posts → Creates approval requests

You only interact through Obsidian - no manual script running needed!
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.gmail_watcher import GmailWatcher
from src.watchers.whatsapp_watcher import WhatsAppWatcher
from src.watchers.linkedin_poster import LinkedInPoster
from src.utils import get_logger, setup_logging


class ApprovedFolderHandler(FileSystemEventHandler):
    """Watches Approved/ folder and auto-executes approved actions."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = get_logger("approved_handler")
        self.poster = LinkedInPoster(vault_path)
        self.processed_files = set()

        # Initialize senders (lazy load to avoid import errors)
        self.email_sender = None
        self.whatsapp_sender = None

    def on_created(self, event):
        """Handle new files in Approved/ folder."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self._process_approval_file(file_path)

    def on_moved(self, event):
        """Handle files moved into Approved/ folder (drag & drop from Obsidian)."""
        if event.is_directory:
            return

        # Check if file was moved INTO the Approved/ folder
        dest_path = Path(event.dest_path)
        if "Approved" in dest_path.parts:
            self._process_approval_file(dest_path)

    def _process_approval_file(self, file_path: Path):
        """Process an approval file (common logic for created and moved files)."""
        # Only process approval files
        if not file_path.name.startswith("approval_"):
            return

        # Avoid processing the same file twice
        if str(file_path) in self.processed_files:
            return

        self.processed_files.add(str(file_path))

        self.logger.info(f"🔔 New approval detected: {file_path.name}")
        print(f"\n🔔 NEW APPROVAL DETECTED: {file_path.name}")
        print("=" * 70)

        # Wait a moment to ensure file is fully written
        time.sleep(1)

        # Route to appropriate handler based on file type
        if "_post_linkedin.md" in file_path.name:
            self._execute_linkedin_post(file_path)
        elif "_reply_whatsapp.md" in file_path.name:
            self._execute_whatsapp_reply(file_path)
        elif "_reply_email.md" in file_path.name:
            self._execute_email_reply(file_path)
        else:
            self.logger.warning(f"Unknown approval type: {file_path.name}")
            print(f"⚠️  Unknown approval type: {file_path.name}")
            print("=" * 70)

    def _execute_linkedin_post(self, file_path: Path):
        """Execute approved LinkedIn post."""
        try:
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
                    return
            else:
                print("❌ Invalid approval file format")
                return

            print()
            print("📝 Post content:")
            print("─" * 60)
            print(post_content)
            print("─" * 60)
            print()

            print("🚀 Posting to LinkedIn...")
            print("   (This may take 10-30 seconds)")
            print()

            # Post to LinkedIn
            result = self.poster.post_update(post_content)

            if result["success"]:
                print("✅ Successfully posted to LinkedIn!")
                print(f"   Timestamp: {result.get('timestamp', 'N/A')}")

                # Move to Done
                done_dir = self.vault_path / "Done"
                done_dir.mkdir(exist_ok=True)
                done_path = done_dir / file_path.name
                file_path.rename(done_path)

                print(f"   Moved to: Done/{file_path.name}")
                print()
                print("🔍 Check your LinkedIn profile to see the post")
                print("=" * 70)
            else:
                print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
                print(f"   {result.get('message', '')}")
                print("=" * 70)

        except Exception as e:
            self.logger.error(f"Failed to execute LinkedIn post: {e}")
            print(f"❌ Error: {e}")
            print("=" * 70)

    def _execute_whatsapp_reply(self, file_path: Path):
        """Execute approved WhatsApp reply."""
        try:
            print(f"💬 Processing WhatsApp reply: {file_path.name}")

            # Lazy load WhatsApp sender
            if not self.whatsapp_sender:
                from src.actions.whatsapp_sender import WhatsAppSender
                self.whatsapp_sender = WhatsAppSender(str(self.vault_path))

            # Read file and extract frontmatter
            import yaml
            content = file_path.read_text()

            # Split frontmatter and body
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                else:
                    print("❌ Invalid file format")
                    return
            else:
                print("❌ No frontmatter found")
                return

            # Extract recipient and message
            recipient = frontmatter.get('recipient') or frontmatter.get('sender')

            # Parse phone number from "Name <phone>" format (if applicable)
            if recipient and '<' in recipient and '>' in recipient:
                import re
                phone_match = re.search(r'<(.+?)>', recipient)
                if phone_match:
                    recipient = phone_match.group(1).strip()
            elif recipient:
                recipient = recipient.strip()

            # Extract reply message from body (support both formats)
            reply_message = None

            # Try "## Suggested Reply" first (orchestrator format)
            if "## Suggested Reply" in body:
                reply_section = body.split("## Suggested Reply")[1]
                # Extract text until next ## heading or end
                lines = reply_section.strip().split('\n')
                reply_lines = []
                for line in lines:
                    if line.strip().startswith('##'):
                        break
                    reply_lines.append(line)
                reply_message = '\n'.join(reply_lines).strip()

            # Fallback to "## Reply" (original format)
            elif "## Reply" in body:
                reply_section = body.split("## Reply")[1]
                lines = reply_section.strip().split('\n')
                reply_lines = []
                for line in lines:
                    if line.strip().startswith('##'):
                        break
                    reply_lines.append(line)
                reply_message = '\n'.join(reply_lines).strip()

            if not reply_message:
                print("❌ No reply message found in file")
                print("   Expected '## Reply' or '## Suggested Reply' section")
                return

            if not recipient or not reply_message:
                print("❌ Missing recipient or message")
                return

            print(f"   To: {recipient}")
            print(f"   Message: {reply_message[:50]}...")
            print()

            # Send WhatsApp message
            result = self.whatsapp_sender.send_message(
                to=recipient,
                message=reply_message
            )

            if result["success"]:
                print("✅ WhatsApp message sent successfully!")

                # Move to Done
                done_dir = self.vault_path / "Done"
                done_dir.mkdir(exist_ok=True)
                done_path = done_dir / file_path.name
                file_path.rename(done_path)

                print(f"   Moved to: Done/{file_path.name}")
            else:
                print(f"❌ Failed to send: {result.get('error')}")

            print("=" * 70)

        except Exception as e:
            self.logger.error(f"Failed to execute WhatsApp reply: {e}")
            print(f"❌ Error: {e}")
            print("=" * 70)

    def _execute_email_reply(self, file_path: Path):
        """Execute approved email reply."""
        try:
            print(f"📧 Processing email reply: {file_path.name}")

            # Lazy load email sender
            if not self.email_sender:
                from src.actions.email_sender import EmailSender
                self.email_sender = EmailSender(str(self.vault_path))

            # Read file and extract frontmatter
            import yaml
            content = file_path.read_text()

            # Split frontmatter and body
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                else:
                    print("❌ Invalid file format")
                    return
            else:
                print("❌ No frontmatter found")
                return

            # Extract email details
            recipient = frontmatter.get('recipient') or frontmatter.get('sender')

            # Parse email address from "Name <email>" format
            if recipient and '<' in recipient and '>' in recipient:
                import re
                email_match = re.search(r'<(.+?)>', recipient)
                if email_match:
                    recipient = email_match.group(1).strip()
            elif recipient:
                # If no angle brackets, assume it's already just an email
                recipient = recipient.strip()

            subject = frontmatter.get('reply_subject') or f"Re: {frontmatter.get('subject', 'Your message')}"

            # Extract reply message from body (support both formats)
            reply_message = None

            # Try "## Suggested Reply" first (orchestrator format)
            if "## Suggested Reply" in body:
                reply_section = body.split("## Suggested Reply")[1]
                # Extract text until next ## heading or end
                lines = reply_section.strip().split('\n')
                reply_lines = []
                for line in lines:
                    if line.strip().startswith('##'):
                        break
                    reply_lines.append(line)
                reply_message = '\n'.join(reply_lines).strip()

            # Fallback to "## Reply" (original format)
            elif "## Reply" in body:
                reply_section = body.split("## Reply")[1]
                lines = reply_section.strip().split('\n')
                reply_lines = []
                for line in lines:
                    if line.strip().startswith('##'):
                        break
                    reply_lines.append(line)
                reply_message = '\n'.join(reply_lines).strip()

            if not reply_message:
                print("❌ No reply message found in file")
                print("   Expected '## Reply' or '## Suggested Reply' section")
                return

            if not recipient or not reply_message:
                print("❌ Missing recipient or message")
                return

            print(f"   To: {recipient}")
            print(f"   Subject: {subject}")
            print(f"   Message: {reply_message[:50]}...")
            print()

            # Send email
            result = self.email_sender.send_email(
                to=recipient,
                subject=subject,
                body=reply_message,
                html=False
            )

            if result["success"]:
                print("✅ Email sent successfully!")
                print(f"   Message ID: {result['message_id']}")

                # Move to Done
                done_dir = self.vault_path / "Done"
                done_dir.mkdir(exist_ok=True)
                done_path = done_dir / file_path.name
                file_path.rename(done_path)

                print(f"   Moved to: Done/{file_path.name}")
            else:
                print(f"❌ Failed to send: {result.get('error')}")

            print("=" * 70)

        except Exception as e:
            self.logger.error(f"Failed to execute email reply: {e}")
            print(f"❌ Error: {e}")
            print("=" * 70)


class AIEmployeeDaemon:
    """Main daemon that orchestrates all watchers and handlers."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = get_logger("ai_employee_daemon")
        self.config_path = str(self.vault_path / "silver" / "config" / "watcher_config.yaml")

        # Initialize watchers
        self.gmail_watcher = None
        self.whatsapp_watcher = None
        self.linkedin_poster = LinkedInPoster(str(vault_path))

        # File system observer for Approved/ folder
        self.observer = Observer()
        self.approved_handler = ApprovedFolderHandler(str(vault_path))

        # Timing
        self.check_interval = 30  # Check every 30 seconds (more responsive)
        self.orchestrator_interval = 60  # Run orchestrator every 1 minute (faster replies)
        self.last_gmail_check = 0
        self.last_whatsapp_check = 0
        self.last_orchestrator_run = 0

    def initialize_watchers(self):
        """Initialize Gmail and WhatsApp watchers."""
        print("🔧 Initializing watchers...")

        # Gmail watcher
        try:
            self.gmail_watcher = GmailWatcher(str(self.vault_path), self.config_path)
            print("✅ Gmail watcher initialized")
        except Exception as e:
            print(f"⚠️  Gmail watcher failed: {e}")
            self.gmail_watcher = None

        # WhatsApp watcher (works in headless mode even in WSL)
        try:
            self.whatsapp_watcher = WhatsAppWatcher(str(self.vault_path), self.config_path)
            print("✅ WhatsApp watcher initialized")
        except Exception as e:
            print(f"⚠️  WhatsApp watcher failed: {e}")
            self.whatsapp_watcher = None

        print()

    def _is_wsl(self):
        """Check if running in WSL (Windows Subsystem for Linux)."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False

    def start_approved_folder_watcher(self):
        """Start watching Approved/ folder for new files."""
        approved_dir = self.vault_path / "Approved"
        approved_dir.mkdir(exist_ok=True)

        self.observer.schedule(self.approved_handler, str(approved_dir), recursive=False)
        self.observer.start()

        print(f"👀 Watching: {approved_dir}")
        print("   When you drag files to Approved/, they'll auto-execute!")
        print()

        # Process any files that are already in Approved/ folder (startup scan)
        self._process_existing_approvals(approved_dir)

    def _process_existing_approvals(self, approved_dir: Path):
        """Process any approval files that already exist in Approved/ folder."""
        try:
            # Debug: print the path being searched
            print(f"🔍 Scanning for existing approvals in: {approved_dir}")

            # Find all approval files
            approval_files = list(approved_dir.glob("approval_*.md"))

            print(f"   Found {len(approval_files)} approval file(s)")

            if approval_files:
                print("   Processing them now...")
                print()

                for file_path in approval_files:
                    print(f"   Processing: {file_path.name}")
                    # Process each file using the handler
                    self.approved_handler._process_approval_file(file_path)
            else:
                print("   No existing approval files to process")
            print()

        except Exception as e:
            self.logger.error(f"Failed to process existing approvals: {e}")
            print(f"⚠️  Error processing existing files: {e}")
            import traceback
            traceback.print_exc()
            print()

    def check_gmail(self):
        """Check Gmail for new messages."""
        if not self.gmail_watcher:
            return

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📧 Checking Gmail...")
            updates = self.gmail_watcher.check_for_updates()

            if updates:
                print(f"   ✅ Found {len(updates)} new email(s)")
                for update in updates:
                    file_path = self.gmail_watcher.create_action_file(update)
                    print(f"      Created: {file_path.name}")
            else:
                print(f"   📭 No new emails")

        except Exception as e:
            self.logger.error(f"Gmail check failed: {e}")
            print(f"   ❌ Error: {e}")

    def check_whatsapp(self):
        """Check WhatsApp for new messages."""
        if not self.whatsapp_watcher:
            return

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 Checking WhatsApp...")
            updates = self.whatsapp_watcher.check_for_updates()

            if updates:
                print(f"   ✅ Found {len(updates)} new message(s)")
                for update in updates:
                    file_path = self.whatsapp_watcher.create_action_file(update)
                    print(f"      Created: {file_path.name}")
            else:
                print(f"   📭 No new messages")

        except Exception as e:
            self.logger.error(f"WhatsApp check failed: {e}")
            print(f"   ❌ Error: {e}")

    def run_orchestrator(self):
        """Run AI orchestrator to generate replies for messages in Needs_Action/."""
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Running AI Orchestrator...")

            # Import orchestrator
            from pathlib import Path
            import subprocess

            orchestrator_script = self.vault_path / "silver" / "scripts" / "orchestrator.py"

            if not orchestrator_script.exists():
                print(f"   ⚠️  Orchestrator script not found")
                return

            # Run orchestrator
            result = subprocess.run(
                [sys.executable, str(orchestrator_script)],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Parse output to show summary
                if "Processed" in result.stdout:
                    # Extract count from output
                    for line in result.stdout.split('\n'):
                        if "Processed" in line:
                            print(f"   {line.strip()}")
                            break
                else:
                    print(f"   ✅ Orchestrator completed")
            else:
                print(f"   ⚠️  Orchestrator exited with code {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:100]}")

        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Orchestrator timeout (>60s)")
        except Exception as e:
            self.logger.error(f"Orchestrator failed: {e}")
            print(f"   ❌ Error: {e}")

    def run(self):
        """Run the daemon continuously."""
        print()
        print("=" * 70)
        print("🤖 AI EMPLOYEE DAEMON - 24/7 AUTONOMOUS OPERATION")
        print("=" * 70)
        print()
        print("This daemon runs continuously and:")
        print("  1. Monitors Gmail/WhatsApp every 30 seconds → Needs_Action/")
        print("  2. AI Orchestrator generates replies every 1 minute → Pending_Approval/")
        print("  3. Watches Approved/ folder for instant execution")
        print("  4. Sends WhatsApp/Email replies automatically")
        print()
        print("WORKFLOW:")
        print("  📧 Client sends message")
        print("  ↓")
        print("  📁 Watcher detects → Needs_Action/")
        print("  ↓")
        print("  🧠 AI generates reply → Pending_Approval/")
        print("  ↓")
        print("  👤 You review in Obsidian")
        print("  ↓")
        print("  ✅ You drag to Approved/")
        print("  ↓")
        print("  🚀 System sends reply automatically")
        print()
        print("YOU ONLY USE OBSIDIAN:")
        print("  - Review AI-generated replies in Pending_Approval/")
        print("  - Edit if needed")
        print("  - Drag to Approved/ to send")
        print("  - System handles everything else!")
        print()
        print("=" * 70)
        print()

        # Initialize
        self.initialize_watchers()
        self.start_approved_folder_watcher()

        print("🚀 Daemon started!")
        print("   Press Ctrl+C to stop")
        print()
        print("=" * 70)
        print()

        try:
            while True:
                current_time = time.time()

                # Check Gmail every 2 minutes
                if current_time - self.last_gmail_check >= self.check_interval:
                    self.check_gmail()
                    self.last_gmail_check = current_time
                    print()

                # Check WhatsApp every 2 minutes
                if current_time - self.last_whatsapp_check >= self.check_interval:
                    self.check_whatsapp()
                    self.last_whatsapp_check = current_time
                    print()

                # Run orchestrator every 5 minutes
                if current_time - self.last_orchestrator_run >= self.orchestrator_interval:
                    self.run_orchestrator()
                    self.last_orchestrator_run = current_time
                    print()

                # Sleep for 10 seconds before next check
                time.sleep(10)

        except KeyboardInterrupt:
            print()
            print("=" * 70)
            print("🛑 Stopping daemon...")
            self.observer.stop()
            self.observer.join()
            print("✅ Daemon stopped")
            print("=" * 70)


def main():
    """Main entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    # Check if vault exists
    if not Path(vault_path).exists():
        print(f"❌ Vault not found: {vault_path}")
        sys.exit(1)

    # Create and run daemon
    daemon = AIEmployeeDaemon(vault_path)
    daemon.run()


if __name__ == "__main__":
    main()

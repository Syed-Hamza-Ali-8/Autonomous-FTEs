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

    def on_created(self, event):
        """Handle new files in Approved/ folder."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process LinkedIn approval files
        if not file_path.name.startswith("approval_") or not file_path.name.endswith("_post_linkedin.md"):
            return

        # Avoid processing the same file twice
        if file_path in self.processed_files:
            return

        self.processed_files.add(file_path)

        self.logger.info(f"🔔 New approval detected: {file_path.name}")
        print(f"\n🔔 NEW APPROVAL DETECTED: {file_path.name}")
        print("=" * 70)

        # Wait a moment to ensure file is fully written
        time.sleep(1)

        # Process the approval
        self._execute_linkedin_post(file_path)

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
        self.check_interval = 120  # Check every 2 minutes
        self.last_gmail_check = 0
        self.last_whatsapp_check = 0

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

        # WhatsApp watcher
        try:
            self.whatsapp_watcher = WhatsAppWatcher(str(self.vault_path), self.config_path)
            print("✅ WhatsApp watcher initialized")
        except Exception as e:
            print(f"⚠️  WhatsApp watcher failed: {e}")
            self.whatsapp_watcher = None

        print()

    def start_approved_folder_watcher(self):
        """Start watching Approved/ folder for new files."""
        approved_dir = self.vault_path / "Approved"
        approved_dir.mkdir(exist_ok=True)

        self.observer.schedule(self.approved_handler, str(approved_dir), recursive=False)
        self.observer.start()

        print(f"👀 Watching: {approved_dir}")
        print("   When you drag files to Approved/, they'll auto-execute!")
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

    def run(self):
        """Run the daemon continuously."""
        print()
        print("=" * 70)
        print("🤖 AI EMPLOYEE DAEMON - AUTONOMOUS OPERATION")
        print("=" * 70)
        print()
        print("This daemon runs continuously and:")
        print("  1. Monitors Gmail/WhatsApp every 2 minutes")
        print("  2. Watches Approved/ folder for instant execution")
        print("  3. Creates files in Obsidian automatically")
        print()
        print("YOU ONLY NEED TO USE OBSIDIAN:")
        print("  - Review files in Needs_Action/")
        print("  - Drag approvals to Approved/ folder")
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

                # Check WhatsApp every 2 minutes (offset by 1 minute)
                if current_time - self.last_whatsapp_check >= self.check_interval:
                    self.check_whatsapp()
                    self.last_whatsapp_check = current_time
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

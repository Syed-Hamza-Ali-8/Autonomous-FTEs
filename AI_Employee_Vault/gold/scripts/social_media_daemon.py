#!/usr/bin/env python3
"""
Gold Tier Social Media Approval Daemon (with Playwright Browser Automation)

This daemon watches the Approved/ folder and automatically posts approved
social media content to Facebook, Instagram, and Twitter using Playwright.

YOU CAN WATCH THE BROWSER POST IN REAL-TIME! 🎬

Same HITL workflow as Silver Tier LinkedIn:
  1. System creates approval file in Pending_Approval/
  2. You review in Obsidian
  3. You drag to Approved/ folder
  4. Daemon detects and posts automatically (with visible browser!)
  5. File moves to Done/

Usage:
    python gold/scripts/social_media_daemon.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml

# Add vault to path
VAULT_PATH = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(VAULT_PATH))

# Import Playwright posters
try:
    from gold.src.actions.facebook_poster_playwright import FacebookPosterPlaywright
    from gold.src.actions.twitter_poster_playwright import TwitterPosterPlaywright
    from gold.src.actions.instagram_poster_playwright import InstagramPosterPlaywright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not available. Install with:")
    print("   pip install playwright && playwright install chromium")


class SocialMediaApprovalHandler(FileSystemEventHandler):
    """Handles approved social media posts with Playwright automation."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.done_dir = self.vault_path / "Done"
        self.failed_dir = self.vault_path / "Failed"

        # Create directories
        self.done_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)

        # Track processed files to avoid duplicates
        self.processed_files = set()

        # Initialize Playwright posters
        if PLAYWRIGHT_AVAILABLE:
            print("🔧 Initializing Playwright posters...")
            try:
                self.facebook_poster = FacebookPosterPlaywright(str(vault_path))
                self.twitter_poster = TwitterPosterPlaywright(str(vault_path))
                self.instagram_poster = InstagramPosterPlaywright(str(vault_path))
                print("   ✅ All posters initialized (Playwright with visible browser)")
            except Exception as e:
                print(f"   ⚠️  Error initializing posters: {e}")
                self.facebook_poster = None
                self.twitter_poster = None
                self.instagram_poster = None
        else:
            self.facebook_poster = None
            self.twitter_poster = None
            self.instagram_poster = None

    def on_created(self, event):
        """Handle new files in Approved/ folder."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process approval files
        if not file_path.name.startswith("approval_"):
            return

        print(f"\n🔔 EVENT DETECTED: File created - {file_path.name}")

        # Small delay to ensure file is fully written
        time.sleep(1)

        # Process the approval
        self._process_approval(file_path)

    def on_moved(self, event):
        """Handle files moved into Approved/ folder (drag from Obsidian)."""
        if event.is_directory:
            return

        # Check if file was moved INTO the Approved/ folder
        dest_path = Path(event.dest_path)

        if dest_path.parent != self.approved_dir:
            return

        # Only process approval files
        if not dest_path.name.startswith("approval_"):
            return

        print(f"\n🔔 EVENT DETECTED: File moved - {dest_path.name}")

        # Small delay to ensure file is fully written
        time.sleep(1)

        # Process the approval
        self._process_approval(dest_path)

    def on_modified(self, event):
        """Handle file modifications (some systems trigger this instead of created)."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process approval files
        if not file_path.name.startswith("approval_"):
            return

        # Check if this file was already processed (to avoid duplicate processing)
        if not hasattr(self, '_processed_files'):
            self._processed_files = set()

        if file_path in self._processed_files:
            return

        print(f"\n🔔 EVENT DETECTED: File modified - {file_path.name}")

        # Mark as processed
        self._processed_files.add(file_path)

        # Small delay to ensure file is fully written
        time.sleep(1)

        # Process the approval
        self._process_approval(file_path)

    def _parse_approval_file(self, file_path: Path) -> dict:
        """Parse approval file and extract frontmatter and content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split frontmatter and body
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    return {'frontmatter': frontmatter, 'body': body}

            return None
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
            return None

    def _extract_post_content(self, body: str) -> str:
        """Extract post content from approval file body."""
        lines = body.split('\n')
        content_lines = []
        in_content = False

        for line in lines:
            if '### Content' in line or '## Content' in line:
                in_content = True
                continue
            elif line.strip().startswith('###') or line.strip().startswith('##'):
                if in_content:
                    break
            elif in_content and line.strip() and not line.strip().startswith('```'):
                content_lines.append(line)

        return '\n'.join(content_lines).strip()

    def _detect_platform(self, file_path: Path, frontmatter: dict) -> str:
        """Detect platform from filename or frontmatter."""
        # Check frontmatter first
        platform = frontmatter.get('platform', '').lower()
        if platform in ['facebook', 'instagram', 'twitter']:
            return platform

        # Check filename
        filename = file_path.name.lower()
        if 'facebook' in filename or 'fb' in filename:
            return 'facebook'
        elif 'instagram' in filename or 'ig' in filename:
            return 'instagram'
        elif 'twitter' in filename or 'tw' in filename:
            return 'twitter'

        return None

    def poll_approved_folder(self):
        """Poll the Approved/ folder for new files (backup for WSL2 event issues)."""
        try:
            approval_files = list(self.approved_dir.glob("approval_*.md"))

            for file_path in approval_files:
                # Skip if already processed
                if str(file_path) in self.processed_files:
                    continue

                print(f"\n🔍 POLLING: Found new file - {file_path.name}")

                # Mark as processed
                self.processed_files.add(str(file_path))

                # Process the approval
                self._process_approval(file_path)
        except Exception as e:
            print(f"⚠️  Polling error: {e}")

    def _process_approval(self, file_path: Path):
        """Process an approved social media post."""
        # Mark as processed to avoid duplicates
        self.processed_files.add(str(file_path))

        print()
        print("=" * 60)
        print(f"📝 APPROVED: {file_path.name}")

        # Parse file
        data = self._parse_approval_file(file_path)
        if not data:
            print("   ❌ Failed to parse approval file")
            return

        frontmatter = data['frontmatter']
        body = data['body']

        # Detect platform
        platform = self._detect_platform(file_path, frontmatter)
        if not platform:
            print("   ❌ Could not detect platform")
            return

        print(f"   Platform: {platform.upper()}")
        print("=" * 60)

        # Extract content
        content = self._extract_post_content(body)
        if not content:
            print("   ❌ No content found")
            return

        # Show content preview
        preview = content[:100] + "..." if len(content) > 100 else content
        print()
        print("📄 Content Preview:")
        print(f"   {preview}")
        print()

        # Post to platform
        print(f"🚀 Posting to {platform.upper()}...")
        print("   🎬 WATCH THE BROWSER - you'll see it post in real-time!")
        print()

        result = None

        try:
            if platform == 'facebook' and self.facebook_poster:
                result = self.facebook_poster.post_update(content)
            elif platform == 'twitter' and self.twitter_poster:
                result = self.twitter_poster.post_update(content)
            elif platform == 'instagram' and self.instagram_poster:
                result = self.instagram_poster.post_update(content)
            else:
                print(f"   ⚠️  Poster not available for {platform}")
                print(f"   Run: python gold/scripts/setup_{platform}.py")
                return

            # Check result
            if result and result.get('success'):
                print()
                print("   ✅ Posted successfully!")
                print(f"   📁 Moving to Done/")

                # Move to Done
                dest = self.done_dir / file_path.name
                file_path.rename(dest)
                print(f"   ✅ Moved to: {dest}")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                message = result.get('message', '') if result else ''
                print()
                print(f"   ❌ Failed: {error}")
                if message:
                    print(f"      {message}")
                print(f"   📁 Moving to Failed/")

                # Move to Failed
                dest = self.failed_dir / file_path.name
                file_path.rename(dest)
                print(f"   ✅ Moved to: {dest}")

        except Exception as e:
            print()
            print(f"   ❌ Exception: {e}")
            print(f"   📁 Moving to Failed/")

            # Move to Failed
            dest = self.failed_dir / file_path.name
            file_path.rename(dest)
            print(f"   ✅ Moved to: {dest}")

        print("=" * 60)


def main():
    """Main daemon loop."""
    print("=" * 70)
    print("🤖 GOLD TIER: SOCIAL MEDIA APPROVAL DAEMON (PLAYWRIGHT)")
    print("=" * 70)
    print()
    print("This daemon watches the Approved/ folder and automatically posts")
    print("approved social media content to Facebook, Instagram, and Twitter.")
    print()
    print("🎬 YOU CAN WATCH THE BROWSER POST IN REAL-TIME!")
    print()
    print("HOW IT WORKS:")
    print("  1. Create approval file in Pending_Approval/")
    print("  2. Review in Obsidian")
    print("  3. Drag to Approved/ folder")
    print("  4. Daemon detects and opens browser to post!")
    print("  5. File moves to Done/")
    print()
    print("SAME WORKFLOW AS SILVER TIER LINKEDIN! ✅")
    print()
    print("=" * 70)
    print()

    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed!")
        print()
        print("Install with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print()
        sys.exit(1)

    # Initialize handler
    handler = SocialMediaApprovalHandler(str(VAULT_PATH))

    # Process any existing files in Approved/ folder (files that were moved before daemon started)
    print("🔍 Checking for existing approval files in Approved/ folder...")
    existing_files = list(handler.approved_dir.glob("approval_*.md"))
    if existing_files:
        print(f"   Found {len(existing_files)} existing approval file(s)")
        for file_path in existing_files:
            print(f"   Processing: {file_path.name}")
            handler._process_approval(file_path)
    else:
        print("   No existing approval files found")
    print()

    # Setup watchdog observer
    observer = Observer()
    observer.schedule(handler, str(handler.approved_dir), recursive=False)

    print("👀 Watching: " + str(handler.approved_dir))
    print("   When you drag files to Approved/, browser will open and post!")
    print()
    print("⚠️  WSL2 Note: Using polling every 3 seconds (WSL2 event detection issue)")
    print()
    print("✅ Daemon started!")
    print("   Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()

    observer.start()

    try:
        poll_counter = 0
        while True:
            time.sleep(1)
            poll_counter += 1

            # Poll every 3 seconds (backup for WSL2 event issues)
            if poll_counter >= 3:
                handler.poll_approved_folder()
                poll_counter = 0

    except KeyboardInterrupt:
        print()
        print("🛑 Stopping daemon...")
        observer.stop()

    observer.join()
    print("✅ Daemon stopped")


if __name__ == "__main__":
    main()

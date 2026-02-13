#!/usr/bin/env python3
"""
AI Employee Orchestrator - Intelligent Reply Generation

This orchestrator:
1. Reads messages from Needs_Action/
2. Generates intelligent replies using AI
3. Creates approval files in Pending_Reply/
4. Waits for human approval before sending

This is the "brain" that makes the AI Employee autonomous.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import yaml
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import get_logger, setup_logging


class AIOrchestrator:
    """Orchestrates AI-powered reply generation for incoming messages."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = get_logger("orchestrator")

        # Folders
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.pending_approval_dir.mkdir(exist_ok=True)

        # Track processed files
        self.processed_files = set()

    def process_needs_action(self):
        """Process all files in Needs_Action/ and generate replies."""

        # Find all message files
        message_files = []
        message_files.extend(self.needs_action_dir.glob("msg_gmail_*.md"))
        message_files.extend(self.needs_action_dir.glob("msg_whatsapp_*.md"))

        if not message_files:
            self.logger.info("No messages to process")
            return 0

        processed_count = 0

        for file_path in message_files:
            # Skip if already processed
            if str(file_path) in self.processed_files:
                continue

            try:
                self.logger.info(f"Processing: {file_path.name}")

                # Read message
                message_data = self._read_message_file(file_path)

                if not message_data:
                    continue

                # Generate AI reply
                reply = self._generate_reply(message_data)

                if not reply:
                    self.logger.warning(f"Could not generate reply for {file_path.name}")
                    continue

                # Create approval file
                approval_file = self._create_approval_file(message_data, reply)

                if approval_file:
                    self.logger.info(f"Created approval: {approval_file.name}")
                    print(f"✅ Created approval: {approval_file.name}")

                    # Mark as processed
                    self.processed_files.add(str(file_path))
                    processed_count += 1

                    # Move original to archive (optional)
                    # file_path.rename(self.vault_path / "Archive" / file_path.name)

            except Exception as e:
                self.logger.error(f"Failed to process {file_path.name}: {e}")
                print(f"❌ Error processing {file_path.name}: {e}")

        return processed_count

    def _read_message_file(self, file_path: Path) -> dict:
        """Read and parse message file."""
        try:
            content = file_path.read_text()

            # Split frontmatter and body
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()

                    return {
                        'file_path': file_path,
                        'source': frontmatter.get('source'),
                        'sender': frontmatter.get('sender'),
                        'subject': frontmatter.get('subject', ''),
                        'body': body,
                        'frontmatter': frontmatter
                    }

            return None

        except Exception as e:
            self.logger.error(f"Failed to read {file_path.name}: {e}")
            return None

    def _generate_reply(self, message_data: dict) -> str:
        """Generate AI reply using Claude via MCP or simple rules."""

        # For now, use a simple template-based approach
        # TODO: Integrate with Claude API or MCP for intelligent replies

        sender = message_data['sender']
        subject = message_data['subject']
        body = message_data['body']

        # Extract actual message content (skip metadata sections)
        if "## Content" in body:
            content_section = body.split("## Content")[1]
            if "## Suggested Actions" in content_section:
                actual_content = content_section.split("## Suggested Actions")[0].strip()
            else:
                actual_content = content_section.strip()
        else:
            actual_content = body

        # Simple rule-based reply generation
        # In production, this should call Claude API

        reply = f"""Thank you for your message.

I've received your message and will review it shortly. I'll get back to you with a detailed response soon.

Best regards,
AI Employee"""

        return reply

    def _create_approval_file(self, message_data: dict, reply: str) -> Path:
        """Create approval file in Pending_Approval/."""

        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = message_data['source']

            if source == 'gmail':
                filename = f"approval_{timestamp}_reply_email.md"
            elif source == 'whatsapp':
                filename = f"approval_{timestamp}_reply_whatsapp.md"
            else:
                filename = f"approval_{timestamp}_reply_{source}.md"

            file_path = self.pending_approval_dir / filename

            # Create frontmatter
            frontmatter = {
                'type': 'reply_approval',
                'source': source,
                'recipient': message_data['sender'],
                'original_subject': message_data['subject'],
                'reply_subject': f"Re: {message_data['subject']}" if message_data['subject'] else None,
                'created': datetime.now().isoformat(),
                'status': 'pending_approval',
                'original_file': message_data['file_path'].name
            }

            # Create body
            body = f"""# Reply Approval Required

**To:** {message_data['sender']}
**Subject:** {message_data['subject'] or 'N/A'}
**Source:** {source}

## Original Message

{message_data['body'][:500]}...

## Suggested Reply

{reply}

## Instructions

1. Review the suggested reply above
2. Edit if needed
3. Drag this file to Approved/ folder to send
4. Or delete to skip

---

**Original file:** {message_data['file_path'].name}
"""

            # Write file
            content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n\n" + body
            file_path.write_text(content)

            return file_path

        except Exception as e:
            self.logger.error(f"Failed to create approval file: {e}")
            return None


def main():
    """Main entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    print()
    print("=" * 70)
    print("🧠 AI ORCHESTRATOR - INTELLIGENT REPLY GENERATION")
    print("=" * 70)
    print()

    # Create orchestrator
    orchestrator = AIOrchestrator(vault_path)

    # Process messages
    print("📋 Processing messages in Needs_Action/...")
    count = orchestrator.process_needs_action()

    print()
    print(f"✅ Processed {count} message(s)")
    print(f"📁 Check Pending_Approval/ folder in Obsidian")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

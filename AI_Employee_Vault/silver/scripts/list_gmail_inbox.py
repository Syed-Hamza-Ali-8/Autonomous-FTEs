#!/usr/bin/env python3
"""
List Received Gmail Messages

This script reads all Gmail messages from Needs_Action/ folder
and displays them in a formatted list.
"""

import sys
from pathlib import Path
import yaml
from datetime import datetime

def parse_email_file(file_path):
    """Parse email markdown file and extract metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return frontmatter, body
        return None, None
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return None, None


def format_timestamp(timestamp_str):
    """Format timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %I:%M %p')
    except:
        return timestamp_str


def list_gmail_messages(vault_path):
    """List all Gmail messages from Needs_Action folder."""

    needs_action = Path(vault_path) / "Needs_Action"
    gmail_files = sorted(needs_action.glob("msg_gmail_*.md"))

    if not gmail_files:
        print("📭 No Gmail messages found in Needs_Action/")
        return

    print("=" * 80)
    print(f"📧 YOUR GMAIL INBOX - {len(gmail_files)} Messages")
    print("=" * 80)
    print()

    # Group by priority
    high_priority = []
    normal_priority = []
    low_priority = []

    for file_path in gmail_files:
        frontmatter, body = parse_email_file(file_path)
        if not frontmatter:
            continue

        priority = frontmatter.get('priority', 'normal')
        if priority == 'high':
            high_priority.append((file_path, frontmatter, body))
        elif priority == 'low':
            low_priority.append((file_path, frontmatter, body))
        else:
            normal_priority.append((file_path, frontmatter, body))

    # Display high priority first
    if high_priority:
        print("🔴 HIGH PRIORITY")
        print("-" * 80)
        for i, (file_path, fm, body) in enumerate(high_priority, 1):
            display_email(i, fm, file_path)
        print()

    # Display normal priority
    if normal_priority:
        print("🟡 NORMAL PRIORITY")
        print("-" * 80)
        for i, (file_path, fm, body) in enumerate(normal_priority, 1):
            display_email(i, fm, file_path)
        print()

    # Display low priority
    if low_priority:
        print("🟢 LOW PRIORITY")
        print("-" * 80)
        for i, (file_path, fm, body) in enumerate(low_priority, 1):
            display_email(i, fm, file_path)
        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total messages: {len(gmail_files)}")
    print(f"  🔴 High priority: {len(high_priority)}")
    print(f"  🟡 Normal priority: {len(normal_priority)}")
    print(f"  🟢 Low priority: {len(low_priority)}")
    print()

    # Categorize by type
    newsletters = []
    invitations = []
    personal = []

    for file_path in gmail_files:
        frontmatter, _ = parse_email_file(file_path)
        if not frontmatter:
            continue

        sender = frontmatter.get('sender', '').lower()
        subject = frontmatter.get('subject', '').lower()

        if any(x in sender for x in ['noreply', 'newsletter', 'changelog', 'team@']):
            newsletters.append(frontmatter)
        elif 'invitation' in subject or 'invitations@linkedin' in sender:
            invitations.append(frontmatter)
        else:
            personal.append(frontmatter)

    print("📋 BY CATEGORY")
    print("-" * 80)
    print(f"  📰 Newsletters/Updates: {len(newsletters)}")
    print(f"  🤝 Invitations: {len(invitations)}")
    print(f"  👤 Personal/Other: {len(personal)}")
    print()


def display_email(index, frontmatter, file_path):
    """Display a single email in formatted output."""
    sender = frontmatter.get('sender', 'Unknown')
    subject = frontmatter.get('subject', 'No subject')
    timestamp = frontmatter.get('timestamp', 'Unknown')
    status = frontmatter.get('status', 'pending')

    # Truncate long subjects
    if len(subject) > 60:
        subject = subject[:57] + "..."

    # Format timestamp
    time_str = format_timestamp(timestamp)

    # Status emoji
    status_emoji = "⏳" if status == "pending" else "✅"

    print(f"{index}. {status_emoji} From: {sender}")
    print(f"   📝 Subject: {subject}")
    print(f"   🕐 Received: {time_str}")
    print(f"   📄 File: {file_path.name}")
    print()


def main():
    """Main entry point."""

    vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"

    # Check if vault exists
    if not Path(vault_path).exists():
        print(f"❌ Vault not found: {vault_path}")
        sys.exit(1)

    list_gmail_messages(vault_path)

    print("💡 WHAT YOU CAN DO:")
    print("-" * 80)
    print("1. Open Obsidian and review these emails")
    print("2. Ask Claude to draft replies for important ones")
    print("3. Archive newsletters: mv Needs_Action/msg_gmail_*.md Archive/")
    print("4. Process with AI: claude code 'Process emails in Needs_Action/'")
    print()


if __name__ == "__main__":
    main()

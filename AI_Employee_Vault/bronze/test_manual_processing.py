#!/usr/bin/env python3
"""
Manual test script to verify file processing logic.

This bypasses watchdog's event system and directly tests:
- MetadataCreator functionality
- File movement from Inbox to Needs_Action
- JSON logging
"""

from pathlib import Path
from src.watcher.file_watcher import InboxHandler

def main():
    # Get vault path (current directory)
    vault_path = Path.cwd()

    print(f"Testing file processing in: {vault_path}")
    print("-" * 60)

    # Create handler
    handler = InboxHandler(vault_path)

    # Get files in Inbox
    inbox_files = list(handler.inbox.glob("*"))
    inbox_files = [f for f in inbox_files if f.is_file()]

    if not inbox_files:
        print("❌ No files found in Inbox folder")
        print(f"   Inbox path: {handler.inbox}")
        return

    print(f"✓ Found {len(inbox_files)} file(s) in Inbox:")
    for f in inbox_files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")

    print("\n" + "-" * 60)
    print("Processing files...\n")

    # Process each file manually
    for filepath in inbox_files:
        print(f"Processing: {filepath.name}")

        try:
            # Call the internal processing method
            handler._process_file(filepath)
            print(f"  ✓ Successfully processed {filepath.name}")
        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "-" * 60)
    print("Verification:")
    print("-" * 60)

    # Check Inbox (should be empty or have only unprocessed files)
    remaining = list(handler.inbox.glob("*"))
    remaining = [f for f in remaining if f.is_file()]
    print(f"Files remaining in Inbox: {len(remaining)}")

    # Check Needs_Action (should have moved files)
    needs_action_files = list(handler.needs_action.glob("*.txt")) + \
                        list(handler.needs_action.glob("*.md"))
    print(f"Files in Needs_Action: {len(needs_action_files)}")
    for f in needs_action_files:
        print(f"  - {f.name}")

    # Check for metadata files
    metadata_files = list(handler.needs_action.glob("FILE_*.md"))
    print(f"\nMetadata files created: {len(metadata_files)}")
    for f in metadata_files:
        print(f"  - {f.name}")

    # Check logs
    log_files = list((vault_path / "Logs").glob("*.json"))
    print(f"\nLog files created: {len(log_files)}")
    for f in log_files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
        # Show first few log entries
        with open(f, 'r') as log:
            lines = log.readlines()[:5]
            for line in lines:
                print(f"    {line.strip()}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple file processor for Bronze tier - processes files in Needs_Action folder.
This is a standalone version that doesn't require the Agent SDK.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.yaml_parser import read_file_with_frontmatter, update_frontmatter, write_file_with_frontmatter
from utils.logger import JSONLogger
from utils.obsidian_api import create_wikilink, create_tag


def generate_simple_summary(content: str, max_length: int = 200) -> str:
    """Generate a simple summary by taking first few sentences."""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    summary = ' '.join(lines[:3])
    if len(summary) > max_length:
        summary = summary[:max_length] + '...'
    return summary


def extract_key_points(content: str, max_points: int = 5) -> List[str]:
    """Extract key points from content (headers, bullet points, etc.)."""
    key_points = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        # Headers
        if line.startswith('#'):
            key_points.append(line)
        # Bullet points
        elif line.startswith('-') or line.startswith('*'):
            key_points.append(line)

        if len(key_points) >= max_points:
            break

    return key_points if key_points else ["No key points detected"]


def extract_action_items(content: str) -> List[str]:
    """Extract action items (checkboxes, TODO items)."""
    action_items = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        # Checkboxes
        if '[ ]' in line or '[x]' in line:
            action_items.append(line)
        # TODO items
        elif line.lower().startswith('todo:') or line.lower().startswith('action:'):
            action_items.append(line)

    return action_items


def process_file(original_file: Path, metadata_file: Path, vault_path: Path, logger: JSONLogger) -> bool:
    """Process a single file and update its metadata."""
    try:
        print(f"\nProcessing: {original_file.name}")

        # Read original file content
        content = original_file.read_text(encoding='utf-8')

        # Generate summary data
        summary_data = {
            "summary": generate_simple_summary(content),
            "key_points": extract_key_points(content),
            "action_items": extract_action_items(content)
        }

        print(f"  ✓ Generated summary ({len(summary_data['summary'])} chars)")
        print(f"  ✓ Found {len(summary_data['key_points'])} key points")
        print(f"  ✓ Found {len(summary_data['action_items'])} action items")

        # Read current metadata
        frontmatter, body = read_file_with_frontmatter(metadata_file)

        # Update frontmatter
        updates = {
            "status": "processed",
            "processed_at": datetime.now().isoformat() + "Z",
            "summary": summary_data["summary"],
            "key_points": summary_data["key_points"],
            "action_items": summary_data["action_items"]
        }
        update_frontmatter(metadata_file, updates)

        # Add graph view section
        original_name = frontmatter.get("original_name", "")
        file_stem = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
        file_type = frontmatter.get("file_type", "unknown")

        processed_tag = create_tag("processed")
        type_tag = create_tag(file_type)
        dashboard_link = create_wikilink("Dashboard")
        original_link = create_wikilink(f"Done/{file_stem}", file_stem)

        graph_section = f"""

---

## Graph View Connections

{processed_tag} {type_tag}

### Related Files
- 📄 Original: {original_link}
- 📊 {dashboard_link}

### Summary
{summary_data["summary"]}

### Key Points
"""
        for point in summary_data["key_points"][:3]:
            graph_section += f"- {point}\n"

        if summary_data["action_items"]:
            graph_section += "\n### Action Items\n"
            for item in summary_data["action_items"][:3]:
                graph_section += f"- [ ] {item}\n"

        # Append to body
        frontmatter_updated, body_current = read_file_with_frontmatter(metadata_file)
        new_body = body_current + graph_section
        write_file_with_frontmatter(metadata_file, frontmatter_updated, new_body)

        print(f"  ✓ Updated metadata file")

        # Move original file to Done
        done_dir = vault_path / "Done"
        done_dir.mkdir(exist_ok=True)
        dest_path = done_dir / original_file.name
        original_file.rename(dest_path)

        print(f"  ✓ Moved to Done/")

        # Log the action
        logger.log_action(
            action_type="file_processed",
            actor="simple_processor",
            target=original_file.name,
            result="success",
            parameters={
                "file_type": file_type,
                "summary_length": len(summary_data["summary"])
            }
        )

        return True

    except Exception as e:
        print(f"  ✗ Error processing {original_file.name}: {e}")
        return False


def main():
    """Main processing function."""
    vault_path = Path(__file__).parent
    needs_action_dir = vault_path / "Needs_Action"

    # Initialize logger
    logs_dir = vault_path / "Logs"
    logger = JSONLogger(logs_dir)

    print(f"Processing files in: {vault_path}")
    print("=" * 60)

    # Find all files in Needs_Action (excluding metadata files)
    files_to_process = []
    if needs_action_dir.exists():
        for file_path in needs_action_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith("FILE_"):
                # Find corresponding metadata file
                metadata_pattern = f"FILE_{file_path.stem}_*.md"
                metadata_files = list(needs_action_dir.glob(metadata_pattern))
                if metadata_files:
                    files_to_process.append((file_path, metadata_files[0]))

    if not files_to_process:
        print("No files to process in Needs_Action/")
        return

    print(f"Found {len(files_to_process)} file(s) to process\n")

    # Process each file
    success_count = 0
    for original_file, metadata_file in files_to_process:
        if process_file(original_file, metadata_file, vault_path, logger):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"Processing complete: {success_count}/{len(files_to_process)} files processed successfully")

    # Update Dashboard
    print("\nUpdating Dashboard...")
    try:
        from watcher.dashboard import update_dashboard
        update_dashboard(vault_path)
        print("✓ Dashboard updated")
    except Exception as e:
        print(f"✗ Error updating dashboard: {e}")


if __name__ == "__main__":
    main()

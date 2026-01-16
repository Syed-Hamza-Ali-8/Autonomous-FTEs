"""
Process Files Agent Skill

Main processing logic for analyzing files in Needs_Action folder.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "bronze" / "src"))

from utils.file_reader import FileReader
from utils.summarizer import Summarizer
from utils.yaml_parser import read_file_with_frontmatter, update_frontmatter
from utils.logger import JSONLogger
from utils.dashboard_updater import DashboardUpdater
from utils.obsidian_api import create_wikilink, create_tag


class FileProcessor:
    """Processes files in Needs_Action folder."""

    def __init__(self, vault_path: Path):
        """
        Initialize FileProcessor.

        Args:
            vault_path: Path to the vault root directory
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.quarantine = self.needs_action / "Quarantine"
        self.logs = self.vault_path / "Logs"

        # Ensure directories exist
        self.done.mkdir(parents=True, exist_ok=True)
        self.quarantine.mkdir(parents=True, exist_ok=True)

        # Initialize utilities
        self.file_reader = FileReader()
        self.summarizer = Summarizer()
        self.logger = JSONLogger(self.logs)
        self.dashboard_updater = DashboardUpdater(vault_path)

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.log = logging.getLogger(__name__)

    def scan_needs_action(self) -> List[Path]:
        """
        Scan Needs_Action folder for pending files.

        Returns:
            List of metadata file paths with status="pending"
        """
        metadata_files = list(self.needs_action.glob("FILE_*.md"))
        pending_files = []

        for metadata_path in metadata_files:
            try:
                frontmatter, _ = read_file_with_frontmatter(metadata_path)
                if frontmatter.get("status") == "pending":
                    pending_files.append(metadata_path)
            except Exception as e:
                self.log.error(f"Error reading metadata {metadata_path}: {e}")

        return pending_files

    def process_file(self, metadata_path: Path) -> bool:
        """
        Process a single file: read, analyze, summarize, update metadata, move to Done.

        Args:
            metadata_path: Path to the metadata file (FILE_*.md)

        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Read metadata
            frontmatter, body = read_file_with_frontmatter(metadata_path)
            original_name = frontmatter.get("original_name")

            if not original_name:
                self.log.error(f"No original_name in metadata: {metadata_path}")
                return False

            # Find the original file
            original_file = self.needs_action / original_name

            if not original_file.exists():
                self.log.error(f"Original file not found: {original_file}")
                self.logger.log_error(
                    action_type="file_processing_failed",
                    target=original_name,
                    error_message="Original file not found",
                    actor="agent_skill"
                )
                return False

            self.log.info(f"Processing: {original_name}")

            # Read file content
            file_data = self.file_reader.read_file(original_file)

            if file_data.get("error"):
                # Handle corrupted/unreadable files
                self.log.error(f"Error reading {original_name}: {file_data['error']}")
                self._move_to_quarantine(original_file, metadata_path, file_data["error"])
                return False

            # Generate summary
            summary_data = self.summarizer.generate_summary(
                content=file_data["content"],
                file_type=file_data["file_type"],
                metadata=file_data["metadata"],
                filename=original_name
            )

            # Update metadata with summary
            self._update_metadata(metadata_path, summary_data)

            # Move files to Done
            self._move_to_done(original_file, metadata_path)

            # Log success
            self.logger.log_action(
                action_type="file_processed",
                actor="agent_skill",
                target=original_name,
                parameters={
                    "file_type": file_data["file_type"],
                    "summary_length": len(summary_data["summary"])
                },
                result="success"
            )

            # Update dashboard after successful processing
            try:
                self.dashboard_updater.update_for_file_processing(original_name, success=True)
            except Exception as e:
                self.log.error(f"Error updating dashboard: {e}")
                # Don't raise - dashboard update failure shouldn't stop processing

            self.log.info(f"✓ Successfully processed: {original_name}")
            return True

        except Exception as e:
            self.log.error(f"Error processing {metadata_path}: {e}")
            self.logger.log_error(
                action_type="file_processing_failed",
                target=str(metadata_path.name),
                error_message=str(e),
                actor="agent_skill"
            )
            return False

    def _update_metadata(self, metadata_path: Path, summary_data: Dict[str, Any]) -> None:
        """
        Update metadata file with summary information and wikilinks for graph view.

        Args:
            metadata_path: Path to the metadata file
            summary_data: Summary data from Summarizer
        """
        # Read current metadata
        frontmatter, body = read_file_with_frontmatter(metadata_path)

        # Get original filename for wikilink
        original_name = frontmatter.get("original_name", "")
        file_stem = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name

        # Update frontmatter
        updates = {
            "status": "processed",
            "processed_at": datetime.now().isoformat() + "Z",
            "summary": summary_data["summary"],
            "key_points": summary_data["key_points"],
            "action_items": summary_data["action_items"]
        }

        update_frontmatter(metadata_path, updates)

        # Add wikilinks and tags to body for graph view
        processed_tag = create_tag("processed")
        file_type = frontmatter.get("file_type", "unknown")
        type_tag = create_tag(file_type)

        # Create wikilinks
        dashboard_link = create_wikilink("Dashboard")
        original_link = create_wikilink(f"Done/{file_stem}", file_stem)

        # Append graph view section to body
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
        for point in summary_data["key_points"][:3]:  # Limit to 3 key points
            graph_section += f"- {point}\n"

        if summary_data["action_items"]:
            graph_section += "\n### Action Items\n"
            for item in summary_data["action_items"][:3]:  # Limit to 3 action items
                graph_section += f"- [ ] {item}\n"

        # Append to existing body
        from utils.yaml_parser import write_file_with_frontmatter
        frontmatter_updated, body_current = read_file_with_frontmatter(metadata_path)
        new_body = body_current + graph_section
        write_file_with_frontmatter(metadata_path, frontmatter_updated, new_body)

        # Log metadata update
        self.logger.log_action(
            action_type="metadata_updated",
            actor="agent_skill",
            target=metadata_path.name,
            parameters={"status": "processed"},
            result="success"
        )

    def _move_to_done(self, original_file: Path, metadata_path: Path) -> None:
        """
        Move processed files to Done folder.

        Args:
            original_file: Path to the original file
            metadata_path: Path to the metadata file
        """
        # Move original file
        dest_file = self.done / original_file.name
        if dest_file.exists():
            # Handle filename conflict
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_file = self.done / f"{original_file.stem}_{timestamp}{original_file.suffix}"

        original_file.rename(dest_file)

        # Move metadata file
        dest_metadata = self.done / metadata_path.name
        if dest_metadata.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_metadata = self.done / f"{metadata_path.stem}_{timestamp}{metadata_path.suffix}"

        metadata_path.rename(dest_metadata)

        # Log file movement
        self.logger.log_action(
            action_type="file_moved",
            actor="agent_skill",
            target=original_file.name,
            parameters={"from": "Needs_Action", "to": "Done"},
            result="success"
        )

    def _move_to_quarantine(
        self,
        original_file: Path,
        metadata_path: Path,
        error_message: str
    ) -> None:
        """
        Move corrupted/unreadable files to Quarantine.

        Args:
            original_file: Path to the original file
            metadata_path: Path to the metadata file
            error_message: Error description
        """
        # Move original file to Quarantine
        dest_file = self.quarantine / original_file.name
        if dest_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_file = self.quarantine / f"{original_file.stem}_{timestamp}{original_file.suffix}"

        original_file.rename(dest_file)

        # Update metadata status and move to Quarantine
        update_frontmatter(metadata_path, {
            "status": "quarantined",
            "quarantined_at": datetime.now().isoformat() + "Z",
            "error": error_message
        })

        dest_metadata = self.quarantine / metadata_path.name
        if dest_metadata.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_metadata = self.quarantine / f"{metadata_path.stem}_{timestamp}{metadata_path.suffix}"

        metadata_path.rename(dest_metadata)

        # Log quarantine action
        self.logger.log_action(
            action_type="file_quarantined",
            actor="agent_skill",
            target=original_file.name,
            parameters={"reason": error_message},
            result="success"
        )

        # Update dashboard after quarantine
        try:
            self.dashboard_updater.update_for_file_processing(original_file.name, success=False)
        except Exception as e:
            self.log.error(f"Error updating dashboard: {e}")
            # Don't raise - dashboard update failure shouldn't stop processing

        self.log.warning(f"⚠ Quarantined: {original_file.name} - {error_message}")

    def process_all(self) -> Dict[str, int]:
        """
        Process all pending files in Needs_Action.

        Returns:
            Dictionary with processing statistics:
                - processed: number of successfully processed files
                - failed: number of failed files
                - quarantined: number of quarantined files
        """
        pending_files = self.scan_needs_action()

        if not pending_files:
            self.log.info("No pending files to process")
            return {"processed": 0, "failed": 0, "quarantined": 0}

        self.log.info(f"Found {len(pending_files)} pending file(s)")

        stats = {"processed": 0, "failed": 0, "quarantined": 0}

        for metadata_path in pending_files:
            success = self.process_file(metadata_path)
            if success:
                stats["processed"] += 1
            else:
                # Check if file was quarantined
                frontmatter, _ = read_file_with_frontmatter(metadata_path)
                if frontmatter.get("status") == "quarantined":
                    stats["quarantined"] += 1
                else:
                    stats["failed"] += 1

        return stats


def main():
    """Main entry point for the skill."""
    if len(sys.argv) < 2:
        print("Usage: python skill.py <vault_path>")
        sys.exit(1)

    vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    print("=" * 60)
    print("Process Files Agent Skill")
    print("=" * 60)

    processor = FileProcessor(vault_path)
    stats = processor.process_all()

    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)
    print(f"✓ Processed: {stats['processed']}")
    print(f"✗ Failed: {stats['failed']}")
    print(f"⚠ Quarantined: {stats['quarantined']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

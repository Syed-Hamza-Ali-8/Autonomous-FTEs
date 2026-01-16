"""
Company Handbook parser for extracting processing rules.

Reads Company_Handbook.md and extracts file type processing rules.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import re


class HandbookParser:
    """Parses Company_Handbook.md to extract processing rules."""

    def __init__(self, handbook_path: Path):
        """
        Initialize HandbookParser.

        Args:
            handbook_path: Path to Company_Handbook.md
        """
        self.handbook_path = handbook_path
        self.rules = self._parse_handbook()

    def _parse_handbook(self) -> Dict[str, Any]:
        """
        Parse Company_Handbook.md and extract processing rules.

        Returns:
            Dictionary with rules for each file type
        """
        if not self.handbook_path.exists():
            return {}

        try:
            with open(self.handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()

            rules = {
                "text": self._extract_section_rules(content, "Text Files"),
                "pdf": self._extract_section_rules(content, "PDF Documents"),
                "image": self._extract_section_rules(content, "Images"),
                "document": self._extract_section_rules(content, "Documents"),
                "unknown": self._extract_section_rules(content, "Unknown File Types"),
                "error_handling": self._extract_error_handling(content),
                "quality_standards": self._extract_quality_standards(content)
            }

            return rules

        except Exception as e:
            print(f"Warning: Could not parse Company_Handbook.md: {e}")
            return {}

    def _extract_section_rules(self, content: str, section_name: str) -> List[str]:
        """
        Extract rules from a specific section.

        Args:
            content: Full handbook content
            section_name: Section header to find

        Returns:
            List of rules (bullet points) from that section
        """
        # Find the section
        pattern = rf"### {re.escape(section_name)}.*?\n(.*?)(?=\n###|\n##|$)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return []

        section_content = match.group(1)

        # Extract bullet points
        rules = []
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                # Remove the leading dash and clean up
                rule = line[1:].strip()
                if rule:
                    rules.append(rule)

        return rules

    def _extract_error_handling(self, content: str) -> Dict[str, str]:
        """
        Extract error handling guidelines.

        Returns:
            Dictionary mapping error types to handling instructions
        """
        pattern = r"## Error Handling Guidelines(.*?)(?=\n##|$)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return {}

        section_content = match.group(1)
        error_rules = {}

        # Parse lines like "- **Corrupted files:** Move to Quarantine..."
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('-') and '**' in line:
                # Extract error type and handling
                parts = line.split(':', 1)
                if len(parts) == 2:
                    error_type = parts[0].replace('-', '').replace('**', '').strip()
                    handling = parts[1].strip()
                    error_rules[error_type.lower()] = handling

        return error_rules

    def _extract_quality_standards(self, content: str) -> List[str]:
        """
        Extract quality standards.

        Returns:
            List of quality standards
        """
        pattern = r"## Quality Standards(.*?)(?=\n##|$)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return []

        section_content = match.group(1)
        standards = []

        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                standard = line[1:].strip()
                if standard:
                    standards.append(standard)

        return standards

    def get_rules_for_type(self, file_type: str) -> List[str]:
        """
        Get processing rules for a specific file type.

        Args:
            file_type: File type (text, pdf, image, document, unknown)

        Returns:
            List of rules for that file type
        """
        return self.rules.get(file_type, [])

    def get_error_handling(self, error_type: str) -> Optional[str]:
        """
        Get error handling instructions for a specific error type.

        Args:
            error_type: Error type (e.g., "corrupted files", "permission errors")

        Returns:
            Handling instructions or None
        """
        return self.rules.get("error_handling", {}).get(error_type.lower())

    def get_quality_standards(self) -> List[str]:
        """
        Get quality standards for summaries.

        Returns:
            List of quality standards
        """
        return self.rules.get("quality_standards", [])

"""
Summary generator for different file types.

Creates concise summaries following Company_Handbook.md rules.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging


class Summarizer:
    """Generates summaries for different file types."""

    def __init__(self, handbook_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize Summarizer.

        Args:
            handbook_rules: Optional dict of processing rules from Company_Handbook.md
        """
        self.logger = logging.getLogger(__name__)
        self.handbook_rules = handbook_rules or {}

    def generate_summary(
        self,
        content: str,
        file_type: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Generate summary based on file type.

        Args:
            content: File content or description
            file_type: Type of file (text, pdf, image, document, unknown)
            metadata: File metadata (word count, size, etc.)
            filename: Original filename

        Returns:
            Dictionary with:
                - summary: str (2-3 sentence summary)
                - key_points: list (main topics/themes)
                - action_items: list (if any identified)
                - analysis: dict (additional analysis details)
        """
        if file_type == "text":
            return self._summarize_text(content, metadata, filename)
        elif file_type == "pdf":
            return self._summarize_pdf(content, metadata, filename)
        elif file_type == "image":
            return self._summarize_image(content, metadata, filename)
        elif file_type == "document":
            return self._summarize_document(content, metadata, filename)
        else:
            return self._summarize_unknown(content, metadata, filename)

    def _summarize_text(
        self,
        content: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Summarize text file following Company_Handbook.md rules:
        - Extract main topics and themes
        - Summarize in 2-3 clear sentences
        - Identify action items if present
        - Note word count and key information
        """
        # Extract basic statistics
        word_count = metadata.get("word_count", 0)
        line_count = metadata.get("line_count", 0)

        # Simple topic extraction (first few sentences or lines)
        lines = content.strip().split('\n')
        first_lines = [line.strip() for line in lines[:5] if line.strip()]

        # Check for action items (lines with TODO, [ ], -, etc.)
        action_items = []
        for line in lines:
            line_lower = line.lower().strip()
            if any(marker in line_lower for marker in ['todo', '[ ]', 'action:', 'task:']):
                action_items.append(line.strip())

        # Generate summary (Bronze tier: simple extraction)
        if len(content) < 100:
            summary = f"Short text file with {word_count} words. Content: {content[:100]}"
        else:
            # Take first 2-3 sentences or first 200 characters
            summary_text = content[:200].strip()
            if '.' in summary_text:
                sentences = summary_text.split('.')
                summary = '. '.join(sentences[:2]) + '.'
            else:
                summary = summary_text + '...'

        # Extract key points (first few non-empty lines)
        key_points = first_lines[:3] if first_lines else ["No content"]

        return {
            "summary": summary,
            "key_points": key_points,
            "action_items": action_items[:5],  # Limit to 5
            "analysis": {
                "word_count": word_count,
                "line_count": line_count,
                "has_action_items": len(action_items) > 0,
                "content_length": "short" if word_count < 100 else "medium" if word_count < 500 else "long"
            }
        }

    def _summarize_pdf(
        self,
        content: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Summarize PDF file following Company_Handbook.md rules:
        - Extract title and author if available
        - Summarize key sections and findings
        - Note page count and document length
        - Identify document type (report, invoice, article, etc.)

        Bronze tier: Basic info only, full extraction in Silver tier.
        """
        file_size = metadata.get("file_size", 0)
        size_mb = file_size / (1024 * 1024)

        # Guess document type from filename
        filename_lower = filename.lower()
        if 'invoice' in filename_lower or 'receipt' in filename_lower:
            doc_type = "invoice/receipt"
        elif 'report' in filename_lower:
            doc_type = "report"
        elif 'article' in filename_lower or 'paper' in filename_lower:
            doc_type = "article"
        else:
            doc_type = "document"

        summary = f"PDF {doc_type} ({size_mb:.1f} MB). Full text extraction will be available in Silver tier."

        return {
            "summary": summary,
            "key_points": [
                f"File type: PDF {doc_type}",
                f"Size: {size_mb:.1f} MB",
                "Bronze tier: Basic metadata only"
            ],
            "action_items": [],
            "analysis": {
                "file_size": file_size,
                "document_type": doc_type,
                "extraction_available": False,
                "tier": "bronze"
            }
        }

    def _summarize_image(
        self,
        content: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Summarize image file following Company_Handbook.md rules:
        - Describe visual content and composition
        - Identify any text visible in the image
        - Note dimensions and file size
        - Describe colors and style

        Bronze tier: Basic info only, vision analysis in Silver tier.
        """
        file_size = metadata.get("file_size", 0)
        size_kb = file_size / 1024
        extension = metadata.get("extension", "unknown")

        summary = f"Image file ({extension}, {size_kb:.1f} KB). Visual analysis will be available in Silver tier with vision capabilities."

        return {
            "summary": summary,
            "key_points": [
                f"Format: {extension}",
                f"Size: {size_kb:.1f} KB",
                "Bronze tier: Basic metadata only"
            ],
            "action_items": [],
            "analysis": {
                "file_size": file_size,
                "format": extension,
                "analysis_available": False,
                "tier": "bronze"
            }
        }

    def _summarize_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Summarize document file following Company_Handbook.md rules:
        - Extract title and metadata
        - Summarize main content
        - Note document structure (headings, sections)
        - Identify document purpose

        Bronze tier: Basic info only, full extraction in Silver tier.
        """
        file_size = metadata.get("file_size", 0)
        size_kb = file_size / 1024
        extension = metadata.get("extension", "unknown")

        summary = f"Document file ({extension}, {size_kb:.1f} KB). Text extraction will be available in Silver tier."

        return {
            "summary": summary,
            "key_points": [
                f"Format: {extension}",
                f"Size: {size_kb:.1f} KB",
                "Bronze tier: Basic metadata only"
            ],
            "action_items": [],
            "analysis": {
                "file_size": file_size,
                "format": extension,
                "extraction_available": False,
                "tier": "bronze"
            }
        }

    def _summarize_unknown(
        self,
        content: str,
        metadata: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """
        Summarize unknown file type following Company_Handbook.md rules:
        - Record filename and size
        - Note that detailed analysis is not available
        - Move to Done without deep analysis
        - Log the file type for future reference
        """
        file_size = metadata.get("file_size", 0)
        size_kb = file_size / 1024
        extension = metadata.get("extension", "unknown")

        summary = f"Unknown file type ({extension}, {size_kb:.1f} KB). Detailed analysis not available for this file type."

        return {
            "summary": summary,
            "key_points": [
                f"Unknown format: {extension}",
                f"Size: {size_kb:.1f} KB",
                "No detailed analysis available"
            ],
            "action_items": [],
            "analysis": {
                "file_size": file_size,
                "extension": extension,
                "supported": False,
                "tier": "bronze"
            }
        }

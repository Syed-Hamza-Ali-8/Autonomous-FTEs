"""
File reader utility for different file types.

Supports reading text, PDF, images, and documents.
Bronze tier focuses on text files; other types return basic info.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging


class FileReader:
    """Reads content from various file types."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def read_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Read file content based on file type.

        Args:
            filepath: Path to the file to read

        Returns:
            Dictionary with:
                - content: str (file content or description)
                - file_type: str (text, pdf, image, document, unknown)
                - metadata: dict (additional info like word count, page count, etc.)
                - error: str (if reading failed)
        """
        if not filepath.exists():
            return {
                "content": None,
                "file_type": "unknown",
                "metadata": {},
                "error": f"File not found: {filepath}"
            }

        # Determine file type by extension
        suffix = filepath.suffix.lower()

        try:
            if suffix in ['.txt', '.md']:
                return self._read_text_file(filepath)
            elif suffix == '.pdf':
                return self._read_pdf_file(filepath)
            elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                return self._read_image_file(filepath)
            elif suffix in ['.docx', '.doc']:
                return self._read_document_file(filepath)
            else:
                return self._read_unknown_file(filepath)
        except Exception as e:
            self.logger.error(f"Error reading {filepath}: {e}")
            return {
                "content": None,
                "file_type": "unknown",
                "metadata": {},
                "error": str(e)
            }

    def _read_text_file(self, filepath: Path) -> Dict[str, Any]:
        """Read plain text or markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Calculate metadata
            word_count = len(content.split())
            line_count = len(content.splitlines())
            char_count = len(content)

            return {
                "content": content,
                "file_type": "text",
                "metadata": {
                    "word_count": word_count,
                    "line_count": line_count,
                    "char_count": char_count,
                    "encoding": "utf-8"
                },
                "error": None
            }
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
                return {
                    "content": content,
                    "file_type": "text",
                    "metadata": {"encoding": "latin-1"},
                    "error": None
                }
            except Exception as e:
                return {
                    "content": None,
                    "file_type": "text",
                    "metadata": {},
                    "error": f"Encoding error: {e}"
                }

    def _read_pdf_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Read PDF file.

        Bronze tier: Returns basic info only.
        Silver tier: Will implement full PDF text extraction.
        """
        file_size = filepath.stat().st_size

        return {
            "content": f"[PDF Document: {filepath.name}]\n\nNote: Full PDF text extraction will be available in Silver tier. For now, only basic metadata is captured.",
            "file_type": "pdf",
            "metadata": {
                "file_size": file_size,
                "extraction_available": False,
                "note": "Bronze tier - basic info only"
            },
            "error": None
        }

    def _read_image_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Read image file.

        Bronze tier: Returns basic info only.
        Silver tier: Will implement image analysis with vision API.
        """
        file_size = filepath.stat().st_size

        return {
            "content": f"[Image File: {filepath.name}]\n\nNote: Image analysis will be available in Silver tier with vision capabilities. For now, only basic metadata is captured.",
            "file_type": "image",
            "metadata": {
                "file_size": file_size,
                "extension": filepath.suffix,
                "analysis_available": False,
                "note": "Bronze tier - basic info only"
            },
            "error": None
        }

    def _read_document_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Read Word document.

        Bronze tier: Returns basic info only.
        Silver tier: Will implement document text extraction.
        """
        file_size = filepath.stat().st_size

        return {
            "content": f"[Document File: {filepath.name}]\n\nNote: Document text extraction will be available in Silver tier. For now, only basic metadata is captured.",
            "file_type": "document",
            "metadata": {
                "file_size": file_size,
                "extension": filepath.suffix,
                "extraction_available": False,
                "note": "Bronze tier - basic info only"
            },
            "error": None
        }

    def _read_unknown_file(self, filepath: Path) -> Dict[str, Any]:
        """Handle unknown file types."""
        file_size = filepath.stat().st_size

        return {
            "content": f"[Unknown File Type: {filepath.name}]\n\nFile type {filepath.suffix} is not recognized. Only basic metadata is available.",
            "file_type": "unknown",
            "metadata": {
                "file_size": file_size,
                "extension": filepath.suffix
            },
            "error": None
        }

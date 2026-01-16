"""
File type detection utility using Python's mimetypes module.

Provides functions to detect file types and categorize them into
user-friendly categories (text, pdf, image, document, unknown).
"""

import mimetypes
from pathlib import Path
from typing import Tuple


# Initialize mimetypes database
mimetypes.init()


def detect_file_type(filepath: Path) -> str:
    """
    Detect file type and return a user-friendly category.

    Args:
        filepath: Path to the file

    Returns:
        File type category: 'text', 'pdf', 'image', 'document', or 'unknown'
    """
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(str(filepath))

    if not mime_type:
        # Fallback to extension-based detection
        ext = filepath.suffix.lower()
        return _categorize_by_extension(ext)

    # Categorize by MIME type
    if mime_type.startswith('text/'):
        return 'text'
    elif mime_type.startswith('image/'):
        return 'image'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type in [
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.oasis.opendocument.text'
    ]:
        return 'document'
    else:
        return 'unknown'


def _categorize_by_extension(ext: str) -> str:
    """
    Categorize file by extension when MIME type is unavailable.

    Args:
        ext: File extension (including dot, e.g., '.txt')

    Returns:
        File type category
    """
    text_extensions = {'.txt', '.md', '.markdown', '.rst', '.log', '.csv', '.json', '.xml', '.yaml', '.yml'}
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico'}
    document_extensions = {'.doc', '.docx', '.odt', '.rtf'}

    if ext in text_extensions:
        return 'text'
    elif ext in image_extensions:
        return 'image'
    elif ext == '.pdf':
        return 'pdf'
    elif ext in document_extensions:
        return 'document'
    else:
        return 'unknown'


def get_mime_type(filepath: Path) -> Tuple[str, str]:
    """
    Get the MIME type and file type category for a file.

    Args:
        filepath: Path to the file

    Returns:
        Tuple of (mime_type, file_type_category)
        mime_type may be None if unknown
    """
    mime_type, _ = mimetypes.guess_type(str(filepath))
    file_type = detect_file_type(filepath)

    return (mime_type or 'application/octet-stream', file_type)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "234 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

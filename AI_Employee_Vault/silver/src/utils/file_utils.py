"""
Utility functions for file operations.

This module provides helper functions for reading, writing, and managing
files in the Obsidian vault.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory

    Raises:
        OSError: If directory cannot be created
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except OSError as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise


def read_file(file_path: Path) -> str:
    """
    Read contents of a file.

    Args:
        file_path: Path to the file

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Read file: {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def write_file(file_path: Path, content: str) -> None:
    """
    Write content to a file.

    Args:
        file_path: Path to the file
        content: Content to write

    Raises:
        IOError: If file cannot be written
    """
    try:
        # Ensure parent directory exists
        ensure_directory_exists(file_path.parent)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Wrote file: {file_path}")
    except IOError as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        raise


def move_file(source: Path, destination: Path) -> None:
    """
    Move a file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path

    Raises:
        FileNotFoundError: If source file doesn't exist
        IOError: If file cannot be moved
    """
    try:
        # Ensure destination directory exists
        ensure_directory_exists(destination.parent)

        source.rename(destination)
        logger.info(f"Moved file: {source} → {destination}")
    except FileNotFoundError:
        logger.error(f"Source file not found: {source}")
        raise
    except IOError as e:
        logger.error(f"Failed to move file {source} to {destination}: {e}")
        raise


def delete_file(file_path: Path) -> None:
    """
    Delete a file.

    Args:
        file_path: Path to the file

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be deleted
    """
    try:
        file_path.unlink()
        logger.info(f"Deleted file: {file_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except OSError as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        raise


def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    """
    List files in a directory matching a pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern (default: "*")

    Returns:
        List of file paths

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    try:
        files = list(directory.glob(pattern))
        logger.debug(f"Found {len(files)} files in {directory} matching {pattern}")
        return files
    except FileNotFoundError:
        logger.error(f"Directory not found: {directory}")
        raise


def get_file_size(file_path: Path) -> int:
    """
    Get size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    try:
        size = file_path.stat().st_size
        logger.debug(f"File size: {file_path} = {size} bytes")
        return size
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise


def file_exists(file_path: Path) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to the file

    Returns:
        True if file exists, False otherwise
    """
    exists = file_path.exists() and file_path.is_file()
    logger.debug(f"File exists check: {file_path} = {exists}")
    return exists


def directory_exists(directory: Path) -> bool:
    """
    Check if a directory exists.

    Args:
        directory: Path to the directory

    Returns:
        True if directory exists, False otherwise
    """
    exists = directory.exists() and directory.is_dir()
    logger.debug(f"Directory exists check: {directory} = {exists}")
    return exists

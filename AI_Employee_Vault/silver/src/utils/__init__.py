"""
Silver tier utilities package.

This package provides shared utility functions for the Silver tier implementation.
"""

from .logger import setup_logging, get_logger
from .yaml_parser import (
    parse_frontmatter,
    serialize_frontmatter,
    update_frontmatter_field,
    get_frontmatter_field,
    load_yaml_file,
    save_yaml_file,
)
from .file_utils import (
    ensure_directory_exists,
    read_file,
    write_file,
    move_file,
    delete_file,
    list_files,
    get_file_size,
    file_exists,
    directory_exists,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    # YAML parsing
    "parse_frontmatter",
    "serialize_frontmatter",
    "update_frontmatter_field",
    "get_frontmatter_field",
    "load_yaml_file",
    "save_yaml_file",
    # File operations
    "ensure_directory_exists",
    "read_file",
    "write_file",
    "move_file",
    "delete_file",
    "list_files",
    "get_file_size",
    "file_exists",
    "directory_exists",
]

"""
YAML parsing utilities.

This module provides helper functions for parsing and manipulating
YAML frontmatter in markdown files.
"""

import re
from typing import Dict, Any, Tuple, Optional
import yaml
import logging

logger = logging.getLogger(__name__)


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, body content)

    Example:
        >>> content = "---\\nid: 123\\n---\\nBody text"
        >>> frontmatter, body = parse_frontmatter(content)
        >>> frontmatter
        {'id': 123}
        >>> body
        'Body text'
    """
    # Match YAML frontmatter between --- delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        logger.warning("No YAML frontmatter found in content")
        return {}, content

    try:
        frontmatter_str = match.group(1)
        body = match.group(2)

        frontmatter = yaml.safe_load(frontmatter_str) or {}
        logger.debug(f"Parsed frontmatter: {len(frontmatter)} fields")

        return frontmatter, body

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML frontmatter: {e}")
        return {}, content


def serialize_frontmatter(frontmatter: Dict[str, Any], body: str) -> str:
    """
    Serialize frontmatter and body into markdown content.

    Args:
        frontmatter: Dictionary of frontmatter fields
        body: Markdown body content

    Returns:
        Complete markdown content with YAML frontmatter

    Example:
        >>> frontmatter = {'id': 123, 'status': 'pending'}
        >>> body = 'Body text'
        >>> content = serialize_frontmatter(frontmatter, body)
        >>> print(content)
        ---
        id: 123
        status: pending
        ---
        Body text
    """
    try:
        # Serialize frontmatter to YAML
        frontmatter_str = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        # Combine with body
        content = f"---\n{frontmatter_str}---\n{body}"
        logger.debug("Serialized frontmatter and body")

        return content

    except yaml.YAMLError as e:
        logger.error(f"Failed to serialize YAML frontmatter: {e}")
        raise


def update_frontmatter_field(
    content: str,
    field: str,
    value: Any
) -> str:
    """
    Update a single field in YAML frontmatter.

    Args:
        content: Markdown content with YAML frontmatter
        field: Field name to update
        value: New value for the field

    Returns:
        Updated markdown content

    Example:
        >>> content = "---\\nstatus: pending\\n---\\nBody"
        >>> updated = update_frontmatter_field(content, 'status', 'approved')
        >>> # status is now 'approved'
    """
    frontmatter, body = parse_frontmatter(content)
    frontmatter[field] = value
    return serialize_frontmatter(frontmatter, body)


def get_frontmatter_field(
    content: str,
    field: str,
    default: Any = None
) -> Any:
    """
    Get a single field from YAML frontmatter.

    Args:
        content: Markdown content with YAML frontmatter
        field: Field name to retrieve
        default: Default value if field not found

    Returns:
        Field value or default

    Example:
        >>> content = "---\\nid: 123\\n---\\nBody"
        >>> get_frontmatter_field(content, 'id')
        123
        >>> get_frontmatter_field(content, 'missing', 'default')
        'default'
    """
    frontmatter, _ = parse_frontmatter(content)
    return frontmatter.get(field, default)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration from a file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary of configuration values

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded YAML config from {file_path}")
        return config
    except FileNotFoundError:
        logger.error(f"YAML file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {e}")
        raise


def save_yaml_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to a YAML file.

    Args:
        file_path: Path to YAML file
        data: Dictionary to save

    Raises:
        IOError: If file cannot be written
        yaml.YAMLError: If data cannot be serialized
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        logger.info(f"Saved YAML config to {file_path}")
    except IOError as e:
        logger.error(f"Failed to write YAML file {file_path}: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to serialize data to YAML: {e}")
        raise

"""
YAML frontmatter parser utility.

Provides functions to parse and write YAML frontmatter in markdown files.
Frontmatter is delimited by '---' at the start and end.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Tuple


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Tuple of (frontmatter_dict, body_content)
        If no frontmatter found, returns ({}, content)
    """
    lines = content.split('\n')

    # Check if file starts with frontmatter delimiter
    if not lines or lines[0].strip() != '---':
        return ({}, content)

    # Find the closing delimiter
    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break

    if end_index is None:
        # No closing delimiter found
        return ({}, content)

    # Extract frontmatter and body
    frontmatter_lines = lines[1:end_index]
    body_lines = lines[end_index + 1:]

    # Parse YAML
    try:
        frontmatter_yaml = '\n'.join(frontmatter_lines)
        frontmatter = yaml.safe_load(frontmatter_yaml) or {}
    except yaml.YAMLError:
        # Invalid YAML, return empty dict
        frontmatter = {}

    body = '\n'.join(body_lines)

    return (frontmatter, body)


def read_file_with_frontmatter(filepath: Path) -> Tuple[Dict[str, Any], str]:
    """
    Read a markdown file and parse its frontmatter.

    Args:
        filepath: Path to the markdown file

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return parse_frontmatter(content)


def write_file_with_frontmatter(
    filepath: Path,
    frontmatter: Dict[str, Any],
    body: str
) -> None:
    """
    Write a markdown file with YAML frontmatter.

    Args:
        filepath: Path to the markdown file
        frontmatter: Dictionary to serialize as YAML frontmatter
        body: Markdown body content
    """
    # Serialize frontmatter to YAML
    frontmatter_yaml = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )

    # Construct full content
    content = f"---\n{frontmatter_yaml}---\n\n{body}"

    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def update_frontmatter(
    filepath: Path,
    updates: Dict[str, Any]
) -> None:
    """
    Update specific fields in a file's frontmatter.

    Args:
        filepath: Path to the markdown file
        updates: Dictionary of fields to update
    """
    # Read existing content
    frontmatter, body = read_file_with_frontmatter(filepath)

    # Update frontmatter
    frontmatter.update(updates)

    # Write back
    write_file_with_frontmatter(filepath, frontmatter, body)

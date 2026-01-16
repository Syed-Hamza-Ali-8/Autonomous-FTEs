#!/usr/bin/env python3
"""
Input Validation Utilities

Provides validation functions for all Silver tier components:
- Email validation
- Phone number validation
- File format validation
- Configuration validation
- Action parameter validation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import yaml


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, f"Invalid email format: {email}"

    # Check length constraints
    if len(email) > 254:  # RFC 5321
        return False, "Email address too long (max 254 characters)"

    local, domain = email.rsplit('@', 1)
    if len(local) > 64:  # RFC 5321
        return False, "Email local part too long (max 64 characters)"

    return True, None


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate (with or without country code)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone or not isinstance(phone, str):
        return False, "Phone number must be a non-empty string"

    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # Check if it starts with + (international format)
    if cleaned.startswith('+'):
        # International format: +[country code][number]
        if not re.match(r'^\+\d{10,15}$', cleaned):
            return False, "Invalid international phone format (use +[country][number])"
    else:
        # Local format: just digits
        if not re.match(r'^\d{10,15}$', cleaned):
            return False, "Invalid phone number (must be 10-15 digits)"

    return True, None


def validate_contact_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate contact name for WhatsApp.

    Args:
        name: Contact name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Contact name must be a non-empty string"

    # Check length
    if len(name) < 1:
        return False, "Contact name cannot be empty"

    if len(name) > 100:
        return False, "Contact name too long (max 100 characters)"

    # Check for invalid characters (basic check)
    if re.search(r'[<>\"\'\\]', name):
        return False, "Contact name contains invalid characters"

    return True, None


def validate_yaml_frontmatter(content: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate YAML frontmatter in markdown file.

    Args:
        content: File content with YAML frontmatter

    Returns:
        Tuple of (is_valid, error_message, parsed_frontmatter)
    """
    if not content or not isinstance(content, str):
        return False, "Content must be a non-empty string", None

    # Check for frontmatter delimiters
    if not content.startswith('---'):
        return False, "Missing YAML frontmatter (must start with ---)", None

    # Split frontmatter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False, "Invalid YAML frontmatter format", None

    try:
        frontmatter = yaml.safe_load(parts[1])
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary", None
        return True, None, frontmatter
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}", None


def validate_action_file(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate action file format and required fields.

    Args:
        file_path: Path to action file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    if not file_path.is_file():
        return False, f"Not a file: {file_path}"

    if file_path.suffix != '.md':
        return False, f"Invalid file extension (must be .md): {file_path}"

    try:
        content = file_path.read_text()
    except Exception as e:
        return False, f"Cannot read file: {e}"

    # Validate frontmatter
    is_valid, error, frontmatter = validate_yaml_frontmatter(content)
    if not is_valid:
        return False, error

    # Check required fields
    required_fields = ['id', 'type', 'status', 'created_at']
    missing_fields = [f for f in required_fields if f not in frontmatter]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Validate status values
    valid_statuses = ['pending', 'approved', 'rejected', 'in_progress', 'completed', 'failed']
    if frontmatter['status'] not in valid_statuses:
        return False, f"Invalid status: {frontmatter['status']} (must be one of {valid_statuses})"

    return True, None


def validate_schedule_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate schedule configuration.

    Args:
        config: Schedule configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Schedule config must be a dictionary"

    # Check required fields
    required_fields = ['schedule_type', 'schedule_config', 'task_config']
    missing_fields = [f for f in required_fields if f not in config]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    # Validate schedule type
    valid_types = ['daily', 'weekly', 'monthly', 'interval']
    if config['schedule_type'] not in valid_types:
        return False, f"Invalid schedule_type: {config['schedule_type']} (must be one of {valid_types})"

    # Validate schedule_config based on type
    schedule_config = config['schedule_config']
    schedule_type = config['schedule_type']

    if schedule_type == 'daily':
        if 'time' not in schedule_config:
            return False, "Daily schedule requires 'time' field"
        if not re.match(r'^\d{2}:\d{2}$', schedule_config['time']):
            return False, "Time must be in HH:MM format"

    elif schedule_type == 'weekly':
        if 'day' not in schedule_config or 'time' not in schedule_config:
            return False, "Weekly schedule requires 'day' and 'time' fields"
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if schedule_config['day'].lower() not in valid_days:
            return False, f"Invalid day: {schedule_config['day']}"
        if not re.match(r'^\d{2}:\d{2}$', schedule_config['time']):
            return False, "Time must be in HH:MM format"

    elif schedule_type == 'monthly':
        if 'day' not in schedule_config or 'time' not in schedule_config:
            return False, "Monthly schedule requires 'day' and 'time' fields"
        try:
            day = int(schedule_config['day'])
            if day < 1 or day > 31:
                return False, "Day must be between 1 and 31"
        except ValueError:
            return False, "Day must be a number"
        if not re.match(r'^\d{2}:\d{2}$', schedule_config['time']):
            return False, "Time must be in HH:MM format"

    elif schedule_type == 'interval':
        if 'minutes' not in schedule_config:
            return False, "Interval schedule requires 'minutes' field"
        try:
            minutes = int(schedule_config['minutes'])
            if minutes < 1:
                return False, "Interval must be at least 1 minute"
        except ValueError:
            return False, "Minutes must be a number"

    return True, None


def validate_approval_rules(rules: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate approval rules configuration.

    Args:
        rules: Approval rules dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(rules, dict):
        return False, "Approval rules must be a dictionary"

    # Check required fields
    if 'sensitive_actions' not in rules:
        return False, "Missing 'sensitive_actions' field"

    if not isinstance(rules['sensitive_actions'], list):
        return False, "'sensitive_actions' must be a list"

    # Validate each sensitive action
    for i, action in enumerate(rules['sensitive_actions']):
        if not isinstance(action, dict):
            return False, f"Action {i} must be a dictionary"

        if 'action_type' not in action:
            return False, f"Action {i} missing 'action_type' field"

        if 'timeout_minutes' in action:
            try:
                timeout = int(action['timeout_minutes'])
                if timeout < 1:
                    return False, f"Action {i} timeout must be at least 1 minute"
            except ValueError:
                return False, f"Action {i} timeout must be a number"

    return True, None


def validate_watcher_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate watcher configuration.

    Args:
        config: Watcher configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Watcher config must be a dictionary"

    # Validate each watcher
    for watcher_name, watcher_config in config.items():
        if not isinstance(watcher_config, dict):
            return False, f"{watcher_name} config must be a dictionary"

        # Check poll_interval
        if 'poll_interval' in watcher_config:
            try:
                interval = int(watcher_config['poll_interval'])
                if interval < 10:
                    return False, f"{watcher_name} poll_interval must be at least 10 seconds"
            except ValueError:
                return False, f"{watcher_name} poll_interval must be a number"

        # Check enabled flag
        if 'enabled' in watcher_config:
            if not isinstance(watcher_config['enabled'], bool):
                return False, f"{watcher_name} enabled must be a boolean"

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove invalid characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename


def validate_path_safety(path: Path, allowed_base: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that a path is within allowed base directory (prevent path traversal).

    Args:
        path: Path to validate
        allowed_base: Base directory that path must be within

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Resolve to absolute paths
        abs_path = path.resolve()
        abs_base = allowed_base.resolve()

        # Check if path is within base
        if not str(abs_path).startswith(str(abs_base)):
            return False, f"Path {path} is outside allowed directory {allowed_base}"

        return True, None
    except Exception as e:
        return False, f"Path validation error: {e}"

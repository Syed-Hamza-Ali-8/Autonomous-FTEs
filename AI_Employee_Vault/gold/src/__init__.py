"""
Gold Tier Package

Autonomous Employee - Gold Tier Implementation
"""

__version__ = "1.0.0-alpha"
__author__ = "Gold Tier Development Team"

from .utils import setup_logging, load_config, get_vault_path

__all__ = [
    "setup_logging",
    "load_config",
    "get_vault_path",
]

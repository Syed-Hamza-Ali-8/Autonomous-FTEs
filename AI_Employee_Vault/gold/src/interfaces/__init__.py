"""
Gold Tier Interfaces Package

Abstract interfaces for swappable implementations.
"""

from .accounting_interface import AccountingInterface
from .social_media_interface import SocialMediaInterface, PostStatus, EngagementType

__all__ = [
    "AccountingInterface",
    "SocialMediaInterface",
    "PostStatus",
    "EngagementType",
]

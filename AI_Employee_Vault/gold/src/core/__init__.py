"""
Gold Tier Core Package

Foundation components for error recovery, audit logging, and health monitoring.
"""

__version__ = "1.0.0-alpha"
__author__ = "Gold Tier Development Team"

from .error_recovery import ErrorRecovery, ErrorType, with_retry
from .audit_logger import AuditLogger, ActionType, ActorType, AuditLogEntry
from .health_monitor import HealthMonitor
from .ralph_wiggum import RalphWiggumLoop

__all__ = [
    "ErrorRecovery",
    "ErrorType",
    "with_retry",
    "AuditLogger",
    "ActionType",
    "ActorType",
    "AuditLogEntry",
    "HealthMonitor",
    "RalphWiggumLoop",
]

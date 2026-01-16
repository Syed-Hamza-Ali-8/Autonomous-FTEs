"""
Actions module for executing external actions.

This module provides:
- ActionExecutor: Main orchestrator for action execution
- EmailSender: Gmail API integration for sending emails
- WhatsAppSender: WhatsApp Web automation for sending messages
"""

from .action_executor import ActionExecutor
from .email_sender import EmailSender
from .whatsapp_sender import WhatsAppSender

__all__ = [
    "ActionExecutor",
    "EmailSender",
    "WhatsAppSender",
]

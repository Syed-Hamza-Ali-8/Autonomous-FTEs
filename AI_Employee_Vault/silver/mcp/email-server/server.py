#!/usr/bin/env python3
"""
Email MCP Server - Official FastMCP Pattern

A Model Context Protocol server that provides email sending capabilities
using Gmail API with OAuth2 authentication.

This implementation follows the official MCP Python SDK patterns:
- Uses FastMCP for automatic tool registration
- Uses @mcp.tool() decorator with type hints
- Async/await for all operations
- Proper error handling and logging to stderr
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp.server.fastmcp import FastMCP  # pyright: ignore[reportMissingImports]

from silver.src.actions.email_sender import EmailSender
from silver.src.utils.validators import validate_email as validate_email_format

# Configure logging to stderr (CRITICAL for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # MUST use stderr, not stdout
)
logger = logging.getLogger("email-mcp-server")

# Initialize FastMCP server
mcp = FastMCP("email-server")

# Global email sender instance (lazy initialization)
_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """
    Get or create email sender instance.

    Uses lazy initialization to avoid loading credentials until needed.
    """
    global _email_sender

    if _email_sender is None:
        vault_path = os.getenv(
            "VAULT_PATH",
            "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        )

        _email_sender = EmailSender(vault_path)
        logger.info("EmailSender initialized")

    return _email_sender


@mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = True
) -> str:
    """
    Send an email via Gmail API with OAuth2 authentication.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        from_email: Sender email address (optional, uses authenticated account by default)
        cc: CC recipients (comma-separated, optional)
        bcc: BCC recipients (comma-separated, optional)
        html: Whether body is HTML (default: True)

    Returns:
        Success message with message ID or error message

    Examples:
        >>> await send_email(
        ...     to="user@example.com",
        ...     subject="Test Email",
        ...     body="Hello from AI Employee!"
        ... )
        "✅ Email sent successfully! Message ID: <abc123@gmail.com>"
    """
    try:
        # Validate recipient email
        is_valid, error = validate_email_format(to)
        if not is_valid:
            return f"❌ Invalid recipient email: {error}"

        # Validate sender email if provided
        if from_email:
            is_valid, error = validate_email_format(from_email)
            if not is_valid:
                return f"❌ Invalid sender email: {error}"

        # Get email sender instance
        sender = get_email_sender()

        # Send email
        logger.info(f"Sending email to {to}: {subject}")
        result = sender.send_email(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            cc=cc,
            bcc=bcc,
            html=html
        )

        if result.get("success"):
            message_id = result.get("message_id", "unknown")
            return f"✅ Email sent successfully!\nMessage ID: {message_id}\nTo: {to}\nSubject: {subject}"
        else:
            error = result.get("error", "Unknown error")
            return f"❌ Failed to send email: {error}"

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return f"❌ Error sending email: {str(e)}"


@mcp.tool()
async def validate_email(email: str) -> str:
    """
    Validate email address format (RFC 5321 compliant).

    Args:
        email: Email address to validate

    Returns:
        Validation result message

    Examples:
        >>> await validate_email("user@example.com")
        "✅ Valid email address: user@example.com"

        >>> await validate_email("invalid-email")
        "❌ Invalid email address: Missing @ symbol"
    """
    try:
        is_valid, error = validate_email_format(email)

        if is_valid:
            return f"✅ Valid email address: {email}"
        else:
            return f"❌ Invalid email address: {error}"

    except Exception as e:
        logger.error(f"Error validating email: {e}", exc_info=True)
        return f"❌ Error validating email: {str(e)}"


@mcp.tool()
async def get_email_status() -> str:
    """
    Get the status of the email service.

    Returns:
        Status message indicating if email service is configured and ready

    Examples:
        >>> await get_email_status()
        "✅ Email service ready. Authenticated as: hey349073@gmail.com"
    """
    try:
        sender = get_email_sender()

        # Check if credentials are configured
        if hasattr(sender, 'smtp_user') and sender.smtp_user:
            return f"✅ Email service ready. Authenticated as: {sender.smtp_user}"
        else:
            return "⚠️ Email service initialized but credentials not fully configured"

    except Exception as e:
        logger.error(f"Error checking email status: {e}", exc_info=True)
        return f"❌ Email service not available: {str(e)}"


def main():
    """
    Run the Email MCP server.

    This server provides email sending capabilities via the Model Context Protocol.
    It uses stdio transport for communication with MCP clients.
    """
    logger.info("Starting Email MCP Server (FastMCP)...")
    logger.info("Server name: email-server")
    logger.info("Available tools: send_email, validate_email, get_email_status")

    # Run server with stdio transport
    # FastMCP handles all the complexity of MCP protocol
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

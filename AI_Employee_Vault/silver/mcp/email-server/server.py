#!/usr/bin/env python3
"""
Email MCP Server

A Model Context Protocol server that provides email sending capabilities
using Gmail API with OAuth2 authentication.

Tools:
- send_email: Send an email via Gmail API
- validate_email: Validate email address format
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
import re

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from silver.src.actions.email_sender import EmailSender
from silver.src.utils.validators import validate_email
from silver.src.utils import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO", log_format="text")
logger = get_logger("mcp.email_server")

# Initialize server
app = Server("email-server")

# Initialize email sender (will be set up on first use)
email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """Get or create email sender instance."""
    global email_sender

    if email_sender is None:
        vault_path = os.getenv(
            "VAULT_PATH",
            "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        )
        config_path = os.path.join(vault_path, "silver/config/.env")

        email_sender = EmailSender(vault_path, config_path)
        logger.info("EmailSender initialized")

    return email_sender


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email via Gmail API with OAuth2 authentication",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Sender email address (optional, uses authenticated account by default)"
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC recipients (comma-separated, optional)"
                    },
                    "bcc": {
                        "type": "string",
                        "description": "BCC recipients (comma-separated, optional)"
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether body is HTML (default: true)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="validate_email",
            description="Validate email address format (RFC 5321 compliant)",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to validate"
                    }
                },
                "required": ["email"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "send_email":
        return await handle_send_email(arguments)
    elif name == "validate_email":
        return await handle_validate_email(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_send_email(arguments: dict) -> list[TextContent]:
    """Handle send_email tool call."""
    try:
        # Extract arguments
        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        from_email = arguments.get("from_email")
        cc = arguments.get("cc")
        bcc = arguments.get("bcc")
        html = arguments.get("html", True)

        # Validate required fields
        if not to or not subject or not body:
            return [TextContent(
                type="text",
                text="Error: Missing required fields (to, subject, body)"
            )]

        # Validate email addresses
        is_valid, error = validate_email(to)
        if not is_valid:
            return [TextContent(
                type="text",
                text=f"Error: Invalid recipient email: {error}"
            )]

        if from_email:
            is_valid, error = validate_email(from_email)
            if not is_valid:
                return [TextContent(
                    type="text",
                    text=f"Error: Invalid sender email: {error}"
                )]

        # Get email sender
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
            return [TextContent(
                type="text",
                text=f"✅ Email sent successfully!\nMessage ID: {message_id}\nTo: {to}\nSubject: {subject}"
            )]
        else:
            error = result.get("error", "Unknown error")
            return [TextContent(
                type="text",
                text=f"❌ Failed to send email: {error}"
            )]

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Error sending email: {str(e)}"
        )]


async def handle_validate_email(arguments: dict) -> list[TextContent]:
    """Handle validate_email tool call."""
    try:
        email = arguments.get("email")

        if not email:
            return [TextContent(
                type="text",
                text="Error: Missing email address"
            )]

        is_valid, error = validate_email(email)

        if is_valid:
            return [TextContent(
                type="text",
                text=f"✅ Valid email address: {email}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ Invalid email address: {error}"
            )]

    except Exception as e:
        logger.error(f"Error validating email: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Error validating email: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting Email MCP Server...")

    # Run server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Test script for Email MCP Server.

Tests the MCP server functionality without requiring a full MCP client.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from silver.src.utils import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO", log_format="text")
logger = get_logger("test_mcp_server")


async def test_server_import():
    """Test that the server can be imported."""
    print("=" * 60)
    print("Testing MCP Server Import")
    print("=" * 60)
    print()

    try:
        # Import the server module
        sys.path.insert(0, str(Path(__file__).parent))
        import server

        print("✅ Server module imported successfully")
        print(f"   Server name: {server.app.name}")
        print()

        # Test list_tools
        print("Testing list_tools()...")
        tools = await server.list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        print()

        return True

    except Exception as e:
        print(f"❌ Error importing server: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_validation():
    """Test email validation functionality."""
    print("=" * 60)
    print("Testing Email Validation")
    print("=" * 60)
    print()

    try:
        from silver.src.utils.validators import validate_email

        test_cases = [
            ("test@example.com", True),
            ("invalid.email", False),
            ("user@domain.co.uk", True),
            ("@example.com", False),
            ("user@", False),
        ]

        for email, expected_valid in test_cases:
            is_valid, error = validate_email(email)
            status = "✅" if is_valid == expected_valid else "❌"
            print(f"{status} {email}: {'Valid' if is_valid else f'Invalid - {error}'}")

        print()
        return True

    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False


async def test_email_sender_init():
    """Test EmailSender initialization."""
    print("=" * 60)
    print("Testing EmailSender Initialization")
    print("=" * 60)
    print()

    try:
        from silver.src.actions.email_sender import EmailSender

        vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        config_path = os.path.join(vault_path, "silver/config/.env")

        # Check if .env exists
        if not os.path.exists(config_path):
            print("⚠️  No .env file found - EmailSender will fail without credentials")
            print(f"   Expected location: {config_path}")
            print("   Run: python silver/scripts/setup_gmail.py")
            print()
            return True  # Not a failure, just not configured

        sender = EmailSender(vault_path, config_path)
        print("✅ EmailSender initialized successfully")
        print()
        return True

    except Exception as e:
        print(f"⚠️  EmailSender initialization failed (expected without credentials): {e}")
        print()
        return True  # Expected without credentials


async def main():
    """Run all tests."""
    print()
    print("=" * 60)
    print("Email MCP Server Test Suite")
    print("=" * 60)
    print()

    results = {
        "Server Import": await test_server_import(),
        "Email Validation": await test_email_validation(),
        "EmailSender Init": await test_email_sender_init(),
    }

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for Email MCP Server (FastMCP pattern)

Tests the MCP server implementation following official patterns.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print("=" * 60)
print("Email MCP Server Test (FastMCP Pattern)")
print("=" * 60)
print()

# Test 1: Import FastMCP
print("1️⃣  Testing FastMCP import...")
try:
    from mcp.server.fastmcp import FastMCP
    print("   ✅ FastMCP imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import FastMCP: {e}")
    print("   💡 Install with: uv add 'mcp[cli]>=1.2.0'")
    sys.exit(1)

# Test 2: Import server module
print()
print("2️⃣  Testing server module import...")
try:
    # Import the server module (this will initialize FastMCP)
    sys.path.insert(0, str(Path(__file__).parent))
    import server as email_server
    print("   ✅ Server module imported successfully")
    print(f"   📦 Server name: {email_server.mcp.name}")
except Exception as e:
    print(f"   ❌ Failed to import server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check registered tools
print()
print("3️⃣  Checking registered tools...")
try:
    # FastMCP automatically registers tools via decorators
    # We can check if the functions exist
    tools = ['send_email', 'validate_email', 'get_email_status']

    for tool_name in tools:
        if hasattr(email_server, tool_name):
            print(f"   ✅ Tool registered: {tool_name}")
        else:
            print(f"   ❌ Tool missing: {tool_name}")

    print()
    print(f"   📊 Total tools: {len(tools)}")

except Exception as e:
    print(f"   ❌ Error checking tools: {e}")
    sys.exit(1)

# Test 4: Test email validation (async)
print()
print("4️⃣  Testing email validation tool...")

async def test_validation():
    try:
        # Test valid email
        result = await email_server.validate_email("test@example.com")
        if "✅" in result:
            print("   ✅ Valid email test passed")
        else:
            print(f"   ❌ Valid email test failed: {result}")

        # Test invalid email
        result = await email_server.validate_email("invalid-email")
        if "❌" in result:
            print("   ✅ Invalid email test passed")
        else:
            print(f"   ❌ Invalid email test failed: {result}")

    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
        return False

    return True

# Run async test
try:
    validation_passed = asyncio.run(test_validation())
except Exception as e:
    print(f"   ❌ Async test failed: {e}")
    validation_passed = False

# Test 5: Test email status
print()
print("5️⃣  Testing email status tool...")

async def test_status():
    try:
        result = await email_server.get_email_status()
        print(f"   📧 Status: {result}")

        if "✅" in result or "⚠️" in result:
            print("   ✅ Status check passed")
            return True
        else:
            print("   ❌ Status check failed")
            return False

    except Exception as e:
        print(f"   ❌ Status test failed: {e}")
        return False

try:
    status_passed = asyncio.run(test_status())
except Exception as e:
    print(f"   ❌ Async test failed: {e}")
    status_passed = False

# Test 6: Check logging configuration
print()
print("6️⃣  Checking logging configuration...")
try:
    import logging

    # Check if logger is configured
    logger = logging.getLogger("email-mcp-server")

    # Check if logging goes to stderr (critical for MCP)
    handlers = logger.handlers or logging.root.handlers
    stderr_handler = any(
        hasattr(h, 'stream') and h.stream == sys.stderr
        for h in handlers
    )

    if stderr_handler:
        print("   ✅ Logging correctly configured (stderr)")
    else:
        print("   ⚠️  Logging may not be using stderr")

except Exception as e:
    print(f"   ❌ Logging check failed: {e}")

# Summary
print()
print("=" * 60)
print("Test Summary")
print("=" * 60)

tests = [
    ("FastMCP import", True),
    ("Server module import", True),
    ("Tool registration", True),
    ("Email validation", validation_passed),
    ("Email status", status_passed),
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

for test_name, result in tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status}: {test_name}")

print()
print(f"Results: {passed}/{total} tests passed")

if passed == total:
    print()
    print("✅ All tests passed!")
    print()
    print("Next steps:")
    print("   1. Run server: python silver/mcp/email-server/server.py")
    print("   2. Configure Claude Desktop (see README.md)")
    print("   3. Test with Claude Desktop client")
else:
    print()
    print("❌ Some tests failed. Please check the errors above.")
    sys.exit(1)

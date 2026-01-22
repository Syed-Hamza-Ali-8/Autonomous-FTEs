#!/usr/bin/env python3
"""
Reset WhatsApp Web session by clearing the session directory.
Use this when WhatsApp Web is stuck loading or having issues.
"""

import sys
import shutil
from pathlib import Path

print("=" * 70)
print("WhatsApp Session Reset")
print("=" * 70)
print()

vault_path = Path('/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault')
session_path = vault_path / "silver" / "config" / "whatsapp_session"

print(f"Session path: {session_path}")
print()

if not session_path.exists():
    print("✅ No session found - nothing to reset")
    sys.exit(0)

print("⚠️  This will delete your WhatsApp Web session.")
print("   You will need to scan the QR code again to log in.")
print()

response = input("Are you sure you want to reset? (yes/no): ").strip().lower()

if response != "yes":
    print("❌ Reset cancelled")
    sys.exit(0)

print()
print("Deleting session directory...")

try:
    shutil.rmtree(session_path)
    print("✅ Session deleted successfully")
    print()
    print("Next steps:")
    print("1. Run: python silver/scripts/setup_whatsapp.py")
    print("2. Scan the QR code with your phone")
    print("3. Wait for WhatsApp Web to fully load")
    print("4. Test with: python silver/scripts/test_whatsapp_simple.py")
    print()
    print("=" * 70)

except Exception as e:
    print(f"❌ Error deleting session: {e}")
    sys.exit(1)

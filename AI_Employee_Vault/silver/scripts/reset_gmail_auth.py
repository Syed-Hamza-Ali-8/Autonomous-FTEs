#!/usr/bin/env python3
"""
Reset Gmail authentication by clearing the refresh token.
This forces re-authentication with a new Gmail account.
"""

import os
import sys
from pathlib import Path


def reset_gmail_auth(vault_path: str) -> None:
    """
    Reset Gmail authentication by clearing the refresh token.

    Args:
        vault_path: Path to the vault root directory
    """
    print("=" * 60)
    print("Reset Gmail Authentication")
    print("=" * 60)
    print()

    env_path = Path(vault_path) / "silver" / "config" / ".env"

    if not env_path.exists():
        print("❌ .env file not found!")
        print(f"   Expected location: {env_path}")
        sys.exit(1)

    print("📋 Current status:")
    print(f"   .env file: {env_path}")
    print()

    # Read existing .env file
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Clear refresh token
    updated_lines = []
    token_found = False

    for line in lines:
        if line.startswith('GMAIL_REFRESH_TOKEN='):
            updated_lines.append('GMAIL_REFRESH_TOKEN=\n')
            token_found = True
            print("✅ Cleared GMAIL_REFRESH_TOKEN")
        else:
            updated_lines.append(line)

    if not token_found:
        print("⚠️  GMAIL_REFRESH_TOKEN not found in .env")
        print("   This is okay - it will be added during setup")

    # Write updated .env file
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    print()
    print("✅ Gmail authentication reset complete!")
    print()
    print("Next steps:")
    print("   1. Add new test user in Google Cloud Console")
    print("   2. Run: python silver/scripts/setup_gmail.py")
    print("   3. Authenticate with the new Gmail account")
    print()


def main():
    """Main entry point."""
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )

    reset_gmail_auth(vault_path)


if __name__ == "__main__":
    main()

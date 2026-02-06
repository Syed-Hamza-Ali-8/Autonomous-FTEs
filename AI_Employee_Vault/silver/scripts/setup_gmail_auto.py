#!/usr/bin/env python3
"""
Gmail API setup script (automatic mode).

This script reads credentials from .env and runs OAuth2 flow to get refresh token.
"""

import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


def setup_gmail_credentials(vault_path: str) -> None:
    """
    Set up Gmail API credentials through OAuth2 flow.

    Args:
        vault_path: Path to the vault root directory
    """
    print("=" * 60)
    print("Gmail API Setup (Automatic)")
    print("=" * 60)
    print()

    # Load .env file
    env_path = Path(vault_path) / "silver" / "config" / ".env"

    if not env_path.exists():
        print("❌ .env file not found!")
        print(f"   Expected location: {env_path}")
        sys.exit(1)

    # Load environment variables
    load_dotenv(env_path)

    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Gmail credentials not found in .env file!")
        print("   Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET")
        sys.exit(1)

    print("✅ Loaded credentials from .env file")
    print(f"   Client ID: {client_id[:20]}...")
    print()

    print("🔐 Starting OAuth2 flow...")
    print("   A browser window will open for authentication")
    print("   Please sign in with your Gmail account")
    print()

    try:
        # Create OAuth2 flow
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            },
            scopes=SCOPES
        )

        # Run OAuth2 flow
        creds = flow.run_local_server(port=0)

        print()
        print("✅ Authentication successful!")
        print()

        # Update .env file
        print("📝 Updating .env file with refresh token...")
        update_env_file(env_path, creds.refresh_token)

        print()
        print("✅ Gmail API setup complete!")
        print()
        print("Credentials saved:")
        print(f"   Client ID: {client_id[:20]}...")
        print(f"   Refresh Token: {creds.refresh_token[:20]}...")
        print()

    except Exception as e:
        print()
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


def update_env_file(env_path: Path, refresh_token: str) -> None:
    """
    Update .env file with refresh token.

    Args:
        env_path: Path to .env file
        refresh_token: OAuth2 refresh token
    """
    # Read existing .env file
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Update refresh token
    updated_lines = []
    token_updated = False

    for line in lines:
        if line.startswith('GMAIL_REFRESH_TOKEN='):
            updated_lines.append(f'GMAIL_REFRESH_TOKEN={refresh_token}\n')
            token_updated = True
        else:
            updated_lines.append(line)

    # Add refresh token if not found
    if not token_updated:
        updated_lines.append(f'\nGMAIL_REFRESH_TOKEN={refresh_token}\n')

    # Write updated .env file
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)


def main():
    """Main entry point."""
    # Get vault path from environment or use default
    vault_path = os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    )

    setup_gmail_credentials(vault_path)


if __name__ == "__main__":
    main()

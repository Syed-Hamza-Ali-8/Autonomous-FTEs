#!/usr/bin/env python3
"""
Gmail API setup script.

This script guides the user through setting up Gmail API credentials
and generating OAuth2 tokens for the Gmail watcher.
"""

import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup_gmail_credentials(vault_path: str) -> None:
    """
    Set up Gmail API credentials through OAuth2 flow.

    Args:
        vault_path: Path to the vault root directory
    """
    print("=" * 60)
    print("Gmail API Setup")
    print("=" * 60)
    print()

    # Check if .env file exists
    env_path = Path(vault_path) / "silver" / "config" / ".env"

    if not env_path.exists():
        print("❌ .env file not found!")
        print(f"   Expected location: {env_path}")
        print()
        print("Please create .env file from template:")
        print(f"   cp {env_path.parent}/.env.example {env_path}")
        sys.exit(1)

    print("📋 Prerequisites:")
    print("   1. Google Cloud Project created")
    print("   2. Gmail API enabled")
    print("   3. OAuth2 credentials created (Desktop app)")
    print()
    print("If you haven't done this yet, visit:")
    print("   https://console.cloud.google.com/")
    print()

    # Ask for credentials
    print("Enter your Gmail API credentials:")
    print()

    client_id = input("Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        sys.exit(1)

    client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        sys.exit(1)

    print()
    print("🔐 Starting OAuth2 flow...")
    print("   A browser window will open for authentication")
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
        print("📝 Updating .env file...")
        update_env_file(env_path, client_id, client_secret, creds.refresh_token)

        print()
        print("✅ Gmail API setup complete!")
        print()
        print("Next steps:")
        print("   1. Test the connection: python silver/scripts/test_smtp.py")
        print("   2. Start the watcher: python -m silver.src.watchers.gmail_watcher")
        print()

    except Exception as e:
        print()
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


def update_env_file(env_path: Path, client_id: str, client_secret: str, refresh_token: str) -> None:
    """
    Update .env file with Gmail credentials.

    Args:
        env_path: Path to .env file
        client_id: Gmail API client ID
        client_secret: Gmail API client secret
        refresh_token: OAuth2 refresh token
    """
    # Read existing .env file
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Update Gmail credentials
    updated_lines = []
    credentials_updated = {
        'GMAIL_CLIENT_ID': False,
        'GMAIL_CLIENT_SECRET': False,
        'GMAIL_REFRESH_TOKEN': False
    }

    for line in lines:
        if line.startswith('GMAIL_CLIENT_ID='):
            updated_lines.append(f'GMAIL_CLIENT_ID={client_id}\n')
            credentials_updated['GMAIL_CLIENT_ID'] = True
        elif line.startswith('GMAIL_CLIENT_SECRET='):
            updated_lines.append(f'GMAIL_CLIENT_SECRET={client_secret}\n')
            credentials_updated['GMAIL_CLIENT_SECRET'] = True
        elif line.startswith('GMAIL_REFRESH_TOKEN='):
            updated_lines.append(f'GMAIL_REFRESH_TOKEN={refresh_token}\n')
            credentials_updated['GMAIL_REFRESH_TOKEN'] = True
        else:
            updated_lines.append(line)

    # Add missing credentials
    if not credentials_updated['GMAIL_CLIENT_ID']:
        updated_lines.append(f'\nGMAIL_CLIENT_ID={client_id}\n')
    if not credentials_updated['GMAIL_CLIENT_SECRET']:
        updated_lines.append(f'GMAIL_CLIENT_SECRET={client_secret}\n')
    if not credentials_updated['GMAIL_REFRESH_TOKEN']:
        updated_lines.append(f'GMAIL_REFRESH_TOKEN={refresh_token}\n')

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

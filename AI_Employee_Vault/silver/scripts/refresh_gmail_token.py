#!/usr/bin/env python3
"""
Quick Gmail Token Refresh Script

This script uses your existing Client ID and Secret to get a new refresh token.
It will open a browser for you to authenticate.
"""

import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def refresh_gmail_token():
    """Get a new Gmail refresh token."""

    print("=" * 70)
    print("Gmail Token Refresh")
    print("=" * 70)
    print()

    # Load existing credentials from .env
    env_path = Path(__file__).parent.parent / "config" / ".env"
    load_dotenv(env_path)

    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Gmail credentials not found in .env file")
        print(f"   Expected location: {env_path}")
        sys.exit(1)

    print(f"✅ Found existing credentials in .env")
    print(f"   Client ID: {client_id[:20]}...")
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

        # Run OAuth2 flow (opens browser)
        print("👉 Please login in the browser window that just opened...")
        creds = flow.run_local_server(port=0)

        print()
        print("✅ Authentication successful!")
        print()

        # Update .env file with new refresh token
        print("📝 Updating .env file with new refresh token...")
        update_env_file(env_path, creds.refresh_token)

        print()
        print("=" * 70)
        print("✅ Gmail token refreshed successfully!")
        print("=" * 70)
        print()
        print("You can now send emails. Try:")
        print("  python3 scripts/test_email.py --live")
        print()

    except Exception as e:
        print()
        print(f"❌ Failed to refresh token: {e}")
        sys.exit(1)


def update_env_file(env_path: Path, new_refresh_token: str) -> None:
    """Update .env file with new refresh token."""

    # Read existing .env file
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Update refresh token
    updated_lines = []
    token_updated = False

    for line in lines:
        if line.startswith('GMAIL_REFRESH_TOKEN='):
            updated_lines.append(f'GMAIL_REFRESH_TOKEN={new_refresh_token}\n')
            token_updated = True
        else:
            updated_lines.append(line)

    # Add token if not found
    if not token_updated:
        updated_lines.append(f'\nGMAIL_REFRESH_TOKEN={new_refresh_token}\n')

    # Write updated .env file
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    print(f"   ✅ Updated: {env_path}")


if __name__ == "__main__":
    refresh_gmail_token()

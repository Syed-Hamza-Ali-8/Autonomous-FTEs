#!/usr/bin/env python3
"""
Test Gmail API Connection

This script verifies that Gmail API credentials are working correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_credentials():
    """Load Gmail credentials from .env file."""
    env_path = Path(__file__).parent.parent / "config" / ".env"

    if not env_path.exists():
        print("❌ .env file not found!")
        return None

    # Read .env file
    credentials = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GMAIL_'):
                key, value = line.split('=', 1)
                credentials[key] = value

    # Check required credentials
    required = ['GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN']
    for key in required:
        if key not in credentials or not credentials[key]:
            print(f"❌ Missing credential: {key}")
            return None

    return credentials


def test_gmail_connection(credentials_dict):
    """Test Gmail API connection."""
    try:
        # Create credentials object
        creds = Credentials(
            token=None,
            refresh_token=credentials_dict['GMAIL_REFRESH_TOKEN'],
            token_uri='https://oauth2.googleapis.com/token',
            client_id=credentials_dict['GMAIL_CLIENT_ID'],
            client_secret=credentials_dict['GMAIL_CLIENT_SECRET']
        )

        # Refresh the token
        print("🔄 Refreshing access token...")
        creds.refresh(Request())
        print("✅ Access token refreshed successfully")

        # Build Gmail service
        print("🔌 Connecting to Gmail API...")
        service = build('gmail', 'v1', credentials=creds)

        # Test: Get user profile
        print("📧 Fetching Gmail profile...")
        profile = service.users().getProfile(userId='me').execute()

        print("\n" + "=" * 60)
        print("✅ Gmail API Connection Successful!")
        print("=" * 60)
        print(f"Email Address: {profile.get('emailAddress')}")
        print(f"Total Messages: {profile.get('messagesTotal', 0):,}")
        print(f"Total Threads: {profile.get('threadsTotal', 0):,}")
        print("=" * 60)

        # Test: List recent messages
        print("\n📬 Testing message retrieval...")
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            q='is:unread'
        ).execute()

        messages = results.get('messages', [])
        if messages:
            print(f"✅ Found {len(messages)} unread message(s)")
        else:
            print("ℹ️  No unread messages found")

        print("\n🎉 All Gmail API tests passed!")
        return True

    except HttpError as e:
        print(f"\n❌ Gmail API Error: {e}")
        if e.resp.status == 401:
            print("   → Authentication failed. Credentials may be invalid.")
        elif e.resp.status == 403:
            print("   → Access forbidden. Check API permissions.")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Gmail API Connection Test")
    print("=" * 60)
    print()

    # Load credentials
    print("📋 Loading credentials from .env file...")
    credentials = load_credentials()

    if not credentials:
        print("\n❌ Failed to load credentials")
        print("\nPlease run: python silver/scripts/setup_gmail.py")
        sys.exit(1)

    print("✅ Credentials loaded")
    print(f"   Client ID: {credentials['GMAIL_CLIENT_ID'][:20]}...")
    print(f"   Client Secret: {credentials['GMAIL_CLIENT_SECRET'][:15]}...")
    print(f"   Refresh Token: {credentials['GMAIL_REFRESH_TOKEN'][:20]}...")
    print()

    # Test connection
    success = test_gmail_connection(credentials)

    if success:
        print("\n✅ Gmail is ready to use!")
        print("\nNext steps:")
        print("   1. Set up WhatsApp: python silver/scripts/setup_whatsapp.py")
        print("   2. Start services: ./silver/scripts/startup.sh")
        sys.exit(0)
    else:
        print("\n❌ Gmail connection test failed")
        print("\nTroubleshooting:")
        print("   1. Re-run setup: python silver/scripts/setup_gmail.py")
        print("   2. Check credentials in silver/config/.env")
        print("   3. Verify Gmail API is enabled in Google Cloud Console")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Gmail OAuth2 Authentication Script

This script will:
1. Open a browser window for Google OAuth2 authentication
2. Generate a token.json file with your refresh token
3. Display the refresh token for you to add to .env
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate():
    """Run OAuth2 flow and save credentials."""
    creds = None

    # Check if token.json exists
    if os.path.exists('token.json'):
        print("Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Starting OAuth2 authentication flow...")
            print("\nMake sure you have credentials.json in this directory!")

            if not os.path.exists('credentials.json'):
                print("\n❌ ERROR: credentials.json not found!")
                print("Please download it from Google Cloud Console and place it in the backend/ folder")
                return

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)

            # Manual flow for WSL/headless
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f"\n🌐 Please go to this URL:\n{auth_url}\n")
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

        print("\n✅ Authentication successful!")
        print(f"✅ Saved credentials to token.json")

    # Display refresh token
    print("\n" + "="*60)
    print("📋 Your Gmail OAuth2 Credentials:")
    print("="*60)

    # Load token.json to get refresh token
    with open('token.json', 'r') as f:
        token_data = json.load(f)

    print(f"\nGMAIL_REFRESH_TOKEN={token_data.get('refresh_token', 'N/A')}")

    print("\n" + "="*60)
    print("📝 Next Steps:")
    print("="*60)
    print("1. Copy the GMAIL_REFRESH_TOKEN value above")
    print("2. Add it to your backend/.env file")
    print("3. Set JOBS_INBOX_EMAIL to the Gmail address you just authenticated")
    print("4. Set HIRING_MANAGER_EMAIL to where you want notifications sent")
    print("5. Set DRY_RUN=false when ready to send real emails")
    print("\n✅ Setup complete!")

if __name__ == '__main__':
    authenticate()

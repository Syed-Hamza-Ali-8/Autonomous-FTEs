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
import sys
import webbrowser

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
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...")
                creds.refresh(Request())
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                print("✅ Token refreshed!")
                return
        except Exception as e:
            print(f"Token invalid: {e}")
            os.remove('token.json')

    # Run OAuth flow
    print("Starting OAuth2 authentication flow...")
    print("\nMake sure you have credentials.json in this directory!")

    if not os.path.exists('credentials.json'):
        print("\n❌ ERROR: credentials.json not found!")
        print("Please download it from Google Cloud Console and place it in the backend/ folder")
        print("\nIMPORTANT: In Google Cloud Console, add 'http://localhost' to authorized redirect URIs!")
        return

    # Load credentials
    with open('credentials.json', 'r') as f:
        creds_data = json.load(f)

    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)

    # Use default redirect URI from credentials.json (http://localhost)
    auth_url = flow.authorization_url(prompt='consent', access_type='offline')[0]
    print(f"\n🌐 Opening browser for authorization...")
    print(f"Or copy this URL manually:\n{auth_url}\n")

    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print("Browser opened. If it didn't open, copy the URL above manually.")
    except:
        print("Could not open browser automatically. Please copy the URL above manually.")

    # Check if code was passed as argument
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        print("\n📋 After authorizing, you'll see a page with a code.")
        print("   Copy the code (it will look like: 4/0Adeu5B...)")
        code = input("Enter the authorization code from the browser: ")

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

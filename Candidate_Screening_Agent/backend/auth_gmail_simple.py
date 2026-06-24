#!/usr/bin/env python3
"""
Simple Gmail OAuth2 Authentication using OOB flow
"""

import json
import os
import sys
import requests

# Load credentials
with open('credentials.json', 'r') as f:
    creds_data = json.load(f)

client_id = creds_data['installed']['client_id']
client_secret = creds_data['installed']['client_secret']

# OAuth parameters
scopes = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Build the authorization URL using OOB
scope_str = ' '.join(scopes)
auth_url = (
    f"https://accounts.google.com/o/oauth2/auth"
    f"?client_id={client_id}"
    f"&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob"
    f"&scope={scope_str.replace(' ', '%20')}"
    f"&response_type=code"
    f"&prompt=consent"
    f"&access_type=offline"
)

print("="*60)
print("Gmail OAuth2 Authentication")
print("="*60)
print(f"\n🌐 Please go to this URL:\n{auth_url}\n")
print("="*60)

# Get the code from user
code = input("Enter the authorization code from the browser: ").strip()

# Exchange code for tokens
token_url = "https://oauth2.googleapis.com/token"
data = {
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "grant_type": "authorization_code"
}

print("\nExchanging code for tokens...")
response = requests.post(token_url, data=data)
token_data = response.json()

if 'error' in token_data:
    print(f"\n❌ Error: {token_data.get('error_description', token_data['error'])}")
    sys.exit(1)

# Save token.json
with open('token.json', 'w') as f:
    json.dump(token_data, f, indent=2)

print("\n✅ Authentication successful!")
print(f"✅ Saved credentials to token.json")

print("\n" + "="*60)
print("📋 Add this to your .env file:")
print("="*60)
print(f"\nGMAIL_REFRESH_TOKEN={token_data.get('refresh_token', 'N/A')}")
print("\n" + "="*60)

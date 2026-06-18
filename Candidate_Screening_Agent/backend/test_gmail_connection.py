"""Test Gmail OAuth2 connection with new credentials."""
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

def test_gmail_connection():
    """Test if Gmail API connection works with OAuth2 credentials."""
    print("=" * 70)
    print("🔍 Testing Gmail OAuth2 Connection")
    print("=" * 70)

    # Get credentials from environment
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    print(f"\n📋 Credentials loaded:")
    print(f"   Client ID: {client_id[:20]}...")
    print(f"   Client Secret: {client_secret[:10]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")

    try:
        # Create credentials object
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        print("\n🔄 Building Gmail service...")
        service = build("gmail", "v1", credentials=creds)

        print("✅ Gmail service built successfully")

        # Test by getting user profile
        print("\n📧 Testing API call (getting profile)...")
        profile = service.users().getProfile(userId="me").execute()

        print(f"✅ Successfully connected to Gmail!")
        print(f"   Email: {profile.get('emailAddress')}")
        print(f"   Messages Total: {profile.get('messagesTotal')}")
        print(f"   Threads Total: {profile.get('threadsTotal')}")

        # Test listing messages
        print("\n📬 Testing message listing...")
        results = service.users().messages().list(userId="me", maxResults=5).execute()
        messages = results.get("messages", [])

        print(f"✅ Successfully listed messages")
        print(f"   Found {len(messages)} recent messages")

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Gmail OAuth2 is working correctly!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n" + "=" * 70)
        print("❌ TEST FAILED - Gmail OAuth2 connection failed")
        print("=" * 70)
        return False

if __name__ == "__main__":
    test_gmail_connection()

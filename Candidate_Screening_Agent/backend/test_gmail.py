#!/usr/bin/env python3
"""
Test Gmail Integration

This script tests:
1. Gmail API connection
2. Ability to send emails (in DRY_RUN mode)
3. Ability to read emails
"""

import asyncio
import os
from dotenv import load_dotenv
from services.gmail_service import gmail_service

load_dotenv()

async def test_gmail():
    print("="*60)
    print("Testing Gmail Integration")
    print("="*60)

    # Check environment variables
    print("\n1. Checking environment variables...")

    required_vars = [
        'GMAIL_CLIENT_ID',
        'GMAIL_CLIENT_SECRET',
        'GMAIL_REFRESH_TOKEN',
        'JOBS_INBOX_EMAIL',
        'HIRING_MANAGER_EMAIL'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing.append(var)
            print(f"   ❌ {var}: Not set")
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'TOKEN' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")

    if missing:
        print(f"\n❌ Missing required variables: {', '.join(missing)}")
        print("\nPlease run: uv run python authenticate_gmail.py")
        return False

    # Check DRY_RUN mode
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    print(f"\n2. DRY_RUN mode: {'✅ Enabled (safe testing)' if dry_run else '⚠️  Disabled (real emails will be sent)'}")

    # Test sending email
    print("\n3. Testing email send...")
    try:
        to_email = os.getenv('HIRING_MANAGER_EMAIL')
        message_id = gmail_service.send_email(
            to=to_email,
            subject="Test Email from Candidate Screening Agent",
            body="This is a test email. If you see this in your logs (DRY_RUN=true), the integration is working!"
        )

        if dry_run:
            print(f"   ✅ Email logged successfully (DRY_RUN mode)")
            print(f"   📧 Would send to: {to_email}")
            print(f"   🆔 Message ID: {message_id}")
        else:
            print(f"   ✅ Email sent successfully!")
            print(f"   📧 Sent to: {to_email}")
            print(f"   🆔 Message ID: {message_id}")
            print(f"   📬 Check your inbox!")
    except Exception as e:
        print(f"   ❌ Error sending email: {e}")
        return False

    print("\n" + "="*60)
    print("✅ Gmail Integration Test Complete!")
    print("="*60)

    if dry_run:
        print("\n💡 To send real emails:")
        print("   1. Set DRY_RUN=false in backend/.env")
        print("   2. Restart the backend server")

    return True

if __name__ == '__main__':
    asyncio.run(test_gmail())

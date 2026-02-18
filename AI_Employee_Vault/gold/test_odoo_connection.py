#!/usr/bin/env python3
"""
Test Odoo Connection with Real Credentials
"""

import sys
from pathlib import Path

# Add MCP odoo directory to path
gold_dir = Path(__file__).parent
sys.path.insert(0, str(gold_dir / "mcp" / "odoo-mcp-python"))

from odoo_client import OdooClient
from dotenv import load_dotenv
import os

# Load environment variables from gold/.env
load_dotenv(gold_dir / ".env")

def test_connection():
    """Test connection to Odoo"""

    print("=" * 70)
    print("Testing Odoo Connection")
    print("=" * 70)
    print()

    # Get credentials from .env
    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")
    use_mock = os.getenv("USE_MOCK_ODOO", "true").lower() == "true"

    print(f"Odoo URL: {url}")
    print(f"Database: {db}")
    print(f"Username: {username}")
    print(f"Using Mock: {use_mock}")
    print()

    if use_mock:
        print("⚠️  WARNING: Still using mock data!")
        print("   Set USE_MOCK_ODOO=false in .env to use real Odoo")
        return False

    try:
        print("1. Creating Odoo client...")
        client = OdooClient(url, db, username, password)

        print("2. Authenticating...")
        uid = client.authenticate()
        print(f"   ✅ Authentication successful! User ID: {uid}")
        print()

        print("3. Testing API access - Fetching company info...")
        companies = client.call(
            'res.company',
            'search_read',
            args=[[]],
            kwargs={'fields': ['name', 'currency_id'], 'limit': 1}
        )

        if companies:
            company = companies[0]
            print(f"   ✅ Company: {company.get('name')}")
            print(f"   ✅ Currency: {company.get('currency_id', ['N/A'])[1] if company.get('currency_id') else 'N/A'}")
        print()

        print("4. Testing accounting data access...")
        # Try to fetch invoices
        invoices = client.call(
            'account.move',
            'search_read',
            args=[[('move_type', 'in', ['out_invoice', 'in_invoice'])]],
            kwargs={'fields': ['name', 'amount_total', 'state'], 'limit': 5}
        )

        print(f"   ✅ Found {len(invoices)} invoice(s) in your Odoo")
        if invoices:
            print("   Sample invoices:")
            for inv in invoices[:3]:
                print(f"      - {inv.get('name')}: ${inv.get('amount_total', 0):.2f} ({inv.get('state')})")
        else:
            print("   ℹ️  No invoices found (this is normal for a new account)")
        print()

        print("=" * 70)
        print("✅ CONNECTION TEST SUCCESSFUL!")
        print("=" * 70)
        print()
        print("Your Odoo is now connected to the AI Employee!")
        print()
        print("Next steps:")
        print("1. Add some sample data to your Odoo (invoices, expenses)")
        print("2. Generate CEO Briefing: python src/intelligence/ceo_briefing.py")
        print("3. Check Reports/CEO_Briefings/ for the report with real data")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ CONNECTION TEST FAILED")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Verify your Odoo URL is correct")
        print("2. Check your email and password")
        print("3. Make sure you can log into Odoo manually")
        print("4. Try accessing: " + url)
        print()

        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

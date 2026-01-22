#!/usr/bin/env python3
"""
Test script for Odoo JSON-RPC client
"""

import sys
from datetime import datetime, timedelta
from odoo_client import OdooClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Test Odoo client functionality"""
    print("=" * 60)
    print("Odoo JSON-RPC Client Test")
    print("=" * 60)

    try:
        # Initialize client
        print("\n1. Initializing Odoo client...")
        client = OdooClient(
            url=os.getenv("ODOO_URL", "http://localhost:8069"),
            db=os.getenv("ODOO_DB", "ai_employee_accounting"),
            username=os.getenv("ODOO_USERNAME", "api@aiemployee.local"),
            password=os.getenv("ODOO_PASSWORD", "")
        )
        print("   ✅ Client initialized")

        # Health check
        print("\n2. Testing connection (health check)...")
        health = client.health_check()
        if health["status"] == "healthy":
            print(f"   ✅ Connection successful")
            print(f"      Database: {health['database']}")
            print(f"      User ID: {health['uid']}")
            print(f"      URL: {health['url']}")
        else:
            print(f"   ❌ Connection failed: {health.get('error', 'Unknown error')}")
            sys.exit(1)

        # Get financial summary
        print("\n3. Testing financial summary...")
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        print(f"   Date range: {date_from} to {date_to}")
        summary = client.get_financial_summary(date_from, date_to)

        print(f"   ✅ Financial summary retrieved")
        print(f"      Revenue: ${summary['revenue']:,.2f}")
        print(f"      Expenses: ${summary['expenses']:,.2f}")
        print(f"      Profit: ${summary['profit']:,.2f}")
        print(f"      Profit Margin: {summary['profit_margin']:.1f}%")
        print(f"      Outstanding Invoices: {summary['outstanding_invoices']}")
        print(f"      Outstanding Amount: ${summary['outstanding_amount']:,.2f}")

        # Get outstanding invoices
        print("\n4. Testing outstanding invoices...")
        invoices = client.get_outstanding_invoices()
        print(f"   ✅ Found {len(invoices)} outstanding invoices")

        if invoices:
            print("   First 3 invoices:")
            for inv in invoices[:3]:
                partner_name = inv['partner_id'][1] if isinstance(inv['partner_id'], list) else "Unknown"
                print(f"      - {inv['name']}: ${inv['amount_residual']:,.2f} ({partner_name})")
        else:
            print("   (No outstanding invoices found)")

        # Get customers
        print("\n5. Testing customer list...")
        customers = client.get_customers(limit=5)
        print(f"   ✅ Found {len(customers)} customers (showing max 5)")

        if customers:
            for customer in customers:
                email = customer.get('email', 'N/A')
                print(f"      - {customer['name']} ({email})")
        else:
            print("   (No customers found)")

        # Get revenue
        print("\n6. Testing revenue calculation...")
        revenue = client.get_revenue(date_from, date_to)
        print(f"   ✅ Revenue: ${revenue:,.2f}")

        # Get expenses
        print("\n7. Testing expenses calculation...")
        expenses = client.get_expenses(date_from, date_to)
        print(f"   ✅ Expenses: ${expenses:,.2f}")

        # Get invoices with filters
        print("\n8. Testing invoice filters...")
        posted_invoices = client.get_invoices({"state": "posted", "limit": 5})
        print(f"   ✅ Found {len(posted_invoices)} posted invoices (max 5)")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

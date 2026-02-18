#!/usr/bin/env python3
"""
Test fetching real accounting data from Odoo using XML-RPC
"""

import sys
from pathlib import Path
import xmlrpc.client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

gold_dir = Path(__file__).parent
load_dotenv(gold_dir / ".env")

def fetch_accounting_data():
    """Fetch real accounting data from Odoo"""

    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")

    print("=" * 70)
    print("Fetching Real Accounting Data from Odoo")
    print("=" * 70)
    print()

    try:
        # Authenticate
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("❌ Authentication failed")
            return

        print(f"✅ Authenticated as User ID: {uid}")
        print()

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # 1. Company Information
        print("1. Company Information:")
        companies = models.execute_kw(
            db, uid, password,
            'res.company', 'search_read',
            [[]],
            {'fields': ['name', 'currency_id', 'email', 'phone'], 'limit': 1}
        )

        if companies:
            company = companies[0]
            print(f"   Company: {company.get('name')}")
            print(f"   Currency: {company.get('currency_id', ['N/A'])[1] if company.get('currency_id') else 'N/A'}")
            print(f"   Email: {company.get('email', 'N/A')}")
            print(f"   Phone: {company.get('phone', 'N/A')}")
        print()

        # 2. Invoices
        print("2. Customer Invoices (Revenue):")
        invoices = models.execute_kw(
            db, uid, password,
            'account.move', 'search_read',
            [[('move_type', '=', 'out_invoice')]],
            {'fields': ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'], 'limit': 10}
        )

        print(f"   Found {len(invoices)} invoice(s)")
        if invoices:
            total_revenue = sum(inv.get('amount_total', 0) for inv in invoices)
            print(f"   Total Revenue: ${total_revenue:,.2f}")
            print()
            print("   Recent invoices:")
            for inv in invoices[:5]:
                partner = inv.get('partner_id', ['Unknown'])[1] if inv.get('partner_id') else 'Unknown'
                print(f"      - {inv.get('name')}: ${inv.get('amount_total', 0):,.2f} ({inv.get('state')}) - {partner}")
        else:
            print("   ℹ️  No invoices found (new account)")
        print()

        # 3. Bills (Expenses)
        print("3. Vendor Bills (Expenses):")
        bills = models.execute_kw(
            db, uid, password,
            'account.move', 'search_read',
            [[('move_type', '=', 'in_invoice')]],
            {'fields': ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'], 'limit': 10}
        )

        print(f"   Found {len(bills)} bill(s)")
        if bills:
            total_expenses = sum(bill.get('amount_total', 0) for bill in bills)
            print(f"   Total Expenses: ${total_expenses:,.2f}")
            print()
            print("   Recent bills:")
            for bill in bills[:5]:
                partner = bill.get('partner_id', ['Unknown'])[1] if bill.get('partner_id') else 'Unknown'
                print(f"      - {bill.get('name')}: ${bill.get('amount_total', 0):,.2f} ({bill.get('state')}) - {partner}")
        else:
            print("   ℹ️  No bills found (new account)")
        print()

        # 4. Bank Accounts
        print("4. Bank Accounts:")
        bank_accounts = models.execute_kw(
            db, uid, password,
            'account.journal', 'search_read',
            [[('type', '=', 'bank')]],
            {'fields': ['name', 'currency_id', 'bank_account_id'], 'limit': 5}
        )

        print(f"   Found {len(bank_accounts)} bank account(s)")
        for acc in bank_accounts:
            print(f"      - {acc.get('name')}")
        print()

        # 5. Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()

        if invoices or bills:
            print("✅ Your Odoo has accounting data!")
            print()
            print(f"   Revenue: ${total_revenue:,.2f}" if invoices else "   Revenue: $0.00 (no invoices)")
            print(f"   Expenses: ${total_expenses:,.2f}" if bills else "   Expenses: $0.00 (no bills)")

            if invoices and bills:
                profit = total_revenue - total_expenses
                print(f"   Profit: ${profit:,.2f}")
            print()
            print("✅ Ready to generate CEO Briefing with REAL data!")
        else:
            print("ℹ️  Your Odoo account is empty (no transactions yet)")
            print()
            print("Options:")
            print("1. Add sample data to Odoo manually")
            print("2. Use mock data for CEO Briefing (USE_MOCK_ODOO=true)")
            print("3. Wait until you have real transactions")
        print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fetch_accounting_data()

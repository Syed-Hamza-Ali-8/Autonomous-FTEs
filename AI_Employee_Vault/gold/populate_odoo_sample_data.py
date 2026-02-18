#!/usr/bin/env python3
"""
Populate Odoo with Sample Accounting Data
Creates realistic sample invoices, bills, customers, and vendors
"""

import sys
from pathlib import Path
import xmlrpc.client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random

gold_dir = Path(__file__).parent
load_dotenv(gold_dir / ".env")

def populate_sample_data():
    """Populate Odoo with sample accounting data"""

    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")

    print("=" * 70)
    print("Populating Odoo with Sample Accounting Data")
    print("=" * 70)
    print()

    try:
        # Authenticate
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("❌ Authentication failed")
            return False

        print(f"✅ Authenticated as User ID: {uid}")
        print()

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Sample data
        customers = [
            {"name": "Tech Solutions Ltd", "email": "contact@techsolutions.pk", "phone": "+92-300-1234567"},
            {"name": "Digital Marketing Co", "email": "info@digitalmarketing.pk", "phone": "+92-321-9876543"},
            {"name": "E-Commerce Ventures", "email": "sales@ecommerce.pk", "phone": "+92-333-5555555"},
            {"name": "Software House Pvt", "email": "admin@softwarehouse.pk", "phone": "+92-300-7777777"},
            {"name": "Consulting Group", "email": "contact@consulting.pk", "phone": "+92-321-8888888"},
        ]

        vendors = [
            {"name": "Cloud Services Provider", "email": "billing@cloudservices.com", "phone": "+1-555-0100"},
            {"name": "Office Supplies Co", "email": "sales@officesupplies.pk", "phone": "+92-300-2222222"},
            {"name": "Internet Service Provider", "email": "support@isp.pk", "phone": "+92-321-3333333"},
        ]

        # 1. Create Customers
        print("1. Creating sample customers...")
        customer_ids = []
        for customer in customers:
            try:
                customer_id = models.execute_kw(
                    db, uid, password,
                    'res.partner', 'create',
                    [{
                        'name': customer['name'],
                        'email': customer['email'],
                        'phone': customer['phone'],
                        'customer_rank': 1,
                        'is_company': True,
                    }]
                )
                customer_ids.append(customer_id)
                print(f"   ✅ Created: {customer['name']}")
            except Exception as e:
                print(f"   ⚠️  Skipped {customer['name']}: {e}")

        print(f"   Created {len(customer_ids)} customers")
        print()

        # 2. Create Vendors
        print("2. Creating sample vendors...")
        vendor_ids = []
        for vendor in vendors:
            try:
                vendor_id = models.execute_kw(
                    db, uid, password,
                    'res.partner', 'create',
                    [{
                        'name': vendor['name'],
                        'email': vendor['email'],
                        'phone': vendor['phone'],
                        'supplier_rank': 1,
                        'is_company': True,
                    }]
                )
                vendor_ids.append(vendor_id)
                print(f"   ✅ Created: {vendor['name']}")
            except Exception as e:
                print(f"   ⚠️  Skipped {vendor['name']}: {e}")

        print(f"   Created {len(vendor_ids)} vendors")
        print()

        # 3. Create Customer Invoices (Revenue)
        print("3. Creating customer invoices (revenue)...")
        invoice_amounts = [
            150000,  # PKR 150,000 (~$535)
            250000,  # PKR 250,000 (~$890)
            180000,  # PKR 180,000 (~$640)
            320000,  # PKR 320,000 (~$1,140)
            95000,   # PKR 95,000 (~$340)
            420000,  # PKR 420,000 (~$1,500)
            175000,  # PKR 175,000 (~$625)
            280000,  # PKR 280,000 (~$1,000)
        ]

        invoice_descriptions = [
            "AI Automation Consulting Services",
            "Custom Software Development",
            "Digital Marketing Campaign",
            "Website Development & Hosting",
            "Business Process Automation",
            "Mobile App Development",
            "SEO & Content Marketing",
            "Cloud Infrastructure Setup",
        ]

        created_invoices = 0
        total_revenue = 0

        for i, (amount, description) in enumerate(zip(invoice_amounts, invoice_descriptions)):
            if i >= len(customer_ids):
                break

            try:
                # Create invoice date (last 30 days)
                days_ago = random.randint(1, 30)
                invoice_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

                invoice_id = models.execute_kw(
                    db, uid, password,
                    'account.move', 'create',
                    [{
                        'move_type': 'out_invoice',
                        'partner_id': customer_ids[i % len(customer_ids)],
                        'invoice_date': invoice_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': description,
                            'quantity': 1,
                            'price_unit': amount,
                        })],
                    }]
                )

                # Post the invoice (make it official)
                models.execute_kw(
                    db, uid, password,
                    'account.move', 'action_post',
                    [[invoice_id]]
                )

                created_invoices += 1
                total_revenue += amount
                print(f"   ✅ Invoice {i+1}: PKR {amount:,} - {description}")

            except Exception as e:
                print(f"   ⚠️  Failed to create invoice {i+1}: {e}")

        print(f"   Created {created_invoices} invoices")
        print(f"   Total Revenue: PKR {total_revenue:,}")
        print()

        # 4. Create Vendor Bills (Expenses)
        print("4. Creating vendor bills (expenses)...")
        bill_amounts = [
            25000,   # PKR 25,000 - Cloud hosting
            15000,   # PKR 15,000 - Office supplies
            8000,    # PKR 8,000 - Internet
            35000,   # PKR 35,000 - Software licenses
            12000,   # PKR 12,000 - Marketing tools
        ]

        bill_descriptions = [
            "Cloud Hosting Services - Monthly",
            "Office Supplies & Equipment",
            "Internet Service - Monthly",
            "Software Licenses & Tools",
            "Marketing & Advertising Tools",
        ]

        created_bills = 0
        total_expenses = 0

        for i, (amount, description) in enumerate(zip(bill_amounts, bill_descriptions)):
            if i >= len(vendor_ids):
                vendor_id = vendor_ids[i % len(vendor_ids)]
            else:
                vendor_id = vendor_ids[i]

            try:
                # Create bill date (last 30 days)
                days_ago = random.randint(1, 30)
                bill_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

                bill_id = models.execute_kw(
                    db, uid, password,
                    'account.move', 'create',
                    [{
                        'move_type': 'in_invoice',
                        'partner_id': vendor_id,
                        'invoice_date': bill_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': description,
                            'quantity': 1,
                            'price_unit': amount,
                        })],
                    }]
                )

                # Post the bill
                models.execute_kw(
                    db, uid, password,
                    'account.move', 'action_post',
                    [[bill_id]]
                )

                created_bills += 1
                total_expenses += amount
                print(f"   ✅ Bill {i+1}: PKR {amount:,} - {description}")

            except Exception as e:
                print(f"   ⚠️  Failed to create bill {i+1}: {e}")

        print(f"   Created {created_bills} bills")
        print(f"   Total Expenses: PKR {total_expenses:,}")
        print()

        # 5. Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()
        print(f"✅ Sample data created successfully!")
        print()
        print(f"   Customers: {len(customer_ids)}")
        print(f"   Vendors: {len(vendor_ids)}")
        print(f"   Invoices: {created_invoices}")
        print(f"   Bills: {created_bills}")
        print()
        print(f"   Total Revenue: PKR {total_revenue:,} (~${total_revenue/280:.2f} USD)")
        print(f"   Total Expenses: PKR {total_expenses:,} (~${total_expenses/280:.2f} USD)")
        print(f"   Profit: PKR {total_revenue - total_expenses:,} (~${(total_revenue - total_expenses)/280:.2f} USD)")
        print()
        print("=" * 70)
        print("NEXT STEP: Generate CEO Briefing")
        print("=" * 70)
        print()
        print("Your Odoo now has real accounting data!")
        print()
        print("Run: python src/intelligence/ceo_briefing.py")
        print("Or: I'll generate it for you automatically")
        print()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_sample_data()
    sys.exit(0 if success else 1)

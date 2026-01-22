"""
Mock Odoo API

Mock implementation of Odoo API for development without real Odoo account.
Implements AccountingInterface with realistic mock data.

Gold Tier Requirement #3: Odoo Accounting Integration (Mock for Phase 1-3)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from ..interfaces.accounting_interface import AccountingInterface


class MockOdooAPI(AccountingInterface):
    """
    Mock Odoo API for development.

    Provides realistic mock data for testing without a real Odoo account.
    Will be replaced with real OdooAPI in Phase 4.

    Usage:
        odoo = MockOdooAPI()
        invoices = odoo.get_invoices(status="PAID")
    """

    def __init__(self):
        self._mock_invoices = self._generate_mock_invoices()
        self._mock_transactions = self._generate_mock_transactions()
        self._mock_contacts = self._generate_mock_contacts()

    def _generate_mock_invoices(self) -> List[Dict[str, Any]]:
        """Generate realistic mock invoices"""
        return [
            {
                "invoice_id": "INV-2026-001",
                "invoice_number": "INV-2026-001",
                "contact": "Client A",
                "contact_id": "contact_001",
                "date": "2026-01-15",
                "due_date": "2026-01-30",
                "status": "PAID",
                "total": 1500.00,
                "amount_due": 0.00,
                "amount_paid": 1500.00,
                "currency": "USD",
                "paid_date": "2026-01-15",
                "line_items": [
                    {
                        "description": "Consulting services - January 2026",
                        "quantity": 10,
                        "unit_amount": 150.00,
                        "line_amount": 1500.00
                    }
                ]
            },
            {
                "invoice_id": "INV-2026-002",
                "invoice_number": "INV-2026-002",
                "contact": "Client B",
                "contact_id": "contact_002",
                "date": "2026-01-10",
                "due_date": "2026-01-25",
                "status": "AUTHORISED",
                "total": 2000.00,
                "amount_due": 2000.00,
                "amount_paid": 0.00,
                "currency": "USD",
                "line_items": [
                    {
                        "description": "Project Alpha - Phase 2",
                        "quantity": 1,
                        "unit_amount": 2000.00,
                        "line_amount": 2000.00
                    }
                ]
            },
            {
                "invoice_id": "INV-2026-003",
                "invoice_number": "INV-2026-003",
                "contact": "Client C",
                "contact_id": "contact_003",
                "date": "2026-01-08",
                "due_date": "2026-02-08",
                "status": "AUTHORISED",
                "total": 1500.00,
                "amount_due": 1500.00,
                "amount_paid": 0.00,
                "currency": "USD",
                "line_items": [
                    {
                        "description": "Monthly retainer - January 2026",
                        "quantity": 1,
                        "unit_amount": 1500.00,
                        "line_amount": 1500.00
                    }
                ]
            }
        ]

    def _generate_mock_transactions(self) -> List[Dict[str, Any]]:
        """Generate realistic mock transactions"""
        return [
            {
                "transaction_id": "tx_001",
                "date": "2026-01-10",
                "amount": -15.00,
                "currency": "USD",
                "category": "expense",
                "subcategory": "software_subscription",
                "description": "Notion subscription - Monthly",
                "vendor": "Notion Labs Inc",
                "business_related": True,
                "tax_deductible": True
            },
            {
                "transaction_id": "tx_002",
                "date": "2026-01-15",
                "amount": 1500.00,
                "currency": "USD",
                "category": "income",
                "subcategory": "consulting",
                "description": "Payment from Client A - INV-2026-001",
                "vendor": "Client A",
                "business_related": True,
                "tax_deductible": False
            },
            {
                "transaction_id": "tx_003",
                "date": "2026-01-12",
                "amount": -50.00,
                "currency": "USD",
                "category": "expense",
                "subcategory": "office_supplies",
                "description": "Office supplies - Amazon",
                "vendor": "Amazon",
                "business_related": True,
                "tax_deductible": True
            },
            {
                "transaction_id": "tx_004",
                "date": "2026-01-14",
                "amount": -16.00,
                "currency": "USD",
                "category": "expense",
                "subcategory": "software_subscription",
                "description": "Slack Premium - Monthly",
                "vendor": "Slack Technologies",
                "business_related": True,
                "tax_deductible": True
            },
            {
                "transaction_id": "tx_005",
                "date": "2026-01-08",
                "amount": 950.00,
                "currency": "USD",
                "category": "income",
                "subcategory": "consulting",
                "description": "Payment from Client D - Project Beta",
                "vendor": "Client D",
                "business_related": True,
                "tax_deductible": False
            }
        ]

    def _generate_mock_contacts(self) -> List[Dict[str, Any]]:
        """Generate realistic mock contacts"""
        return [
            {
                "contact_id": "contact_001",
                "name": "Client A",
                "email": "client-a@example.com",
                "type": "CUSTOMER",
                "balance": 0.00
            },
            {
                "contact_id": "contact_002",
                "name": "Client B",
                "email": "client-b@example.com",
                "type": "CUSTOMER",
                "balance": 2000.00
            },
            {
                "contact_id": "contact_003",
                "name": "Client C",
                "email": "client-c@example.com",
                "type": "CUSTOMER",
                "balance": 1500.00
            },
            {
                "contact_id": "contact_004",
                "name": "Notion Labs Inc",
                "email": "billing@notion.so",
                "type": "SUPPLIER",
                "balance": 0.00
            }
        ]

    def get_invoices(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contact_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get mock invoices with optional filters"""
        invoices = self._mock_invoices.copy()

        # Apply filters
        if status:
            invoices = [inv for inv in invoices if inv["status"] == status]
        if contact_id:
            invoices = [inv for inv in invoices if inv["contact_id"] == contact_id]
        if start_date:
            invoices = [inv for inv in invoices if inv["date"] >= start_date]
        if end_date:
            invoices = [inv for inv in invoices if inv["date"] <= end_date]

        return invoices

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get mock transactions with optional filters"""
        transactions = self._mock_transactions.copy()

        # Apply filters
        if transaction_type:
            transactions = [tx for tx in transactions if tx["category"] == transaction_type]
        if start_date:
            transactions = [tx for tx in transactions if tx["date"] >= start_date]
        if end_date:
            transactions = [tx for tx in transactions if tx["date"] <= end_date]

        return transactions

    def get_contacts(
        self,
        contact_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get mock contacts with optional filters"""
        contacts = self._mock_contacts.copy()

        # Apply filters
        if contact_type and contact_type != "ALL":
            contacts = [c for c in contacts if c["type"] == contact_type]
        if search:
            search_lower = search.lower()
            contacts = [
                c for c in contacts
                if search_lower in c["name"].lower() or search_lower in c["email"].lower()
            ]

        return contacts

    def get_profit_and_loss(
        self,
        start_date: str,
        end_date: str,
        periods: int = 1
    ) -> Dict[str, Any]:
        """Get mock P&L report"""
        # Calculate from mock transactions
        transactions = self.get_transactions(start_date, end_date)

        revenue = sum(tx["amount"] for tx in transactions if tx["category"] == "income")
        expenses = abs(sum(tx["amount"] for tx in transactions if tx["category"] == "expense"))
        net_profit = revenue - expenses

        return {
            "report_type": "ProfitAndLoss",
            "period": f"{start_date} to {end_date}",
            "revenue": revenue,
            "expenses": expenses,
            "net_profit": net_profit,
            "sections": [
                {
                    "title": "Revenue",
                    "total": revenue,
                    "rows": [
                        {
                            "account": "Consulting Income",
                            "amount": revenue
                        }
                    ]
                },
                {
                    "title": "Expenses",
                    "total": expenses,
                    "rows": [
                        {
                            "account": "Software Subscriptions",
                            "amount": 31.00
                        },
                        {
                            "account": "Office Supplies",
                            "amount": 50.00
                        }
                    ]
                }
            ]
        }

    def get_balance_sheet(self, date: str) -> Dict[str, Any]:
        """Get mock balance sheet"""
        return {
            "report_type": "BalanceSheet",
            "date": date,
            "assets": {
                "current_assets": {
                    "cash": 5000.00,
                    "accounts_receivable": 3500.00,
                    "total": 8500.00
                },
                "total": 8500.00
            },
            "liabilities": {
                "current_liabilities": {
                    "accounts_payable": 500.00,
                    "total": 500.00
                },
                "total": 500.00
            },
            "equity": {
                "retained_earnings": 8000.00,
                "total": 8000.00
            }
        }

    def get_cash_flow(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get mock cash flow report"""
        return {
            "report_type": "CashFlow",
            "period": f"{start_date} to {end_date}",
            "operating_activities": {
                "cash_received": 2450.00,
                "cash_paid": -81.00,
                "net": 2369.00
            },
            "investing_activities": {
                "net": 0.00
            },
            "financing_activities": {
                "net": 0.00
            },
            "net_cash_flow": 2369.00
        }

    def create_invoice(
        self,
        contact: str,
        date: str,
        due_date: str,
        line_items: List[Dict[str, Any]],
        reference: Optional[str] = None,
        status: str = "DRAFT"
    ) -> Dict[str, Any]:
        """Create mock invoice"""
        invoice_number = f"INV-2026-{len(self._mock_invoices) + 1:03d}"
        total = sum(item["line_amount"] for item in line_items)

        invoice = {
            "invoice_id": invoice_number,
            "invoice_number": invoice_number,
            "contact": contact,
            "contact_id": f"contact_{len(self._mock_contacts) + 1:03d}",
            "date": date,
            "due_date": due_date,
            "status": status,
            "total": total,
            "amount_due": total if status != "PAID" else 0.00,
            "amount_paid": 0.00 if status != "PAID" else total,
            "currency": "USD",
            "line_items": line_items,
            "reference": reference
        }

        self._mock_invoices.append(invoice)
        return invoice

    def update_invoice(
        self,
        invoice_id: str,
        status: Optional[str] = None,
        payment_date: Optional[str] = None,
        payment_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update mock invoice"""
        for invoice in self._mock_invoices:
            if invoice["invoice_id"] == invoice_id:
                if status:
                    invoice["status"] = status
                if payment_date:
                    invoice["paid_date"] = payment_date
                if payment_amount:
                    invoice["amount_paid"] = payment_amount
                    invoice["amount_due"] = invoice["total"] - payment_amount
                return invoice

        raise ValueError(f"Invoice not found: {invoice_id}")

    def categorize_transaction(
        self,
        description: str,
        vendor: str,
        amount: float
    ) -> Dict[str, Any]:
        """Mock transaction categorization"""
        # Simple keyword-based categorization
        description_lower = description.lower()
        vendor_lower = vendor.lower()

        if any(keyword in description_lower for keyword in ["notion", "slack", "software", "subscription"]):
            category = "expense"
            subcategory = "software_subscription"
            business_related = True
            tax_deductible = True
        elif any(keyword in description_lower for keyword in ["office", "supplies", "equipment"]):
            category = "expense"
            subcategory = "office_supplies"
            business_related = True
            tax_deductible = True
        elif amount > 0:
            category = "income"
            subcategory = "consulting"
            business_related = True
            tax_deductible = False
        else:
            category = "expense"
            subcategory = "other"
            business_related = False
            tax_deductible = False

        return {
            "category": category,
            "subcategory": subcategory,
            "business_related": business_related,
            "tax_deductible": tax_deductible,
            "confidence": 0.85,
            "reasoning": f"Categorized based on keywords in description and vendor"
        }

    def sync_transactions(
        self,
        since: Optional[str] = None,
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """Mock transaction sync"""
        transactions = self.get_transactions(start_date=since)

        if auto_categorize:
            for tx in transactions:
                if "category" not in tx or not tx["category"]:
                    categorization = self.categorize_transaction(
                        tx["description"],
                        tx["vendor"],
                        tx["amount"]
                    )
                    tx.update(categorization)

        return {
            "synced": len(transactions),
            "categorized": len(transactions) if auto_categorize else 0,
            "errors": 0,
            "files_created": [f"/Vault/Accounting/Transactions/{tx['transaction_id']}.md" for tx in transactions]
        }

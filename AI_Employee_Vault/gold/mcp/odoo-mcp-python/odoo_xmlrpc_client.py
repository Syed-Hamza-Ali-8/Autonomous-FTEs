"""
XML-RPC Odoo Client Wrapper
Works with Odoo Cloud instances that require XML-RPC instead of JSON-RPC
"""

import xmlrpc.client
from typing import Dict, List, Any
from datetime import datetime


class OdooXMLRPCClient:
    """Odoo client using XML-RPC (works with Odoo Cloud)"""

    def __init__(self, url: str, db: str, username: str, password: str):
        """Initialize Odoo XML-RPC client"""
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        self.common = None

    def authenticate(self):
        """Authenticate with Odoo"""
        if self.uid:
            return self.uid

        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise Exception("Authentication failed")

        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        return self.uid

    def get_financial_summary(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get financial summary for period"""
        if not self.uid:
            self.authenticate()

        # Get customer invoices (revenue)
        invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<=', date_to),
                ('state', '=', 'posted')
            ]],
            {'fields': ['amount_total', 'payment_state']}
        )

        # Get vendor bills (expenses)
        bills = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [[
                ('move_type', '=', 'in_invoice'),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<=', date_to),
                ('state', '=', 'posted')
            ]],
            {'fields': ['amount_total']}
        )

        # Calculate totals
        revenue = sum(inv.get('amount_total', 0) for inv in invoices)
        expenses = sum(bill.get('amount_total', 0) for bill in bills)
        profit = revenue - expenses
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0

        # Outstanding invoices (not paid)
        outstanding_invoices = [inv for inv in invoices if inv.get('payment_state') != 'paid']
        outstanding_amount = sum(inv.get('amount_total', 0) for inv in outstanding_invoices)

        return {
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "profit_margin": profit_margin,
            "outstanding_invoices": len(outstanding_invoices),
            "outstanding_amount": outstanding_amount,
            "date_from": date_from,
            "date_to": date_to
        }

    def get_invoices(self, filters: Dict = None) -> List[Dict[str, Any]]:
        """Get invoices with optional filters"""
        if not self.uid:
            self.authenticate()

        domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]

        if filters:
            if 'date_from' in filters:
                domain.append(('invoice_date', '>=', filters['date_from']))
            if 'date_to' in filters:
                domain.append(('invoice_date', '<=', filters['date_to']))

        invoices = self.models.execute_kw(
            self.db, self.uid, self.password,
            'account.move', 'search_read',
            [domain],
            {'fields': ['name', 'amount_total', 'payment_state', 'partner_id', 'invoice_date']}
        )

        return invoices

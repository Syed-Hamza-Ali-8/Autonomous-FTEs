"""
Odoo JSON-RPC Client
Implements Odoo 19+ External API using JSON-RPC
"""

import requests
import json
from typing import Dict, List, Optional, Any
import random


class OdooClient:
    """Client for Odoo JSON-RPC API"""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize Odoo client

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            db: Database name
            username: Username for authentication
            password: Password for authentication
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.session_id = None
        self.cookies = {}

    def authenticate(self) -> int:
        """
        Authenticate with Odoo and get user ID

        Returns:
            User ID (uid)

        Raises:
            Exception: If authentication fails
        """
        try:
            response = requests.post(
                f"{self.url}/web/session/authenticate",
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "db": self.db,
                        "login": self.username,
                        "password": self.password
                    },
                    "id": random.randint(1, 1000000)
                },
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"Authentication failed: {data['error'].get('message', 'Unknown error')}")

            result = data.get("result", {})
            self.uid = result.get("uid")
            self.session_id = result.get("session_id")

            # Store session cookies
            if response.cookies:
                self.cookies = dict(response.cookies)

            if not self.uid:
                raise Exception("Authentication failed: No UID returned")

            return self.uid

        except requests.RequestException as e:
            raise Exception(f"Odoo authentication error: {str(e)}")

    def call(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
        """
        Call Odoo model method via JSON-RPC

        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method name (e.g., 'search_read')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result

        Raises:
            Exception: If call fails
        """
        if not self.uid:
            self.authenticate()

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        try:
            response = requests.post(
                f"{self.url}/web/dataset/call_kw",
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "model": model,
                        "method": method,
                        "args": args,
                        "kwargs": kwargs
                    },
                    "id": random.randint(1, 1000000)
                },
                headers={"Content-Type": "application/json"},
                cookies=self.cookies
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                # Retry authentication once if session expired
                if "session" in error_msg.lower() or "authentication" in error_msg.lower():
                    self.uid = None
                    self.authenticate()
                    return self.call(model, method, args, kwargs)
                raise Exception(f"Odoo API error: {error_msg}")

            return data.get("result")

        except requests.RequestException as e:
            raise Exception(f"Odoo API call error: {str(e)}")

    def search_read(self, model: str, domain: List = None, fields: List = None,
                    limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        Search and read records

        Args:
            model: Odoo model name
            domain: Search domain (list of tuples)
            fields: Fields to read
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of record dictionaries
        """
        if domain is None:
            domain = []
        if fields is None:
            fields = []

        kwargs = {"fields": fields, "offset": offset}
        if limit is not None:
            kwargs["limit"] = limit

        return self.call(model, "search_read", [domain], kwargs)

    def get_invoices(self, filters: Dict = None) -> List[Dict]:
        """
        Get invoices with optional filters

        Args:
            filters: Dictionary with filter options:
                - state: Invoice state (draft, posted, cancel)
                - payment_state: Payment state (not_paid, in_payment, paid, partial)
                - date_from: Start date (YYYY-MM-DD)
                - date_to: End date (YYYY-MM-DD)
                - partner_id: Customer ID
                - limit: Maximum number of invoices

        Returns:
            List of invoice dictionaries
        """
        if filters is None:
            filters = {}

        domain = []

        # Filter by state
        if "state" in filters:
            domain.append(["state", "=", filters["state"]])

        # Filter by payment state
        if "payment_state" in filters:
            domain.append(["payment_state", "=", filters["payment_state"]])

        # Filter by date range
        if "date_from" in filters:
            domain.append(["invoice_date", ">=", filters["date_from"]])
        if "date_to" in filters:
            domain.append(["invoice_date", "<=", filters["date_to"]])

        # Filter by customer
        if "partner_id" in filters:
            domain.append(["partner_id", "=", filters["partner_id"]])

        fields = [
            "name", "partner_id", "invoice_date", "invoice_date_due",
            "amount_total", "amount_residual", "state", "payment_state",
            "currency_id", "invoice_line_ids"
        ]

        return self.search_read("account.move", domain, fields, filters.get("limit"))

    def get_outstanding_invoices(self) -> List[Dict]:
        """
        Get outstanding invoices (posted but not fully paid)

        Returns:
            List of outstanding invoice dictionaries
        """
        domain = [
            ["state", "=", "posted"],
            ["payment_state", "in", ["not_paid", "partial"]]
        ]

        fields = [
            "name", "partner_id", "invoice_date", "invoice_date_due",
            "amount_total", "amount_residual", "payment_state"
        ]

        return self.search_read("account.move", domain, fields)

    def get_account_move_lines(self, date_from: str, date_to: str,
                               account_types: List[str] = None) -> List[Dict]:
        """
        Get account move lines (journal entries) for financial analysis

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            account_types: List of account types to filter (e.g., ['income', 'expense'])

        Returns:
            List of account move line dictionaries
        """
        domain = [
            ["date", ">=", date_from],
            ["date", "<=", date_to]
        ]

        if account_types:
            domain.append(["account_id.user_type_id.type", "in", account_types])

        fields = [
            "date", "name", "account_id", "partner_id", "debit", "credit",
            "balance", "move_id", "journal_id"
        ]

        return self.search_read("account.move.line", domain, fields)

    def get_revenue(self, date_from: str, date_to: str) -> float:
        """
        Get revenue for a date range

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Total revenue amount
        """
        # Revenue accounts typically have type 'income'
        lines = self.get_account_move_lines(date_from, date_to, ["income"])

        # Sum credit amounts (revenue increases credit)
        revenue = sum(line.get("credit", 0) for line in lines)

        return revenue

    def get_expenses(self, date_from: str, date_to: str) -> float:
        """
        Get expenses for a date range

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Total expenses amount
        """
        # Expense accounts typically have type 'expense'
        lines = self.get_account_move_lines(date_from, date_to, ["expense"])

        # Sum debit amounts (expenses increase debit)
        expenses = sum(line.get("debit", 0) for line in lines)

        return expenses

    def get_financial_summary(self, date_from: str, date_to: str) -> Dict:
        """
        Get financial summary for a date range

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Dictionary with financial summary:
                - revenue: Total revenue
                - expenses: Total expenses
                - profit: Net profit
                - profit_margin: Profit margin percentage
                - outstanding_invoices: Number of outstanding invoices
                - outstanding_amount: Total outstanding amount
                - date_from: Start date
                - date_to: End date
        """
        # Get all data in parallel (simulated with sequential calls)
        revenue = self.get_revenue(date_from, date_to)
        expenses = self.get_expenses(date_from, date_to)
        outstanding_invoices = self.get_outstanding_invoices()

        profit = revenue - expenses
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        total_outstanding = sum(inv.get("amount_residual", 0) for inv in outstanding_invoices)

        return {
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "profit_margin": profit_margin,
            "outstanding_invoices": len(outstanding_invoices),
            "outstanding_amount": total_outstanding,
            "date_from": date_from,
            "date_to": date_to
        }

    def get_customers(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get customers (partners)

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of customer dictionaries
        """
        domain = [["customer_rank", ">", 0]]
        fields = ["name", "email", "phone", "country_id", "vat"]

        return self.search_read("res.partner", domain, fields, limit)

    def health_check(self) -> Dict:
        """
        Health check - verify connection and authentication

        Returns:
            Dictionary with health status:
                - status: 'healthy' or 'unhealthy'
                - uid: User ID (if healthy)
                - database: Database name (if healthy)
                - url: Server URL (if healthy)
                - error: Error message (if unhealthy)
        """
        try:
            self.authenticate()
            return {
                "status": "healthy",
                "uid": self.uid,
                "database": self.db,
                "url": self.url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

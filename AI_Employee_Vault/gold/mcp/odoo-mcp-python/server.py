#!/usr/bin/env python3
"""
Odoo MCP Server
Exposes Odoo accounting data via Model Context Protocol
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from odoo_client import OdooClient

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("odoo")

# Initialize Odoo client
odoo = OdooClient(
    url=os.getenv("ODOO_URL", "http://localhost:8069"),
    db=os.getenv("ODOO_DB", "ai_employee_accounting"),
    username=os.getenv("ODOO_USERNAME", "api@aiemployee.local"),
    password=os.getenv("ODOO_PASSWORD", "")
)


@mcp.tool()
async def get_financial_summary(date_from: str, date_to: str) -> str:
    """Get financial summary including revenue, expenses, profit, and outstanding invoices.

    Args:
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
    """
    try:
        summary = odoo.get_financial_summary(date_from, date_to)
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_outstanding_invoices() -> str:
    """Get list of outstanding invoices (posted but not fully paid)."""
    try:
        invoices = odoo.get_outstanding_invoices()
        return json.dumps(invoices, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_invoices(
    state: str = None,
    payment_state: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = None
) -> str:
    """Get invoices with optional filters.

    Args:
        state: Invoice state (draft, posted, cancel)
        payment_state: Payment state (not_paid, in_payment, paid, partial)
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
        limit: Maximum number of invoices to return
    """
    try:
        filters = {}
        if state:
            filters["state"] = state
        if payment_state:
            filters["payment_state"] = payment_state
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if limit:
            filters["limit"] = limit

        invoices = odoo.get_invoices(filters)
        return json.dumps(invoices, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_revenue(date_from: str, date_to: str) -> str:
    """Get total revenue for a date range.

    Args:
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
    """
    try:
        revenue = odoo.get_revenue(date_from, date_to)
        result = {
            "revenue": revenue,
            "date_from": date_from,
            "date_to": date_to
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_expenses(date_from: str, date_to: str) -> str:
    """Get total expenses for a date range.

    Args:
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
    """
    try:
        expenses = odoo.get_expenses(date_from, date_to)
        result = {
            "expenses": expenses,
            "date_from": date_from,
            "date_to": date_to
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_customers(limit: int = None) -> str:
    """Get list of customers.

    Args:
        limit: Maximum number of customers to return
    """
    try:
        customers = odoo.get_customers(limit)
        return json.dumps(customers, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def health_check() -> str:
    """Check Odoo connection and authentication status."""
    try:
        health = odoo.health_check()
        return json.dumps(health, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

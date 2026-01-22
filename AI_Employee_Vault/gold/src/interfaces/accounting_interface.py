"""
Accounting Interface

Abstract interface for accounting systems.
Allows swapping between Mock Xero (development) and Real Xero (production).

Gold Tier Requirement #3: Xero Accounting Integration
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class AccountingInterface(ABC):
    """
    Abstract interface for accounting systems.

    Both MockXeroAPI and XeroAPI must implement this interface.
    This allows seamless switching between mock and real implementations.
    """

    @abstractmethod
    def get_invoices(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contact_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get invoices from accounting system.

        Args:
            status: Filter by status (DRAFT, SUBMITTED, AUTHORISED, PAID, VOIDED)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            contact_id: Filter by contact ID

        Returns:
            List of invoice dictionaries
        """
        pass

    @abstractmethod
    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from accounting system.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            transaction_type: Filter by type (income, expense, transfer)

        Returns:
            List of transaction dictionaries
        """
        pass

    @abstractmethod
    def get_contacts(
        self,
        contact_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contacts (customers/suppliers) from accounting system.

        Args:
            contact_type: Filter by type (CUSTOMER, SUPPLIER, ALL)
            search: Search term

        Returns:
            List of contact dictionaries
        """
        pass

    @abstractmethod
    def get_profit_and_loss(
        self,
        start_date: str,
        end_date: str,
        periods: int = 1
    ) -> Dict[str, Any]:
        """
        Get Profit & Loss report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            periods: Number of periods

        Returns:
            P&L report dictionary
        """
        pass

    @abstractmethod
    def get_balance_sheet(
        self,
        date: str
    ) -> Dict[str, Any]:
        """
        Get Balance Sheet report.

        Args:
            date: Report date (YYYY-MM-DD)

        Returns:
            Balance sheet dictionary
        """
        pass

    @abstractmethod
    def get_cash_flow(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get Cash Flow report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Cash flow dictionary
        """
        pass

    @abstractmethod
    def create_invoice(
        self,
        contact: str,
        date: str,
        due_date: str,
        line_items: List[Dict[str, Any]],
        reference: Optional[str] = None,
        status: str = "DRAFT"
    ) -> Dict[str, Any]:
        """
        Create a new invoice.

        Args:
            contact: Contact name or ID
            date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            line_items: List of line items
            reference: Optional reference
            status: Invoice status (DRAFT, SUBMITTED, AUTHORISED)

        Returns:
            Created invoice dictionary
        """
        pass

    @abstractmethod
    def update_invoice(
        self,
        invoice_id: str,
        status: Optional[str] = None,
        payment_date: Optional[str] = None,
        payment_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update an existing invoice.

        Args:
            invoice_id: Invoice ID
            status: New status (AUTHORISED, PAID, VOIDED)
            payment_date: Payment date (YYYY-MM-DD)
            payment_amount: Payment amount

        Returns:
            Updated invoice dictionary
        """
        pass

    @abstractmethod
    def categorize_transaction(
        self,
        description: str,
        vendor: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Automatically categorize a transaction using AI.

        Args:
            description: Transaction description
            vendor: Vendor name
            amount: Transaction amount

        Returns:
            Categorization result dictionary
        """
        pass

    @abstractmethod
    def sync_transactions(
        self,
        since: Optional[str] = None,
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """
        Sync transactions from accounting system to vault.

        Args:
            since: Sync transactions since this date (ISO-8601)
            auto_categorize: Whether to auto-categorize transactions

        Returns:
            Sync result dictionary
        """
        pass

"""
services/financial_summary_service.py — Financial metrics from the database.

CRITICAL PRINCIPLE: This service always uses direct SQL/ORM queries.
It NEVER uses the AI to compute financial numbers.
The AI uses the OUTPUT of this service to format natural language responses.

"No inventar movimientos. Nunca asumir datos inexistentes." — CLAUDE.md

Responsible for:
- Monthly income/expense totals
- All-time balance calculation
- Category expense breakdowns
- Month-over-month comparison
- Recent transactions list
- Building comprehensive context dict for AI query responses

TODO: Implement in Sprint 5.
"""
import logging
from datetime import date

from app.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)

_transaction_repo = TransactionRepository()


class FinancialSummaryService:
    """Computes financial metrics directly from PostgreSQL."""

    def get_monthly_summary(
        self,
        user_id: str,
        year: int = None,
        month: int = None,
    ) -> dict:
        """
        Income, expense, and balance totals for a month.
        Defaults to the current month.

        Returns:
            {
                'year': int, 'month': int,
                'income': float, 'expense': float, 'balance': float,
            }

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_current_balance(self, user_id: str) -> float:
        """
        All-time net balance: total income - total expenses.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_expenses_by_category(
        self,
        user_id: str,
        year: int,
        month: int,
    ) -> list[dict]:
        """
        Expense totals per category for a given month.

        Returns:
            [{'category_name': str, 'total': float, 'percentage': float, ...}]

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_monthly_comparison(self, user_id: str) -> dict:
        """
        Compare current month with previous month.

        Returns:
            {
                'current': {'income': float, 'expense': float},
                'previous': {'income': float, 'expense': float},
                'expense_change_pct': float,  # positive = spending more
            }

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_biggest_expense(
        self,
        user_id: str,
        year: int = None,
        month: int = None,
    ):
        """
        Get the single largest expense transaction for a period.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_recent_transactions(self, user_id: str, limit: int = 5) -> list:
        """
        Get the N most recent transactions for dashboard home card.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def build_query_context(self, user_id: str) -> dict:
        """
        Aggregate all financial metrics into a single dict for AI responses.
        The AI uses this to answer natural language queries without inventing data.

        Returns comprehensive dict with current month, balance, categories, etc.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

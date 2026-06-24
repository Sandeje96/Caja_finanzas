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
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month
            
        totals = _transaction_repo.get_monthly_totals(user_id, year, month)
        return {
            'year': year,
            'month': month,
            'income': totals.get('income', 0.0),
            'expense': totals.get('expense', 0.0),
            'balance': totals.get('balance', 0.0)
        }

    def get_current_balance(self, user_id: str) -> float:
        """
        All-time net balance: total income - total expenses.
        """
        return _transaction_repo.get_all_time_balance(user_id)

    def get_expenses_by_category(
        self,
        user_id: str,
        year: int,
        month: int,
    ) -> list[dict]:
        """
        Expense totals per category for a given month.
        """
        return _transaction_repo.get_by_category_totals(user_id, year, month)

    def get_monthly_comparison(self, user_id: str) -> dict:
        """
        Compare current month with previous month.
        """
        today = date.today()
        current_year, current_month = today.year, today.month
        
        if current_month == 1:
            prev_year, prev_month = current_year - 1, 12
        else:
            prev_year, prev_month = current_year, current_month - 1
            
        current = _transaction_repo.get_monthly_totals(user_id, current_year, current_month)
        previous = _transaction_repo.get_monthly_totals(user_id, prev_year, prev_month)
        
        c_exp = current.get('expense', 0.0)
        p_exp = previous.get('expense', 0.0)
        
        change_pct = 0.0
        if p_exp > 0:
            change_pct = ((c_exp - p_exp) / p_exp) * 100
            
        return {
            'current': current,
            'previous': previous,
            'expense_change_pct': change_pct
        }

    def get_biggest_expense(
        self,
        user_id: str,
        year: int = None,
        month: int = None,
    ):
        """
        Get the single largest expense transaction for a period.
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month
            
        return _transaction_repo.get_biggest_expense(user_id, year, month)

    def get_recent_transactions(self, user_id: str, limit: int = 5) -> list:
        """
        Get the N most recent transactions for dashboard home card.
        """
        return _transaction_repo.get_recent(user_id, limit)

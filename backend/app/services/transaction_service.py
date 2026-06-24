"""
services/transaction_service.py — Business logic for financial transactions.

Responsible for:
- Creating transactions (with automatic category resolution)
- Updating transactions (with ownership validation)
- Soft-deleting transactions
- Validating business rules (amount > 0, valid type, etc.)

Category resolution strategy:
  1. Try exact name match (case-insensitive)
  2. Try partial name match (ILIKE '%name%')
  3. Fallback to 'Otros' category if nothing matches

TODO: Implement core methods in Sprint 3.
"""
import logging
from datetime import date

from app.extensions import db
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)

_transaction_repo = TransactionRepository()
_category_repo    = CategoryRepository()


class TransactionService:
    """Business logic layer for financial transactions."""

    def create_expense(
        self,
        user_id: str,
        amount: float,
        description: str,
        category_name: str = None,
        transaction_date: date = None,
        message_id: str = None,
        ai_confidence: float = None,
        source: str = 'whatsapp',
    ):
        """
        Create a new expense transaction.
        Automatically resolves category_name to the best matching Category.

        Returns the created Transaction instance.

        TODO: Implement in Sprint 3.
        """
        raise NotImplementedError("Sprint 3")

    def create_income(
        self,
        user_id: str,
        amount: float,
        description: str,
        category_name: str = None,
        transaction_date: date = None,
        message_id: str = None,
        ai_confidence: float = None,
        source: str = 'whatsapp',
    ):
        """
        Create a new income transaction.
        Automatically resolves category_name to the best matching Category.

        Returns the created Transaction instance.

        TODO: Implement in Sprint 3.
        """
        raise NotImplementedError("Sprint 3")

    def update_transaction(
        self,
        transaction_id: str,
        user_id: str,
        **kwargs,
    ):
        """
        Update fields on an existing transaction.
        Validates that the transaction belongs to the user.

        Raises:
            ValueError: If transaction not found or doesn't belong to user

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """
        Soft-delete a transaction.
        Validates ownership before deleting.

        Returns True if deleted, False if not found or unauthorized.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def get_transaction(self, transaction_id: str, user_id: str):
        """
        Get a single transaction by ID, validating user ownership.

        Returns the Transaction or raises ValueError if not found/unauthorized.

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5")

    def _resolve_category(self, category_name: str, user_id: str):
        """
        Find the best matching category or fall back to 'Otros'.
        Returns a Category instance (never None — always falls back).
        """
        if category_name:
            category = _category_repo.find_best_match(category_name, user_id)
            if category:
                return category

        # Fallback: always return 'Otros' so no transaction is category-less
        fallback = _category_repo.get_fallback_category(user_id)
        if not fallback:
            logger.error("[TransactionService] 'Otros' category not found — run flask seed-db")
        return fallback

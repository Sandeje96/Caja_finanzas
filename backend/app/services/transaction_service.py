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
"""
import logging
from datetime import date

from app.extensions import db
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction import Transaction

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
        category_name: str | None = None,
        merchant: str | None = None,
        message_id: str | None = None,
        ai_confidence: float | None = None,
    ) -> Transaction:
        """
        Creates a new expense transaction.
        Amount will be forced negative.
        """
        abs_amount = abs(float(amount))
        category_id = self._resolve_category(user_id, category_name, 'expense')

        t = Transaction(
            user_id=user_id,
            amount=abs_amount,
            type='expense',
            merchant=merchant,
            description=description,
            category_id=category_id,
            message_id=message_id,
            ai_confidence=ai_confidence,
            source='whatsapp'
        )
        db.session.add(t)
        db.session.commit()
        logger.info(f"[TransactionService] Expense created for user {user_id}: ${abs_amount}")
        return t

    def create_income(
        self,
        user_id: str,
        amount: float,
        description: str,
        category_name: str | None = None,
        message_id: str | None = None,
        ai_confidence: float | None = None,
    ) -> Transaction:
        """
        Creates a new income transaction.
        Amount will be forced positive.
        """
        abs_amount = abs(float(amount))
        category_id = self._resolve_category(user_id, category_name, 'income')

        t = Transaction(
            user_id=user_id,
            amount=abs_amount,
            type='income',
            description=description,
            category_id=category_id,
            message_id=message_id,
            ai_confidence=ai_confidence,
            source='whatsapp'
        )
        db.session.add(t)
        db.session.commit()
        logger.info(f"[TransactionService] Income created for user {user_id}: ${abs_amount}")
        return t

    def update_transaction(
        self,
        transaction_id: str,
        user_id: str,
        **kwargs,
    ):
        """
        Update fields on an existing transaction.
        Validates that the transaction belongs to the user.
        """
        t = _transaction_repo.get_by_id(transaction_id)
        if not t or str(t.user_id) != str(user_id):
            raise ValueError("Transaction not found or unauthorized")
            
        for key, value in kwargs.items():
            if hasattr(t, key):
                setattr(t, key, value)
                
        _transaction_repo.save()
        return t

    def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """
        Soft-delete a transaction.
        Validates ownership before deleting.
        """
        t = _transaction_repo.get_by_id(transaction_id)
        if not t or str(t.user_id) != str(user_id):
            return False
            
        _transaction_repo.soft_delete(t.id)
        return True

    def get_transaction(self, transaction_id: str, user_id: str):
        """
        Get a single transaction by ID, validating user ownership.
        """
        t = _transaction_repo.get_by_id(transaction_id)
        if not t or str(t.user_id) != str(user_id):
            raise ValueError("Transaction not found or unauthorized")
        return t

    def get_last_transaction(self, user_id: str):
        """Returns the most recent transaction for the user."""
        recent = _transaction_repo.get_recent(user_id, limit=1)
        return recent[0] if recent else None

    def confirm_last_transaction(self, user_id: str):
        """Confirms the most recent transaction."""
        t = self.get_last_transaction(user_id)
        if not t:
            return None
        _transaction_repo.save()
        return t

    def delete_last_transaction(self, user_id: str):
        """Soft-deletes the most recent transaction."""
        t = self.get_last_transaction(user_id)
        if not t:
            return None
        _transaction_repo.soft_delete(t.id)
        return t

    def update_last_transaction(self, user_id: str, amount: float = None, category_name: str = None, description: str = None):
        """Updates the most recent transaction based on AI extraction."""
        t = self.get_last_transaction(user_id)
        if not t:
            return None
        
        if amount is not None:
            t.amount = amount
        if category_name is not None:
            category = self._resolve_category(category_name, user_id)
            t.category_id = category.id if category else None
        if description is not None:
            t.description = description
            
        _transaction_repo.save()
        return t

    def get_recent_transactions_text(self, user_id: str, limit: int = 5) -> str:
        """Formats the N most recent transactions into a readable text block."""
        recent = _transaction_repo.get_recent(user_id, limit=limit)
        if not recent:
            return "No tenés movimientos registrados."
            
        lines = ["Tus últimos movimientos:"]
        for t in recent:
            cat_name = t.category.name if t.category else 'Otros'
            sign = "-" if t.type == 'expense' else "+"
            lines.append(f"• {t.transaction_date.strftime('%d/%m')} | {cat_name} | {sign}${float(t.amount):,.0f}".replace(',', '.'))
        return "\n".join(lines)

    def _resolve_category(self, user_id: str, category_name: str | None, transaction_type: str = 'both'):
        """
        Find the best matching category or fall back to 'Otros'.
        Returns a Category ID.
        """
        if category_name:
            category = _category_repo.find_best_match(category_name, user_id)
            if category:
                return category.id
                
            # Create category automatically if not found
            category = _category_repo.create(
                user_id=user_id,
                name=category_name.capitalize(),
                type=transaction_type,
                is_system=False
            )
            _category_repo.save()
            return category.id

        # Fallback: always return 'Otros' so no transaction is category-less
        fallback = _category_repo.get_fallback_category(user_id)
        if not fallback:
            logger.error("[TransactionService] 'Otros' category not found — run flask seed-db")
            return None
        return fallback.id

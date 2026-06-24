"""repositories/transaction_repository.py"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, func

from app.models.attachment import Attachment
from app.models.category import Category
from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):

    def __init__(self):
        super().__init__(Transaction)

    def get_for_user_paginated(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        type: str = None,
        category_id: str = None,
        date_from: date = None,
        date_to: date = None,
        search: str = None,
    ):
        """
        Get paginated transactions for a user with optional filters.
        Used by the dashboard transactions page.
        """
        query = (
            Transaction.query
            .filter_by(user_id=user_id, deleted_at=None)
        )

        if type:
            query = query.filter(Transaction.type == type)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        if date_from:
            query = query.filter(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(Transaction.transaction_date <= date_to)
        if search:
            query = query.filter(Transaction.description.ilike(f'%{search}%'))

        return query.order_by(Transaction.transaction_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_recent_without_attachment(
        self,
        user_id: str,
        hours: int = 24,
    ) -> Transaction | None:
        """
        Find the most recent transaction without an attachment, created within the last N hours.
        Used to automatically associate incoming receipt images to transactions.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        has_attachment = (
            Attachment.query
            .filter(
                Attachment.transaction_id == Transaction.id,
                Attachment.deleted_at.is_(None),
            )
            .exists()
        )

        return (
            Transaction.query
            .filter(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                Transaction.created_at >= cutoff,
                ~has_attachment,
            )
            .order_by(Transaction.created_at.desc())
            .first()
        )

    def get_monthly_totals(self, user_id: str, year: int, month: int) -> dict:
        """
        Get income and expense totals for a specific month.
        Returns {'income': float, 'expense': float, 'balance': float}
        """
        rows = (
            Transaction.query
            .with_entities(
                Transaction.type,
                func.sum(Transaction.amount).label('total'),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                func.extract('year',  Transaction.transaction_date) == year,
                func.extract('month', Transaction.transaction_date) == month,
            )
            .group_by(Transaction.type)
            .all()
        )

        totals = {'income': 0.0, 'expense': 0.0}
        for row in rows:
            if row.type in totals:
                totals[row.type] = float(row.total or 0)
        totals['balance'] = totals['income'] - totals['expense']
        return totals

    def get_all_time_balance(self, user_id: str) -> float:
        """
        Net balance = all-time income - all-time expenses.
        """
        rows = (
            Transaction.query
            .with_entities(
                Transaction.type,
                func.sum(Transaction.amount).label('total'),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                Transaction.type.in_(['income', 'expense']),
            )
            .group_by(Transaction.type)
            .all()
        )

        totals = {'income': 0.0, 'expense': 0.0}
        for row in rows:
            totals[row.type] = float(row.total or 0)
        return totals['income'] - totals['expense']

    def get_by_category_totals(self, user_id: str, year: int, month: int) -> list[dict]:
        """
        Expense totals grouped by category for a given month.
        Returns list of dicts sorted by total descending.
        """
        rows = (
            Transaction.query
            .with_entities(
                Category.id.label('category_id'),
                Category.name.label('category_name'),
                Category.icon.label('category_icon'),
                Category.color.label('category_color'),
                func.sum(Transaction.amount).label('total'),
            )
            .join(Category, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.deleted_at.is_(None),
                func.extract('year',  Transaction.transaction_date) == year,
                func.extract('month', Transaction.transaction_date) == month,
            )
            .group_by(Category.id, Category.name, Category.icon, Category.color)
            .order_by(func.sum(Transaction.amount).desc())
            .all()
        )

        return [
            {
                'category_id':    str(r.category_id),
                'category_name':  r.category_name,
                'category_icon':  r.category_icon,
                'category_color': r.category_color,
                'total':          float(r.total or 0),
            }
            for r in rows
        ]

    def get_recent(self, user_id: str, limit: int = 5) -> list[Transaction]:
        """Get the N most recent transactions for a user."""
        return (
            Transaction.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .limit(limit)
            .all()
        )

"""
models/category.py — Category entity.

Categories classify transactions (expense / income / both).

Two types:
  - System categories (user_id = NULL, is_system = True):
    Global, shared by all users. Seeded at startup. Cannot be modified by users.
  - User categories (user_id = <uuid>, is_system = False):
    Custom categories created by a specific user.

The IA maps natural language (e.g., "combustible") to the closest category name.
"""
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import BaseModel


class Category(BaseModel):
    __tablename__ = 'categories'

    # ─── Ownership ────────────────────────────────────────────────────────────
    # NULL = global system category available to all users
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # ─── Properties ───────────────────────────────────────────────────────────
    name = Column(String(100), nullable=False)

    # expense | income | both
    type = Column(String(10), default='both', nullable=False)

    # Emoji or icon name for UI display
    icon = Column(String(50), nullable=True)

    # Hex color string: '#FF5722'
    color = Column(String(7), nullable=True)

    # System categories cannot be edited by users
    is_system = Column(Boolean, default=False, nullable=False)

    # ─── Constraints ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "type IN ('expense', 'income', 'both')",
            name='check_category_type',
        ),
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='categories')
    transactions = db.relationship(
        'Transaction', back_populates='category', lazy='dynamic',
        primaryjoin="and_(Category.id==Transaction.category_id, Transaction.deleted_at==None)"
    )

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'user_id':   str(self.user_id) if self.user_id else None,
            'name':      self.name,
            'type':      self.type,
            'icon':      self.icon,
            'color':     self.color,
            'is_system': self.is_system,
        })
        return base

    def __repr__(self) -> str:
        scope = 'global' if self.user_id is None else f'user={self.user_id}'
        return f'<Category name={self.name} type={self.type} {scope}>'

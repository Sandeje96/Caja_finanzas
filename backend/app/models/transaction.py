"""
models/transaction.py — Transaction entity.

The core financial record. Every expense, income, transfer, or adjustment
is a transaction row.

Key design decisions:
  - message_id links the transaction back to the WhatsApp message that created it
    (full conversational traceability)
  - ai_confidence (0-1) records how sure the AI was about its extraction
  - source distinguishes between WhatsApp-created and dashboard-created transactions
  - amount is always positive; direction is indicated by `type`
"""
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import BaseModel


class Transaction(BaseModel):
    __tablename__ = 'transactions'

    # ─── Foreign keys ─────────────────────────────────────────────────────────
    user_id     = Column(UUID(as_uuid=True), ForeignKey('users.id'),     nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), nullable=True)

    # Link to the WhatsApp message that originated this transaction
    message_id  = Column(UUID(as_uuid=True), ForeignKey('messages.id'),   nullable=True)

    # ─── Financial data ───────────────────────────────────────────────────────
    # expense | income | transfer | adjustment
    type   = Column(String(20), nullable=False)

    # Always positive — direction is determined by `type`
    amount = Column(Numeric(15, 2), nullable=False)

    merchant         = Column(String(255), nullable=True)
    description      = Column(Text,   nullable=True)
    notes            = Column(Text,   nullable=True)
    transaction_date = Column(Date,   nullable=False, default=date.today)

    # ─── Metadata ─────────────────────────────────────────────────────────────
    # whatsapp | dashboard | import
    source = Column(String(20), default='whatsapp', nullable=False)

    # AI extraction confidence: 0.000 to 1.000
    ai_confidence = Column(Numeric(4, 3), nullable=True)

    # ─── Constraints ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "type IN ('expense', 'income', 'transfer', 'adjustment')",
            name='check_transaction_type',
        ),
        CheckConstraint(
            "source IN ('whatsapp', 'dashboard', 'import')",
            name='check_transaction_source',
        ),
        CheckConstraint(
            'amount > 0',
            name='check_transaction_amount_positive',
        ),
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    user     = db.relationship('User',     back_populates='transactions')
    category = db.relationship('Category', back_populates='transactions')
    message  = db.relationship('Message',  back_populates='transactions')
    attachments = db.relationship(
        'Attachment', back_populates='transaction', lazy='dynamic',
        primaryjoin="and_(Transaction.id==Attachment.transaction_id, Attachment.deleted_at==None)"
    )

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'user_id':          str(self.user_id),
            'category_id':      str(self.category_id) if self.category_id else None,
            'message_id':       str(self.message_id)  if self.message_id  else None,
            'type':             self.type,
            'amount':           float(self.amount),
            'description':      self.description,
            'notes':            self.notes,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'source':           self.source,
            'ai_confidence':    float(self.ai_confidence) if self.ai_confidence else None,
            # Eager-loaded category name for convenience
            'category_name':    self.category.name if self.category else None,
            'category_icon':    self.category.icon if self.category else None,
        })
        return base

    def __repr__(self) -> str:
        return f'<Transaction {self.type} ${self.amount} on {self.transaction_date}>'

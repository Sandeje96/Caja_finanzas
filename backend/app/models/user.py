"""
models/user.py — User entity.

A user is identified by their WhatsApp phone number (E.164 format).
The email + password_hash fields are only used for dashboard authentication.
A user can interact with the system exclusively via WhatsApp without ever
setting an email or password.
"""
from sqlalchemy import Boolean, Column, String, DateTime

from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = 'users'

    # ─── Identity ─────────────────────────────────────────────────────────────
    # Primary identifier for WhatsApp channel
    phone = Column(String(20), unique=True, nullable=False, index=True)

    # Optional: display name from WhatsApp or set by user
    name = Column(String(100), nullable=True)

    # Dashboard login credentials (OTP based)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)

    # ─── Preferences ──────────────────────────────────────────────────────────
    timezone = Column(String(50), default='America/Argentina/Buenos_Aires', nullable=False)
    currency = Column(String(10), default='ARS', nullable=False)

    # ─── Status ───────────────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    conversations = db.relationship(
        'Conversation', back_populates='user', lazy='dynamic',
        primaryjoin="and_(User.id==Conversation.user_id, Conversation.deleted_at==None)"
    )
    transactions = db.relationship(
        'Transaction', back_populates='user', lazy='dynamic',
        primaryjoin="and_(User.id==Transaction.user_id, Transaction.deleted_at==None)"
    )
    attachments = db.relationship(
        'Attachment', back_populates='user', lazy='dynamic',
        primaryjoin="and_(User.id==Attachment.user_id, Attachment.deleted_at==None)"
    )
    ai_logs = db.relationship('AILog', back_populates='user', lazy='dynamic')
    categories = db.relationship(
        'Category', back_populates='user', lazy='dynamic',
        primaryjoin="and_(User.id==Category.user_id, Category.deleted_at==None)"
    )

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'phone':     self.phone,
            'name':      self.name,
            'timezone':  self.timezone,
            'currency':  self.currency,
            'is_active': self.is_active,
        })
        return base

    def to_public_dict(self) -> dict:
        """Safe dict for API responses."""
        return self.to_dict()

    def __repr__(self) -> str:
        return f'<User phone={self.phone} name={self.name}>'

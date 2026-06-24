"""
models/conversation.py — Conversation entity.

Each WhatsApp "session" is modeled as a Conversation.
A user has one active conversation at a time.
Conversations are never deleted — they are a strategic asset for future AI features.
"""
from sqlalchemy import Boolean, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db
from app.models.base import BaseModel


class Conversation(BaseModel):
    __tablename__ = 'conversations'

    # ─── Foreign keys ─────────────────────────────────────────────────────────
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # ─── State ────────────────────────────────────────────────────────────────
    # Only one conversation per user should be active at a time
    is_active = Column(Boolean, default=True, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='conversations')
    messages = db.relationship(
        'Message',
        back_populates='conversation',
        lazy='dynamic',
        order_by='Message.created_at',
        primaryjoin="and_(Conversation.id==Message.conversation_id, Message.deleted_at==None)"
    )

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'user_id':    str(self.user_id),
            'is_active':  self.is_active,
            'started_at': self.created_at.isoformat() if self.created_at else None,
        })
        return base

    def __repr__(self) -> str:
        return f'<Conversation id={self.id} user={self.user_id} active={self.is_active}>'

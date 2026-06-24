"""
models/message.py — Message entity.

Every incoming and outgoing message is stored permanently.
Messages are the core audit trail and the source of truth for the AI context window.

Key field:
  whatsapp_message_id — WhatsApp's own message ID.
  Used for deduplication: WhatsApp may re-send the same webhook event
  (at-least-once delivery). A UNIQUE constraint prevents double-processing.
"""
from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions import db
from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = 'messages'

    # ─── Foreign keys ─────────────────────────────────────────────────────────
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)

    # ─── WhatsApp deduplication key ───────────────────────────────────────────
    # Unique index ensures we never process the same message twice
    whatsapp_message_id = Column(String(100), index=True, nullable=True)

    # ─── Content ──────────────────────────────────────────────────────────────
    # 'user' = from WhatsApp user | 'assistant' = from AI | 'system' = internal
    role = Column(String(10), nullable=False, default='user')

    content = Column(Text, nullable=False)

    # text | image | document | audio | video
    message_type = Column(String(20), default='text', nullable=False)

    # Full raw WhatsApp webhook payload (for auditing and future features)
    raw_payload = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    # ─── Constraints ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='check_message_role',
        ),
        CheckConstraint(
            "message_type IN ('text', 'image', 'document', 'audio', 'video')",
            name='check_message_type',
        ),
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    conversation = db.relationship('Conversation', back_populates='messages')
    transactions = db.relationship('Transaction', back_populates='message', lazy='dynamic')
    ai_logs = db.relationship('AILog', back_populates='message', lazy='dynamic')

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'conversation_id':     str(self.conversation_id),
            'role':                self.role,
            'content':             self.content,
            'message_type':        self.message_type,
            'whatsapp_message_id': self.whatsapp_message_id,
        })
        return base

    def to_ai_context_dict(self) -> dict:
        """Format compatible with OpenAI messages array."""
        return {'role': self.role, 'content': self.content}

    def __repr__(self) -> str:
        preview = (self.content or '')[:40]
        return f'<Message [{self.role}] "{preview}...">'

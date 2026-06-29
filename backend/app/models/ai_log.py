"""
models/ai_log.py — AI interaction log entity.

Records every call made to OpenAI for:
  1. Cost monitoring (track token usage and USD spend)
  2. Debugging (see what prompt produced what result)
  3. Performance analysis (latency per intent)
  4. Audit trail

This table grows indefinitely — implement archival policy in production
(e.g., move records older than 90 days to S3 cold storage).
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import BaseModel


class AILog(BaseModel):
    __tablename__ = 'ai_logs'

    # ─── Foreign keys ─────────────────────────────────────────────────────────
    user_id    = Column(UUID(as_uuid=True), ForeignKey('users.id'),    nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=True)

    # ─── Classification result ────────────────────────────────────────────────
    intent = Column(String(50), nullable=True)   # REGISTER_EXPENSE, QUERY, etc.

    # ─── Raw Data ─────────────────────────────────────────────────────────────
    request_json  = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    response_json = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    # ─── Token usage ──────────────────────────────────────────────────────────
    prompt_tokens     = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens      = Column(Integer, nullable=True)

    # ─── Model and cost ───────────────────────────────────────────────────────
    model    = Column(String(50),      nullable=True)   # gpt-4o-mini
    cost_usd = Column(Numeric(10, 6),  nullable=True)   # estimated USD cost

    # ─── Performance ──────────────────────────────────────────────────────────
    latency_ms = Column(Integer, nullable=True)   # round-trip time in ms

    # ─── Status ───────────────────────────────────────────────────────────────
    success       = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    user    = db.relationship('User',    back_populates='ai_logs')
    message = db.relationship('Message', back_populates='ai_logs')

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'user_id':            str(self.user_id)    if self.user_id    else None,
            'message_id':         str(self.message_id) if self.message_id else None,
            'intent':             self.intent,
            'request_json':       self.request_json,
            'response_json':      self.response_json,
            'total_tokens':       self.total_tokens,
            'model':              self.model,
            'cost_usd':           float(self.cost_usd) if self.cost_usd else None,
            'latency_ms':         self.latency_ms,
            'success':            self.success,
        })
        return base

    def __repr__(self) -> str:
        return f'<AILog intent={self.intent} tokens={self.total_tokens} ok={self.success}>'

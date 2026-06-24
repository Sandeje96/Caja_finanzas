"""
models/pending_action.py — Acciones pendientes de confirmación humana.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import BaseModel


class PendingAction(BaseModel):
    __tablename__ = 'pending_actions'

    user_id      = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    action_type  = Column(String(50), nullable=False)
    payload_json = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False, default=dict)
    
    expires_at   = Column(DateTime(timezone=True), nullable=False)
    resolved_at  = Column(DateTime(timezone=True), nullable=True)
    
    # pending, confirmed, cancelled, expired
    status       = Column(String(20), default='pending', nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('pending_actions', lazy=True))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    @property
    def is_active(self) -> bool:
        """Check if action is pending and not expired."""
        if self.status != 'pending':
            return False
        if self.expires_at:
            exp = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
            if datetime.now(timezone.utc) > exp:
                return False
        return True

    def mark_expired_if_needed(self) -> bool:
        """Marks as expired if past expiration date. Returns True if state changed."""
        if self.status == 'pending' and self.expires_at:
            exp = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
            if datetime.now(timezone.utc) > exp:
                self.status = 'expired'
                self.resolved_at = datetime.now(timezone.utc)
                return True
        return False

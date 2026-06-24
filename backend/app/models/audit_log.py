"""
models/audit_log.py — Audit Log entity.

Records all manual modifications made via the dashboard.
"""
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions import db
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'), nullable=False)
    
    # The action performed: 'UPDATE', 'DELETE', etc.
    action = Column(String(50), nullable=False)
    
    # Changes saved as JSON { "field": {"old": val, "new": val} }
    changes = Column(JSONB, nullable=False)
    
    # ─── Relationships ────────────────────────────────────────────────────────
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic', overlaps="ai_logs,attachments,categories,conversations,transactions"))
    transaction = db.relationship('Transaction', backref=db.backref('audit_logs', lazy='dynamic', overlaps="attachments"))

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'user_id': str(self.user_id),
            'transaction_id': str(self.transaction_id),
            'action': self.action,
            'changes': self.changes,
        })
        return base

    def __repr__(self) -> str:
        return f'<AuditLog {self.action} tx={self.transaction_id}>'

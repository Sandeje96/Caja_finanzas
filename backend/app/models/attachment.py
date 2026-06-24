"""
models/attachment.py — Attachment entity.

Represents a receipt, invoice, or document associated with a transaction.
The actual file is stored in Supabase Storage (private bucket).
Only the storage_path and metadata are stored in PostgreSQL.

Key design:
  - transaction_id is nullable: a file can arrive before the transaction is created
  - status tracks the upload lifecycle: pending → uploaded | failed
  - whatsapp_media_id links back to the WhatsApp media object (for debugging)
  - Access is via signed URLs with expiration (never public permanent URLs)
"""
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.extensions import db
from app.models.base import BaseModel


class Attachment(BaseModel):
    __tablename__ = 'attachments'

    # ─── Foreign keys ─────────────────────────────────────────────────────────
    # Nullable: a receipt can arrive before the transaction is recorded
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'), nullable=True)
    user_id        = Column(UUID(as_uuid=True), ForeignKey('users.id'),        nullable=False)

    # ─── Storage ──────────────────────────────────────────────────────────────
    # Path within the Supabase bucket: '{user_id}/2026/06/{uuid}.jpg'
    storage_path = Column(String(500), nullable=False)

    # Permanent public URL — NULL for private buckets (use signed URLs instead)
    public_url = Column(Text, nullable=True)

    # ─── File metadata ────────────────────────────────────────────────────────
    file_name  = Column(String(255), nullable=True)
    mime_type  = Column(String(100), nullable=True)
    file_size  = Column(Integer,     nullable=True)   # bytes

    # ─── Status ───────────────────────────────────────────────────────────────
    # pending → uploading → uploaded | failed
    status = Column(String(20), default='uploaded', nullable=False)

    # ─── OCR Data ─────────────────────────────────────────────────────────────
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    ocr_json         = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    ocr_confidence   = Column(db.Float, nullable=True)
    ocr_processed_at = Column(db.DateTime(timezone=True), nullable=True)
    # pending, processed, failed
    ocr_status       = Column(String(20), nullable=True)

    # WhatsApp's own media ID — used to re-download if needed
    whatsapp_media_id = Column(String(100), nullable=True)

    # ─── Constraints ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'uploaded', 'failed', 'processing')",
            name='check_attachment_status',
        ),
    )

    # ─── Relationships ────────────────────────────────────────────────────────
    user        = db.relationship('User',        back_populates='attachments')
    transaction = db.relationship('Transaction', back_populates='attachments')

    # ─── Serialization ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            'transaction_id':    str(self.transaction_id) if self.transaction_id else None,
            'user_id':           str(self.user_id),
            'storage_path':      self.storage_path,
            'file_name':         self.file_name,
            'mime_type':         self.mime_type,
            'file_size':         self.file_size,
            'status':            self.status,
            # NOTE: public_url is not exposed here
            # Use GET /api/attachments/<id>/url for a signed URL
        })
        return base

    @property
    def file_size_mb(self) -> float | None:
        """File size in megabytes, rounded to 2 decimal places."""
        if self.file_size is None:
            return None
        return round(self.file_size / (1024 * 1024), 2)

    def __repr__(self) -> str:
        return f'<Attachment {self.file_name} status={self.status}>'

"""repositories/attachment_repository.py"""
from app.models.attachment import Attachment
from app.repositories.base_repository import BaseRepository


class AttachmentRepository(BaseRepository):

    def __init__(self):
        super().__init__(Attachment)

    def get_by_transaction(self, transaction_id: str) -> list[Attachment]:
        """Get all uploaded attachments for a transaction."""
        return (
            Attachment.query
            .filter_by(
                transaction_id=transaction_id,
                deleted_at=None,
                status='uploaded',
            )
            .order_by(Attachment.created_at.desc())
            .all()
        )

    def get_orphaned_for_user(self, user_id: str, limit: int = 5) -> list[Attachment]:
        """
        Get attachments not yet linked to a transaction.
        Ordered by most recent first.
        """
        return (
            Attachment.query
            .filter(
                Attachment.user_id == user_id,
                Attachment.transaction_id.is_(None),
                Attachment.deleted_at.is_(None),
            )
            .order_by(Attachment.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_for_user_paginated(self, user_id: str, page: int = 1, per_page: int = 20):
        """Get paginated attachments for a user (dashboard gallery view)."""
        return (
            Attachment.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Attachment.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def find_by_whatsapp_media_id(self, media_id: str) -> Attachment | None:
        """Find an attachment by its WhatsApp media object ID."""
        return Attachment.query.filter_by(
            whatsapp_media_id=media_id,
            deleted_at=None,
        ).first()

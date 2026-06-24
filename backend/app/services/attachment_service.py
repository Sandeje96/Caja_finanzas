"""
services/attachment_service.py — Receipt and document processing.

Full pipeline (Sprint 4):
  1. Receive WhatsApp media_id from webhook
  2. Get temporary download URL via WhatsApp Graph API
  3. Download file bytes
  4. Validate MIME type and size
  5. Generate unique storage path: {user_id}/{year}/{month}/{uuid}.{ext}
  6. Upload to Supabase Storage (private bucket)
  7. Create Attachment record in DB
  8. Auto-associate to most recent unlinked transaction (< 24h)
  9. Return confirmation text for WhatsApp reply

TODO: Implement in Sprint 4.
"""
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Allowed MIME types
ALLOWED_MIME_TYPES: set[str] = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'application/pdf',
}

# File extension mapping
MIME_TO_EXT: dict[str, str] = {
    'image/jpeg':      'jpg',
    'image/jpg':       'jpg',
    'image/png':       'png',
    'image/webp':      'webp',
    'application/pdf': 'pdf',
}

MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB


class AttachmentService:

    def process_incoming_media(
        self,
        user_id: str,
        whatsapp_media_id: str,
        mime_type: str,
    ):
        """
        Full pipeline: download from WhatsApp → validate → upload → link to transaction.
        Returns the created Attachment record.

        TODO: Implement in Sprint 4.
        """
        raise NotImplementedError("Sprint 4")

    def validate_file(self, file_bytes: bytes, mime_type: str) -> None:
        """
        Validate MIME type and file size.
        Raises ValueError with a user-friendly message if invalid.
        """
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Tipo de archivo no permitido: {mime_type}. "
                f"Se aceptan: JPG, PNG, WEBP, PDF."
            )
        size_mb = len(file_bytes) / (1024 * 1024)
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Archivo demasiado grande: {size_mb:.1f} MB. Máximo: 10 MB."
            )

    def generate_storage_path(self, user_id: str, mime_type: str) -> str:
        """
        Generate a unique, organized storage path.
        Format: {user_id}/{year}/{month:02d}/{uuid}.{ext}

        Example: 'abc123/2026/06/f47ac10b-58cc-4372-a567-0e02b2c3d479.jpg'
        """
        ext  = MIME_TO_EXT.get(mime_type, 'bin')
        now  = datetime.utcnow()
        uid  = str(uuid.uuid4())
        return f"{user_id}/{now.year}/{now.month:02d}/{uid}.{ext}"

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary signed URL for a private bucket file.
        Default expiry: 1 hour.

        TODO: Implement using StorageService in Sprint 4.
        """
        raise NotImplementedError("Sprint 4")

    def associate_to_transaction(
        self,
        attachment_id: str,
        transaction_id: str,
        user_id: str,
    ) -> bool:
        """
        Link an orphaned attachment to a specific transaction.
        Validates that both belong to the same user.
        Returns True if linked successfully.

        TODO: Implement in Sprint 4.
        """
        raise NotImplementedError("Sprint 4")

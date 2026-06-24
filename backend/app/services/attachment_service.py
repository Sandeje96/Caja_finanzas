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
        """
        # 1. Validate MIME early
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Tipo de archivo no permitido: {mime_type}. Se aceptan: JPG, PNG, WEBP, PDF.")
            
        from app.services.whatsapp_service import WhatsAppService
        whatsapp_service = WhatsAppService()
        
        # 2. Get download URL
        url = whatsapp_service.get_media_download_url(whatsapp_media_id)
        if not url:
            raise ValueError("No se pudo obtener el link de descarga desde WhatsApp.")
            
        # 3. Download bytes
        file_bytes = whatsapp_service.download_media(url)
        if not file_bytes:
            raise ValueError("Error al descargar el archivo desde WhatsApp.")
            
        # 4. Validate size & mime
        self.validate_file(file_bytes, mime_type)
        
        # 5. Generate storage path & upload
        storage_path = self.generate_storage_path(user_id, mime_type)
        
        from app.services.storage_service import StorageService
        storage_service = StorageService()
        storage_service.upload_file(file_bytes, storage_path, mime_type)
        
        # 6. Find recent transaction to associate
        from app.repositories.transaction_repository import TransactionRepository
        transaction_repo = TransactionRepository()
        recent_tx = transaction_repo.get_recent_without_attachment(user_id, hours=24)
        
        # 7. Persist Attachment
        from app.extensions import db
        from app.models.attachment import Attachment
        
        attachment = Attachment(
            user_id=user_id,
            transaction_id=recent_tx.id if recent_tx else None,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size=len(file_bytes),
            whatsapp_media_id=whatsapp_media_id,
            status='uploaded'
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        logger.info(f"[AttachmentService] Processed media {whatsapp_media_id} for user {user_id}. Linked to {recent_tx.id if recent_tx else 'None'}")
        return attachment

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
        """
        ext  = MIME_TO_EXT.get(mime_type, 'bin')
        now  = datetime.utcnow()
        uid  = str(uuid.uuid4())
        return f"{user_id}/{now.year}/{now.month:02d}/{uid}.{ext}"

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Generate a temporary signed URL for a private bucket file.
        """
        from app.services.storage_service import StorageService
        storage_service = StorageService()
        return storage_service.generate_signed_url(storage_path, expires_in=expires_in)

    def associate_to_transaction(
        self,
        attachment_id: str,
        transaction_id: str,
        user_id: str,
    ) -> bool:
        """
        Link an orphaned attachment to a specific transaction.
        """
        from app.models.attachment import Attachment
        from app.extensions import db
        from app.repositories.transaction_repository import TransactionRepository
        
        attachment = Attachment.query.get(attachment_id)
        if not attachment or str(attachment.user_id) != str(user_id):
            return False
            
        transaction_repo = TransactionRepository()
        t = transaction_repo.get_by_id(transaction_id)
        if not t or str(t.user_id) != str(user_id):
            return False
            
        attachment.transaction_id = t.id
        db.session.commit()
        return True

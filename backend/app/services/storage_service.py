"""
services/storage_service.py — Supabase Storage abstraction layer.

All file storage operations go through this service.
Using Supabase Storage (S3-compatible) with a PRIVATE bucket.
Access to files is only via signed URLs with short expiration.

TODO: Implement in Sprint 4.
"""
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class StorageService:
    """Abstraction over Supabase Storage (S3-compatible)."""

    def _get_client(self):
        from supabase import create_client
        url = current_app.config.get('SUPABASE_URL', '')
        key = current_app.config.get('SUPABASE_KEY', '')
        if not url or not key:
            logger.warning("[StorageService] SUPABASE_URL or SUPABASE_KEY not configured")
            raise ValueError("Configuración de Supabase faltante")
        return create_client(url, key)

    def upload_file(
        self,
        file_bytes: bytes,
        storage_path: str,
        mime_type: str,
        bucket: str = None,
    ) -> dict:
        """
        Upload a file to Supabase Storage.
        """
        bucket = bucket or current_app.config.get('SUPABASE_BUCKET_RECEIPTS', 'receipts')
        client = self._get_client()
        
        # supabase-py upload
        client.storage.from_(bucket).upload(
            file=file_bytes,
            path=storage_path,
            file_options={"content-type": mime_type}
        )
        
        logger.info(f"[StorageService] Uploaded {storage_path} to bucket {bucket}")
        return {'storage_path': storage_path, 'public_url': None}

    def generate_signed_url(
        self,
        storage_path: str,
        bucket: str = None,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a temporary signed URL for dashboard file preview/download.
        """
        bucket = bucket or current_app.config.get('SUPABASE_BUCKET_RECEIPTS', 'receipts')
        client = self._get_client()
        
        response = client.storage.from_(bucket).create_signed_url(storage_path, expires_in)
        # response is usually a dictionary containing 'signedURL'
        return response.get('signedURL', '') if isinstance(response, dict) else response

    def delete_file(self, storage_path: str, bucket: str = None) -> bool:
        """
        Delete a file from storage.
        """
        bucket = bucket or current_app.config.get('SUPABASE_BUCKET_RECEIPTS', 'receipts')
        client = self._get_client()
        
        response = client.storage.from_(bucket).remove([storage_path])
        return len(response) > 0

"""
services/storage_service.py — Supabase Storage abstraction layer.

All file storage operations go through this service.
Using Supabase Storage (S3-compatible) with a PRIVATE bucket.
Access to files is only via signed URLs with short expiration.

TODO: Implement in Sprint 4.
"""
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageService:
    """Abstraction over Supabase Storage (S3-compatible)."""

    def upload_file(
        self,
        file_bytes: bytes,
        storage_path: str,
        mime_type: str,
        bucket: str = None,
    ) -> dict:
        """
        Upload a file to Supabase Storage.

        Args:
            file_bytes: Raw file content
            storage_path: Destination path within bucket
            mime_type: Content-Type of the file
            bucket: Bucket name (defaults to SUPABASE_BUCKET_RECEIPTS from config)

        Returns:
            {'storage_path': str, 'public_url': None}  # private bucket → no public URL

        TODO: Implement in Sprint 4 using supabase-py client.
        """
        raise NotImplementedError("Sprint 4")

    def generate_signed_url(
        self,
        storage_path: str,
        bucket: str = None,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a temporary signed URL for dashboard file preview/download.

        Args:
            storage_path: Path within the bucket
            bucket: Bucket name
            expires_in: URL lifetime in seconds (default: 1 hour)

        Returns:
            Signed URL string

        TODO: Implement in Sprint 4.
        """
        raise NotImplementedError("Sprint 4")

    def delete_file(self, storage_path: str, bucket: str = None) -> bool:
        """
        Delete a file from storage.
        Returns True if deleted, False if not found or error.

        TODO: Implement in Sprint 4.
        """
        raise NotImplementedError("Sprint 4")

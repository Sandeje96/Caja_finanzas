import pytest
from unittest.mock import patch, MagicMock

from app.models.attachment import Attachment
from app.models.transaction import Transaction
from app.services.attachment_service import AttachmentService


@pytest.fixture
def attachment_service():
    return AttachmentService()


def test_validate_file_valid_mime(attachment_service):
    # Should not raise
    attachment_service.validate_file(b"dummy data", "image/jpeg")
    attachment_service.validate_file(b"dummy data", "application/pdf")

def test_validate_file_invalid_mime(attachment_service):
    with pytest.raises(ValueError, match="Tipo de archivo no permitido"):
        attachment_service.validate_file(b"dummy data", "text/plain")

def test_validate_file_size_exceeded(attachment_service):
    # 11 MB file
    big_file = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="Archivo demasiado grande"):
        attachment_service.validate_file(big_file, "image/jpeg")

@patch('app.services.whatsapp_service.WhatsAppService')
@patch('app.repositories.transaction_repository.TransactionRepository')
@patch('app.services.storage_service.StorageService')
@patch('app.extensions.db')
def test_process_incoming_media_orphan(mock_db, mock_storage_class, mock_repo_class, mock_whatsapp_class, attachment_service):
    mock_whatsapp = mock_whatsapp_class.return_value
    mock_whatsapp.get_media_download_url.return_value = "https://example.com/media"
    mock_whatsapp.download_media.return_value = b"image_data"
    
    mock_storage = mock_storage_class.return_value
    mock_storage.upload_file.return_value = {'storage_path': 'test_path', 'public_url': None}
    
    mock_repo = mock_repo_class.return_value
    mock_repo.get_recent_without_attachment.return_value = None
    
    attachment = attachment_service.process_incoming_media("user123", "media_123", "image/jpeg")
    
    assert attachment.user_id == "user123"
    assert attachment.transaction_id is None
    assert attachment.mime_type == "image/jpeg"
    assert attachment.whatsapp_media_id == "media_123"

@patch('app.services.whatsapp_service.WhatsAppService')
@patch('app.repositories.transaction_repository.TransactionRepository')
@patch('app.services.storage_service.StorageService')
@patch('app.extensions.db')
def test_process_incoming_media_associated(mock_db, mock_storage_class, mock_repo_class, mock_whatsapp_class, attachment_service):
    mock_whatsapp = mock_whatsapp_class.return_value
    mock_whatsapp.get_media_download_url.return_value = "https://example.com/media"
    mock_whatsapp.download_media.return_value = b"pdf_data"
    
    class FakeTx:
        id = "tx123"
        
    mock_repo = mock_repo_class.return_value
    mock_repo.get_recent_without_attachment.return_value = FakeTx()
    
    attachment = attachment_service.process_incoming_media("user123", "media_pdf", "application/pdf")
    
    assert attachment.user_id == "user123"
    assert attachment.transaction_id == "tx123"
    assert attachment.mime_type == "application/pdf"
    
@patch('app.services.storage_service.StorageService')
def test_get_signed_url(mock_storage_class, attachment_service):
    mock_storage = mock_storage_class.return_value
    mock_storage.generate_signed_url.return_value = "https://signed.url"
    
    url = attachment_service.get_signed_url("path/to/file.jpg")
    assert url == "https://signed.url"
    mock_storage.generate_signed_url.assert_called_once_with("path/to/file.jpg", expires_in=3600)

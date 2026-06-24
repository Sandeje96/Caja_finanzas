"""
services/receipt_search_service.py
"""
import logging
from app.repositories.transaction_repository import TransactionRepository
from app.services.attachment_service import AttachmentService

logger = logging.getLogger(__name__)

class ReceiptSearchService:
    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.attachment_service = AttachmentService()

    def search_receipts(self, user_id: str, merchant_name: str) -> str:
        if not merchant_name:
            return "Por favor, indicame el nombre del comercio para buscar el comprobante."
            
        attachments = self.transaction_repo.search_receipts_by_merchant(user_id, merchant_name)
        
        if not attachments:
            return f"No encontré comprobantes asociados a '{merchant_name}'."
            
        count = len(attachments)
        reply = f"Encontré {count} comprobante{'s' if count > 1 else ''} asociado{'s' if count > 1 else ''} a '{merchant_name}':\n"
        
        for i, att in enumerate(attachments[:5]):  # limit to top 5
            try:
                url = self.attachment_service.get_signed_url(att.storage_path)
                reply += f"\n📎 Comprobante {i+1}:\n{url}\n"
            except Exception as e:
                logger.error(f"Error generating URL for attachment {att.id}: {e}")
                reply += f"\n📎 Comprobante {i+1}: Error al generar el enlace.\n"
                
        if count > 5:
            reply += "\n(Mostrando los últimos 5 resultados)"
            
        return reply

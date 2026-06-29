"""
services/webhook_processor.py — Main orchestrator for WhatsApp webhook events.

This service is the brain of the application. It coordinates all other services
to process an incoming WhatsApp message end-to-end.
"""
import logging
import threading

from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.whatsapp_service import WhatsAppService
from app.utils.helpers import normalize_phone

logger = logging.getLogger(__name__)

_user_repo = UserRepository()
_conversation_service = ConversationService()
_whatsapp_service = WhatsAppService()


class WebhookProcessor:
    """
    Orchestrates the complete WhatsApp message processing pipeline.
    Instantiated once per request in the webhook endpoint.
    """

    def process_async(self, payload: dict) -> None:
        """
        Launch message processing in a background daemon thread.
        Returns immediately — caller (webhook endpoint) can respond 200 at once.
        """
        thread = threading.Thread(
            target=self._process_with_context,
            args=(payload,),
            daemon=True,
            name=f"webhook-{id(payload)}",
        )
        thread.start()
        logger.debug(f"[WebhookProcessor] Launched background thread {thread.name}")

    def _process_with_context(self, payload: dict) -> None:
        """Wraps _process inside a Flask app context for DB access in threads."""
        from app import create_app
        import os

        env = os.environ.get('FLASK_ENV', 'development')
        app = create_app(env)
        with app.app_context():
            self._process(payload)

    def _process(self, payload: dict) -> None:
        """
        Main pipeline. Runs inside a Flask app context.
        """
        import time
        start_time = time.time()
        
        # 1. Extract message data
        message_data = self._extract_message_data(payload)
        if not message_data:
            return

        phone = message_data['phone']
        whatsapp_message_id = message_data['message_id']
        msg_type = message_data['type']
        content = message_data['content']
        raw_payload = message_data['raw_payload']

        # 2. Deduplicate
        if _conversation_service.is_duplicate_message(whatsapp_message_id):
            logger.info(f"[WebhookProcessor] Duplicate message ignored: {whatsapp_message_id}")
            return

        # 3. Find or create user
        normalized_phone = normalize_phone(phone)
        user, created = _user_repo.find_or_create_by_phone(normalized_phone)
        if created:
            _user_repo.save()
            logger.info(f"[WebhookProcessor] Created new user: {normalized_phone}")

        # 4. Get or create active conversation
        conversation = _conversation_service.get_or_create_active_conversation(user.id)

        # 5. Persist incoming message
        user_msg = _conversation_service.save_user_message(
            conversation_id=conversation.id,
            content=content if content else f"[{msg_type} message]",
            message_type=msg_type,
            whatsapp_message_id=whatsapp_message_id,
            raw_payload=raw_payload
        )

        logger.info(f"[WebhookProcessor] Received {msg_type} from {normalized_phone}: {content}")

        # 6. AI Processing & Transaction Logic
        if msg_type == 'text' and content:
            reply_text = self._handle_text_message(user, conversation, user_msg, content)
        elif msg_type in ('image', 'document'):
            reply_text = self._handle_media_message(user, conversation, user_msg, msg_type, raw_payload)
        elif msg_type == 'audio':
            reply_text = self._handle_audio_message(user, conversation, user_msg, raw_payload)
        else:
            reply_text = "Por ahora solo puedo procesar mensajes de texto, imágenes, PDFs y audios."

        # 9. Persist assistant response message
        _conversation_service.save_assistant_message(conversation.id, reply_text)
        
        # 10. Send reply via WhatsAppService
        _whatsapp_service.send_text_message(normalized_phone, reply_text)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[WebhookProcessor] Processed message {user_msg.id} in {elapsed_ms}ms")


    def _extract_message_data(self, payload: dict) -> dict | None:
        """
        Extract relevant fields from a WhatsApp webhook payload.
        """
        try:
            entry = payload.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return None
                
            msg = messages[0]
            phone = msg.get('from')
            msg_id = msg.get('id')
            msg_type = msg.get('type')
            
            content = None
            if msg_type == 'text':
                content = msg.get('text', {}).get('body')
            elif msg_type == 'image':
                content = msg.get('image', {}).get('caption')
            elif msg_type == 'document':
                content = msg.get('document', {}).get('caption') or msg.get('document', {}).get('filename')
                
            return {
                'phone': phone,
                'message_id': msg_id,
                'type': msg_type,
                'content': content,
                'raw_payload': payload
            }
        except Exception as e:
            logger.warning(f"[WebhookProcessor] Failed to extract message data: {e}")
            return None

    def _handle_text_message(
        self,
        user,
        conversation,
        user_msg,
        content: str,
    ) -> str:
        text_lower = content.strip().lower()
        
        from app.services.transaction_service import TransactionService
        from app.services.pending_action_service import PendingActionService
        transaction_service = TransactionService()
        pending_action_service = PendingActionService()

        # Fast-path for simple confirmations without using AI
        if text_lower in ('ok', 'si', 'sí', 'dale', 'confirmar'):
            result = pending_action_service.resolve_last_action(str(user.id))
            if result:
                reply_text = f"✅ Acción confirmada y ejecutada correctamente."
                t = result.get('transaction')
                if t:
                    cat_name = t.category.name if t.category else 'Otros'
                    reply_text += f"\n\nMonto: ${float(t.amount):,.0f}\nCategoría: {cat_name}".replace(',', '.')
            else:
                reply_text = "No tenés ninguna acción pendiente de confirmación."
            return reply_text
            
        elif text_lower in ('no', 'cancelar', 'olvidalo'):
            if pending_action_service.cancel_last_action(str(user.id)):
                return "🚫 Acción cancelada. No se registró ningún cambio."
            else:
                return "No tenés ninguna acción pendiente para cancelar."
                
        # Main AI logic
        context = _conversation_service.build_ai_context(conversation.id)
        
        from app.services.ai_service import AIService
        ai_service = AIService()
        
        ai_result = ai_service.classify_intent(
            message=content,
            context=context,
            user_id=user.id,
            message_id=str(user_msg.id)
        )
        
        intent = ai_result.get('intent')
        confidence = ai_result.get('confidence', 0.0)
        entities = ai_result.get('entities', {})
        
        logger.info(f"[WebhookProcessor] Intent detectado: {intent} (conf: {confidence}) JSON recibido: {entities}")
        
        if intent in ('REGISTER_EXPENSE', 'REGISTER_INCOME'):
            amount = entities.get('amount')
            merchant = entities.get('merchant')
            desc = entities.get('description', '')
            category_name = entities.get('category')
            
            # Use description as merchant fallback if needed
            if not merchant and desc:
                merchant = desc
                
            if not amount:
                action_type = 'CONFIRM_EXPENSE' if intent == 'REGISTER_EXPENSE' else 'CONFIRM_INCOME'
                pending_action_service.create_action(
                    user_id=user.id,
                    action_type=action_type,
                    payload={
                        'description': desc,
                        'category': category_name,
                        'merchant': merchant,
                        'message_id': str(user_msg.id),
                        'confidence': confidence
                    }
                )
                return "¿De cuánto fue el monto exacto?"
                
            if confidence >= 0.80:
                if intent == 'REGISTER_EXPENSE':
                    t = transaction_service.create_expense(
                        user_id=user.id,
                        amount=amount,
                        description=desc,
                        category_name=category_name,
                        merchant=merchant,
                        message_id=user_msg.id,
                        ai_confidence=confidence
                    )
                    verb = "Gasto registrado"
                else:
                    t = transaction_service.create_income(
                        user_id=user.id,
                        amount=amount,
                        description=desc,
                        category_name=category_name,
                        message_id=user_msg.id,
                        ai_confidence=confidence
                    )
                    verb = "Ingreso registrado"
                    
                formatted_date = t.transaction_date.strftime('%d/%m/%Y')
                cat_name = t.category.name if t.category else 'Otros'
                formatted_amount = f"{float(t.amount):,.0f}".replace(',', '.')
                logger.info(f"[WebhookProcessor] Transacción creada exitosamente (ID: {t.id})")
                return f"✅ {verb}\n\nMonto: ${formatted_amount}\nCategoría: {cat_name}\nFecha: {formatted_date}"
            else:
                # Low confidence -> Create pending action
                action_type = 'CONFIRM_EXPENSE' if intent == 'REGISTER_EXPENSE' else 'CONFIRM_INCOME'
                verb = "gasto" if intent == 'REGISTER_EXPENSE' else "ingreso"
                pending_action_service.create_action(
                    user_id=user.id,
                    action_type=action_type,
                    payload={
                        'amount': amount,
                        'description': desc,
                        'category': category_name,
                        'merchant': merchant,
                        'message_id': str(user_msg.id),
                        'confidence': confidence
                    }
                )
                formatted_amount = f"{float(amount):,.0f}".replace(',', '.')
                return f"⚠️ Por favor confirmá este {verb}:\n\nMonto: ${formatted_amount}\nCategoría: {category_name or 'Otros'}\n\nRespondé OK para confirmar o NO para cancelar."
                
        elif intent == 'CONFIRM_TRANSACTION':
            result = pending_action_service.resolve_last_action(str(user.id))
            if result:
                return f"✅ Acción confirmada."
            else:
                return "No encontré ninguna acción pendiente para confirmar."
        elif intent == 'CANCEL_TRANSACTION':
            if pending_action_service.cancel_last_action(str(user.id)):
                return "🚫 Acción cancelada."
            else:
                return "No encontré ninguna acción pendiente para cancelar."
        elif intent == 'UPDATE_TRANSACTION':
            pending_action_service.create_action(
                user_id=user.id,
                action_type='UPDATE_TRANSACTION',
                payload={
                    'amount': entities.get('amount'),
                    'category': entities.get('category'),
                    'description': entities.get('description')
                }
            )
            return "¿Querés aplicar esta corrección al último movimiento?\nRespondé OK para confirmar."
        elif intent == 'DELETE_TRANSACTION':
            pending_action_service.create_action(
                user_id=user.id,
                action_type='DELETE_TRANSACTION',
                payload={}
            )
            return "⚠️ ¿Estás seguro que querés eliminar el último movimiento?\nRespondé OK para confirmar."
        elif intent == 'QUERY_RECENT':
            return transaction_service.get_recent_transactions_text(user.id, limit=5)
        elif intent == 'QUERY_RECEIPT':
            last_t = transaction_service.get_last_transaction(user.id)
            if not last_t:
                return "No tenés movimientos recientes."
            else:
                from app.models.attachment import Attachment
                att = Attachment.query.filter_by(transaction_id=last_t.id).filter(Attachment.deleted_at.is_(None)).first()
                if att:
                    from app.services.attachment_service import AttachmentService
                    url = AttachmentService().get_signed_url(att.storage_path)
                    return f"📎 Enlace temporal generado correctamente:\n\n{url}"
                else:
                    return "El último movimiento no tiene ningún comprobante asociado."
        elif intent == 'QUERY_RECEIPT_SEARCH':
            from app.services.receipt_search_service import ReceiptSearchService
            return ReceiptSearchService().search_receipts(str(user.id), entities.get('merchant'))
        elif intent in (
            'QUERY_MONTH_EXPENSES', 'QUERY_MONTH_INCOME', 'QUERY_BALANCE',
            'QUERY_CATEGORY_EXPENSES', 'QUERY_TOP_CATEGORY', 'QUERY_BIGGEST_EXPENSE',
            'QUERY_COMPARE_MONTHS', 'QUERY_DATE_EXPENSES'
        ):
            from app.services.financial_analytics_service import FinancialAnalyticsService
            return FinancialAnalyticsService().handle_query(str(user.id), intent, entities)
        else:
            return f"No entendí bien tu solicitud (Intent detectado: {intent}). Solo registro gastos e ingresos por ahora."


    def _handle_media_message(
        self,
        user,
        conversation,
        user_msg,
        msg_type: str,
        raw_payload: dict,
    ) -> str:
        media_id = None
        mime_type = None
        
        # The Meta webhook payload contains an array of messages.
        messages_array = raw_payload.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [])
        if messages_array:
            msg_obj = messages_array[0]
            if msg_type == 'image':
                media_id = msg_obj.get('image', {}).get('id')
                mime_type = msg_obj.get('image', {}).get('mime_type')
            elif msg_type == 'document':
                media_id = msg_obj.get('document', {}).get('id')
                mime_type = msg_obj.get('document', {}).get('mime_type')
        
        if not media_id or not mime_type:
            return "❌ No se pudo identificar el archivo adjunto."
            
        from app.services.attachment_service import AttachmentService
        attachment_service = AttachmentService()
        
        try:
            attachment = attachment_service.process_incoming_media(
                user_id=user.id,
                whatsapp_media_id=media_id,
                mime_type=mime_type
            )
            
            if attachment.transaction_id:
                return "✅ Comprobante asociado al último gasto correctamente."
            else:
                # Orphan attachment -> OCR Flow
                from app.services.ocr_service import OCRService
                from app.services.pending_action_service import PendingActionService
                from datetime import datetime, timezone
                
                ocr_service = OCRService()
                url = attachment_service.get_signed_url(attachment.storage_path)
                ocr_data, conf = ocr_service.analyze_receipt_from_url(url, str(user.id), str(user_msg.id))
                
                # Guardar metadatos OCR en attachment
                attachment.ocr_json = ocr_data
                attachment.ocr_confidence = conf
                attachment.ocr_processed_at = datetime.now(timezone.utc)
                
                from app.extensions import db
                if not ocr_data or conf < 0.80:
                    attachment.ocr_status = 'failed'
                    reply_text = "No pude interpretar correctamente el comprobante.\n¿Querés registrar el gasto manualmente?"
                else:
                    attachment.ocr_status = 'processed'
                    PendingActionService().create_action(
                        user_id=user.id,
                        action_type='OCR_CREATE_TRANSACTION',
                        payload={
                            'attachment_id': str(attachment.id),
                            'merchant': ocr_data.get('merchant'),
                            'amount': ocr_data.get('amount'),
                            'category': ocr_data.get('category'),
                            'date': ocr_data.get('date'),
                            'confidence': conf
                        }
                    )
                    amount_fmt = f"{float(ocr_data.get('amount', 0)):,.0f}".replace(',', '.')
                    reply_text = (
                        f"Detecté:\n"
                        f"Comercio: {ocr_data.get('merchant', 'Desconocido')}\n"
                        f"Monto: ${amount_fmt}\n"
                        f"Categoría: {ocr_data.get('category', 'Otros')}\n"
                        f"Fecha: {ocr_data.get('date', '')}\n\n"
                        f"¿Querés registrar este gasto? (Respondé Sí o No)"
                    )
                db.session.commit()
                return reply_text
        except ValueError as ve:
            return f"❌ Error: {str(ve)}"
        except Exception as e:
            logger.error(f"[WebhookProcessor] Error processing media: {e}", exc_info=True)
            return "❌ Ocurrió un error inesperado al procesar el archivo."

    def _handle_audio_message(
        self,
        user,
        conversation,
        user_msg,
        raw_payload: dict,
    ) -> str:
        logger.info(f"[WebhookProcessor] Recibido mensaje de audio (user: {user.id}). Stub para el futuro.")
        return "Todavía no puedo procesar notas de voz, ¡pero lo aprenderé pronto!"

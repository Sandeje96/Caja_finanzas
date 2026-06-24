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
            text_lower = content.strip().lower()
            
            from app.services.transaction_service import TransactionService
            transaction_service = TransactionService()

            # Fast-path for simple confirmations without using AI
            if text_lower in ('ok', 'si', 'sí', 'dale', 'confirmar'):
                t = transaction_service.confirm_last_transaction(user.id)
                if t:
                    reply_text = f"✅ Movimiento confirmado (${float(t.amount):,.0f})".replace(',', '.')
                else:
                    reply_text = "No tenés ningún movimiento reciente pendiente de confirmación."
            else:
                context = _conversation_service.build_ai_context(conversation.id)
                
                # Use AIService to classify intent and extract entities
                from app.services.ai_service import AIService
                ai_service = AIService()
                
                ai_result = ai_service.classify_intent(
                    message=content,
                    context=context,
                    user_id=str(user.id),
                    message_id=str(user_msg.id)
                )
                
                intent = ai_result.get('intent')
                confidence = ai_result.get('confidence', 0.0)
                entities = ai_result.get('entities', {})
                
                if intent in ('REGISTER_EXPENSE', 'REGISTER_INCOME'):
                    amount = entities.get('amount')
                    if not amount:
                        reply_text = "No logré detectar el monto. Por favor, indicalo nuevamente."
                    else:
                        category_name = entities.get('category')
                        desc = entities.get('description', '')
                        
                        if intent == 'REGISTER_EXPENSE':
                            t = transaction_service.create_expense(
                                user_id=user.id,
                                amount=amount,
                                description=desc,
                                category_name=category_name,
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
                        
                        if t.is_confirmed:
                            reply_text = f"✅ {verb}\n\nMonto: ${formatted_amount}\nCategoría: {cat_name}\nFecha: {formatted_date}"
                        else:
                            reply_text = f"⚠️ Por favor confirmá este {verb.lower()}:\n\nMonto: ${formatted_amount}\nCategoría: {cat_name}\nFecha: {formatted_date}\n\nRespondé OK para confirmar."
                elif intent == 'CONFIRM_TRANSACTION':
                    t = transaction_service.confirm_last_transaction(user.id)
                    if t:
                        reply_text = f"✅ Movimiento confirmado (${float(t.amount):,.0f})".replace(',', '.')
                    else:
                        reply_text = "No encontré ningún movimiento reciente para confirmar."
                elif intent == 'UPDATE_TRANSACTION':
                    amount = entities.get('amount')
                    category_name = entities.get('category')
                    desc = entities.get('description')
                    t = transaction_service.update_last_transaction(user.id, amount=amount, category_name=category_name, description=desc)
                    if t:
                        cat_name = t.category.name if t.category else 'Otros'
                        reply_text = f"✅ Movimiento actualizado y confirmado.\n\nMonto: ${float(t.amount):,.0f}\nCategoría: {cat_name}".replace(',', '.')
                    else:
                        reply_text = "No encontré ningún movimiento reciente para actualizar."
                elif intent == 'DELETE_TRANSACTION':
                    t = transaction_service.delete_last_transaction(user.id)
                    if t:
                        reply_text = f"🗑️ Movimiento eliminado (${float(t.amount):,.0f})".replace(',', '.')
                    else:
                        reply_text = "No encontré ningún movimiento reciente para eliminar."
                elif intent == 'QUERY_RECENT':
                    reply_text = transaction_service.get_recent_transactions_text(user.id, limit=5)
                elif intent == 'QUERY_RECEIPT':
                    last_t = transaction_service.get_last_transaction(user.id)
                    if not last_t:
                        reply_text = "No tenés movimientos recientes."
                    else:
                        from app.models.attachment import Attachment
                        att = Attachment.query.filter_by(transaction_id=last_t.id).filter(Attachment.deleted_at.is_(None)).first()
                        if att:
                            from app.services.attachment_service import AttachmentService
                            url = AttachmentService().get_signed_url(att.storage_path)
                            reply_text = f"📎 Enlace temporal generado correctamente:\n\n{url}"
                        else:
                            reply_text = "El último movimiento no tiene ningún comprobante asociado."
                else:
                    reply_text = f"No entendí bien tu solicitud (Intent detectado: {intent}). Solo registro gastos e ingresos por ahora."
        
        elif msg_type in ('image', 'document'):
            media_id = None
            mime_type = None
            
            # The Meta webhook payload contains an array of messages.
            # Extract the actual media_id and mime_type from the raw payload
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
                reply_text = "❌ No se pudo identificar el archivo adjunto."
            else:
                from app.services.attachment_service import AttachmentService
                attachment_service = AttachmentService()
                
                try:
                    attachment = attachment_service.process_incoming_media(
                        user_id=str(user.id),
                        whatsapp_media_id=media_id,
                        mime_type=mime_type
                    )
                    
                    if attachment.transaction_id:
                        reply_text = "✅ Comprobante asociado correctamente."
                    else:
                        reply_text = "📎 Comprobante guardado.\n\nNo encontré un gasto reciente para asociarlo.\nMás adelante podrás vincularlo manualmente."
                except ValueError as ve:
                    reply_text = f"❌ Error: {str(ve)}"
                except Exception as e:
                    logger.error(f"[WebhookProcessor] Error processing media: {e}", exc_info=True)
                    reply_text = "❌ Ocurrió un error inesperado al procesar el archivo."
        
        else:
            reply_text = "Por ahora solo puedo procesar mensajes de texto, imágenes y PDFs."

        # 9. Persist assistant response message
        _conversation_service.save_assistant_message(conversation.id, reply_text)
        
        # 10. Send reply via WhatsAppService
        _whatsapp_service.send_text_message(normalized_phone, reply_text)


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
        message_text: str,
        message_db_id: str,
    ) -> str:
        raise NotImplementedError("Sprint 3")

    def _handle_media_message(
        self,
        user,
        conversation,
        media_data: dict,
    ) -> str:
        raise NotImplementedError("Sprint 4")

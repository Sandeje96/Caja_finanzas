"""
services/pending_action_service.py — Gestor de acciones pendientes.

Maneja el ciclo de vida de operaciones que requieren confirmación humana.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.pending_action import PendingAction
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

# Action Types
ACTION_CONFIRM_EXPENSE     = 'CONFIRM_EXPENSE'
ACTION_CONFIRM_INCOME      = 'CONFIRM_INCOME'
ACTION_OCR_CREATE_EXPENSE  = 'OCR_CREATE_TRANSACTION'
ACTION_UPDATE_TRANSACTION  = 'UPDATE_TRANSACTION'
ACTION_DELETE_TRANSACTION  = 'DELETE_TRANSACTION'

_transaction_service = TransactionService()


class PendingActionService:

    def create_action(self, user_id: str, action_type: str, payload: dict, expires_in_hours: int = 24) -> PendingAction:
        """Crea una nueva acción pendiente de confirmación."""
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        
        action = PendingAction(
            user_id=user_id,
            action_type=action_type,
            payload_json=payload,
            expires_at=expires_at,
            status='pending'
        )
        db.session.add(action)
        db.session.commit()
        logger.info(f"[PendingActionService] Creada acción {action_type} para user {user_id}")
        return action

    def get_last_active_action(self, user_id: str) -> Optional[PendingAction]:
        """Obtiene la última acción pendiente y no expirada del usuario."""
        action = PendingAction.query.filter_by(user_id=user_id, status='pending').order_by(PendingAction.created_at.desc()).first()
        if action and action.mark_expired_if_needed():
            db.session.commit()
            return None
        return action

    def cancel_last_action(self, user_id: str) -> bool:
        """Cancela la última acción pendiente activa."""
        action = self.get_last_active_action(user_id)
        if not action:
            return False
            
        action.status = 'cancelled'
        action.resolved_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"[PendingActionService] Cancelada acción {action.action_type} (user {user_id})")
        return True

    def resolve_last_action(self, user_id: str) -> Optional[dict]:
        """
        Resuelve la última acción pendiente activa, ejecutándola.
        Retorna un dict con información de la ejecución o None si no hay acción activa.
        """
        action = self.get_last_active_action(user_id)
        if not action:
            return None
            
        action_type = action.action_type
        payload = action.payload_json
        
        result = {'action_type': action_type, 'payload': payload, 'transaction': None}
        
        try:
            if action_type == ACTION_CONFIRM_EXPENSE:
                t = _transaction_service.create_expense(
                    user_id=user_id,
                    amount=payload.get('amount'),
                    description=payload.get('description'),
                    category_name=payload.get('category'),
                    merchant=payload.get('merchant'),
                    message_id=payload.get('message_id'),
                    ai_confidence=payload.get('confidence')
                )
                result['transaction'] = t

            elif action_type == ACTION_CONFIRM_INCOME:
                t = _transaction_service.create_income(
                    user_id=user_id,
                    amount=payload.get('amount'),
                    description=payload.get('description'),
                    category_name=payload.get('category'),
                    message_id=payload.get('message_id'),
                    ai_confidence=payload.get('confidence')
                )
                result['transaction'] = t

            elif action_type == ACTION_OCR_CREATE_EXPENSE:
                t = _transaction_service.create_expense(
                    user_id=user_id,
                    amount=payload.get('amount'),
                    description=f"Ticket de {payload.get('merchant', 'comercio')}",
                    category_name=payload.get('category'),
                    merchant=payload.get('merchant'),
                    ai_confidence=payload.get('confidence')
                )
                result['transaction'] = t
                
                # Asignar el attachment
                attachment_id = payload.get('attachment_id')
                if attachment_id:
                    from app.models.attachment import Attachment
                    attachment = Attachment.query.get(attachment_id)
                    if attachment:
                        attachment.transaction_id = t.id

            elif action_type == ACTION_UPDATE_TRANSACTION:
                t = _transaction_service.update_last_transaction(
                    user_id=user_id,
                    amount=payload.get('amount'),
                    category_name=payload.get('category'),
                    description=payload.get('description')
                )
                result['transaction'] = t

            elif action_type == ACTION_DELETE_TRANSACTION:
                t = _transaction_service.delete_last_transaction(user_id)
                result['transaction'] = t

            else:
                logger.error(f"[PendingActionService] Tipo de acción desconocido: {action_type}")
                return None

            action.status = 'confirmed'
            action.resolved_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"[PendingActionService] Resuelta acción {action_type} (user {user_id})")
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"[PendingActionService] Error resolviendo acción {action.id}: {e}")
            raise

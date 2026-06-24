"""
services/conversation_service.py — Manages conversation lifecycle.

Responsible for:
- Creating and retrieving active conversations per user
- Persisting incoming (user) and outgoing (assistant) messages
- Building the AI context window from message history
- Deduplication check delegation
"""
import logging

from app.extensions import db
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)

_conversation_repo = ConversationRepository()
_message_repo = MessageRepository()


class ConversationService:
    """Manages the conversational state for each user."""

    def get_or_create_active_conversation(self, user_id: str) -> Conversation:
        """
        Return the current active conversation for a user.
        If none exists, create a new one.
        """
        conversation = _conversation_repo.get_active_for_user(user_id)
        if conversation:
            return conversation
        
        # Deactivate any previous active ones just in case
        _conversation_repo.deactivate_all_for_user(user_id)
        
        conversation = _conversation_repo.create(user_id=user_id, is_active=True)
        _conversation_repo.save()
        logger.info(f"[ConversationService] Created new active conversation for user {user_id}")
        return conversation

    def save_user_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = 'text',
        whatsapp_message_id: str = None,
        raw_payload: dict = None,
    ) -> Message:
        """
        Persist an incoming message from the WhatsApp user.
        Returns the created Message instance.
        """
        message = _message_repo.create(
            conversation_id=conversation_id,
            role='user',
            content=content or '',
            message_type=message_type,
            whatsapp_message_id=whatsapp_message_id,
            raw_payload=raw_payload
        )
        _message_repo.save()
        logger.debug(f"[ConversationService] Saved user message {whatsapp_message_id}")
        return message

    def save_assistant_message(self, conversation_id: str, content: str) -> Message:
        """
        Persist the AI assistant's response.
        Returns the created Message instance.
        """
        message = _message_repo.create(
            conversation_id=conversation_id,
            role='assistant',
            content=content,
            message_type='text'
        )
        _message_repo.save()
        return message

    def build_ai_context(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Build the messages array for the OpenAI API.
        Returns a list of {'role': ..., 'content': ...} dicts in chronological order.
        """
        messages = _message_repo.get_context_window(conversation_id, limit=limit)
        return [m.to_ai_context_dict() for m in messages]

    def is_duplicate_message(self, whatsapp_message_id: str) -> bool:
        """
        Check if a WhatsApp message has already been processed.
        Returns True if duplicate (should be discarded silently).
        """
        if not whatsapp_message_id:
            return False
        return _message_repo.is_duplicate(whatsapp_message_id)

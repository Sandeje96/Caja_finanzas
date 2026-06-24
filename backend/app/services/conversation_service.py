"""
services/conversation_service.py — Manages conversation lifecycle.

Responsible for:
- Creating and retrieving active conversations per user
- Persisting incoming (user) and outgoing (assistant) messages
- Building the AI context window from message history
- Deduplication check delegation

TODO: Implement in Sprint 2.
"""
import logging

from app.extensions import db
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)

_conversation_repo = ConversationRepository()
_message_repo = MessageRepository()


class ConversationService:
    """Manages the conversational state for each user."""

    def get_or_create_active_conversation(self, user_id: str):
        """
        Return the current active conversation for a user.
        If none exists, create a new one.

        TODO: Implement in Sprint 2.
        """
        raise NotImplementedError("Sprint 2")

    def save_user_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = 'text',
        whatsapp_message_id: str = None,
        raw_payload: dict = None,
    ):
        """
        Persist an incoming message from the WhatsApp user.
        Returns the created Message instance.

        TODO: Implement in Sprint 2.
        """
        raise NotImplementedError("Sprint 2")

    def save_assistant_message(self, conversation_id: str, content: str):
        """
        Persist the AI assistant's response.
        Returns the created Message instance.

        TODO: Implement in Sprint 2.
        """
        raise NotImplementedError("Sprint 2")

    def build_ai_context(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Build the messages array for the OpenAI API.
        Returns a list of {'role': ..., 'content': ...} dicts in chronological order.

        The limit is controlled by OPENAI_MAX_CONTEXT_MESSAGES in config.

        TODO: Implement in Sprint 3.
        """
        raise NotImplementedError("Sprint 3")

    def is_duplicate_message(self, whatsapp_message_id: str) -> bool:
        """
        Check if a WhatsApp message has already been processed.
        Returns True if duplicate (should be discarded silently).

        TODO: Implement in Sprint 2.
        """
        raise NotImplementedError("Sprint 2")

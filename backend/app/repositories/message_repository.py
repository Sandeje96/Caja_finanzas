"""repositories/message_repository.py"""
from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository):

    def __init__(self):
        super().__init__(Message)

    def find_by_whatsapp_id(self, whatsapp_message_id: str) -> Message | None:
        """
        Find a message by its WhatsApp message ID.
        Used for deduplication — if found, the webhook event has already been processed.
        """
        return Message.query.filter_by(
            whatsapp_message_id=whatsapp_message_id,
            deleted_at=None,
        ).first()

    def get_context_window(self, conversation_id: str, limit: int = 10) -> list[Message]:
        """
        Get the last N messages of a conversation for AI context.
        Returns messages in chronological order (oldest → newest).
        Only includes user and assistant messages (not system).
        """
        messages = (
            Message.query
            .filter(
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
                Message.role.in_(['user', 'assistant']),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        # Reverse to get chronological order for the AI prompt
        return list(reversed(messages))

    def get_by_conversation(self, conversation_id: str, page: int = 1, per_page: int = 50):
        """Get paginated messages for a conversation (dashboard view)."""
        return (
            Message.query
            .filter_by(conversation_id=conversation_id, deleted_at=None)
            .order_by(Message.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def is_duplicate(self, whatsapp_message_id: str) -> bool:
        """Quick check — True if the WhatsApp message ID already exists in DB."""
        return self.find_by_whatsapp_id(whatsapp_message_id) is not None

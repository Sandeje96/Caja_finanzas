"""repositories/conversation_repository.py"""
from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository):

    def __init__(self):
        super().__init__(Conversation)

    def get_active_for_user(self, user_id: str) -> Conversation | None:
        """
        Get the current active conversation for a user.
        Returns the most recent one if multiple are active (shouldn't happen).
        """
        return (
            Conversation.query
            .filter_by(user_id=user_id, is_active=True, deleted_at=None)
            .order_by(Conversation.created_at.desc())
            .first()
        )

    def deactivate_all_for_user(self, user_id: str) -> int:
        """
        Deactivate all active conversations for a user.
        Called before creating a new one.
        Returns number of rows affected.
        """
        result = (
            Conversation.query
            .filter_by(user_id=user_id, is_active=True, deleted_at=None)
            .update({'is_active': False})
        )
        return result

    def get_recent_for_user(self, user_id: str, limit: int = 10) -> list[Conversation]:
        """Get the N most recent conversations for a user."""
        return (
            Conversation.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

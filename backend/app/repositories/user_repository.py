"""repositories/user_repository.py"""
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(self):
        super().__init__(User)

    def find_by_phone(self, phone: str) -> User | None:
        """Find an active user by phone number (E.164 format, e.g. +5491112345678)."""
        return User.query.filter_by(phone=phone, deleted_at=None).first()

    def find_by_email(self, email: str) -> User | None:
        """Find an active user by email address (case-sensitive)."""
        return User.query.filter_by(email=email.lower(), deleted_at=None).first()

    def find_or_create_by_phone(self, phone: str, **defaults) -> tuple[User, bool]:
        """
        Find a user by phone or create one if not found.

        Args:
            phone: E.164 phone number
            **defaults: Additional fields to set when creating (name, timezone, etc.)

        Returns:
            (user, created): user instance and a bool indicating if it was just created
        """
        user = self.find_by_phone(phone)
        if user:
            return user, False

        user = self.create(phone=phone, **defaults)
        return user, True

    def get_active_users(self) -> list[User]:
        """Return all active users (not deleted, not deactivated)."""
        return User.query.filter_by(is_active=True, deleted_at=None).all()

"""repositories/category_repository.py"""
from sqlalchemy import or_

from app.models.category import Category
from app.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):

    def __init__(self):
        super().__init__(Category)

    def get_all_for_user(self, user_id: str) -> list[Category]:
        """
        Get all categories available to a user:
        - Global system categories (user_id IS NULL)
        - User-specific custom categories (user_id = <user_id>)

        Sorted alphabetically by name.
        """
        return (
            Category.query
            .filter(
                Category.deleted_at.is_(None),
                or_(
                    Category.user_id == user_id,
                    Category.user_id.is_(None),
                ),
            )
            .order_by(Category.name)
            .all()
        )

    def find_by_name(self, name: str, user_id: str = None) -> Category | None:
        """
        Find a category by exact name (case-insensitive).
        Checks both user-specific and global categories.
        """
        return (
            Category.query
            .filter(
                Category.deleted_at.is_(None),
                Category.name.ilike(name),
                or_(
                    Category.user_id == user_id,
                    Category.user_id.is_(None),
                ),
            )
            .first()
        )

    def find_best_match(self, name: str, user_id: str = None) -> Category | None:
        """
        Find the closest matching category by name.
        1. Tries exact match (case-insensitive)
        2. Falls back to partial match (ILIKE '%name%')

        Used by the AI to map extracted category strings to DB categories.
        """
        if not name:
            return None

        # Exact match first (more precise)
        exact = self.find_by_name(name, user_id)
        if exact:
            return exact

        # Partial match
        return (
            Category.query
            .filter(
                Category.deleted_at.is_(None),
                Category.name.ilike(f'%{name}%'),
                or_(
                    Category.user_id == user_id,
                    Category.user_id.is_(None),
                ),
            )
            .first()
        )

    def get_system_categories(self) -> list[Category]:
        """Get all global system categories (user_id IS NULL, is_system=True)."""
        return (
            Category.query
            .filter_by(is_system=True, user_id=None, deleted_at=None)
            .order_by(Category.name)
            .all()
        )

    def get_fallback_category(self, user_id: str = None) -> Category | None:
        """Return the 'Otros' catch-all category."""
        return self.find_by_name('Otros', user_id)

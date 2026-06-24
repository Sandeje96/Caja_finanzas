"""
repositories/base_repository.py — Generic CRUD base repository.

Pattern: API → Service → Repository → DB
Repositories are the ONLY layer that talks to SQLAlchemy directly.
Services never import db.session directly.
"""
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from app.extensions import db

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic repository providing common CRUD operations.

    Subclasses pass their model class to __init__:
        class UserRepository(BaseRepository):
            def __init__(self):
                super().__init__(User)
    """

    def __init__(self, model: type):
        self.model = model

    # ─── Read ─────────────────────────────────────────────────────────────────

    def get_by_id(self, record_id: Any) -> T | None:
        """Get a single active (non-deleted) record by UUID."""
        return self.model.query.filter_by(id=record_id, deleted_at=None).first()

    def get_all(self, **filters) -> list[T]:
        """
        Get all active records, optionally filtered by column=value pairs.

        Example:
            user_repo.get_all(is_active=True)
        """
        query = self.model.query.filter_by(deleted_at=None)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.all()

    def count(self, **filters) -> int:
        """Count active records matching the given filters."""
        query = self.model.query.filter_by(deleted_at=None)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.count()

    def exists(self, **filters) -> bool:
        """Return True if at least one active record matches the filters."""
        return self.count(**filters) > 0

    # ─── Write ────────────────────────────────────────────────────────────────

    def create(self, **kwargs) -> T:
        """
        Instantiate and persist a new record.
        Flushes (gets DB-generated ID) but does NOT commit.
        Call save() to commit.
        """
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.flush()
        return instance

    def update(self, instance: T, **kwargs) -> T:
        """
        Update fields on an existing record.
        Flushes but does NOT commit.
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.updated_at = datetime.now(timezone.utc)
        db.session.flush()
        return instance

    def soft_delete(self, instance: T) -> T:
        """
        Mark a record as deleted by setting deleted_at.
        Flushes but does NOT commit.
        """
        instance.soft_delete()
        db.session.flush()
        return instance

    # ─── Session management ───────────────────────────────────────────────────

    def save(self) -> None:
        """Commit the current session transaction."""
        db.session.commit()

    def rollback(self) -> None:
        """Roll back the current session transaction."""
        db.session.rollback()

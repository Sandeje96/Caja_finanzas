"""
extensions.py — Flask extension instances.

All extensions are instantiated here (without an app) so they can be
imported anywhere without circular dependencies. They are bound to the
app inside create_app() via the init_app() pattern.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Database ORM
db: SQLAlchemy = SQLAlchemy()

# Database migrations (Alembic wrapper)
migrate: Migrate = Migrate()

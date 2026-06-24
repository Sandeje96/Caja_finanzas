import logging
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')


def get_engine():
    """Get the SQLAlchemy engine from the Flask app."""
    try:
        # Flask-SQLAlchemy >= 3.0
        return current_app.extensions['migrate'].db.engine
    except (TypeError, AttributeError, KeyError):
        # Fallback
        return current_app.extensions['migrate'].db.get_engine()


def get_engine_url() -> str:
    """Get the database URL from Flask config."""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# Override alembic.ini sqlalchemy.url with the Flask app's DATABASE_URL
config.set_main_option('sqlalchemy.url', get_engine_url())

# SQLAlchemy metadata — used for autogenerate support
target_db = current_app.extensions['migrate'].db


def get_metadata():
    """Get the SQLAlchemy metadata from the Flask-Migrate extension."""
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL script without a live DB connection.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (default).
    Connects to the database and applies migrations.
    """
    def process_revision_directives(context, revision, directives):
        """Skip generating an empty migration when nothing has changed."""
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No schema changes detected — empty migration skipped.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get('process_revision_directives') is None:
        conf_args['process_revision_directives'] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

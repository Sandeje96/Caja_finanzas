"""
app/__init__.py — Flask application factory.

Usage:
    from app import create_app
    app = create_app('development')
"""
import logging
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from app.config import config
from app.extensions import db, migrate

logger = logging.getLogger(__name__)


def create_app(config_name: str = 'default') -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'production', 'testing', 'default'

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    _init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register standalone routes (health, error handlers)
    _register_routes(app)

    # Register Flask CLI commands
    _register_commands(app)

    logger.info(
        f"[App] Finanzas IA WhatsApp started — env={config_name}, "
        f"db={app.config['SQLALCHEMY_DATABASE_URI'][:40]}..."
    )
    return app


# ─── Private helpers ──────────────────────────────────────────────────────────

def _init_extensions(app: Flask) -> None:
    """Initialize and bind Flask extensions to the app."""
    # CORS: allow React frontend in dev; restrict in production via env
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Import all models BEFORE calling migrate.init_app so Alembic
    # can detect every table during autogenerate.
    import app.models.user          # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.message       # noqa: F401
    import app.models.category      # noqa: F401
    import app.models.transaction   # noqa: F401
    import app.models.attachment    # noqa: F401
    import app.models.ai_log        # noqa: F401

    db.init_app(app)
    migrate.init_app(app, db)


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints with their URL prefixes."""
    from app.api.webhook       import webhook_bp
    from app.api.auth          import auth_bp
    from app.api.transactions  import transactions_bp
    from app.api.categories    import categories_bp
    from app.api.attachments   import attachments_bp
    from app.api.conversations import conversations_bp
    from app.api.dashboard     import dashboard_bp

    app.register_blueprint(webhook_bp,       url_prefix='/api')
    app.register_blueprint(auth_bp,          url_prefix='/api/auth')
    app.register_blueprint(transactions_bp,  url_prefix='/api')
    app.register_blueprint(categories_bp,    url_prefix='/api')
    app.register_blueprint(attachments_bp,   url_prefix='/api')
    app.register_blueprint(conversations_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp,     url_prefix='/api')


def _register_routes(app: Flask) -> None:
    """Register standalone routes and error handlers."""

    @app.route('/api/health', methods=['GET'])
    def health():
        """
        Health check endpoint.
        Returns 200 if the service and database are reachable.
        Returns 503 if the database is unreachable.
        """
        db_status = 'ok'
        db_error = None

        try:
            db.session.execute(text('SELECT 1'))
        except Exception as exc:
            db_status = 'error'
            db_error = str(exc)
            logger.error(f"[Health] Database check failed: {exc}")

        overall = 'ok' if db_status == 'ok' else 'degraded'
        payload = {
            'status': overall,
            'service': 'finanzas-ia-whatsapp',
            'version': '0.1.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {
                'database': db_status,
            },
        }
        if db_error:
            payload['checks']['database_error'] = db_error

        http_code = 200 if overall == 'ok' else 503
        return jsonify(payload), http_code

    # ─── Error handlers ───────────────────────────────────────────────────────

    @app.errorhandler(400)
    def bad_request(exc):
        return jsonify({'error': 'Bad request', 'detail': str(exc)}), 400

    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        db.session.rollback()
        logger.error(f"[App] Unhandled exception: {exc}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def _register_commands(app: Flask) -> None:
    """Register Flask CLI commands accessible via `flask <command>`."""

    @app.cli.command('seed-db')
    def seed_db_command():
        """Seed the database with initial system categories."""
        from app.seeds import seed_categories
        with app.app_context():
            seed_categories()

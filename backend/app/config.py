"""
config.py — Application configuration classes.

Loaded via app factory: app.config.from_object(config[config_name])
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""

    # ─── Flask ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')

    # ─── SQLAlchemy ───────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://finanzas_user:finanzas_pass@localhost:5432/finanzas_ia',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_pre_ping': True,       # Detect stale connections
        'pool_recycle': 300,         # Recycle connections every 5 min
        'pool_size': 10,
        'max_overflow': 20,
    }

    # ─── JWT (Sprint 6) ───────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-CHANGE-IN-PRODUCTION')
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900))
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 604800))

    # ─── WhatsApp Cloud API ───────────────────────────────────────────────────
    WHATSAPP_TOKEN: str = os.environ.get('WHATSAPP_TOKEN', '')
    WHATSAPP_VERIFY_TOKEN: str = os.environ.get('WHATSAPP_VERIFY_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID: str = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_API_VERSION: str = os.environ.get('WHATSAPP_API_VERSION', 'v18.0')

    # ─── OpenAI (Sprint 3) ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL_FAST: str = os.environ.get('OPENAI_MODEL_FAST', 'gpt-4o-mini')
    OPENAI_MAX_CONTEXT_MESSAGES: int = int(os.environ.get('OPENAI_MAX_CONTEXT_MESSAGES', 10))

    # ─── Supabase Storage (Sprint 4) ──────────────────────────────────────────
    SUPABASE_URL: str = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.environ.get('SUPABASE_KEY', '')
    SUPABASE_BUCKET_RECEIPTS: str = os.environ.get('SUPABASE_BUCKET_RECEIPTS', 'receipts')

    # ─── App Defaults ─────────────────────────────────────────────────────────
    DEFAULT_TIMEZONE: str = os.environ.get('DEFAULT_TIMEZONE', 'America/Argentina/Buenos_Aires')
    DEFAULT_CURRENCY: str = os.environ.get('DEFAULT_CURRENCY', 'ARS')
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 30))


class DevelopmentConfig(Config):
    """Development-specific config. Debug enabled, verbose logging."""
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False  # Set True to log all SQL queries


class ProductionConfig(Config):
    """Production config. Debug disabled, strict security."""
    DEBUG: bool = False
    SQLALCHEMY_ECHO: bool = False

    def __init__(self):
        # Enforce required secrets in production
        required = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        for var in required:
            if not os.environ.get(var):
                raise RuntimeError(f"Missing required environment variable: {var}")


class TestingConfig(Config):
    """Testing config. Uses a separate test database."""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'TEST_DATABASE_URL',
        'postgresql://finanzas_user:finanzas_pass@localhost:5432/finanzas_ia_test',
    )
    SQLALCHEMY_ECHO: bool = False


config: dict = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}

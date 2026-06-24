"""Initial database schema — all tables for Finanzas IA WhatsApp MVP.

Creates:
  users, conversations, messages, categories,
  transactions, attachments, ai_logs

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-24 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision    = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on    = None


def upgrade() -> None:

    # ────────────────────────────────────────────────────────────────────────
    # USERS
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id',            postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('phone',         sa.String(20),  nullable=False),
        sa.Column('name',          sa.String(100), nullable=True),
        sa.Column('email',         sa.String(150), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('timezone',      sa.String(50),  nullable=False, server_default='America/Argentina/Buenos_Aires'),
        sa.Column('currency',      sa.String(10),  nullable=False, server_default='ARS'),
        sa.Column('is_active',     sa.Boolean(),   nullable=False, server_default=sa.true()),
        sa.Column('created_at',    sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at',    sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at',    sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('phone', name='uq_users_phone'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.execute("CREATE INDEX idx_users_phone ON users (phone) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_users_email ON users (email) WHERE deleted_at IS NULL")

    # ────────────────────────────────────────────────────────────────────────
    # CONVERSATIONS
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'conversations',
        sa.Column('id',        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id',   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_conversations_user_id'),
    )
    op.execute("CREATE INDEX idx_conversations_user_id ON conversations (user_id) WHERE deleted_at IS NULL")

    # ────────────────────────────────────────────────────────────────────────
    # MESSAGES
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'messages',
        sa.Column('id',                   postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('conversation_id',      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('whatsapp_message_id',  sa.String(100), nullable=True),
        sa.Column('role',                 sa.String(10),  nullable=False),
        sa.Column('content',              sa.Text(),      nullable=False),
        sa.Column('message_type',         sa.String(20),  nullable=False, server_default='text'),
        sa.Column('raw_payload',          postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='fk_messages_conversation_id'),
        sa.UniqueConstraint('whatsapp_message_id', name='uq_messages_whatsapp_message_id'),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')",                            name='check_message_role'),
        sa.CheckConstraint("message_type IN ('text', 'image', 'document', 'audio', 'video')",   name='check_message_type'),
    )
    op.execute("CREATE INDEX idx_messages_conversation_id ON messages (conversation_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_messages_whatsapp_id    ON messages (whatsapp_message_id) WHERE whatsapp_message_id IS NOT NULL")
    op.execute("CREATE INDEX idx_messages_created_at     ON messages (created_at DESC)")

    # ────────────────────────────────────────────────────────────────────────
    # CATEGORIES
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'categories',
        sa.Column('id',        postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id',   postgresql.UUID(as_uuid=True), nullable=True),   # NULL = global
        sa.Column('name',      sa.String(100), nullable=False),
        sa.Column('type',      sa.String(10),  nullable=False, server_default='both'),
        sa.Column('icon',      sa.String(50),  nullable=True),
        sa.Column('color',     sa.String(7),   nullable=True),
        sa.Column('is_system', sa.Boolean(),   nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_categories_user_id'),
        sa.CheckConstraint("type IN ('expense', 'income', 'both')", name='check_category_type'),
    )
    op.execute("CREATE INDEX idx_categories_user_id ON categories (user_id) WHERE deleted_at IS NULL")

    # ────────────────────────────────────────────────────────────────────────
    # TRANSACTIONS
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'transactions',
        sa.Column('id',               postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id',          postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id',      postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id',       postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type',             sa.String(20),      nullable=False),
        sa.Column('amount',           sa.Numeric(15, 2),  nullable=False),
        sa.Column('description',      sa.Text(),          nullable=True),
        sa.Column('notes',            sa.Text(),          nullable=True),
        sa.Column('transaction_date', sa.Date(),          nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('source',           sa.String(20),      nullable=False, server_default='whatsapp'),
        sa.Column('ai_confidence',    sa.Numeric(4, 3),   nullable=True),
        sa.Column('is_confirmed',     sa.Boolean(),       nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'],     ['users.id'],      name='fk_transactions_user_id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='fk_transactions_category_id'),
        sa.ForeignKeyConstraint(['message_id'],  ['messages.id'],   name='fk_transactions_message_id'),
        sa.CheckConstraint("type IN ('expense', 'income', 'transfer', 'adjustment')", name='check_transaction_type'),
        sa.CheckConstraint("source IN ('whatsapp', 'dashboard', 'import')",           name='check_transaction_source'),
        sa.CheckConstraint("amount > 0",                                               name='check_transaction_amount_positive'),
    )
    op.execute("CREATE INDEX idx_transactions_user_id    ON transactions (user_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_transactions_date       ON transactions (user_id, transaction_date DESC) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_transactions_type       ON transactions (user_id, type) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_transactions_category   ON transactions (category_id) WHERE deleted_at IS NULL AND category_id IS NOT NULL")

    # ────────────────────────────────────────────────────────────────────────
    # ATTACHMENTS
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'attachments',
        sa.Column('id',                 postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('transaction_id',     postgresql.UUID(as_uuid=True), nullable=True),   # nullable: orphaned receipts
        sa.Column('user_id',            postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storage_path',       sa.String(500), nullable=False),
        sa.Column('public_url',         sa.Text(),      nullable=True),
        sa.Column('file_name',          sa.String(255), nullable=True),
        sa.Column('mime_type',          sa.String(100), nullable=True),
        sa.Column('file_size',          sa.Integer(),   nullable=True),
        sa.Column('status',             sa.String(20),  nullable=False, server_default='uploaded'),
        sa.Column('whatsapp_media_id',  sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_attachments_transaction_id'),
        sa.ForeignKeyConstraint(['user_id'],        ['users.id'],        name='fk_attachments_user_id'),
        sa.CheckConstraint("status IN ('pending', 'uploaded', 'failed', 'processing')", name='check_attachment_status'),
    )
    op.execute("CREATE INDEX idx_attachments_transaction_id ON attachments (transaction_id) WHERE deleted_at IS NULL AND transaction_id IS NOT NULL")
    op.execute("CREATE INDEX idx_attachments_user_id        ON attachments (user_id) WHERE deleted_at IS NULL")

    # ────────────────────────────────────────────────────────────────────────
    # AI LOGS
    # ────────────────────────────────────────────────────────────────────────
    op.create_table(
        'ai_logs',
        sa.Column('id',                postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id',           postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id',        postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('intent',            sa.String(50),    nullable=True),
        sa.Column('prompt_tokens',     sa.Integer(),     nullable=True),
        sa.Column('completion_tokens', sa.Integer(),     nullable=True),
        sa.Column('total_tokens',      sa.Integer(),     nullable=True),
        sa.Column('model',             sa.String(50),    nullable=True),
        sa.Column('cost_usd',          sa.Numeric(10, 6), nullable=True),
        sa.Column('latency_ms',        sa.Integer(),     nullable=True),
        sa.Column('success',           sa.Boolean(),     nullable=False, server_default=sa.true()),
        sa.Column('error_message',     sa.Text(),        nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'],    ['users.id'],    name='fk_ai_logs_user_id'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name='fk_ai_logs_message_id'),
    )
    op.execute("CREATE INDEX idx_ai_logs_user_id    ON ai_logs (user_id) WHERE user_id IS NOT NULL")
    op.execute("CREATE INDEX idx_ai_logs_created_at ON ai_logs (created_at DESC)")


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table('ai_logs')
    op.drop_table('attachments')
    op.drop_table('transactions')
    op.drop_table('categories')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')

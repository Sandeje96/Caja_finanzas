"""add pending actions and ocr

Revision ID: 77cdd994f796
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 16:52:19.779069

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77cdd994f796'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Create pending_actions table
    op.create_table(
        'pending_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_pending_actions_user_id'), 'pending_actions', ['user_id'], unique=False)
    op.create_index(op.f('ix_pending_actions_status'), 'pending_actions', ['status'], unique=False)

    # Add OCR columns to attachments
    op.add_column('attachments', sa.Column('ocr_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('attachments', sa.Column('ocr_confidence', sa.Float(), nullable=True))
    op.add_column('attachments', sa.Column('ocr_processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('attachments', sa.Column('ocr_status', sa.String(length=20), nullable=True))

    # Drop is_confirmed from transactions
    op.drop_column('transactions', 'is_confirmed')


def downgrade() -> None:
    # Add back is_confirmed to transactions
    op.add_column('transactions', sa.Column('is_confirmed', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False))

    # Drop OCR columns from attachments
    op.drop_column('attachments', 'ocr_status')
    op.drop_column('attachments', 'ocr_processed_at')
    op.drop_column('attachments', 'ocr_confidence')
    op.drop_column('attachments', 'ocr_json')

    # Drop pending_actions table
    op.drop_index(op.f('ix_pending_actions_status'), table_name='pending_actions')
    op.drop_index(op.f('ix_pending_actions_user_id'), table_name='pending_actions')
    op.drop_table('pending_actions')

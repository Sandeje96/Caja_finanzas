"""add merchant column

Revision ID: 123456789abc
Revises: 77cdd994f796
Create Date: 2026-06-24 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '77cdd994f796'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('transactions', sa.Column('merchant', sa.String(length=255), nullable=True))

def downgrade():
    op.drop_column('transactions', 'merchant')

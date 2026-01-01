"""add refresh token

Revision ID: 005_add_refresh_token
Revises: 004_add_password_reset
Create Date: 2024-12-31 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_refresh_token'
down_revision = '004_add_password_reset'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add refresh_token and refresh_token_expires columns to users table
    op.add_column('users', sa.Column('refresh_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('refresh_token_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove refresh_token columns
    op.drop_column('users', 'refresh_token_expires')
    op.drop_column('users', 'refresh_token')


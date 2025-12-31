"""add two factor auth

Revision ID: 010_add_two_factor_auth
Revises: 009_add_tags
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_two_factor_auth'
down_revision = '009_add_tags'
branch_labels = None
depends_on = None


def upgrade():
    # Add 2FA fields to users table
    op.add_column('users', sa.Column('totp_secret', sa.String(), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    # Remove 2FA fields from users table
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')


"""add password reset tokens

Revision ID: 004_add_password_reset
Revises: 003_add_user_admin_role
Create Date: 2024-12-31 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_password_reset'
down_revision = '003_add_user_admin_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reset_token and reset_token_expires columns to users table
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove reset_token columns
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')


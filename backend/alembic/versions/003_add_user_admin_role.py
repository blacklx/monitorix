"""add user admin role

Revision ID: 003_add_user_admin_role
Revises: 002_add_performance_indexes
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_user_admin_role'
down_revision = '002_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Make the first user (if exists) an admin
    # This is done via application logic, but we ensure the column exists


def downgrade() -> None:
    # Remove is_admin column
    op.drop_column('users', 'is_admin')


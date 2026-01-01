"""add node verify_ssl

Revision ID: 011_add_node_verify_ssl
Revises: 010_add_two_factor_auth
Create Date: 2026-01-01 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_add_node_verify_ssl'
down_revision = '010_add_two_factor_auth'
branch_labels = None
depends_on = None


def upgrade():
    # Add verify_ssl column to nodes table
    # Default to True to maintain security by default
    op.add_column('nodes', sa.Column('verify_ssl', sa.Boolean(), nullable=False, server_default=sa.text('true')))


def downgrade():
    # Remove verify_ssl column from nodes table
    op.drop_column('nodes', 'verify_ssl')


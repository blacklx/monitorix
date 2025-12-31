"""Add tags to nodes and vms

Revision ID: 009_add_tags
Revises: 008_add_audit_logs
Create Date: 2024-12-31 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_tags'
down_revision = '008_add_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tags column to nodes table
    op.add_column('nodes', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add tags column to vms table
    op.add_column('vms', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Create index for tag filtering (using GIN index for JSON array queries)
    op.create_index('ix_nodes_tags', 'nodes', ['tags'], unique=False, postgresql_using='gin')
    op.create_index('ix_vms_tags', 'vms', ['tags'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ix_vms_tags', table_name='vms')
    op.drop_index('ix_nodes_tags', table_name='nodes')
    op.drop_column('vms', 'tags')
    op.drop_column('nodes', 'tags')


"""Add notification channels table

Revision ID: 006_add_notification_channels
Revises: 005_add_refresh_token
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_notification_channels'
down_revision = '005_add_refresh_token'
branch_labels = None
depends_on = None


def upgrade():
    # Create notification_channels table
    op.create_table(
        'notification_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('webhook_url', sa.String(), nullable=False),
        sa.Column('alert_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('severity_filter', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_channels_id'), 'notification_channels', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_notification_channels_id'), table_name='notification_channels')
    op.drop_table('notification_channels')


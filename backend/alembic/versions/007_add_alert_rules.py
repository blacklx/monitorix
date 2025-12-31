"""Add alert rules table

Revision ID: 007_add_alert_rules
Revises: 006_add_notification_channels
Create Date: 2024-12-31 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_alert_rules'
down_revision = '006_add_notification_channels'
branch_labels = None
depends_on = None


def upgrade():
    # Create alert_rules table
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('operator', sa.String(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False, server_default='warning'),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('vm_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['vm_id'], ['vms.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_id'), 'alert_rules', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_alert_rules_id'), table_name='alert_rules')
    op.drop_table('alert_rules')


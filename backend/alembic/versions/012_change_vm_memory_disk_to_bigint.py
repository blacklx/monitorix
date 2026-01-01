"""change vm memory disk to bigint

Revision ID: 012_change_vm_memory_disk_to_bigint
Revises: 011_add_node_verify_ssl
Create Date: 2026-01-01 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_change_vm_memory_disk_to_bigint'
down_revision = '011_add_node_verify_ssl'
branch_labels = None
depends_on = None


def upgrade():
    # Change memory_total and disk_total from INTEGER to BIGINT
    # This is necessary because large VMs can have memory/disk values
    # that exceed the INTEGER limit (2,147,483,647 bytes = ~2GB)
    op.alter_column('vms', 'memory_total',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False,
                    existing_server_default=sa.text('0'))
    op.alter_column('vms', 'disk_total',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False,
                    existing_server_default=sa.text('0'))


def downgrade():
    # Revert back to INTEGER (may fail if values exceed INTEGER limit)
    op.alter_column('vms', 'disk_total',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    existing_server_default=sa.text('0'))
    op.alter_column('vms', 'memory_total',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    existing_server_default=sa.text('0'))


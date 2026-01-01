"""Add performance indexes

Revision ID: 002_add_performance_indexes
Revises: 001_initial_schema
Create Date: 2024-12-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_performance_indexes'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Indexes for nodes table
    op.create_index('ix_nodes_status', 'nodes', ['status'], unique=False)
    op.create_index('ix_nodes_is_active', 'nodes', ['is_active'], unique=False)
    op.create_index('ix_nodes_maintenance_mode', 'nodes', ['maintenance_mode'], unique=False)
    op.create_index('ix_nodes_last_check', 'nodes', ['last_check'], unique=False)
    
    # Indexes for VMs table
    op.create_index('ix_vms_node_id', 'vms', ['node_id'], unique=False)
    op.create_index('ix_vms_status', 'vms', ['status'], unique=False)
    op.create_index('ix_vms_last_check', 'vms', ['last_check'], unique=False)
    
    # Indexes for services table
    op.create_index('ix_services_vm_id', 'services', ['vm_id'], unique=False)
    op.create_index('ix_services_is_active', 'services', ['is_active'], unique=False)
    op.create_index('ix_services_maintenance_mode', 'services', ['maintenance_mode'], unique=False)
    op.create_index('ix_services_type', 'services', ['type'], unique=False)
    
    # Indexes for health_checks table
    op.create_index('ix_health_checks_service_id', 'health_checks', ['service_id'], unique=False)
    op.create_index('ix_health_checks_status', 'health_checks', ['status'], unique=False)
    op.create_index('ix_health_checks_service_status', 'health_checks', ['service_id', 'status'], unique=False)
    
    # Indexes for metrics table
    op.create_index('ix_metrics_node_id', 'metrics', ['node_id'], unique=False)
    op.create_index('ix_metrics_vm_id', 'metrics', ['vm_id'], unique=False)
    op.create_index('ix_metrics_metric_type', 'metrics', ['metric_type'], unique=False)
    op.create_index('ix_metrics_node_type', 'metrics', ['node_id', 'metric_type'], unique=False)
    op.create_index('ix_metrics_vm_type', 'metrics', ['vm_id', 'metric_type'], unique=False)
    op.create_index('ix_metrics_recorded_type', 'metrics', ['recorded_at', 'metric_type'], unique=False)
    
    # Indexes for alerts table
    op.create_index('ix_alerts_is_resolved', 'alerts', ['is_resolved'], unique=False)
    op.create_index('ix_alerts_severity', 'alerts', ['severity'], unique=False)
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'], unique=False)
    op.create_index('ix_alerts_node_id', 'alerts', ['node_id'], unique=False)
    op.create_index('ix_alerts_vm_id', 'alerts', ['vm_id'], unique=False)
    op.create_index('ix_alerts_service_id', 'alerts', ['service_id'], unique=False)
    op.create_index('ix_alerts_resolved_created', 'alerts', ['is_resolved', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_alerts_resolved_created', table_name='alerts')
    op.drop_index('ix_alerts_service_id', table_name='alerts')
    op.drop_index('ix_alerts_vm_id', table_name='alerts')
    op.drop_index('ix_alerts_node_id', table_name='alerts')
    op.drop_index('ix_alerts_alert_type', table_name='alerts')
    op.drop_index('ix_alerts_severity', table_name='alerts')
    op.drop_index('ix_alerts_is_resolved', table_name='alerts')
    op.drop_index('ix_metrics_recorded_type', table_name='metrics')
    op.drop_index('ix_metrics_vm_type', table_name='metrics')
    op.drop_index('ix_metrics_node_type', table_name='metrics')
    op.drop_index('ix_metrics_metric_type', table_name='metrics')
    op.drop_index('ix_metrics_vm_id', table_name='metrics')
    op.drop_index('ix_metrics_node_id', table_name='metrics')
    op.drop_index('ix_health_checks_service_status', table_name='health_checks')
    op.drop_index('ix_health_checks_status', table_name='health_checks')
    op.drop_index('ix_health_checks_service_id', table_name='health_checks')
    op.drop_index('ix_services_type', table_name='services')
    op.drop_index('ix_services_maintenance_mode', table_name='services')
    op.drop_index('ix_services_is_active', table_name='services')
    op.drop_index('ix_services_vm_id', table_name='services')
    op.drop_index('ix_vms_last_check', table_name='vms')
    op.drop_index('ix_vms_status', table_name='vms')
    op.drop_index('ix_vms_node_id', table_name='vms')
    op.drop_index('ix_nodes_last_check', table_name='nodes')
    op.drop_index('ix_nodes_maintenance_mode', table_name='nodes')
    op.drop_index('ix_nodes_is_active', table_name='nodes')
    op.drop_index('ix_nodes_status', table_name='nodes')


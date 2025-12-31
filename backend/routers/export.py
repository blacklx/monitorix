from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from database import get_db
from models import Node, VM, Service, Alert
from auth import get_current_active_user
import csv
import json
import io

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/nodes/csv")
async def export_nodes_csv(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all nodes to CSV"""
    nodes = db.query(Node).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Name', 'URL', 'Username', 'Is Local', 'Is Active', 
        'Maintenance Mode', 'Status', 'Last Check', 'Created At', 'Updated At'
    ])
    
    for node in nodes:
        writer.writerow([
            node.id,
            node.name,
            node.url,
            node.username,
            node.is_local,
            node.is_active,
            node.maintenance_mode,
            node.status,
            node.last_check.isoformat() if node.last_check else '',
            node.created_at.isoformat() if node.created_at else '',
            node.updated_at.isoformat() if node.updated_at else ''
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=nodes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/nodes/json")
async def export_nodes_json(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all nodes to JSON"""
    nodes = db.query(Node).all()
    
    data = [{
        'id': node.id,
        'name': node.name,
        'url': node.url,
        'username': node.username,
        'is_local': node.is_local,
        'is_active': node.is_active,
        'maintenance_mode': node.maintenance_mode,
        'status': node.status,
        'last_check': node.last_check.isoformat() if node.last_check else None,
        'created_at': node.created_at.isoformat() if node.created_at else None,
        'updated_at': node.updated_at.isoformat() if node.updated_at else None
    } for node in nodes]
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=nodes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


@router.get("/vms/csv")
async def export_vms_csv(
    node_id: Optional[int] = Query(None, description="Filter by node ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all VMs to CSV"""
    query = db.query(VM)
    if node_id:
        query = query.filter(VM.node_id == node_id)
    vms = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Node ID', 'VM ID', 'Name', 'Status', 'CPU Cores', 
        'Memory (MB)', 'Disk (GB)', 'Uptime', 'Last Check', 'Created At', 'Updated At'
    ])
    
    for vm in vms:
        writer.writerow([
            vm.id,
            vm.node_id,
            vm.vm_id,
            vm.name,
            vm.status,
            vm.cpu_cores,
            vm.memory_mb,
            vm.disk_gb,
            vm.uptime,
            vm.last_check.isoformat() if vm.last_check else '',
            vm.created_at.isoformat() if vm.created_at else '',
            vm.updated_at.isoformat() if vm.updated_at else ''
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=vms_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/vms/json")
async def export_vms_json(
    node_id: Optional[int] = Query(None, description="Filter by node ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all VMs to JSON"""
    query = db.query(VM)
    if node_id:
        query = query.filter(VM.node_id == node_id)
    vms = query.all()
    
    data = [{
        'id': vm.id,
        'node_id': vm.node_id,
        'vm_id': vm.vm_id,
        'name': vm.name,
        'status': vm.status,
        'cpu_cores': vm.cpu_cores,
        'memory_mb': vm.memory_mb,
        'disk_gb': vm.disk_gb,
        'uptime': vm.uptime,
        'last_check': vm.last_check.isoformat() if vm.last_check else None,
        'created_at': vm.created_at.isoformat() if vm.created_at else None,
        'updated_at': vm.updated_at.isoformat() if vm.updated_at else None
    } for vm in vms]
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=vms_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


@router.get("/services/csv")
async def export_services_csv(
    vm_id: Optional[int] = Query(None, description="Filter by VM ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all services to CSV"""
    query = db.query(Service)
    if vm_id:
        query = query.filter(Service.vm_id == vm_id)
    services = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Name', 'Type', 'Target', 'Port', 'VM ID', 'Check Interval', 
        'Timeout', 'Expected Status', 'Is Active', 'Maintenance Mode', 
        'Custom Command', 'Created At', 'Updated At'
    ])
    
    for service in services:
        writer.writerow([
            service.id,
            service.name,
            service.type,
            service.target,
            service.port or '',
            service.vm_id or '',
            service.check_interval,
            service.timeout,
            service.expected_status,
            service.is_active,
            service.maintenance_mode,
            service.custom_command or '',
            service.created_at.isoformat() if service.created_at else '',
            service.updated_at.isoformat() if service.updated_at else ''
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=services_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/services/json")
async def export_services_json(
    vm_id: Optional[int] = Query(None, description="Filter by VM ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all services to JSON"""
    query = db.query(Service)
    if vm_id:
        query = query.filter(Service.vm_id == vm_id)
    services = query.all()
    
    data = [{
        'id': service.id,
        'name': service.name,
        'type': service.type,
        'target': service.target,
        'port': service.port,
        'vm_id': service.vm_id,
        'check_interval': service.check_interval,
        'timeout': service.timeout,
        'expected_status': service.expected_status,
        'is_active': service.is_active,
        'maintenance_mode': service.maintenance_mode,
        'custom_command': service.custom_command,
        'created_at': service.created_at.isoformat() if service.created_at else None,
        'updated_at': service.updated_at.isoformat() if service.updated_at else None
    } for service in services]
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=services_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


@router.get("/alerts/csv")
async def export_alerts_csv(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all alerts to CSV"""
    query = db.query(Alert)
    
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Alert Type', 'Severity', 'Message', 'Node ID', 'VM ID', 
        'Service ID', 'Is Resolved', 'Resolved At', 'Created At'
    ])
    
    for alert in alerts:
        writer.writerow([
            alert.id,
            alert.alert_type,
            alert.severity,
            alert.message,
            alert.node_id or '',
            alert.vm_id or '',
            alert.service_id or '',
            alert.is_resolved,
            alert.resolved_at.isoformat() if alert.resolved_at else '',
            alert.created_at.isoformat() if alert.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/alerts/json")
async def export_alerts_json(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all alerts to JSON"""
    query = db.query(Alert)
    
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    data = [{
        'id': alert.id,
        'alert_type': alert.alert_type,
        'severity': alert.severity,
        'message': alert.message,
        'node_id': alert.node_id,
        'vm_id': alert.vm_id,
        'service_id': alert.service_id,
        'is_resolved': alert.is_resolved,
        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
        'created_at': alert.created_at.isoformat() if alert.created_at else None
    } for alert in alerts]
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


@router.get("/all/csv")
async def export_all_csv(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all data (nodes, VMs, services, alerts) to CSV as separate sheets (ZIP)"""
    # For simplicity, we'll create a combined CSV with all data
    # In a production system, you might want to create a ZIP file with separate CSV files
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write nodes
    writer.writerow(['=== NODES ==='])
    writer.writerow([
        'ID', 'Name', 'URL', 'Username', 'Is Local', 'Is Active', 
        'Maintenance Mode', 'Status', 'Last Check', 'Created At', 'Updated At'
    ])
    nodes = db.query(Node).all()
    for node in nodes:
        writer.writerow([
            node.id, node.name, node.url, node.username, node.is_local,
            node.is_active, node.maintenance_mode, node.status,
            node.last_check.isoformat() if node.last_check else '',
            node.created_at.isoformat() if node.created_at else '',
            node.updated_at.isoformat() if node.updated_at else ''
        ])
    
    writer.writerow([])
    writer.writerow(['=== VMs ==='])
    writer.writerow([
        'ID', 'Node ID', 'VM ID', 'Name', 'Status', 'CPU Cores', 
        'Memory (MB)', 'Disk (GB)', 'Uptime', 'Last Check', 'Created At', 'Updated At'
    ])
    vms = db.query(VM).all()
    for vm in vms:
        writer.writerow([
            vm.id, vm.node_id, vm.vm_id, vm.name, vm.status,
            vm.cpu_cores, vm.memory_mb, vm.disk_gb, vm.uptime,
            vm.last_check.isoformat() if vm.last_check else '',
            vm.created_at.isoformat() if vm.created_at else '',
            vm.updated_at.isoformat() if vm.updated_at else ''
        ])
    
    writer.writerow([])
    writer.writerow(['=== SERVICES ==='])
    writer.writerow([
        'ID', 'Name', 'Type', 'Target', 'Port', 'VM ID', 'Check Interval', 
        'Timeout', 'Expected Status', 'Is Active', 'Maintenance Mode', 
        'Custom Command', 'Created At', 'Updated At'
    ])
    services = db.query(Service).all()
    for service in services:
        writer.writerow([
            service.id, service.name, service.type, service.target,
            service.port or '', service.vm_id or '', service.check_interval,
            service.timeout, service.expected_status, service.is_active,
            service.maintenance_mode, service.custom_command or '',
            service.created_at.isoformat() if service.created_at else '',
            service.updated_at.isoformat() if service.updated_at else ''
        ])
    
    writer.writerow([])
    writer.writerow(['=== ALERTS ==='])
    writer.writerow([
        'ID', 'Alert Type', 'Severity', 'Message', 'Node ID', 'VM ID', 
        'Service ID', 'Is Resolved', 'Resolved At', 'Created At'
    ])
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    for alert in alerts:
        writer.writerow([
            alert.id, alert.alert_type, alert.severity, alert.message,
            alert.node_id or '', alert.vm_id or '', alert.service_id or '',
            alert.is_resolved,
            alert.resolved_at.isoformat() if alert.resolved_at else '',
            alert.created_at.isoformat() if alert.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=monitorix_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/all/json")
async def export_all_json(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export all data (nodes, VMs, services, alerts) to JSON"""
    nodes = db.query(Node).all()
    vms = db.query(VM).all()
    services = db.query(Service).all()
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    
    data = {
        'export_date': datetime.utcnow().isoformat(),
        'nodes': [{
            'id': node.id,
            'name': node.name,
            'url': node.url,
            'username': node.username,
            'is_local': node.is_local,
            'is_active': node.is_active,
            'maintenance_mode': node.maintenance_mode,
            'status': node.status,
            'last_check': node.last_check.isoformat() if node.last_check else None,
            'created_at': node.created_at.isoformat() if node.created_at else None,
            'updated_at': node.updated_at.isoformat() if node.updated_at else None
        } for node in nodes],
        'vms': [{
            'id': vm.id,
            'node_id': vm.node_id,
            'vm_id': vm.vm_id,
            'name': vm.name,
            'status': vm.status,
            'cpu_cores': vm.cpu_cores,
            'memory_mb': vm.memory_mb,
            'disk_gb': vm.disk_gb,
            'uptime': vm.uptime,
            'last_check': vm.last_check.isoformat() if vm.last_check else None,
            'created_at': vm.created_at.isoformat() if vm.created_at else None,
            'updated_at': vm.updated_at.isoformat() if vm.updated_at else None
        } for vm in vms],
        'services': [{
            'id': service.id,
            'name': service.name,
            'type': service.type,
            'target': service.target,
            'port': service.port,
            'vm_id': service.vm_id,
            'check_interval': service.check_interval,
            'timeout': service.timeout,
            'expected_status': service.expected_status,
            'is_active': service.is_active,
            'maintenance_mode': service.maintenance_mode,
            'custom_command': service.custom_command,
            'created_at': service.created_at.isoformat() if service.created_at else None,
            'updated_at': service.updated_at.isoformat() if service.updated_at else None
        } for service in services],
        'alerts': [{
            'id': alert.id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'node_id': alert.node_id,
            'vm_id': alert.vm_id,
            'service_id': alert.service_id,
            'is_resolved': alert.is_resolved,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'created_at': alert.created_at.isoformat() if alert.created_at else None
        } for alert in alerts]
    }
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=monitorix_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


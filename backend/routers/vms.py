from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import VM, Node, Metric
from schemas import VMResponse
from auth import get_current_active_user
from uptime import calculate_service_uptime
from scheduler import sync_vms
from sqlalchemy import func, and_

router = APIRouter(prefix="/api/vms", tags=["vms"])


@router.get("", response_model=List[VMResponse])
async def get_vms(
    node_id: Optional[int] = Query(None, description="Filter by node ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all VMs, optionally filtered by node"""
    query = db.query(VM)
    if node_id:
        query = query.filter(VM.node_id == node_id)
    vms = query.all()
    return vms


@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific VM"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    return vm


@router.post("/{vm_id}/sync")
async def sync_vm(
    vm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Manually sync a VM from its node"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    node = db.query(Node).filter(Node.id == vm.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    await sync_vms(node)
    db.refresh(vm)
    return vm


@router.get("/{vm_id}/uptime")
async def get_vm_uptime(
    vm_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get uptime statistics for a VM"""
    from models import Metric
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get metrics data to track VM status over time
    # We use CPU metrics as a proxy for VM availability
    metrics_count = db.query(func.count()).filter(
        and_(
            Metric.vm_id == vm_id,
            Metric.metric_type == "cpu",
            Metric.recorded_at >= since
        )
    ).scalar() or 0
    
    # Expected checks (one per minute)
    expected_checks = hours * 60
    total_checks = min(metrics_count, expected_checks) if metrics_count > 0 else 1
    
    # Calculate online checks based on status and metrics
    if vm.status == "running" and vm.last_check and vm.last_check >= since:
        if metrics_count > 0:
            online_checks = metrics_count
        else:
            # VM is running but no metrics yet, assume online
            online_checks = 1
            total_checks = 1
    elif metrics_count > 0:
        # We have historical metrics
        online_checks = metrics_count
    else:
        # No data
        online_checks = 0
    
    # Calculate uptime percentage
    if total_checks > 0:
        uptime_percent = (online_checks / total_checks) * 100.0
    else:
        uptime_percent = 0.0
    
    downtime_minutes = ((total_checks - online_checks) / max(total_checks, 1)) * hours * 60
    
    return {
        "uptime_percent": uptime_percent,
        "downtime_minutes": downtime_minutes,
        "total_checks": total_checks,
        "online_checks": online_checks,
        "period_hours": hours
    }


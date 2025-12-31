from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
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
    node_id: Optional[int] = Query(None, description="Filter VMs by node ID"),
    tag: Optional[str] = Query(None, description="Filter VMs by tag name"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all virtual machines.
    
    Returns a list of all VMs across all nodes with their current status and resource usage.
    Optionally filter by node ID or tag.
    
    **Examples**:
    - `/api/vms?node_id=1` - Get all VMs on node 1
    - `/api/vms?tag=production` - Get all VMs tagged with "production"
    """
    query = db.query(VM).options(joinedload(VM.node))
    if node_id:
        query = query.filter(VM.node_id == node_id)
    if tag:
        # Filter VMs that have this tag in their tags array
        # PostgreSQL JSONB @> operator checks if array contains the value
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        query = query.filter(cast(VM.tags, JSONB).contains([tag]))
    vms = query.all()
    return vms


@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific VM"""
    vm = db.query(VM).options(joinedload(VM.node)).filter(VM.id == vm_id).first()
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
    vm = db.query(VM).options(joinedload(VM.node)).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    node = vm.node
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
    
    # Get actual metrics with timestamps to calculate real uptime
    actual_metrics = db.query(Metric).filter(
        and_(
            Metric.vm_id == vm_id,
            Metric.metric_type == "cpu",
            Metric.recorded_at >= since
        )
    ).order_by(Metric.recorded_at).all()
    
    if not actual_metrics:
        # No metrics data - use status and last_check
        if vm.status == "running" and vm.last_check and vm.last_check >= since:
            # VM is running and was checked recently
            time_since_check = (datetime.utcnow() - vm.last_check).total_seconds() / 60
            if time_since_check < 5:  # Checked within last 5 minutes
                online_checks = max(1, int((hours * 60) - time_since_check))
                total_checks = hours * 60
            else:
                online_checks = 0
                total_checks = hours * 60
        else:
            online_checks = 0
            total_checks = hours * 60
    else:
        # We have metrics data - calculate based on actual time coverage
        first_metric_time = actual_metrics[0].recorded_at
        last_metric_time = actual_metrics[-1].recorded_at
        
        # Count unique time periods (group by minute)
        unique_periods = set()
        for metric in actual_metrics:
            period_key = metric.recorded_at.replace(second=0, microsecond=0)
            unique_periods.add(period_key)
        
        online_checks = len(unique_periods)
        
        # Calculate total expected periods
        period_start = max(since, first_metric_time)
        period_end = min(datetime.utcnow(), last_metric_time)
        total_period_seconds = (period_end - period_start).total_seconds()
        total_expected_periods = max(1, int(total_period_seconds / 60))
        
        # If VM is currently running, extend the period to now
        if vm.status == "running" and vm.last_check and vm.last_check >= since:
            time_since_last_metric = (datetime.utcnow() - last_metric_time).total_seconds() / 60
            if time_since_last_metric < 5:  # Recent metric
                additional_periods = min(int(time_since_last_metric), int((datetime.utcnow() - period_start).total_seconds() / 60) - online_checks)
                online_checks += max(0, additional_periods)
        
        total_checks = max(online_checks, total_expected_periods)
    
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


from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import Metric
from schemas import MetricResponse
from auth import get_current_active_user
import csv
import json
import io

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=List[MetricResponse])
async def get_metrics(
    node_id: Optional[int] = None,
    vm_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get metrics with optional filters"""
    query = db.query(Metric)
    
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    if vm_id:
        query = query.filter(Metric.vm_id == vm_id)
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    # Filter by time range
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Metric.recorded_at >= since)
    
    metrics = query.order_by(Metric.recorded_at.desc()).limit(1000).all()
    return metrics


@router.get("/export/csv")
async def export_metrics_csv(
    node_id: Optional[int] = None,
    vm_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export metrics to CSV"""
    query = db.query(Metric)
    
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    if vm_id:
        query = query.filter(Metric.vm_id == vm_id)
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Metric.recorded_at >= since)
    
    metrics = query.order_by(Metric.recorded_at.asc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Node ID', 'VM ID', 'Metric Type', 'Value', 'Unit', 'Recorded At'])
    
    for metric in metrics:
        writer.writerow([
            metric.id,
            metric.node_id or '',
            metric.vm_id or '',
            metric.metric_type,
            metric.value,
            metric.unit,
            metric.recorded_at.isoformat()
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/export/json")
async def export_metrics_json(
    node_id: Optional[int] = None,
    vm_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export metrics to JSON"""
    query = db.query(Metric)
    
    if node_id:
        query = query.filter(Metric.node_id == node_id)
    if vm_id:
        query = query.filter(Metric.vm_id == vm_id)
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Metric.recorded_at >= since)
    
    metrics = query.order_by(Metric.recorded_at.asc()).all()
    
    # Convert to JSON
    data = [{
        'id': metric.id,
        'node_id': metric.node_id,
        'vm_id': metric.vm_id,
        'metric_type': metric.metric_type,
        'value': metric.value,
        'unit': metric.unit,
        'recorded_at': metric.recorded_at.isoformat()
    } for metric in metrics]
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
    )


from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database import get_db
from models import Metric
from schemas import MetricResponse
from auth import get_current_active_user
import csv
import json
import io

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def _aggregate_metrics(
    db: Session,
    node_id: Optional[int],
    vm_id: Optional[int],
    metric_type: Optional[str],
    since: datetime,
    aggregation_interval: str = "hour"
) -> List[Dict[str, Any]]:
    """
    Aggregate metrics by time interval (hour or day).
    
    Returns aggregated metrics with average, min, max values per interval.
    """
    # Build base query
    base_filter = [Metric.recorded_at >= since]
    if node_id:
        base_filter.append(Metric.node_id == node_id)
    if vm_id:
        base_filter.append(Metric.vm_id == vm_id)
    if metric_type:
        base_filter.append(Metric.metric_type == metric_type)
    
    # Group by time interval
    if aggregation_interval == "hour":
        # Group by hour: date_trunc('hour', recorded_at)
        time_expr = func.date_trunc('hour', Metric.recorded_at)
    else:  # day
        # Group by day: date_trunc('day', recorded_at)
        time_expr = func.date_trunc('day', Metric.recorded_at)
    
    # Aggregate query
    aggregated = db.query(
        Metric.node_id,
        Metric.vm_id,
        Metric.metric_type,
        Metric.unit,
        time_expr.label('time_bucket'),
        func.avg(Metric.value).label('avg_value'),
        func.min(Metric.value).label('min_value'),
        func.max(Metric.value).label('max_value'),
        func.count(Metric.id).label('sample_count')
    ).filter(
        and_(*base_filter)
    ).group_by(
        Metric.node_id,
        Metric.vm_id,
        Metric.metric_type,
        Metric.unit,
        time_expr
    ).order_by(
        time_expr.desc()
    ).all()
    
    # Convert to dict format
    result = []
    for row in aggregated:
        result.append({
            'node_id': row.node_id,
            'vm_id': row.vm_id,
            'metric_type': row.metric_type,
            'unit': row.unit,
            'value': float(row.avg_value),  # Use average as primary value
            'min_value': float(row.min_value),
            'max_value': float(row.max_value),
            'sample_count': row.sample_count,
            'recorded_at': row.time_bucket,
            'aggregated': True
        })
    
    return result


@router.get("", response_model=List[MetricResponse])
async def get_metrics(
    node_id: Optional[int] = Query(None, description="Filter metrics by node ID"),
    vm_id: Optional[int] = Query(None, description="Filter metrics by VM ID"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type (cpu, memory, disk)"),
    hours: int = Query(24, description="Number of hours of history to retrieve", ge=1, le=720),
    aggregate: bool = Query(True, description="Enable automatic aggregation for long time periods"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get metrics data with automatic aggregation for long time periods.
    
    Returns historical metrics data for nodes and VMs. Metrics include CPU usage,
    memory usage, and disk usage percentages.
    
    **Aggregation Strategy**:
    - Last 24 hours: Detailed metrics (every minute)
    - 24-168 hours (1 week): Hourly aggregation (average per hour)
    - > 168 hours (1 week): Daily aggregation (average per day)
    
    **Parameters**:
    - `hours`: Number of hours of history (1-720, default: 24)
    - `metric_type`: Filter by type: `cpu`, `memory`, or `disk`
    - `aggregate`: Enable automatic aggregation (default: true)
    
    **Examples**:
    - `/api/metrics?node_id=1&hours=48` - Get 48 hours of metrics for node 1 (hourly aggregated)
    - `/api/metrics?vm_id=5&metric_type=cpu&hours=12` - Get 12 hours of detailed CPU metrics for VM 5
    - `/api/metrics?node_id=1&hours=720&aggregate=true` - Get 30 days of daily aggregated metrics
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Determine aggregation strategy
    use_aggregation = aggregate and hours > 24
    
    if use_aggregation:
        # Use aggregation for long time periods
        if hours <= 168:  # Up to 1 week: hourly aggregation
            aggregation_interval = "hour"
        else:  # More than 1 week: daily aggregation
            aggregation_interval = "day"
        
        # Get aggregated metrics
        aggregated_metrics = _aggregate_metrics(
            db, node_id, vm_id, metric_type, since, aggregation_interval
        )
        
        # Also get recent detailed metrics (last 24 hours)
        recent_since = datetime.utcnow() - timedelta(hours=24)
        detailed_query = db.query(Metric).options(
            joinedload(Metric.node),
            joinedload(Metric.vm)
        )
        
        if node_id:
            detailed_query = detailed_query.filter(Metric.node_id == node_id)
        if vm_id:
            detailed_query = detailed_query.filter(Metric.vm_id == vm_id)
        if metric_type:
            detailed_query = detailed_query.filter(Metric.metric_type == metric_type)
        
        detailed_query = detailed_query.filter(
            Metric.recorded_at >= recent_since
        )
        detailed_metrics = detailed_query.order_by(Metric.recorded_at.desc()).limit(500).all()
        
        # Combine: detailed for recent, aggregated for older
        # Filter aggregated to exclude recent period
        aggregated_filtered = [
            m for m in aggregated_metrics
            if m['recorded_at'] < recent_since
        ]
        
        # Convert detailed metrics to response format
        detailed_response = [
            MetricResponse(
                id=metric.id,
                node_id=metric.node_id,
                vm_id=metric.vm_id,
                metric_type=metric.metric_type,
                value=metric.value,
                unit=metric.unit,
                recorded_at=metric.recorded_at
            ) for metric in detailed_metrics
        ]
        
        # Convert aggregated metrics to response format (use avg_value as value)
        aggregated_response = [
            MetricResponse(
                id=0,  # Aggregated metrics don't have IDs
                node_id=m['node_id'],
                vm_id=m['vm_id'],
                metric_type=m['metric_type'],
                value=m['value'],  # Average value
                unit=m['unit'],
                recorded_at=m['recorded_at']
            ) for m in aggregated_filtered
        ]
        
        # Combine and sort by time (newest first)
        all_metrics = detailed_response + aggregated_response
        all_metrics.sort(key=lambda x: x.recorded_at, reverse=True)
        
        return all_metrics[:1000]  # Limit total results
    else:
        # No aggregation: return detailed metrics
        query = db.query(Metric).options(
            joinedload(Metric.node),
            joinedload(Metric.vm)
        )
        
        if node_id:
            query = query.filter(Metric.node_id == node_id)
        if vm_id:
            query = query.filter(Metric.vm_id == vm_id)
        if metric_type:
            query = query.filter(Metric.metric_type == metric_type)
        
        query = query.filter(Metric.recorded_at >= since)
        
        # Adjust limit based on time period
        if hours <= 24:
            limit = 2000  # More detailed for short periods
        elif hours <= 168:
            limit = 1000
        else:
            limit = 500
        
        metrics = query.order_by(Metric.recorded_at.desc()).limit(limit).all()
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


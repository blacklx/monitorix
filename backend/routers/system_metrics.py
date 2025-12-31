"""
Copyright 2024 Monitorix Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import Metric
from auth import get_current_active_user, get_current_admin_user
from system_metrics import get_system_metrics, get_system_metrics_summary
from cache import get, set, get_cache_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system-metrics", tags=["system-metrics"])


@router.get("/current")
async def get_current_system_metrics(
    current_user = Depends(get_current_active_user)
):
    """
    Get current system metrics for the Monitorix backend server.
    
    Returns real-time CPU, memory, disk, network, and process metrics.
    This endpoint provides insight into the health and resource usage
    of the Monitorix application itself.
    """
    try:
        metrics = get_system_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {
            "error": "Failed to collect system metrics",
            "detail": str(e)
        }


@router.get("/summary")
async def get_system_metrics_summary_endpoint(
    current_user = Depends(get_current_active_user)
):
    """
    Get a summary of system metrics suitable for dashboard display.
    
    Returns key metrics (CPU%, Memory%, Disk%, etc.) in a simplified format.
    Results are cached for 10 seconds to reduce load.
    """
    cache_key = get_cache_key("system:metrics:summary")
    
    # Try cache first
    cached_summary = get(cache_key)
    if cached_summary:
        return cached_summary
    
    try:
        summary = get_system_metrics_summary()
        # Cache for 10 seconds
        set(cache_key, summary, ttl=10)
        return summary
    except Exception as e:
        logger.error(f"Error getting system metrics summary: {e}")
        return {
            "error": "Failed to collect system metrics summary",
            "detail": str(e)
        }


@router.get("/history")
async def get_system_metrics_history(
    hours: int = Query(24, description="Number of hours of history", ge=1, le=168),
    metric_type: Optional[str] = Query(None, description="Filter by metric type (cpu, memory, disk)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get historical system metrics.
    
    Returns stored system metrics from the database. System metrics are
    collected periodically and stored as regular metrics with node_id=None.
    
    **Parameters**:
    - `hours`: Number of hours of history (1-168, default: 24)
    - `metric_type`: Filter by type: `cpu`, `memory`, or `disk`
    
    **Examples**:
    - `/api/system-metrics/history?hours=48` - Get 48 hours of system metrics
    - `/api/system-metrics/history?metric_type=cpu&hours=12` - Get 12 hours of CPU metrics
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(Metric).filter(
        Metric.node_id.is_(None),
        Metric.vm_id.is_(None),
        Metric.recorded_at >= since
    )
    
    if metric_type:
        query = query.filter(Metric.metric_type == metric_type)
    
    metrics = query.order_by(Metric.recorded_at.desc()).limit(1000).all()
    
    return [
        {
            "id": m.id,
            "metric_type": m.metric_type,
            "value": m.value,
            "unit": m.unit,
            "recorded_at": m.recorded_at.isoformat()
        }
        for m in metrics
    ]


@router.post("/collect")
async def collect_system_metrics_now(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Manually trigger collection of system metrics (admin only).
    
    This endpoint forces immediate collection and storage of system metrics.
    Normally, metrics are collected automatically by the scheduler.
    """
    try:
        from system_metrics import get_system_metrics
        from models import Metric
        
        metrics = get_system_metrics()
        
        if "error" in metrics:
            return {
                "success": False,
                "error": metrics.get("error", "Unknown error")
            }
        
        # Store metrics in database
        timestamp = datetime.utcnow()
        
        # CPU metric
        cpu_metric = Metric(
            node_id=None,
            vm_id=None,
            metric_type="cpu",
            value=metrics["cpu"]["percent"],
            unit="percent",
            recorded_at=timestamp
        )
        db.add(cpu_metric)
        
        # Memory metric
        memory_metric = Metric(
            node_id=None,
            vm_id=None,
            metric_type="memory",
            value=metrics["memory"]["percent"],
            unit="percent",
            recorded_at=timestamp
        )
        db.add(memory_metric)
        
        # Disk metric
        disk_metric = Metric(
            node_id=None,
            vm_id=None,
            metric_type="disk",
            value=metrics["disk"]["percent"],
            unit="percent",
            recorded_at=timestamp
        )
        db.add(disk_metric)
        
        db.commit()
        
        # Invalidate cache
        from cache import delete_pattern
        delete_pattern("system:metrics:*")
        
        return {
            "success": True,
            "message": "System metrics collected and stored",
            "timestamp": timestamp.isoformat(),
            "metrics": {
                "cpu": metrics["cpu"]["percent"],
                "memory": metrics["memory"]["percent"],
                "disk": metrics["disk"]["percent"]
            }
        }
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


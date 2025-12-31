"""
Uptime calculation utilities
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models import Node, Service, HealthCheck, Metric
from datetime import datetime, timedelta
from typing import Dict, Optional


def calculate_node_uptime(db: Session, node_id: int, hours: int = 24) -> Dict:
    """
    Calculate uptime percentage for a node based on status checks and metrics
    
    Uses metrics data to track status over time for more accurate calculation.
    
    Returns:
        {
            "uptime_percent": float,
            "downtime_minutes": float,
            "total_checks": int,
            "online_checks": int,
            "period_hours": int
        }
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        return {
            "uptime_percent": 0.0,
            "downtime_minutes": 0.0,
            "total_checks": 0,
            "online_checks": 0,
            "period_hours": hours
        }
    
    # Get metrics data to track status over time
    # We use CPU metrics as a proxy for node availability
    # If CPU metrics exist, the node was online
    metrics = db.query(func.count()).filter(
        and_(
            Metric.node_id == node_id,
            Metric.metric_type == "cpu",
            Metric.recorded_at >= since
        )
    ).scalar() or 0
    
    # Get node checks from last_check timestamps
    # Count checks in the period (assuming checks every 60 seconds)
    expected_checks = hours * 60  # One check per minute
    total_checks = min(metrics, expected_checks)
    
    # If we have metrics, node was online for those periods
    # If node is currently online and we have recent data, count as online
    online_checks = 0
    if node.status == "online" and node.last_check and node.last_check >= since:
        # Node is currently online
        if metrics > 0:
            # We have metrics data, use that
            online_checks = metrics
        else:
            # No metrics but node is online, assume 100% if recent check
            online_checks = 1
            total_checks = 1
    elif metrics > 0:
        # We have historical metrics but node might be offline now
        online_checks = metrics
    else:
        # No data at all
        online_checks = 0
        total_checks = 1
    
    # Calculate uptime percentage
    if total_checks > 0:
        uptime_percent = (online_checks / total_checks) * 100.0
    else:
        uptime_percent = 0.0
    
    # Calculate downtime
    downtime_minutes = ((total_checks - online_checks) / max(total_checks, 1)) * hours * 60
    
    return {
        "uptime_percent": uptime_percent,
        "downtime_minutes": downtime_minutes,
        "total_checks": total_checks,
        "online_checks": online_checks,
        "period_hours": hours
    }


def calculate_service_uptime(db: Session, service_id: int, hours: int = 24) -> Dict:
    """
    Calculate uptime percentage for a service based on health checks
    
    Returns:
        {
            "uptime_percent": float,
            "downtime_minutes": float,
            "total_checks": int,
            "up_checks": int,
            "down_checks": int,
            "period_hours": int
        }
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all health checks in the period
    checks = db.query(HealthCheck).filter(
        and_(
            HealthCheck.service_id == service_id,
            HealthCheck.checked_at >= since
        )
    ).order_by(HealthCheck.checked_at).all()
    
    if not checks:
        return {
            "uptime_percent": 0.0,
            "downtime_minutes": 0.0,
            "total_checks": 0,
            "up_checks": 0,
            "down_checks": 0,
            "period_hours": hours
        }
    
    total_checks = len(checks)
    up_checks = sum(1 for check in checks if check.status == "up")
    down_checks = total_checks - up_checks
    
    if total_checks > 0:
        uptime_percent = (up_checks / total_checks) * 100.0
    else:
        uptime_percent = 0.0
    
    downtime_minutes = (down_checks / total_checks) * hours * 60 if total_checks > 0 else 0.0
    
    return {
        "uptime_percent": uptime_percent,
        "downtime_minutes": downtime_minutes,
        "total_checks": total_checks,
        "up_checks": up_checks,
        "down_checks": down_checks,
        "period_hours": hours
    }


def format_uptime(uptime_percent: float) -> str:
    """Format uptime percentage as a readable string"""
    if uptime_percent >= 99.9:
        return "99.9%"
    elif uptime_percent >= 99.0:
        return f"{uptime_percent:.2f}%"
    else:
        return f"{uptime_percent:.1f}%"


def format_downtime(downtime_minutes: float) -> str:
    """Format downtime in minutes as a readable string"""
    if downtime_minutes < 1:
        return f"{int(downtime_minutes * 60)}s"
    elif downtime_minutes < 60:
        return f"{int(downtime_minutes)}m"
    else:
        hours = int(downtime_minutes // 60)
        minutes = int(downtime_minutes % 60)
        return f"{hours}h {minutes}m"


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
    
    # Get actual metrics with timestamps to calculate real uptime
    # Use time intervals between metrics to determine actual uptime
    actual_metrics = db.query(Metric).filter(
        and_(
            Metric.node_id == node_id,
            Metric.metric_type == "cpu",
            Metric.recorded_at >= since
        )
    ).order_by(Metric.recorded_at).all()
    
    if not actual_metrics:
        # No metrics data - use status and last_check
        if node.status == "online" and node.last_check and node.last_check >= since:
            # Node is online and was checked recently
            # Estimate based on check interval (60 seconds)
            time_since_check = (datetime.utcnow() - node.last_check).total_seconds() / 60
            if time_since_check < 5:  # Checked within last 5 minutes
                online_checks = max(1, int((hours * 60) - time_since_check))
                total_checks = hours * 60
            else:
                # Last check was too long ago, can't determine
                online_checks = 0
                total_checks = hours * 60
        else:
            # Node is offline or no recent check
            online_checks = 0
            total_checks = hours * 60
    else:
        # We have metrics data - calculate based on actual time coverage
        first_metric_time = actual_metrics[0].recorded_at
        last_metric_time = actual_metrics[-1].recorded_at
        
        # Calculate time span covered by metrics
        period_start = max(since, first_metric_time)
        period_end = min(datetime.utcnow(), last_metric_time)
        
        # Count unique time periods (group by minute to avoid double counting)
        unique_periods = set()
        for metric in actual_metrics:
            # Round to minute to group metrics in same minute
            period_key = metric.recorded_at.replace(second=0, microsecond=0)
            unique_periods.add(period_key)
        
        online_checks = len(unique_periods)
        
        # Calculate total expected periods in the time range
        total_period_seconds = (period_end - period_start).total_seconds()
        total_expected_periods = max(1, int(total_period_seconds / 60))  # One per minute
        
        # If node is currently online, extend the period to now
        if node.status == "online" and node.last_check and node.last_check >= since:
            time_since_last_metric = (datetime.utcnow() - last_metric_time).total_seconds() / 60
            if time_since_last_metric < 5:  # Recent metric
                # Add periods from last metric to now
                additional_periods = min(int(time_since_last_metric), int((datetime.utcnow() - period_start).total_seconds() / 60) - online_checks)
                online_checks += max(0, additional_periods)
        
        total_checks = max(online_checks, total_expected_periods)
    
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


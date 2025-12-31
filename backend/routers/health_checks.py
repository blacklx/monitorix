from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import HealthCheck, Service
from schemas import HealthCheckResponse
from auth import get_current_active_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/health-checks", tags=["health-checks"])


@router.get("", response_model=List[HealthCheckResponse])
async def get_health_checks(
    service_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    hours: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get health check results"""
    query = db.query(HealthCheck).options(joinedload(HealthCheck.service))
    
    if service_id:
        query = query.filter(HealthCheck.service_id == service_id)
    if status:
        query = query.filter(HealthCheck.status == status)
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(HealthCheck.checked_at >= since)
    
    health_checks = query.order_by(HealthCheck.checked_at.desc()).limit(limit).all()
    return health_checks


@router.get("/latest/{service_id}", response_model=HealthCheckResponse)
async def get_latest_health_check(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get the latest health check for a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    health_check = db.query(HealthCheck).filter(
        HealthCheck.service_id == service_id
    ).order_by(HealthCheck.checked_at.desc()).first()
    
    if not health_check:
        raise HTTPException(status_code=404, detail="No health checks found for this service")
    
    return health_check


@router.get("/stats/{service_id}")
async def get_health_check_stats(
    service_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get health check statistics for a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    since = datetime.utcnow() - timedelta(hours=hours)
    checks = db.query(HealthCheck).filter(
        HealthCheck.service_id == service_id,
        HealthCheck.checked_at >= since
    ).all()
    
    total = len(checks)
    up = sum(1 for c in checks if c.status == "up")
    down = sum(1 for c in checks if c.status == "down")
    warning = sum(1 for c in checks if c.status == "warning")
    
    avg_response_time = None
    if checks:
        response_times = [c.response_time for c in checks if c.response_time is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
    
    return {
        "total_checks": total,
        "up": up,
        "down": down,
        "warning": warning,
        "uptime_percent": (up / total * 100) if total > 0 else 0,
        "avg_response_time": avg_response_time,
        "period_hours": hours
    }


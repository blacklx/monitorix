from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Node, VM, Service, HealthCheck, Alert
from schemas import DashboardStats
from auth import get_current_active_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get dashboard statistics.
    
    Returns an overview of system status including:
    - Total and online nodes
    - Total and running VMs
    - Total and healthy services
    - Active alerts count
    
    This endpoint is optimized for dashboard display and provides a quick
    overview of the entire monitoring system.
    """
    total_nodes = db.query(Node).count()
    online_nodes = db.query(Node).filter(Node.status == "online").count()
    
    total_vms = db.query(VM).count()
    running_vms = db.query(VM).filter(VM.status == "running").count()
    
    total_services = db.query(Service).filter(Service.is_active == True).count()
    
    # Get healthy services (last check was successful)
    recent_checks = db.query(HealthCheck).filter(
        HealthCheck.checked_at >= datetime.utcnow() - timedelta(minutes=5)
    ).subquery()
    
    healthy_services = db.query(Service).join(
        recent_checks, Service.id == recent_checks.c.service_id
    ).filter(recent_checks.c.status == "up").distinct().count()
    
    active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
    
    return DashboardStats(
        total_nodes=total_nodes,
        online_nodes=online_nodes,
        total_vms=total_vms,
        running_vms=running_vms,
        total_services=total_services,
        healthy_services=healthy_services,
        active_alerts=active_alerts
    )


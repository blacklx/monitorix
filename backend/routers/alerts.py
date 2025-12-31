from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Alert
from schemas import AlertResponse
from auth import get_current_active_user
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class BulkResolveRequest(BaseModel):
    alert_ids: List[int]


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status (true/false)"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (node_down, vm_down, service_down, high_usage)"),
    limit: int = Query(100, description="Maximum number of alerts to return", ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all alerts.
    
    Returns a list of alerts with optional filtering by resolved status, severity, or type.
    Results are ordered by creation date (most recent first).
    
    **Examples**:
    - `/api/alerts?resolved=false` - Get only unresolved alerts
    - `/api/alerts?severity=critical&limit=50` - Get top 50 critical alerts
    """
    query = db.query(Alert).options(
        joinedload(Alert.user)
    )
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts


@router.get("/stats")
async def get_alert_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get alert statistics"""
    total = db.query(Alert).count()
    unresolved = db.query(Alert).filter(Alert.is_resolved == False).count()
    critical = db.query(Alert).filter(
        Alert.severity == "critical",
        Alert.is_resolved == False
    ).count()
    warning = db.query(Alert).filter(
        Alert.severity == "warning",
        Alert.is_resolved == False
    ).count()
    
    return {
        "total": total,
        "unresolved": unresolved,
        "critical": critical,
        "warning": warning
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific alert"""
    alert = db.query(Alert).options(
        joinedload(Alert.user)
    ).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Mark an alert as resolved"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/bulk-resolve")
async def bulk_resolve_alerts(
    request: BulkResolveRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Mark multiple alerts as resolved"""
    alerts = db.query(Alert).filter(
        Alert.id.in_(request.alert_ids),
        Alert.is_resolved == False
    ).all()
    
    for alert in alerts:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
    
    db.commit()
    return {"resolved": len(alerts), "message": f"Resolved {len(alerts)} alerts"}


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()


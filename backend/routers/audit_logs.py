from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime, timedelta
from database import get_db
from models import AuditLog, User
from schemas import AuditLogResponse
from auth import get_current_admin_user
from sqlalchemy import and_, or_, func

router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get audit logs (admin only)"""
    query = db.query(AuditLog).options(
        joinedload(AuditLog.user)
    )
    
    # Filter by date range
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(AuditLog.created_at >= since)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id is not None:
        query = query.filter(AuditLog.resource_id == resource_id)
    if success is not None:
        query = query.filter(AuditLog.success == success)
    
    # Order by most recent first
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs


@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get audit log statistics (admin only)"""
    since = datetime.utcnow() - timedelta(days=days)
    
    total_logs = db.query(AuditLog).filter(AuditLog.created_at >= since).count()
    successful_logs = db.query(AuditLog).filter(
        and_(AuditLog.created_at >= since, AuditLog.success == True)
    ).count()
    failed_logs = db.query(AuditLog).filter(
        and_(AuditLog.created_at >= since, AuditLog.success == False)
    ).count()
    
    # Count by action
    actions = db.query(AuditLog.action, func.count(AuditLog.id)).filter(
        AuditLog.created_at >= since
    ).group_by(AuditLog.action).all()
    
    # Count by resource type
    resource_types = db.query(AuditLog.resource_type, func.count(AuditLog.id)).filter(
        AuditLog.created_at >= since
    ).group_by(AuditLog.resource_type).all()
    
    # Count by user
    users = db.query(AuditLog.username, func.count(AuditLog.id)).filter(
        AuditLog.created_at >= since
    ).group_by(AuditLog.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
    
    return {
        "total": total_logs,
        "successful": successful_logs,
        "failed": failed_logs,
        "actions": {action: count for action, count in actions},
        "resource_types": {rtype: count for rtype, count in resource_types},
        "top_users": {username or "System": count for username, count in users}
    }


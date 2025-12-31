"""
Audit logging utility for tracking user actions and system changes
"""
from sqlalchemy.orm import Session
from models import AuditLog, User
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    Log an action to the audit log
    
    Args:
        db: Database session
        user_id: ID of the user performing the action (None for system actions)
        action: Action type (create, update, delete, login, logout, etc.)
        resource_type: Type of resource (user, node, vm, service, etc.)
        resource_id: ID of the affected resource
        resource_name: Name of the affected resource
        changes: Dictionary with before/after values
        ip_address: IP address of the user
        user_agent: User agent string
        success: Whether the action was successful
        error_message: Error message if action failed
    """
    try:
        username = None
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                username = user.username
        
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")
        db.rollback()


def get_client_ip(request) -> Optional[str]:
    """Extract client IP address from request"""
    if hasattr(request, 'client') and request.client:
        return request.client.host
    return None


def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    if hasattr(request, 'headers'):
        return request.headers.get('user-agent')
    return None


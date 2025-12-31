"""
Webhook notification system
"""
import httpx
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from models import Webhook, Alert
import json

logger = logging.getLogger(__name__)


async def send_webhook(webhook: Webhook, payload: Dict) -> bool:
    """
    Send a webhook notification
    
    Args:
        webhook: Webhook configuration
        payload: Data to send
    
    Returns:
        True if webhook was sent successfully, False otherwise
    """
    if not webhook.is_active:
        return False
    
    try:
        headers = webhook.headers or {}
        headers.setdefault("Content-Type", "application/json")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method=webhook.method,
                url=webhook.url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Webhook {webhook.name} sent successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to send webhook {webhook.name}: {e}")
        return False


async def send_alert_webhooks(
    db: Session,
    alert: Alert,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    node_name: Optional[str] = None,
    vm_name: Optional[str] = None,
    service_name: Optional[str] = None
):
    """
    Send webhook notifications for an alert
    
    Args:
        db: Database session
        alert: Alert object
        alert_type: Type of alert
        severity: Alert severity
        title: Alert title
        message: Alert message
        node_name: Optional node name
        vm_name: Optional VM name
        service_name: Optional service name
    """
    # Get all active webhooks that should trigger for this alert type
    webhooks = db.query(Webhook).filter(Webhook.is_active == True).all()
    
    for webhook in webhooks:
        # Check if webhook should trigger for this alert type
        if webhook.alert_types:
            if alert_type not in webhook.alert_types:
                continue
        
        # Build payload
        payload = {
            "alert_id": alert.id,
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "timestamp": alert.created_at.isoformat() if alert.created_at else None,
            "node_name": node_name,
            "vm_name": vm_name,
            "service_name": service_name
        }
        
        # Send webhook
        await send_webhook(webhook, payload)


"""
Notification channels system (Slack, Discord)
"""
import httpx
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from models import NotificationChannel, Alert
import json

logger = logging.getLogger(__name__)


def get_severity_color(severity: str) -> str:
    """Get color code for severity"""
    colors = {
        "critical": "#dc3545",  # Red
        "warning": "#ffc107",   # Yellow/Orange
        "info": "#17a2b8"       # Blue
    }
    return colors.get(severity.lower(), "#6c757d")  # Default gray


def get_severity_emoji(severity: str) -> str:
    """Get emoji for severity"""
    emojis = {
        "critical": "🔴",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    return emojis.get(severity.lower(), "📢")


async def send_slack_notification(
    channel: NotificationChannel,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    node_name: Optional[str] = None,
    vm_name: Optional[str] = None,
    service_name: Optional[str] = None
) -> bool:
    """
    Send a notification to Slack
    
    Args:
        channel: Notification channel configuration
        alert_type: Type of alert
        severity: Alert severity
        title: Alert title
        message: Alert message
        node_name: Optional node name
        vm_name: Optional VM name
        service_name: Optional service name
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not channel.is_active:
        return False
    
    try:
        # Build Slack message payload
        color = get_severity_color(severity)
        emoji = get_severity_emoji(severity)
        
        # Build fields for Slack message
        fields = []
        if node_name:
            fields.append({
                "title": "Node",
                "value": node_name,
                "short": True
            })
        if vm_name:
            fields.append({
                "title": "VM",
                "value": vm_name,
                "short": True
            })
        if service_name:
            fields.append({
                "title": "Service",
                "value": service_name,
                "short": True
            })
        
        fields.append({
            "title": "Alert Type",
            "value": alert_type,
            "short": True
        })
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {title}",
                    "text": message,
                    "fields": fields,
                    "footer": "Monitorix",
                    "ts": int(__import__("time").time())
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                channel.webhook_url,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Slack notification sent successfully to {channel.name}")
            return True
    except Exception as e:
        logger.error(f"Failed to send Slack notification to {channel.name}: {e}")
        return False


async def send_discord_notification(
    channel: NotificationChannel,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    node_name: Optional[str] = None,
    vm_name: Optional[str] = None,
    service_name: Optional[str] = None
) -> bool:
    """
    Send a notification to Discord
    
    Args:
        channel: Notification channel configuration
        alert_type: Type of alert
        severity: Alert severity
        title: Alert title
        message: Alert message
        node_name: Optional node name
        vm_name: Optional VM name
        service_name: Optional service name
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not channel.is_active:
        return False
    
    try:
        # Build Discord embed payload
        color = int(get_severity_color(severity).replace("#", ""), 16)  # Convert hex to int
        emoji = get_severity_emoji(severity)
        
        # Build description with details
        description_parts = [message]
        if node_name:
            description_parts.append(f"**Node:** {node_name}")
        if vm_name:
            description_parts.append(f"**VM:** {vm_name}")
        if service_name:
            description_parts.append(f"**Service:** {service_name}")
        
        embed = {
            "title": f"{emoji} {title}",
            "description": "\n".join(description_parts),
            "color": color,
            "fields": [
                {
                    "name": "Alert Type",
                    "value": alert_type,
                    "inline": True
                },
                {
                    "name": "Severity",
                    "value": severity.upper(),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Monitorix"
            },
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        payload = {
            "embeds": [embed]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                channel.webhook_url,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Discord notification sent successfully to {channel.name}")
            return True
    except Exception as e:
        logger.error(f"Failed to send Discord notification to {channel.name}: {e}")
        return False


async def send_alert_notifications(
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
    Send notifications to all active notification channels for an alert
    
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
    # Get all active notification channels
    channels = db.query(NotificationChannel).filter(NotificationChannel.is_active == True).all()
    
    for channel in channels:
        # Check if channel should trigger for this alert type
        if channel.alert_types:
            if alert_type not in channel.alert_types:
                continue
        
        # Check if channel should trigger for this severity
        if channel.severity_filter:
            if severity not in channel.severity_filter:
                continue
        
        # Send notification based on channel type
        if channel.type == "slack":
            await send_slack_notification(
                channel=channel,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                node_name=node_name,
                vm_name=vm_name,
                service_name=service_name
            )
        elif channel.type == "discord":
            await send_discord_notification(
                channel=channel,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                node_name=node_name,
                vm_name=vm_name,
                service_name=service_name
            )


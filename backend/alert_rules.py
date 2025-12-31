"""
Alert rules evaluation system
"""
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import AlertRule, Alert, Metric, Node, VM, Service
from email_notifications import send_alert_notification
from webhooks import send_alert_webhooks
from notification_channels import send_alert_notifications

logger = logging.getLogger(__name__)


def evaluate_rule(rule: AlertRule, metric_value: float) -> bool:
    """
    Evaluate if an alert rule condition is met
    
    Args:
        rule: Alert rule to evaluate
        metric_value: Current metric value
    
    Returns:
        True if rule condition is met, False otherwise
    """
    operator = rule.operator
    threshold = rule.threshold
    
    if operator == ">":
        return metric_value > threshold
    elif operator == "<":
        return metric_value < threshold
    elif operator == ">=":
        return metric_value >= threshold
    elif operator == "<=":
        return metric_value <= threshold
    elif operator == "==":
        return abs(metric_value - threshold) < 0.01  # Float comparison
    else:
        logger.warning(f"Unknown operator: {operator}")
        return False


def check_cooldown(rule: AlertRule) -> bool:
    """
    Check if rule is in cooldown period
    
    Args:
        rule: Alert rule to check
    
    Returns:
        True if rule can trigger (not in cooldown), False otherwise
    """
    if not rule.last_triggered:
        return True
    
    cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
    return datetime.utcnow() > cooldown_end


async def evaluate_alert_rules(
    db: Session,
    metric_type: str,
    metric_value: float,
    node_id: Optional[int] = None,
    vm_id: Optional[int] = None,
    service_id: Optional[int] = None
):
    """
    Evaluate all applicable alert rules for a metric
    
    Args:
        db: Database session
        metric_type: Type of metric (cpu, memory, disk, response_time)
        metric_value: Current metric value
        node_id: Optional node ID
        vm_id: Optional VM ID
        service_id: Optional service ID
    """
    # Get all active rules for this metric type
    query = db.query(AlertRule).filter(
        AlertRule.is_active == True,
        AlertRule.metric_type == metric_type
    )
    
    # Filter by scope (node, vm, service, or global)
    if node_id:
        # Rules for this specific node or global rules
        query = query.filter(
            (AlertRule.node_id == node_id) | (AlertRule.node_id.is_(None))
        )
    else:
        # Only global rules
        query = query.filter(AlertRule.node_id.is_(None))
    
    if vm_id:
        query = query.filter(
            (AlertRule.vm_id == vm_id) | (AlertRule.vm_id.is_(None))
        )
    else:
        query = query.filter(AlertRule.vm_id.is_(None))
    
    if service_id:
        query = query.filter(
            (AlertRule.service_id == service_id) | (AlertRule.service_id.is_(None))
        )
    else:
        query = query.filter(AlertRule.service_id.is_(None))
    
    rules = query.all()
    
    for rule in rules:
        # Check cooldown
        if not check_cooldown(rule):
            continue
        
        # Evaluate rule condition
        if evaluate_rule(rule, metric_value):
            # Check if alert already exists
            existing_alert = db.query(Alert).filter(
                Alert.alert_type == "high_usage",
                Alert.is_resolved == False,
                Alert.node_id == (node_id if node_id else None),
                Alert.vm_id == (vm_id if vm_id else None),
                Alert.service_id == (service_id if service_id else None)
            ).first()
            
            if existing_alert:
                continue  # Alert already exists, skip
            
            # Create alert
            node_name = None
            vm_name = None
            service_name = None
            
            if node_id:
                node = db.query(Node).filter(Node.id == node_id).first()
                if node:
                    node_name = node.name
            
            if vm_id:
                vm = db.query(VM).filter(VM.id == vm_id).first()
                if vm:
                    vm_name = vm.name
            
            if service_id:
                service = db.query(Service).filter(Service.id == service_id).first()
                if service:
                    service_name = service.name
            
            # Build alert message
            title = f"{rule.name} - {metric_type.upper()} threshold exceeded"
            message = f"{metric_type.upper()} is {metric_value:.2f}% (threshold: {rule.operator} {rule.threshold}%)"
            
            if node_name:
                message += f" on node {node_name}"
            if vm_name:
                message += f" (VM: {vm_name})"
            if service_name:
                message += f" (Service: {service_name})"
            
            alert = Alert(
                alert_type="high_usage",
                severity=rule.severity,
                title=title,
                message=message,
                node_id=node_id,
                vm_id=vm_id,
                service_id=service_id
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # Update rule last_triggered
            rule.last_triggered = datetime.utcnow()
            db.commit()
            
            # Send notifications
            send_alert_notification(
                alert_type="high_usage",
                severity=rule.severity,
                title=title,
                message=message,
                node_name=node_name,
                vm_name=vm_name,
                service_name=service_name
            )
            
            await send_alert_webhooks(
                db=db,
                alert=alert,
                alert_type="high_usage",
                severity=rule.severity,
                title=title,
                message=message,
                node_name=node_name,
                vm_name=vm_name,
                service_name=service_name
            )
            
            await send_alert_notifications(
                db=db,
                alert=alert,
                alert_type="high_usage",
                severity=rule.severity,
                title=title,
                message=message,
                node_name=node_name,
                vm_name=vm_name,
                service_name=service_name
            )
            
            # Broadcast alert via WebSocket (import from scheduler)
            try:
                from scheduler import _broadcast_update
                if _broadcast_update:
                    await _broadcast_update("alert", {
                        "id": alert.id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "title": alert.title,
                        "message": alert.message,
                        "node_id": alert.node_id,
                        "vm_id": alert.vm_id,
                        "service_id": alert.service_id,
                        "created_at": alert.created_at.isoformat() if alert.created_at else None
                    })
            except Exception as e:
                logger.error(f"Failed to broadcast alert: {e}")
            
            logger.info(f"Alert rule '{rule.name}' triggered: {message}")


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Node, VM, Service, HealthCheck, Metric, Alert
from proxmox_client import ProxmoxClient
from health_checks import HealthChecker
from email_notifications import send_alert_notification
from webhooks import send_alert_webhooks
from notification_channels import send_alert_notifications
from alert_rules import evaluate_alert_rules
from cache import invalidate_cache
from datetime import datetime
import logging
from typing import Dict, List
import asyncio

# Import broadcast function from main (will be set dynamically)
_broadcast_update = None

def set_broadcast_function(broadcast_func):
    """Set the broadcast function from main.py"""
    global _broadcast_update
    _broadcast_update = broadcast_func

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_node(node: Node) -> Dict:
    """Check a single Proxmox node"""
    db = SessionLocal()
    try:
        # Skip check if in maintenance mode
        if node.maintenance_mode:
            logger.debug(f"Node {node.name} is in maintenance mode, skipping check")
            return {"status": "maintenance"}
        
        client = ProxmoxClient(node.url, node.username, node.token)
        
        # Test connection
        if not client.test_connection():
            was_online = node.status == "online"
            node.status = "offline"
            node.last_check = datetime.utcnow()
            db.commit()
            
            # Send email notification if node just went offline
            if was_online:
                # Create alert
                alert = Alert(
                    alert_type="node_down",
                    severity="critical",
                    title=f"Node {node.name} is offline",
                    message=f"Node {node.name} is no longer responding",
                    node_id=node.id
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                
                send_alert_notification(
                    alert_type="node_down",
                    severity="critical",
                    title=f"Node {node.name} is offline",
                    message=f"Node {node.name} is no longer responding",
                    node_name=node.name
                )
                
                # Send webhook notifications
                await send_alert_webhooks(
                    db=db,
                    alert=alert,
                    alert_type="node_down",
                    severity="critical",
                    title=f"Node {node.name} is offline",
                    message=f"Node {node.name} is no longer responding",
                    node_name=node.name
                )
                
                # Send notification channel notifications (Slack, Discord)
                await send_alert_notifications(
                    db=db,
                    alert=alert,
                    alert_type="node_down",
                    severity="critical",
                    title=f"Node {node.name} is offline",
                    message=f"Node {node.name} is no longer responding",
                    node_name=node.name
                )
            
            return {"status": "offline"}
        
        # Get node status
        node_status = client.get_node_status()
        node.status = node_status.get("status", "unknown")
        node.last_check = datetime.utcnow()
        
        # Store metrics
        if node_status.get("status") == "online":
            # Store CPU metric
            metric_cpu = Metric(
                node_id=node.id,
                metric_type="cpu",
                value=node_status.get("cpu_usage", 0),
                unit="percent"
            )
            db.add(metric_cpu)
            
            # Store memory metric
            metric_memory = Metric(
                node_id=node.id,
                metric_type="memory",
                value=node_status.get("memory_usage", 0),
                unit="percent"
            )
            db.add(metric_memory)
            
            # Store disk metric
            metric_disk = Metric(
                node_id=node.id,
                metric_type="disk",
                value=node_status.get("disk_usage", 0),
                unit="percent"
            )
            db.add(metric_disk)
            
            # Evaluate alert rules for node metrics
            if node_status.get("cpu_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="cpu",
                    metric_value=node_status.get("cpu_usage", 0),
                    node_id=node.id
                )
            
            if node_status.get("memory_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="memory",
                    metric_value=node_status.get("memory_usage", 0),
                    node_id=node.id
                )
            
            if node_status.get("disk_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="disk",
                    metric_value=node_status.get("disk_usage", 0),
                    node_id=node.id
                )
        
        db.commit()
            
            # Evaluate alert rules for node metrics
            if node_status.get("cpu_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="cpu",
                    metric_value=node_status.get("cpu_usage", 0),
                    node_id=node.id
                )
            
            if node_status.get("memory_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="memory",
                    metric_value=node_status.get("memory_usage", 0),
                    node_id=node.id
                )
            
            if node_status.get("disk_usage") is not None:
                await evaluate_alert_rules(
                    db=db,
                    metric_type="disk",
                    metric_value=node_status.get("disk_usage", 0),
                    node_id=node.id
                )
        
        # Broadcast update via WebSocket
        if _broadcast_update:
            try:
                await _broadcast_update("node_update", {
                    "node_id": node.id,
                    "status": node.status,
                    "last_check": str(node.last_check)
                })
            except Exception as e:
                logger.error(f"Failed to broadcast node update: {e}")
        
        return node_status
    except Exception as e:
        logger.error(f"Error checking node {node.name}: {e}")
        node.status = "error"
        node.last_check = datetime.utcnow()
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


async def sync_vms(node: Node):
    """Sync VMs from Proxmox node"""
    try:
        client = ProxmoxClient(node.url, node.username, node.token)
        vms_data = client.get_vms()
        
        db = SessionLocal()
        try:
            # Get existing VMs for this node
            existing_vms = {vm.vmid: vm for vm in db.query(VM).filter(VM.node_id == node.id).all()}
            
            for vm_data in vms_data:
                vmid = vm_data["vmid"]
                
                if vmid in existing_vms:
                    # Update existing VM
                    vm = existing_vms[vmid]
                    vm.name = vm_data.get("name", vm.name)
                    vm.status = vm_data.get("status", "unknown")
                    vm.cpu_usage = vm_data.get("cpu_usage", 0)
                    vm.memory_usage = vm_data.get("memory_usage", 0)
                    vm.memory_total = vm_data.get("memory_total", 0)
                    vm.disk_usage = vm_data.get("disk_usage", 0)
                    vm.disk_total = vm_data.get("disk_total", 0)
                    vm.uptime = vm_data.get("uptime", 0)
                    vm.last_check = datetime.utcnow()
                else:
                    # Create new VM
                    vm = VM(
                        node_id=node.id,
                        vmid=vmid,
                        name=vm_data.get("name", f"VM {vmid}"),
                        status=vm_data.get("status", "unknown"),
                        cpu_usage=vm_data.get("cpu_usage", 0),
                        memory_usage=vm_data.get("memory_usage", 0),
                        memory_total=vm_data.get("memory_total", 0),
                        disk_usage=vm_data.get("disk_usage", 0),
                        disk_total=vm_data.get("disk_total", 0),
                        uptime=vm_data.get("uptime", 0),
                        last_check=datetime.utcnow()
                    )
                    db.add(vm)
                
                # Store VM metrics
                metric_cpu = Metric(
                    node_id=node.id,
                    vm_id=vm.id if vm.id else None,
                    metric_type="cpu",
                    value=vm_data.get("cpu_usage", 0),
                    unit="percent"
                )
                db.add(metric_cpu)
                
                metric_memory = Metric(
                    node_id=node.id,
                    vm_id=vm.id if vm.id else None,
                    metric_type="memory",
                    value=vm_data.get("memory_usage", 0),
                    unit="percent"
                )
                db.add(metric_memory)
                
                # Evaluate alert rules for VM CPU
                if vm_data.get("cpu_usage") is not None:
                    await evaluate_alert_rules(
                        db=db,
                        metric_type="cpu",
                        metric_value=vm_data.get("cpu_usage", 0),
                        node_id=node.id,
                        vm_id=vm.id if vm.id else None
                    )
                
                # Evaluate alert rules for VM Memory
                if vm_data.get("memory_usage") is not None:
                    await evaluate_alert_rules(
                        db=db,
                        metric_type="memory",
                        metric_value=vm_data.get("memory_usage", 0),
                        node_id=node.id,
                        vm_id=vm.id if vm.id else None
                    )
            
            db.commit()
            
            # Invalidate cache
            invalidate_cache("vms")
            invalidate_cache("dashboard")
            
            # Broadcast update via WebSocket
            if _broadcast_update:
                try:
                    await _broadcast_update("vms_update", {
                        "node_id": node.id,
                        "vm_count": len(vms_data)
                    })
                except Exception as e:
                    logger.error(f"Failed to broadcast VMs update: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error syncing VMs for node {node.name}: {e}")


async def check_service(service: Service):
    """Check a single service"""
    try:
        result = await HealthChecker.check_service(
            service_type=service.type,
            target=service.target,
            port=service.port,
            timeout=service.timeout,
            expected_status=service.expected_status,
            custom_command=service.custom_command,
            custom_script=service.custom_script
        )
        
        db = SessionLocal()
        try:
            # Store health check result
            health_check = HealthCheck(
                service_id=service.id,
                status=result["status"],
                response_time=result.get("response_time"),
                status_code=result.get("status_code"),
                error_message=result.get("error_message")
            )
            db.add(health_check)
            
            # Create alert if service is down
            if result["status"] == "down":
                existing_alert = db.query(Alert).filter(
                    Alert.service_id == service.id,
                    Alert.is_resolved == False
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        alert_type="service_down",
                        severity="critical",
                        title=f"Service {service.name} is down",
                        message=result.get("error_message", "Service check failed"),
                        service_id=service.id
                    )
                    db.add(alert)
                    db.commit()  # Commit to get alert ID
                    db.refresh(alert)
                    
                    # Send email notification
                    vm_name = None
                    if service.vm_id:
                        vm = db.query(VM).filter(VM.id == service.vm_id).first()
                        if vm:
                            vm_name = vm.name
                    
                    send_alert_notification(
                        alert_type="service_down",
                        severity="critical",
                        title=f"Service {service.name} is down",
                        message=result.get("error_message", "Service check failed"),
                        service_name=service.name,
                        vm_name=vm_name
                    )
                    
                    # Send webhook notifications
                    await send_alert_webhooks(
                        db=db,
                        alert=alert,
                        alert_type="service_down",
                        severity="critical",
                        title=f"Service {service.name} is down",
                        message=result.get("error_message", "Service check failed"),
                        service_name=service.name,
                        vm_name=vm_name
                    )
                    
                    # Send notification channel notifications (Slack, Discord)
                    await send_alert_notifications(
                        db=db,
                        alert=alert,
                        alert_type="service_down",
                        severity="critical",
                        title=f"Service {service.name} is down",
                        message=result.get("error_message", "Service check failed"),
                        service_name=service.name,
                        vm_name=vm_name
                    )
            else:
                # Resolve existing alerts
                db.query(Alert).filter(
                    Alert.service_id == service.id,
                    Alert.is_resolved == False
                ).update({"is_resolved": True, "resolved_at": datetime.utcnow()}                    )
            
            db.commit()
            
            # Invalidate cache
            invalidate_cache("services")
            invalidate_cache("dashboard")
            
            # Broadcast update via WebSocket
            if _broadcast_update:
                try:
                    await _broadcast_update("service_update", {
                        "service_id": service.id,
                        "status": result["status"],
                        "response_time": result.get("response_time")
                    })
                except Exception as e:
                    logger.error(f"Failed to broadcast service update: {e}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error checking service {service.name}: {e}")


async def run_node_checks():
    """Run checks for all active nodes"""
    db = SessionLocal()
    try:
        nodes = db.query(Node).filter(Node.is_active == True).all()
        for node in nodes:
            # Refresh node from database to ensure we have latest data
            db.refresh(node)
            await check_node(node)
            await sync_vms(node)
    finally:
        db.close()


async def run_service_checks():
    """Run checks for all active services"""
    db = SessionLocal()
    try:
        services = db.query(Service).filter(
            Service.is_active == True,
            Service.maintenance_mode == False
        ).all()
        for service in services:
            await check_service(service)
    finally:
        db.close()


async def cleanup_old_metrics():
    """Clean up old metrics based on retention policy"""
    from config import settings
    from datetime import timedelta
    
    if not settings.metrics_cleanup_enabled:
        return
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.metrics_retention_days)
        
        deleted_count = db.query(Metric).filter(
            Metric.recorded_at < cutoff_date
        ).delete()
        
        db.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old metrics (older than {settings.metrics_retention_days} days)")
    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    scheduler.add_job(
        run_node_checks,
        trigger=IntervalTrigger(seconds=60),
        id="node_checks",
        replace_existing=True
    )
    
    scheduler.add_job(
        run_service_checks,
        trigger=IntervalTrigger(seconds=60),
        id="service_checks",
        replace_existing=True
    )
    
    # Run metrics cleanup daily at 2 AM
    scheduler.add_job(
        cleanup_old_metrics,
        trigger=IntervalTrigger(hours=24),
        id="metrics_cleanup",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


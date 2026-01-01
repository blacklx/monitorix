"""
Copyright 2024 Monitorix Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from celery import Task
from database import SessionLocal
from models import Node, Service, Metric
from proxmox_client import ProxmoxClient
from scheduler import check_node, sync_vms, check_service
from config import settings
from datetime import datetime, timedelta
from cache import invalidate_cache
import logging
import subprocess
import os
import json
import csv
import io
import asyncio

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion"""
        if self._db is not None:
            self._db.close()
            self._db = None


# Only define tasks if Celery is enabled
if settings.celery_enabled:
    try:
        from celery_app import celery_app
        
        @celery_app.task(base=DatabaseTask, bind=True, name="tasks.bulk_create_nodes")
        def bulk_create_nodes_task(self, nodes_data: list):
            """
            Background task to create multiple nodes.
            
            Args:
                nodes_data: List of node dictionaries to create
            
            Returns:
                dict: Result with created and failed nodes
            """
            db = self.db
            created = []
            failed = []
            
            try:
                for node_data in nodes_data:
                    try:
                        # Check if node name already exists
                        existing = db.query(Node).filter(Node.name == node_data["name"]).first()
                        if existing:
                            failed.append({
                                "node": node_data,
                                "error": "Node with this name already exists"
                            })
                            continue
                        
                        # Test connection
                        verify_ssl = node_data.get("verify_ssl", True)  # Default to True if not provided
                        client = ProxmoxClient(
                            node_data["url"],
                            node_data["username"],
                            node_data["token"],
                            verify_ssl=verify_ssl
                        )
                        if not client.test_connection():
                            failed.append({
                                "node": node_data,
                                "error": "Failed to connect to Proxmox node"
                            })
                            continue
                        
                        # Create node
                        node = Node(
                            name=node_data["name"],
                            url=node_data["url"],
                            username=node_data["username"],
                            token=node_data["token"],
                            verify_ssl=node_data.get("verify_ssl", True),
                            is_local=node_data.get("is_local", False),
                            tags=node_data.get("tags", [])
                        )
                        db.add(node)
                        db.commit()
                        db.refresh(node)
                        
                        # Initial sync (run synchronously in Celery task)
                        # Note: These are async functions, but we run them in sync context
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(check_node(node))
                            loop.run_until_complete(sync_vms(node))
                        finally:
                            loop.close()
                        
                        created.append({
                            "id": node.id,
                            "name": node.name,
                            "url": node.url
                        })
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error creating node {node_data.get('name', 'unknown')}: {e}")
                        failed.append({
                            "node": node_data,
                            "error": str(e)
                        })
                
                # Invalidate cache
                if created:
                    invalidate_cache("nodes")
                    invalidate_cache("dashboard")
                
                return {
                    "success": True,
                    "created": created,
                    "failed": failed,
                    "total": len(nodes_data),
                    "created_count": len(created),
                    "failed_count": len(failed)
                }
            except Exception as e:
                logger.error(f"Error in bulk_create_nodes_task: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "created": created,
                    "failed": failed
                }


        @celery_app.task(base=DatabaseTask, bind=True, name="tasks.bulk_create_services")
        def bulk_create_services_task(self, services_data: list):
            """
            Background task to create multiple services.
            
            Args:
                services_data: List of service dictionaries to create
            
            Returns:
                dict: Result with created and failed services
            """
            db = self.db
            created = []
            failed = []
            
            try:
                for service_data in services_data:
                    try:
                        # Validate VM if provided
                        if service_data.get("vm_id"):
                            from models import VM
                            vm = db.query(VM).filter(VM.id == service_data["vm_id"]).first()
                            if not vm:
                                failed.append({
                                    "service": service_data,
                                    "error": "VM not found"
                                })
                                continue
                        
                        # Create service
                        service = Service(**service_data)
                        db.add(service)
                        db.commit()
                        db.refresh(service)
                        
                        # Initial check (run synchronously in Celery task)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(check_service(service))
                        finally:
                            loop.close()
                        
                        created.append({
                            "id": service.id,
                            "name": service.name,
                            "type": service.check_type
                        })
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error creating service {service_data.get('name', 'unknown')}: {e}")
                        failed.append({
                            "service": service_data,
                            "error": str(e)
                        })
                
                # Invalidate cache
                if created:
                    invalidate_cache("services")
                    invalidate_cache("dashboard")
                
                return {
                    "success": True,
                    "created": created,
                    "failed": failed,
                    "total": len(services_data),
                    "created_count": len(created),
                    "failed_count": len(failed)
                }
            except Exception as e:
                logger.error(f"Error in bulk_create_services_task: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "created": created,
                    "failed": failed
                }


        @celery_app.task(base=DatabaseTask, bind=True, name="tasks.sync_vms")
        def sync_vms_task(self, node_id: int):
            """
            Background task to synchronize VMs from a Proxmox node.
            
            Args:
                node_id: ID of the node to sync
            
            Returns:
                dict: Result with sync status
            """
            db = self.db
            try:
                node = db.query(Node).filter(Node.id == node_id).first()
                if not node:
                    return {
                        "success": False,
                        "error": f"Node {node_id} not found"
                    }
                
                # Sync VMs (run synchronously in Celery task)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(sync_vms(node))
                finally:
                    loop.close()
                
                # Invalidate cache
                invalidate_cache("vms")
                invalidate_cache("dashboard")
                invalidate_cache(f"node:{node_id}")
                
                return {
                    "success": True,
                    "node_id": node_id,
                    "node_name": node.name,
                    "message": "VM synchronization completed"
                }
            except Exception as e:
                logger.error(f"Error in sync_vms_task for node {node_id}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "node_id": node_id
                }


        @celery_app.task(base=DatabaseTask, bind=True, name="tasks.cleanup_metrics")
        def cleanup_metrics_task(self):
            """
            Background task to clean up old metrics based on retention policy.
            
            Returns:
                dict: Result with cleanup status
            """
            db = self.db
            try:
                if not settings.metrics_cleanup_enabled:
                    return {
                        "success": True,
                        "message": "Metrics cleanup is disabled",
                        "deleted_count": 0
                    }
                
                cutoff_date = datetime.utcnow() - timedelta(days=settings.metrics_retention_days)
                
                deleted_count = db.query(Metric).filter(
                    Metric.recorded_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger.info(f"Cleaned up {deleted_count} old metrics (older than {settings.metrics_retention_days} days)")
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": settings.metrics_retention_days
                }
            except Exception as e:
                logger.error(f"Error in cleanup_metrics_task: {e}")
                db.rollback()
                return {
                    "success": False,
                    "error": str(e)
                }


        @celery_app.task(bind=True, name="tasks.create_backup")
        def create_backup_task(self):
            """
            Background task to create a database backup.
            
            Returns:
                dict: Result with backup status
            """
            try:
                from routers.backup import get_postgres_container_name, get_database_credentials
                
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"backup_{timestamp}.sql"
                backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, backup_filename)
                
                container_name = get_postgres_container_name()
                creds = get_database_credentials()
                
                docker_exec_cmd = [
                    "docker", "exec", container_name,
                    "pg_dump",
                    "-U", creds["user"],
                    "-d", creds["database"],
                    "--clean",
                    "--if-exists"
                ]
                
                env = os.environ.copy()
                env["PGPASSWORD"] = creds["password"]
                
                result = subprocess.run(
                    docker_exec_cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    with open(backup_path, "w") as f:
                        f.write(result.stdout)
                    logger.info(f"Backup created successfully: {backup_filename}")
                    return {
                        "success": True,
                        "filename": backup_filename,
                        "path": backup_path,
                        "size": os.path.getsize(backup_path),
                        "created_at": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"Backup failed: {result.stderr}")
                    return {
                        "success": False,
                        "error": result.stderr
                    }
            except Exception as e:
                logger.error(f"Error in create_backup_task: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }


        @celery_app.task(base=DatabaseTask, bind=True, name="tasks.export_data")
        def export_data_task(self, export_type: str, format_type: str, filters: dict = None):
            """
            Background task to export data (nodes, VMs, services, alerts).
            
            Args:
                export_type: Type of data to export (nodes, vms, services, alerts)
                format_type: Export format (csv, json)
                filters: Optional filters for the export
            
            Returns:
                dict: Result with export data or file path
            """
            db = self.db
            try:
                filters = filters or {}
                
                if export_type == "nodes":
                    query = db.query(Node)
                    if filters.get("tag"):
                        from sqlalchemy import cast
                        from sqlalchemy.dialects.postgresql import JSONB
                        query = query.filter(cast(Node.tags, JSONB).contains([filters["tag"]]))
                    items = query.all()
                    
                    if format_type == "csv":
                        output = io.StringIO()
                        writer = csv.writer(output)
                        writer.writerow([
                            'ID', 'Name', 'URL', 'Username', 'Is Local', 'Is Active',
                            'Maintenance Mode', 'Status', 'Last Check', 'Created At', 'Updated At'
                        ])
                        for node in items:
                            writer.writerow([
                                node.id, node.name, node.url, node.username,
                                node.is_local, node.is_active, node.maintenance_mode,
                                node.status,
                                node.last_check.isoformat() if node.last_check else '',
                                node.created_at.isoformat() if node.created_at else '',
                                node.updated_at.isoformat() if node.updated_at else ''
                            ])
                        return {
                            "success": True,
                            "format": "csv",
                            "data": output.getvalue(),
                            "count": len(items)
                        }
                    else:  # json
                        data = [{
                            'id': node.id, 'name': node.name, 'url': node.url,
                            'username': node.username, 'is_local': node.is_local,
                            'is_active': node.is_active, 'maintenance_mode': node.maintenance_mode,
                            'status': node.status,
                            'last_check': node.last_check.isoformat() if node.last_check else None,
                            'created_at': node.created_at.isoformat() if node.created_at else None,
                            'updated_at': node.updated_at.isoformat() if node.updated_at else None
                        } for node in items]
                        return {
                            "success": True,
                            "format": "json",
                            "data": json.dumps(data, indent=2),
                            "count": len(items)
                        }
                
                # Similar implementations for vms, services, alerts...
                # (Simplified for brevity - full implementation would handle all types)
                
                return {
                    "success": False,
                    "error": f"Export type {export_type} not implemented in background task"
                }
            except Exception as e:
                logger.error(f"Error in export_data_task: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    except ImportError as e:
        logger.warning(f"Celery not available, tasks will not be registered: {e}")
    except Exception as e:
        logger.error(f"Error setting up Celery tasks: {e}")


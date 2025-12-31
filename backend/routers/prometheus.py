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
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from models import Node, VM, Service, Alert, Metric
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prometheus", tags=["prometheus"])

# Prometheus metrics
nodes_total = Gauge("monitorix_nodes_total", "Total number of nodes")
nodes_online = Gauge("monitorix_nodes_online", "Number of online nodes")
vms_total = Gauge("monitorix_vms_total", "Total number of VMs")
vms_running = Gauge("monitorix_vms_running", "Number of running VMs")
services_total = Gauge("monitorix_services_total", "Total number of services")
services_healthy = Gauge("monitorix_services_healthy", "Number of healthy services")
alerts_active = Gauge("monitorix_alerts_active", "Number of active alerts")
node_cpu_usage = Gauge("monitorix_node_cpu_usage_percent", "CPU usage percentage", ["node_id", "node_name"])
node_memory_usage = Gauge("monitorix_node_memory_usage_percent", "Memory usage percentage", ["node_id", "node_name"])
node_disk_usage = Gauge("monitorix_node_disk_usage_percent", "Disk usage percentage", ["node_id", "node_name"])
vm_cpu_usage = Gauge("monitorix_vm_cpu_usage_percent", "VM CPU usage percentage", ["vm_id", "vm_name", "node_id"])
vm_memory_usage = Gauge("monitorix_vm_memory_usage_percent", "VM memory usage percentage", ["vm_id", "vm_name", "node_id"])
service_response_time = Histogram("monitorix_service_response_time_seconds", "Service response time in seconds", ["service_id", "service_name"])


@router.get("/metrics")
async def prometheus_metrics(db: Session = Depends(get_db)):
    """
    Prometheus metrics endpoint.
    
    Exposes Monitorix metrics in Prometheus format for scraping.
    No authentication required (can be protected by network-level access control).
    """
    try:
        # Update node metrics
        total_nodes = db.query(Node).count()
        online_nodes = db.query(Node).filter(Node.status == "online").count()
        nodes_total.set(total_nodes)
        nodes_online.set(online_nodes)
        
        # Update VM metrics
        total_vms = db.query(VM).count()
        running_vms = db.query(VM).filter(VM.status == "running").count()
        vms_total.set(total_vms)
        vms_running.set(running_vms)
        
        # Update service metrics
        total_services = db.query(Service).filter(Service.is_active == True).count()
        healthy_services = db.query(Service).filter(Service.status == "up").count()
        services_total.set(total_services)
        services_healthy.set(healthy_services)
        
        # Update alert metrics
        active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
        alerts_active.set(active_alerts)
        
        # Update node resource metrics (latest values)
        nodes = db.query(Node).all()
        for node in nodes:
            latest_cpu = db.query(Metric).filter(
                Metric.node_id == node.id,
                Metric.vm_id.is_(None),
                Metric.metric_type == "cpu"
            ).order_by(Metric.recorded_at.desc()).first()
            
            latest_memory = db.query(Metric).filter(
                Metric.node_id == node.id,
                Metric.vm_id.is_(None),
                Metric.metric_type == "memory"
            ).order_by(Metric.recorded_at.desc()).first()
            
            latest_disk = db.query(Metric).filter(
                Metric.node_id == node.id,
                Metric.vm_id.is_(None),
                Metric.metric_type == "disk"
            ).order_by(Metric.recorded_at.desc()).first()
            
            if latest_cpu:
                node_cpu_usage.labels(node_id=str(node.id), node_name=node.name).set(latest_cpu.value)
            if latest_memory:
                node_memory_usage.labels(node_id=str(node.id), node_name=node.name).set(latest_memory.value)
            if latest_disk:
                node_disk_usage.labels(node_id=str(node.id), node_name=node.name).set(latest_disk.value)
        
        # Update VM resource metrics (latest values)
        vms = db.query(VM).all()
        for vm in vms:
            latest_cpu = db.query(Metric).filter(
                Metric.vm_id == vm.id,
                Metric.metric_type == "cpu"
            ).order_by(Metric.recorded_at.desc()).first()
            
            latest_memory = db.query(Metric).filter(
                Metric.vm_id == vm.id,
                Metric.metric_type == "memory"
            ).order_by(Metric.recorded_at.desc()).first()
            
            if latest_cpu:
                vm_cpu_usage.labels(vm_id=str(vm.id), vm_name=vm.name, node_id=str(vm.node_id)).set(latest_cpu.value)
            if latest_memory:
                vm_memory_usage.labels(vm_id=str(vm.id), vm_name=vm.name, node_id=str(vm.node_id)).set(latest_memory.value)
        
        # Generate Prometheus metrics output
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return Response(content=f"# Error generating metrics: {e}\n", media_type=CONTENT_TYPE_LATEST)


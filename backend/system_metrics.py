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
import psutil
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def get_system_metrics() -> Dict:
    """
    Collect system metrics for the Monitorix backend server.
    
    Returns:
        dict: System metrics including CPU, memory, disk, and network usage
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_total = memory.total
        memory_used = memory.used
        memory_available = memory.available
        memory_percent = memory.percent
        
        # Disk metrics (root filesystem)
        disk = psutil.disk_usage('/')
        disk_total = disk.total
        disk_used = disk.used
        disk_free = disk.free
        disk_percent = disk.percent
        
        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent if network else 0
        network_bytes_recv = network.bytes_recv if network else 0
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        
        # Process metrics (Monitorix backend process)
        process = psutil.Process()
        process_cpu_percent = process.cpu_percent(interval=0.1)
        process_memory_info = process.memory_info()
        process_memory_mb = process_memory_info.rss / 1024 / 1024  # Convert to MB
        process_num_threads = process.num_threads()
        process_create_time = process.create_time()
        process_uptime_seconds = datetime.now().timestamp() - process_create_time
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "count_logical": cpu_count_logical
            },
            "memory": {
                "total": memory_total,
                "used": memory_used,
                "available": memory_available,
                "percent": memory_percent
            },
            "disk": {
                "total": disk_total,
                "used": disk_used,
                "free": disk_free,
                "percent": disk_percent
            },
            "network": {
                "bytes_sent": network_bytes_sent,
                "bytes_recv": network_bytes_recv
            },
            "system": {
                "uptime_seconds": uptime_seconds,
                "boot_time": datetime.fromtimestamp(boot_time).isoformat()
            },
            "process": {
                "cpu_percent": process_cpu_percent,
                "memory_mb": process_memory_mb,
                "num_threads": process_num_threads,
                "uptime_seconds": process_uptime_seconds
            }
        }
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def get_system_metrics_summary() -> Dict:
    """
    Get a summary of system metrics suitable for dashboard display.
    
    Returns:
        dict: Summary with key metrics
    """
    metrics = get_system_metrics()
    
    if "error" in metrics:
        return metrics
    
    return {
        "timestamp": metrics["timestamp"],
        "cpu_percent": metrics["cpu"]["percent"],
        "memory_percent": metrics["memory"]["percent"],
        "memory_used_gb": round(metrics["memory"]["used"] / 1024 / 1024 / 1024, 2),
        "memory_total_gb": round(metrics["memory"]["total"] / 1024 / 1024 / 1024, 2),
        "disk_percent": metrics["disk"]["percent"],
        "disk_used_gb": round(metrics["disk"]["used"] / 1024 / 1024 / 1024, 2),
        "disk_total_gb": round(metrics["disk"]["total"] / 1024 / 1024 / 1024, 2),
        "uptime_seconds": metrics["system"]["uptime_seconds"],
        "process_memory_mb": round(metrics["process"]["memory_mb"], 2)
    }


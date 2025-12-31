from proxmoxer import ProxmoxAPI
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProxmoxClient:
    def __init__(self, url: str, username: str, token: str):
        """
        Initialize Proxmox client
        
        Args:
            url: Proxmox API URL (e.g., https://192.168.1.10:8006)
            username: Proxmox username (e.g., user@pam or user@pve)
            token: Proxmox API token (format: token_id=secret)
        """
        self.url = url
        self.username = username
        self.token = token
        self._api = None

    def _get_api(self):
        """Get or create Proxmox API client"""
        if self._api is None:
            try:
                # Parse token (format: token_id=secret)
                if "=" in self.token:
                    token_id, token_secret = self.token.split("=", 1)
                else:
                    # Assume it's just the secret, use username as token_id
                    token_id = self.username.split("@")[0]
                    token_secret = self.token

                self._api = ProxmoxAPI(
                    self.url,
                    user=self.username,
                    token_name=token_id,
                    token_value=token_secret,
                    verify_ssl=False  # You may want to enable SSL verification in production
                )
            except Exception as e:
                logger.error(f"Failed to connect to Proxmox: {e}")
                raise
        return self._api

    def test_connection(self) -> bool:
        """Test connection to Proxmox node"""
        try:
            api = self._get_api()
            api.version.get()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_node_status(self) -> Dict:
        """Get node status and information"""
        try:
            api = self._get_api()
            # Get cluster status
            cluster_status = api.cluster.status.get()
            
            # Get node list
            nodes = api.nodes.get()
            
            if not nodes:
                return {"status": "error", "message": "No nodes found"}
            
            # Get first node info (assuming single node or primary node)
            node_name = nodes[0]["node"]
            node_info = api.nodes(node_name).status.get()
            
            return {
                "status": "online",
                "node": node_name,
                "uptime": node_info.get("uptime", 0),
                "cpu_usage": node_info.get("cpu", 0) * 100,
                "memory_used": node_info.get("memory", {}).get("used", 0),
                "memory_total": node_info.get("memory", {}).get("total", 0),
                "memory_usage": (node_info.get("memory", {}).get("used", 0) / 
                               max(node_info.get("memory", {}).get("total", 1), 1)) * 100,
                "disk_used": node_info.get("rootfs", {}).get("used", 0),
                "disk_total": node_info.get("rootfs", {}).get("total", 0),
                "disk_usage": (node_info.get("rootfs", {}).get("used", 0) / 
                             max(node_info.get("rootfs", {}).get("total", 1), 1)) * 100,
            }
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            return {"status": "error", "message": str(e)}

    def get_vms(self) -> List[Dict]:
        """Get list of all VMs and containers"""
        try:
            api = self._get_api()
            nodes = api.nodes.get()
            all_vms = []

            for node in nodes:
                node_name = node["node"]
                # Get QEMU VMs
                qemu_vms = api.nodes(node_name).qemu.get()
                for vm in qemu_vms:
                    vm_status = api.nodes(node_name).qemu(vm["vmid"]).status.current.get()
                    all_vms.append({
                        "vmid": vm["vmid"],
                        "name": vm.get("name", f"VM {vm['vmid']}"),
                        "node": node_name,
                        "status": vm_status.get("status", "unknown"),
                        "cpu_usage": vm_status.get("cpu", 0) * 100,
                        "memory_used": vm_status.get("mem", 0),
                        "memory_total": vm_status.get("maxmem", 0),
                        "memory_usage": (vm_status.get("mem", 0) / 
                                       max(vm_status.get("maxmem", 1), 1)) * 100,
                        "disk_used": vm_status.get("disk", 0),
                        "disk_total": vm_status.get("maxdisk", 0),
                        "disk_usage": (vm_status.get("disk", 0) / 
                                     max(vm_status.get("maxdisk", 1), 1)) * 100,
                        "uptime": vm_status.get("uptime", 0),
                    })
                
                # Get LXC containers
                lxc_containers = api.nodes(node_name).lxc.get()
                for container in lxc_containers:
                    container_status = api.nodes(node_name).lxc(container["vmid"]).status.current.get()
                    all_vms.append({
                        "vmid": container["vmid"],
                        "name": container.get("name", f"CT {container['vmid']}"),
                        "node": node_name,
                        "status": container_status.get("status", "unknown"),
                        "cpu_usage": container_status.get("cpu", 0) * 100,
                        "memory_used": container_status.get("mem", 0),
                        "memory_total": container_status.get("maxmem", 0),
                        "memory_usage": (container_status.get("mem", 0) / 
                                       max(container_status.get("maxmem", 1), 1)) * 100,
                        "disk_used": container_status.get("disk", 0),
                        "disk_total": container_status.get("maxdisk", 0),
                        "disk_usage": (container_status.get("disk", 0) / 
                                     max(container_status.get("maxdisk", 1), 1)) * 100,
                        "uptime": container_status.get("uptime", 0),
                    })

            return all_vms
        except Exception as e:
            logger.error(f"Failed to get VMs: {e}")
            return []


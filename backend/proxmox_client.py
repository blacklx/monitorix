from proxmoxer import ProxmoxAPI
from typing import Dict, List, Optional
import logging
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from config import settings

logger = logging.getLogger(__name__)


class ProxmoxClient:
    def __init__(self, url: str, username: str, token: str, verify_ssl: Optional[bool] = None, ca_bundle: Optional[str] = None):
        """
        Initialize Proxmox client
        
        Args:
            url: Proxmox API URL (e.g., https://192.168.1.10:8006)
            username: Proxmox username (e.g., user@pam or user@pve)
            token: Proxmox API token (format: token_id=secret)
            verify_ssl: Whether to verify SSL certificates (defaults to PROXMOX_VERIFY_SSL from config)
            ca_bundle: Path to CA bundle file for SSL verification (optional)
        """
        # Normalize URL: remove trailing slash, ensure proper format
        self.url = self._normalize_url(url)
        self.username = username
        self.token = token
        self.verify_ssl = verify_ssl if verify_ssl is not None else settings.proxmox_verify_ssl
        self.ca_bundle = ca_bundle or settings.proxmox_ca_bundle
        self._api = None
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize Proxmox URL to prevent proxmoxer parsing errors.
        
        Removes trailing slashes and ensures proper URL format.
        """
        if not url:
            return url
        
        # Strip whitespace
        url = url.strip()
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Parse and reconstruct URL to ensure proper format
        try:
            parsed = urlparse(url)
            
            # Ensure scheme is present
            if not parsed.scheme:
                # If no scheme, assume https
                url = f"https://{url}"
                parsed = urlparse(url)
            
            # Reconstruct URL without path (proxmoxer doesn't need it)
            # Keep only: scheme, netloc (host:port)
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,  # This includes host:port
                '',  # No path
                '',  # No params
                '',  # No query
                ''   # No fragment
            ))
            
            return normalized
        except Exception as e:
            logger.warning(f"Failed to normalize URL '{url}': {e}. Using original URL.")
            return url.rstrip('/')

    def _get_api(self):
        """Get or create Proxmox API client"""
        if self._api is None:
            try:
                # Log the URL being used for debugging
                logger.debug(f"Creating ProxmoxAPI with URL: {self.url}")
                
                # Parse token (format: token_id=secret)
                if "=" in self.token:
                    token_id, token_secret = self.token.split("=", 1)
                else:
                    # Assume it's just the secret, use username as token_id
                    token_id = self.username.split("@")[0]
                    token_secret = self.token

                # Determine SSL verification setting
                verify_ssl = self.verify_ssl
                if self.ca_bundle:
                    # If CA bundle is provided, use it for verification
                    verify_ssl = self.ca_bundle

                # ProxmoxAPI expects the URL without trailing slash and without path
                # Ensure URL is in the correct format: scheme://host:port
                api_url = self.url
                
                # Double-check URL format before passing to ProxmoxAPI
                parsed = urlparse(api_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid URL format: {api_url}. Expected format: https://host:port")
                
                logger.debug(f"ProxmoxAPI parameters: url={api_url}, user={self.username}, token_name={token_id}, verify_ssl={verify_ssl}")
                
                self._api = ProxmoxAPI(
                    api_url,
                    user=self.username,
                    token_name=token_id,
                    token_value=token_secret,
                    verify_ssl=verify_ssl
                )
                
                if not self.verify_ssl:
                    logger.warning(f"SSL verification is DISABLED for Proxmox connection to {self.url}. "
                                 "This is a security risk! Enable SSL verification in production.")
            except ValueError as e:
                # Re-raise ValueError with more context
                logger.error(f"Invalid URL format for Proxmox: {e}. URL was: {self.url}")
                raise
            except Exception as e:
                logger.error(f"Failed to create ProxmoxAPI connection: {e}")
                logger.error(f"URL: {self.url}, Username: {self.username}, Token format: {'token_id=secret' if '=' in self.token else 'secret only'}")
                raise
        return self._api

    def test_connection(self) -> bool:
        """Test connection to Proxmox node"""
        try:
            logger.debug(f"Testing connection to Proxmox node at {self.url}")
            api = self._get_api()
            result = api.version.get()
            logger.debug(f"Connection test successful. Proxmox version: {result}")
            return True
        except ValueError as e:
            # ValueError usually means URL format issue
            logger.error(f"Connection test failed - Invalid URL format: {e}")
            logger.error(f"URL was: {self.url}")
            return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")
            logger.error(f"URL: {self.url}, Username: {self.username}")
            # Check if it's the IPv6 error specifically
            if "Invalid IPv6 URL" in error_msg or "IPv6" in error_msg:
                logger.error(f"IPv6 URL error detected. Original URL: {self.url}, Normalized URL: {self.url}")
                logger.error("This might be a proxmoxer library issue. Try using IP address instead of hostname, or check URL format.")
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


from proxmoxer import ProxmoxAPI
from proxmoxer.backends.https import AuthenticationError
from typing import Dict, List, Optional
import logging
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from config import settings
import re

logger = logging.getLogger(__name__)

# Workaround for proxmoxer "Invalid IPv6 URL" bug
# This is a known bug in proxmoxer 2.0.1 where IPv4 addresses trigger IPv6 validation errors
# The bug is in proxmoxer's URL parsing - it incorrectly validates IPv4 addresses as IPv6
def _patch_proxmoxer_url_validation():
    """Patch proxmoxer's URL validation to fix IPv6 bug with IPv4 addresses"""
    try:
        import proxmoxer.core
        import proxmoxer.backends.https
        
        # Patch ProxmoxAPI.__init__ to normalize URLs before passing to backend
        if hasattr(proxmoxer.core, 'ProxmoxAPI'):
            original_proxmox_api_init = proxmoxer.core.ProxmoxAPI.__init__
            
            def patched_proxmox_api_init(self, host, *args, **kwargs):
                # Normalize the host/URL parameter
                if isinstance(host, str):
                    # Check if it's an IPv4 address URL
                    ipv4_pattern = r'^https?://(\d{1,3}\.){3}\d{1,3}(:\d+)?/?$'
                    if re.match(ipv4_pattern, host):
                        # Remove trailing slash
                        host = host.rstrip('/')
                return original_proxmox_api_init(self, host, *args, **kwargs)
            
            proxmoxer.core.ProxmoxAPI.__init__ = patched_proxmox_api_init
            logger.debug("Patched proxmoxer ProxmoxAPI.__init__")
            
        # Also try to patch the backend's URL validation
        if hasattr(proxmoxer.backends.https, 'ProxmoxHttpSession'):
            original_session_init = proxmoxer.backends.https.ProxmoxHttpSession.__init__
            
            def patched_session_init(self, *args, **kwargs):
                # Normalize URL if provided
                if args and isinstance(args[0], str):
                    url = args[0]
                    ipv4_pattern = r'^https?://(\d{1,3}\.){3}\d{1,3}(:\d+)?/?$'
                    if re.match(ipv4_pattern, url):
                        args = (url.rstrip('/'),) + args[1:]
                elif 'url' in kwargs:
                    url = kwargs['url']
                    ipv4_pattern = r'^https?://(\d{1,3}\.){3}\d{1,3}(:\d+)?/?$'
                    if re.match(ipv4_pattern, url):
                        kwargs['url'] = url.rstrip('/')
                return original_session_init(self, *args, **kwargs)
            
            proxmoxer.backends.https.ProxmoxHttpSession.__init__ = patched_session_init
            logger.debug("Patched proxmoxer ProxmoxHttpSession.__init__")
            
    except Exception as e:
        logger.warning(f"Failed to patch proxmoxer URL validation: {e}. Will use workaround in connection code.")

# Apply patch on import
_patch_proxmoxer_url_validation()


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
                
                # Extract hostname and port separately to avoid proxmoxer parsing issues
                hostname = parsed.hostname
                port = parsed.port
                
                # Reconstruct URL in the simplest possible format
                # Proxmoxer can be sensitive to URL format, so we ensure it's exactly right
                if port:
                    # Ensure port is included
                    clean_url = f"{parsed.scheme}://{hostname}:{port}"
                else:
                    clean_url = f"{parsed.scheme}://{hostname}"
                
                logger.info(f"ProxmoxAPI connection attempt: url={clean_url}, user={self.username}, token_name={token_id}, verify_ssl={verify_ssl}")
                logger.debug(f"Original URL: {api_url}, Cleaned URL: {clean_url}, Hostname: {hostname}, Port: {port}")
                
                # ProxmoxAPI can accept either:
                # 1. URL as first parameter: ProxmoxAPI("https://host:port", user=..., token_name=..., token_value=...)
                # 2. Host and port separately: ProxmoxAPI(host, port=port, user=..., token_name=..., token_value=...)
                # 
                # The "Invalid IPv6 URL" error suggests proxmoxer is having trouble parsing the URL.
                # Let's try using host and port separately first, which might avoid the URL parsing bug.
                try:
                    # Try using host and port as separate parameters (this might avoid the URL parsing bug)
                    if port:
                        logger.debug(f"Trying ProxmoxAPI with host={hostname}, port={port}")
                        self._api = ProxmoxAPI(
                            hostname,
                            port=port,
                            user=self.username,
                            token_name=token_id,
                            token_value=token_secret,
                            verify_ssl=verify_ssl
                        )
                    else:
                        # No port specified, use URL format
                        logger.debug(f"Trying ProxmoxAPI with URL={clean_url}")
                        self._api = ProxmoxAPI(
                            clean_url,
                            user=self.username,
                            token_name=token_id,
                            token_value=token_secret,
                            verify_ssl=verify_ssl
                        )
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check for SSL certificate errors
                    if "SSL" in error_msg or "certificate" in error_msg.lower() or "CERTIFICATE_VERIFY_FAILED" in error_msg:
                        logger.warning(f"SSL certificate verification failed for {clean_url}")
                        logger.warning(f"This usually means Proxmox is using a self-signed certificate.")
                        logger.warning(f"Current verify_ssl setting: {verify_ssl}")
                        if verify_ssl = verify_ssl
                            raise ValueError(
                                f"SSL certificate verification failed for {clean_url}. "
                                f"This usually means Proxmox is using a self-signed certificate. "
                                f"To disable SSL verification (for testing only), uncheck 'Verify SSL Certificate' in the node settings in web UI. "
                                f"Note: Disabling SSL verification is a security risk and should only be used in trusted networks."
                            ) from e
                        else:
                            # SSL verification is already disabled, but still getting SSL error
                            raise ValueError(
                                f"SSL connection failed for {clean_url} even with SSL verification disabled. "
                                f"Error: {error_msg}. "
                                f"Please check that the Proxmox node is accessible and the URL is correct."
                            ) from e
                    
                    # If we get IPv6 error, it's a known proxmoxer bug
                    # Try using hostname instead of IP if it's an IP address
                    if "Invalid IPv6 URL" in error_msg or "IPv6" in error_msg:
                        logger.warning(f"ProxmoxAPI failed with cleaned URL '{clean_url}' due to IPv6 error (proxmoxer bug).")
                        logger.warning(f"This is a known bug in proxmoxer 2.0.1. Trying workaround...")
                        
                        # Workaround: Try using the hostname directly if we can resolve it
                        # Otherwise, we'll need to use a different approach
                        try:
                            import socket
                            # Try to get hostname from IP
                            try:
                                hostname_resolved = socket.gethostbyaddr(hostname)[0]
                                logger.info(f"Resolved {hostname} to hostname: {hostname_resolved}")
                                url_with_hostname = f"{parsed.scheme}://{hostname_resolved}:{port}"
                                logger.info(f"Trying with hostname instead of IP: {url_with_hostname}")
                                self._api = ProxmoxAPI(
                                    url_with_hostname,
                                    user=self.username,
                                    token_name=token_id,
                                    token_value=token_secret,
                                    verify_ssl=verify_ssl
                                )
                            except (socket.herror, socket.gaierror):
                                # Can't resolve hostname, try one more time with original URL
                                logger.warning(f"Could not resolve hostname for {hostname}, trying original URL format")
                                raise ValueError(f"Proxmoxer library bug: Cannot connect to {clean_url}. This is a known issue with proxmoxer 2.0.1. Please try using a hostname instead of IP address, or upgrade proxmoxer library.")
                        except Exception as fallback_error:
                            # If all else fails, raise a helpful error message
                            raise ValueError(
                                f"Failed to connect to Proxmox node at {clean_url}. "
                                f"This appears to be a bug in proxmoxer 2.0.1 library. "
                                f"Error: {error_msg}. "
                                f"Try using a hostname instead of IP address, or check if there's an updated version of proxmoxer."
                            ) from e
                    else:
                        # Re-raise if it's a different error
                        raise
                
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
            # ValueError usually means URL format issue or SSL certificate issue
            error_msg = str(e)
            logger.error(f"Connection test failed - Invalid URL format or SSL issue: {error_msg}")
            logger.error(f"URL was: {self.url}, verify_ssl={self.verify_ssl}")
            # Check if it's an SSL certificate error
            if "SSL certificate" in error_msg or "SSL verification" in error_msg:
                logger.error(f"SSL certificate verification failed. Current verify_ssl setting: {self.verify_ssl}")
                if self.verify_ssl:
                    logger.error("To disable SSL verification, set verify_ssl=False when creating ProxmoxClient, or disable it in the node settings in web UI.")
            return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")
            logger.error(f"URL: {self.url}, Username: {self.username}, verify_ssl={self.verify_ssl}")
            
            # Check for SSL certificate errors
            if "SSL" in error_msg or "certificate" in error_msg.lower() or "CERTIFICATE_VERIFY_FAILED" in error_msg:
                logger.error(f"SSL certificate verification failed. Current verify_ssl setting: {self.verify_ssl}")
                if self.verify_ssl:
                    logger.error("This usually means Proxmox is using a self-signed certificate.")
                    logger.error("To disable SSL verification, set verify_ssl=False when creating ProxmoxClient, or disable it in the node settings in web UI.")
                else:
                    logger.error("SSL verification is disabled but still getting SSL error. Check that the Proxmox node is accessible.")
            
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


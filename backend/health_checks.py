import httpx
import socket
import subprocess
import platform
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthChecker:
    @staticmethod
    async def check_http(url: str, timeout: int = 5, expected_status: int = 200) -> Dict:
        """
        Check HTTP/HTTPS endpoint
        
        Returns:
            {
                "status": "up" | "down" | "warning",
                "response_time": float (milliseconds),
                "status_code": int,
                "error_message": str | None
            }
        """
        start_time = datetime.now()
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == expected_status:
                    return {
                        "status": "up",
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "error_message": None
                    }
                else:
                    return {
                        "status": "warning",
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "error_message": f"Expected status {expected_status}, got {response.status_code}"
                    }
        except httpx.TimeoutException:
            return {
                "status": "down",
                "response_time": None,
                "status_code": None,
                "error_message": f"Request timeout after {timeout} seconds"
            }
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "status": "down",
                "response_time": response_time if response_time < timeout * 1000 else None,
                "status_code": None,
                "error_message": str(e)
            }

    @staticmethod
    def check_port(host: str, port: int, timeout: int = 3) -> Dict:
        """
        Check if a port is open
        
        Returns:
            {
                "status": "up" | "down",
                "response_time": float (milliseconds) | None,
                "error_message": str | None
            }
        """
        start_time = datetime.now()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            sock.close()
            
            if result == 0:
                return {
                    "status": "up",
                    "response_time": response_time,
                    "error_message": None
                }
            else:
                return {
                    "status": "down",
                    "response_time": None,
                    "error_message": f"Port {port} is not open"
                }
        except Exception as e:
            return {
                "status": "down",
                "response_time": None,
                "error_message": str(e)
            }

    @staticmethod
    def check_ping(host: str, timeout: int = 3, count: int = 1) -> Dict:
        """
        Check if host responds to ping
        
        Returns:
            {
                "status": "up" | "down",
                "response_time": float (milliseconds) | None,
                "error_message": str | None
            }
        """
        try:
            # Determine ping command based on OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 1
            )
            
            if result.returncode == 0:
                # Try to extract response time from output
                response_time = None
                output = result.stdout
                if "time=" in output or "time<" in output:
                    # Parse ping time (format varies by OS)
                    import re
                    time_match = re.search(r'time[<=](\d+\.?\d*)', output)
                    if time_match:
                        response_time = float(time_match.group(1))
                
                return {
                    "status": "up",
                    "response_time": response_time,
                    "error_message": None
                }
            else:
                return {
                    "status": "down",
                    "response_time": None,
                    "error_message": "Host did not respond to ping"
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "down",
                "response_time": None,
                "error_message": f"Ping timeout after {timeout} seconds"
            }
        except Exception as e:
            return {
                "status": "down",
                "response_time": None,
                "error_message": str(e)
            }

    @staticmethod
    def check_custom(command: str, script: Optional[str] = None, timeout: int = 30) -> Dict:
        """
        Execute custom health check command or script
        
        Args:
            command: Command to execute (e.g., "curl -f http://example.com || exit 1")
            script: Optional script content to execute
            timeout: Timeout in seconds
        
        Returns:
            {
                "status": "up" | "down",
                "response_time": float (milliseconds) | None,
                "error_message": str | None
            }
        """
        start_time = datetime.now()
        try:
            if script:
                # Execute script content
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
                    f.write(script)
                    script_path = f.name
                
                try:
                    # Make script executable
                    os.chmod(script_path, 0o755)
                    
                    # Execute script
                    result = subprocess.run(
                        [script_path],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        shell=True
                    )
                    
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if result.returncode == 0:
                        return {
                            "status": "up",
                            "response_time": response_time,
                            "error_message": None
                        }
                    else:
                        return {
                            "status": "down",
                            "response_time": response_time,
                            "error_message": result.stderr or f"Script exited with code {result.returncode}"
                        }
                finally:
                    # Clean up script file
                    try:
                        os.unlink(script_path)
                    except:
                        pass
            else:
                # Execute command directly
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True
                )
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if result.returncode == 0:
                    return {
                        "status": "up",
                        "response_time": response_time,
                        "error_message": None
                    }
                else:
                    return {
                        "status": "down",
                        "response_time": response_time,
                        "error_message": result.stderr or f"Command exited with code {result.returncode}"
                    }
        except subprocess.TimeoutExpired:
            return {
                "status": "down",
                "response_time": None,
                "error_message": f"Custom check timeout after {timeout} seconds"
            }
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "status": "down",
                "response_time": response_time if response_time < timeout * 1000 else None,
                "error_message": str(e)
            }

    @staticmethod
    async def check_service(service_type: str, target: str, port: Optional[int] = None, 
                           timeout: int = 5, expected_status: int = 200,
                           custom_command: Optional[str] = None,
                           custom_script: Optional[str] = None) -> Dict:
        """
        Generic service check based on type
        
        Args:
            service_type: "http", "https", "ping", "port", "custom"
            target: URL, IP, or hostname
            port: Port number (for port checks)
            timeout: Timeout in seconds
            expected_status: Expected HTTP status code
            custom_command: Custom command to execute (for custom type)
            custom_script: Custom script content (for custom type)
        """
        if service_type == "custom":
            if not custom_command and not custom_script:
                return {
                    "status": "down",
                    "response_time": None,
                    "error_message": "Custom command or script required for custom health checks"
                }
            return HealthChecker.check_custom(custom_command or "", custom_script, timeout)
        elif service_type in ["http", "https"]:
            return await HealthChecker.check_http(target, timeout, expected_status)
        elif service_type == "ping":
            return HealthChecker.check_ping(target, timeout)
        elif service_type == "port":
            if port is None:
                return {
                    "status": "down",
                    "response_time": None,
                    "error_message": "Port number required for port checks"
                }
            return HealthChecker.check_port(target, port, timeout)
        else:
            return {
                "status": "down",
                "response_time": None,
                "error_message": f"Unknown service type: {service_type}"
            }


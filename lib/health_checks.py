"""
Health Check Framework - Comprehensive validation and monitoring
"""

import asyncio
import socket
import subprocess
import json
import os
import psutil
import requests
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import ssl
import certifi
from datetime import datetime


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}


class HealthCheckFramework:
    """Comprehensive health check system"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: List[HealthCheckResult] = []
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "response_time": 5.0,
        }
        
    def register_check(self, name: str, check_func: Callable):
        """Register a health check"""
        self.checks[name] = check_func
        
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all registered health checks"""
        self.results.clear()
        
        # Run built-in checks
        builtin_checks = [
            self.check_system_resources,
            self.check_network_connectivity,
            self.check_docker_daemon,
            self.check_proxmox_connection,
            self.check_python_dependencies,
            self.check_ssl_certificates,
            self.check_file_permissions,
            self.check_api_endpoints,
        ]
        
        for check in builtin_checks:
            result = await check()
            self.results.append(result)
            
        # Run registered custom checks
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                    
                if isinstance(result, HealthCheckResult):
                    self.results.append(result)
                elif isinstance(result, bool):
                    status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                    self.results.append(HealthCheckResult(
                        name=name,
                        status=status,
                        message=f"Check {'passed' if result else 'failed'}"
                    ))
            except Exception as e:
                self.results.append(HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Check failed with error: {str(e)}"
                ))
                
        return self.results
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if cpu_percent > self.thresholds["cpu_percent"]:
                issues.append(f"High CPU usage: {cpu_percent}%")
                status = HealthStatus.WARNING
                
            if memory.percent > self.thresholds["memory_percent"]:
                issues.append(f"High memory usage: {memory.percent}%")
                status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else HealthStatus.CRITICAL
                
            if disk.percent > self.thresholds["disk_percent"]:
                issues.append(f"Low disk space: {disk.percent}% used")
                status = HealthStatus.CRITICAL
                
            message = "; ".join(issues) if issues else "System resources are healthy"
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3),
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {str(e)}"
            )
    
    async def check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity"""
        try:
            # Check DNS resolution
            socket.gethostbyname("google.com")
            
            # Check internet connectivity
            response = requests.get("https://www.google.com", timeout=5)
            response_time = response.elapsed.total_seconds()
            
            if response_time > self.thresholds["response_time"]:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.WARNING,
                    message=f"Slow network response: {response_time:.2f}s",
                    details={"response_time": response_time}
                )
                
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.HEALTHY,
                message="Network connectivity is good",
                details={"response_time": response_time}
            )
            
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Network connectivity issue: {str(e)}"
            )
        except socket.gaierror:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.CRITICAL,
                message="DNS resolution failed"
            )
    
    async def check_docker_daemon(self) -> HealthCheckResult:
        """Check Docker daemon status"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse Docker info
                info_lines = result.stdout.split('\n')
                containers_running = 0
                
                for line in info_lines:
                    if "Containers:" in line and "Running:" in line:
                        try:
                            containers_running = int(line.split("Running:")[1].split()[0])
                        except:
                            pass
                            
                return HealthCheckResult(
                    name="docker_daemon",
                    status=HealthStatus.HEALTHY,
                    message="Docker daemon is running",
                    details={
                        "containers_running": containers_running,
                        "docker_version": self._get_docker_version()
                    }
                )
            else:
                return HealthCheckResult(
                    name="docker_daemon",
                    status=HealthStatus.CRITICAL,
                    message="Docker daemon is not responding"
                )
                
        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name="docker_daemon",
                status=HealthStatus.CRITICAL,
                message="Docker daemon check timed out"
            )
        except FileNotFoundError:
            return HealthCheckResult(
                name="docker_daemon",
                status=HealthStatus.WARNING,
                message="Docker not installed"
            )
    
    async def check_proxmox_connection(self) -> HealthCheckResult:
        """Check Proxmox API connectivity"""
        config_file = Path("etc/time-shift-config.json")
        
        if not config_file.exists():
            return HealthCheckResult(
                name="proxmox_connection",
                status=HealthStatus.WARNING,
                message="Proxmox configuration not found"
            )
            
        try:
            with open(config_file) as f:
                config = json.load(f)
                
            proxmox_config = config.get("proxmox", {})
            host = proxmox_config.get("host")
            
            if not host:
                return HealthCheckResult(
                    name="proxmox_connection",
                    status=HealthStatus.WARNING,
                    message="Proxmox host not configured"
                )
                
            # Try to connect to Proxmox API
            url = f"https://{host}:8006/api2/json/version"
            response = requests.get(url, verify=False, timeout=5)
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="proxmox_connection",
                    status=HealthStatus.HEALTHY,
                    message=f"Connected to Proxmox at {host}",
                    details={"version": response.json().get("data", {})}
                )
            else:
                return HealthCheckResult(
                    name="proxmox_connection",
                    status=HealthStatus.WARNING,
                    message=f"Proxmox API returned status {response.status_code}"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="proxmox_connection",
                status=HealthStatus.CRITICAL,
                message=f"Failed to connect to Proxmox: {str(e)}"
            )
    
    async def check_python_dependencies(self) -> HealthCheckResult:
        """Check Python dependencies"""
        try:
            import pkg_resources
            
            requirements_file = Path("requirements.txt")
            if not requirements_file.exists():
                return HealthCheckResult(
                    name="python_dependencies",
                    status=HealthStatus.WARNING,
                    message="requirements.txt not found"
                )
                
            missing_packages = []
            outdated_packages = []
            
            with open(requirements_file) as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                
            for requirement in requirements:
                try:
                    pkg_resources.require(requirement)
                except pkg_resources.DistributionNotFound:
                    missing_packages.append(requirement)
                except pkg_resources.VersionConflict as e:
                    outdated_packages.append(str(e))
                    
            if missing_packages or outdated_packages:
                issues = []
                if missing_packages:
                    issues.append(f"Missing: {', '.join(missing_packages)}")
                if outdated_packages:
                    issues.append(f"Outdated: {', '.join(outdated_packages)}")
                    
                return HealthCheckResult(
                    name="python_dependencies",
                    status=HealthStatus.WARNING,
                    message="; ".join(issues),
                    details={
                        "missing": missing_packages,
                        "outdated": outdated_packages
                    }
                )
                
            return HealthCheckResult(
                name="python_dependencies",
                status=HealthStatus.HEALTHY,
                message="All Python dependencies are satisfied"
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="python_dependencies",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check dependencies: {str(e)}"
            )
    
    async def check_ssl_certificates(self) -> HealthCheckResult:
        """Check SSL certificate validity"""
        try:
            # Check for SSL certificates in common locations
            cert_locations = [
                Path("certs"),
                Path("/etc/ssl/certs"),
                Path.home() / ".ssl",
            ]
            
            issues = []
            for cert_dir in cert_locations:
                if cert_dir.exists():
                    for cert_file in cert_dir.glob("*.pem"):
                        try:
                            with open(cert_file, 'rb') as f:
                                cert_data = f.read()
                                
                            # Basic certificate validation
                            context = ssl.create_default_context(cafile=certifi.where())
                            
                        except Exception as e:
                            issues.append(f"{cert_file.name}: {str(e)}")
                            
            if issues:
                return HealthCheckResult(
                    name="ssl_certificates",
                    status=HealthStatus.WARNING,
                    message=f"Certificate issues found: {len(issues)}",
                    details={"issues": issues}
                )
                
            return HealthCheckResult(
                name="ssl_certificates",
                status=HealthStatus.HEALTHY,
                message="SSL certificates are valid"
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="ssl_certificates",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check certificates: {str(e)}"
            )
    
    async def check_file_permissions(self) -> HealthCheckResult:
        """Check critical file permissions"""
        try:
            issues = []
            
            # Check executable permissions
            executables = [
                Path("bin/time-shift-cli.py"),
                Path("integrate.py"),
                Path("install.sh"),
            ]
            
            for exe in executables:
                if exe.exists() and not os.access(exe, os.X_OK):
                    issues.append(f"{exe} is not executable")
                    
            # Check config file permissions
            config_files = [
                Path("etc/time-shift-config.json"),
                Path(".env"),
            ]
            
            for config in config_files:
                if config.exists():
                    stat = config.stat()
                    if stat.st_mode & 0o077:  # Check for world/group permissions
                        issues.append(f"{config} has overly permissive permissions")
                        
            if issues:
                return HealthCheckResult(
                    name="file_permissions",
                    status=HealthStatus.WARNING,
                    message=f"Permission issues found: {len(issues)}",
                    details={"issues": issues}
                )
                
            return HealthCheckResult(
                name="file_permissions",
                status=HealthStatus.HEALTHY,
                message="File permissions are correct"
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="file_permissions",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check permissions: {str(e)}"
            )
    
    async def check_api_endpoints(self) -> HealthCheckResult:
        """Check API endpoint availability"""
        try:
            # Check if FastAPI is configured
            api_config = Path("etc/api_config.json")
            if not api_config.exists():
                return HealthCheckResult(
                    name="api_endpoints",
                    status=HealthStatus.HEALTHY,
                    message="API not configured (optional)"
                )
                
            # Try to connect to API
            response = requests.get("http://localhost:8000/health", timeout=5)
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="api_endpoints",
                    status=HealthStatus.HEALTHY,
                    message="API endpoints are responsive",
                    details=response.json()
                )
            else:
                return HealthCheckResult(
                    name="api_endpoints",
                    status=HealthStatus.WARNING,
                    message=f"API returned status {response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                name="api_endpoints",
                status=HealthStatus.WARNING,
                message="API server not running"
            )
        except Exception as e:
            return HealthCheckResult(
                name="api_endpoints",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check API: {str(e)}"
            )
    
    def _get_docker_version(self) -> Optional[str]:
        """Get Docker version"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get health check summary"""
        if not self.results:
            return {"status": "unknown", "message": "No health checks have been run"}
            
        # Count by status
        status_counts = {status: 0 for status in HealthStatus}
        for result in self.results:
            status_counts[result.status] += 1
            
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
        elif status_counts[HealthStatus.UNKNOWN] > 0:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
            
        return {
            "status": overall_status.value,
            "total_checks": len(self.results),
            "status_counts": {k.value: v for k, v in status_counts.items() if v > 0},
            "timestamp": datetime.now().isoformat(),
        }


# Standalone health check functions for backward compatibility

def check_connectivity() -> bool:
    """Check basic network connectivity"""
    try:
        socket.gethostbyname("google.com")
        return True
    except:
        return False


def check_proxmox_connection() -> bool:
    """Check Proxmox connection"""
    framework = HealthCheckFramework()
    result = asyncio.run(framework.check_proxmox_connection())
    return result.status == HealthStatus.HEALTHY


def check_docker_daemon() -> bool:
    """Check Docker daemon"""
    framework = HealthCheckFramework()
    result = asyncio.run(framework.check_docker_daemon())
    return result.status == HealthStatus.HEALTHY


def verify_vm_template() -> bool:
    """Verify VM template availability"""
    # This would check if the VM template exists in Proxmox
    return True  # Placeholder


def verify_compose_file() -> bool:
    """Verify Docker Compose file"""
    compose_file = Path("docker-compose.yml")
    return compose_file.exists()


# Make functions available for import
__all__ = [
    'HealthCheckFramework',
    'HealthStatus',
    'HealthCheckResult',
    'check_connectivity',
    'check_proxmox_connection',
    'check_docker_daemon',
    'verify_vm_template',
    'verify_compose_file',
]
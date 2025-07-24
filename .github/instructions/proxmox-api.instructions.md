---
applyTo: ["lib/proxmox_api.py", "lib/proxmox_api_async.py", "**/proxmox/**", "**/*proxmox*"]
---

# Proxmox API Integration Instructions

## Proxmox API Client Patterns

### Basic Client Configuration
```python
from lib.proxmox_api import ProxmoxAPI
from lib.config_models import ProxmoxConfig
import aiohttp
import ssl

class ProxmoxClient:
    """Proxmox VE API client with proper configuration"""
    
    def __init__(self, config: ProxmoxConfig):
        self.config = config
        self.base_url = f"https://{config.host}:{config.port}/api2/json"
        self.session = None
        self.ticket = None
        
        # SSL configuration - often disabled for internal Proxmox
        if not config.verify_ssl:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        else:
            self.ssl_context = ssl.create_default_context()
    
    async def authenticate(self) -> str:
        """Authenticate and get ticket"""
        auth_data = {
            'username': self.config.username,
            'password': self.config.password
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.ssl_context),
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as session:
            async with session.post(f"{self.base_url}/access/ticket", data=auth_data) as response:
                response.raise_for_status()
                result = await response.json()
                
                self.ticket = result['data']['ticket']
                self.csrf_token = result['data']['CSRFPreventionToken']
                
                return self.ticket
```

### VM Management Operations
```python
from typing import Dict, List, Any, Optional

class ProxmoxVMManager:
    """VM lifecycle management"""
    
    def __init__(self, client: ProxmoxClient):
        self.client = client
        self.node = client.config.node
    
    async def create_vm(self, vmid: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new VM with configuration"""
        # Default VM configuration for time-shift VMs
        default_config = {
            'vmid': vmid,
            'name': f'time-shift-vm-{vmid}',
            'memory': 2048,
            'cores': 2,
            'sockets': 1,
            'ostype': 'l26',  # Linux 2.6+
            'net0': 'virtio,bridge=vmbr0',
            'ide2': 'none,media=cdrom',
            'boot': 'cdn',
            'agent': 1,  # Enable QEMU guest agent
            'start': 0   # Don't auto-start
        }
        
        # Merge provided config with defaults
        vm_config = {**default_config, **config}
        
        endpoint = f"/nodes/{self.node}/qemu"
        return await self.client.post(endpoint, data=vm_config)
    
    async def get_vm_status(self, vmid: int) -> Dict[str, Any]:
        """Get VM status and configuration"""
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/status/current"
        return await self.client.get(endpoint)
    
    async def start_vm(self, vmid: int) -> str:
        """Start VM and return task ID"""
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/status/start"
        result = await self.client.post(endpoint)
        return result['data']  # Task ID
    
    async def stop_vm(self, vmid: int, force: bool = False) -> str:
        """Stop VM gracefully or forcefully"""
        action = "stop" if not force else "shutdown"
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/status/{action}"
        result = await self.client.post(endpoint)
        return result['data']
    
    async def clone_vm(self, vmid: int, newid: int, name: str = None) -> str:
        """Clone existing VM"""
        clone_config = {
            'newid': newid,
            'name': name or f'clone-of-{vmid}',
            'full': 1,  # Full clone
            'target': self.node
        }
        
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/clone"
        result = await self.client.post(endpoint, data=clone_config)
        return result['data']
    
    async def delete_vm(self, vmid: int, purge: bool = True) -> str:
        """Delete VM and optionally purge from configs"""
        params = {'purge': 1} if purge else {}
        endpoint = f"/nodes/{self.node}/qemu/{vmid}"
        result = await self.client.delete(endpoint, params=params)
        return result['data']
```

### Template Management
```python
class ProxmoxTemplateManager:
    """Manage VM templates for time-shift operations"""
    
    def __init__(self, client: ProxmoxClient):
        self.client = client
        self.node = client.config.node
    
    async def create_time_shift_template(self, base_vmid: int, template_vmid: int) -> str:
        """Create time-shift template from base VM"""
        # First, clone the base VM
        clone_config = {
            'newid': template_vmid,
            'name': 'time-shift-template',
            'full': 1,
            'target': self.node
        }
        
        endpoint = f"/nodes/{self.node}/qemu/{base_vmid}/clone"
        result = await self.client.post(endpoint, data=clone_config)
        task_id = result['data']
        
        # Wait for clone to complete
        await self.wait_for_task(task_id)
        
        # Convert to template
        endpoint = f"/nodes/{self.node}/qemu/{template_vmid}/template"
        await self.client.post(endpoint)
        
        return template_vmid
    
    async def deploy_from_template(self, template_vmid: int, new_vmid: int, 
                                 vm_config: Dict[str, Any]) -> str:
        """Deploy new VM from template"""
        # Clone from template
        clone_result = await self.clone_vm(template_vmid, new_vmid, 
                                         vm_config.get('name', f'time-shift-{new_vmid}'))
        
        # Wait for clone completion
        await self.wait_for_task(clone_result)
        
        # Apply additional configuration
        if vm_config:
            endpoint = f"/nodes/{self.node}/qemu/{new_vmid}/config"
            await self.client.post(endpoint, data=vm_config)
        
        return new_vmid
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates"""
        endpoint = f"/nodes/{self.node}/qemu"
        result = await self.client.get(endpoint)
        
        # Filter only templates
        templates = [vm for vm in result['data'] if vm.get('template', 0) == 1]
        return templates
```

### Task Management
```python
import asyncio
from enum import Enum

class TaskStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    
class ProxmoxTaskManager:
    """Handle Proxmox task monitoring"""
    
    def __init__(self, client: ProxmoxClient):
        self.client = client
        self.node = client.config.node
    
    async def wait_for_task(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for task completion with timeout"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
            
            status = await self.get_task_status(task_id)
            
            if status['status'] == TaskStatus.STOPPED:
                if status.get('exitstatus') == 'OK':
                    return status
                else:
                    raise RuntimeError(f"Task {task_id} failed: {status.get('exitstatus')}")
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        endpoint = f"/nodes/{self.node}/tasks/{task_id}/status"
        result = await self.client.get(endpoint)
        return result['data']
    
    async def get_task_log(self, task_id: str, start: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task log entries"""
        endpoint = f"/nodes/{self.node}/tasks/{task_id}/log"
        params = {'start': start, 'limit': limit}
        result = await self.client.get(endpoint, params=params)
        return result['data']
    
    async def list_tasks(self, running_only: bool = False) -> List[Dict[str, Any]]:
        """List node tasks"""
        endpoint = f"/nodes/{self.node}/tasks"
        params = {'running': 1} if running_only else {}
        result = await self.client.get(endpoint, params=params)
        return result['data']
```

### Storage and Backup Management
```python
class ProxmoxStorageManager:
    """Manage storage and backups"""
    
    def __init__(self, client: ProxmoxClient):
        self.client = client
        self.node = client.config.node
    
    async def list_storage(self) -> List[Dict[str, Any]]:
        """List available storage"""
        endpoint = f"/nodes/{self.node}/storage"
        result = await self.client.get(endpoint)
        return result['data']
    
    async def create_backup(self, vmid: int, storage: str, mode: str = 'snapshot') -> str:
        """Create VM backup"""
        backup_config = {
            'vmid': vmid,
            'storage': storage,
            'mode': mode,  # snapshot, suspend, stop
            'compress': 'gzip',
            'notes': f'Time-shift backup created at {datetime.now().isoformat()}'
        }
        
        endpoint = f"/nodes/{self.node}/vzdump"
        result = await self.client.post(endpoint, data=backup_config)
        return result['data']
    
    async def restore_backup(self, archive: str, vmid: int, storage: str = None) -> str:
        """Restore VM from backup"""
        restore_config = {
            'archive': archive,
            'vmid': vmid,
            'force': 1  # Overwrite existing VM
        }
        
        if storage:
            restore_config['storage'] = storage
        
        endpoint = f"/nodes/{self.node}/qemu"
        result = await self.client.post(endpoint, data=restore_config)
        return result['data']
```

### Network Configuration
```python
class ProxmoxNetworkManager:
    """Manage VM network configuration"""
    
    def __init__(self, client: ProxmoxClient):
        self.client = client
        self.node = client.config.node
    
    async def list_networks(self) -> List[Dict[str, Any]]:
        """List available networks/bridges"""
        endpoint = f"/nodes/{self.node}/network"
        result = await self.client.get(endpoint)
        return result['data']
    
    async def configure_vm_network(self, vmid: int, network_config: Dict[str, str]) -> None:
        """Configure VM network interfaces"""
        # Example network_config:
        # {
        #     'net0': 'virtio,bridge=vmbr0,firewall=1',
        #     'net1': 'virtio,bridge=vmbr1,tag=100'
        # }
        
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/config"
        await self.client.post(endpoint, data=network_config)
    
    async def get_vm_network_info(self, vmid: int) -> Dict[str, Any]:
        """Get VM network interface information"""
        endpoint = f"/nodes/{self.node}/qemu/{vmid}/agent/network-get-interfaces"
        try:
            result = await self.client.get(endpoint)
            return result['data']
        except Exception:
            # Guest agent might not be running
            return {}
```

## Best Practices

### 1. Authentication & Security
- Always use ticket-based authentication
- Implement proper SSL context handling
- Handle authentication token renewal
- Log authentication events

### 2. Error Handling
```python
from aiohttp import ClientError, ClientResponseError

async def robust_api_call(self, endpoint: str, method: str = 'GET', **kwargs):
    """Make API call with comprehensive error handling"""
    try:
        response = await self.client.request(method, endpoint, **kwargs)
        return response
    except ClientResponseError as e:
        if e.status == 401:
            # Token expired, re-authenticate
            await self.authenticate()
            return await self.client.request(method, endpoint, **kwargs)
        elif e.status == 403:
            raise PermissionError(f"Insufficient permissions for {endpoint}")
        elif e.status == 404:
            raise ValueError(f"Resource not found: {endpoint}")
        else:
            raise
    except ClientError as e:
        logger.error(f"Network error accessing Proxmox API: {e}")
        raise ConnectionError(f"Failed to connect to Proxmox API: {e}")
```

### 3. Resource Management
- Always close sessions properly
- Implement connection pooling for high-throughput operations
- Use context managers for resource cleanup
- Monitor and limit concurrent connections

### 4. Configuration Validation
```python
def validate_vm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate VM configuration before creation"""
    required_fields = ['vmid', 'memory', 'cores']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate resource limits
    if config['memory'] < 512:
        raise ValueError("Minimum memory is 512MB")
    
    if config['cores'] < 1 or config['cores'] > 32:
        raise ValueError("Cores must be between 1 and 32")
    
    return config
```

### 5. Monitoring & Logging
- Log all VM lifecycle operations
- Monitor task completion status
- Track resource usage and quotas
- Implement health checks for API connectivity

### Common Patterns to Follow

1. **Async Context Managers**: Use for session management
2. **Task Monitoring**: Always wait for long-running operations
3. **Configuration Validation**: Validate before API calls
4. **Error Recovery**: Implement retry logic for transient failures
5. **Resource Cleanup**: Proper cleanup of failed operations
6. **Security**: Never log credentials, use proper SSL configuration
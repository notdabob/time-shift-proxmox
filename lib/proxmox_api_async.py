"""
Proxmox API Module - Async version with connection pooling
Handles all interactions with the Proxmox Virtual Environment API
"""

import aiohttp
import json
import ssl
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
from lib.validators import validate_ip_address, validate_port, validate_username

logger = logging.getLogger(__name__)


class ProxmoxAPIAsync:
    """Async Proxmox API client with connection pooling"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Proxmox API client
        
        Args:
            config: Proxmox configuration parameters
        """
        self.host = validate_ip_address(config.get('host')) if '.' in str(config.get('host', '')) else config.get('host')
        self.port = validate_port(config.get('port', 8006))
        self.username = validate_username(config.get('username'))
        self.password = config.get('password')
        self.node = config.get('node')
        self.verify_ssl = config.get('verify_ssl', False)
        
        self.base_url = f"https://{self.host}:{self.port}/api2/json"
        
        # Connection pooling settings
        self.connector = None
        self.session = None
        
        # Authentication tokens
        self.ticket = None
        self.csrf_token = None
        self.ticket_expiry = None
        
        # SSL context
        self.ssl_context = ssl.create_default_context()
        if not self.verify_ssl:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Create connection pool and session"""
        if not self.session:
            self.connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool size
                limit_per_host=5,
                ttl_dns_cache=300,
                ssl=self.ssl_context
            )
            self.session = aiohttp.ClientSession(connector=self.connector)
            logger.info("Created async session with connection pooling")
    
    async def close(self):
        """Close session and connection pool"""
        if self.session:
            await self.session.close()
            self.session = None
            self.connector = None
            logger.info("Closed async session")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Proxmox and get ticket/CSRF token
        
        Returns:
            bool: True if authentication successful
        """
        if not self.session:
            await self.connect()
            
        auth_data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/access/ticket",
                data=auth_data
            ) as response:
                response.raise_for_status()
                
                data = (await response.json())['data']
                self.ticket = data['ticket']
                self.csrf_token = data['CSRFPreventionToken']
                
                # Tickets typically expire after 2 hours
                self.ticket_expiry = datetime.now() + timedelta(hours=2)
                
                # Update session headers
                self.session.headers.update({
                    'CSRFPreventionToken': self.csrf_token
                })
                self.session.cookie_jar.update_cookies(
                    {'PVEAuthCookie': self.ticket}
                )
                
                logger.info("Successfully authenticated with Proxmox")
                return True
                
        except aiohttp.ClientError as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if not self.ticket or not self.ticket_expiry:
            return await self.authenticate()
        
        # Check if ticket is about to expire (5 minutes buffer)
        if datetime.now() >= self.ticket_expiry - timedelta(minutes=5):
            logger.info("Ticket about to expire, re-authenticating")
            return await self.authenticate()
            
        return True
    
    async def get_vm_status(self, vm_id: int) -> Optional[Dict[str, Any]]:
        """
        Get VM status information
        
        Args:
            vm_id: VM ID
            
        Returns:
            VM status information or None if failed
        """
        if not await self.ensure_authenticated():
            return None
        
        try:
            async with self.session.get(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/current"
            ) as response:
                response.raise_for_status()
                return (await response.json())['data']
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get VM status: {e}")
            return None
    
    async def start_vm(self, vm_id: int) -> bool:
        """
        Start a VM
        
        Args:
            vm_id: VM ID
            
        Returns:
            True if successful
        """
        if not await self.ensure_authenticated():
            return False
        
        try:
            async with self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/start"
            ) as response:
                response.raise_for_status()
                logger.info(f"VM {vm_id} start command sent")
                return True
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to start VM: {e}")
            return False
    
    async def stop_vm(self, vm_id: int) -> bool:
        """
        Stop a VM
        
        Args:
            vm_id: VM ID
            
        Returns:
            True if successful
        """
        if not await self.ensure_authenticated():
            return False
        
        try:
            async with self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/stop"
            ) as response:
                response.raise_for_status()
                logger.info(f"VM {vm_id} stop command sent")
                return True
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to stop VM: {e}")
            return False
    
    async def execute_vm_command(self, vm_id: int, command: str) -> Optional[Dict[str, Any]]:
        """
        Execute command in VM (requires qemu-guest-agent)
        
        Args:
            vm_id: VM ID
            command: Command to execute
            
        Returns:
            Command execution result or None if failed
        """
        if not await self.ensure_authenticated():
            return None
        
        try:
            data = {'command': command}
            
            async with self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/agent/exec",
                data=data
            ) as response:
                response.raise_for_status()
                return (await response.json())['data']
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to execute command in VM: {e}")
            return None
    
    async def create_vm_snapshot(self, vm_id: int, snapshot_name: str) -> bool:
        """
        Create VM snapshot
        
        Args:
            vm_id: VM ID
            snapshot_name: Name for the snapshot
            
        Returns:
            True if successful
        """
        if not await self.ensure_authenticated():
            return False
        
        try:
            data = {
                'snapname': snapshot_name,
                'description': f"Time-shift snapshot created at {datetime.now()}"
            }
            
            async with self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/snapshot",
                data=data
            ) as response:
                response.raise_for_status()
                logger.info(f"Snapshot '{snapshot_name}' created for VM {vm_id}")
                return True
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to create snapshot: {e}")
            return False
    
    async def list_vms(self) -> Optional[List[Dict[str, Any]]]:
        """
        List all VMs on the node
        
        Returns:
            List of VM information or None if failed
        """
        if not await self.ensure_authenticated():
            return None
        
        try:
            async with self.session.get(
                f"{self.base_url}/nodes/{self.node}/qemu"
            ) as response:
                response.raise_for_status()
                return (await response.json())['data']
                
        except aiohttp.ClientError as e:
            logger.error(f"Failed to list VMs: {e}")
            return None
    
    async def batch_vm_status(self, vm_ids: List[int]) -> Dict[int, Optional[Dict[str, Any]]]:
        """
        Get status for multiple VMs concurrently
        
        Args:
            vm_ids: List of VM IDs
            
        Returns:
            Dict mapping VM ID to status
        """
        import asyncio
        
        tasks = [self.get_vm_status(vm_id) for vm_id in vm_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            vm_id: result if not isinstance(result, Exception) else None
            for vm_id, result in zip(vm_ids, results)
        }


# Migration helper to convert from sync to async
def migrate_to_async(sync_api: 'ProxmoxAPI') -> ProxmoxAPIAsync:
    """
    Create async API instance from sync instance
    
    Args:
        sync_api: Synchronous ProxmoxAPI instance
        
    Returns:
        ProxmoxAPIAsync instance with same configuration
    """
    config = {
        'host': sync_api.host,
        'port': sync_api.port,
        'username': sync_api.username,
        'password': sync_api.password,
        'node': sync_api.node,
        'verify_ssl': sync_api.verify_ssl
    }
    return ProxmoxAPIAsync(config)


# Example usage
async def example_usage():
    """Example of using the async API"""
    config = {
        'host': '192.168.1.100',
        'port': 8006,
        'username': 'root@pam',
        'password': 'your_password',
        'node': 'proxmox-node',
        'verify_ssl': False
    }
    
    # Using context manager
    async with ProxmoxAPIAsync(config) as api:
        # List all VMs
        vms = await api.list_vms()
        if vms:
            print(f"Found {len(vms)} VMs")
            
            # Get status of all VMs concurrently
            vm_ids = [vm['vmid'] for vm in vms]
            statuses = await api.batch_vm_status(vm_ids)
            
            for vm_id, status in statuses.items():
                if status:
                    print(f"VM {vm_id}: {status.get('status', 'unknown')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
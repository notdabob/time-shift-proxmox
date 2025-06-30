"""
Proxmox API Module - Proxmox API interactions
Handles all interactions with the Proxmox Virtual Environment API
"""

import requests
import json
import urllib3
from datetime import datetime
import logging

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxAPI:
    """Proxmox API client for VM management operations"""
    
    def __init__(self, config):
        """
        Initialize Proxmox API client
        
        Args:
            config (dict): Proxmox configuration parameters
        """
        self.host = config.get('host')
        self.port = config.get('port', 8006)
        self.username = config.get('username')
        self.password = config.get('password')
        self.node = config.get('node')
        self.verify_ssl = config.get('verify_ssl', False)
        
        self.base_url = f"https://{self.host}:{self.port}/api2/json"
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        self.ticket = None
        self.csrf_token = None
        
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self):
        """
        Authenticate with Proxmox and get ticket/CSRF token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        auth_data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/access/ticket",
                data=auth_data
            )
            response.raise_for_status()
            
            data = response.json()['data']
            self.ticket = data['ticket']
            self.csrf_token = data['CSRFPreventionToken']
            
            # Set authentication headers
            self.session.headers.update({
                'CSRFPreventionToken': self.csrf_token
            })
            self.session.cookies.set('PVEAuthCookie', self.ticket)
            
            self.logger.info("Successfully authenticated with Proxmox")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def get_vm_status(self, vm_id):
        """
        Get VM status information
        
        Args:
            vm_id (int): VM ID
            
        Returns:
            dict: VM status information or None if failed
        """
        if not self.ticket:
            if not self.authenticate():
                return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/current"
            )
            response.raise_for_status()
            
            return response.json()['data']
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get VM status: {e}")
            return None
    
    def start_vm(self, vm_id):
        """
        Start a VM
        
        Args:
            vm_id (int): VM ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ticket:
            if not self.authenticate():
                return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/start"
            )
            response.raise_for_status()
            
            self.logger.info(f"VM {vm_id} start command sent")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to start VM: {e}")
            return False
    
    def stop_vm(self, vm_id):
        """
        Stop a VM
        
        Args:
            vm_id (int): VM ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ticket:
            if not self.authenticate():
                return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/status/stop"
            )
            response.raise_for_status()
            
            self.logger.info(f"VM {vm_id} stop command sent")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to stop VM: {e}")
            return False
    
    def execute_vm_command(self, vm_id, command):
        """
        Execute command in VM (requires qemu-guest-agent)
        
        Args:
            vm_id (int): VM ID
            command (str): Command to execute
            
        Returns:
            dict: Command execution result or None if failed
        """
        if not self.ticket:
            if not self.authenticate():
                return None
        
        try:
            data = {
                'command': command
            }
            
            response = self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/agent/exec",
                data=data
            )
            response.raise_for_status()
            
            return response.json()['data']
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to execute command in VM: {e}")
            return None
    
    def create_vm_snapshot(self, vm_id, snapshot_name):
        """
        Create VM snapshot
        
        Args:
            vm_id (int): VM ID
            snapshot_name (str): Name for the snapshot
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ticket:
            if not self.authenticate():
                return False
        
        try:
            data = {
                'snapname': snapshot_name,
                'description': f"Time-shift snapshot created at {datetime.now()}"
            }
            
            response = self.session.post(
                f"{self.base_url}/nodes/{self.node}/qemu/{vm_id}/snapshot",
                data=data
            )
            response.raise_for_status()
            
            self.logger.info(f"Snapshot '{snapshot_name}' created for VM {vm_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create snapshot: {e}")
            return False
    
    def list_vms(self):
        """
        List all VMs on the node
        
        Returns:
            list: List of VM information or None if failed
        """
        if not self.ticket:
            if not self.authenticate():
                return None
        
        try:
            response = self.session.get(
                f"{self.base_url}/nodes/{self.node}/qemu"
            )
            response.raise_for_status()
            
            return response.json()['data']
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to list VMs: {e}")
            return None

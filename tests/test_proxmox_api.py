"""
Tests for proxmox_api.py and proxmox_api_async.py
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import requests
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.proxmox_api import ProxmoxAPI
from lib.proxmox_api_async import ProxmoxAPIAsync


class TestProxmoxAPISync:
    """Test cases for synchronous Proxmox API"""
    
    @pytest.fixture
    def config(self):
        """Sample configuration"""
        return {
            'host': '192.168.1.100',
            'port': 8006,
            'username': 'root@pam',
            'password': 'test_password',
            'node': 'proxmox-node',
            'verify_ssl': False
        }
    
    @pytest.fixture
    def api(self, config):
        """Create API instance"""
        return ProxmoxAPI(config)
    
    def test_initialization(self, api, config):
        """Test API initialization"""
        assert api.host == config['host']
        assert api.port == config['port']
        assert api.username == config['username']
        assert api.password == config['password']
        assert api.node == config['node']
        assert api.verify_ssl == config['verify_ssl']
        assert api.base_url == f"https://{config['host']}:{config['port']}/api2/json"
    
    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post, api):
        """Test successful authentication"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'ticket': 'PVE:test_ticket',
                'CSRFPreventionToken': 'test_csrf_token'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = api.authenticate()
        
        assert result is True
        assert api.ticket == 'PVE:test_ticket'
        assert api.csrf_token == 'test_csrf_token'
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post, api):
        """Test failed authentication"""
        mock_post.side_effect = requests.exceptions.RequestException("Auth failed")
        
        result = api.authenticate()
        
        assert result is False
        assert api.ticket is None
        assert api.csrf_token is None
    
    @patch('requests.Session.get')
    def test_get_vm_status(self, mock_get, api):
        """Test getting VM status"""
        api.ticket = 'test_ticket'
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'status': 'running',
                'cpu': 0.5,
                'mem': 1024
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = api.get_vm_status(100)
        
        assert result['status'] == 'running'
        assert result['cpu'] == 0.5
        assert result['mem'] == 1024
    
    @patch('requests.Session.get')
    def test_get_vm_status_no_auth(self, mock_get, api):
        """Test getting VM status without authentication"""
        api.ticket = None
        
        with patch.object(api, 'authenticate', return_value=False):
            result = api.get_vm_status(100)
            assert result is None
    
    @patch('requests.Session.post')
    def test_start_vm(self, mock_post, api):
        """Test starting a VM"""
        api.ticket = 'test_ticket'
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = api.start_vm(100)
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_stop_vm(self, mock_post, api):
        """Test stopping a VM"""
        api.ticket = 'test_ticket'
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = api.stop_vm(100)
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_create_vm_snapshot(self, mock_post, api):
        """Test creating VM snapshot"""
        api.ticket = 'test_ticket'
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = api.create_vm_snapshot(100, 'test_snapshot')
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check that snapshot data was sent
        call_args = mock_post.call_args
        assert call_args[1]['data']['snapname'] == 'test_snapshot'
    
    @patch('requests.Session.get')
    def test_list_vms(self, mock_get, api):
        """Test listing VMs"""
        api.ticket = 'test_ticket'
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {'vmid': 100, 'name': 'vm1'},
                {'vmid': 101, 'name': 'vm2'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = api.list_vms()
        
        assert len(result) == 2
        assert result[0]['vmid'] == 100
        assert result[1]['vmid'] == 101


class TestProxmoxAPIAsync:
    """Test cases for asynchronous Proxmox API"""
    
    @pytest.fixture
    def config(self):
        """Sample configuration"""
        return {
            'host': '192.168.1.100',
            'port': 8006,
            'username': 'root@pam',
            'password': 'test_password',
            'node': 'proxmox-node',
            'verify_ssl': False
        }
    
    @pytest.fixture
    async def api(self, config):
        """Create async API instance"""
        api = ProxmoxAPIAsync(config)
        yield api
        await api.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, config):
        """Test async API initialization"""
        api = ProxmoxAPIAsync(config)
        
        assert api.host == config['host']
        assert api.port == config['port']
        assert api.username == config['username']
        assert api.password == config['password']
        assert api.node == config['node']
        assert api.verify_ssl == config['verify_ssl']
        
        await api.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test async context manager"""
        async with ProxmoxAPIAsync(config) as api:
            assert api.session is not None
            assert api.connector is not None
        
        # After exiting context, session should be closed
        assert api.session is None
        assert api.connector is None
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, api):
        """Test successful async authentication"""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            'data': {
                'ticket': 'PVE:test_ticket',
                'CSRFPreventionToken': 'test_csrf_token'
            }
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(api, 'session') as mock_session:
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            result = await api.authenticate()
            
            assert result is True
            assert api.ticket == 'PVE:test_ticket'
            assert api.csrf_token == 'test_csrf_token'
            assert api.ticket_expiry is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, api):
        """Test failed async authentication"""
        with patch.object(api, 'session') as mock_session:
            mock_session.post.side_effect = aiohttp.ClientError("Auth failed")
            
            result = await api.authenticate()
            
            assert result is False
            assert api.ticket is None
    
    @pytest.mark.asyncio
    async def test_ensure_authenticated(self, api):
        """Test authentication check and refresh"""
        # Test when not authenticated
        with patch.object(api, 'authenticate', return_value=True) as mock_auth:
            result = await api.ensure_authenticated()
            assert result is True
            mock_auth.assert_called_once()
        
        # Test when authenticated and valid
        api.ticket = 'test_ticket'
        from datetime import datetime, timedelta
        api.ticket_expiry = datetime.now() + timedelta(hours=1)
        
        with patch.object(api, 'authenticate') as mock_auth:
            result = await api.ensure_authenticated()
            assert result is True
            mock_auth.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_vm_status_async(self, api):
        """Test getting VM status asynchronously"""
        api.ticket = 'test_ticket'
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            'data': {
                'status': 'running',
                'cpu': 0.5,
                'mem': 1024
            }
        })
        mock_response.raise_for_status = Mock()
        
        with patch.object(api, 'ensure_authenticated', return_value=True):
            with patch.object(api, 'session') as mock_session:
                mock_session.get.return_value.__aenter__.return_value = mock_response
                
                result = await api.get_vm_status(100)
                
                assert result['status'] == 'running'
                assert result['cpu'] == 0.5
                assert result['mem'] == 1024
    
    @pytest.mark.asyncio
    async def test_batch_vm_status(self, api):
        """Test batch VM status retrieval"""
        vm_ids = [100, 101, 102]
        
        async def mock_get_vm_status(vm_id):
            if vm_id == 102:
                raise Exception("VM not found")
            return {'vmid': vm_id, 'status': 'running'}
        
        with patch.object(api, 'get_vm_status', side_effect=mock_get_vm_status):
            results = await api.batch_vm_status(vm_ids)
            
            assert results[100] == {'vmid': 100, 'status': 'running'}
            assert results[101] == {'vmid': 101, 'status': 'running'}
            assert results[102] is None  # Failed request
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self, api):
        """Test connection pooling settings"""
        await api.connect()
        
        assert api.connector is not None
        assert api.connector.limit == 10
        assert api.connector.limit_per_host == 5
        
        await api.close()


class TestMigration:
    """Test migration from sync to async"""
    
    def test_migrate_to_async(self):
        """Test creating async API from sync API"""
        from lib.proxmox_api_async import migrate_to_async
        
        config = {
            'host': '192.168.1.100',
            'port': 8006,
            'username': 'root@pam',
            'password': 'test_password',
            'node': 'proxmox-node',
            'verify_ssl': False
        }
        
        sync_api = ProxmoxAPI(config)
        async_api = migrate_to_async(sync_api)
        
        assert async_api.host == sync_api.host
        assert async_api.port == sync_api.port
        assert async_api.username == sync_api.username
        assert async_api.password == sync_api.password
        assert async_api.node == sync_api.node
        assert async_api.verify_ssl == sync_api.verify_ssl


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
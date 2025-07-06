"""
Test suite for health checks module
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from health_checks import HealthChecker, HealthStatus


class TestHealthChecker:
    """Test HealthChecker functionality"""
    
    @pytest.fixture
    def health_checker(self):
        """Create a HealthChecker instance"""
        return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_system_time(self, health_checker):
        """Test system time health check"""
        with patch('subprocess.run') as mock_run:
            # Successful time check
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='System clock synchronized: yes\n'
            )
            
            result = await health_checker.check_system_time()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "system_time"
            assert "synchronized" in result.message
    
    @pytest.mark.asyncio
    async def test_check_system_time_not_synced(self, health_checker):
        """Test system time not synchronized"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='System clock synchronized: no\n'
            )
            
            result = await health_checker.check_system_time()
            
            assert result.status == HealthStatus.WARNING
            assert "not synchronized" in result.message
    
    @pytest.mark.asyncio
    async def test_check_disk_space(self, health_checker):
        """Test disk space health check"""
        with patch('psutil.disk_usage') as mock_disk:
            # Healthy disk usage (50%)
            mock_disk.return_value = MagicMock(percent=50.0)
            
            result = await health_checker.check_disk_space()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "disk_space"
            assert "50.0%" in result.message
    
    @pytest.mark.asyncio
    async def test_check_disk_space_warning(self, health_checker):
        """Test disk space warning threshold"""
        with patch('psutil.disk_usage') as mock_disk:
            # Warning level (85%)
            mock_disk.return_value = MagicMock(percent=85.0)
            
            result = await health_checker.check_disk_space()
            
            assert result.status == HealthStatus.WARNING
            assert "85.0%" in result.message
    
    @pytest.mark.asyncio
    async def test_check_disk_space_critical(self, health_checker):
        """Test disk space critical threshold"""
        with patch('psutil.disk_usage') as mock_disk:
            # Critical level (95%)
            mock_disk.return_value = MagicMock(percent=95.0)
            
            result = await health_checker.check_disk_space()
            
            assert result.status == HealthStatus.CRITICAL
            assert "95.0%" in result.message
    
    @pytest.mark.asyncio
    async def test_check_memory_usage(self, health_checker):
        """Test memory usage health check"""
        with patch('psutil.virtual_memory') as mock_memory:
            # Healthy memory usage (60%)
            mock_memory.return_value = MagicMock(percent=60.0)
            
            result = await health_checker.check_memory_usage()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "memory"
            assert "60.0%" in result.message
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_warning(self, health_checker):
        """Test memory usage warning"""
        with patch('psutil.virtual_memory') as mock_memory:
            # Warning level (85%)
            mock_memory.return_value = MagicMock(percent=85.0)
            
            result = await health_checker.check_memory_usage()
            
            assert result.status == HealthStatus.WARNING
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity(self, health_checker):
        """Test network connectivity check"""
        with patch('subprocess.run') as mock_run:
            # Successful ping
            mock_run.return_value = MagicMock(returncode=0)
            
            result = await health_checker.check_network_connectivity()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "network"
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity_failure(self, health_checker):
        """Test network connectivity failure"""
        with patch('subprocess.run') as mock_run:
            # Failed ping
            mock_run.return_value = MagicMock(returncode=1)
            
            result = await health_checker.check_network_connectivity()
            
            assert result.status == HealthStatus.CRITICAL
            assert "Network connectivity" in result.message
    
    @pytest.mark.asyncio
    async def test_check_required_services(self, health_checker):
        """Test required services check"""
        services = ["ntp", "ssh"]
        
        with patch('subprocess.run') as mock_run:
            # All services active
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='active\n'
            )
            
            result = await health_checker.check_required_services(services)
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "services"
            assert mock_run.call_count == 2
    
    @pytest.mark.asyncio
    async def test_check_required_services_inactive(self, health_checker):
        """Test inactive service detection"""
        services = ["ntp", "ssh"]
        
        with patch('subprocess.run') as mock_run:
            # First service active, second inactive
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='active\n'),
                MagicMock(returncode=0, stdout='inactive\n')
            ]
            
            result = await health_checker.check_required_services(services)
            
            assert result.status == HealthStatus.WARNING
            assert "ssh" in result.details["inactive_services"]
    
    @pytest.mark.asyncio
    async def test_check_proxmox_connection(self, health_checker):
        """Test Proxmox connection check"""
        config = {
            "host": "192.168.1.100",
            "port": 8006
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await health_checker.check_proxmox_connection(config)
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "proxmox"
    
    @pytest.mark.asyncio
    async def test_check_proxmox_connection_failure(self, health_checker):
        """Test Proxmox connection failure"""
        config = {
            "host": "192.168.1.100",
            "port": 8006
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session.get.side_effect = Exception("Connection failed")
            
            result = await health_checker.check_proxmox_connection(config)
            
            assert result.status == HealthStatus.CRITICAL
            assert "Connection failed" in result.message
    
    @pytest.mark.asyncio
    async def test_check_time_shift_permissions(self, health_checker):
        """Test time shift permission check"""
        with patch('os.geteuid', return_value=0):
            result = await health_checker.check_time_shift_permissions()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.component == "permissions"
    
    @pytest.mark.asyncio
    async def test_check_time_shift_permissions_non_root(self, health_checker):
        """Test time shift permissions as non-root"""
        with patch('os.geteuid', return_value=1000):
            result = await health_checker.check_time_shift_permissions()
            
            assert result.status == HealthStatus.CRITICAL
            assert "root privileges" in result.message
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self, health_checker):
        """Test running all health checks"""
        # Mock all individual checks
        mock_checks = [
            AsyncMock(return_value=MagicMock(status=HealthStatus.HEALTHY)),
            AsyncMock(return_value=MagicMock(status=HealthStatus.WARNING)),
            AsyncMock(return_value=MagicMock(status=HealthStatus.HEALTHY))
        ]
        
        with patch.object(health_checker, 'check_system_time', mock_checks[0]):
            with patch.object(health_checker, 'check_disk_space', mock_checks[1]):
                with patch.object(health_checker, 'check_memory_usage', mock_checks[2]):
                    results = await health_checker.run_all_checks()
        
        assert len(results) >= 3
        # Should have called all mocked checks
        for mock_check in mock_checks:
            mock_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_overall_status(self, health_checker):
        """Test overall status calculation"""
        # All healthy
        results = [
            MagicMock(status=HealthStatus.HEALTHY),
            MagicMock(status=HealthStatus.HEALTHY)
        ]
        assert health_checker.get_overall_status(results) == HealthStatus.HEALTHY
        
        # One warning
        results.append(MagicMock(status=HealthStatus.WARNING))
        assert health_checker.get_overall_status(results) == HealthStatus.WARNING
        
        # One critical
        results.append(MagicMock(status=HealthStatus.CRITICAL))
        assert health_checker.get_overall_status(results) == HealthStatus.CRITICAL
    
    @pytest.mark.asyncio
    async def test_check_cpu_usage(self, health_checker):
        """Test CPU usage check"""
        with patch('psutil.cpu_percent') as mock_cpu:
            # Normal CPU usage
            mock_cpu.return_value = 45.0
            
            result = await health_checker.check_cpu_usage()
            
            assert result.status == HealthStatus.HEALTHY
            assert "45.0%" in result.message
            
            # High CPU usage
            mock_cpu.return_value = 95.0
            result = await health_checker.check_cpu_usage()
            assert result.status == HealthStatus.WARNING
    
    @pytest.mark.asyncio
    async def test_format_health_report(self, health_checker):
        """Test health report formatting"""
        results = [
            MagicMock(
                component="test1",
                status=HealthStatus.HEALTHY,
                message="Test 1 is healthy",
                details={"key": "value"}
            ),
            MagicMock(
                component="test2",
                status=HealthStatus.WARNING,
                message="Test 2 has warnings",
                details={}
            )
        ]
        
        report = health_checker.format_health_report(results)
        
        assert isinstance(report, str)
        assert "test1" in report
        assert "HEALTHY" in report
        assert "test2" in report
        assert "WARNING" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
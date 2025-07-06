"""
Test suite for network tools module
"""

import pytest
import socket
from unittest.mock import patch, MagicMock, Mock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from network_tools import NetworkTools


class TestNetworkTools:
    """Test NetworkTools functionality"""
    
    @pytest.fixture
    def network_tools(self):
        """Create a NetworkTools instance"""
        return NetworkTools()
    
    def test_ping_host(self, network_tools):
        """Test ping functionality"""
        with patch('subprocess.run') as mock_run:
            # Successful ping
            mock_run.return_value = MagicMock(returncode=0)
            
            result = network_tools.ping_host('192.168.1.100', count=3, timeout=2)
            
            assert result is True
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert 'ping' in cmd[0]
            assert '-c' in cmd
            assert '3' in cmd
            assert '-W' in cmd
            assert '2' in cmd
            assert '192.168.1.100' in cmd
    
    def test_ping_host_failure(self, network_tools):
        """Test ping failure"""
        with patch('subprocess.run') as mock_run:
            # Failed ping
            mock_run.return_value = MagicMock(returncode=1)
            
            result = network_tools.ping_host('192.168.1.100')
            
            assert result is False
    
    def test_check_port_open(self, network_tools):
        """Test port connectivity check"""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            
            # Port is open
            mock_socket.connect_ex.return_value = 0
            
            result = network_tools.check_port_open('192.168.1.100', 443, timeout=5)
            
            assert result is True
            mock_socket.settimeout.assert_called_with(5)
            mock_socket.connect_ex.assert_called_with(('192.168.1.100', 443))
            mock_socket.close.assert_called()
    
    def test_check_port_closed(self, network_tools):
        """Test closed port detection"""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            
            # Port is closed
            mock_socket.connect_ex.return_value = 111  # Connection refused
            
            result = network_tools.check_port_open('192.168.1.100', 443)
            
            assert result is False
    
    def test_resolve_hostname(self, network_tools):
        """Test hostname resolution"""
        with patch('socket.gethostbyname') as mock_resolve:
            mock_resolve.return_value = '192.168.1.100'
            
            ip = network_tools.resolve_hostname('server.example.com')
            
            assert ip == '192.168.1.100'
            mock_resolve.assert_called_with('server.example.com')
    
    def test_resolve_hostname_failure(self, network_tools):
        """Test hostname resolution failure"""
        with patch('socket.gethostbyname') as mock_resolve:
            mock_resolve.side_effect = socket.gaierror("Name resolution failed")
            
            ip = network_tools.resolve_hostname('invalid.hostname')
            
            assert ip is None
    
    def test_get_network_interfaces(self, network_tools):
        """Test getting network interfaces"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='eth0\nlo\nwlan0\n'
            )
            
            interfaces = network_tools.get_network_interfaces()
            
            assert interfaces == ['eth0', 'lo', 'wlan0']
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert 'ip' in cmd[0]
            assert 'link' in cmd
            assert 'show' in cmd
    
    def test_get_interface_ip(self, network_tools):
        """Test getting interface IP address"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='    inet 192.168.1.50/24 brd 192.168.1.255 scope global eth0\n'
            )
            
            ip = network_tools.get_interface_ip('eth0')
            
            assert ip == '192.168.1.50'
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert 'ip' in cmd[0]
            assert 'addr' in cmd
            assert 'show' in cmd
            assert 'eth0' in cmd
    
    def test_get_interface_ip_no_address(self, network_tools):
        """Test interface with no IP"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>\n'
            )
            
            ip = network_tools.get_interface_ip('eth0')
            
            assert ip is None
    
    def test_validate_idrac_connection(self, network_tools):
        """Test iDRAC connection validation"""
        with patch.object(network_tools, 'ping_host', return_value=True):
            with patch.object(network_tools, 'check_port_open', return_value=True):
                with patch('requests.get') as mock_get:
                    # Mock successful HTTPS connection
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_get.return_value = mock_response
                    
                    result = network_tools.validate_idrac_connection(
                        '192.168.1.200',
                        username='root',
                        password='calvin'
                    )
                    
                    assert result is True
    
    def test_validate_idrac_connection_no_ping(self, network_tools):
        """Test iDRAC validation with no ping response"""
        with patch.object(network_tools, 'ping_host', return_value=False):
            result = network_tools.validate_idrac_connection('192.168.1.200')
            
            assert result is False
    
    def test_validate_idrac_connection_port_closed(self, network_tools):
        """Test iDRAC validation with closed HTTPS port"""
        with patch.object(network_tools, 'ping_host', return_value=True):
            with patch.object(network_tools, 'check_port_open', return_value=False):
                result = network_tools.validate_idrac_connection('192.168.1.200')
                
                assert result is False
    
    def test_scan_network_range(self, network_tools):
        """Test network range scanning"""
        with patch.object(network_tools, 'ping_host') as mock_ping:
            # Only .100 and .101 respond
            mock_ping.side_effect = lambda host, **kwargs: host in ['192.168.1.100', '192.168.1.101']
            
            active_hosts = network_tools.scan_network_range('192.168.1.0/24', max_workers=2)
            
            assert '192.168.1.100' in active_hosts
            assert '192.168.1.101' in active_hosts
            assert len(active_hosts) == 2
    
    def test_find_idrac_systems(self, network_tools):
        """Test finding iDRAC systems in network"""
        with patch.object(network_tools, 'scan_network_range') as mock_scan:
            mock_scan.return_value = ['192.168.1.100', '192.168.1.101', '192.168.1.102']
            
            with patch.object(network_tools, 'check_port_open') as mock_port:
                # Only .100 and .102 have HTTPS port open
                mock_port.side_effect = lambda host, port, **kwargs: host in ['192.168.1.100', '192.168.1.102']
                
                idrac_systems = network_tools.find_idrac_systems('192.168.1.0/24')
                
                assert idrac_systems == ['192.168.1.100', '192.168.1.102']
    
    def test_test_connectivity(self, network_tools):
        """Test comprehensive connectivity test"""
        target = '192.168.1.100'
        
        with patch.object(network_tools, 'ping_host', return_value=True):
            with patch.object(network_tools, 'check_port_open') as mock_port:
                mock_port.side_effect = lambda host, port, **kwargs: port in [22, 443]
                
                results = network_tools.test_connectivity(target, ports=[22, 443, 3389])
                
                assert results['host'] == target
                assert results['ping'] is True
                assert results['ports'][22] is True
                assert results['ports'][443] is True
                assert results['ports'][3389] is False
    
    def test_get_route_to_host(self, network_tools):
        """Test getting route to host"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='192.168.1.100 via 192.168.1.1 dev eth0 src 192.168.1.50\n'
            )
            
            route = network_tools.get_route_to_host('192.168.1.100')
            
            assert route is not None
            assert '192.168.1.1' in route
            assert 'eth0' in route
    
    def test_check_dns_resolution(self, network_tools):
        """Test DNS resolution check"""
        # Test with IP address (should always return True)
        assert network_tools.check_dns_resolution('192.168.1.100') is True
        
        # Test with hostname
        with patch('socket.gethostbyname') as mock_resolve:
            mock_resolve.return_value = '192.168.1.100'
            
            assert network_tools.check_dns_resolution('server.example.com') is True
            
            # Test failed resolution
            mock_resolve.side_effect = socket.gaierror("DNS failure")
            assert network_tools.check_dns_resolution('invalid.host') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
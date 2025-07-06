"""
Test suite for configuration models
Demonstrates comprehensive testing approach for the time-shift project
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
from pydantic import ValidationError

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from config_models import (
    TimeShiftConfig, ProxmoxConfig, VMConfig, NetworkConfig,
    LogLevel, OSType, NetworkConfigType,
    load_config_from_file, save_config_to_file, create_default_config,
    validate_config_security
)


class TestProxmoxConfig:
    """Test ProxmoxConfig model validation"""
    
    def test_valid_proxmox_config(self):
        """Test creation of valid Proxmox configuration"""
        config = ProxmoxConfig(
            host="192.168.1.100",
            port=8006,
            username="root@pam",
            password="secure_password_123",
            node="proxmox-node"
        )
        
        assert config.host == "192.168.1.100"
        assert config.port == 8006
        assert config.username == "root@pam"
        assert config.verify_ssl is False  # Default value
    
    def test_invalid_username_format(self):
        """Test validation of username format"""
        with pytest.raises(ValidationError) as exc_info:
            ProxmoxConfig(
                host="192.168.1.100",
                username="root",  # Missing realm
                password="secure_password_123",
                node="proxmox-node"
            )
        
        assert "Username must include realm" in str(exc_info.value)
    
    def test_weak_password_validation(self):
        """Test password strength validation"""
        with pytest.raises(ValidationError) as exc_info:
            ProxmoxConfig(
                host="192.168.1.100",
                username="root@pam",
                password="password",  # Weak password
                node="proxmox-node"
            )
        
        assert "Password is too weak" in str(exc_info.value)
    
    def test_invalid_port_range(self):
        """Test port range validation"""
        with pytest.raises(ValidationError):
            ProxmoxConfig(
                host="192.168.1.100",
                port=70000,  # Invalid port
                username="root@pam",
                password="secure_password_123",
                node="proxmox-node"
            )


class TestVMConfig:
    """Test VMConfig model validation"""
    
    def test_valid_vm_config(self):
        """Test creation of valid VM configuration"""
        config = VMConfig(
            name="test-vm",
            memory=4096,
            cores=4,
            disk_size=50
        )
        
        assert config.name == "test-vm"
        assert config.memory == 4096
        assert config.os_type == OSType.LINUX_26  # Default value
    
    def test_invalid_vm_name(self):
        """Test VM name validation"""
        with pytest.raises(ValidationError) as exc_info:
            VMConfig(name="test vm!")  # Invalid characters
        
        assert "can only contain letters, numbers, and hyphens" in str(exc_info.value)
    
    def test_memory_limits(self):
        """Test memory range validation"""
        # Test minimum memory
        with pytest.raises(ValidationError):
            VMConfig(name="test-vm", memory=256)  # Below minimum
        
        # Test maximum memory
        with pytest.raises(ValidationError):
            VMConfig(name="test-vm", memory=50000)  # Above maximum


class TestNetworkConfig:
    """Test NetworkConfig model validation"""
    
    def test_dhcp_configuration(self):
        """Test DHCP network configuration"""
        config = NetworkConfig(
            bridge="vmbr0",
            ip_config=NetworkConfigType.DHCP
        )
        
        assert config.ip_config == NetworkConfigType.DHCP
        assert config.ip_address is None
    
    def test_static_ip_validation(self):
        """Test static IP configuration validation"""
        # Valid static configuration
        config = NetworkConfig(
            ip_config=NetworkConfigType.STATIC,
            ip_address="192.168.1.50",
            netmask="24",
            gateway="192.168.1.1"
        )
        
        assert str(config.ip_address) == "192.168.1.50"
        assert config.netmask == "24"
    
    def test_static_ip_missing_address(self):
        """Test static IP configuration without IP address"""
        with pytest.raises(ValidationError) as exc_info:
            NetworkConfig(
                ip_config=NetworkConfigType.STATIC
                # Missing ip_address
            )
        
        assert "IP address is required for static configuration" in str(exc_info.value)
    
    def test_invalid_netmask(self):
        """Test invalid netmask validation"""
        with pytest.raises(ValidationError) as exc_info:
            NetworkConfig(
                ip_config=NetworkConfigType.STATIC,
                ip_address="192.168.1.50",
                netmask="999"  # Invalid netmask
            )
        
        assert "Invalid netmask format" in str(exc_info.value)


class TestTimeShiftConfig:
    """Test main TimeShiftConfig model"""
    
    def test_complete_valid_config(self):
        """Test creation of complete valid configuration"""
        config_data = {
            "proxmox": {
                "host": "192.168.1.100",
                "username": "root@pam",
                "password": "secure_password_123",
                "node": "proxmox-node"
            },
            "vm": {
                "name": "test-vm"
            },
            "network": {
                "bridge": "vmbr0"
            },
            "time": {
                "timezone": "UTC"
            },
            "idrac": {
                "default_username": "root"
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        config = TimeShiftConfig(**config_data)
        
        assert config.proxmox.host == "192.168.1.100"
        assert config.vm.name == "test-vm"
        assert config.logging.level == LogLevel.INFO
        assert config.version == "0.2.0"  # Default version
    
    def test_config_with_defaults(self):
        """Test configuration with default values"""
        minimal_config = {
            "proxmox": {
                "host": "192.168.1.100",
                "username": "root@pam",
                "password": "secure_password_123",
                "node": "proxmox-node"
            },
            "vm": {"name": "test-vm"},
            "network": {},
            "time": {},
            "idrac": {},
            "logging": {}
        }
        
        config = TimeShiftConfig(**minimal_config)
        
        # Check defaults are applied
        assert config.vm.memory == 2048  # Default memory
        assert config.network.ip_config == NetworkConfigType.DHCP
        assert config.time.backup_original is True
        assert config.security.encrypt_passwords is True


class TestConfigFileOperations:
    """Test configuration file operations"""
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration from file"""
        config = create_default_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            save_config_to_file(config, temp_path)
            
            # Verify file exists
            assert Path(temp_path).exists()
            
            # Load configuration
            loaded_config = load_config_from_file(temp_path)
            
            # Verify loaded config matches original
            assert loaded_config.proxmox.host == config.proxmox.host
            assert loaded_config.vm.name == config.vm.name
            
        finally:
            # Clean up
            if Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file"""
        with pytest.raises(FileNotFoundError):
            load_config_from_file("nonexistent_config.json")
    
    def test_load_invalid_json_config(self):
        """Test loading invalid JSON configuration"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_config_from_file(temp_path)
        finally:
            Path(temp_path).unlink()


class TestSecurityValidation:
    """Test security validation functions"""
    
    def test_secure_configuration(self):
        """Test configuration with good security practices"""
        config = create_default_config()
        config.proxmox.password = "very_secure_password_123!"
        config.idrac.default_password = "custom_idrac_password"
        config.proxmox.verify_ssl = True
        config.idrac.ssl_verify = True
        config.security.allow_root = False
        
        warnings = validate_config_security(config)
        
        # Should have minimal warnings with secure config
        assert len(warnings) == 0
    
    def test_insecure_configuration(self):
        """Test configuration with security issues"""
        config = create_default_config()
        config.proxmox.password = "password"  # Weak password
        config.idrac.default_password = "calvin"  # Dell standard default
        config.security.allow_root = True
        config.security.encrypt_passwords = False
        
        warnings = validate_config_security(config)
        
        # Should have multiple security warnings
        assert len(warnings) > 0
        assert any("weak" in warning.lower() for warning in warnings)
        assert any("default" in warning.lower() for warning in warnings)
        assert any("root access" in warning.lower() for warning in warnings)


class TestConfigurationDefaults:
    """Test default configuration creation"""
    
    def test_create_default_config(self):
        """Test creation of default configuration"""
        config = create_default_config()
        
        # Verify basic structure
        assert config.proxmox is not None
        assert config.vm is not None
        assert config.network is not None
        assert config.time is not None
        assert config.idrac is not None
        assert config.logging is not None
        assert config.security is not None
        
        # Verify default values
        assert config.vm.memory == 2048
        assert config.vm.cores == 2
        assert config.time.backup_original is True
        assert config.logging.level == LogLevel.INFO
    
    def test_default_config_validation(self):
        """Test that default configuration passes validation"""
        config = create_default_config()
        
        # Should be able to serialize/deserialize without errors
        config_dict = config.dict()
        recreated_config = TimeShiftConfig(**config_dict)
        
        assert recreated_config.vm.name == config.vm.name


# Integration tests
class TestConfigurationIntegration:
    """Integration tests for configuration management"""
    
    @patch('lib.config_models.datetime')
    def test_config_timestamps(self, mock_datetime):
        """Test configuration timestamp handling"""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        config = create_default_config()
        
        assert config.created_at == fixed_time
        
        # Test update timestamp
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_config_to_file(config, temp_path)
            assert config.updated_at == fixed_time
        finally:
            Path(temp_path).unlink()
    
    def test_enum_value_handling(self):
        """Test enum value handling in configuration"""
        config = create_default_config()
        
        # Test enum assignment
        config.logging.level = LogLevel.DEBUG
        config.vm.os_type = OSType.WINDOWS
        config.network.ip_config = NetworkConfigType.STATIC
        
        # Test serialization preserves enum values
        config_dict = config.dict()
        assert config_dict['logging']['level'] == 'DEBUG'
        assert config_dict['vm']['os_type'] == 'win'
        assert config_dict['network']['ip_config'] == 'static'


# Pytest fixtures
@pytest.fixture
def sample_config():
    """Fixture providing a sample configuration for testing"""
    return create_default_config()


@pytest.fixture
def temp_config_file():
    """Fixture providing a temporary configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if Path(temp_path).exists():
        Path(temp_path).unlink()


# Performance and stress tests
class TestConfigurationPerformance:
    """Performance tests for configuration operations"""
    
    def test_large_config_performance(self):
        """Test performance with large configuration"""
        import time
        
        start_time = time.time()
        
        # Create and validate 100 configurations
        for i in range(100):
            config = create_default_config()
            config.vm.name = f"test-vm-{i}"
            
            # Serialize and deserialize
            config_dict = config.dict()
            TimeShiftConfig(**config_dict)
        
        end_time = time.time()
        
        # Should complete quickly (adjust threshold as needed)
        assert (end_time - start_time) < 5.0
    
    @pytest.mark.slow
    def test_config_validation_stress(self):
        """Stress test for configuration validation"""
        # Test with many invalid configurations
        invalid_configs = []
        
        for i in range(1000):
            try:
                ProxmoxConfig(
                    host=f"192.168.1.{i % 256}",
                    username="invalid_username",  # Missing realm
                    password="weak",  # Weak password
                    node=f"node-{i}"
                )
            except ValidationError:
                invalid_configs.append(i)
        
        # All should fail validation
        assert len(invalid_configs) == 1000


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
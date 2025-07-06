"""
Test suite for security module
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from security import SecurityManager


class TestSecurityManager:
    """Test SecurityManager functionality"""
    
    @pytest.fixture
    def security_manager(self):
        """Create a SecurityManager instance"""
        return SecurityManager()
    
    def test_encrypt_password(self, security_manager):
        """Test password encryption"""
        password = "test_password_123"
        
        encrypted = security_manager.encrypt_password(password)
        
        # Should return a different string
        assert encrypted != password
        # Should be base64 encoded
        assert isinstance(encrypted, str)
        # Should be decodable
        import base64
        try:
            base64.b64decode(encrypted)
        except Exception:
            pytest.fail("Encrypted password is not valid base64")
    
    def test_decrypt_password(self, security_manager):
        """Test password decryption"""
        password = "test_password_123"
        
        encrypted = security_manager.encrypt_password(password)
        decrypted = security_manager.decrypt_password(encrypted)
        
        assert decrypted == password
    
    def test_encrypt_decrypt_empty_password(self, security_manager):
        """Test encrypting empty password"""
        password = ""
        
        encrypted = security_manager.encrypt_password(password)
        decrypted = security_manager.decrypt_password(encrypted)
        
        assert decrypted == password
    
    def test_generate_secure_key(self, security_manager):
        """Test secure key generation"""
        key1 = security_manager.generate_secure_key()
        key2 = security_manager.generate_secure_key()
        
        # Should be 32 bytes (256 bits)
        assert len(key1) == 32
        assert len(key2) == 32
        # Should be different each time
        assert key1 != key2
    
    def test_hash_password(self, security_manager):
        """Test password hashing"""
        password = "test_password_123"
        
        hash1 = security_manager.hash_password(password)
        hash2 = security_manager.hash_password(password)
        
        # Should produce consistent hash
        assert hash1 == hash2
        # Should not be the original password
        assert hash1 != password
        # Should be hex string
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_validate_password_strength(self, security_manager):
        """Test password strength validation"""
        # Weak passwords
        assert security_manager.validate_password_strength("") is False
        assert security_manager.validate_password_strength("short") is False
        assert security_manager.validate_password_strength("password") is False
        assert security_manager.validate_password_strength("12345678") is False
        
        # Strong passwords
        assert security_manager.validate_password_strength("StrongP@ssw0rd!") is True
        assert security_manager.validate_password_strength("Complex123!@#") is True
    
    def test_secure_delete_file(self, security_manager):
        """Test secure file deletion"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"sensitive data")
            tmp_path = tmp.name
        
        assert Path(tmp_path).exists()
        
        result = security_manager.secure_delete_file(tmp_path)
        
        assert result is True
        assert not Path(tmp_path).exists()
    
    def test_secure_delete_nonexistent_file(self, security_manager):
        """Test deleting non-existent file"""
        result = security_manager.secure_delete_file("/nonexistent/file.txt")
        assert result is False
    
    def test_sanitize_input(self, security_manager):
        """Test input sanitization"""
        # Test command injection attempts
        assert security_manager.sanitize_input("test; rm -rf /") == "test rm -rf /"
        assert security_manager.sanitize_input("test && echo hack") == "test  echo hack"
        assert security_manager.sanitize_input("test | cat /etc/passwd") == "test  cat /etc/passwd"
        assert security_manager.sanitize_input("test`whoami`") == "testwhoami"
        assert security_manager.sanitize_input("test$(whoami)") == "testwhoami"
        
        # Normal input should pass through
        assert security_manager.sanitize_input("normal-input_123") == "normal-input_123"
    
    def test_validate_file_permissions(self, security_manager):
        """Test file permission validation"""
        with tempfile.NamedTemporaryFile() as tmp:
            # Set readable permissions
            os.chmod(tmp.name, 0o644)
            assert security_manager.validate_file_permissions(tmp.name) is True
            
            # Set world-writable permissions
            os.chmod(tmp.name, 0o666)
            assert security_manager.validate_file_permissions(tmp.name) is False
    
    def test_create_secure_temp_file(self, security_manager):
        """Test secure temporary file creation"""
        content = "test content"
        
        temp_path = security_manager.create_secure_temp_file(
            content, 
            prefix="test_",
            suffix=".txt"
        )
        
        assert temp_path is not None
        assert Path(temp_path).exists()
        
        # Check permissions (should be 0o600)
        stat_info = os.stat(temp_path)
        assert stat_info.st_mode & 0o777 == 0o600
        
        # Check content
        with open(temp_path, 'r') as f:
            assert f.read() == content
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_audit_log(self, security_manager):
        """Test audit logging"""
        with patch('builtins.open', mock_open()) as mock_file:
            result = security_manager.audit_log(
                "test_action",
                "test_user",
                {"key": "value"}
            )
            
            assert result is True
            mock_file.assert_called()
            
            # Check that JSON was written
            written_content = ""
            for call in mock_file().write.call_args_list:
                written_content += call[0][0]
            
            assert "test_action" in written_content
            assert "test_user" in written_content
    
    def test_check_root_access(self, security_manager):
        """Test root access check"""
        with patch('os.geteuid', return_value=0):
            assert security_manager.check_root_access() is True
        
        with patch('os.geteuid', return_value=1000):
            assert security_manager.check_root_access() is False
    
    def test_validate_ip_address(self, security_manager):
        """Test IP address validation"""
        # Valid IP addresses
        assert security_manager.validate_ip_address("192.168.1.1") is True
        assert security_manager.validate_ip_address("10.0.0.1") is True
        assert security_manager.validate_ip_address("172.16.0.1") is True
        
        # Invalid IP addresses
        assert security_manager.validate_ip_address("256.256.256.256") is False
        assert security_manager.validate_ip_address("192.168.1") is False
        assert security_manager.validate_ip_address("not.an.ip.address") is False
        assert security_manager.validate_ip_address("") is False
    
    def test_validate_port_number(self, security_manager):
        """Test port number validation"""
        # Valid ports
        assert security_manager.validate_port_number(80) is True
        assert security_manager.validate_port_number(443) is True
        assert security_manager.validate_port_number(8080) is True
        assert security_manager.validate_port_number(65535) is True
        
        # Invalid ports
        assert security_manager.validate_port_number(0) is False
        assert security_manager.validate_port_number(-1) is False
        assert security_manager.validate_port_number(65536) is False
        assert security_manager.validate_port_number(100000) is False
    
    def test_escape_shell_command(self, security_manager):
        """Test shell command escaping"""
        # Test dangerous characters
        assert security_manager.escape_shell_command("test; rm -rf /") == "'test; rm -rf /'"
        assert security_manager.escape_shell_command("test'quote") == "'test'\"'\"'quote'"
        assert security_manager.escape_shell_command("normal-command") == "normal-command"
    
    def test_generate_api_key(self, security_manager):
        """Test API key generation"""
        key1 = security_manager.generate_api_key()
        key2 = security_manager.generate_api_key()
        
        # Should be 32 characters (hex)
        assert len(key1) == 32
        assert len(key2) == 32
        # Should be different
        assert key1 != key2
        # Should be hex
        assert all(c in '0123456789abcdef' for c in key1)
    
    def test_verify_file_integrity(self, security_manager):
        """Test file integrity verification"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        # Calculate hash
        file_hash = security_manager.calculate_file_hash(tmp_path)
        
        # Verify integrity
        assert security_manager.verify_file_integrity(tmp_path, file_hash) is True
        
        # Modify file
        with open(tmp_path, 'a') as f:
            f.write("modified")
        
        # Should fail verification
        assert security_manager.verify_file_integrity(tmp_path, file_hash) is False
        
        # Cleanup
        os.unlink(tmp_path)
    
    def test_secure_config_load(self, security_manager):
        """Test secure configuration loading"""
        config_data = {
            "password": "secret123",
            "api_key": "key123",
            "normal_setting": "value"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(config_data, tmp)
            tmp_path = tmp.name
        
        # Set secure permissions
        os.chmod(tmp_path, 0o600)
        
        loaded_config = security_manager.secure_config_load(tmp_path)
        
        assert loaded_config == config_data
        
        # Test with insecure permissions
        os.chmod(tmp_path, 0o666)
        loaded_config = security_manager.secure_config_load(tmp_path)
        assert loaded_config is None
        
        # Cleanup
        os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Security Module - Comprehensive security framework
Provides encryption, credential management, and security utilities
"""

import os
import base64
import json
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    Fernet = None
    print("Warning: cryptography package not installed. Install with: pip install cryptography")

try:
    import keyring
except ImportError:
    keyring = None
    print("Warning: keyring package not installed. Install with: pip install keyring")


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class CredentialManager:
    """Secure credential storage and retrieval"""
    
    def __init__(self, service_name: str = "time-shift-proxmox"):
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        
        if not keyring:
            self.logger.warning("Keyring not available, falling back to environment variables")
    
    def store_credential(self, username: str, password: str, context: str = "default") -> bool:
        """
        Store credentials securely
        
        Args:
            username: Username to store
            password: Password to store
            context: Context/identifier for the credential
            
        Returns:
            bool: True if stored successfully
        """
        try:
            if keyring:
                key = f"{self.service_name}:{context}:{username}"
                keyring.set_password(key, username, password)
                self.logger.info(f"Stored credential for {username} in context {context}")
                return True
            else:
                # Fallback to environment variables (less secure)
                env_key = f"TIMESHIFT_{context.upper()}_{username.upper()}_PASSWORD"
                os.environ[env_key] = password
                self.logger.warning(f"Stored credential in environment variable {env_key}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to store credential: {e}")
            return False
    
    def retrieve_credential(self, username: str, context: str = "default") -> Optional[str]:
        """
        Retrieve stored credentials
        
        Args:
            username: Username to retrieve password for
            context: Context/identifier for the credential
            
        Returns:
            str: Password if found, None otherwise
        """
        try:
            if keyring:
                key = f"{self.service_name}:{context}:{username}"
                password = keyring.get_password(key, username)
                if password:
                    self.logger.info(f"Retrieved credential for {username} from keyring")
                    return password
            
            # Fallback to environment variables
            env_key = f"TIMESHIFT_{context.upper()}_{username.upper()}_PASSWORD"
            password = os.getenv(env_key)
            if password:
                self.logger.info(f"Retrieved credential for {username} from environment")
                return password
            
            self.logger.warning(f"No credential found for {username} in context {context}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential: {e}")
            return None
    
    def delete_credential(self, username: str, context: str = "default") -> bool:
        """
        Delete stored credentials
        
        Args:
            username: Username to delete
            context: Context/identifier for the credential
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            if keyring:
                key = f"{self.service_name}:{context}:{username}"
                keyring.delete_password(key, username)
                self.logger.info(f"Deleted credential for {username}")
                return True
            else:
                env_key = f"TIMESHIFT_{context.upper()}_{username.upper()}_PASSWORD"
                if env_key in os.environ:
                    del os.environ[env_key]
                    self.logger.info(f"Deleted environment credential {env_key}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete credential: {e}")
            return False


class ConfigEncryption:
    """Configuration file encryption and decryption"""
    
    def __init__(self, password: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._key = None
        
        if password:
            self._key = self._derive_key(password.encode())
        elif not Fernet:
            raise SecurityError("Cryptography package required for encryption")
    
    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key from password"""
        salt = b'time-shift-salt'  # In production, use random salt and store it
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def generate_key(self) -> str:
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        return key.decode()
    
    def encrypt_data(self, data: Union[str, Dict[str, Any]], password: Optional[str] = None) -> str:
        """
        Encrypt data using Fernet symmetric encryption
        
        Args:
            data: Data to encrypt (string or dict)
            password: Optional password for key derivation
            
        Returns:
            str: Base64 encoded encrypted data
        """
        if not Fernet:
            raise SecurityError("Cryptography package not available")
        
        if password:
            key = self._derive_key(password.encode())
        elif self._key:
            key = self._key
        else:
            raise SecurityError("No encryption key available")
        
        cipher_suite = Fernet(key)
        
        if isinstance(data, dict):
            data = json.dumps(data)
        
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, password: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        Decrypt data using Fernet symmetric encryption
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            password: Optional password for key derivation
            
        Returns:
            Union[str, Dict]: Decrypted data
        """
        if not Fernet:
            raise SecurityError("Cryptography package not available")
        
        if password:
            key = self._derive_key(password.encode())
        elif self._key:
            key = self._key
        else:
            raise SecurityError("No encryption key available")
        
        cipher_suite = Fernet(key)
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = cipher_suite.decrypt(decoded_data)
            
            # Try to parse as JSON, return string if it fails
            try:
                return json.loads(decrypted_data.decode())
            except json.JSONDecodeError:
                return decrypted_data.decode()
                
        except Exception as e:
            raise SecurityError(f"Failed to decrypt data: {e}")
    
    def encrypt_config_file(self, config_path: str, output_path: str, password: str) -> bool:
        """
        Encrypt an entire configuration file
        
        Args:
            config_path: Path to source config file
            output_path: Path to encrypted output file
            password: Encryption password
            
        Returns:
            bool: True if encryption successful
        """
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            encrypted_data = self.encrypt_data(config_data, password)
            
            with open(output_path, 'w') as f:
                json.dump({
                    "encrypted": True,
                    "data": encrypted_data,
                    "created": datetime.now().isoformat()
                }, f, indent=2)
            
            self.logger.info(f"Encrypted config file {config_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt config file: {e}")
            return False
    
    def decrypt_config_file(self, encrypted_path: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Decrypt a configuration file
        
        Args:
            encrypted_path: Path to encrypted config file
            password: Decryption password
            
        Returns:
            Dict: Decrypted configuration data
        """
        try:
            with open(encrypted_path, 'r') as f:
                encrypted_config = json.load(f)
            
            if not encrypted_config.get("encrypted"):
                # File is not encrypted, return as-is
                return encrypted_config
            
            decrypted_data = self.decrypt_data(encrypted_config["data"], password)
            self.logger.info(f"Decrypted config file {encrypted_path}")
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt config file: {e}")
            return None


class SecurityAuditor:
    """Security auditing and validation utilities"""
    
    def __init__(self, audit_log_path: str = "/var/log/time-shift/security.log"):
        self.audit_log_path = audit_log_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure audit log directory exists
        Path(audit_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    def log_security_event(self, event_type: str, user: str, action: str, 
                          resource: str, result: str, **kwargs) -> None:
        """
        Log security-relevant events
        
        Args:
            event_type: Type of security event (auth, access, config, etc.)
            user: User performing the action
            action: Action being performed
            resource: Resource being accessed
            result: Result of the action (success/failure)
            **kwargs: Additional context data
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user": user,
            "action": action,
            "resource": resource,
            "result": result,
            "context": kwargs
        }
        
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
    
    def validate_config_security(self, config: Dict[str, Any]) -> Dict[str, list]:
        """
        Validate configuration for security issues
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Dict: Security issues found, categorized by severity
        """
        issues = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        # Check for hardcoded passwords
        self._check_hardcoded_credentials(config, issues)
        
        # Check SSL/TLS settings
        self._check_ssl_settings(config, issues)
        
        # Check file permissions
        self._check_file_permissions(config, issues)
        
        # Check for weak configurations
        self._check_weak_configurations(config, issues)
        
        return issues
    
    def _check_hardcoded_credentials(self, config: Dict[str, Any], issues: Dict[str, list]) -> None:
        """Check for hardcoded credentials in configuration"""
        def check_value(value, path=""):
            if isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, str):
                # Common patterns for hardcoded credentials
                if any(pattern in value.lower() for pattern in ["password", "secret", "key", "token"]):
                    if any(weak in value.lower() for weak in ["password", "123456", "admin", "default"]):
                        issues["critical"].append(f"Weak credential detected at {path}")
                    elif not value.startswith("$") and len(value) < 16:
                        issues["high"].append(f"Potentially hardcoded credential at {path}")
        
        check_value(config)
    
    def _check_ssl_settings(self, config: Dict[str, Any], issues: Dict[str, list]) -> None:
        """Check SSL/TLS configuration settings"""
        ssl_configs = []
        
        def find_ssl_configs(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "ssl" in k.lower() or "tls" in k.lower() or "verify" in k.lower():
                        ssl_configs.append((f"{path}.{k}" if path else k, v))
                    find_ssl_configs(v, f"{path}.{k}" if path else k)
        
        find_ssl_configs(config)
        
        for path, value in ssl_configs:
            if isinstance(value, bool) and not value:
                issues["high"].append(f"SSL verification disabled at {path}")
            elif isinstance(value, str) and value.lower() in ["false", "no", "disabled"]:
                issues["high"].append(f"SSL verification disabled at {path}")
    
    def _check_file_permissions(self, config: Dict[str, Any], issues: Dict[str, list]) -> None:
        """Check file permissions for security"""
        # This would check actual file permissions
        # Implementation depends on specific requirements
        pass
    
    def _check_weak_configurations(self, config: Dict[str, Any], issues: Dict[str, list]) -> None:
        """Check for other weak configuration patterns"""
        # Check for default ports
        if config.get("proxmox", {}).get("port") == 8006:
            issues["low"].append("Using default Proxmox port (consider using non-standard port)")
        
        # Check for overly permissive settings
        if config.get("security", {}).get("allow_root", True):
            issues["medium"].append("Root access is allowed (consider restricting)")


class SecurityManager:
    """Main security management class that coordinates all security functions"""
    
    def __init__(self, config_path: str = "etc/time-shift-config.json"):
        self.config_path = config_path
        self.credential_manager = CredentialManager()
        self.encryption = ConfigEncryption()
        self.auditor = SecurityAuditor()
        self.logger = logging.getLogger(__name__)
    
    def secure_setup(self, password: str) -> bool:
        """
        Perform initial security setup
        
        Args:
            password: Master password for encryption
            
        Returns:
            bool: True if setup successful
        """
        try:
            # Load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Validate current security
                issues = self.auditor.validate_config_security(config)
                if issues["critical"]:
                    self.logger.error(f"Critical security issues found: {issues['critical']}")
                    return False
                
                # Encrypt sensitive configuration
                encrypted_path = f"{self.config_path}.encrypted"
                if self.encryption.encrypt_config_file(self.config_path, encrypted_path, password):
                    self.logger.info("Configuration encrypted successfully")
                    
                    # Create backup of original
                    backup_path = f"{self.config_path}.backup"
                    os.rename(self.config_path, backup_path)
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Security setup failed: {e}")
            return False
    
    def load_secure_config(self, password: str) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt configuration
        
        Args:
            password: Decryption password
            
        Returns:
            Dict: Decrypted configuration
        """
        encrypted_path = f"{self.config_path}.encrypted"
        
        if os.path.exists(encrypted_path):
            config = self.encryption.decrypt_config_file(encrypted_path, password)
            if config:
                self.auditor.log_security_event(
                    "config", "system", "load_config", encrypted_path, "success"
                )
                return config
        
        # Fallback to unencrypted config
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.auditor.log_security_event(
                "config", "system", "load_config", self.config_path, "success",
                warning="Configuration not encrypted"
            )
            return config
        
        return None
    
    def create_api_token(self, user: str, expiry_hours: int = 24) -> str:
        """
        Create a temporary API token for authentication
        
        Args:
            user: Username for the token
            expiry_hours: Token expiry in hours
            
        Returns:
            str: Generated token
        """
        token_data = {
            "user": user,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
            "random": secrets.token_hex(16)
        }
        
        token = base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()
        
        self.auditor.log_security_event(
            "auth", user, "create_token", "api", "success",
            expiry_hours=expiry_hours
        )
        
        return token
    
    def validate_api_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API token
        
        Args:
            token: Token to validate
            
        Returns:
            Dict: Token data if valid, None otherwise
        """
        try:
            token_data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
            
            # Check expiry
            expires = datetime.fromisoformat(token_data["expires"])
            if datetime.now() > expires:
                self.auditor.log_security_event(
                    "auth", token_data.get("user", "unknown"), "validate_token", 
                    "api", "failure", reason="expired"
                )
                return None
            
            self.auditor.log_security_event(
                "auth", token_data["user"], "validate_token", "api", "success"
            )
            
            return token_data
            
        except Exception as e:
            self.auditor.log_security_event(
                "auth", "unknown", "validate_token", "api", "failure", 
                reason=str(e)
            )
            return None


# Example usage and utility functions
def setup_security_example():
    """Example of how to set up security for the time-shift application"""
    security_manager = SecurityManager()
    
    # Perform initial security setup
    master_password = input("Enter master password for encryption: ")
    if security_manager.secure_setup(master_password):
        print("Security setup completed successfully")
        
        # Store sample credentials
        security_manager.credential_manager.store_credential(
            "admin", "secure_password", "proxmox"
        )
        
        # Generate API token
        token = security_manager.create_api_token("admin", 24)
        print(f"API Token generated: {token[:50]}...")
        
    else:
        print("Security setup failed")


if __name__ == "__main__":
    setup_security_example()
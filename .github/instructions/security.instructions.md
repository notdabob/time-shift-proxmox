---
applyTo: ["lib/security.py", "lib/secure_token_storage.py", "lib/validators.py", "**/security/**", "**/auth/**"]
---

# Security Code Instructions

## Security Framework Guidelines

### Credential Management
```python
from lib.security import CredentialManager
import keyring
import os
from pathlib import Path

# NEVER hardcode credentials
class SecureConfig:
    """Secure configuration management"""
    
    def __init__(self):
        self.cred_manager = CredentialManager("time-shift-proxmox")
    
    def get_proxmox_credentials(self) -> tuple[str, str]:
        """Retrieve Proxmox credentials securely"""
        username = os.getenv('PROXMOX_USER')
        password = self.cred_manager.get_credential(username or 'default', 'proxmox')
        
        if not password:
            raise SecurityError("Proxmox credentials not found")
        
        return username, password
    
    def store_idrac_credentials(self, host: str, username: str = "root", password: str = "calvin"):
        """Store iDRAC credentials (Dell defaults are acceptable)"""
        # Dell iDRAC defaults are industry standard and documented
        return self.cred_manager.store_credential(username, password, f"idrac-{host}")
```

### Encryption Utilities
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets

class EncryptionManager:
    """Handle encryption/decryption operations"""
    
    @staticmethod
    def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> str:
        """Encrypt string data"""
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: bytes) -> str:
        """Decrypt string data"""
        try:
            f = Fernet(key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise SecurityError("Failed to decrypt data - invalid key or corrupted data")
```

### Input Validation & Sanitization
```python
import re
import ipaddress
from urllib.parse import urlparse
from typing import Union

class SecurityValidator:
    """Security-focused input validation"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """Validate and normalize IP address"""
        try:
            # This will raise ValueError for invalid IPs
            addr = ipaddress.ip_address(ip)
            return str(addr)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")
    
    @staticmethod
    def validate_hostname(hostname: str) -> str:
        """Validate hostname format"""
        if not hostname or len(hostname) > 253:
            raise ValueError("Invalid hostname length")
        
        # Basic hostname validation
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(pattern, hostname):
            raise ValueError(f"Invalid hostname format: {hostname}")
        
        return hostname.lower()
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> int:
        """Validate port number"""
        try:
            port_num = int(port)
            if not 1 <= port_num <= 65535:
                raise ValueError(f"Port must be between 1 and 65535, got {port_num}")
            return port_num
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port number: {port}")
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        # Remove or replace dangerous characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_chars = re.sub(r'\.\.', '.', safe_chars)  # Prevent directory traversal
        
        # Ensure not empty after sanitization
        if not safe_chars.strip():
            raise ValueError("Filename cannot be empty after sanitization")
        
        return safe_chars.strip()
```

### Secure API Clients
```python
import aiohttp
import ssl
from typing import Dict, Any, Optional

class SecureAPIClient:
    """Secure HTTP client with proper certificate handling"""
    
    def __init__(self, base_url: str, verify_ssl: bool = True, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Configure SSL context
        if verify_ssl:
            self.ssl_context = ssl.create_default_context()
        else:
            # For expired certificates (like iDRAC), disable verification
            # This is intentional for this project's use case
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make secure HTTP request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Security headers
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': 'time-shift-proxmox/1.0',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        })
        kwargs['headers'] = headers
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            connector=aiohttp.TCPConnector(ssl=self.ssl_context)
        ) as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                # Log security-relevant errors without exposing sensitive data
                logger.error(f"API request failed to {self.base_url}", 
                           extra={"method": method, "endpoint": endpoint, "error_type": type(e).__name__})
                raise SecurityError(f"API request failed: {type(e).__name__}")
```

### Audit Logging
```python
import structlog
from datetime import datetime
from typing import Dict, Any, Optional

class SecurityAuditLogger:
    """Security-focused audit logging"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security.audit")
    
    def log_authentication(self, username: str, success: bool, source_ip: str = None):
        """Log authentication attempts"""
        self.logger.info("authentication_attempt",
                        username=username,
                        success=success,
                        source_ip=source_ip,
                        timestamp=datetime.utcnow().isoformat())
    
    def log_privilege_escalation(self, username: str, action: str, target: str = None):
        """Log privilege escalation events"""
        self.logger.warning("privilege_escalation",
                          username=username,
                          action=action,
                          target=target,
                          timestamp=datetime.utcnow().isoformat())
    
    def log_time_manipulation(self, original_time: datetime, target_time: datetime, duration: int):
        """Log time manipulation operations"""
        self.logger.warning("time_manipulation",
                          original_time=original_time.isoformat(),
                          target_time=target_time.isoformat(),
                          duration_seconds=duration,
                          timestamp=datetime.utcnow().isoformat())
    
    def log_ssl_bypass(self, target_host: str, reason: str):
        """Log SSL certificate bypasses"""
        self.logger.info("ssl_verification_bypassed",
                        target_host=target_host,
                        reason=reason,
                        timestamp=datetime.utcnow().isoformat())
    
    def log_security_scan(self, scan_type: str, findings: int, severity: str = "info"):
        """Log security scan results"""
        self.logger.info("security_scan_completed",
                        scan_type=scan_type,
                        findings_count=findings,
                        severity=severity,
                        timestamp=datetime.utcnow().isoformat())
```

### Configuration Security
```python
from pathlib import Path
import stat
import os

class SecureConfigManager:
    """Manage configuration files securely"""
    
    @staticmethod
    def create_secure_config_file(file_path: Path, content: str) -> None:
        """Create configuration file with secure permissions"""
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        file_path.write_text(content)
        
        # Set secure permissions (owner read/write only)
        file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    
    @staticmethod
    def validate_config_permissions(file_path: Path) -> bool:
        """Validate configuration file has secure permissions"""
        if not file_path.exists():
            return False
        
        file_stat = file_path.stat()
        mode = file_stat.st_mode
        
        # Check if file is readable by group or others
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            logger.warning(f"Configuration file {file_path} has insecure permissions")
            return False
        
        return True
    
    @staticmethod
    def backup_config_securely(source: Path, backup_dir: Path) -> Path:
        """Create secure backup of configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{source.name}.{timestamp}.bak"
        
        # Create backup directory with secure permissions
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.chmod(stat.S_IRWXU)  # Owner only
        
        # Copy file and set secure permissions
        backup_path.write_text(source.read_text())
        backup_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        
        return backup_path
```

## Security Best Practices

### 1. Credential Handling
- **NEVER** hardcode credentials in source code
- Use environment variables or secure credential stores
- Dell iDRAC defaults (`root`/`calvin`) are acceptable as they're industry standard
- Rotate credentials regularly where possible

### 2. SSL/TLS Configuration  
- **DO NOT** change `ssl_verify: false` settings - required for expired certificates
- Document why SSL verification is disabled
- Use proper SSL context configuration
- Log SSL bypass events for audit

### 3. Input Validation
- Validate all external inputs
- Sanitize file paths to prevent directory traversal
- Use parameterized queries/API calls
- Implement rate limiting where appropriate

### 4. Logging & Monitoring
- Log all security-relevant events
- Never log sensitive data (passwords, tokens)
- Use structured logging for better analysis
- Include timestamps and source information

### 5. Error Handling
- Don't expose sensitive information in error messages
- Log detailed errors internally
- Return generic error messages to users
- Implement proper exception hierarchies

### 6. Time Operations Security
- Always backup original time before manipulation
- Implement automatic restoration mechanisms
- Log all time changes for audit trails
- Validate time values to prevent overflow/underflow

### 7. File Operations
- Set secure file permissions (600 for config files)
- Validate file paths to prevent traversal attacks
- Use atomic file operations where possible
- Regular backup of critical configuration

### Common Security Anti-patterns to Avoid

1. **Logging credentials**: Never log passwords or API keys
2. **Weak randomness**: Use `secrets` module, not `random`
3. **SQL injection**: Use parameterized queries
4. **Path traversal**: Validate and sanitize file paths
5. **Information leakage**: Generic error messages for users
6. **Insecure defaults**: Fail secure, not open
7. **Missing input validation**: Validate all external inputs
8. **Weak encryption**: Use modern algorithms and proper key management
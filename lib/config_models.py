"""
Configuration Models - Pydantic models for configuration validation
Provides type-safe configuration parsing and validation
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, IPvAnyAddress
from enum import Enum
from datetime import datetime
import ipaddress


class LogLevel(str, Enum):
    """Supported logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OSType(str, Enum):
    """Supported OS types for VM creation"""
    LINUX_26 = "l26"
    LINUX_24 = "l24"
    WINDOWS = "win"
    OTHER = "other"


class NetworkConfigType(str, Enum):
    """Network configuration types"""
    DHCP = "dhcp"
    STATIC = "static"
    MANUAL = "manual"


class ProxmoxConfig(BaseModel):
    """Proxmox VE configuration"""
    host: Union[IPvAnyAddress, str] = Field(..., description="Proxmox host IP or hostname")
    port: int = Field(default=8006, ge=1, le=65535, description="Proxmox API port")
    username: str = Field(..., min_length=1, description="Proxmox username")
    password: str = Field(..., min_length=1, description="Proxmox password")
    node: str = Field(..., min_length=1, description="Proxmox node name")
    verify_ssl: bool = Field(default=False, description="Verify SSL certificates")
    timeout: int = Field(default=30, ge=5, le=300, description="API timeout in seconds")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if '@' not in v:
            raise ValueError('Username must include realm (e.g., root@pam)')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Basic password strength validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if v.lower() in ['password', '12345678', 'admin123']:
            raise ValueError('Password is too weak')
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "host": "192.168.1.100",
                "port": 8006,
                "username": "root@pam",
                "password": "secure_password_123",
                "node": "proxmox-node-01",
                "verify_ssl": False,
                "timeout": 30
            }
        }


class VMConfig(BaseModel):
    """Virtual Machine configuration"""
    name: str = Field(..., min_length=1, max_length=15, description="VM name")
    memory: int = Field(default=2048, ge=512, le=32768, description="Memory in MB")
    cores: int = Field(default=2, ge=1, le=32, description="CPU cores")
    disk_size: int = Field(default=20, ge=10, le=1000, description="Disk size in GB")
    os_type: OSType = Field(default=OSType.LINUX_26, description="Operating system type")
    template: Optional[str] = Field(default=None, description="Template to clone from")
    
    @validator('name')
    def validate_vm_name(cls, v):
        """Validate VM name format"""
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('VM name can only contain letters, numbers, and hyphens')
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "name": "time-shift-vm",
                "memory": 2048,
                "cores": 2,
                "disk_size": 20,
                "os_type": "l26",
                "template": "debian-12-standard"
            }
        }


class NetworkConfig(BaseModel):
    """Network configuration"""
    bridge: str = Field(default="vmbr0", description="Network bridge")
    ip_config: NetworkConfigType = Field(default=NetworkConfigType.DHCP, description="IP configuration type")
    ip_address: Optional[IPvAnyAddress] = Field(default=None, description="Static IP address")
    netmask: Optional[str] = Field(default=None, description="Network mask")
    gateway: Optional[IPvAnyAddress] = Field(default=None, description="Gateway IP")
    dns_servers: List[Union[IPvAnyAddress, str]] = Field(default_factory=list, description="DNS servers")
    
    @validator('ip_address')
    def validate_static_ip_requirements(cls, v, values):
        """Validate static IP configuration requirements"""
        if values.get('ip_config') == NetworkConfigType.STATIC:
            if v is None:
                raise ValueError('IP address is required for static configuration')
        return v
    
    @validator('netmask')
    def validate_netmask(cls, v):
        """Validate netmask format"""
        if v is not None:
            try:
                ipaddress.IPv4Network(f"192.168.1.1/{v}", strict=False)
            except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                raise ValueError('Invalid netmask format')
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "bridge": "vmbr0",
                "ip_config": "dhcp",
                "dns_servers": ["8.8.8.8", "8.8.4.4"]
            }
        }


class TimeConfig(BaseModel):
    """Time manipulation configuration"""
    timezone: str = Field(default="UTC", description="System timezone")
    ntp_servers: List[str] = Field(default_factory=lambda: ["pool.ntp.org", "time.nist.gov"], description="NTP servers")
    backup_original: bool = Field(default=True, description="Backup original time settings")
    max_shift_days: int = Field(default=3650, ge=1, le=7300, description="Maximum days to shift (safety limit)")
    auto_restore_hours: int = Field(default=24, ge=1, le=168, description="Auto-restore after hours")
    
    @validator('ntp_servers')
    def validate_ntp_servers(cls, v):
        """Validate NTP server list"""
        if not v:
            raise ValueError('At least one NTP server is required')
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "timezone": "UTC",
                "ntp_servers": ["pool.ntp.org", "time.nist.gov"],
                "backup_original": True,
                "max_shift_days": 365,
                "auto_restore_hours": 24
            }
        }


class IDRACConfig(BaseModel):
    """iDRAC connection configuration
    
    Dell iDRAC standard default credentials:
    - Username: root
    - Password: calvin
    
    These are Dell's factory defaults for all iDRAC interfaces.
    """
    default_username: str = Field(default="root", description="Default iDRAC username (Dell standard)")
    default_password: str = Field(default="calvin", description="Default iDRAC password (Dell standard)")
    ssl_verify: bool = Field(default=False, description="Verify SSL certificates")
    timeout: int = Field(default=30, ge=5, le=120, description="Connection timeout")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Retry attempts")
    retry_delay: int = Field(default=5, ge=1, le=60, description="Delay between retries in seconds")
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "default_username": "root",
                "default_password": "calvin",
                "ssl_verify": False,
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    file: str = Field(default="/var/log/time-shift/time-shift.log", description="Log file path")
    max_size: str = Field(default="10MB", description="Maximum log file size")
    backup_count: int = Field(default=5, ge=1, le=50, description="Number of backup log files")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    console_output: bool = Field(default=True, description="Enable console output")
    structured: bool = Field(default=False, description="Use structured JSON logging")
    
    @validator('max_size')
    def validate_max_size(cls, v):
        """Validate log file size format"""
        import re
        if not re.match(r'^\d+[KMGT]?B?$', v.upper()):
            raise ValueError('Invalid size format. Use format like "10MB", "1GB", etc.')
        return v
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "level": "INFO",
                "file": "/var/log/time-shift/time-shift.log",
                "max_size": "10MB",
                "backup_count": 5,
                "console_output": True,
                "structured": False
            }
        }


class SecurityConfig(BaseModel):
    """Security configuration"""
    encrypt_passwords: bool = Field(default=True, description="Encrypt stored passwords")
    allow_root: bool = Field(default=False, description="Allow root user operations")
    require_confirmation: bool = Field(default=True, description="Require operation confirmation")
    api_key_length: int = Field(default=32, ge=16, le=128, description="API key length")
    session_timeout: int = Field(default=3600, ge=300, le=86400, description="Session timeout in seconds")
    max_login_attempts: int = Field(default=3, ge=1, le=10, description="Maximum login attempts")
    lockout_duration: int = Field(default=300, ge=60, le=3600, description="Lockout duration in seconds")
    audit_log: bool = Field(default=True, description="Enable audit logging")
    
    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "encrypt_passwords": True,
                "allow_root": False,
                "require_confirmation": True,
                "api_key_length": 32,
                "session_timeout": 3600,
                "max_login_attempts": 3,
                "lockout_duration": 300,
                "audit_log": True
            }
        }


class TimeShiftConfig(BaseModel):
    """Main configuration model"""
    proxmox: ProxmoxConfig
    vm: VMConfig
    network: NetworkConfig
    time: TimeConfig
    idrac: IDRACConfig
    logging: LoggingConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Metadata
    version: str = Field(default="0.2.0", description="Configuration version")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Configuration creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Last update time")
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            IPvAnyAddress: str,
        }
        schema_extra = {
            "example": {
                "proxmox": {
                    "host": "192.168.1.100",
                    "port": 8006,
                    "username": "root@pam",
                    "password": "secure_password",
                    "node": "proxmox-node",
                    "verify_ssl": False
                },
                "vm": {
                    "name": "time-shift-vm",
                    "memory": 2048,
                    "cores": 2,
                    "disk_size": 20,
                    "os_type": "l26"
                },
                "network": {
                    "bridge": "vmbr0",
                    "ip_config": "dhcp"
                },
                "time": {
                    "timezone": "UTC",
                    "backup_original": True
                },
                "idrac": {
                    "default_username": "root",
                    "ssl_verify": False
                },
                "logging": {
                    "level": "INFO",
                    "console_output": True
                },
                "security": {
                    "encrypt_passwords": True,
                    "require_confirmation": True
                }
            }
        }


# Utility functions for configuration management
def load_config_from_file(file_path: str) -> TimeShiftConfig:
    """
    Load and validate configuration from file
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        TimeShiftConfig: Validated configuration object
        
    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If configuration file not found
    """
    import json
    from pathlib import Path
    
    config_file = Path(file_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    try:
        return TimeShiftConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


def save_config_to_file(config: TimeShiftConfig, file_path: str) -> None:
    """
    Save configuration to file
    
    Args:
        config: Configuration object to save
        file_path: Path to save configuration file
    """
    import json
    from pathlib import Path
    
    # Update timestamp
    config.updated_at = datetime.now()
    
    # Ensure directory exists
    config_file = Path(file_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config.dict(), f, indent=2, default=str)


def create_default_config() -> TimeShiftConfig:
    """
    Create a default configuration with sensible defaults
    
    Returns:
        TimeShiftConfig: Default configuration object
    """
    return TimeShiftConfig(
        proxmox=ProxmoxConfig(
            host="192.168.1.100",
            username="root@pam",
            password="change_me",
            node="proxmox-node"
        ),
        vm=VMConfig(),
        network=NetworkConfig(),
        time=TimeConfig(),
        idrac=IDRACConfig(),
        logging=LoggingConfig(),
        security=SecurityConfig()
    )


def validate_config_security(config: TimeShiftConfig) -> List[str]:
    """
    Validate configuration for security issues
    
    Args:
        config: Configuration to validate
        
    Returns:
        List[str]: List of security warnings/issues
    """
    warnings = []
    
    # Check for weak passwords
    if config.proxmox.password in ['password', 'admin', 'change_me']:
        warnings.append("Proxmox password appears to be weak or default")
    
    if config.idrac.default_password == 'calvin':
        warnings.append("Using default iDRAC password")
    
    # Check SSL settings
    if not config.proxmox.verify_ssl:
        warnings.append("SSL verification disabled for Proxmox")
    
    if not config.idrac.ssl_verify:
        warnings.append("SSL verification disabled for iDRAC")
    
    # Check security settings
    if config.security.allow_root:
        warnings.append("Root access is enabled")
    
    if not config.security.encrypt_passwords:
        warnings.append("Password encryption is disabled")
    
    if not config.security.require_confirmation:
        warnings.append("Operation confirmation is disabled")
    
    return warnings


if __name__ == "__main__":
    # Example usage
    try:
        # Create default config
        config = create_default_config()
        print("Default configuration created successfully")
        
        # Validate security
        warnings = validate_config_security(config)
        if warnings:
            print("Security warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        # Save to file
        save_config_to_file(config, "example_config.json")
        print("Configuration saved to example_config.json")
        
        # Load from file
        loaded_config = load_config_from_file("example_config.json")
        print("Configuration loaded and validated successfully")
        
    except Exception as e:
        print(f"Error: {e}")
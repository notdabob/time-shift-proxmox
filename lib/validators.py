"""
Input Validation Module - Centralized validation functions
"""

import re
import ipaddress
from typing import Union, Optional, Tuple
from pathlib import Path


class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


def validate_ip_address(ip: str) -> str:
    """
    Validate IP address (IPv4 or IPv6)
    
    Args:
        ip: IP address string
        
    Returns:
        str: Validated IP address
        
    Raises:
        ValidationError: If IP is invalid
    """
    try:
        # This handles both IPv4 and IPv6
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        raise ValidationError(f"Invalid IP address: {ip}")


def validate_hostname(hostname: str) -> str:
    """
    Validate hostname according to RFC 1123
    
    Args:
        hostname: Hostname string
        
    Returns:
        str: Validated hostname
        
    Raises:
        ValidationError: If hostname is invalid
    """
    if not hostname or len(hostname) > 253:
        raise ValidationError("Hostname must be between 1 and 253 characters")
    
    # Remove trailing dot if present
    if hostname.endswith('.'):
        hostname = hostname[:-1]
    
    # Check each label
    labels = hostname.split('.')
    for label in labels:
        if not label or len(label) > 63:
            raise ValidationError("Each hostname label must be between 1 and 63 characters")
        
        # Label must start with alphanumeric, end with alphanumeric,
        # and contain only alphanumeric and hyphens
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
            raise ValidationError(f"Invalid hostname label: {label}")
    
    return hostname


def validate_port(port: Union[int, str]) -> int:
    """
    Validate network port number
    
    Args:
        port: Port number (int or string)
        
    Returns:
        int: Validated port number
        
    Raises:
        ValidationError: If port is invalid
    """
    try:
        port_num = int(port)
        if not 1 <= port_num <= 65535:
            raise ValidationError(f"Port must be between 1 and 65535, got {port_num}")
        return port_num
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid port number: {port}")


def validate_username(username: str) -> str:
    """
    Validate username (alphanumeric, underscore, hyphen, dot)
    
    Args:
        username: Username string
        
    Returns:
        str: Validated username
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username:
        raise ValidationError("Username cannot be empty")
    
    if len(username) > 255:
        raise ValidationError("Username too long (max 255 characters)")
    
    # Allow alphanumeric, underscore, hyphen, dot, @
    if not re.match(r'^[a-zA-Z0-9._@-]+$', username):
        raise ValidationError(f"Invalid username: {username}")
    
    return username


def validate_vm_name(name: str) -> str:
    """
    Validate VM name for Proxmox
    
    Args:
        name: VM name
        
    Returns:
        str: Validated VM name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("VM name cannot be empty")
    
    if len(name) > 63:
        raise ValidationError("VM name too long (max 63 characters)")
    
    # Proxmox VM names: alphanumeric and hyphen
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*$', name):
        raise ValidationError(f"Invalid VM name: {name}. Must start with alphanumeric and contain only alphanumeric and hyphens")
    
    return name


def validate_path(path: str, must_exist: bool = False, 
                 must_be_file: bool = False, must_be_dir: bool = False) -> Path:
    """
    Validate file system path
    
    Args:
        path: Path string
        must_exist: Whether path must exist
        must_be_file: Whether path must be a file
        must_be_dir: Whether path must be a directory
        
    Returns:
        Path: Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path_obj = Path(path).resolve()
        
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")
        
        if must_be_file and path_obj.exists() and not path_obj.is_file():
            raise ValidationError(f"Path is not a file: {path}")
        
        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        
        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid path: {path} - {e}")


def validate_command(command: str, allow_shell: bool = False) -> str:
    """
    Validate shell command for safety
    
    Args:
        command: Command string
        allow_shell: Whether to allow shell metacharacters
        
    Returns:
        str: Validated command
        
    Raises:
        ValidationError: If command contains dangerous patterns
    """
    if not command:
        raise ValidationError("Command cannot be empty")
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'\$\(',  # Command substitution $(...)
        r'`',     # Backticks
        r';\s*rm', # rm after semicolon
        r'>\s*/dev/.*', # Redirecting to devices
    ]
    
    if not allow_shell:
        # Additional patterns for non-shell commands
        dangerous_patterns.extend([
            r'&&',
            r'\|\|',
            r';',
            r'\|',
            r'>',
            r'<',
            r'\$',
        ])
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            raise ValidationError(f"Command contains potentially dangerous pattern: {pattern}")
    
    return command


def validate_idrac_credentials(username: str, password: str) -> Tuple[str, str]:
    """
    Validate iDRAC credentials
    
    Args:
        username: iDRAC username
        password: iDRAC password
        
    Returns:
        Tuple[str, str]: Validated credentials
        
    Raises:
        ValidationError: If credentials are invalid
    """
    # Validate username
    if not username:
        raise ValidationError("iDRAC username cannot be empty")
    
    # iDRAC usernames are typically alphanumeric
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError(f"Invalid iDRAC username: {username}")
    
    # Validate password
    if not password:
        raise ValidationError("iDRAC password cannot be empty")
    
    # Basic length check (iDRAC passwords have specific requirements)
    if len(password) < 8:
        raise ValidationError("iDRAC password must be at least 8 characters")
    
    return username, password


def validate_proxmox_node(node: str) -> str:
    """
    Validate Proxmox node name
    
    Args:
        node: Node name
        
    Returns:
        str: Validated node name
        
    Raises:
        ValidationError: If node name is invalid
    """
    if not node:
        raise ValidationError("Node name cannot be empty")
    
    # Proxmox node names follow hostname rules
    return validate_hostname(node)


def validate_github_token(token: str) -> str:
    """
    Validate GitHub personal access token format
    
    Args:
        token: GitHub token
        
    Returns:
        str: Validated token
        
    Raises:
        ValidationError: If token format is invalid
    """
    if not token:
        raise ValidationError("GitHub token cannot be empty")
    
    # GitHub tokens start with specific prefixes
    valid_prefixes = ['ghp_', 'github_pat_', 'ghs_', 'ghr_']
    
    if not any(token.startswith(prefix) for prefix in valid_prefixes):
        raise ValidationError(f"Invalid GitHub token format. Should start with one of: {', '.join(valid_prefixes)}")
    
    # Basic length check
    if len(token) < 40:
        raise ValidationError("GitHub token appears too short")
    
    return token


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"|?*\x00\\/'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    # Truncate if too long
    if len(filename) > max_length:
        # Keep extension if present
        parts = filename.rsplit('.', 1)
        if len(parts) == 2 and len(parts[1]) <= 10:  # Reasonable extension length
            name, ext = parts
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]
    
    return filename


# Convenience validation decorators
def validate_input(*validators):
    """
    Decorator to validate function inputs
    
    Usage:
        @validate_input(validate_ip_address, validate_port)
        def connect(ip, port):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate positional arguments
            validated_args = []
            for i, (arg, validator) in enumerate(zip(args, validators)):
                if validator:
                    try:
                        validated_args.append(validator(arg))
                    except ValidationError as e:
                        raise ValidationError(f"Argument {i}: {e}")
                else:
                    validated_args.append(arg)
            
            # Add remaining args that don't have validators
            validated_args.extend(args[len(validators):])
            
            return func(*validated_args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test validations
    try:
        print("Testing validations...")
        
        # Test IP validation
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"
        assert validate_ip_address("::1") == "::1"
        
        # Test hostname validation
        assert validate_hostname("proxmox-node01.local") == "proxmox-node01.local"
        
        # Test port validation
        assert validate_port(8006) == 8006
        assert validate_port("443") == 443
        
        # Test username validation
        assert validate_username("root@pam") == "root@pam"
        
        # Test VM name validation
        assert validate_vm_name("time-shift-vm") == "time-shift-vm"
        
        print("All validations passed!")
        
    except ValidationError as e:
        print(f"Validation error: {e}")
# GitHub Copilot Instructions for Time-Shift Proxmox

## Project Overview

This is a specialized Debian-based VM template for Proxmox that can temporarily shift system time to access iDRAC interfaces with expired SSL certificates. The project focuses on Dell iDRAC management through time manipulation while maintaining security and operational integrity.

## Core Architecture

- **Plugin-based system**: Extensible architecture with plugin manager (`lib/integration_plugins.py`)
- **Async operations**: Heavy use of asyncio for API calls and time operations
- **Type safety**: Pydantic models for configuration validation (`lib/config_models.py`)
- **Security framework**: Comprehensive security tools and credential management (`lib/security.py`)
- **Health monitoring**: Built-in health check framework (`lib/health_checks.py`)

## Development Standards

### Code Style & Quality
- **Python 3.8+** minimum version
- **Black** formatting (line length: 88)
- **MyPy** type checking with strict settings
- **isort** import sorting with black profile
- **Bandit** security scanning
- **Pytest** for testing with coverage

### Project Structure
```
├── lib/          # Core library modules
├── bin/          # Executable scripts
├── tests/        # Test suite
├── etc/          # Configuration files
├── docs/         # Documentation
└── scripts/      # Utility scripts
```

## Security Guidelines

### **CRITICAL - DO NOT MODIFY:**
- `ssl_verify: false` settings (required for expired certificates)
- Dell default iDRAC credentials (`root`/`calvin`)
- `etc/time-shift-config.json` structure
- No symlinks within the project

### Security Best Practices
- Use `CredentialManager` class for sensitive data storage
- Implement proper input validation with Pydantic models
- Use `structlog` for security event logging
- Encrypt configuration files containing credentials
- Follow principle of least privilege for VM operations

## Code Patterns & Conventions

### Pydantic Models
```python
class ConfigModel(BaseModel):
    """Always include docstrings"""
    field: str = Field(..., description="Clear field description")
    
    @validator('field')
    def validate_field(cls, v):
        """Implement validation logic"""
        return v
```

### Plugin Development
```python
class CustomPlugin(IntegrationPlugin):
    """Extend IntegrationPlugin base class"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom-plugin",
            version="1.0.0",
            capabilities=["deploy", "manage"],
            priority=PluginPriority.NORMAL
        )
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Implementation with proper error handling"""
```

### Error Handling
- Use custom exception classes inheriting from base exceptions
- Implement comprehensive logging with `structlog`
- Always handle async operations with proper try/catch
- Use Rich console for user-friendly error messages

### Time Operations
- **ALWAYS** backup original time before manipulation
- Implement automatic restoration mechanisms
- Use `lib/time_ops.py` for all time-related operations
- Log all time changes for audit trails

## API Integrations

### Proxmox API
- Use `lib/proxmox_api.py` and `lib/proxmox_api_async.py`
- Always validate SSL certificates are disabled when needed
- Implement proper connection pooling for async operations
- Handle API versioning and compatibility

### Dell iDRAC
- Default credentials: `root`/`calvin` (Dell factory standards)
- SSL verification disabled by design for expired certificates
- Use time-shifting to access interfaces with date issues

## Configuration Management

### Environment Variables
```python
# Use python-dotenv for environment management
from dotenv import load_dotenv
load_dotenv()

# Prefer environment variables for sensitive config
api_key = os.getenv('PROXMOX_API_KEY')
```

### Configuration Files
- Use `etc/` directory for all config files
- Validate with Pydantic models
- Support both JSON and YAML formats
- Implement configuration templating for deployments

## Testing Guidelines

### Test Organization
```python
# tests/test_module.py
import pytest
from unittest.mock import Mock, patch

class TestModule:
    """Test class for module functionality"""
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async operations"""
    
    @pytest.mark.integration
    def test_integration(self):
        """Mark integration tests"""
    
    @pytest.mark.security
    def test_security_feature(self):
        """Mark security-related tests"""
```

### Test Fixtures
- Use pytest fixtures for common setup
- Mock external dependencies (Proxmox API, time operations)
- Test both success and failure scenarios
- Include edge cases and security boundaries

## CLI Development

### Click Framework
```python
import click
from rich.console import Console

console = Console()

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def command(ctx, verbose: bool):
    """Use Rich for enhanced console output"""
    console.print("[green]Success message[/green]")
```

### Master CLI Integration
- Extend `master.py` for new commands
- Use consistent option naming
- Implement progress indicators with Rich
- Provide clear error messages and help text

## Docker & Containerization

### Docker Patterns
- Use multi-stage builds for optimization
- Implement health checks in containers
- Follow security best practices for container images
- Use `docker/` directory for Docker-related files

### Compose Integration
- Support Docker Compose for complex deployments
- Use environment variable injection
- Implement proper service dependencies
- Include monitoring and logging services

## Documentation Standards

### Code Documentation
```python
def function(param: str) -> bool:
    """
    Brief description of function purpose.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: Description of when raised
        
    Example:
        >>> function("example")
        True
    """
```

### README Updates
- Keep installation instructions current
- Document all CLI commands with examples
- Include troubleshooting sections
- Maintain security considerations section

## Performance Considerations

### Async Operations
- Use `aiohttp` for HTTP requests
- Implement connection pooling
- Use proper timeout configurations
- Handle concurrent operations efficiently

### Resource Management
- Implement proper cleanup in context managers
- Use lazy loading for heavy operations
- Monitor memory usage in long-running operations
- Optimize database/API query patterns

## Deployment & Operations

### VM Template Creation
- Use standardized VM configurations
- Implement proper templating system
- Include monitoring and logging setup
- Follow security hardening guidelines

### Monitoring & Logging
- Use `structlog` for structured logging
- Implement health check endpoints
- Monitor time synchronization status
- Track SSL certificate states

## Common Pitfalls to Avoid

1. **Time Zone Issues**: Always work in UTC internally
2. **SSL Certificate Validation**: Don't enable where disabled by design
3. **Credential Exposure**: Never log sensitive credentials
4. **Resource Leaks**: Always cleanup VM resources and connections
5. **Race Conditions**: Proper async synchronization for time operations
6. **Configuration Drift**: Validate configurations against models

## Integration Points

### External Systems
- Proxmox VE API integration
- Dell iDRAC management interfaces
- Container orchestration platforms
- Monitoring and alerting systems

### Plugin Ecosystem
- Security scanning plugins
- Backup and restore plugins
- Network validation plugins
- Deployment automation plugins

When contributing code, always consider the security implications, especially around time manipulation and credential management. Maintain the plugin architecture principles and ensure all new functionality integrates with the existing health check and security frameworks.
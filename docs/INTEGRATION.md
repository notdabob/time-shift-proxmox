# Time Shift Proxmox - Integration Master Documentation

## 🚀 One-Click Integration System

The Time Shift Proxmox project now features a comprehensive one-click integration system that provides holistic automation for all deployment, configuration, and management tasks.

## Quick Start

```bash
# One-click setup - handles everything automatically
./one-click-setup.sh

# Or use individual components:
./master.py         # Unified CLI for all operations
./integrate.py      # Integration framework management
```

## Architecture Overview

### 1. **Master CLI (`master.py`)**
The unified command interface that provides:
- VM deployment and management
- Docker container orchestration
- Health monitoring
- Security scanning
- Configuration management
- Plugin system control

### 2. **Integration Framework (`integrate.py`)**
Modular integration system featuring:
- Auto-discovery of integrations
- Manifest-based configuration
- Health check validation
- Hook system for customization
- Parallel execution support

### 3. **Plugin Architecture**
Extensible plugin system with:
- Built-in plugins (Proxmox, Docker, Git, Security, Monitoring)
- Dynamic plugin loading
- Priority-based execution
- Dependency management
- Event hooks

### 4. **Configuration Templating**
Dynamic configuration generation:
- Jinja2-based templates
- Multi-format support (JSON, YAML, ENV, INI, TOML)
- Interactive configuration wizard
- Validation and defaults
- Configuration sets

### 5. **Health Check Framework**
Comprehensive validation system:
- System resource monitoring
- Network connectivity checks
- Service availability validation
- Dependency verification
- Real-time status reporting

## Available Commands

### Master CLI Commands

```bash
# VM Operations
./master.py vm deploy --name my-vm --cores 4 --memory 4096
./master.py vm manage --vmid 100 --action start
./master.py vm timeshift --date 2023-01-01 --duration 300

# Docker Operations
./master.py docker up --build
./master.py docker down
./master.py docker logs

# System Management
./master.py health --full
./master.py security --level full --fix
./master.py status
./master.py backup --type all --destination /backups

# Configuration
./master.py wizard
./master.py plugins --plugin proxmox
```

### Integration Framework Commands

```bash
# Integration Management
./integrate.py list                    # List all integrations
./integrate.py info proxmox-deploy     # Show integration details
./integrate.py run proxmox-deploy      # Run specific integration
./integrate.py deploy --type deploy    # Deploy all integrations

# Interactive Mode
./integrate.py wizard                  # Guided integration setup
./integrate.py init                    # Initialize framework
```

## Integration Manifest Format

Create custom integrations by adding a `manifest.yaml` file:

```yaml
name: my-integration
version: 1.0.0
description: Custom integration for specific task
type: deploy  # deploy|configure|test|monitor|backup|restore|update|security|performance
platforms:
  - linux
  - darwin
requirements:
  - python-package>=1.0.0
dependencies:
  - another-integration
tags:
  - custom
  - automation
config_template:
  setting1: default_value
  setting2: another_default
commands:
  default: "echo 'Running integration'"
  test: "pytest tests/"
  deploy: "ansible-playbook deploy.yml"
health_checks:
  - check_service_running
  - verify_configuration
pre_hooks:
  - "echo 'Preparing...'"
post_hooks:
  - "echo 'Completed!'"
environment:
  MY_VAR: value
```

## Plugin Development

Create custom plugins by extending the base class:

```python
from lib.integration_plugins import IntegrationPlugin, PluginMetadata, PluginPriority

class MyCustomPlugin(IntegrationPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            author="Your Name",
            description="Custom plugin description",
            priority=PluginPriority.MEDIUM,
            capabilities=["action1", "action2"],
            config_schema={
                "setting": {"type": "string", "required": True}
            }
        )
    
    async def initialize(self) -> bool:
        # Initialize plugin resources
        return True
    
    async def execute(self, action: str, **kwargs) -> Any:
        if action == "action1":
            return await self.do_action1(**kwargs)
        elif action == "action2":
            return await self.do_action2(**kwargs)
```

## Configuration Templates

The system includes pre-built templates for:

1. **Proxmox Configuration**
   - Connection settings
   - VM defaults
   - Network configuration

2. **Docker Compose**
   - Service definitions
   - Network setup
   - Volume management

3. **Kubernetes Deployment**
   - Deployment specs
   - Service configuration
   - Resource limits

4. **Environment Variables**
   - Application settings
   - API keys
   - Feature flags

### Creating Configuration Sets

```bash
# Interactive template configuration
python3 -c "
from lib.config_templating import ConfigTemplateEngine
engine = ConfigTemplateEngine()
engine.create_config_set('production', ['proxmox', 'docker-compose', 'environment'], {
    'proxmox_host': '10.0.0.100',
    'app_name': 'timeshift-prod'
})
"
```

## Health Check System

The framework includes comprehensive health checks:

- **System Resources**: CPU, memory, disk usage
- **Network**: Connectivity, DNS, response times
- **Services**: Docker, Proxmox API, database connections
- **Dependencies**: Python packages, system tools
- **Security**: SSL certificates, file permissions
- **API Endpoints**: Service availability

## Integration Workflow

1. **Discovery Phase**
   - Scans `integrations/` directory
   - Loads manifest files
   - Registers built-in integrations

2. **Validation Phase**
   - Checks platform compatibility
   - Verifies requirements
   - Validates configuration

3. **Execution Phase**
   - Runs pre-hooks
   - Executes main commands
   - Processes post-hooks
   - Performs health checks

4. **Monitoring Phase**
   - Tracks execution status
   - Collects metrics
   - Reports results

## Best Practices

1. **Integration Design**
   - Keep integrations focused and single-purpose
   - Use descriptive names and clear documentation
   - Implement proper error handling
   - Include comprehensive health checks

2. **Configuration Management**
   - Use templates for consistency
   - Store sensitive data securely
   - Version control configurations
   - Validate before deployment

3. **Plugin Development**
   - Follow the plugin interface strictly
   - Implement proper initialization
   - Handle cleanup in shutdown
   - Use async/await for I/O operations

4. **Security**
   - Never hardcode credentials
   - Use environment variables for secrets
   - Implement proper permission checks
   - Regular security scanning

## Troubleshooting

### Common Issues

1. **Integration Not Found**
   - Check manifest.yaml syntax
   - Verify file location
   - Run `./integrate.py list`

2. **Plugin Loading Fails**
   - Check Python dependencies
   - Verify plugin class structure
   - Review initialization logs

3. **Health Check Failures**
   - Run individual checks
   - Check service status
   - Verify network connectivity

### Debug Mode

```bash
# Enable verbose logging
export DEBUG=1
./master.py health --verbose

# Check specific integration
./integrate.py run my-integration --dry-run
```

## Advanced Features

### Parallel Execution
```bash
# Deploy multiple integrations concurrently
./integrate.py deploy --type deploy

# Sequential execution for dependencies
./integrate.py deploy --sequential
```

### Custom Hooks
```python
# Register custom hooks
manager.register_hook("pre_deploy", my_pre_deploy_function)
manager.register_hook("post_deploy", my_post_deploy_function)
```

### Telemetry Integration
```python
# Add monitoring hooks
@manager.register_hook("post_execute")
async def track_execution(plugin, result, **kwargs):
    # Send metrics to monitoring system
    await send_metrics({
        "plugin": plugin.metadata.name,
        "success": result.get("status") == "success",
        "duration": result.get("duration")
    })
```

## Contributing

To add new integrations:

1. Create directory: `integrations/your-integration/`
2. Add `manifest.yaml` with proper configuration
3. Include any supporting scripts or templates
4. Test with `./integrate.py run your-integration`
5. Submit pull request with documentation

## License

This integration system is part of the Time Shift Proxmox project and follows the same license terms.
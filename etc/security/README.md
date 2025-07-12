# Security Configuration Documentation

This directory contains security policies and configurations for the Time-Shift Proxmox project.

## Files

### 1. command-permissions.json
**Purpose**: Define which commands can be executed with auto-approval, require confirmation, or are forbidden.

**Used by**:
- `scripts/safe-commands.sh` - Command validation in shell scripts
- `master.py` - CLI command execution
- Integration framework - Plugin command execution

**Key Features**:
- Command whitelisting with granular control
- Auto-approval for safe operations
- Confirmation requirements for risky operations
- Forbidden command blacklist
- Pattern matching for command validation

### 2. execution-policy.yaml
**Purpose**: Comprehensive security policies for the entire execution environment.

**Covers**:
- Authentication and session management
- Network security policies
- File system access controls
- Process execution limits
- Logging and auditing
- Secrets management
- Compliance standards
- Emergency procedures

## Usage Examples

### Validating a Command
```python
import json

with open('etc/security/command-permissions.json') as f:
    permissions = json.load(f)

def is_command_allowed(command):
    cmd_parts = command.split()
    base_cmd = cmd_parts[0]
    
    # Check if forbidden
    if command in permissions['forbidden_commands']:
        return False, "Command is forbidden"
    
    # Check if approved
    if base_cmd in permissions['approved_commands']:
        cmd_config = permissions['approved_commands'][base_cmd]
        if cmd_config.get('auto_approve'):
            return True, "Auto-approved"
        elif cmd_config.get('require_confirmation'):
            return None, "Requires confirmation"
    
    return False, "Command not in whitelist"
```

### Reading Security Policy
```python
import yaml

with open('etc/security/execution-policy.yaml') as f:
    policy = yaml.safe_load(f)

# Check SSL verification policy
ssl_verify = policy['network']['ssl_verification']['default']

# Get session timeout
timeout = policy['authentication']['session_timeout']
```

## Security Best Practices

1. **Never modify these files directly in production** - Changes should go through code review
2. **Regular audits** - Review command permissions quarterly
3. **Principle of least privilege** - Only whitelist necessary commands
4. **Monitor logs** - Check audit logs for security violations
5. **Update policies** - Keep policies current with new threats

## Integration with Scripts

The `safe-commands.sh` script uses these policies:
```bash
#!/bin/bash
# Example usage in safe-commands.sh

PERMISSIONS_FILE="etc/security/command-permissions.json"

validate_command() {
    local cmd="$1"
    # Validation logic using jq or python
    python -c "
import json
with open('$PERMISSIONS_FILE') as f:
    perms = json.load(f)
    # Validation logic here
"
}
```

## File Locations

### command-permissions.json
- **Location**: `etc/security/command-permissions.json`
- **Purpose**: Define command execution permissions and security rules
- **Note**: The original `scripts/command-permissions.json` has been moved here

### execution-policy.yaml
- **Location**: `etc/security/execution-policy.yaml`
- **Purpose**: Comprehensive security policies for the execution environment

## Migration Notes

The enhanced `command-permissions.json` adds:
- Comprehensive documentation via `_description` and `_usage` fields
- More command coverage (20+ commands vs original 5)
- Detailed security rules and forbidden patterns
- Descriptions for each command
- Granular control over subcommands and flags

### Updating Scripts

If you have scripts that reference the old location, update them:
```bash
# Old location
PERMISSIONS_FILE="scripts/command-permissions.json"

# New location
PERMISSIONS_FILE="etc/security/command-permissions.json"
```

## Future Enhancements

1. **Dynamic policy loading** - Reload policies without restart
2. **Policy validation** - JSON schema validation for policies
3. **Policy versioning** - Track policy changes over time
4. **Integration with SIEM** - Send security events to SIEM systems
5. **Machine learning** - Anomaly detection for command patterns
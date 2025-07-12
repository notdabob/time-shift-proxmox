# Security Configuration Structure

## Directory Organization

```
etc/security/
├── command-permissions.json    # Command execution permissions
├── execution-policy.yaml       # Comprehensive security policies
├── README.md                   # Documentation
└── STRUCTURE.md               # This file
```

## Purpose

The `etc/security/` directory centralizes all security-related configurations for the time-shift-proxmox project.

## Files

### command-permissions.json
- **Purpose**: Define which commands can be executed, with what restrictions
- **Format**: JSON for performance and strict parsing
- **Used by**: 
  - `scripts/safe-commands-enhanced.sh` (new)
  - Can be integrated into `master.py` and other Python scripts
  - Future integration with `scripts/safe-commands.sh`

### execution-policy.yaml
- **Purpose**: Broader security policies beyond command execution
- **Format**: YAML for readability and complex configurations
- **Covers**:
  - Authentication policies
  - Network security settings
  - File system restrictions
  - Process execution limits
  - Logging and auditing
  - Secrets management
  - Compliance standards

### README.md
- **Purpose**: Comprehensive documentation
- **Includes**:
  - File descriptions
  - Usage examples
  - Integration instructions
  - Security best practices

## Why JSON for command-permissions.json?

1. **Performance**: Faster parsing than YAML
2. **Security**: Stricter syntax prevents injection
3. **Compatibility**: Native Python support without dependencies
4. **Validation**: Easier to validate structure

## Why YAML for execution-policy.yaml?

1. **Readability**: More human-friendly for complex policies
2. **Comments**: Supports inline documentation
3. **Structure**: Better for nested configurations
4. **Standards**: Common for policy files (Kubernetes, Docker, etc.)

## Integration

Scripts should reference the security configurations as:
```bash
PERMISSIONS_FILE="etc/security/command-permissions.json"
POLICY_FILE="etc/security/execution-policy.yaml"
```

No symlinks are used - files exist in their canonical location.
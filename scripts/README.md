# Scripts Directory

This directory contains utility scripts for the time-shift-proxmox project.

## Command Permissions

The `command-permissions.json` file has been moved to `etc/security/` for better organization.

**Location**: `../etc/security/command-permissions.json`

## Scripts

### safe-commands.sh
- Original safe commands wrapper
- Uses hardcoded command list (doesn't use JSON file yet)
- Simple switch/case implementation

### safe-commands-enhanced.sh
- Enhanced version that uses `etc/security/command-permissions.json`
- Supports all features defined in the JSON configuration
- Provides auto-approval, confirmation prompts, and forbidden command blocking

### Other Scripts
- `consolidate-setup.sh` - Adds deprecation warnings to redundant setup scripts
- `proxmox_docker_vm_complete.sh` - Proxmox Docker VM setup
- `setup-vscode-mcp.sh` - VS Code MCP setup

## Usage

To use the enhanced safe commands wrapper:
```bash
./safe-commands-enhanced.sh git status
./safe-commands-enhanced.sh rm -f tempfile.txt  # Will require confirmation
./safe-commands-enhanced.sh sudo apt update     # Will be blocked (forbidden)
```

## Configuration

All command permissions are configured in:
`etc/security/command-permissions.json`

No duplicate files or symlinks are used.
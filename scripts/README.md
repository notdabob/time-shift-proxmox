# Scripts Directory

This directory contains utility scripts and tools for the Time-Shift Proxmox project.

## Script Categories

### Authentication Scripts (`auth/`)
Scripts for setting up GitHub authentication and repository access:
- `browser-auth.sh` - Browser-based GitHub authentication
- `pat-setup.sh` - Personal Access Token setup
- `token-file-setup.sh` - Token file management
- `setup-github-token.sh` - GitHub token configuration
- `setup-secure-token.sh` - Secure token storage
- `web-auth-setup.sh` - Web-based authentication
- `interactive-git-setup.sh` - Interactive Git configuration

### Utility Scripts
- `consolidate-setup.sh` - Setup consolidation utilities  
- `proxmox_docker_vm_complete.sh` - Complete Proxmox VM setup
- `safe-commands.sh` / `safe-commands-enhanced.sh` - Safe command execution
- `setup-vscode-mcp.sh` - VS Code MCP setup
- `generate_pdf.sh` - PDF generation utilities
- `scrub-api-keys.sh` - API key cleaning
- `easy-git-auth.sh` - Simplified Git authentication
- `git-clone-easy.sh` - Easy repository cloning

### Deprecated Scripts (`deprecated/`)
Legacy scripts that have been replaced by newer implementations:
- `instant-setup.sh` - Legacy instant setup
- `quick-setup.sh` - Legacy quick setup  
- `one-click-setup.sh` - Legacy one-click setup
- `fix-installation.sh` - Legacy installation fixes

## Command Security

### Safe Command Execution
- `safe-commands.sh` - Original safe commands wrapper with hardcoded command list
- `safe-commands-enhanced.sh` - Enhanced version using `etc/security/command-permissions.json`

Command permissions are configured in: `../etc/security/command-permissions.json`

Usage examples:
```bash
./safe-commands-enhanced.sh git status          # Auto-approved
./safe-commands-enhanced.sh rm -f tempfile.txt  # Requires confirmation  
./safe-commands-enhanced.sh sudo apt update     # Blocked (forbidden)
```

## Usage Recommendations

### For New Installations
Use the main `setup.sh` script in the project root for the most up-to-date installation process.

### For Authentication Issues
1. Try `auth/browser-auth.sh` for browser-based setup
2. Use `auth/pat-setup.sh` for Personal Access Token setup
3. Use `auth/interactive-git-setup.sh` for guided configuration

### For Development
Use `setup-vscode-mcp.sh` to configure VS Code with Model Context Protocol support.

## Script Maintenance

When adding new scripts:
1. Place them in the appropriate category subdirectory
2. Update this README
3. Ensure scripts are executable (`chmod +x`)
4. Follow the project's coding standards
5. Add error handling and user-friendly output
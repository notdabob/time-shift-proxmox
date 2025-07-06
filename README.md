# Time-Shift Proxmox VM Solution

A Debian-based VM template for Proxmox that can temporarily shift system time to access iDRAC interfaces with expired SSL certificates.

## 🚀 Quick Start - One Command Setup

### Easiest: Browser-Based Authentication (Recommended)

```bash
# This opens your browser for GitHub login - no token copying needed!
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/browser-auth.sh && chmod +x browser-auth.sh && ./browser-auth.sh
```

### For Private Repository (with GitHub Token) - No Password Prompts!

```bash
# Option 1: Save token and auto-configure git (easiest)
echo 'ghp_YourActualToken' > ~/.time-shift-proxmox-token && chmod 600 ~/.time-shift-proxmox-token
git config --global credential.helper store
echo "https://notdabob:$(cat ~/.time-shift-proxmox-token)@github.com" > ~/.git-credentials
git clone https://github.com/notdabob/time-shift-proxmox.git && cd time-shift-proxmox && sudo ./setup.sh

# Option 2: One-liner with token parameter
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/git-clone-easy.sh
chmod +x git-clone-easy.sh && ./git-clone-easy.sh ghp_YourActualToken
```

### Alternative: Pass Token Directly

```bash
# One-liner with token (replace YOUR_TOKEN)
sudo GITHUB_TOKEN=YOUR_TOKEN bash -c "$(curl -fsSL https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/quick-setup.sh)"
```

This single command will:

- Clone the repository
- Install all dependencies
- Configure Dell iDRAC defaults (root/calvin)
- Set up the VM environment
- Make all scripts executable
- Run initial configuration wizard

## Project Goal

Create a specialized VM solution that can:

- Temporarily modify system time to access systems with expired SSL certificates
- Specifically target Dell iDRAC interfaces that often have expired certificates
- Provide automated time restoration after operations
- Integrate with Proxmox VE for easy deployment and management

## Features

- **Time Manipulation**: Safely shift system time to bypass expired SSL certificate issues
- **Proxmox Integration**: Full API integration for VM management
- **Network Validation**: Comprehensive connectivity and certificate validation tools
- **Configuration Wizard**: Interactive setup for easy deployment
- **Logging**: Detailed operation logging for troubleshooting
- **Backup/Restore**: Automatic backup and restoration of original time settings

## Manual Installation

If you prefer to install manually:

```bash
# Clone and setup in one command
git clone https://github.com/notdabob/time-shift-proxmox.git && \
cd time-shift-proxmox && \
chmod +x bin/*.py && \
./bin/setup-project-requirements.py && \
./bin/vm-config-wizard.py
```

## Usage

After installation, everything is ready to use:

- **Access iDRAC with expired certificates**:

  ```bash
  ./time-shift-idrac.sh <idrac-ip>
  ```

- **Advanced Time-Shift CLI**: `./bin/time-shift-cli.py`
- **Reconfigure**: `./bin/vm-config-wizard.py`

## Configuration

The main configuration file for the VM solution is located at `etc/time-shift-config.json`.
Project-specific configurations are in `etc/project_config.json`.

## Requirements

- Python 3.8+
- Proxmox VE 7.0+
- Debian 11+ (for VM template)
- Root access for time manipulation
- Network connectivity to target iDRAC interfaces

## Security Considerations

- This tool requires root privileges to modify system time.
- SSL verification is disabled when connecting to systems with expired certificates.
- Default iDRAC credentials (root/calvin) are Dell's factory standards and are automatically configured.
- Passwords in configuration files should be properly secured.
- Time manipulation affects the entire system - use with caution.
- Always test in isolated environments first.

### Dell iDRAC Default Credentials
The project uses Dell's standard factory default credentials:
- Username: `root`
- Password: `calvin`

These are the universal defaults for all Dell iDRAC interfaces and are automatically configured in the system.

## Documentation

- [`docs/PERPLEXITY_CONVERSATION.md`](docs/PERPLEXITY_CONVERSATION.md) - Original conversation source
- [`GEMINI.md`](GEMINI.md) - Gemini AI integration details
- [`.env`](.env) - Environment variables template
- [`requirements.txt`](requirements.txt) - Python dependencies

## License

This project is provided as-is for educational and operational purposes. Use responsibly and in accordance with your organization's security policies.

## Contributing

Contributions are welcome! Please ensure all changes include appropriate tests and documentation updates.

## Support

For issues and questions, please review the troubleshooting section and check the log files for detailed error information.

## One-Click Tools Summary

- **Quick Setup**: `curl -sSL https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/setup.sh | bash`
- **Access iDRAC**: `./time-shift-idrac.sh <idrac-ip>`
- **Manual Setup**: `git clone ... && cd ... && ./setup.sh`

All operations are designed to be single-command executions with no additional configuration required.

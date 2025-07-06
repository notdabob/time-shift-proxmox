# Time-Shift Proxmox VM Solution

A Debian-based VM template for Proxmox that can temporarily shift system time to access iDRAC interfaces with expired SSL certificates.

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

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/notdabob/time-shift-proxmox.git
   cd time-shift-proxmox
   ```

2. Setup project requirements and make scripts executable:

   ```bash
   chmod +x bin/*.py && ./bin/setup-project-requirements.py
   ```

## Usage

After installation, you can use the following scripts:

- **Configuration Wizard**: `./bin/vm-config-wizard.py`
- **Time-Shift CLI**: `./bin/time-shift-cli.py`

Refer to the respective script's `--help` for usage details.

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

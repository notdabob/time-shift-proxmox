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

1. Clone this repository to your Proxmox host or management system
2. Install required Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the configuration wizard:

   ```bash
   ./bin/vm-config-wizard
   ```

4. Make the CLI executable:

   ```bash
   chmod +x bin/time-shift-cli
   ```

## Usage

### Basic Time Shift Operation

```bash
./bin/time-shift-cli --target-date 2020-01-01 --idrac-ip 192.168.1.100
```

### Restore Original Time

```bash
./bin/time-shift-cli --action restore
```

### Validate iDRAC Connectivity

```bash
./bin/time-shift-cli --action validate --idrac-ip 192.168.1.100
```

### Using Custom Configuration

```bash
./bin/time-shift-cli --config /path/to/custom-config.json --action shift --target-date 2019-06-15
```

## Configuration

The main configuration file is located at `etc/time-shift-config.json`. Key sections include:

- **Proxmox**: Connection details for Proxmox VE API
- **VM**: Virtual machine specifications and settings
- **Network**: Network configuration for the VM
- **Time**: Timezone and NTP server settings
- **iDRAC**: Default credentials and connection parameters
- **Logging**: Log file locations and verbosity levels

## File Structure

```text
time-shift-proxmox/
├── bin/
│   ├── time-shift-cli           # Main CLI interface
│   └── vm-config-wizard         # Initial setup wizard
├── etc/
│   └── time-shift-config.json   # Primary configuration
├── lib/
│   ├── proxmox_api.py          # Proxmox API interactions
│   ├── time_ops.py             # Time manipulation functions
│   └── network_tools.py        # Network validation
├── var/
│   └── logs/                   # Log directory
└── usr/local/share/time-shift/ # Desktop shortcuts/bookmarks
```

## Requirements

- Python 3.8+
- Proxmox VE 7.0+
- Debian 11+ (for VM template)
- Root access for time manipulation
- Network connectivity to target iDRAC interfaces

## Python Dependencies

- `requests` - HTTP client for API calls
- `urllib3` - HTTP library with SSL handling
- Standard library modules: `json`, `datetime`, `subprocess`, `socket`, `ssl`

## Security Considerations

- This tool requires root privileges to modify system time
- SSL verification is disabled when connecting to systems with expired certificates
- Passwords in configuration files should be properly secured
- Time manipulation affects the entire system - use with caution
- Always test in isolated environments first

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the script has root privileges for time operations
2. **Network Connectivity**: Verify network access to target iDRAC interfaces
3. **Proxmox API Errors**: Check Proxmox credentials and API accessibility
4. **Time Restoration Failed**: Manual restoration may be required - check logs

### Log Files

- Main log: `/var/logs/time-shift.log`
- Detailed error information available with `--verbose` flag

## Examples

### Complete Workflow

```bash
# 1. Configure the system
./bin/vm-config-wizard

# 2. Shift time to access expired iDRAC certificate
./bin/time-shift-cli --target-date 2020-01-01 --idrac-ip 192.168.1.100

# 3. Access iDRAC interface (certificate now appears valid)
# ... perform required iDRAC operations ...

# 4. Restore original time
./bin/time-shift-cli --action restore
```

### Batch Operations

```bash
# Validate multiple iDRAC interfaces
for ip in 192.168.1.100 192.168.1.101 192.168.1.102; do
    ./bin/time-shift-cli --action validate --idrac-ip $ip
done
```

## Development Guidelines

### API Key Management

When adding new API keys to `.env` files, always include SonarQube disable comments:

```bash
# Service Name API Key
# sonar-disable-next-line
API_KEY_NAME=your_api_key_here
```

This prevents security warnings while maintaining proper secret management practices.

## License

This project is provided as-is for educational and operational purposes. Use responsibly and in accordance with your organization's security policies.

## Contributing

Contributions are welcome! Please ensure all changes include appropriate tests and documentation updates.

## Support

For issues and questions, please review the troubleshooting section and check the log files for detailed error information.

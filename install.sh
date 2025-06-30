#!/bin/bash
"""
Time-Shift VM Installation Script
Automates the installation and setup of the Time-Shift VM solution
"""

# Time-Shift Proxmox VM Solution - Installation Script

echo "=================================="
echo "Time-Shift VM Solution Installer"
echo "=================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Check Python version
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo "Making scripts executable..."
chmod +x bin/time-shift-cli
chmod +x bin/vm-config-wizard

echo "Creating log directory..."
mkdir -p var/logs
chown $(logname):$(logname) var/logs 2>/dev/null || chown $USER:$USER var/logs

echo "Setting up desktop shortcuts..."
mkdir -p usr/local/share/time-shift

# Create desktop shortcut
cat > usr/local/share/time-shift/time-shift.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Time-Shift VM
Comment=Access iDRAC with expired certificates
Exec=$(pwd)/bin/time-shift-cli.py
Icon=utilities-terminal
Terminal=true
Categories=System;
EOF

echo "Installation complete!"
echo
echo "Next steps:"
echo "1. Run the configuration wizard: ./bin/vm-config-wizard.py"
echo "2. Edit etc/time-shift-config.json as needed"
echo "3. Test with: ./bin/time-shift-cli.py --action validate --idrac-ip <your-idrac-ip>"
echo
echo "For help: ./bin/time-shift-cli.py --help"

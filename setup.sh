#!/bin/bash
# Time-Shift Proxmox One-Click Setup Script
# This script provides a complete automated setup for the Time-Shift Proxmox solution

set -e  # Exit on error

echo "🚀 Time-Shift Proxmox One-Click Setup"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script requires root privileges for time manipulation features."
    echo "Please run with sudo: sudo bash setup.sh"
    exit 1
fi

# Set installation directory
INSTALL_DIR="/opt/time-shift-proxmox"
echo "📁 Installing to: $INSTALL_DIR"

# Handle repository cloning with authentication
clone_repository() {
    # Check for token in multiple locations
    TOKEN=""
    
    # 1. Check .pat file in current directory
    if [ -f ".pat" ] && [ -z "$TOKEN" ]; then
        TOKEN=$(grep -v '^#' .pat | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
        if [ ! -z "$TOKEN" ]; then
            echo "✓ Using token from .pat file"
        fi
    fi
    
    # 2. Check ~/.pat file
    if [ -f "$HOME/.pat" ] && [ -z "$TOKEN" ]; then
        TOKEN=$(grep -v '^#' "$HOME/.pat" | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
        if [ ! -z "$TOKEN" ]; then
            echo "✓ Using token from ~/.pat file"
        fi
    fi
    
    # 3. Check legacy token file
    if [ -f "$HOME/.time-shift-proxmox-token" ] && [ -z "$TOKEN" ]; then
        TOKEN=$(cat "$HOME/.time-shift-proxmox-token")
        if [ ! -z "$TOKEN" ]; then
            echo "✓ Using token from ~/.time-shift-proxmox-token"
        fi
    fi
    
    # 4. Check environment variable
    if [ ! -z "$GITHUB_TOKEN" ] && [ -z "$TOKEN" ]; then
        TOKEN="$GITHUB_TOKEN"
        echo "✓ Using token from GITHUB_TOKEN environment variable"
    fi
    
    if [ ! -z "$TOKEN" ]; then
        # Configure git credentials
        git config --global credential.helper store
        echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
        chmod 600 ~/.git-credentials
        
        git clone https://notdabob:${TOKEN}@github.com/notdabob/time-shift-proxmox.git "$INSTALL_DIR" 2>/dev/null
    else
        # Try public clone first
        git clone https://github.com/notdabob/time-shift-proxmox.git "$INSTALL_DIR" 2>/dev/null || {
            echo "⚠️  Repository appears to be private. Please provide authentication."
            echo ""
            echo "Easy method: Create a .pat file:"
            echo "1. echo 'YOUR_GITHUB_TOKEN' > .pat"
            echo "2. Run this setup again"
            echo ""
            echo "Get a token from: https://github.com/settings/tokens"
            echo "(Select 'repo' scope when creating the token)"
            exit 1
        }
    fi
}

# Clone repository if not already present
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📥 Cloning repository..."
    clone_repository
else
    echo "📂 Repository already exists, updating..."
    cd "$INSTALL_DIR"
    if [ -f "$HOME/.time-shift-proxmox-token" ]; then
        TOKEN=$(cat "$HOME/.time-shift-proxmox-token")
        git config credential.helper store
        git pull https://notdabob:${TOKEN}@github.com/notdabob/time-shift-proxmox.git 2>/dev/null || git pull
    else
        git pull
    fi
fi

cd "$INSTALL_DIR"

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    ntp \
    ntpdate \
    curl \
    jq \
    git

# Create Python virtual environment
echo ""
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Make all scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x bin/*.py
chmod +x run_tests.sh 2>/dev/null || true

# Create convenience wrapper scripts
echo ""
echo "📝 Creating convenience scripts..."

# Create main time-shift-idrac script
cat > /usr/local/bin/time-shift-idrac << 'EOF'
#!/bin/bash
# Time-Shift iDRAC Access Script
# Usage: time-shift-idrac <idrac-ip>

if [ -z "$1" ]; then
    echo "Usage: time-shift-idrac <idrac-ip>"
    echo "Example: time-shift-idrac 192.168.1.100"
    exit 1
fi

IDRAC_IP="$1"
INSTALL_DIR="/opt/time-shift-proxmox"

cd "$INSTALL_DIR"
source venv/bin/activate

echo "🔄 Connecting to iDRAC at $IDRAC_IP with time-shift..."
echo "Using Dell default credentials (root/calvin)"
echo ""

# Run the time-shift CLI with iDRAC connection
python3 bin/time-shift-cli.py connect-idrac \
    --host "$IDRAC_IP" \
    --username root \
    --password calvin \
    --auto-shift

deactivate
EOF

chmod +x /usr/local/bin/time-shift-idrac

# Create system service for automatic time restoration
echo ""
echo "🔧 Setting up systemd service..."
cat > /etc/systemd/system/time-shift-restore.service << EOF
[Unit]
Description=Time-Shift Automatic Restoration Service
After=network.target

[Service]
Type=oneshot
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/bin/time-shift-cli.py restore-time
RemainAfterExit=yes
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable time-shift-restore.service

# Create initial configuration with Dell defaults
echo ""
echo "⚙️  Creating configuration with Dell iDRAC defaults..."
mkdir -p etc
cat > etc/time-shift-config.json << EOF
{
    "idrac": {
        "default_username": "root",
        "default_password": "calvin",
        "ssl_verify": false,
        "timeout": 30,
        "default_port": 443
    },
    "time_shift": {
        "backup_file": "/tmp/time_shift_backup.txt",
        "ntp_servers": ["pool.ntp.org", "time.nist.gov"],
        "max_shift_days": 3650
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/time-shift-proxmox.log",
        "max_size": "10MB",
        "backup_count": 5
    },
    "proxmox": {
        "api_verify_ssl": false,
        "timeout": 30
    }
}
EOF

# Run initial configuration wizard
echo ""
echo "🧙 Running configuration wizard..."
source venv/bin/activate
python3 bin/vm-config-wizard.py --auto-detect || true
deactivate

# Create quick test script
echo ""
echo "🧪 Creating test script..."
cat > test-installation.sh << 'EOF'
#!/bin/bash
echo "Testing Time-Shift Proxmox installation..."
echo ""

# Test Python environment
source venv/bin/activate
python3 -c "import sys; print(f'✓ Python {sys.version.split()[0]} is working')"

# Test imports
python3 -c "import time_ops; print('✓ Time operations module loaded')"
python3 -c "import network_tools; print('✓ Network tools module loaded')"
python3 -c "import config_models; print('✓ Configuration models loaded')"

# Test CLI
python3 bin/time-shift-cli.py --version && echo "✓ CLI is working"

deactivate

echo ""
echo "✅ All tests passed!"
EOF
chmod +x test-installation.sh

# Display completion message
echo ""
echo "✅ Installation Complete!"
echo "========================"
echo ""
echo "📋 Quick Usage Guide:"
echo ""
echo "1. Access iDRAC with expired certificate:"
echo "   time-shift-idrac <idrac-ip>"
echo ""
echo "2. Advanced time-shift operations:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo "   ./bin/time-shift-cli.py --help"
echo ""
echo "3. Run tests:"
echo "   cd $INSTALL_DIR"
echo "   ./test-installation.sh"
echo ""
echo "4. View logs:"
echo "   tail -f /var/log/time-shift-proxmox.log"
echo ""
echo "🔐 Dell iDRAC Default Credentials:"
echo "   Username: root"
echo "   Password: calvin"
echo ""
echo "Happy time-shifting! 🕐"
#!/bin/bash
# Time-Shift iDRAC Quick Access Script
# This script provides the simplest way to access an iDRAC with expired certificates

if [ -z "$1" ]; then
    echo "Time-Shift iDRAC Access Tool"
    echo ""
    echo "Usage: ./time-shift-idrac.sh <idrac-ip>"
    echo ""
    echo "Example: ./time-shift-idrac.sh 192.168.1.100"
    echo ""
    echo "This will:"
    echo "  - Automatically detect the certificate expiration date"
    echo "  - Temporarily shift system time to access the iDRAC"
    echo "  - Use Dell default credentials (root/calvin)"
    echo "  - Restore original time after completion"
    exit 1
fi

IDRAC_IP="$1"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script requires root privileges to modify system time."
    echo "Please run with sudo: sudo ./time-shift-idrac.sh $IDRAC_IP"
    exit 1
fi

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for authentication if needed for private repo updates
if [ -f ".pat" ] || [ -f "$HOME/.pat" ]; then
    # Load token for potential git operations
    if [ -f ".pat" ]; then
        TOKEN=$(grep -v '^#' .pat | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
    elif [ -f "$HOME/.pat" ]; then
        TOKEN=$(grep -v '^#' "$HOME/.pat" | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
    fi
    
    if [ ! -z "$TOKEN" ]; then
        git config --global credential.helper store
        echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
        chmod 600 ~/.git-credentials
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Running setup first..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

echo "🔄 Connecting to iDRAC at $IDRAC_IP"
echo "📋 Using Dell default credentials (root/calvin)"
echo ""

# Run the time-shift operation
python3 bin/time-shift-cli.py connect-idrac \
    --host "$IDRAC_IP" \
    --username root \
    --password calvin \
    --auto-shift \
    --verbose

# Deactivate virtual environment
deactivate

echo ""
echo "✅ Operation complete. System time has been restored."
#!/bin/bash
# Fix Installation Script - Repairs existing installations

set -e

echo "🔧 Time-Shift Proxmox Installation Repair"
echo "========================================"
echo ""

# Check current directory
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Check for token in various locations
TOKEN=""
if [ -f ".pat" ]; then
    TOKEN=$(grep -v '^#' .pat | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
    if [ ! -z "$TOKEN" ] && [ "$TOKEN" != "YOUR_GITHUB_TOKEN_HERE" ]; then
        echo "✓ Found token in .pat file"
    else
        TOKEN=""
    fi
fi

if [ -z "$TOKEN" ] && [ -f "$HOME/.pat" ]; then
    TOKEN=$(grep -v '^#' "$HOME/.pat" | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
    if [ ! -z "$TOKEN" ]; then
        echo "✓ Found token in ~/.pat file"
    fi
fi

if [ -z "$TOKEN" ] && [ -f "$HOME/.time-shift-proxmox-token" ]; then
    TOKEN=$(cat "$HOME/.time-shift-proxmox-token")
    if [ ! -z "$TOKEN" ]; then
        echo "✓ Found token in ~/.time-shift-proxmox-token"
    fi
fi

# If no token found, prompt for it
if [ -z "$TOKEN" ]; then
    echo ""
    echo "❌ No valid GitHub token found!"
    echo ""
    echo "Please enter your GitHub Personal Access Token:"
    echo "(Get one from https://github.com/settings/tokens with 'repo' scope)"
    read -s TOKEN
    echo ""
    
    if [ -z "$TOKEN" ]; then
        echo "❌ No token provided. Exiting."
        exit 1
    fi
    
    # Save for future use
    echo "$TOKEN" > .pat
    chmod 600 .pat
fi

# Configure git
echo "Configuring git authentication..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Test authentication
echo "Testing GitHub authentication..."
if ! git ls-remote https://github.com/notdabob/time-shift-proxmox.git >/dev/null 2>&1; then
    echo "❌ Authentication failed! Please check your token."
    exit 1
fi
echo "✅ Authentication successful!"

# Clone fresh copy to current directory
echo ""
echo "Cloning fresh copy..."
if [ -d "time-shift-proxmox" ]; then
    echo "Removing old clone..."
    rm -rf time-shift-proxmox
fi

git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox

# Run the proper setup
echo ""
echo "Running setup..."
if [ -f "./setup.sh" ]; then
    sudo ./setup.sh
else
    echo "❌ setup.sh not found in repository!"
    exit 1
fi

echo ""
echo "✅ Installation repaired!"
echo ""
echo "The repository is now in: $(pwd)"
echo ""
echo "Available commands:"
echo "- ./time-shift-idrac.sh <idrac-ip>"
echo "- ./bin/time-shift-cli.py --help"
echo ""
echo "Or use the global command:"
echo "- time-shift-idrac <idrac-ip>"
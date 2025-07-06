#!/bin/bash
# Ultra-simple setup script for Time-Shift Proxmox
# This handles everything including GitHub authentication

set -e

echo "🚀 Time-Shift Proxmox Quick Setup"
echo "================================="
echo ""

# Function to setup with token
setup_with_token() {
    local token=$1
    local temp_dir="/tmp/time-shift-setup-$$"
    
    # Create temp directory
    mkdir -p "$temp_dir"
    cd "$temp_dir"
    
    # Clone using token directly in URL
    echo "📥 Downloading Time-Shift Proxmox..."
    git clone https://notdabob:${token}@github.com/notdabob/time-shift-proxmox.git 2>/dev/null || {
        echo "❌ Failed to clone repository. Please check your token."
        rm -rf "$temp_dir"
        exit 1
    }
    
    # Move to permanent location
    if [ -d "/opt/time-shift-proxmox" ]; then
        echo "📂 Updating existing installation..."
        rm -rf /opt/time-shift-proxmox.bak
        mv /opt/time-shift-proxmox /opt/time-shift-proxmox.bak
    fi
    
    mv time-shift-proxmox /opt/time-shift-proxmox
    cd /opt/time-shift-proxmox
    
    # Save token for future use
    echo "$token" > "$HOME/.time-shift-proxmox-token"
    chmod 600 "$HOME/.time-shift-proxmox-token"
    
    # Run setup
    echo "🔧 Running setup..."
    if [ -f "./setup.sh" ]; then
        ./setup.sh
    else
        echo "❌ setup.sh not found!"
        exit 1
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs root privileges."
    echo "Please run: sudo $0"
    exit 1
fi

# Check for token in environment or file
if [ ! -z "$GITHUB_TOKEN" ]; then
    echo "✓ Using token from GITHUB_TOKEN environment variable"
    setup_with_token "$GITHUB_TOKEN"
elif [ ! -z "$1" ]; then
    echo "✓ Using token from command line"
    setup_with_token "$1"
elif [ -f "$HOME/.time-shift-proxmox-token" ]; then
    echo "✓ Using saved token"
    TOKEN=$(cat "$HOME/.time-shift-proxmox-token")
    setup_with_token "$TOKEN"
else
    echo "❌ No GitHub token found!"
    echo ""
    echo "Please provide your GitHub Personal Access Token using one of these methods:"
    echo ""
    echo "Method 1 - Command line:"
    echo "  sudo $0 YOUR_GITHUB_TOKEN"
    echo ""
    echo "Method 2 - Environment variable:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  sudo -E $0"
    echo ""
    echo "Method 3 - Save to file:"
    echo "  echo 'your_token_here' > ~/.time-shift-proxmox-token"
    echo "  chmod 600 ~/.time-shift-proxmox-token"
    echo "  sudo $0"
    echo ""
    echo "To create a token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Generate new token (classic) with 'repo' scope"
    echo "3. Copy the token and use one of the methods above"
    exit 1
fi

echo ""
echo "✅ All done! You can now use:"
echo "   time-shift-idrac <idrac-ip>"
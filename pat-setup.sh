#!/bin/bash
# PAT File Setup - The simplest way to authenticate
# Just put your token in a .pat file and run this script

set -e

echo "🔐 PAT File Authentication Setup"
echo "================================"
echo ""

# Function to find and validate PAT
find_pat_token() {
    local token=""
    
    # Check .pat in current directory
    if [ -f ".pat" ]; then
        token=$(grep -v '^#' .pat | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
        if [ ! -z "$token" ]; then
            echo "✓ Found token in .pat file"
            echo "$token"
            return 0
        fi
    fi
    
    # Check ~/.pat
    if [ -f "$HOME/.pat" ]; then
        token=$(grep -v '^#' "$HOME/.pat" | grep -v '^YOUR_GITHUB_TOKEN_HERE$' | head -n1)
        if [ ! -z "$token" ]; then
            echo "✓ Found token in ~/.pat file"
            echo "$token"
            return 0
        fi
    fi
    
    return 1
}

# Check if .pat file exists
if ! find_pat_token > /dev/null 2>&1; then
    echo "📝 Creating .pat file template..."
    cat > .pat << 'EOF'
# GitHub Personal Access Token
# Replace the line below with your actual token
YOUR_GITHUB_TOKEN_HERE
EOF
    
    echo ""
    echo "⚠️  Please edit the .pat file and add your GitHub token:"
    echo ""
    echo "1. Get a token from: https://github.com/settings/tokens"
    echo "   - Click 'Generate new token (classic)'"
    echo "   - Name: 'time-shift-proxmox'"
    echo "   - Scope: ✓ repo"
    echo "   - Generate and copy the token"
    echo ""
    echo "2. Edit .pat file and replace YOUR_GITHUB_TOKEN_HERE with your token"
    echo "   nano .pat"
    echo "   OR"
    echo "   echo 'ghp_YourActualTokenHere' > .pat"
    echo ""
    echo "3. Run this script again: ./pat-setup.sh"
    exit 0
fi

# Get the token
TOKEN=$(find_pat_token | tail -n1)

# Configure git
echo ""
echo "📋 Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Also save to standard location for other scripts
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token

# Clone repository
echo ""
echo "📥 Cloning repository..."
if [ -d "time-shift-proxmox" ]; then
    cd time-shift-proxmox
    git pull
else
    git clone https://github.com/notdabob/time-shift-proxmox.git
    cd time-shift-proxmox
fi

# Copy .pat file to installation directory
if [ -f "../.pat" ]; then
    cp ../.pat .
fi

# Run setup
echo ""
echo "🚀 Running setup..."
if [ -f "./setup.sh" ]; then
    sudo ./setup.sh
else
    echo "❌ setup.sh not found!"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your token is saved in multiple locations for convenience:"
echo "- .pat (for easy editing)"
echo "- ~/.time-shift-proxmox-token"
echo "- ~/.git-credentials (for git)"
echo ""
echo "You can now use: time-shift-idrac <idrac-ip>"
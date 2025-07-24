#!/bin/bash
# Instant Setup Script - Works with private repos
# This script can be copy-pasted directly into terminal

cat << 'SCRIPT' > /tmp/time-shift-setup.sh
#!/bin/bash
set -e

echo "🚀 Time-Shift Proxmox Instant Setup"
echo "==================================="
echo ""

# Function to setup GitHub authentication
setup_github_auth() {
    echo "📋 GitHub Authentication Required"
    echo ""
    echo "This is a private repository. You need a GitHub Personal Access Token."
    echo ""
    echo "Steps:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Name: 'time-shift-proxmox'"
    echo "4. Select scope: [✓] repo"
    echo "5. Click 'Generate token'"
    echo "6. Copy the token (starts with ghp_)"
    echo ""
    
    # Get token
    echo "Paste your token here (or press Ctrl+C to cancel):"
    read -s TOKEN
    echo ""
    
    if [ -z "$TOKEN" ]; then
        echo "❌ No token provided"
        exit 1
    fi
    
    # Save token
    echo "$TOKEN" > ~/.time-shift-proxmox-token
    chmod 600 ~/.time-shift-proxmox-token
    
    # Configure git
    git config --global credential.helper store
    echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    
    echo "✅ Authentication configured"
}

# Check for existing token
if [ -f ~/.time-shift-proxmox-token ]; then
    echo "✅ Found existing token"
    TOKEN=$(cat ~/.time-shift-proxmox-token)
else
    setup_github_auth
    TOKEN=$(cat ~/.time-shift-proxmox-token)
fi

# Clone repository
echo ""
echo "📥 Cloning repository..."
if [ -d "time-shift-proxmox" ]; then
    cd time-shift-proxmox
    git pull
else
    git clone https://notdabob:${TOKEN}@github.com/notdabob/time-shift-proxmox.git
    cd time-shift-proxmox
fi

# Make scripts executable
chmod +x *.sh 2>/dev/null || true
chmod +x bin/*.py 2>/dev/null || true

# Run setup
echo ""
echo "🔧 Running setup..."
if [ -f "./setup.sh" ]; then
    sudo bash ./setup.sh
else
    echo "❌ setup.sh not found. Running basic setup..."
    
    # Basic setup if setup.sh is missing
    echo "Installing dependencies..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv git
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    echo "✅ Basic setup complete"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. cd time-shift-proxmox"
echo "2. ./time-shift-idrac.sh <idrac-ip>"
SCRIPT

chmod +x /tmp/time-shift-setup.sh
/tmp/time-shift-setup.sh
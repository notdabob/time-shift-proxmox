#!/bin/bash
# Interactive Git Authentication Setup
# This script prompts for your PAT token and configures everything

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}GitHub PAT Authentication Setup${NC}"
echo "==============================="
echo ""
echo "This script will help you set up GitHub authentication"
echo "for the time-shift-proxmox private repository."
echo ""

# Check if already configured
if [ -f ~/.git-credentials ] && grep -q "github.com" ~/.git-credentials 2>/dev/null; then
    echo -e "${YELLOW}Git credentials already configured.${NC}"
    read -p "Reconfigure? (y/n): " reconfigure
    if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
        echo "Using existing credentials."
        TOKEN=$(grep github.com ~/.git-credentials | sed 's/https:\/\/notdabob://' | sed 's/@github.com//')
    fi
fi

# Get token if not already set
if [ -z "$TOKEN" ]; then
    echo -e "${BLUE}Steps to get your GitHub token:${NC}"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Name: 'time-shift-proxmox'"
    echo "4. Select scope: [✓] repo"
    echo "5. Click 'Generate token' and copy it"
    echo ""
    echo "Please paste your GitHub Personal Access Token:"
    echo "(It will be hidden as you type/paste)"
    read -s TOKEN
    echo ""
fi

# Validate token format
if [[ ! "$TOKEN" =~ ^ghp_ ]] && [ ${#TOKEN} -lt 40 ]; then
    echo -e "${YELLOW}Warning: Token doesn't look like a GitHub PAT token.${NC}"
    echo "GitHub tokens usually start with 'ghp_' and are 40+ characters."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Configure git
echo "Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Also save to other common locations
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token

# Create .pat file in home directory
echo "$TOKEN" > ~/.pat
chmod 600 ~/.pat

echo -e "${GREEN}✅ Credentials configured successfully!${NC}"
echo ""

# Clone or update repository
if [ -d "time-shift-proxmox" ]; then
    echo "Repository already exists. Updating..."
    cd time-shift-proxmox
    git pull
else
    echo "Cloning repository..."
    if git clone https://github.com/notdabob/time-shift-proxmox.git; then
        cd time-shift-proxmox
        echo -e "${GREEN}✅ Repository cloned successfully!${NC}"
    else
        echo "❌ Failed to clone repository. Please check your token."
        exit 1
    fi
fi

# Run setup
echo ""
echo "Running Time-Shift Proxmox setup..."
if [ -f "./setup.sh" ]; then
    sudo ./setup.sh
else
    echo "❌ setup.sh not found!"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All done!${NC}"
echo ""
echo "Your token is saved in multiple locations:"
echo "- ~/.git-credentials (for git)"
echo "- ~/.time-shift-proxmox-token"
echo "- ~/.pat"
echo ""
echo "You can now use: time-shift-idrac <idrac-ip>"
#!/bin/bash
# GitHub Token Configuration Script for Time-Shift Proxmox
# This script handles the personal access token setup automatically

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration file for storing token
TOKEN_FILE="$HOME/.time-shift-proxmox-token"
REPO_URL="https://github.com/notdabob/time-shift-proxmox.git"

echo -e "${GREEN}GitHub Token Setup for Time-Shift Proxmox${NC}"
echo "=========================================="
echo ""

# Function to validate token format
validate_token() {
    local token=$1
    # GitHub tokens are typically 40 characters or start with ghp_
    if [[ ${#token} -lt 40 ]] && [[ ! $token =~ ^ghp_ ]]; then
        return 1
    fi
    return 0
}

# Check if token already exists
if [ -f "$TOKEN_FILE" ]; then
    echo -e "${YELLOW}Found existing token configuration${NC}"
    read -p "Do you want to use the existing token? (y/n): " use_existing
    if [[ $use_existing =~ ^[Yy]$ ]]; then
        TOKEN=$(cat "$TOKEN_FILE")
    else
        rm -f "$TOKEN_FILE"
    fi
fi

# Get token if not already set
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}You need a GitHub Personal Access Token${NC}"
    echo ""
    echo "To create one:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Name it: 'time-shift-proxmox-access'"
    echo "4. Select scope: [✓] repo"
    echo "5. Click 'Generate token' and copy it"
    echo ""
    
    # Read token with better UX
    echo "Enter your GitHub Personal Access Token:"
    echo "(Tip: You can paste it here, it will be hidden)"
    read -s -p "Token: " TOKEN
    echo ""
    
    # Validate token
    if ! validate_token "$TOKEN"; then
        echo -e "${RED}Invalid token format. GitHub tokens should be at least 40 characters or start with 'ghp_'${NC}"
        exit 1
    fi
    
    # Save token securely
    echo "$TOKEN" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    echo -e "${GREEN}✓ Token saved securely${NC}"
fi

# Configure git to use the token
echo ""
echo "Configuring Git credentials..."

# Create a custom credential helper script
CRED_HELPER="$HOME/.time-shift-git-creds"
cat > "$CRED_HELPER" << 'EOF'
#!/bin/bash
# Custom credential helper for time-shift-proxmox

TOKEN_FILE="$HOME/.time-shift-proxmox-token"

if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
    echo "username=notdabob"
    echo "password=$TOKEN"
else
    exit 1
fi
EOF

chmod 700 "$CRED_HELPER"

# Configure git to use our helper for this repo
git config --global credential.https://github.com/notdabob/time-shift-proxmox.git.helper "!$CRED_HELPER"

# Clone the repository
echo ""
echo "Cloning repository..."
if [ -d "time-shift-proxmox" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd time-shift-proxmox
    git pull
else
    # Clone using the token
    git clone https://notdabob:${TOKEN}@github.com/notdabob/time-shift-proxmox.git
    cd time-shift-proxmox
fi

# Run the setup
echo ""
echo -e "${GREEN}Repository cloned successfully!${NC}"
echo "Running Time-Shift Proxmox setup..."
echo ""

if [ -f "./setup.sh" ]; then
    sudo ./setup.sh
else
    echo -e "${RED}Error: setup.sh not found in the repository${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Your GitHub token is saved in: $TOKEN_FILE"
echo "To remove stored credentials, run: rm $TOKEN_FILE $CRED_HELPER"
echo ""
echo "You can now use: ./time-shift-idrac.sh <idrac-ip>"
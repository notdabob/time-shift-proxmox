#!/bin/bash
# Easy Git Authentication Setup - No Password Prompts!
# This script sets up git credentials without any interactive prompts

set -e

echo "🔐 Easy Git Authentication Setup"
echo "================================"
echo ""

# Function to setup git credentials without prompts
setup_git_credentials() {
    local username=$1
    local token=$2
    
    # Configure git to use credential store
    git config --global credential.helper store
    
    # Pre-populate the credentials file
    echo "https://${username}:${token}@github.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    
    echo "✅ Git credentials configured successfully!"
}

# Check for token
if [ ! -z "$1" ] && [ ! -z "$2" ]; then
    # Username and token passed as arguments
    USERNAME="$1"
    TOKEN="$2"
elif [ ! -z "$GITHUB_USERNAME" ] && [ ! -z "$GITHUB_TOKEN" ]; then
    # From environment variables
    USERNAME="$GITHUB_USERNAME"
    TOKEN="$GITHUB_TOKEN"
elif [ -f "$HOME/.time-shift-proxmox-creds" ]; then
    # From credentials file (format: username:token)
    CREDS=$(cat "$HOME/.time-shift-proxmox-creds")
    USERNAME=$(echo "$CREDS" | cut -d':' -f1)
    TOKEN=$(echo "$CREDS" | cut -d':' -f2-)
else
    echo "Usage: $0 [username] [token]"
    echo ""
    echo "Or use one of these methods:"
    echo ""
    echo "1. Environment variables:"
    echo "   export GITHUB_USERNAME=notdabob"
    echo "   export GITHUB_TOKEN=ghp_YourTokenHere"
    echo "   ./easy-git-auth.sh"
    echo ""
    echo "2. Credentials file:"
    echo "   echo 'notdabob:ghp_YourTokenHere' > ~/.time-shift-proxmox-creds"
    echo "   chmod 600 ~/.time-shift-proxmox-creds"
    echo "   ./easy-git-auth.sh"
    echo ""
    echo "3. Direct parameters:"
    echo "   ./easy-git-auth.sh notdabob ghp_YourTokenHere"
    exit 1
fi

# Setup credentials
setup_git_credentials "$USERNAME" "$TOKEN"

# Test by cloning
echo ""
echo "🧪 Testing authentication..."
if git ls-remote https://github.com/notdabob/time-shift-proxmox.git >/dev/null 2>&1; then
    echo "✅ Authentication successful!"
    echo ""
    echo "You can now clone without any password prompts:"
    echo "git clone https://github.com/notdabob/time-shift-proxmox.git"
else
    echo "❌ Authentication failed. Please check your credentials."
    exit 1
fi
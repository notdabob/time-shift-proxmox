#!/bin/bash
# Ultra-simple git clone with credentials - no prompts!

# Default username
USERNAME="${GITHUB_USERNAME:-notdabob}"

# Get token from various sources
if [ ! -z "$1" ]; then
    TOKEN="$1"
elif [ ! -z "$GITHUB_TOKEN" ]; then
    TOKEN="$GITHUB_TOKEN"
elif [ -f "$HOME/.time-shift-proxmox-token" ]; then
    TOKEN=$(cat "$HOME/.time-shift-proxmox-token")
else
    echo "❌ No token found!"
    echo ""
    echo "Usage: $0 YOUR_GITHUB_TOKEN"
    echo ""
    echo "Or save your token:"
    echo "echo 'ghp_YourTokenHere' > ~/.time-shift-proxmox-token"
    exit 1
fi

# Setup git credentials automatically
git config --global credential.helper store
echo "https://${USERNAME}:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Clone the repository
echo "📥 Cloning time-shift-proxmox..."
git clone https://github.com/notdabob/time-shift-proxmox.git

# Run setup if successful
if [ -d "time-shift-proxmox" ]; then
    cd time-shift-proxmox
    echo "✅ Clone successful! Running setup..."
    sudo ./setup.sh
else
    echo "❌ Clone failed!"
    exit 1
fi
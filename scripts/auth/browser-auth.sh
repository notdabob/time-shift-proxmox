#!/bin/bash
# Browser-based GitHub Authentication using GitHub CLI
# This is the easiest method with full browser integration

set -e

echo "🌐 Browser-based GitHub Authentication"
echo "====================================="
echo ""

# Function to install GitHub CLI
install_github_cli() {
    echo "📦 Installing GitHub CLI..."
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        apt update -qq
        apt install -y gh
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        dnf install -y 'dnf-command(config-manager)'
        dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        dnf install -y gh
    else
        echo "❌ Unsupported OS for automatic GitHub CLI installation"
        echo "Please install GitHub CLI manually: https://cli.github.com"
        exit 1
    fi
}

# Check if gh is installed
if ! command -v gh > /dev/null; then
    echo "GitHub CLI not found."
    read -p "Install GitHub CLI? (y/n): " install_gh
    if [[ $install_gh =~ ^[Yy]$ ]]; then
        install_github_cli
    else
        echo "❌ GitHub CLI is required for browser authentication"
        exit 1
    fi
fi

# Authenticate with GitHub via browser
echo "🔐 Launching browser for GitHub authentication..."
echo ""

# Check if already authenticated
if gh auth status >/dev/null 2>&1; then
    echo "✅ Already authenticated with GitHub"
    read -p "Re-authenticate? (y/n): " reauth
    if [[ ! $reauth =~ ^[Yy]$ ]]; then
        TOKEN=$(gh auth token)
    else
        gh auth logout
        gh auth login --web --scopes repo
        TOKEN=$(gh auth token)
    fi
else
    # New authentication
    echo "This will open your browser to authenticate with GitHub."
    echo "After authentication, you'll be returned here automatically."
    echo ""
    read -p "Press Enter to continue..."
    
    gh auth login --web --scopes repo
    TOKEN=$(gh auth token)
fi

# Verify we got a token
if [ -z "$TOKEN" ]; then
    echo "❌ Failed to obtain authentication token"
    exit 1
fi

echo ""
echo "✅ Authentication successful!"

# Save token for other scripts
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token

# Configure git to use the token
echo ""
echo "📝 Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Clone the repository
echo ""
echo "📥 Cloning time-shift-proxmox repository..."
if [ -d "time-shift-proxmox" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd time-shift-proxmox
    git pull
else
    # Use gh to clone (it handles auth automatically)
    gh repo clone notdabob/time-shift-proxmox
    cd time-shift-proxmox
fi

# Run setup
echo ""
echo "🚀 Running Time-Shift Proxmox setup..."
if [ -f "./setup.sh" ]; then
    sudo ./setup.sh
else
    echo "❌ setup.sh not found!"
    exit 1
fi

echo ""
echo "✅ All done! You can now use:"
echo "   time-shift-idrac <idrac-ip>"
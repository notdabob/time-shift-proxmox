# GitHub Authentication Setup for Private Repository

## Method 1: Personal Access Token (Recommended)

### Step 1: Create a Personal Access Token on GitHub
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "time-shift-proxmox-access"
4. Select scopes:
   - `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 2: Configure Git to Use the Token

On your Proxmox host:

```bash
# Method A: Store credentials permanently (less secure but convenient)
git config --global credential.helper store
git clone https://github.com/notdabob/time-shift-proxmox.git
# When prompted:
# Username: notdabob
# Password: <paste-your-personal-access-token>

# Method B: Cache credentials temporarily (more secure)
git config --global credential.helper 'cache --timeout=3600'  # Cache for 1 hour
git clone https://github.com/notdabob/time-shift-proxmox.git
# Enter username and token as above
```

### Step 3: Clone Using Token in URL (One-liner)
```bash
# Replace YOUR_TOKEN with your actual token
git clone https://notdabob:YOUR_TOKEN@github.com/notdabob/time-shift-proxmox.git
```

## Method 2: SSH Key Authentication (Most Secure)

### Step 1: Generate SSH Key on Proxmox Host
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your-email@example.com"
# Press Enter to accept default location
# Optionally set a passphrase

# Display your public key
cat ~/.ssh/id_ed25519.pub
```

### Step 2: Add SSH Key to GitHub
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Title: "Proxmox Host - time-shift"
4. Key: Paste the output from `cat ~/.ssh/id_ed25519.pub`
5. Click "Add SSH key"

### Step 3: Clone Using SSH
```bash
# Test SSH connection
ssh -T git@github.com

# Clone using SSH URL
git clone git@github.com:notdabob/time-shift-proxmox.git
```

## Method 3: GitHub CLI (Easiest)

### Install and Authenticate
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt update
apt install gh

# Authenticate
gh auth login
# Follow the prompts to authenticate via browser

# Clone
gh repo clone notdabob/time-shift-proxmox
```

## Quick Setup Script

Save this as `setup-github-auth.sh`:

```bash
#!/bin/bash
echo "GitHub Authentication Setup for time-shift-proxmox"
echo "================================================"
echo ""
echo "Choose authentication method:"
echo "1) Personal Access Token (PAT)"
echo "2) SSH Key"
echo "3) GitHub CLI"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Setting up Personal Access Token authentication..."
        git config --global credential.helper store
        echo ""
        echo "1. Go to: https://github.com/settings/tokens"
        echo "2. Generate a new token with 'repo' scope"
        echo "3. Copy the token"
        echo ""
        read -p "Press Enter when ready to continue..."
        git clone https://github.com/notdabob/time-shift-proxmox.git
        ;;
    2)
        echo "Setting up SSH authentication..."
        if [ ! -f ~/.ssh/id_ed25519 ]; then
            ssh-keygen -t ed25519 -C "proxmox@time-shift"
        fi
        echo ""
        echo "Add this key to GitHub at https://github.com/settings/keys"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "Press Enter after adding the key to GitHub..."
        git clone git@github.com:notdabob/time-shift-proxmox.git
        ;;
    3)
        echo "Setting up GitHub CLI..."
        if ! command -v gh &> /dev/null; then
            echo "Installing GitHub CLI..."
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            apt update
            apt install -y gh
        fi
        gh auth login
        gh repo clone notdabob/time-shift-proxmox
        ;;
esac

if [ -d "time-shift-proxmox" ]; then
    cd time-shift-proxmox
    echo ""
    echo "✅ Repository cloned successfully!"
    echo "Running setup..."
    sudo ./setup.sh
else
    echo "❌ Failed to clone repository"
fi
```

## Security Notes

1. **Never commit tokens or passwords** to any repository
2. **Use SSH keys** for the most secure authentication
3. **Rotate tokens regularly** if using PAT method
4. **Use credential cache** instead of store for better security
5. **Limit token scopes** to only what's needed (repo access)

## Troubleshooting

If authentication fails:
1. Verify your username is correct
2. Ensure you're using the token, not your GitHub password
3. Check token permissions include 'repo' scope
4. For SSH, ensure your key is added to ssh-agent: `ssh-add ~/.ssh/id_ed25519`
5. Check your Proxmox host can reach GitHub: `ping github.com`
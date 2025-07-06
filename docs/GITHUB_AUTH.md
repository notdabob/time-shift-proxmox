# GitHub Authentication Setup for Private Repository

## Method 0: Interactive Token Setup (Easiest!)

### Copy, Paste, Done!

```bash
# Download and run the interactive setup
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/interactive-git-setup.sh
chmod +x interactive-git-setup.sh
./interactive-git-setup.sh
```

This script will:
1. Prompt you to paste your GitHub token (hidden input)
2. Configure git credentials automatically
3. Clone the repository
4. Run the setup

Perfect for terminals that support paste!

## Method 1: Browser-Based Authentication

### Fully Automated with Browser

```bash
# Download and run the browser auth script
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/browser-auth.sh
chmod +x browser-auth.sh
./browser-auth.sh
```

This will:
1. Install GitHub CLI if needed
2. Open your browser for authentication
3. Automatically capture the token
4. Configure git credentials
5. Clone the repository
6. Run the setup

No manual token copying required!

## Method 1: Personal Access Token (Manual)

### Step 1: Create a Personal Access Token on GitHub

1. Go to <https://github.com/settings/tokens>
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "time-shift-proxmox-access"
4. Select scopes:
   - `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 2: Configure Git to Use the Token (No Password Prompts!)

On your Proxmox host:

```bash
# Method A: Interactive setup with token prompt
cat << 'SCRIPT' > setup-git-auth.sh
#!/bin/bash
echo "GitHub PAT Authentication Setup"
echo "=============================="
echo ""
echo "Please paste your GitHub Personal Access Token:"
echo "(The token will be hidden as you type/paste)"
echo "Press Enter after pasting:"
read -s TOKEN
echo ""

# Check if token was provided
if [ -z "$TOKEN" ]; then
    echo "❌ No token provided!"
    echo "Please run the script again and paste your token."
    exit 1
fi

# Validate token length
if [ ${#TOKEN} -lt 40 ]; then
    echo "⚠️  Token seems too short. GitHub tokens are usually 40+ characters."
    echo "Token length: ${#TOKEN} characters"
fi

echo "Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Also save token to file for debugging
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token

echo "✅ Credentials configured!"
echo ""

# Test authentication first
echo "Testing authentication..."
if git ls-remote https://github.com/notdabob/time-shift-proxmox.git >/dev/null 2>&1; then
    echo "✅ Authentication successful!"
    echo ""
    echo "Cloning repository..."
    git clone https://github.com/notdabob/time-shift-proxmox.git
else
    echo "❌ Authentication failed!"
    echo ""
    echo "Please check:"
    echo "1. Your token has 'repo' scope"
    echo "2. The token is valid and not expired"
    echo "3. You pasted the complete token"
    echo ""
    echo "Get a new token from: https://github.com/settings/tokens"
    exit 1
fi
SCRIPT

chmod +x setup-git-auth.sh
./setup-git-auth.sh

# Method B: One-liner with token from file
echo 'ghp_YourTokenHere' > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token
git config --global credential.helper store
echo "https://notdabob:$(cat ~/.time-shift-proxmox-token)@github.com" > ~/.git-credentials
git clone https://github.com/notdabob/time-shift-proxmox.git

# Method C: Use our helper script
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/git-clone-easy.sh
chmod +x git-clone-easy.sh
./git-clone-easy.sh ghp_YourTokenHere
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

1. Go to <https://github.com/settings/keys>
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

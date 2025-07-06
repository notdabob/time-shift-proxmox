# Quick Start Commands for Private Repository

## Copy-Paste This Entire Block Into Your Terminal:

```bash
# Create setup script
cat << 'EOF' > setup-time-shift.sh
#!/bin/bash
echo "Time-Shift Proxmox Quick Setup"
echo "=============================="
echo ""

# Get GitHub token
if [ -f ~/.time-shift-proxmox-token ]; then
    TOKEN=$(cat ~/.time-shift-proxmox-token)
    echo "Using saved token"
else
    echo "Enter your GitHub Personal Access Token:"
    echo "(Get one from https://github.com/settings/tokens with 'repo' scope)"
    read -s TOKEN
    echo "$TOKEN" > ~/.time-shift-proxmox-token
    chmod 600 ~/.time-shift-proxmox-token
fi

# Configure git to avoid password prompts
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Clone repository
echo "Cloning repository..."
git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox

# Run setup
if [ -f "./setup.sh" ]; then
    chmod +x setup.sh
    sudo ./setup.sh
else
    echo "Installing dependencies..."
    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "Setup complete!"
fi
EOF

chmod +x setup-time-shift.sh
./setup-time-shift.sh
```

## Alternative: Direct Clone with Token

If you already have your token, use this one-liner:

```bash
TOKEN='ghp_YourTokenHere' && git config --global credential.helper store && echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials && chmod 600 ~/.git-credentials && git clone https://github.com/notdabob/time-shift-proxmox.git && cd time-shift-proxmox && sudo ./setup.sh
```

## Getting a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: "time-shift-proxmox"
4. Select scope: ✓ repo
5. Generate and copy the token (starts with ghp_)

## No Copy-Paste in Terminal?

If you can't paste in your terminal, save the token to a file first:

```bash
# On a machine where you CAN paste:
echo 'ghp_YourTokenHere' > token.txt

# Transfer token.txt to your Proxmox host, then:
TOKEN=$(cat token.txt) && rm token.txt
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox && sudo ./setup.sh
```
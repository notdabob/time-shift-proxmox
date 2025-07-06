#!/bin/bash
# Token File Setup - Alternative method for terminals with paste issues
# This script reads the token from a file instead of stdin

set -e

echo "GitHub Token File Setup"
echo "======================="
echo ""
echo "This method uses a file to avoid paste issues."
echo ""

# Check if token file exists
TOKEN_FILE="github-token.txt"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "Step 1: Create a file with your GitHub token"
    echo ""
    echo "Run ONE of these commands:"
    echo ""
    echo "Option A - Using echo:"
    echo "  echo 'ghp_YourActualTokenHere' > $TOKEN_FILE"
    echo ""
    echo "Option B - Using nano editor:"
    echo "  nano $TOKEN_FILE"
    echo "  (paste your token, press Ctrl+X, Y, Enter)"
    echo ""
    echo "Option C - Using cat:"
    echo "  cat > $TOKEN_FILE"
    echo "  (paste token, press Ctrl+D)"
    echo ""
    echo "Then run this script again: ./$0"
    exit 0
fi

# Read token from file
echo "Reading token from $TOKEN_FILE..."
TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n\r ')

# Security: Remove the token file
rm -f "$TOKEN_FILE"
echo "✓ Token file removed for security"

# Validate token
if [ -z "$TOKEN" ]; then
    echo "❌ Token file was empty!"
    exit 1
fi

if [ ${#TOKEN} -lt 40 ]; then
    echo "⚠️  Warning: Token seems short (${#TOKEN} chars)"
fi

# Configure git
echo ""
echo "Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Save to other locations
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token
echo "$TOKEN" > ~/.pat
chmod 600 ~/.pat

echo "✅ Credentials configured!"

# Test authentication
echo ""
echo "Testing authentication..."
if git ls-remote https://github.com/notdabob/time-shift-proxmox.git >/dev/null 2>&1; then
    echo "✅ Authentication successful!"
    echo ""
    
    # Clone repository
    if [ -d "time-shift-proxmox" ]; then
        echo "Repository exists, updating..."
        cd time-shift-proxmox
        git pull
    else
        echo "Cloning repository..."
        git clone https://github.com/notdabob/time-shift-proxmox.git
        cd time-shift-proxmox
    fi
    
    # Run setup
    echo ""
    echo "Running setup..."
    if [ -f "./setup.sh" ]; then
        sudo ./setup.sh
    fi
else
    echo "❌ Authentication failed!"
    echo ""
    echo "Token was: ${#TOKEN} characters long"
    echo ""
    echo "Please verify:"
    echo "1. Token has 'repo' scope"
    echo "2. Token is not expired"
    echo "3. No extra spaces or newlines"
    exit 1
fi
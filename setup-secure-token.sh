#!/bin/bash
# Secure Token Setup Script - Migrates tokens to secure storage

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Time-Shift Proxmox - Secure Token Setup${NC}"
echo "============================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    exit 1
fi

# Function to validate GitHub token
validate_github_token() {
    local token=$1
    if [[ ${#token} -lt 40 ]] && [[ ! $token =~ ^ghp_ ]] && [[ ! $token =~ ^github_pat_ ]]; then
        return 1
    fi
    return 0
}

# Check for existing tokens in legacy locations
echo -e "\n${YELLOW}Checking for existing tokens...${NC}"

LEGACY_LOCATIONS=(
    "$HOME/.time-shift-proxmox-token"
    "$HOME/.pat"
    ".pat"
    "$HOME/.git-credentials"
)

FOUND_TOKENS=0
for location in "${LEGACY_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        echo -e "  Found token at: $location"
        FOUND_TOKENS=$((FOUND_TOKENS + 1))
    fi
done

if [ $FOUND_TOKENS -gt 0 ]; then
    echo -e "\n${YELLOW}Found $FOUND_TOKENS legacy token file(s).${NC}"
    echo -n "Would you like to migrate them to secure storage? (y/n): "
    read -r MIGRATE
    
    if [[ $MIGRATE =~ ^[Yy]$ ]]; then
        python3 -c "
from lib.secure_token_storage import migrate_legacy_tokens
count = migrate_legacy_tokens()
print(f'\\nMigrated {count} token(s) to secure storage.')
"
    fi
fi

# Interactive token setup
echo -e "\n${GREEN}GitHub Token Setup${NC}"
echo "==================="
echo "Enter your GitHub Personal Access Token (PAT)."
echo "The token will be stored securely in your system keyring."
echo ""

# Check if token already exists
EXISTING_TOKEN=$(python3 -c "
from lib.secure_token_storage import get_github_token
token = get_github_token()
if token:
    print(token[:10] + '...' + token[-4:])
")

if [ -n "$EXISTING_TOKEN" ]; then
    echo -e "${YELLOW}Existing token found: $EXISTING_TOKEN${NC}"
    echo -n "Replace with a new token? (y/n): "
    read -r REPLACE
    if [[ ! $REPLACE =~ ^[Yy]$ ]]; then
        echo "Keeping existing token."
        exit 0
    fi
fi

# Read token securely
echo -n "GitHub Token (input hidden): "
read -rs GITHUB_TOKEN
echo

# Validate token
if ! validate_github_token "$GITHUB_TOKEN"; then
    echo -e "\n${RED}Invalid token format. GitHub tokens should:${NC}"
    echo "  - Start with 'ghp_' or 'github_pat_'"
    echo "  - Be at least 40 characters long"
    exit 1
fi

# Store token securely
echo -e "\n${YELLOW}Storing token securely...${NC}"
python3 -c "
from lib.secure_token_storage import store_github_token
if store_github_token('$GITHUB_TOKEN'):
    print('✓ Token stored successfully in secure storage')
else:
    print('✗ Failed to store token')
    exit(1)
"

# Configure git to use the token
echo -e "\n${YELLOW}Configuring git...${NC}"
git config --global credential.helper store

# Create credential helper script
HELPER_SCRIPT="$HOME/.time-shift-git-helper"
cat > "$HELPER_SCRIPT" << 'EOF'
#!/bin/bash
# Git credential helper for time-shift-proxmox

GITHUB_TOKEN=$(python3 -c "
from lib.secure_token_storage import get_github_token
token = get_github_token()
if token:
    print(token)
")

if [ -n "$GITHUB_TOKEN" ]; then
    echo "username=token"
    echo "password=$GITHUB_TOKEN"
fi
EOF

chmod +x "$HELPER_SCRIPT"

# Configure git to use our helper
git config --global credential.https://github.com.helper "$HELPER_SCRIPT"

echo -e "\n${GREEN}✓ Setup completed successfully!${NC}"
echo "Your GitHub token is now stored securely."
echo ""
echo "You can now clone private repositories without entering credentials:"
echo "  git clone https://github.com/notdabob/time-shift-proxmox.git"
echo ""
echo "To manage your tokens, use:"
echo "  python3 -m lib.secure_token_storage"
#!/bin/bash
# Web-based GitHub Authentication Setup
# This script opens a browser for authentication and captures the token automatically

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🌐 Web-based GitHub Authentication Setup${NC}"
echo "========================================"
echo ""

# Function to open URL in browser
open_browser() {
    local url=$1
    
    # Try different methods to open browser
    if command -v xdg-open > /dev/null; then
        xdg-open "$url" 2>/dev/null || true
    elif command -v gnome-open > /dev/null; then
        gnome-open "$url" 2>/dev/null || true
    elif command -v firefox > /dev/null; then
        firefox "$url" 2>/dev/null & 
    elif command -v chromium > /dev/null; then
        chromium "$url" 2>/dev/null &
    elif command -v google-chrome > /dev/null; then
        google-chrome "$url" 2>/dev/null &
    else
        echo -e "${YELLOW}Could not auto-open browser. Please open manually:${NC}"
        echo "$url"
    fi
}

# Method 1: GitHub OAuth Device Flow (Recommended)
github_device_flow() {
    echo -e "${BLUE}Using GitHub Device Flow Authentication${NC}"
    echo ""
    
    # GitHub OAuth App credentials (public client)
    CLIENT_ID="178c6fc778ccc68e1d6a"  # GitHub CLI's client ID (public)
    
    # Request device code
    echo "Requesting device code..."
    RESPONSE=$(curl -s -X POST https://github.com/login/device/code \
        -H "Accept: application/json" \
        -d "client_id=${CLIENT_ID}" \
        -d "scope=repo")
    
    DEVICE_CODE=$(echo "$RESPONSE" | jq -r '.device_code')
    USER_CODE=$(echo "$RESPONSE" | jq -r '.user_code')
    VERIFICATION_URL=$(echo "$RESPONSE" | jq -r '.verification_uri')
    INTERVAL=$(echo "$RESPONSE" | jq -r '.interval')
    
    if [ -z "$DEVICE_CODE" ] || [ "$DEVICE_CODE" = "null" ]; then
        echo -e "${RED}Failed to get device code${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}Opening browser for authentication...${NC}"
    echo -e "Enter this code: ${YELLOW}${USER_CODE}${NC}"
    echo ""
    
    # Open browser
    open_browser "$VERIFICATION_URL"
    
    echo "Waiting for authentication..."
    echo "(Browser should open automatically. If not, go to: $VERIFICATION_URL)"
    echo ""
    
    # Poll for token
    while true; do
        sleep "$INTERVAL"
        
        TOKEN_RESPONSE=$(curl -s -X POST https://github.com/login/oauth/access_token \
            -H "Accept: application/json" \
            -d "client_id=${CLIENT_ID}" \
            -d "device_code=${DEVICE_CODE}" \
            -d "grant_type=urn:ietf:params:oauth:grant-type:device_code")
        
        ERROR=$(echo "$TOKEN_RESPONSE" | jq -r '.error // empty')
        TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')
        
        if [ ! -z "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
            echo -e "${GREEN}✅ Authentication successful!${NC}"
            return 0
        elif [ "$ERROR" = "authorization_pending" ]; then
            printf "."
        elif [ "$ERROR" = "slow_down" ]; then
            INTERVAL=$((INTERVAL + 5))
            printf "."
        else
            echo ""
            echo -e "${RED}Authentication failed: $ERROR${NC}"
            return 1
        fi
    done
}

# Method 2: Use GitHub CLI if available
use_github_cli() {
    if command -v gh > /dev/null; then
        echo -e "${BLUE}GitHub CLI detected. Using it for authentication...${NC}"
        
        # Check if already authenticated
        if gh auth status >/dev/null 2>&1; then
            echo "Already authenticated with GitHub CLI"
            TOKEN=$(gh auth token)
        else
            echo "Launching GitHub CLI authentication..."
            gh auth login --web --scopes repo
            TOKEN=$(gh auth token)
        fi
        
        if [ ! -z "$TOKEN" ]; then
            echo -e "${GREEN}✅ Got token from GitHub CLI${NC}"
            return 0
        fi
    fi
    return 1
}

# Method 3: Local callback server
setup_local_callback_server() {
    echo -e "${BLUE}Setting up local callback server...${NC}"
    
    # Create a simple Python server to catch the callback
    cat > /tmp/github_auth_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.parse
import webbrowser
import sys
import json

class AuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'token' in params:
            token = params['token'][0]
            # Save token to file
            with open('/tmp/github_token.txt', 'w') as f:
                f.write(token)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #28a745;">✅ Authentication Successful!</h1>
                    <p>You can close this window and return to your terminal.</p>
                    <script>setTimeout(function(){ window.close(); }, 3000);</script>
                </body>
                </html>
            ''')
            
            # Shutdown server after success
            sys.stderr.write("TOKEN_RECEIVED\n")
            sys.stderr.flush()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Waiting for token...')
    
    def log_message(self, format, *args):
        pass  # Suppress logs

# Start server
PORT = 8888
with socketserver.TCPServer(("", PORT), AuthHandler) as httpd:
    print(f"Server listening on port {PORT}")
    # Open browser to GitHub token page with callback
    token_url = f"https://github.com/settings/tokens/new?description=time-shift-proxmox&scopes=repo"
    print(f"Opening browser to: {token_url}")
    print("After creating token, you'll need to manually copy it")
    webbrowser.open(token_url)
    httpd.serve_forever()
EOF

    # Run the server in background
    python3 /tmp/github_auth_server.py &
    SERVER_PID=$!
    
    echo ""
    echo -e "${YELLOW}Manual step required:${NC}"
    echo "1. Browser will open to create a new token"
    echo "2. Create the token with 'repo' scope"
    echo "3. Copy the generated token"
    echo "4. Come back here and paste it"
    echo ""
    
    # Wait for user to paste token
    read -s -p "Paste your token here: " TOKEN
    echo ""
    
    # Kill the server
    kill $SERVER_PID 2>/dev/null || true
    
    if [ ! -z "$TOKEN" ]; then
        return 0
    fi
    return 1
}

# Main authentication flow
echo "Choose authentication method:"
echo "1. GitHub Device Flow (recommended - fully automated)"
echo "2. GitHub CLI (if installed)"
echo "3. Manual token creation"
echo ""
read -p "Enter choice (1-3) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        github_device_flow
        ;;
    2)
        if ! use_github_cli; then
            echo "GitHub CLI not available, falling back to device flow..."
            github_device_flow
        fi
        ;;
    3)
        setup_local_callback_server
        ;;
    *)
        github_device_flow
        ;;
esac

# Check if we got a token
if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to obtain token${NC}"
    exit 1
fi

# Save token securely
echo "$TOKEN" > ~/.time-shift-proxmox-token
chmod 600 ~/.time-shift-proxmox-token

# Configure git
echo ""
echo "Configuring git credentials..."
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Clone repository
echo ""
echo -e "${BLUE}Cloning repository...${NC}"
if git clone https://github.com/notdabob/time-shift-proxmox.git; then
    cd time-shift-proxmox
    echo ""
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo ""
    echo "Running Time-Shift Proxmox setup..."
    sudo ./setup.sh
else
    echo -e "${RED}Failed to clone repository${NC}"
    exit 1
fi
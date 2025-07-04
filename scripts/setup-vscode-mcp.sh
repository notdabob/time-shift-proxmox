#!/bin/bash
# setup-vscode-mcp.sh - VS Code MCP integration setup
# filepath: /Users/lordsomer/Library/CloudStorage/Dropbox/Projects/ProxMox_VM_TimeShift/setup-vscode-mcp.sh

set -e

echo "🔧 Setting up VS Code MCP Integration with ServeMyAPI"
echo "===================================================="

# VS Code settings paths
VSCODE_USER_DIR="$HOME/Library/Application Support/Code/User"
VSCODE_SETTINGS="$VSCODE_USER_DIR/settings.json"

# Ensure VS Code directories exist
mkdir -p "$VSCODE_USER_DIR"

# Backup existing settings
if [ -f "$VSCODE_SETTINGS" ]; then
    echo "📋 Backing up existing VS Code settings..."
    cp "$VSCODE_SETTINGS" "$VSCODE_SETTINGS.backup.$(date +%Y%m%d-%H%M%S)"
fi

# Install MCP-related VS Code extensions
echo "📦 Installing MCP-related VS Code extensions..."

# Core extensions
code --install-extension ms-vscode.vscode-json
code --install-extension redhat.vscode-yaml

echo "✅ Extensions installed"

# Create or update VS Code settings for MCP
echo "⚙️  Configuring VS Code settings for MCP..."

# Create base settings if they don't exist
if [ ! -f "$VSCODE_SETTINGS" ]; then
    echo "{}" > "$VSCODE_SETTINGS"
fi

# Use Python to update JSON settings safely
python3 << EOF
import json
import os

settings_file = "$VSCODE_SETTINGS"

# Load existing settings
try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except:
    settings = {}

# Add MCP configuration
settings.update({
    "mcp.servers": {
        "servemyapi": {
            "command": "node",
            "args": [f"/Users/{os.getenv('USER')}/.mcp/servers/servemyapi/index.js"],
            "description": "ServeMyAPI MCP Server for secure API key management"
        }
    },
    "mcp.autoStart": True,
    "mcp.logging.level": "info",
    "terminal.integrated.env.osx": {
        "PATH": f"\${env:PATH}:/Users/{os.getenv('USER')}/.mcp/bin"
    },
    "ai.apiKeys.storage": "keychain",
    "ai.keychain.service": "AI-MCP-"
})

# Save updated settings
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("✅ VS Code settings updated")
EOF

# Create project-specific VS Code settings
PROJECT_VSCODE_DIR="/Users/lordsomer/Library/CloudStorage/Dropbox/Projects/ProxMox_VM_TimeShift/time-shift-proxmox/.vscode"
PROJECT_SETTINGS="$PROJECT_VSCODE_DIR/settings.json"

echo "📁 Creating project-specific VS Code settings..."
mkdir -p "$PROJECT_VSCODE_DIR"

cat > "$PROJECT_SETTINGS" << EOF
{
  "mcp.enabled": true,
  "mcp.servers": {
    "servemyapi": {
      "enabled": true,
      "autoStart": true
    }
  },
  "ai.enabled": true,
  "ai.apiKeys.source": "mcp",
  "python.defaultInterpreterPath": "/usr/bin/python3",
  "python.terminal.activateEnvironment": true,
  "files.associations": {
    "*.env": "shellscript",
    "*.env.*": "shellscript"
  },
  "terminal.integrated.env.osx": {
    "PATH": "\${env:PATH}:/Users/$USER/.mcp/bin"
  }
}
EOF

echo "✅ VS Code MCP integration setup complete!"
EOF
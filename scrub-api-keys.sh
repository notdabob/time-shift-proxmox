#!/bin/bash

# API Key Scrubbing Script for Git History
# This script removes API keys from commit messages and file content

echo "🔥 CRITICAL: Scrubbing API keys from git history..."

# List of API keys to remove
API_KEYS=(
)

# Create expressions for git filter-repo
EXPRESSIONS=""
for key in "${API_KEYS[@]}"; do
    EXPRESSIONS="$EXPRESSIONS --replace-text <(echo '$key==>***REDACTED***')"
done

echo "Creating backup of current repository..."
cp -r .git .git.backup

echo "Removing API keys from file content..."
eval "git filter-repo $EXPRESSIONS --force"

echo "✅ API keys scrubbed from git history!"
echo "⚠️  You MUST force push to update the remote repository:"
echo "    git push --force-with-lease origin main"
echo ""
echo "🔒 IMPORTANT: Generate new API keys for all services!"

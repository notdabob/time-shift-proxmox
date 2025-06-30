#!/bin/bash

# API Key Scrubbing Script for Git History
# This script removes API keys from commit messages and file content

echo "🔥 CRITICAL: Scrubbing API keys from git history..."

# List of API keys to remove
API_KEYS=(
    "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"
    "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"
    "AIzaSyASYlIp9cnVKYWfTKYqRK_tlbBoYpFZnEM"
    "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"
    "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"
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

#!/bin/bash
# Script to add deprecation warnings to redundant setup scripts

DEPRECATED_SCRIPTS=(
    "one-click-setup.sh"
    "instant-setup.sh"
    "interactive-git-setup.sh"
    "web-auth-setup.sh"
    "token-file-setup.sh"
    "setup-github-token.sh"
    "git-clone-easy.sh"
    "easy-git-auth.sh"
)

DEPRECATION_MESSAGE='#!/bin/bash
# DEPRECATED: This script is deprecated and will be removed in the next major version.
# Please use one of the following instead:
#   - setup.sh: For complete installation
#   - pat-setup.sh: For PAT file authentication
#   - setup-secure-token.sh: For secure token storage
# See SETUP_SCRIPTS.md for more information.

echo "⚠️  WARNING: This script is deprecated!"
echo "Please use one of the recommended scripts instead:"
echo "  - setup.sh: For complete installation"
echo "  - pat-setup.sh: For PAT file authentication"
echo "  - setup-secure-token.sh: For secure token storage"
echo ""
echo "See SETUP_SCRIPTS.md for more information."
echo ""
read -p "Do you want to continue anyway? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Original script content follows...
'

echo "Adding deprecation warnings to redundant setup scripts..."

for script in "${DEPRECATED_SCRIPTS[@]}"; do
    if [ -f "../$script" ]; then
        echo "Processing $script..."
        # Create a backup
        cp "../$script" "../$script.backup"
        
        # Get the original content (excluding shebang)
        original_content=$(tail -n +2 "../$script")
        
        # Write new content with deprecation warning
        echo "$DEPRECATION_MESSAGE" > "../$script"
        echo "$original_content" >> "../$script"
        
        echo "✓ Added deprecation warning to $script"
    else
        echo "⚠️  $script not found, skipping..."
    fi
done

echo ""
echo "✅ Deprecation warnings added to all redundant scripts."
echo "Backup files created with .backup extension."
echo ""
echo "Next steps:"
echo "1. Test that the modified scripts still work"
echo "2. Update README.md to reference only primary scripts"
echo "3. Consider removing deprecated scripts in next release"
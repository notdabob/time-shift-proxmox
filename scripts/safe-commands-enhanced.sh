#!/bin/bash
# Enhanced safe command wrapper that uses command-permissions.json
# Usage: ./scripts/safe-commands-enhanced.sh <command> [args...]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PERMISSIONS_FILE="${PERMISSIONS_FILE:-$PROJECT_ROOT/etc/security/command-permissions.json}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if permissions file exists
if [ ! -f "$PROJECT_ROOT/$PERMISSIONS_FILE" ]; then
    echo -e "${RED}Error: Permissions file not found at $PERMISSIONS_FILE${NC}"
    exit 1
fi

# Function to check if command is allowed
check_command() {
    local cmd="$1"
    shift
    local args="$@"
    
    # Use Python to parse JSON and check permissions
    python3 - <<EOF
import json
import sys
import re

with open('$PROJECT_ROOT/$PERMISSIONS_FILE') as f:
    perms = json.load(f)

cmd = '$cmd'
args = '''$args'''
full_command = f"{cmd} {args}".strip()

# Check if command is forbidden
for forbidden in perms.get('forbidden_commands', []):
    if forbidden in full_command or re.match(forbidden, full_command):
        print(f"FORBIDDEN: Command matches forbidden pattern: {forbidden}")
        sys.exit(1)

# Check if command is approved
approved = perms.get('approved_commands', {})
if cmd in approved:
    cmd_config = approved[cmd]
    
    # Check if auto-approved
    if cmd_config.get('auto_approve', False):
        print(f"APPROVED: {cmd} is auto-approved")
        sys.exit(0)
    
    # Check if confirmation required
    if cmd_config.get('require_confirmation', False):
        print(f"CONFIRM: {cmd} requires confirmation")
        sys.exit(2)
    
    print(f"MANUAL: {cmd} requires manual approval")
    sys.exit(3)
else:
    print(f"UNKNOWN: {cmd} is not in the approved commands list")
    sys.exit(4)
EOF

    return $?
}

# Main execution
COMMAND="$1"
shift || true
ARGS="$@"

# Check if command is provided
if [ -z "$COMMAND" ]; then
    echo -e "${RED}Error: No command provided${NC}"
    echo "Usage: $0 <command> [args...]"
    exit 1
fi

# Check command permissions
check_command "$COMMAND" "$ARGS"
STATUS=$?

case $STATUS in
    0)
        # Auto-approved - execute
        echo -e "${GREEN}✓ Executing auto-approved command: $COMMAND $ARGS${NC}"
        exec "$COMMAND" $ARGS
        ;;
    1)
        # Forbidden
        echo -e "${RED}✗ Command is forbidden and cannot be executed${NC}"
        exit 1
        ;;
    2)
        # Requires confirmation
        echo -e "${YELLOW}⚠ Command requires confirmation: $COMMAND $ARGS${NC}"
        read -p "Do you want to execute this command? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Executing with confirmation: $COMMAND $ARGS${NC}"
            exec "$COMMAND" $ARGS
        else
            echo -e "${RED}✗ Command cancelled by user${NC}"
            exit 1
        fi
        ;;
    3)
        # Manual approval required
        echo -e "${YELLOW}⚠ Command requires manual approval: $COMMAND $ARGS${NC}"
        echo "This command is not auto-approved. Please review before executing."
        read -p "Do you want to execute this command? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Executing with manual approval: $COMMAND $ARGS${NC}"
            exec "$COMMAND" $ARGS
        else
            echo -e "${RED}✗ Command cancelled by user${NC}"
            exit 1
        fi
        ;;
    4)
        # Unknown command
        echo -e "${RED}✗ Command not in approved list: $COMMAND${NC}"
        echo "To execute this command, add it to the approved_commands in:"
        echo "  $PERMISSIONS_FILE"
        exit 1
        ;;
    *)
        # Unexpected status
        echo -e "${RED}✗ Unexpected error checking command permissions${NC}"
        exit 1
        ;;
esac
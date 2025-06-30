#!/bin/bash
# Safe command wrapper for auto-approval
# Usage: ./scripts/safe-commands.sh <command-name> [args...]

case "$1" in
    "git-status")
        git status
        ;;
    "git-add")
        git add "${@:2}"
        ;;
    "git-commit")
        git commit -m "${@:2}"
        ;;
    "list-files")
        ls -la "${@:2}"
        ;;
    "check-python")
        python3 --version
        ;;
    "install-deps")
        pip install -r requirements.txt
        ;;
    "make-executable")
        chmod +x "${@:2}"
        ;;
    *)
        echo "Command '$1' not in safe list"
        echo "Available safe commands:"
        echo "  git-status, git-add, git-commit, list-files"
        echo "  check-python, install-deps, make-executable"
        exit 1
        ;;
esac

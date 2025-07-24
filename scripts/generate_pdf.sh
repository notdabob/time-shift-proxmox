#!/bin/sh
#
# Converts the main Perplexity AI conversation Markdown file into a PDF.
# Checks for pandoc and a LaTeX installation before running.

# Configuration file path
CONFIG_FILE="etc/project_config.json"

# Read configuration from JSON file
DOCS_FILE_PATH_REGEX=$(jq -r '.docs.docsFilePathRegex' "$CONFIG_FILE")
DOCS_OUTPUT_FILE_PATH=$(jq -r '.docs.docsOutputFilePath' "$CONFIG_FILE")

if [ -z "$DOCS_FILE_PATH_REGEX" ] || [ -z "$DOCS_OUTPUT_FILE_PATH" ]; then
    echo "Error: Could not read docs configuration from $CONFIG_FILE. Please ensure 'docsFilePathRegex' and 'docsOutputFilePath' are defined." >&2
    exit 1
fi

# 1. Check if pandoc is installed
if ! command -v pandoc >/dev/null 2>&1; then
    echo "Error: pandoc is not installed. Please install it to generate the PDF." >&2
    echo "On macOS (with Homebrew): brew install pandoc" >&2
    echo "On Debian/Ubuntu: sudo apt-get install pandoc" >&2
    exit 1
fi

# 2. Check for a LaTeX engine, which pandoc uses for PDF generation.
if ! command -v pdflatex >/dev/null 2>&1; then
    echo "Warning: A LaTeX engine (like pdflatex) was not found." >&2
    echo "PDF generation may fail. Please install a LaTeX distribution." >&2
    echo "On macOS (with Homebrew): brew install --cask mactex-no-gui" >&2
    echo "On Debian/Ubuntu: sudo apt-get install texlive-latex-base" >&2
fi

echo "Generating $DOCS_OUTPUT_FILE_PATH from $DOCS_FILE_PATH_REGEX..."
if pandoc "$DOCS_FILE_PATH_REGEX" -o "$DOCS_OUTPUT_FILE_PATH"; then
    echo "Successfully created $DOCS_OUTPUT_FILE_PATH."
else
    echo "Error: PDF generation failed. Check pandoc output above for details." >&2
    exit 1
fi

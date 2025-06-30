#!/bin/sh
#
# Converts the main Perplexity AI conversation Markdown file into a PDF.
# Checks for pandoc and a LaTeX installation before running.

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

echo "Generating Perplexity.pdf from docs/PERPLEXITY_CONVERSATION.md..."
if pandoc docs/PERPLEXITY_CONVERSATION.md -o Perplexity.pdf; then
    echo "Successfully created Perplexity.pdf."
else
    echo "Error: PDF generation failed. Check pandoc output above for details." >&2
    exit 1
fi
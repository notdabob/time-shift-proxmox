#!/bin/bash
# Test runner script for Time Shift Proxmox project

echo "Running Time Shift Proxmox Test Suite"
echo "====================================="

# Ensure we're in the project root
cd "$(dirname "$0")"

# Run all tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ -v --cov=lib --cov=bin --cov-report=term-missing --cov-report=html

# Run specific test categories if needed
if [ "$1" == "unit" ]; then
    echo "Running unit tests only..."
    python -m pytest tests/test_*.py -v -k "not integration"
elif [ "$1" == "integration" ]; then
    echo "Running integration tests only..."
    python -m pytest tests/ -v -k "integration"
fi

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
    echo ""
    echo "Coverage report available in htmlcov/index.html"
else
    echo ""
    echo "✗ Some tests failed!"
    exit 1
fi
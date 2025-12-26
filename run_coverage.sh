#!/bin/bash
#
# Run pytest with coverage reporting
#
# This script runs the full test suite with coverage reporting.
# It disables the unraisable exception plugin to avoid cleanup errors.
#
# Usage:
#   ./run_coverage.sh              # Run with terminal report
#   ./run_coverage.sh html         # Run with HTML report
#   ./run_coverage.sh both         # Run with both terminal and HTML reports
#

# Activate virtual environment
source llf_venv/bin/activate

# Determine report type
REPORT_TYPE="${1:-term}"

case "$REPORT_TYPE" in
    html)
        echo "Running tests with HTML coverage report..."
        pytest --cov --cov-report=html -p no:unraisableexception
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    both)
        echo "Running tests with both terminal and HTML coverage reports..."
        pytest --cov --cov-report=term --cov-report=html -p no:unraisableexception
        echo ""
        echo "Coverage report also available in htmlcov/index.html"
        ;;
    term|*)
        echo "Running tests with terminal coverage report..."
        pytest --cov --cov-report=term -p no:unraisableexception
        ;;
esac

# Capture exit code from pytest
EXIT_CODE=$?

echo ""
echo "Test execution completed with exit code: $EXIT_CODE"
echo ""
echo "Note: Ignore any 'Exception ignored in atexit callback' warnings."
echo "These are harmless cleanup warnings and don't affect test results."
echo ""

exit $EXIT_CODE

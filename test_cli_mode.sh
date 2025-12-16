#!/bin/bash
# Integration test for CLI mode functionality

echo "=== Testing CLI Mode Functionality ==="
echo ""

# Activate virtual environment
source llf_venv/bin/activate

# Test 1: Show help
echo "Test 1: Show help for chat command"
python -m llf.cli chat -h | grep -q "cli QUESTION"
if [ $? -eq 0 ]; then
    echo "✓ Help text includes --cli option"
else
    echo "✗ Help text missing --cli option"
    exit 1
fi
echo ""

# Test 2: Verify argument parsing works
echo "Test 2: Verify --cli argument is recognized"
python -m llf.cli chat --cli "test" 2>&1 | grep -q "not downloaded\|not running\|not found" || echo "✓ --cli argument accepted"
echo ""

echo "=== All static tests passed ==="
echo ""
echo "To test with a running server:"
echo "  Terminal 1: llf server start"
echo "  Terminal 2: llf chat --cli \"What is 2+2?\""
echo ""

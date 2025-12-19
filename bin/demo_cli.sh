#!/bin/bash
# LLF CLI Demonstration Script
#
# This script demonstrates various ways to use the LLF command-line interface.
# Make sure you've activated the virtual environment first:
#   source llf_venv/bin/activate

set -e  # Exit on error

echo "========================================"
echo "LLF Command-Line Interface Demo"
echo "========================================"
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

demo_command() {
    echo -e "${BLUE}$ $1${NC}"
    eval "$1"
    echo
}

# 1. Show version
echo -e "${GREEN}1. Check LLF version${NC}"
demo_command "llf --version"

# 2. Show general help
echo -e "${GREEN}2. Display general help${NC}"
demo_command "llf -h | head -20"

# 3. Show download command help
echo -e "${GREEN}3. Display download command help${NC}"
demo_command "llf download -h"

# 4. List downloaded models
echo -e "${GREEN}4. List downloaded models${NC}"
demo_command "llf list"

# 5. Show model info
echo -e "${GREEN}5. Show model information${NC}"
demo_command "llf info"

# 6. Demonstrate custom download directory
echo -e "${GREEN}6. Show custom download directory usage${NC}"
echo -e "${YELLOW}Example (not executed):${NC}"
echo "  llf -d /custom/path download"
echo "  llf -d /custom/path chat"
echo

# 7. Demonstrate different log levels
echo -e "${GREEN}7. Available log levels${NC}"
echo "  --log-level DEBUG   : Show detailed debugging information"
echo "  --log-level INFO    : Show normal operational messages (default)"
echo "  --log-level WARNING : Show only warnings and errors"
echo "  --log-level ERROR   : Show only errors"
echo

echo "========================================"
echo "Demo Complete!"
echo "========================================"
echo
echo "To start chatting with the LLM, run:"
echo "  llf"
echo
echo "For more examples, see:"
echo "  - README.md"
echo "  - USAGE.md"
echo "  - QUICK_REFERENCE.md"

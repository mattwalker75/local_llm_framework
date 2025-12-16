#!/usr/bin/env bash
#
# Llama Server Wrapper Script
#
# This script starts the llama-server binary with the specified model.
# It provides a simple interface for the LLF framework to manage the server.
#
# Usage:
#   start_llama_server.sh --server-path PATH --model-file PATH [--host HOST] [--port PORT]
#

set -e

# Default values
HOST="0.0.0.0"
PORT="8000"
SERVER_PATH=""
MODEL_FILE=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --server-path)
            SERVER_PATH="$2"
            shift 2
            ;;
        --model-file)
            MODEL_FILE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --server-path PATH --model-file PATH [--host HOST] [--port PORT]"
            echo ""
            echo "Options:"
            echo "  --server-path PATH   Path to llama-server binary (required)"
            echo "  --model-file PATH    Path to GGUF model file (required)"
            echo "  --host HOST          Host to bind to (default: 0.0.0.0)"
            echo "  --port PORT          Port to bind to (default: 8000)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$SERVER_PATH" ]; then
    echo "Error: --server-path is required"
    exit 1
fi

if [ -z "$MODEL_FILE" ]; then
    echo "Error: --model-file is required"
    exit 1
fi

# Check if server binary exists
if [ ! -f "$SERVER_PATH" ]; then
    echo "Error: llama-server binary not found at: $SERVER_PATH"
    exit 1
fi

# Check if server binary is executable
if [ ! -x "$SERVER_PATH" ]; then
    echo "Error: llama-server binary is not executable: $SERVER_PATH"
    exit 1
fi

# Check if model file exists
if [ ! -f "$MODEL_FILE" ]; then
    echo "Error: Model file not found at: $MODEL_FILE"
    exit 1
fi

# Start the llama-server
echo "Starting llama-server..."
echo "  Server: $SERVER_PATH"
echo "  Model:  $MODEL_FILE"
echo "  Host:   $HOST"
echo "  Port:   $PORT"
echo ""

exec "$SERVER_PATH" --model "$MODEL_FILE" --host "$HOST" --port "$PORT"

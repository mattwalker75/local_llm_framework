#!/usr/bin/env python3
"""
Manual Test Script for Missing local_llm_server Configuration Handling

WHY THIS IS A MANUAL TEST (NOT A REGULAR PYTEST TEST):
----------------------------------------------------
This script is NOT run by pytest during normal test execution. It's a manual integration
test that requires the 'llf' CLI to be installed and accessible in your PATH.

Regular pytest tests (test_*.py) use mocking to test individual components in isolation,
while this script performs end-to-end testing of the actual installed CLI behavior with
real subprocess calls.

HOW TO RUN THIS SCRIPT:
-----------------------
From the project root directory:
    python3 tests/manual_test_missing_config.py

Or make it executable and run directly:
    chmod +x tests/manual_test_missing_config.py
    ./tests/manual_test_missing_config.py

PREREQUISITES:
--------------
- The 'llf' command must be installed (pip install -e .)
- Python 3.7 or higher

WHAT THIS SCRIPT TESTS:
-----------------------
This script verifies graceful handling of missing local_llm_server configuration by
testing two scenarios:

1. External API config (OpenAI) - no local_llm_server section at all
   - Tests that server commands handle missing local server config gracefully
   - Verifies helpful error messages are shown instead of crashes

2. Local config with non-existent llama-server binary path
   - Tests that server commands detect invalid llama-server paths
   - Verifies clear error messages when binary doesn't exist

Expected behavior:
- server status: Should show API info for external, error for broken local
- server start/stop/restart: Should show helpful "not configured" message
- No crashes, exceptions, or confusing stack traces
- User-friendly error messages with actionable guidance

WHY IT'S NAMED 'manual_test_*' INSTEAD OF 'test_*':
---------------------------------------------------
The 'manual_test_' prefix prevents pytest from automatically discovering and running
this script. If it were named 'test_*.py', pytest would try to run it and fail because:
1. It expects 'llf' to be installed (which may not be true in test environments)
2. It uses subprocess calls instead of mocking
3. It's an integration test, not a unit test
"""
import json
import tempfile
import subprocess
from pathlib import Path

def test_config(config_content, test_name, commands):
    """Test a specific configuration."""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}\n")

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_content, f, indent=2)
        config_file = f.name

    try:
        for cmd in commands:
            print(f"\n> llf --config {config_file} {cmd}")
            print("-" * 60)
            result = subprocess.run(
                f"llf --config {config_file} {cmd}",
                shell=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            print(f"Exit code: {result.returncode}")
    finally:
        Path(config_file).unlink()

# Test 1: External API config (no local_llm_server)
external_api_config = {
    "llm_endpoint": {
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "sk-test-key",
        "model_name": "gpt-4"
    },
    "model_dir": "models",
    "cache_dir": ".cache",
    "log_level": "ERROR",
    "inference_params": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9
    }
}

# Test 2: Local config with non-existent llama-server path
broken_local_config = {
    "local_llm_server": {
        "llama_server_path": "/nonexistent/path/llama-server",
        "server_host": "127.0.0.1",
        "server_port": 8000,
        "model_dir": "test-model"
    },
    "llm_endpoint": {
        "api_base_url": "http://127.0.0.1:8000/v1",
        "api_key": "EMPTY",
        "model_name": "test-model"
    },
    "model_dir": "models",
    "cache_dir": ".cache",
    "log_level": "ERROR",
    "inference_params": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1
    }
}

# Commands to test
server_commands = [
    "server status",
    "server start",
    "server stop",
    "server restart"
]

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Missing local_llm_server Configuration Handling")
    print("="*60)

    # Test external API config
    test_config(
        external_api_config,
        "External API (OpenAI) - No local_llm_server section",
        server_commands
    )

    # Test broken local config
    test_config(
        broken_local_config,
        "Local config with non-existent llama-server binary",
        server_commands
    )

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)

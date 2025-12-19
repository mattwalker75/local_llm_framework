# Local LLM Framework (LLF)

A flexible Python framework designed to run Large Language Models (LLMs) locally using llama.cpp, or connect to external LLM APIs (OpenAI, Anthropic, etc.).

## Overview

Local LLM Framework (LLF) provides maximum flexibility - run models locally for zero token costs and full privacy, or seamlessly switch to external APIs when needed. Phase 1 focuses on CLI-based interaction with plans for future expansion into API servers, GUIs, and advanced features.

**Current Version:** 0.1.0 (Phase 1)

## Features

### Phase 1 (Current)
- ✅ Run modern LLMs locally using llama.cpp (llama-server)
- ✅ Connect to external LLM APIs (OpenAI, Anthropic, etc.)
- ✅ Seamless switching between local and external LLMs via config
- ✅ Automatic model download and management from HuggingFace Hub (GGUF format)
- ✅ Interactive CLI chat interface with colored output
- ✅ Web-based GUI interface for easy management and chat
- ✅ Local network access for server and GUI (with `--share` flag)
- ✅ Authentication system for GUI with secret key protection
- ✅ Customizable prompt configuration system
- ✅ Production-quality modular architecture
- ✅ Comprehensive unit testing (100% test passing rate)
- ✅ Clean installation and uninstallation process
- ✅ Support for Qwen2.5-Coder-7B-Instruct-GGUF (default local model)
- ✅ Configurable inference parameters per API
- ✅ Independent server management (start/stop/status/restart for local LLM)
- ✅ OpenAI-compatible API interface

### Future Phases (Planned)
- 🔮 Voice input/output
- 🔮 Internet access capabilities
- 🔮 Tool execution (commands, filesystem access)
- 🔮 Multi-model switching via configuration

## System Requirements

### Hardware
- **RAM:** Minimum 8GB recommended (7B quantized model requires ~4-6GB RAM)
- **Storage:** 10GB+ free space for models (quantized GGUF models are much smaller)
- **GPU:** Optional (llama.cpp supports Metal on macOS, CUDA on Linux/Windows)
  - CPU-only mode works well with quantized models

### Software
- **Python:** 3.11 or higher
- **llama.cpp:** Compiled with llama-server binary (see setup instructions below)
- **Operating System:**
  - macOS (Apple Silicon or Intel) ✅ Fully supported
  - Linux (Ubuntu 20.04+, other distributions)
  - Windows (via WSL2 recommended)

## Installation

### 1. Compile llama.cpp (One-Time Setup)

**IMPORTANT:** You need to compile llama.cpp first to get the llama-server binary.

```bash
# Clone llama.cpp repository (in parent directory of local_llm_framework)
cd ..
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Compile llama.cpp
mkdir build
cd build
cmake ..
cmake --build . --config Release

# Verify llama-server binary exists
ls bin/llama-server  # Should show the binary
```

**Note:** By default, LLF expects llama-server at `../llama.cpp/build/bin/llama-server`. You can configure a different path in the config file if needed.

### 2. Clone the Repository

```bash
cd ../  # Go back to parent directory
git clone <repository-url>
cd local_llm_framework
```

### 3. Create Virtual Environment

**IMPORTANT:** LLF must be installed and run inside a Python virtual environment.

```bash
# Create virtual environment
python -m venv llf_venv

# Activate virtual environment
source llf_venv/bin/activate  # On macOS/Linux
# OR
llf_venv\Scripts\activate  # On Windows
```

### 4. Verify Virtual Environment is Active

```bash
# Should show path to llf_venv
echo $VIRTUAL_ENV
```

### 5. Install LLF Package

**Important:** Use `pip install -e .` (NOT `python setup.py install`)

```bash
# Install in editable mode (recommended)
pip install -e .
```

**What this does:**
- Reads `setup.py` and installs all dependencies from `requirements.txt`
- Creates the `llf` command (entry point)
- Installs in "editable" mode - code changes take effect immediately
- Modern, recommended approach (running `setup.py` directly is deprecated)

**Installed dependencies:**
- OpenAI Python client (for llama-server and external API compatibility)
- HuggingFace Hub (for model downloads)
- Rich (CLI interface)
- Requests, psutil (HTTP requests and process management)
- Pytest and coverage tools (for testing)

**Optional: Install with dev tools:**
```bash
pip install -e .[dev]  # Includes pytest, flake8, mypy, black
```

## Usage

### Quick Start

```bash
# Activate virtual environment
source llf_venv/bin/activate

# Verify LLF command is available
llf --version

# Run LLF
llf
```

### Command-Line Interface

LLF provides three ways to run commands:

1. **Standalone script** (after activating venv):
   ```bash
   ./bin/llf -h
   ```

2. **Installed command** (recommended):
   ```bash
   pip install -e .
   llf -h
   ```

3. **Python module**:
   ```bash
   python -m llf.cli -h
   ```

### Getting Help

```bash
# General help
llf -h
llf --help

# Command-specific help
llf download -h
llf chat -h
llf list -h
llf info -h
```

### Common Commands

```bash
# Start interactive chat (default)
llf
llf chat

# Download the default model
llf model download

# Download a specific HuggingFace model
llf model download --huggingface-model "mistralai/Mistral-7B-Instruct-v0.2"

# Download a model from a direct URL
llf model download --url "https://example.com/model.gguf" --name "my-custom-model"

# List downloaded models
llf model list

# Show model information
llf model info

# Set custom download directory
llf -d /custom/path model download

# Enable debug logging
llf --log-level DEBUG chat

# Show version
llf --version
```

### Server Management

LLF runs a local llama-server on `localhost:8000` to serve model inference requests. You can manage this server independently:

```bash
# Start the server independently (runs in foreground)
llf server start

# Start the server in background (daemon mode)
llf server start --daemon

# Start server with a specific HuggingFace model
llf server start --huggingface-model "mistralai/Mistral-7B-Instruct-v0.2"

# Start server with a GGUF model in custom directory
llf server start --gguf-dir test_gguf --gguf-file my-model.gguf

# Make server accessible on local network (binds to 0.0.0.0)
llf server start --share

# Check server status
llf server status

# Stop the server
llf server stop

# Restart the server
llf server restart
```

**Network Access:**

By default, the server only listens on `127.0.0.1` (localhost), making it accessible only from the same machine. To make it accessible from other devices on your local network:

```bash
# Start server with network access
llf server start --share

# Access from same device:
# http://127.0.0.1:8000/v1

# Access from other devices on local network:
# http://YOUR_IP:8000/v1
# Replace YOUR_IP with your machine's IP address (e.g., 192.168.1.100)
```

**Security Note:** The `--share` flag binds to `0.0.0.0`, making the server accessible to ALL devices on your local network. This does NOT expose it to the internet (unlike some tools that create public tunnels). Only use `--share` on trusted networks.

**Chat with Server Auto-Start Control:**

```bash
# Default: prompts to start server if not running
llf chat

# Auto-start server without prompting
llf chat --auto-start-server

# Exit with error if server not running
llf chat --no-server-start
```

**Typical Workflow:**

1. Start server in background: `llf server start --daemon`
2. Run multiple chat sessions: `llf chat --no-server-start`
3. Stop server when done: `llf server stop`

This allows you to keep the server running while executing multiple commands or chat sessions against it.

### Web-Based GUI Interface

LLF includes a modern web-based GUI interface built with Gradio, providing an intuitive alternative to the command-line interface.

**Start the GUI:**

```bash
# Start GUI (opens in browser automatically on port 7860)
llf gui

# Start on custom port
llf gui --port 8080

# Make GUI accessible on local network
llf gui --share

# Require authentication with secret key
llf gui --key MY_SECRET_KEY_123

# Combine network access with authentication
llf gui --share --key MY_SECRET_KEY_123

# Start without opening browser
llf gui --no-browser
```

**Network Access and Security:**

By default, the GUI only listens on `127.0.0.1` (localhost). To make it accessible from other devices on your local network, use the `--share` flag:

```bash
# Make GUI accessible on local network
llf gui --share

# Access from same device:
# http://127.0.0.1:7860

# Access from other devices on local network:
# http://YOUR_IP:7860
# Replace YOUR_IP with your machine's IP address (e.g., 192.168.1.100)
```

**Authentication:**

When exposing the GUI to your local network, you can require authentication using the `--key` parameter:

```bash
# Start GUI with authentication
llf gui --share --key MY_SECRET_KEY_123
```

When `--key` is set, users will see a login page that requires entering the secret key before accessing the GUI. This provides basic protection for network-accessible instances.

**Security Notes:**
- The `--share` flag binds to `0.0.0.0`, making the GUI accessible to ALL devices on your local network
- This does NOT create an internet tunnel (unlike Gradio's built-in share feature)
- Only use `--share` on trusted networks
- Always use `--key` when enabling network access to prevent unauthorized access
- The authentication is basic string comparison - suitable for local network protection but not cryptographically secure

**GUI Features:**

The GUI provides 5 main tabs:

1. **💬 Chat Tab**
   - Interactive conversation with your LLM
   - Conversation history display
   - Clear chat functionality

2. **🖥️ Server Tab**
   - View server status
   - Start/stop/restart local LLM server
   - Real-time status updates

3. **📦 Models Tab**
   - List downloaded models
   - Download models from HuggingFace or URL
   - View model information

4. **⚙️ Config Tab (Infrastructure)**
   - View and edit `configs/config.json`
   - Configure local server settings, API connections, inference parameters
   - Auto-reload on save
   - Create backups of configuration

5. **📝 Config Tab (Prompts)**
   - View and edit `configs/config_prompt.json`
   - Customize system prompts, conversation format, and message injection
   - Auto-reload on save
   - Create backups of configuration

**When to Use GUI vs CLI:**

- **Use GUI** when:
  - You prefer visual interfaces
  - Managing configuration files
  - Monitoring server status in real-time
  - You need remote access (with --share flag)

- **Use CLI** when:
  - Automating tasks with scripts
  - Working in terminal-only environments
  - Integrating with other command-line tools
  - You prefer keyboard-based workflows

### Interactive Chat Commands

Once in the chat interface:

- **Type your message** - Chat with the LLM
- `help` - Display help information
- `info` - Show model and system information
- `clear` - Clear the screen
- `exit` or `quit` - Exit the application
- **Ctrl+C** - Force exit at any time

### Command-Line Options

**Global Options:**
- `-d, --download-dir PATH` - Set model download directory
- `-c, --config FILE` - Load configuration from JSON file
- `--cache-dir PATH` - Set HuggingFace cache directory
- `--log-level LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--version` - Show version information

**Download Options:**
- `--huggingface-model NAME` - HuggingFace model identifier (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
- `--url URL --name NAME` - Download from direct URL (both flags required together)
  - `--url` - Direct URL to GGUF model file (e.g., "https://example.com/model.gguf")
  - `--name` - Local directory name for the model (e.g., "my-custom-model")
  - Cannot be used with `--huggingface-model`
- `--force` - Force re-download even if model exists
- `--token TOKEN` - HuggingFace API token for private models

**Model Selection (for server/chat commands):**
- `--huggingface-model NAME` - Use HuggingFace model structure (models/{sanitized_name}/)
- `--gguf-dir DIR --gguf-file FILE` - Use GGUF model in custom directory (models/DIR/FILE)
  - Both flags must be specified together
  - Example: `--gguf-dir test_gguf --gguf-file my-model.gguf`

For detailed usage information, see [USAGE.md](USAGE.md)

## Configuration

### Default Settings (Local LLM)

LLF uses sensible defaults for local llama.cpp runtime:
- **Model:** Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
- **GGUF File:** qwen2.5-coder-7b-instruct-q4_k_m.gguf (Q4_K_M quantization)
- **Model Directory:** `./models/`
- **Cache Directory:** `./.cache/`
- **llama-server Path:** `../llama.cpp/build/bin/llama-server`
- **API Base URL:** `http://127.0.0.1:8000/v1`
- **Temperature:** 0.7
- **Max Tokens:** 2048

### Local LLM Configuration

Create a `configs/config.json` file for local llama.cpp:

```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "gguf_file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf"
  },
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
  },
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1
  },
  "log_level": "INFO"
}
```

### External API Configuration (OpenAI)

To use OpenAI or other external APIs, simply change the endpoint configuration:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-OPENAI-API-KEY",
    "model_name": "gpt-4"
  },
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  },
  "log_level": "INFO"
}
```

**Note:** External APIs don't support llama.cpp-specific parameters like `top_k` and `repetition_penalty`. See example config files in [configs/config_examples/](configs/config_examples/):
- `configs/config_examples/config.local.example` - For local llama-server
- `configs/config_examples/config.openai.example` - For OpenAI API
- `configs/config_examples/config.anthropic.example` - For Anthropic API

**Quick setup:**
```bash
cp configs/config_examples/config.local.example configs/config.json    # For local LLM
# OR
cp configs/config_examples/config.openai.example configs/config.json   # For OpenAI
```

Use configuration: `llf --config configs/config.json chat`

## Testing

LLF includes comprehensive unit tests with **90% code coverage**.

### Run All Tests

```bash
source llf_venv/bin/activate
pytest tests/
```

### Run with Coverage Report

```bash
pytest tests/ --cov=llf --cov-report=term-missing
```

### Run with HTML Coverage Report

```bash
pytest tests/ --cov=llf --cov-report=html
# Open htmlcov/index.html in browser
```

## Project Structure

```
local_llm_framework/
├── llf/                        # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # CLI interface module
│   ├── config.py              # Configuration management
│   ├── llm_runtime.py         # llama-server runtime management
│   ├── logging_config.py      # Logging configuration
│   └── model_manager.py       # Model download and management
├── tests/                      # Unit tests (90% coverage)
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_llm_runtime.py
│   └── test_model_manager.py
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
└── README.md                 # This file
```

## Troubleshooting

### Virtual Environment Not Active

```bash
source llf_venv/bin/activate
which python  # Should point to llf_venv/bin/python
```

### Model Download Fails

```bash
# For private models, set HuggingFace token:
export HUGGING_FACE_HUB_TOKEN="your_token_here"
python -m llf.cli download --force
```

### Out of Memory

1. Close other applications
2. Use a smaller model
3. Reduce GPU memory utilization in config

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf llf_venv/

# Remove downloaded models (optional)
rm -rf models/ .cache/

# Remove repository
cd .. && rm -rf local_llm_framework/
```

## Known Limitations (Phase 1)

- No API server exposure (local llama-server only)
- No voice input/output
- No internet access for LLM
- No tool execution capabilities
- Single model per session

These limitations are intentional for Phase 1 and will be addressed in future releases.

## Version History

### v0.1.0 (Phase 1) - Current
- Initial release
- CLI-based interaction
- Automatic model management (GGUF format)
- llama.cpp/llama-server integration
- Comprehensive testing

---

**Built for the local LLM community**

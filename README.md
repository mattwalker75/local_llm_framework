# Local LLM Framework (LLF)

A flexible Python framework designed to run Large Language Models (LLMs) locally on your computer using llama.cpp as the runtime engine.

## Overview

Local LLM Framework (LLF) provides maximum flexibility, zero token costs, and full local control while exposing LLMs through multiple access methods. Phase 1 focuses exclusively on CLI-based interaction with plans for future expansion into API servers, GUIs, and advanced features.

**Current Version:** 0.1.0 (Phase 1)

## Features

### Phase 1 (Current)
- ✅ Run modern LLMs locally using llama.cpp (llama-server)
- ✅ Automatic model download and management from HuggingFace Hub (GGUF format)
- ✅ Interactive CLI chat interface
- ✅ Production-quality modular architecture
- ✅ Comprehensive unit testing (88% coverage)
- ✅ Clean installation and uninstallation process
- ✅ Support for Qwen2.5-Coder-7B-Instruct-GGUF (default model)
- ✅ Configurable inference parameters
- ✅ Independent server management (start/stop/status/restart)
- ✅ OpenAI-compatible API interface

### Future Phases (Planned)
- 🔮 GUI interface
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

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- OpenAI Python client (for llama-server compatibility)
- HuggingFace Hub (for model downloads)
- Rich (CLI interface)
- Pytest and coverage tools (for testing)

## Usage

### Quick Start

```bash
# Activate virtual environment
source llf_venv/bin/activate

# Install LLF command (one-time setup)
pip install -e .

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
llf download

# Download a specific model
llf download --model "mistralai/Mistral-7B-Instruct-v0.2"

# List downloaded models
llf list

# Show model information
llf info

# Set custom download directory
llf -d /custom/path download

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

# Start server with a specific model
llf server start --model "mistralai/Mistral-7B-Instruct-v0.2"

# Check server status
llf server status

# Stop the server
llf server stop

# Restart the server
llf server restart
```

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
- `--model NAME` - Model name from HuggingFace Hub
- `--force` - Force re-download even if model exists
- `--token TOKEN` - HuggingFace API token for private models

For detailed usage information, see [USAGE.md](USAGE.md)

## Configuration

### Default Settings

LLF uses sensible defaults:
- **Model:** Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
- **GGUF File:** qwen2.5-coder-7b-instruct-q4_k_m.gguf (Q4_K_M quantization)
- **Model Directory:** `./models/`
- **Cache Directory:** `./.cache/`
- **llama-server Path:** `../llama.cpp/build/bin/llama-server`
- **Temperature:** 0.7
- **Max Tokens:** 2048

### Custom Configuration

Create a `config.json` file:

```json
{
  "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
  "gguf_file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
  "llama_server_path": "/custom/path/to/llama-server",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "log_level": "INFO"
}
```

Use it: `python -m llf.cli --config config.json`

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

- No GUI interface
- No API server exposure
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

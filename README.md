# Local LLM Framework (LLF)

A flexible Python framework designed to run Large Language Models (LLMs) locally on your computer using vLLM as the runtime engine.

## Overview

Local LLM Framework (LLF) provides maximum flexibility, zero token costs, and full local control while exposing LLMs through multiple access methods. Phase 1 focuses exclusively on CLI-based interaction with plans for future expansion into API servers, GUIs, and advanced features.

**Current Version:** 0.1.0 (Phase 1)

## Features

### Phase 1 (Current)
- ✅ Run modern LLMs locally using vLLM
- ✅ Automatic model download and management from HuggingFace Hub
- ✅ Interactive CLI chat interface
- ✅ Production-quality modular architecture
- ✅ Comprehensive unit testing (90% coverage)
- ✅ Clean installation and uninstallation process
- ✅ Support for Qwen3-Coder-30B-A3B-Instruct (default model)
- ✅ Configurable inference parameters

### Future Phases (Planned)
- 🔮 GUI interface
- 🔮 OpenAI-compatible API server
- 🔮 Voice input/output
- 🔮 Internet access capabilities
- 🔮 Tool execution (commands, filesystem access)
- 🔮 Multi-model switching via configuration

## System Requirements

### Hardware
- **RAM:** Minimum 32GB recommended (default 30B model requires ~20GB+ VRAM/RAM)
- **Storage:** 50GB+ free space for models
- **GPU:** Optional but recommended (CUDA-compatible for best performance)
  - CPU-only mode supported but slower

### Software
- **Python:** 3.11 or higher
- **Operating System:**
  - macOS (Apple Silicon or Intel)
  - Linux (Ubuntu 20.04+, other distributions)
  - Windows (via WSL2 recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd local_llm_framework
```

### 2. Create Virtual Environment

**IMPORTANT:** LLF must be installed and run inside a Python virtual environment.

```bash
# Create virtual environment
python -m venv llf_venv

# Activate virtual environment
source llf_venv/bin/activate  # On macOS/Linux
# OR
llf_venv\Scripts\activate  # On Windows
```

### 3. Verify Virtual Environment is Active

```bash
# Should show path to llf_venv
echo $VIRTUAL_ENV
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- vLLM (LLM runtime engine)
- OpenAI Python client (for vLLM compatibility)
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
- **Model:** Qwen/Qwen3-Coder-30B-A3B-Instruct
- **Model Directory:** `./models/`
- **Cache Directory:** `./.cache/`
- **Temperature:** 0.7
- **Max Tokens:** 2048

### Custom Configuration

Create a `config.json` file:

```json
{
  "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
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
│   ├── llm_runtime.py         # vLLM runtime management
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
- Automatic model management
- vLLM integration
- Comprehensive testing

---

**Built for the local LLM community**

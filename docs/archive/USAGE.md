# LLF Command-Line Usage Guide

This guide covers all command-line options and usage patterns for the Local LLM Framework (LLF).

## Installation Methods

### Method 1: Using the Standalone Script (Quick & Easy)

After activating your virtual environment, you can run LLF directly from the bin directory:

```bash
source llf_venv/bin/activate
./bin/llf -h
```

You can also add it to your PATH:

```bash
export PATH="$PWD/bin:$PATH"
llf -h
```

### Method 2: Installing as a Package (Recommended)

Install LLF as a package to get the `llf` command globally available in your virtual environment:

```bash
source llf_venv/bin/activate
pip install -e .

# Now you can use 'llf' from anywhere
llf -h
```

### Method 3: Using Python Module (Always Works)

```bash
python -m llf.cli -h
```

## Getting Help

### General Help

```bash
llf -h
llf --help
```

**Output:**
```
usage: llf [-h] [-d PATH] [-c FILE] [--cache-dir PATH] [--log-level LEVEL]
           [--version]
           COMMAND ...

Local LLM Framework - Run LLMs locally with llama.cpp

positional arguments:
  COMMAND               Available commands (default: chat)
    chat                Start interactive chat with LLM
    download            Download a model from HuggingFace Hub (GGUF format)
    list                List all downloaded models
    info                Show detailed model information
    server              Manage llama-server

options:
  -h, --help            show this help message and exit
  -d PATH, --download-dir PATH
                        Directory for downloading and storing models (default: ./models/)
  -c FILE, --config FILE
                        Path to configuration JSON file
  --cache-dir PATH      Directory for model cache (default: ./.cache/)
  --log-level LEVEL     Set logging level (default: INFO)
  --version             show program's version number and exit

Examples:
  # Chat commands
  llf                              Start interactive chat (default)
  llf chat                         Start interactive chat (prompts to start server if not running)
  llf chat --auto-start-server     Auto-start server if not running (no prompt)
  llf chat --no-server-start       Exit with error if server not running

  # Server management
  llf server start                 Start llama-server (stays in foreground)
  llf server start --daemon        Start server in background
  llf server status                Check if server is running
  llf server stop                  Stop running server

  # Model management (GGUF format)
  llf download                     Download default GGUF model
  llf download --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf list                         List downloaded models
  llf info                         Show model information

  # Configuration
  llf -d /custom/path              Set custom download directory
  llf --log-level DEBUG            Enable debug logging
```

### Command-Specific Help

```bash
llf chat -h
llf model -h
llf server -h
llf gui -h
llf datastore -h
llf module -h
llf tool -h
```

## Global Options

These options can be used with any command.

### `-d, --download-dir PATH`

Specify where models should be downloaded and stored.

```bash
# Store models in a custom directory
llf -d /mnt/storage/models download

# Use custom directory for chat
llf -d /mnt/storage/models chat
```

### `-c, --config FILE`

Load configuration from a JSON file.

```bash
llf -c configs/my_config.json chat
```

**Example configs/config.json:**
```json
{
  "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
  "model_dir": "/custom/models",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "log_level": "INFO"
}
```

### `--cache-dir PATH`

Specify the HuggingFace cache directory.

```bash
llf --cache-dir /tmp/hf_cache download
```

### `--log-level LEVEL`

Set the logging verbosity level.

```bash
# Show only errors
llf --log-level ERROR chat

# Show debug information
llf --log-level DEBUG download

# Options: DEBUG, INFO, WARNING, ERROR
```

### `--version`

Display the LLF version.

```bash
llf --version
# Output: llf 0.1.0 (Phase 1)
```

## Commands

### 1. GUI Command

Start the web-based GUI interface for easy management and chat.

```bash
# Start GUI (opens in browser automatically)
llf gui
llf gui start

# Start in background (daemon mode)
llf gui start --daemon

# Start on custom port
llf gui start --port 8080

# Make GUI accessible on local network
llf gui start --share

# Start with authentication
llf gui start --key MY_SECRET_KEY_123

# Combine network access with authentication
llf gui start --share --key MY_SECRET_KEY_123

# Start without opening browser
llf gui start --no-browser

# Stop GUI daemon
llf gui stop

# Check GUI status
llf gui status
```

**GUI Features:**

1. **💬 Chat Tab**
   - Interactive conversation with streaming responses
   - Multiline input support
   - Clear chat and shutdown GUI buttons

2. **🖥️ Server Tab**
   - Server status with placeholder text ("Click on Check Status")
   - Start/stop/restart controls with visual status indicators
   - Real-time status updates (✅ running, ⭕ stopped, ❌ error)

3. **📦 Models Tab**
   - **Your Models:**
     - Auto-loads model list on startup
     - Radio selection with scroll support
     - "Default" option + all downloaded models
     - Click model to view details
     - Refresh List button
   - **Download Model:**
     - Toggle between HuggingFace and URL methods
     - Real-time progress with visual indicators (📥⏳🔄⚠️🎉✅)
     - Status messages during and after download

4. **⚙️ Configuration Tab**
   - **Config.json:**
     - Auto-loads on startup
     - JSON editor with syntax highlighting
     - Save with validation
     - Reload with status feedback
     - Create backups
   - **Config_prompt.json:**
     - Auto-loads on startup
     - Save/reload with status messages
     - Backup support

5. **📚 Data Stores Tab** (Future: RAG features)
6. **🔌 Modules Tab** (Future: extensions)
7. **🛠️ Tools Tab** (Future: LLM capabilities)

**Network Access:**
- Default: Only accessible on localhost (127.0.0.1)
- `--share`: Makes GUI accessible on local network (0.0.0.0)
- `--key`: Adds authentication protection (recommended with --share)

**GUI Improvements in v0.2.0:**
- Auto-loading of configs and models on startup
- Placeholder text for empty sections
- Real-time download progress
- Dual download methods (HuggingFace + URL)
- Status feedback for all operations
- Improved button layout and alignment

### 2. Chat (Default Command)

Start an interactive chat session with the LLM.

```bash
# These are all equivalent
llf
llf chat
python -m llf.cli
```

**Interactive Commands (while in chat):**
- Type your message and press Enter to chat
- `help` - Show help information
- `info` - Show model and system information
- `clear` - Clear the screen
- `exit` or `quit` - Exit the application
- `Ctrl+C` - Force exit

**Example Session:**
```bash
$ llf

Welcome to LLF!
Model: Qwen/Qwen3-Coder-30B-A3B-Instruct
...

You: Hello! Can you help me write a Python function?
Assistant: Of course! I'd be happy to help you write a Python function...

You: exit
Goodbye!
```

### 3. Model Command

Manage model downloads and information.

```bash
# Download the default model
llf model download

# Download a specific HuggingFace model
llf model download --huggingface-model "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"

# Download from direct URL
llf model download --url "https://example.com/model.gguf" --name "my-model"

# Force re-download
llf model download --force

# Download with authentication token (for private models)
llf model download --huggingface-model "private/model" --token "hf_xxxxxxxxxxxxx"

# Download to custom directory
llf -d /mnt/storage/models model download

# List all downloaded models
llf model list

# Show default model information
llf model info

# Show specific model information
llf model info --huggingface-model "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
```

**Download Options:**
- `--huggingface-model NAME` - HuggingFace model identifier
- `--url URL --name NAME` - Download from direct URL (both required together)
- `--force` - Re-download even if model exists
- `--token TOKEN` - HuggingFace API token for private models

**Example Output (llf model list):**
```
Downloaded Models:
  ✓ Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  ✓ mistralai/Mistral-7B-Instruct-v0.2
```

**Example Output (llf model info):**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Model Info                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Name: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
Path: /path/to/models/Qwen2.5-Coder-7B-Instruct-GGUF
Downloaded: Yes
GGUF File: qwen2.5-coder-7b-instruct-q4_k_m.gguf
```

### 4. Server Command

Manage the llama-server inference server independently. LLF runs a local server on `localhost:8000` that can be controlled separately from the chat interface.

**Basic Server Management:**

```bash
# Start server in foreground (blocks terminal)
llf server start

# Start server in background (daemon mode)
llf server start --daemon

# Check server status
llf server status

# Stop the server
llf server stop

# Restart the server
llf server restart
```

**Server with Model Selection:**

```bash
# Start server with specific model
llf server start --model "mistralai/Mistral-7B-Instruct-v0.2"

# Start in background with specific model
llf server start --daemon --model "Qwen/Qwen3-Coder-30B-A3B-Instruct"
```

**Chat Command with Server Control:**

The chat command provides flags to control server behavior:

```bash
# Default: prompts user if server is not running
llf chat

# Auto-start server if not running (no prompt)
llf chat --auto-start-server

# Exit with error if server not running (don't start)
llf chat --no-server-start

# Combine with model selection
llf chat --model "mistralai/Mistral-7B-Instruct-v0.2" --auto-start-server
```

**Example Output:**

```bash
$ llf server status
✗ Server is not running

$ llf server start --daemon
Starting llama-server with model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF...
This may take a minute or two...
✓ Server started successfully on http://127.0.0.1:8000
Server is running in daemon mode.
Use 'llf server stop' to stop the server.

$ llf server status
✓ Server is running on http://127.0.0.1:8000
Model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

$ llf chat --no-server-start
[Connects to existing server without prompting]

$ llf server stop
Stopping server...
✓ Server stopped successfully
```

**Typical Workflows:**

**Workflow 1: Long-Running Server**
```bash
# Start server once
llf server start --daemon

# Run multiple chat sessions
llf chat --no-server-start
# ... exit and return later ...
llf chat --no-server-start

# Stop when done
llf server stop
```

**Workflow 2: Quick Session**
```bash
# Let chat command handle everything
llf chat --auto-start-server
# ... chat session ...
# Server automatically stops on exit
```

**Workflow 3: Development/Testing**
```bash
# Start server in foreground to see logs
llf server start

# In another terminal, run commands
llf chat --no-server-start

# Ctrl+C in first terminal stops server
```

### 5. Data Store Command (Placeholder)

Manage data stores for RAG (Retrieval-Augmented Generation). These commands are placeholders for future functionality.

```bash
# List all data stores
llf datastore list

# List only attached data stores
llf datastore list --attached

# Attach a data store
llf datastore attach

# Detach a data store
llf datastore detach

# Show data store information
llf datastore info DATA_STORE_NAME
```

**Purpose:** Will support managing data sources that provide context to LLM queries through RAG.

**Directory:** `data_stores/` (for storing RAG data files)

### 6. Module Command (Placeholder)

Manage modules that extend engagement between the LLM and user. These commands are placeholders for future functionality.

```bash
# List all modules
llf module list

# List only enabled modules
llf module list --enabled

# Enable a module
llf module enable

# Disable a module
llf module disable

# Show module information
llf module info MODULE_NAME
```

**Purpose:** Will support extensions that enhance interaction capabilities (e.g., text-to-speech, speech-to-text).

**Directory:** `modules/` (for storing module files)

### 7. Tool Command (Placeholder)

Manage tools that extend the LLM's capabilities. These commands are placeholders for future functionality.

```bash
# List all tools
llf tool list

# List only enabled tools
llf tool list --enabled

# Enable a tool
llf tool enable TOOL_NAME

# Disable a tool
llf tool disable TOOL_NAME

# Show tool information
llf tool info TOOL_NAME
```

**Purpose:** Will support extensions that enhance LLM functionality (e.g., internet search, code execution, file operations).

**Directory:** `tools/` (for storing tool files)

## Common Use Cases

### First-Time Setup

```bash
# 1. Activate virtual environment
source llf_venv/bin/activate

# 2. Install LLF (optional but recommended)
pip install -e .

# 3. Download the default model
llf download

# 4. Start chatting
llf
```

### Using a Custom Model Directory

If you have limited space on your main drive:

```bash
# Download to external drive
llf -d /mnt/external/llm_models download

# Use the model from external drive
llf -d /mnt/external/llm_models chat
```

### Working with Multiple Models

```bash
# Download multiple models
llf download --model "Qwen/Qwen3-Coder-30B-A3B-Instruct"
llf download --model "mistralai/Mistral-7B-Instruct-v0.2"

# List all downloaded models
llf list

# Get info about a specific model
llf info --model "mistralai/Mistral-7B-Instruct-v0.2"
```

### Debugging Issues

```bash
# Enable debug logging
llf --log-level DEBUG download

# Check if model is properly downloaded
llf info

# Verify with verbose output
llf --log-level DEBUG chat
```

### Using Configuration Files

Create a `configs/config.json`:

```json
{
  "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
  "model_dir": "/mnt/storage/models",
  "cache_dir": "/mnt/storage/cache",
  "inference_params": {
    "temperature": 0.5,
    "max_tokens": 4096,
    "top_p": 0.95
  },
  "log_level": "DEBUG"
}
```

Then use it:

```bash
llf -c configs/config.json chat
```

## Environment Variables

You can also use environment variables for some settings:

```bash
# Set HuggingFace token
export HUGGING_FACE_HUB_TOKEN="hf_xxxxxxxxxxxxx"

# Download private model (token automatically used)
llf download --model "private/model"
```

## Exit Codes

LLF uses standard exit codes:

- `0` - Success
- `1` - Error occurred

Use in scripts:

```bash
llf download && llf chat || echo "Failed!"
```

## Tips & Tricks

### Create an Alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias llf-chat='cd /path/to/local_llm_framework && source llf_venv/bin/activate && llf'
```

### Use with Different Python Versions

```bash
python3.11 -m venv llf_venv
source llf_venv/bin/activate
pip install -r requirements.txt
llf chat
```

### Quick Model Switch

```bash
# Create different config files
llf -c configs/qwen_config.json chat
llf -c configs/mistral_config.json chat
```

### Batch Operations

```bash
# Download multiple models in sequence
for model in "Qwen/Qwen3-Coder-30B-A3B-Instruct" "mistralai/Mistral-7B-Instruct-v0.2"; do
  llf download --model "$model"
done
```

## Troubleshooting

### Command Not Found

```bash
# Make sure virtual environment is activated
source llf_venv/bin/activate

# If still not found, use:
python -m llf.cli -h

# Or install the package:
pip install -e .
```

### Permission Denied

```bash
# Make sure the script is executable
chmod +x bin/llf
```

### Module Not Found

```bash
# Ensure you're in the virtual environment
which python
# Should show: /path/to/llf_venv/bin/python

# Reinstall dependencies if needed
pip install -r requirements.txt
```

## Advanced Usage

### Programmatic Usage

You can also import and use LLF in your Python scripts:

```python
from llf.config import Config
from llf.model_manager import ModelManager
from llf.llm_runtime import LLMRuntime

# Create config
config = Config()

# Download model
manager = ModelManager(config)
manager.download_model()

# Run inference
runtime = LLMRuntime(config, manager)
runtime.start_server()
response = runtime.chat([{"role": "user", "content": "Hello!"}])
print(response)
runtime.stop_server()
```

---

For more information, see the main [README.md](README.md) or visit the project repository.

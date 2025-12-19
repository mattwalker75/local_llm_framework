# LLF Configuration Guide

## Overview

The Local LLM Framework (LLF) uses a JSON configuration file for managing all settings. This allows you to easily customize the framework without modifying code.

## Configuration File Location

The framework automatically looks for configuration files at:
```
<project_root>/configs/config.json        # Infrastructure configuration
<project_root>/configs/config_prompt.json  # Prompt configuration (optional)
```

If these files don't exist, LLF will use built-in default values.

**Configuration backups** are automatically saved to:
```
<project_root>/configs/backups/
```

## Getting Started

1. **Copy the example configuration:**
   ```bash
   cp configs/config_examples/config.local.example configs/config.json
   ```

2. **Edit `configs/config.json`** to customize your settings (see below for options)

3. **Run LLF** - it will automatically load your configuration:
   ```bash
   llf chat
   ```

## Configuration Options

### Model Settings

- **`model_name`**: HuggingFace repository name for the model
  - Example: `"Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"`

- **`model_alias`**: Short alias for the model (used internally)
  - Example: `"qwen2.5-coder"`

- **`gguf_file`**: Specific GGUF quantized model file to use
  - Example: `"qwen2.5-coder-7b-instruct-q4_k_m.gguf"`

### Path Settings

All paths can be absolute or relative to the project root.

- **`model_dir`**: Directory where models are stored
  - Default: `"models"`
  - Example: `"/absolute/path/to/models"` or `"models"`

- **`cache_dir`**: Directory for caching
  - Default: `".cache"`

- **`llama_server_path`**: Path to llama-server executable
  - Default: `"../llama.cpp/build/bin/llama-server"`
  - Example: `"/usr/local/bin/llama-server"`

### Local Server Settings

These settings configure the local llama-server when you start it. Only needed for local LLM.

- **`server_host`**: Host address to bind the local server to
  - Default: `"127.0.0.1"`
  - Change to `"0.0.0.0"` to allow network access

- **`server_port`**: Port number for the local server
  - Default: `8000`
  - Change if port 8000 is already in use

- **`server_params`** (Optional): Additional parameters to pass to llama-server
  - Format: Dictionary of key-value pairs
  - These are passed directly to the llama-server CLI as `--key value`
  - **To see all available options, run:** `../llama.cpp/build/bin/llama-server -h`

  **Common examples:**
  ```json
  "server_params": {
    "ctx-size": 8192,        // Context window size (default ~2048)
    "n-gpu-layers": 35,      // GPU layers (0=CPU only, -1=all layers)
    "threads": 8,            // CPU threads for inference
    "batch-size": 512,       // Batch size for prompt processing
    "flash-attn": true       // Enable flash attention (if supported)
  }
  ```

  **This section is completely optional.** If omitted, llama-server uses its default values.

**Note**: `server_host` and `server_port` should match the URL in `api_base_url` for local usage.

### API Settings

These settings control which LLM service to use. Simply change the URL to switch between local and external LLMs.

- **`api_base_url`**: Base URL for the LLM API
  - **Local server**: `"http://127.0.0.1:8000/v1"` (default)
  - **OpenAI**: `"https://api.openai.com/v1"`
  - **Custom API**: `"https://your-api.com/v1"`
  - **To switch**: Just comment out one URL and uncomment another

- **`api_key`**: API key for authentication
  - **Local server**: `"EMPTY"` (no authentication needed)
  - **OpenAI**: `"sk-proj-your-api-key-here"`
  - **Other APIs**: Your actual API key
  - **Security**: Keep this secure! Don't commit to git (already in .gitignore)

### Logging Settings

- **`log_level`**: Controls logging verbosity
  - Options: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
  - Default: `"INFO"`
  - Example: `"ERROR"` (only show errors)

### Inference Parameters

The `inference_params` object controls how the LLM generates responses:

- **`temperature`**: Controls randomness (0.0-2.0)
  - Lower = more deterministic, Higher = more creative
  - Default: `0.7`

- **`max_tokens`**: Maximum tokens in response
  - Default: `2048`

- **`top_p`**: Nucleus sampling parameter (0.0-1.0)
  - Default: `0.9`

- **`top_k`**: Top-k sampling parameter
  - Default: `50`

- **`repetition_penalty`**: Penalty for repeating tokens (1.0+)
  - Default: `1.1`

## Example Configurations

### Local LLM (Default)

```json
{
  "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
  "model_alias": "qwen2.5-coder",
  "gguf_file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
  "model_dir": "models",
  "cache_dir": ".cache",
  "llama_server_path": "../llama.cpp/build/bin/llama-server",
  "server_host": "127.0.0.1",
  "server_port": 8000,
  "api_base_url": "http://127.0.0.1:8000/v1",
  "api_key": "EMPTY",
  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1
  }
}
```

### Switch to OpenAI

Just change the `api_base_url`, `model_name`, and `api_key`:

```json
{
  "model_name": "gpt-4",
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "sk-proj-YOUR-OPENAI-API-KEY",
  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

### Easy Switching Example

Keep both configurations in your config.json and comment/uncomment as needed:

```json
{
  "_comment": "Local LLM - uncomment these to use local server",
  "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
  "api_base_url": "http://127.0.0.1:8000/v1",
  "api_key": "EMPTY",

  "_comment": "OpenAI - uncomment these to use ChatGPT",
  "_model_name": "gpt-4",
  "_api_base_url": "https://api.openai.com/v1",
  "_api_key": "sk-proj-YOUR-KEY-HERE",

  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

## Overriding Configuration

You can override configuration values in two ways:

### 1. Command-line Arguments

Some settings can be overridden via CLI:

```bash
# Override model
llf chat --model "different/model"

# Override log level
llf --log-level DEBUG chat

# Use custom config file
llf --config /path/to/custom_config.json chat
```

### 2. Custom Configuration File

Specify a different config file:

```bash
llf --config ~/.llf/my_config.json chat
```

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. Built-in defaults (in code)
2. `config.json` file (if exists)
3. Custom config file (if specified with `--config`)
4. Command-line arguments (if provided)

## Common Configuration Tasks

### Use a Different Model

Edit `config.json`:
```json
{
  "model_name": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
  "gguf_file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
}
```

### Change Server Port

Edit `config.json`:
```json
{
  "server_port": 9000
}
```

### Reduce Logging Verbosity

Edit `config.json`:
```json
{
  "log_level": "ERROR"
}
```

### Adjust Response Creativity

Edit `config.json`:
```json
{
  "inference_params": {
    "temperature": 1.0,
    "top_p": 0.95
  }
}
```

### Switch to External LLM API (OpenAI)

**Recommended workflow for switching to external LLM:**

1. **Update the API endpoint** (don't worry about model_name yet):
   ```json
   {
     "llm_endpoint": {
       "api_base_url": "https://api.openai.com/v1",
       "api_key": "sk-proj-YOUR-API-KEY-HERE",
       "model_name": ""
     }
   }
   ```

2. **List available models** from the endpoint:
   ```bash
   llf server list_models
   ```
   This will query the endpoint and display all available models in a table.

3. **Update the model_name** with your chosen model:
   ```json
   {
     "llm_endpoint": {
       "api_base_url": "https://api.openai.com/v1",
       "api_key": "sk-proj-YOUR-API-KEY-HERE",
       "model_name": "gpt-4"
     }
   }
   ```

4. **Start using LLF** normally:
   ```bash
   llf chat
   # All commands work the same!
   llf chat --cli "What is 2+2?"
   cat file.txt | llf chat --cli "Summarize this"
   ```

**To switch back to local**: Just change the `llm_endpoint` section back to local settings:
```json
{
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
  }
}
```

**Important notes**:
- Use `llf server list_models` to discover available models from any OpenAI-compatible endpoint
- Keep your API key secure - `config.json` is already in .gitignore
- Server commands (`llf server start/stop`) only needed for local LLM
- `llf server list_models` works with both local and external endpoints

## Troubleshooting

### Configuration Not Loading

1. Check that `config.json` exists in the project root
2. Validate JSON syntax (use `cat config.json | python -m json.tool`)
3. Check file permissions

### Invalid Configuration Values

If LLF fails to start:
1. Compare your `config.json` with `config.json.example`
2. Check for typos in key names
3. Ensure paths are valid and accessible
4. Verify port numbers are in valid range (1-65535)

### Resetting to Defaults

Simply rename or delete `config.json`:
```bash
mv config.json config.json.backup
```

LLF will use built-in defaults.

## Advanced Usage

### Save Current Configuration

You can save your current runtime configuration:

```python
from llf.config import get_config

config = get_config()
config.save_to_file("my_config.json")
```

### Programmatic Configuration

```python
from pathlib import Path
from llf.config import Config

# Load specific config
config = Config(Path("custom_config.json"))

# Modify and save
config.temperature = 0.5
config.save_to_file("modified_config.json")
```

## Notes

- `config.json` is ignored by git (in `.gitignore`)
- Use `config.json.example` as a template for version control
- Relative paths in config are resolved from project root
- Changes to `config.json` require restarting LLF to take effect

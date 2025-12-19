# LLF Configuration Guide

## Overview

The Local LLM Framework (LLF) uses a dual configuration system with two separate JSON files:

1. **Infrastructure Configuration** (`configs/config.json`): Server settings, API endpoints, model paths, inference parameters
2. **Prompt Configuration** (`configs/config_prompt.json`): System prompts, conversation format, message injection

This separation allows you to:
- Swap infrastructure settings without affecting prompts
- Share prompt templates across different setups
- Version control prompts separately from credentials

## Configuration File Locations

The framework automatically looks for configuration files at:
```
<project_root>/configs/config.json        # Infrastructure configuration
<project_root>/configs/config_prompt.json  # Prompt configuration
```

If these files don't exist, LLF will use built-in default values.

**Configuration backups** are automatically saved to:
```
<project_root>/configs/backups/config_YYYYMMDD_HHMMSS.json
<project_root>/configs/backups/config_prompt_YYYYMMDD_HHMMSS.json
```

Backups are created when you save configurations through the GUI.

## Getting Started

### Infrastructure Configuration

1. **Copy the example configuration:**
   ```bash
   cp configs/config_examples/config.local.example configs/config.json
   ```

2. **Edit `configs/config.json`** to customize your settings (see below for options)

3. **Run LLF** - it will automatically load your configuration:
   ```bash
   llf chat
   ```

### Prompt Configuration

1. **Copy the example prompt configuration:**
   ```bash
   cp configs/config_examples/config_prompt.example configs/config_prompt.json
   ```

2. **Edit `configs/config_prompt.json`** to customize prompts and conversation format

3. **Changes take effect** on the next chat session or GUI reload

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

- **`healthcheck_interval`**: Seconds between health checks during server startup
  - Default: `2.0`
  - Controls how frequently LLF checks if the server is ready during startup
  - Reduce to `1.0` for faster startup (checks more frequently)
  - Increase to `3.0` or higher if server takes longer to initialize
  - Only applies to local llama-server (not used with external APIs)

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
  "healthcheck_interval": 2.0,
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

## Prompt Configuration (`config_prompt.json`)

The prompt configuration file controls how the LLM receives and formats messages. This is separate from infrastructure configuration to allow easy sharing of prompt templates.

### Prompt Configuration Structure

```json
{
  "system_prompt": "You are a helpful AI assistant...",
  "conversation_format": {
    "user_prefix": "User: ",
    "assistant_prefix": "Assistant: ",
    "system_prefix": "System: ",
    "message_separator": "\n\n"
  },
  "injected_messages": [
    {
      "role": "system",
      "content": "Always be concise and helpful.",
      "position": "start"
    }
  ]
}
```

### Configuration Fields

#### `system_prompt` (string)

The main system prompt that sets the LLM's behavior and personality.

**Example:**
```json
{
  "system_prompt": "You are a helpful coding assistant specialized in Python. Provide clear, concise code examples with explanations."
}
```

#### `conversation_format` (object)

Controls how messages are formatted in the conversation.

**Fields:**
- `user_prefix`: Text before user messages (default: `"User: "`)
- `assistant_prefix`: Text before assistant messages (default: `"Assistant: "`)
- `system_prefix`: Text before system messages (default: `"System: "`)
- `message_separator`: Text between messages (default: `"\n\n"`)

**Example:**
```json
{
  "conversation_format": {
    "user_prefix": "Human: ",
    "assistant_prefix": "AI: ",
    "system_prefix": "[SYSTEM]: ",
    "message_separator": "\n---\n"
  }
}
```

#### `injected_messages` (array)

Messages automatically added to conversations. Useful for context or behavior modification.

**Fields per message:**
- `role`: Message role (`"system"`, `"user"`, or `"assistant"`)
- `content`: Message content
- `position`: Where to inject (`"start"` or `"end"`)

**Example:**
```json
{
  "injected_messages": [
    {
      "role": "system",
      "content": "Always format code with proper syntax highlighting.",
      "position": "start"
    },
    {
      "role": "system",
      "content": "Provide sources when citing information.",
      "position": "start"
    }
  ]
}
```

### Example Configurations

#### Default Configuration

```json
{
  "system_prompt": "You are a helpful, harmless, and honest AI assistant.",
  "conversation_format": {
    "user_prefix": "User: ",
    "assistant_prefix": "Assistant: ",
    "system_prefix": "System: ",
    "message_separator": "\n\n"
  },
  "injected_messages": []
}
```

#### Coding Assistant Configuration

```json
{
  "system_prompt": "You are an expert programming assistant. Provide clear, well-documented code with explanations. Focus on best practices and maintainability.",
  "conversation_format": {
    "user_prefix": "Developer: ",
    "assistant_prefix": "AI: ",
    "system_prefix": "[SYS]: ",
    "message_separator": "\n\n"
  },
  "injected_messages": [
    {
      "role": "system",
      "content": "Always include error handling in code examples.",
      "position": "start"
    },
    {
      "role": "system",
      "content": "Explain your reasoning before providing code.",
      "position": "start"
    }
  ]
}
```

#### Creative Writing Assistant

```json
{
  "system_prompt": "You are a creative writing assistant. Help users develop stories, characters, and narratives with vivid descriptions and engaging dialogue.",
  "conversation_format": {
    "user_prefix": "Writer: ",
    "assistant_prefix": "Muse: ",
    "system_prefix": "",
    "message_separator": "\n\n---\n\n"
  },
  "injected_messages": [
    {
      "role": "system",
      "content": "Encourage creativity and unique perspectives.",
      "position": "start"
    }
  ]
}
```

### Managing Prompt Configurations

#### Via GUI

1. Open the GUI: `llf gui`
2. Navigate to **Config (Prompts)** tab
3. Edit the JSON directly
4. Click **Save Config** to apply changes
5. Click **Create Backup** to save a timestamped backup

#### Via Command Line

```bash
# Edit directly
nano configs/config_prompt.json

# Or use your preferred editor
code configs/config_prompt.json
```

#### Backup and Restore

Backups are automatically created in `configs/backups/` with timestamps:

```bash
# List backups
ls -lh configs/backups/config_prompt_*.json

# Restore a backup
cp configs/backups/config_prompt_20251218_103758.json configs/config_prompt.json

# Create manual backup
cp configs/config_prompt.json configs/backups/config_prompt_$(date +%Y%m%d_%H%M%S).json
```

### Tips for Prompt Configuration

1. **Be Specific**: Clear system prompts lead to better responses
2. **Test Changes**: Try different prompts to find what works best
3. **Use Injected Messages**: Add consistent context without repeating in every conversation
4. **Keep Backups**: Experiment freely knowing you can restore previous versions
5. **Version Control**: Consider keeping prompt templates in version control (without credentials)

## Notes

- `config.json` and `config_prompt.json` are ignored by git (in `.gitignore`)
- Use example files as templates for version control
- Relative paths in config are resolved from project root
- Infrastructure changes require restarting LLF
- Prompt changes take effect on next conversation or GUI reload
- Backups are created automatically when saving through GUI

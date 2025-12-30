# Configuration Guide: config.json

This document provides a comprehensive guide to configuring the Local LLM Framework via the `configs/config.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Single Local LLM Server Configuration](#single-local-llm-server-configuration)
4. [Multiple Local LLM Server Configuration](#multiple-local-llm-server-configuration)
5. [OpenAI (ChatGPT) Configuration](#openai-chatgpt-configuration)
6. [Anthropic (Claude) Configuration](#anthropic-claude-configuration)
7. [Configuration Options Reference](#configuration-options-reference)
8. [Optional Parameters](#optional-parameters)
9. [Tool Execution Modes](#tool-execution-modes)

---

## Overview

The `config.json` file controls:
- LLM backend configuration (local or external API)
- Server management and connection settings
- Inference parameters for text generation
- Tool system configuration
- Logging and directory paths

The framework supports:
- **Local GGUF models** via llama.cpp server
- **Multiple local servers** running different models simultaneously
- **OpenAI API** (ChatGPT)
- **Anthropic API** (Claude)

---

## Configuration Structure

A configuration file contains the following top-level sections:

```json
{
  "local_llm_server": { ... },           // Single server (legacy)
  "local_llm_servers": [ ... ],          // Multiple servers (modern)
  "llm_endpoint": { ... },               // API connection settings
  "model_dir": "models",                 // Model storage directory
  "cache_dir": ".cache",                 // Cache directory
  "inference_params": { ... },           // Generation parameters
  "log_level": "ERROR"                   // Logging verbosity
}
```

---

## Single Local LLM Server Configuration

Use this configuration for running a single local GGUF model with llama-server.

### Basic Example

```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "healthcheck_interval": 2.0,
    "model_dir": "Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "gguf_file": "qwen3-coder-30b.gguf"
  },

  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "qwen3-coder",
    "tool_execution_mode": "dual_pass_write_only"
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1
  },

  "log_level": "ERROR"
}
```

### With Optional Server Parameters

You can add `server_params` to customize llama-server behavior:

```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "healthcheck_interval": 2.0,
    "model_dir": "Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "gguf_file": "qwen3-coder-30b.gguf",

    "server_params": {
      "ctx-size": "8192",
      "n-gpu-layers": "40",
      "threads": "8",
      "batch-size": "512"
    }
  },

  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "qwen3-coder"
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1
  },

  "log_level": "ERROR"
}
```

**Common `server_params` Options:**
- `ctx-size`: Context window size (e.g., "4096", "8192", "16384")
- `n-gpu-layers`: Number of layers to offload to GPU (e.g., "35", "40", "-1" for all)
- `threads`: CPU threads to use (e.g., "8", "12")
- `batch-size`: Batch size for prompt processing (e.g., "512", "1024")
- `n-predict`: Maximum tokens to generate (e.g., "2048")

---

## Multiple Local LLM Server Configuration

Run multiple local models simultaneously and switch between them.

### Multi-Server Example

```json
{
  "local_llm_servers": [
    {
      "name": "qwen-coder",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8000,
      "healthcheck_interval": 2.0,
      "auto_start": false,
      "model_dir": "Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF",
      "gguf_file": "qwen3-coder-30b.gguf",
      "server_params": {
        "ctx-size": "8192",
        "n-gpu-layers": "40",
        "threads": "8"
      }
    },
    {
      "name": "llama-3",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8001,
      "healthcheck_interval": 2.0,
      "auto_start": false,
      "model_dir": "Meta--Llama-3.1-8B-Instruct-GGUF",
      "gguf_file": "llama-3.1-8b-instruct-q5_k_m.gguf",
      "server_params": {
        "ctx-size": "4096",
        "n-gpu-layers": "35",
        "threads": "6"
      }
    },
    {
      "name": "qwen-small",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8002,
      "healthcheck_interval": 2.0,
      "auto_start": false,
      "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
      "gguf_file": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
      "server_params": {
        "ctx-size": "4096",
        "n-gpu-layers": "30"
      }
    }
  ],

  "llm_endpoint": {
    "default_local_server": "qwen-coder",
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF",
    "tool_execution_mode": "dual_pass_write_only"
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 50,
    "repetition_penalty": 1.1
  },

  "log_level": "ERROR"
}
```

### Multi-Server Management Commands

```bash
# List all configured servers
llf server list

# Start a specific server
llf server start qwen-coder

# Start with force flag (bypasses memory warnings)
llf server start llama-3 --force

# Stop a specific server
llf server stop qwen-coder

# Switch the default server
llf server switch llama-3

# Check server status
llf server status qwen-small
```

**Important Notes:**
- Each server must have a **unique port number**
- Each server must have a **unique name**
- The `default_local_server` determines which server the framework uses
- Running multiple large models simultaneously can exhaust system memory
- The framework warns before starting additional servers (use `--force` to bypass)

---

## OpenAI (ChatGPT) Configuration

Configure the framework to use OpenAI's cloud API instead of local models.

### OpenAI Example

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-OPENAI-API-KEY",
    "model_name": "gpt-4",
    "tool_execution_mode": "dual_pass_write_only"
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  },

  "log_level": "ERROR"
}
```

### OpenAI Configuration Steps

1. **Get API Key**: Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Replace API Key**: Set `api_key` to your key (starts with `sk-proj-` or `sk-`)
3. **Choose Model**: Select from available models:
   - `gpt-4o` - Latest GPT-4 Optimized
   - `gpt-4-turbo` - Fast GPT-4 variant
   - `gpt-4` - Standard GPT-4
   - `gpt-3.5-turbo` - Faster, cheaper model

### OpenAI-Specific Notes

- **No `server_params`**: Server parameters are only for local llama-server
- **Different inference parameters**: OpenAI supports `temperature` (0.0-2.0) and `top_p`, but **not** `top_k` or `repetition_penalty`
- **API costs**: OpenAI charges per token - monitor usage at platform.openai.com
- **XML format tool**: Disable `xml_format` tool (OpenAI has native JSON tool calling)

### OpenAI with Custom Parameters

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-OPENAI-API-KEY",
    "model_name": "gpt-4-turbo",
    "tool_execution_mode": "dual_pass_write_only",
    "tools": {
      "xml_format": "disable"
    }
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.8,
    "max_tokens": 4096,
    "top_p": 0.95,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  },

  "log_level": "ERROR"
}
```

---

## Anthropic (Claude) Configuration

Configure the framework to use Anthropic's Claude API.

### Anthropic Example

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.anthropic.com/v1",
    "api_key": "sk-ant-YOUR-ANTHROPIC-API-KEY",
    "model_name": "claude-3-opus-20240229",
    "tool_execution_mode": "dual_pass_write_only"
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  },

  "log_level": "ERROR"
}
```

### Anthropic Configuration Steps

1. **Get API Key**: Visit [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. **Replace API Key**: Set `api_key` to your key (starts with `sk-ant-`)
3. **Choose Model**: Select from available Claude models:
   - `claude-3-opus-20240229` - Most powerful Claude 3 model
   - `claude-3-sonnet-20240229` - Balanced performance and speed
   - `claude-3-haiku-20240307` - Fastest, most affordable Claude 3
   - `claude-2.1` - Previous generation

### Anthropic-Specific Notes

- **No `server_params`**: Server parameters are only for local llama-server
- **Different inference parameters**: Anthropic supports `temperature` (0.0-1.0) and `top_p`, but **not** `top_k` or `repetition_penalty`
- **Temperature range**: Unlike OpenAI (0.0-2.0), Anthropic uses 0.0-1.0
- **API costs**: Anthropic charges per token - monitor usage at console.anthropic.com
- **XML format tool**: Disable `xml_format` tool (Claude has native JSON tool calling)
- **Max tokens**: Claude 3 models support up to 4096 output tokens

### Anthropic with Custom Parameters

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.anthropic.com/v1",
    "api_key": "sk-ant-YOUR-ANTHROPIC-API-KEY",
    "model_name": "claude-3-sonnet-20240229",
    "tool_execution_mode": "dual_pass_write_only",
    "tools": {
      "xml_format": "disable"
    }
  },

  "model_dir": "models",
  "cache_dir": ".cache",

  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.9
  },

  "log_level": "ERROR"
}
```

---

## Configuration Options Reference

### Top-Level Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `local_llm_server` | Object | No | Single local server configuration (legacy) |
| `local_llm_servers` | Array | No | Multiple local server configurations |
| `llm_endpoint` | Object | Yes | API connection settings |
| `model_dir` | String | Yes | Directory for storing models (relative to project root) |
| `cache_dir` | String | Yes | Directory for caching (relative to project root) |
| `inference_params` | Object | Yes | LLM generation parameters |
| `log_level` | String | Yes | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### Local Server Options (`local_llm_server` or items in `local_llm_servers`)

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `name` | String | Yes (multi) | Unique name for the server (multi-server only) |
| `llama_server_path` | String | Yes | Path to llama-server executable |
| `server_host` | String | Yes | Server hostname (typically `127.0.0.1`) |
| `server_port` | Integer | Yes | Server port (must be unique per server) |
| `healthcheck_interval` | Float | Yes | Seconds between health checks (e.g., `2.0`) |
| `auto_start` | Boolean | No | Auto-start server on framework launch (default: `false`) |
| `model_dir` | String | Yes | Subdirectory within `models/` containing GGUF file |
| `gguf_file` | String | Yes | GGUF model filename |
| `server_params` | Object | No | Optional llama-server parameters (see below) |

### LLM Endpoint Options (`llm_endpoint`)

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `api_base_url` | String | Yes | API endpoint URL |
| `api_key` | String | Yes | API key (`EMPTY` for local servers) |
| `model_name` | String | Yes | Model identifier |
| `default_local_server` | String | No | Name of default local server (multi-server only) |
| `tool_execution_mode` | String | No | Tool execution mode (see below) |
| `tools` | Object | No | Tool configuration (e.g., `{"xml_format": "enable"}`) |

### Inference Parameters (`inference_params`)

| Parameter | Type | Range | Local | OpenAI | Anthropic | Description |
|-----------|------|-------|-------|--------|-----------|-------------|
| `temperature` | Float | 0.0-2.0 | ✓ | ✓ | ✓ (0.0-1.0) | Randomness in generation |
| `max_tokens` | Integer | 1-∞ | ✓ | ✓ | ✓ | Maximum tokens in response |
| `top_p` | Float | 0.0-1.0 | ✓ | ✓ | ✓ | Nucleus sampling threshold |
| `top_k` | Integer | 1-∞ | ✓ | ✗ | ✗ | Top-K sampling (local only) |
| `repetition_penalty` | Float | 1.0-∞ | ✓ | ✗ | ✗ | Penalty for repetition (local only) |
| `frequency_penalty` | Float | -2.0-2.0 | ✗ | ✓ | ✗ | Frequency penalty (OpenAI only) |
| `presence_penalty` | Float | -2.0-2.0 | ✗ | ✓ | ✗ | Presence penalty (OpenAI only) |

---

## Optional Parameters

### Server Parameters (`server_params`)

**Only applicable to local llama-server configurations.**

These parameters are passed directly to the llama-server executable. All values must be **strings**.

```json
"server_params": {
  "ctx-size": "8192",
  "n-gpu-layers": "40",
  "threads": "8",
  "batch-size": "512",
  "n-predict": "2048",
  "rope-freq-base": "10000",
  "rope-freq-scale": "1.0"
}
```

**Common Parameters:**

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `ctx-size` | Context window size | `"4096"`, `"8192"`, `"16384"` |
| `n-gpu-layers` | GPU layers to offload | `"35"`, `"40"`, `"-1"` (all) |
| `threads` | CPU threads | `"4"`, `"8"`, `"12"` |
| `batch-size` | Prompt processing batch | `"512"`, `"1024"` |
| `n-predict` | Max generation tokens | `"2048"`, `"4096"` |
| `rope-freq-base` | RoPE frequency base | `"10000"` |
| `rope-freq-scale` | RoPE frequency scale | `"1.0"`, `"0.5"` |

**Finding More Parameters:**

Run `llama-server --help` to see all available options.

### Inference Parameters (`inference_params`)

**Applicable to all configurations (local and external APIs).**

Control text generation behavior:

```json
"inference_params": {
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 0.9,
  "top_k": 50,
  "repetition_penalty": 1.1
}
```

**Parameter Details:**

- **`temperature`** (0.0-2.0): Controls randomness
  - `0.0`: Deterministic, always picks most likely token
  - `0.7`: Balanced creativity and coherence (recommended)
  - `1.5+`: Very creative, may lose coherence

- **`max_tokens`** (1-∞): Maximum tokens in response
  - Consider model's context window
  - OpenAI/Anthropic may have specific limits

- **`top_p`** (0.0-1.0): Nucleus sampling
  - `0.9`: Consider top 90% probability mass (recommended)
  - `1.0`: Consider all tokens
  - Alternative to temperature

- **`top_k`** (1-∞): Top-K sampling (local models only)
  - `50`: Consider top 50 tokens (recommended)
  - Limits token pool before top_p

- **`repetition_penalty`** (1.0-∞): Repetition penalty (local models only)
  - `1.0`: No penalty
  - `1.1`: Light penalty (recommended)
  - `1.5+`: Strong penalty, may harm coherence

---

## Tool Execution Modes

The `tool_execution_mode` option controls how the framework handles streaming and tool calling with memory.

### Available Modes

| Mode | Streaming During Tool Execution | Memory Writing | Best For |
|------|----------------------------------|----------------|----------|
| `single_pass` | ✓ Yes | After all tools complete | Fast response, simple flows |
| `dual_pass_write_only` | ✗ No (buffered) | After each tool, before final response | Best UX, recommended |
| `dual_pass_all` | ✗ No (buffered) | After each tool AND final response | Maximum memory detail |

### Mode Descriptions

**`single_pass`** (Default - Legacy)
- Streams response to user while tools are executing
- Writes to memory only after all tool calls complete
- Fastest perceived response time
- Memory doesn't include intermediate tool results

**`dual_pass_write_only`** (Recommended)
- Buffers response during tool execution
- Writes tool calls to memory immediately after each execution
- Final response starts after all tools complete
- Best user experience with complete memory tracking

**`dual_pass_all`**
- Buffers response during tool execution
- Writes both tool calls AND assistant response to memory
- Most complete memory tracking
- Two separate memory write operations

### Configuration Example

```json
"llm_endpoint": {
  "api_base_url": "http://127.0.0.1:8000/v1",
  "api_key": "EMPTY",
  "model_name": "qwen3-coder",
  "tool_execution_mode": "dual_pass_write_only"
}
```

### When to Use Each Mode

- **Use `single_pass`** if:
  - You want the fastest streaming response
  - Memory tracking of tool calls is not critical
  - You're using a fast local model

- **Use `dual_pass_write_only`** if:
  - You want complete memory of tool calls
  - You prefer to see final response after tools complete
  - You're using memory-based workflows (recommended)

- **Use `dual_pass_all`** if:
  - You need maximum memory detail
  - You want both tool calls and responses tracked
  - You're debugging or analyzing conversations

---

## Configuration Examples Summary

### Quick Reference: What Goes Where

| Configuration Type | Required Sections | Optional Sections |
|-------------------|-------------------|-------------------|
| **Single Local Server** | `local_llm_server`, `llm_endpoint`, `inference_params` | `server_params` |
| **Multi Local Servers** | `local_llm_servers`, `llm_endpoint`, `inference_params` | `server_params` per server |
| **OpenAI** | `llm_endpoint`, `inference_params` | None (no server sections) |
| **Anthropic** | `llm_endpoint`, `inference_params` | None (no server sections) |

### Example File Locations

Pre-configured examples are available in `configs/config_examples/`:
- [config.local.gguf.json](../configs/config_examples/config.local.gguf.json) - Single local server
- [config.multi-server.json](../configs/config_examples/config.multi-server.json) - Multiple local servers
- [config.openai.json](../configs/config_examples/config.openai.json) - OpenAI API
- [config.anthropic.json](../configs/config_examples/config.anthropic.json) - Anthropic API

---

## Tips and Best Practices

### Security

- **Never commit API keys** to version control
- Store API keys in environment variables or secure vaults
- Use `.gitignore` to exclude `config.json` if it contains secrets

### Performance

- **Local models**: Adjust `n-gpu-layers` based on your GPU VRAM
- **Context size**: Larger `ctx-size` uses more memory but handles longer conversations
- **Temperature**: Lower values (0.3-0.5) for factual tasks, higher (0.7-1.0) for creative tasks
- **Multi-server**: Avoid running multiple large models simultaneously unless you have sufficient RAM

### Memory Management

- Use `dual_pass_write_only` for best balance of UX and memory tracking
- Monitor memory usage when running multiple servers
- The framework will warn before starting additional servers (bypass with `--force`)

### Switching Configurations

- Keep multiple config files in `configs/config_examples/`
- Copy the desired example to `configs/config.json`
- Or use `llf server switch <name>` to switch between local servers

---

## Related Documentation

- [Prompt Configuration](config_prompt_json.md) - System prompts and templates
- [Memory Registry](memory_registry_json.md) - Memory system configuration
- [Tools Registry](tools_registryi_json.md) - Tool system configuration
- [Directory Structure](Directory_Structure.md) - Project layout

---

## Troubleshooting

### Common Issues

**"Connection refused" errors:**
- Check that the server is running: `llf server status`
- Verify `api_base_url` matches your server's host/port
- Ensure no firewall is blocking the port

**"API key invalid" errors:**
- Verify your API key is correct
- Check for extra spaces or quotes
- Ensure API key hasn't expired (for external APIs)

**High memory usage:**
- Reduce `ctx-size` in `server_params`
- Lower `n-gpu-layers` to use more CPU instead of GPU
- Avoid running multiple large models simultaneously

**Slow generation:**
- Increase `n-gpu-layers` to use more GPU
- Reduce `ctx-size` if you don't need long context
- Try a smaller/faster model
- Increase `batch-size` for faster prompt processing

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.

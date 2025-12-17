# Configuration Examples

This directory contains example configuration files for different LLM backends.

## Quick Start

Copy the appropriate example to `config.json` in the project root:

```bash
# For local llama-server
cp config_examples/config.local.example config.json

# For OpenAI API
cp config_examples/config.openai.example config.json

# For Anthropic API
cp config_examples/config.anthropic.example config.json
```

Then edit `config.json` with your specific settings (API keys, model names, etc.).

---

## Available Configurations

### 1. config.local.example

**Use case**: Running LLMs locally using llama.cpp/llama-server

**Requirements**:
- Compiled llama.cpp with llama-server binary
- Downloaded GGUF model file (e.g., Qwen2.5-Coder-7B-Instruct-GGUF)

**Features**:
- Full local control (no API costs)
- Privacy (data never leaves your machine)
- Supports llama.cpp-specific parameters (top_k, repetition_penalty)

**Setup**:
```bash
cp config_examples/config.local.example config.json
# Download model: llf download
# Start chatting: llf chat
```

---

### 2. config.openai.example

**Use case**: Using OpenAI's GPT models (GPT-4, GPT-3.5, etc.)

**Requirements**:
- OpenAI API key (from https://platform.openai.com/api-keys)

**Features**:
- Access to latest GPT models
- No local setup needed
- Pay-per-use pricing

**Setup**:
```bash
cp config_examples/config.openai.example config.json
# Edit config.json: Add your API key
# Start chatting: llf chat
```

**Important**:
- Remove `top_k` and `repetition_penalty` from inference_params (not supported by OpenAI)
- Use `max_tokens` for GPT-3.5/GPT-4, or `max_completion_tokens` for newer models

---

### 3. config.anthropic.example

**Use case**: Using Anthropic's Claude models

**Requirements**:
- Anthropic API key (from https://console.anthropic.com/)

**Features**:
- Access to Claude models (Claude 3, etc.)
- No local setup needed
- Pay-per-use pricing

**Setup**:
```bash
cp config_examples/config.anthropic.example config.json
# Edit config.json: Add your API key
# Start chatting: llf chat
```

**Important**:
- Remove `top_k` and `repetition_penalty` from inference_params (not supported by Anthropic)

---

## Configuration Structure

All configs follow this structure:

```json
{
  "local_llm_server": {
    // Local server settings (only used for local LLM)
  },
  "llm_endpoint": {
    // API endpoint settings (determines which LLM to use)
    "api_base_url": "...",
    "api_key": "...",
    "model_name": "..."
  },
  "inference_params": {
    // Generation parameters (varies by API)
  },
  "log_level": "ERROR"
}
```

---

## Switching Between Configurations

You can easily switch between different LLM backends by copying different example files:

**Local development (free, private)**:
```bash
cp config_examples/config.local.example config.json
```

**Production with OpenAI (powerful, paid)**:
```bash
cp config_examples/config.openai.example config.json
```

**Or keep multiple configs**:
```bash
cp config_examples/config.local.example config.local.json
cp config_examples/config.openai.example config.openai.json

# Use with --config flag:
llf --config config.local.json chat
llf --config config.openai.json chat
```

---

## Parameter Compatibility

Different APIs support different parameters:

| Parameter | Local (llama.cpp) | OpenAI | Anthropic |
|-----------|-------------------|--------|-----------|
| temperature | ✅ | ✅ | ✅ |
| max_tokens | ✅ | ✅ | ✅ |
| top_p | ✅ | ✅ | ✅ |
| top_k | ✅ | ❌ | ❌ |
| repetition_penalty | ✅ | ❌ | ❌ |

**Important**: Only include parameters supported by your chosen API to avoid errors.

---

## Security Notes

**Never commit your actual `config.json` with API keys to git!**

The `.gitignore` file already excludes:
- `config.json` (your actual config with secrets)

But allows:
- `config*.example` (example templates without secrets)

Always use environment-specific configs and keep API keys secure.

---

For more information, see:
- [Main README](../README.md)
- [Configuration Guide](../CONFIG_README.md)
- [Codebase Review](../docs/CODEBASE_REVIEW.md)

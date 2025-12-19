# Configuration Examples

This directory contains example configuration files for different LLM backends.

## Quick Start

Copy the appropriate example to `config.json` in the project root:

```bash
# For local llama-server with HuggingFace models (recommended for beginners)
cp config_examples/config.local.huggingface.example config.json

# For local llama-server with custom GGUF directory
cp config_examples/config.local.gguf.example config.json

# For OpenAI API
cp config_examples/config.openai.example config.json

# For Anthropic API
cp config_examples/config.anthropic.example config.json
```

Then edit `config.json` with your specific settings (API keys, model names, etc.).

---

## Available Configurations

### 1. config.local.huggingface.example / config.local.huggingface.json

**Use case**: Running LLMs locally with models downloaded from HuggingFace (safetensors format)

**Requirements**:
- Compiled llama.cpp with llama-server binary
- Downloaded model from HuggingFace (e.g., Qwen/Qwen2.5-Coder-7B-Instruct)

**Features**:
- Full local control (no API costs)
- Privacy (data never leaves your machine)
- Easy model downloads via `llf model download`
- Uses standard HuggingFace model format (safetensors)
- Supports llama.cpp-specific parameters (top_k, repetition_penalty)

**How it works**:
- `local_llm_server.model_dir`: HuggingFace model directory (e.g., "Qwen--Qwen2.5-Coder-7B-Instruct")
  - Directory name uses `--` instead of `/` from HuggingFace model name
  - Contains safetensors files and model configuration
- `llm_endpoint.model_name`: Original HuggingFace repo name (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct")
  - Used for downloads and metadata
- No `gguf_file` needed - llama-server loads safetensors directly

**Setup**:
```bash
cp config_examples/config.local.huggingface.example config.json
# Download model: llf model download
# Start chatting: llf chat
```

**Clean reference**: [config.local.huggingface.json](config.local.huggingface.json)

---

### 2. config.local.gguf.example / config.local.gguf.json

**Use case**: Running LLMs locally with GGUF files from custom sources (URLs, manual downloads)

**Requirements**:
- Compiled llama.cpp with llama-server binary
- GGUF model file in a custom directory

**Features**:
- Full local control (no API costs)
- Privacy (data never leaves your machine)
- Complete control over model file organization
- Useful for URL-downloaded models, custom quantizations, or testing
- Can store multiple GGUF models in the same directory
- Supports llama.cpp-specific parameters (top_k, repetition_penalty)

**How it works**:
- `local_llm_server.model_dir`: Custom subdirectory name in `models/` (e.g., "custom_models")
  - Not tied to HuggingFace naming - use any name you want
- `local_llm_server.gguf_file`: Specific GGUF file to use (e.g., "my-model.gguf")
  - Can store multiple GGUF files in the same directory
- `llm_endpoint.model_name`: Descriptive name for the model (e.g., "custom-model")
  - Just metadata, not used for file paths
- Full path: `models/custom_models/my-model.gguf`

**Example use cases**:
- Downloaded GGUF from URL: `llf model download --url https://example.com/model.gguf --name my_downloads`
- Custom quantized models: Store all your q4/q5/q8 variants in one directory
- Testing multiple models: Organize by use case (coding, chat, reasoning)
- Manual downloads: Drop GGUF files directly into `models/my_models/`

**Setup**:
```bash
cp config_examples/config.local.gguf.example config.json
# Edit config.json: Set model_dir and gguf_file
# Ensure your GGUF file is in models/{model_dir}/
# Start chatting: llf chat
```

**Clean reference**: [config.local.gguf.json](config.local.gguf.json)

---

### 3. config.openai.example / config.openai.json

**Use case**: Using OpenAI's GPT models (GPT-4, GPT-3.5, etc.) via cloud API

**Requirements**:
- OpenAI API key (from https://platform.openai.com/api-keys)

**Features**:
- Access to latest GPT models
- No local setup needed (cloud-based)
- Pay-per-use pricing
- No local server required - `local_llm_server` section not needed

**How it works**:
- All inference happens remotely via OpenAI's API
- No `local_llm_server` configuration needed
- Only `llm_endpoint` section is used

**Setup**:
```bash
cp config_examples/config.openai.example config.json
# Edit config.json: Add your API key
# Start chatting: llf chat
```

**Important**:
- `top_k` and `repetition_penalty` are NOT supported by OpenAI API (already excluded from example)
- Use `max_tokens` for GPT-3.5/GPT-4, or `max_completion_tokens` for newer models

**Clean reference**: [config.openai.json](config.openai.json)

---

### 4. config.anthropic.example / config.anthropic.json

**Use case**: Using Anthropic's Claude models via cloud API

**Requirements**:
- Anthropic API key (from https://console.anthropic.com/)

**Features**:
- Access to Claude models (Claude 3, etc.)
- No local setup needed (cloud-based)
- Pay-per-use pricing
- No local server required - `local_llm_server` section not needed

**How it works**:
- All inference happens remotely via Anthropic's API
- No `local_llm_server` configuration needed
- Only `llm_endpoint` section is used

**Setup**:
```bash
cp config_examples/config.anthropic.example config.json
# Edit config.json: Add your API key
# Start chatting: llf chat
```

**Important**:
- `top_k` and `repetition_penalty` are NOT supported by Anthropic API (already excluded from example)

**Clean reference**: [config.anthropic.json](config.anthropic.json)

---

## Configuration File Types

This directory contains two types of files:

### Example Files (*.example)
- Heavily commented with explanations
- Include setup instructions and use cases
- Safe to copy and edit
- Examples: `config.local.huggingface.example`, `config.openai.example`

### Clean Reference Files (*.json)
- No comments, ready to use
- Minimal, clean JSON structure
- Good for quick reference or programmatic use
- Examples: `config.local.huggingface.json`, `config.openai.json`

Both contain the same configuration - choose whichever you prefer!

---

## Configuration Structure

### Local LLM Configs (HuggingFace, GGUF)

```json
{
  "local_llm_server": {
    // Settings for local llama-server
    "llama_server_path": "...",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "model_dir": "...",        // Always included
    "gguf_file": "..."         // Only for GGUF config
  },
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "..."
  },
  "inference_params": {
    // Includes llama.cpp params: top_k, repetition_penalty
  }
}
```

### External API Configs (OpenAI, Anthropic)

```json
{
  // No local_llm_server section - not needed for cloud APIs
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "model_name": "gpt-4"
  },
  "inference_params": {
    // Only OpenAI/Anthropic compatible params
    // Excludes: top_k, repetition_penalty
  }
}
```

**Key difference**: Local configs need `local_llm_server`, external APIs don't.

---

## Choosing Between Local Configurations

**Key difference**: Model file format and source

### Use config.local.huggingface.example when:
- ✅ Downloading models from HuggingFace in **safetensors format** (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct")
- ✅ Using `llf model download` to download from HuggingFace
- ✅ You want the standard HuggingFace directory structure
- ✅ You're new to LLF (recommended for beginners)
- ✅ Working with standard HuggingFace models (not pre-quantized GGUF)

### Use config.local.gguf.example when:
- ✅ Using **GGUF format** models (pre-quantized for llama.cpp)
- ✅ Downloading GGUF models from direct URLs (`llf model download --url`)
- ✅ Manually downloading GGUF files from any source
- ✅ Organizing multiple GGUF files in custom directories
- ✅ Testing different quantizations (q4, q5, q8) in one directory
- ✅ You want complete control over directory naming and organization

---

## Switching Between Configurations

You can easily switch between different LLM backends by copying different example files:

**Local development with HuggingFace (free, private, recommended)**:
```bash
cp config_examples/config.local.huggingface.example config.json
```

**Local development with custom GGUF (free, private, advanced)**:
```bash
cp config_examples/config.local.gguf.example config.json
```

**Production with OpenAI (powerful, paid)**:
```bash
cp config_examples/config.openai.example config.json
```

**Or keep multiple configs**:
```bash
cp config_examples/config.local.huggingface.example config.local.json
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
- `config*.json` in config_examples/ (clean references without secrets)

Always use environment-specific configs and keep API keys secure.

---

## Legacy Configuration

**Note**: The original `config.local.example` file has been split into two focused examples:
- `config.local.huggingface.example` - For HuggingFace model structure
- `config.local.gguf.example` - For custom GGUF directories

The old `config.local.example` is still available for backward compatibility but will be removed in a future version. Please migrate to one of the new examples.

---

For more information, see:
- [Main README](../README.md)
- [Configuration Guide](../CONFIG_README.md)
- [Codebase Review](../docs/CODEBASE_REVIEW.md)

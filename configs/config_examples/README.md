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

## Advanced Features

### Tools Configuration

The `tools` section in `llm_endpoint` enables optional features:

```json
{
  "llm_endpoint": {
    "tools": {
      "xml_format": "enable"
    }
  }
}
```

**Available Tools:**

#### xml_format
**Purpose**: Parse XML-style function calls and convert to OpenAI JSON format

**When to enable**:
- ✅ Using models like Qwen3-Coder that output XML format function calls
- ✅ Working with Chinese language models
- ✅ Custom fine-tuned models trained on XML function calling

**When to disable**:
- ❌ Using OpenAI API (uses native JSON)
- ❌ Using Anthropic API (uses native JSON)
- ❌ Models that natively support OpenAI JSON format

**Example XML → JSON conversion**:
```xml
<!-- Model outputs -->
<function=search_memories>
<parameter=query>user preferences</parameter>
</function>
```
```json
// Converted to
{
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "search_memories",
      "arguments": "{\"query\": \"user preferences\"}"
    }
  }]
}
```

**Configuration**:
```json
{
  "llm_endpoint": {
    "tools": {
      "xml_format": "enable"  // or "disable"
    }
  }
}
```

**CLI management**:
```bash
# Enable (session override)
llf tool xml_format enable

# Disable (session override)
llf tool xml_format disable

# Reset to config file setting
llf tool xml_format auto

# Check status
llf tool list
```

**See also**: [tools/xml_format/README.md](../../tools/xml_format/README.md)

---

### Tool Execution Modes

The `tool_execution_mode` setting controls how the framework balances streaming UX with tool calling accuracy.

```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**The Problem**: Streaming responses (chunks appear as they're generated) and tool calling (requires complete JSON) are fundamentally incompatible. When memory tools are enabled, the LLM can't stream because function calls need the full response.

**Available Modes:**

#### 1. `single_pass` (Default)
- **How it works**: Single LLM call, no streaming when tools available
- **Pros**: Always accurate, simple, predictable
- **Cons**: No streaming when memory enabled (poor UX)
- **Best for**: When accuracy matters more than streaming UX

```json
"tool_execution_mode": "single_pass"
```

**Example interaction**:
```
User: "What's my name?"
[Pause while LLM thinks]
Assistant: "Your name is Matt." [appears all at once]
```

#### 2. `dual_pass_write_only` (Recommended)
- **How it works**: Automatically detects operation type
  - WRITE operations ("Remember X"): Dual-pass (stream + background tools)
  - READ operations ("What's my name?"): Single-pass with tools (accurate)
  - GENERAL chat: Stream only
- **Pros**: Streaming for writes, accurate reads, best balance
- **Cons**: 2x LLM calls for write operations (higher cost)
- **Best for**: Most use cases, interactive chat applications

```json
"tool_execution_mode": "dual_pass_write_only"
```

**Example interaction**:
```
User: "Remember that I like pizza"
Assistant: "I'll remember that you like pizza." [streams in real-time]
[Background: Actually stores to memory]

User: "What do I like?"
[Pause while LLM retrieves from memory]
Assistant: "You like pizza." [accurate, from memory]

User: "Tell me a joke"
Assistant: "Why did the... [streams naturally]
```

#### 3. `dual_pass_all` (Advanced - Use with Caution)
- **How it works**: Always makes two LLM calls when tools available
- **Pros**: Always streams (best UX)
- **Cons**:
  - 2x LLM calls for all operations (highest cost)
  - **Dangerous for reads**: User sees Pass 1 response (may be wrong), but Pass 2 retrieves actual data
- **Best for**: Write-heavy applications that don't use memory reads

```json
"tool_execution_mode": "dual_pass_all"
```

**⚠️ Warning**:
```
User: "What's my name?"
Assistant: "I don't have that information." [streams, but wrong!]
[Background: Pass 2 retrieves "Matt" from memory, but user never sees it]
```

**NOT recommended** for applications that read from memory.

---

### Operation Type Detection

For `dual_pass_write_only` mode, the framework automatically classifies user messages:

**READ Operations** (single-pass with tools):
- `"What's my name?"`
- `"Do you remember...?"`
- `"Can you recall...?"`
- `"Tell me about my preferences"`

**WRITE Operations** (dual-pass streaming):
- `"Remember that..."`
- `"My name is..."`
- `"I like..."`
- `"Store this..."`

**GENERAL Operations** (streaming only):
- `"Tell me a joke"`
- `"How's the weather?"`
- `"Explain quantum physics"`

---

### Cost Comparison

| Mode | READ Operations | WRITE Operations | GENERAL Chat |
|------|----------------|------------------|--------------|
| `single_pass` | 1 LLM call | 1 LLM call | 1 LLM call |
| `dual_pass_write_only` | 1 LLM call | **2 LLM calls** | 1 LLM call |
| `dual_pass_all` | **2 LLM calls** | **2 LLM calls** | 1 LLM call |

**Recommendation**: Use `dual_pass_write_only` for best balance of cost and UX.

---

### Configuration Examples by Use Case

**Personal Assistant** (recommended):
```json
{
  "llm_endpoint": {
    "tools": {
      "xml_format": "enable"
    },
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**Data Entry System** (write-heavy):
```json
{
  "llm_endpoint": {
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**Q&A System** (read-heavy, accuracy critical):
```json
{
  "llm_endpoint": {
    "tool_execution_mode": "single_pass"
  }
}
```

**External APIs** (OpenAI, Anthropic):
```json
{
  "llm_endpoint": {
    "tools": {
      "xml_format": "disable"
    },
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

---

### Full Documentation

For complete details on tool execution modes, see:
- **[docs/TOOL_EXECUTION_MODES.md](../../docs/TOOL_EXECUTION_MODES.md)** - Comprehensive guide
- **[tools/xml_format/README.md](../../tools/xml_format/README.md)** - XML parser documentation

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

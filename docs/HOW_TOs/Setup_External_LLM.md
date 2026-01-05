# Setup External LLM: OpenAI & Anthropic

> **Use ChatGPT, Claude, and Other Cloud LLMs**
> Connect the LLM Framework to external API providers like OpenAI (ChatGPT) or Anthropic (Claude) instead of running models locally.

---

## Table of Contents

1. [What is an External LLM?](#what-is-an-external-llm)
2. [Why Use External LLMs?](#why-use-external-llms)
3. [Prerequisites](#prerequisites)
4. [Understanding the Configuration](#understanding-the-configuration)
5. [Setup OpenAI (ChatGPT)](#setup-openai-chatgpt)
6. [Setup Anthropic (Claude)](#setup-anthropic-claude)
7. [Listing Available Models](#listing-available-models)
8. [Using the External LLM](#using-the-external-llm)
9. [Switching Between Local and External](#switching-between-local-and-external)
10. [Advanced Configuration](#advanced-configuration)
11. [Troubleshooting](#troubleshooting)

---

## What is an External LLM?

An **external LLM** is a cloud-based AI model accessed via API rather than running locally on your computer.

### Local vs External LLMs

| Aspect | Local LLM | External LLM |
|--------|-----------|--------------|
| **Location** | Runs on your computer | Runs on provider's servers |
| **Setup** | Requires model download (GB) | Just needs API key |
| **Resources** | Uses your RAM/CPU/GPU | Uses provider's infrastructure |
| **Cost** | Free (electricity only) | Pay per usage (API calls) |
| **Privacy** | Completely private | Data sent to provider |
| **Speed** | Depends on your hardware | Usually very fast |
| **Capability** | Depends on model size | Latest, most capable models |
| **Internet** | Not required | Required |

### Popular External LLM Providers

| Provider | Models | Website | API Docs |
|----------|--------|---------|----------|
| **OpenAI** | GPT-4, GPT-4 Turbo, GPT-3.5, GPT-4o | https://platform.openai.com | [API Reference](https://platform.openai.com/docs) |
| **Anthropic** | Claude 3 Opus, Sonnet, Haiku, Claude 2.1 | https://console.anthropic.com | [API Reference](https://docs.anthropic.com) |
| **Other** | Any OpenAI-compatible API | Various | Various |

---

## Why Use External LLMs?

**Advantages:**
- Access to the most powerful models (GPT-4, Claude 3 Opus)
- No local hardware requirements (no GPU needed)
- Faster responses (usually)
- Always up-to-date with latest model versions
- No model downloads (instant setup)

**Disadvantages:**
- Requires internet connection
- Costs money (pay per token)
- Data sent to third party (privacy concerns)
- Subject to rate limits
- Requires API key management

**Best for:**
- Users without powerful hardware
- Need access to cutting-edge models
- Production applications
- Don't mind API costs
- Non-sensitive data

---

## Prerequisites

Before setting up an external LLM, ensure you have:

1. **Active Virtual Environment**
   ```bash
   source llf_venv/bin/activate  # On macOS/Linux
   ```

2. **API Key from Provider**
   - OpenAI: [Get API key](https://platform.openai.com/api-keys)
   - Anthropic: [Get API key](https://console.anthropic.com/settings/keys)

3. **Billing Setup** (if required by provider)
   - OpenAI requires payment method
   - Anthropic requires payment method

4. **Internet Connection** (for API calls)

5. **Configuration File Access**
   - Edit `configs/config.json`

---

## Understanding the Configuration

### Key Difference from Local Setup

When using external LLMs, your configuration is **simpler** because:

**❌ You DON'T need:**
- `local_llm_server` section (no local server)
- `local_llm_servers` array (no servers to manage)
- llama-server binary
- Downloaded model files
- Server start/stop commands

**✅ You ONLY need:**
- `llm_endpoint` section (API connection details)
- `api_base_url` (provider's API endpoint)
- `api_key` (your secret API key)
- `model_name` (which model to use)
- Basic paths and parameters

### Configuration Structure

A minimal external LLM configuration looks like this:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.provider.com/v1",
    "api_key": "your-api-key-here",
    "model_name": "model-name"
  },
  "model_dir": "models",
  "cache_dir": ".cache",
  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  }
}
```

**Notice:**
- No `local_llm_server` section
- No `llama_server_path`
- No `gguf_file`
- Much simpler!

---

## Setup OpenAI (ChatGPT)

Follow these steps to configure the framework to use OpenAI's models.

### Step 1: Get Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Sign in or create an account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-proj-` or `sk-`)
6. **Important:** Save it securely - you can't see it again!

### Step 2: Set Up Billing

1. Go to [Billing Settings](https://platform.openai.com/account/billing)
2. Add a payment method
3. Set up usage limits (recommended)
4. Review [Pricing](https://openai.com/pricing)

### Step 3: Use Example Configuration

The easiest way to start is using the provided example:

```bash
# Copy OpenAI example configuration
cp configs/config_examples/config.openai.example configs/config.json

# Or use the .json version with comments
cp configs/config_examples/config.openai.json configs/config.json
```

### Step 4: Edit Configuration

Open `configs/config.json` and update your API key:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-ACTUAL-API-KEY-HERE",
    "model_name": "gpt-4"
  },
  "model_dir": "models",
  "cache_dir": ".cache",
  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  }
}
```

**Replace:**
- `sk-proj-YOUR-ACTUAL-API-KEY-HERE` with your actual OpenAI API key

### Step 5: Choose a Model (Optional)

Popular OpenAI models:

| Model | Best For | Cost | Notes |
|-------|----------|------|-------|
| `gpt-4` | Complex reasoning, coding | $$$ | Most capable |
| `gpt-4-turbo` | Fast GPT-4, longer context | $$ | Faster, cheaper |
| `gpt-4o` | Latest multimodal model | $$ | Best balance |
| `gpt-3.5-turbo` | Fast, simple tasks | $ | Most affordable |

To use a different model, update `model_name`:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-API-KEY",
    "model_name": "gpt-4o"
  }
}
```

### Step 6: Verify Configuration

List available models to verify your API key works:

```bash
llf server list_models
```

You can update the `model_name` config parameter in the `configs/config.json` to any of the listed models.

**Expected output:**
```
Available models from https://api.openai.com/v1:
  - gpt-4
  - gpt-4-turbo
  - gpt-4o
  - gpt-3.5-turbo
  - (and more...)
```

If you see errors, verify your API key is correct.

### Step 7: Start Chatting

You're ready to use OpenAI! Skip server commands and jump straight to chat:

```bash
llf chat
```

**Example session:**
```
You: Hello! Can you help me write a Python function?

GPT-4: Of course! I'd be happy to help you write a Python function. What would you like the function to do?
```

---

## Setup Anthropic (Claude)

Follow these steps to configure the framework to use Anthropic's Claude models.

### Step 1: Get Your Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com)
2. Sign in or create an account
3. Navigate to [API Keys](https://console.anthropic.com/settings/keys)
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-`)
6. **Important:** Save it securely!

### Step 2: Set Up Billing

1. Go to [Billing](https://console.anthropic.com/settings/billing)
2. Add a payment method
3. Review [Pricing](https://www.anthropic.com/pricing)

### Step 3: Use Example Configuration

```bash
# Copy Anthropic example configuration
cp configs/config_examples/config.anthropic.example configs/config.json

# Or use the .json version with comments
cp configs/config_examples/config.anthropic.json configs/config.json
```

### Step 4: Edit Configuration

Open `configs/config.json` and update your API key:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.anthropic.com/v1",
    "api_key": "sk-ant-YOUR-ACTUAL-API-KEY-HERE",
    "model_name": "claude-3-opus-20240229"
  },
  "model_dir": "models",
  "cache_dir": ".cache",
  "log_level": "ERROR",
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  }
}
```

**Replace:**
- `sk-ant-YOUR-ACTUAL-API-KEY-HERE` with your actual Anthropic API key

### Step 5: Choose a Claude Model (Optional)

Popular Claude models:

| Model | Best For | Cost | Notes |
|-------|----------|------|-------|
| `claude-3-opus-20240229` | Most capable, complex tasks | $$$ | Best quality |
| `claude-3-sonnet-20240229` | Balanced capability & speed | $$ | Best value |
| `claude-3-haiku-20240307` | Fast, simple tasks | $ | Most affordable |
| `claude-2.1` | Previous generation | $$ | Still capable |

To use a different model, update `model_name`:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.anthropic.com/v1",
    "api_key": "sk-ant-YOUR-API-KEY",
    "model_name": "claude-3-sonnet-20240229"
  }
}
```

### Step 6: Verify Configuration

List available models:

```bash
llf server list_models
```

You can update the `model_name` config parameter in the `configs/config.json` to any of the listed models.

**Expected output:**
```
Available models from https://api.anthropic.com/v1:
  - claude-3-opus-20240229
  - claude-3-sonnet-20240229
  - claude-3-haiku-20240307
  - claude-2.1
```

### Step 7: Start Chatting

You're ready to use Claude!

```bash
llf chat
```

**Example session:**
```
You: Hello Claude! Can you help me with Python?

Claude: Hello! I'd be delighted to help you with Python. I can assist with everything from basic syntax to advanced topics...
```

---

## Listing Available Models

After configuring your API endpoint, you can list all available models from the provider.

### Command

```bash
llf server list_models
```

**Purpose:**
- Verify your API key works
- See which models are available
- Find exact model names to use in config

### Example Outputs

**OpenAI:**
```
Available models from https://api.openai.com/v1:
  - gpt-4
  - gpt-4-0613
  - gpt-4-32k
  - gpt-4-turbo
  - gpt-4-turbo-preview
  - gpt-4o
  - gpt-4o-mini
  - gpt-3.5-turbo
  - gpt-3.5-turbo-16k
```

**Anthropic:**
```
Available models from https://api.anthropic.com/v1:
  - claude-3-opus-20240229
  - claude-3-sonnet-20240229
  - claude-3-haiku-20240307
  - claude-2.1
  - claude-2.0
```

### Updating Model Name

After seeing the list, update your config to use your preferred model:

1. **Edit `configs/config.json`**
2. **Find the `llm_endpoint` section**
3. **Update `model_name`**:
   ```json
   {
     "llm_endpoint": {
       "api_base_url": "https://api.openai.com/v1",
       "api_key": "sk-proj-YOUR-KEY",
       "model_name": "gpt-4o"  ← Update this
     }
   }
   ```
4. **Save the file**
5. **Start chatting** - changes take effect immediately

---

## Using the External LLM

Once configured, using an external LLM is nearly identical to using a local one.

### What Works the Same

All these commands work normally:

```bash
# Chat
llf chat
llf chat --cli "Your question"

# GUI
llf gui
llf gui start --daemon

# Memory
llf memory list
llf memory enable main_memory

# Data Stores (RAG)
llf datastore list
llf datastore attach my_docs

# Modules (Speech)
llf module enable text2speech

# Tools
llf tool enable web_search
```

### What's Different

**You DON'T use server commands:**

```bash
# ❌ These are NOT needed with external LLMs
llf server start       # No local server
llf server stop        # Nothing to stop
llf server status      # No server running
llf server restart     # Nothing to restart

# ✅ This ONE server command still works
llf server list_models # Lists models from external API
```

### Typical Workflow

**With External LLM:**
1. Activate virtual environment: `source llf_venv/bin/activate`
2. Start chatting: `llf chat`
3. Done! (no server to stop)

**Compare to Local LLM:**
1. Activate virtual environment: `source llf_venv/bin/activate`
2. Start server: `llf server start --daemon`
3. Start chatting: `llf chat`
4. Stop server: `llf server stop`

**External LLMs are simpler!** No server management required.

### Example Chat Session

```bash
# Activate environment
source llf_venv/bin/activate

# Start chatting immediately
llf chat

# Chat interface opens
You: Write a Python function to calculate fibonacci numbers

GPT-4: Here's a Python function that calculates Fibonacci numbers...

You: Can you add memoization to make it faster?

GPT-4: Absolutely! Here's the optimized version with memoization...

You: exit
```

---

## Switching Between Local and External

You can easily switch between local and external LLMs by changing your configuration.

### Save Multiple Configurations

Keep different config files for different setups:

```bash
# Save current config with a name
cp configs/config.json configs/config.local.backup

# Save external configs
cp configs/config.json configs/config.openai.backup
cp configs/config.json configs/config.anthropic.backup
```

### Switch to OpenAI

```bash
# Option 1: Use example
cp configs/config_examples/config.openai.example configs/config.json
# Then edit to add your API key

# Option 2: Use your backup
cp configs/config.openai.backup configs/config.json
```

### Switch to Anthropic

```bash
# Option 1: Use example
cp configs/config_examples/config.anthropic.example configs/config.json
# Then edit to add your API key

# Option 2: Use your backup
cp configs/config.anthropic.backup configs/config.json
```

### Switch to Local LLM

```bash
# Option 1: Use example
cp configs/config_examples/config.local.example configs/config.json
# Then edit to add your paths

# Option 2: Use your backup
cp configs/config.local.backup configs/config.json
```

### Quick Config Switching Script

Create a helper script `switch_config.sh`:

```bash
#!/bin/bash
# Usage: ./switch_config.sh [openai|anthropic|local]

case "$1" in
  openai)
    cp configs/config.openai.backup configs/config.json
    echo "Switched to OpenAI"
    ;;
  anthropic)
    cp configs/config.anthropic.backup configs/config.json
    echo "Switched to Anthropic"
    ;;
  local)
    cp configs/config.local.backup configs/config.json
    echo "Switched to Local LLM"
    ;;
  *)
    echo "Usage: $0 [openai|anthropic|local]"
    exit 1
    ;;
esac

llf server list_models || echo "Using local LLM"
```

Make it executable:
```bash
chmod +x switch_config.sh
```

Use it:
```bash
./switch_config.sh openai
./switch_config.sh local
```

---

## Advanced Configuration

### Inference Parameters

Different providers support different parameters.

#### OpenAI Parameters

```json
{
  "inference_params": {
    "temperature": 0.7,        // 0.0-2.0 (OpenAI supports up to 2.0)
    "max_tokens": 2048,        // Max response tokens
    "top_p": 0.9,              // 0.0-1.0 nucleus sampling
    "frequency_penalty": 0.0,  // -2.0 to 2.0 (OpenAI specific)
    "presence_penalty": 0.0    // -2.0 to 2.0 (OpenAI specific)
  }
}
```

**Note:** OpenAI does NOT support:
- `top_k` (llama.cpp only)
- `repetition_penalty` (llama.cpp only)

#### Anthropic Parameters

```json
{
  "inference_params": {
    "temperature": 0.7,  // 0.0-1.0 (Anthropic max is 1.0, not 2.0)
    "max_tokens": 2048,  // Max response tokens (up to 4096)
    "top_p": 0.9         // 0.0-1.0 nucleus sampling
  }
}
```

**Note:** Anthropic does NOT support:
- `top_k`
- `repetition_penalty`
- `frequency_penalty`
- `presence_penalty`

### Tool Configuration

For OpenAI and Anthropic, disable XML format for tools:

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-KEY",
    "model_name": "gpt-4",
    "tools": {
      "xml_format": "disable"
    },
    "tool_execution_mode": "dual_pass_write_only"
  }
}
```

**Why?**
- OpenAI and Anthropic use native JSON for function calling
- Local models may use XML format
- This ensures compatibility

### Multiple External Providers

You can configure multiple external endpoints (though not commonly needed):

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-proj-YOUR-OPENAI-KEY",
    "model_name": "gpt-4"
  },
  "model_dir": "models",
  "cache_dir": ".cache"
}
```

To switch providers, just change `api_base_url`, `api_key`, and `model_name`.

### Using OpenAI-Compatible APIs

Some providers offer OpenAI-compatible APIs (Groq, Together AI, etc.):

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.groq.com/openai/v1",
    "api_key": "gsk_YOUR-GROQ-KEY",
    "model_name": "mixtral-8x7b-32768"
  }
}
```

Any API that follows the OpenAI format should work!

---

## Troubleshooting

### Common Issues

#### Problem: "Invalid API Key"

**Error:**
```
Error: Authentication failed. Invalid API key.
```

**Solutions:**
1. Verify API key is correct in `configs/config.json`
2. Check for extra spaces or quotes around the key
3. Ensure key hasn't been revoked
4. OpenAI keys start with `sk-proj-` or `sk-`
5. Anthropic keys start with `sk-ant-`

#### Problem: "Model Not Found"

**Error:**
```
Error: The model 'gpt-5' does not exist
```

**Solutions:**
1. Run `llf server list_models` to see available models
2. Check spelling of `model_name` in config
3. Use exact model name from list
4. Some models require special access

#### Problem: "Rate Limit Exceeded"

**Error:**
```
Error: Rate limit exceeded. Please try again later.
```

**Solutions:**
1. Wait a few seconds and try again
2. Check your API usage limits
3. Consider upgrading your plan
4. Add delays between requests

#### Problem: "Insufficient Quota"

**Error:**
```
Error: You exceeded your current quota
```

**Solutions:**
1. Check billing at provider console
2. Add payment method if not set up
3. Add credits to account
4. Review usage limits

#### Problem: "Connection Error"

**Error:**
```
Error: Could not connect to API endpoint
```

**Solutions:**
1. Check internet connection
2. Verify `api_base_url` is correct
3. Check if provider's API is down
4. Try pinging the API endpoint
5. Check firewall settings

#### Problem: "Server Commands Don't Work"

**Error:**
```
$ llf server start
Error: No local server configured
```

**This is normal!**
- External LLMs don't use local server
- Skip `llf server start/stop/status`
- Use `llf server list_models` to verify connection
- Go straight to `llf chat`

### Debugging Tips

#### Enable Debug Logging

Edit `configs/config.json`:

```json
{
  "log_level": "DEBUG"
}
```

Then check output for detailed error messages.

#### Test API Key Manually

**OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-YOUR-KEY"
```

**Anthropic:**
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-YOUR-KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-opus-20240229","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
```

#### Verify Configuration

Check your config is valid JSON:

```bash
# Validate JSON syntax
cat configs/config.json | python -m json.tool
```

If errors appear, fix JSON formatting.

### Cost Management

#### Monitor Usage

- **OpenAI:** [Usage Dashboard](https://platform.openai.com/usage)
- **Anthropic:** [Usage Console](https://console.anthropic.com/settings/billing)

#### Set Limits

1. Set monthly spending limits
2. Enable usage alerts
3. Monitor costs regularly
4. Use cheaper models for testing (gpt-3.5-turbo, claude-haiku)

#### Cost Optimization

```json
{
  "inference_params": {
    "temperature": 0.7,
    "max_tokens": 1024  ← Lower this to reduce costs
  }
}
```

Lower `max_tokens` = fewer tokens per response = lower cost.

---

## Best Practices

### Security

1. **Never commit API keys to git**
   ```bash
   # Add to .gitignore
   echo "configs/config.json" >> .gitignore
   ```

2. **Use environment variables** (optional)
   ```bash
   export OPENAI_API_KEY="sk-proj-YOUR-KEY"
   # Update config to read from environment
   ```

3. **Rotate keys regularly**
   - Create new keys periodically
   - Delete old keys

4. **Use separate keys for dev/prod**
   - Development key for testing
   - Production key for real use

### Cost Efficiency

1. **Use appropriate models**
   - GPT-3.5 Turbo for simple tasks
   - GPT-4 only when needed
   - Claude Haiku for fast, cheap responses

2. **Limit max_tokens**
   - Set reasonable limits
   - Avoid unnecessarily long responses

3. **Cache responses** when possible
   - The framework caches in `.cache/` directory
   - Avoid re-asking identical questions

4. **Test locally first**
   - Develop with local LLM
   - Switch to external for production

### Configuration Management

1. **Keep backups**
   ```bash
   cp configs/config.json configs/config.$(date +%Y%m%d).backup
   ```

2. **Document your configs**
   - Add comments (use .json files with `_comment` fields)
   - Note which keys are for what

3. **Version control**
   - Keep example configs in git
   - Keep actual keys OUT of git

---

## Summary

You now know how to use external LLMs with the LLM Framework:

**Key Takeaways:**
1. **No local server needed** - Simpler configuration
2. **Just need API key** - From OpenAI or Anthropic
3. **Two main changes** - Update `api_base_url` and `api_key`
4. **List models first** - Use `llf server list_models`
5. **Skip server commands** - Go straight to `llf chat`

**Quick Reference:**

```bash
# Setup (one time)
cp configs/config_examples/config.openai.example configs/config.json
# Edit config.json to add your API key

# Verify connection
llf server list_models

# Start using
llf chat

# No server to stop!
```

**Configuration Files:**
- OpenAI: `configs/config_examples/config.openai.example`
- Anthropic: `configs/config_examples/config.anthropic.example`
- Local: `configs/config_examples/config.local.example`

**Important:**
- External LLMs cost money (pay per use)
- Local LLMs are free (but require hardware)
- You can switch between them anytime
- All other features work the same (memory, tools, etc.)

**For More Help:**
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Documentation](https://docs.anthropic.com)
- [Basic User Guide](../Basic_User_Guide.md)
- [Troubleshooting Guide](Troubleshooting.md)

Happy chatting with your external LLM!
# Setup Multiple LLMs

> **Download, Convert, and Configure Multiple Local LLM Models**
> Learn how to download models from HuggingFace, convert them to GGUF format, and configure your system to run multiple LLM servers simultaneously.

---

## Table of Contents

1. [What is Multi-LLM Setup?](#what-is-multi-llm-setup)
2. [Prerequisites](#prerequisites)
3. [Finding Models on HuggingFace](#finding-models-on-huggingface)
4. [Downloading Models](#downloading-models)
5. [Converting Models to GGUF Format](#converting-models-to-gguf-format)
6. [Configuring Single LLM Server](#configuring-single-llm-server)
7. [Configuring Multiple LLM Servers](#configuring-multiple-llm-servers)
8. [Managing Multiple Servers](#managing-multiple-servers)
9. [Switching Between LLMs](#switching-between-llms)
10. [Cleanup and Disk Space Management](#cleanup-and-disk-space-management)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)
13. [Summary](#summary)

---

## What is Multi-LLM Setup?

The Local LLM Framework supports running multiple Large Language Models simultaneously, each on its own port. This allows you to:

### Benefits of Multiple LLMs

- **Specialized Models**: Use different models for different tasks
  - Coding model for development
  - General chat model for conversations
  - Lightweight model for quick queries
  - Reasoning model for complex problems

- **Easy Switching**: Change between models without restarting
  - Switch active LLM with one command
  - Compare responses from different models
  - Test new models without losing your current setup

- **Resource Flexibility**: Run models appropriate for current task
  - Large model when you need power
  - Small model when you need speed
  - Balance between performance and resource usage

### Use Cases

**Single LLM Configuration:**
- Personal use with one favorite model
- Limited RAM/resources
- Simple, straightforward setup

**Multiple LLM Configuration:**
- Different models for different use cases
- Testing and comparing models
- Team environment with diverse needs
- Development vs. production models

---

## Prerequisites

Before setting up multiple LLMs, ensure you have:

1. **Completed Basic Setup**:
   - Followed [QUICK_INSTALL.md](../QUICK_INSTALL.md)
   - Virtual environment activated: `source llf_venv/bin/activate`
   - llama.cpp compiled with llama-server binary

2. **Sufficient Resources**:
   - Adequate RAM for your models (see [Model Sizes](#model-sizes) below)
   - Sufficient disk space (each model can be 3-50+ GB)
   - CPU or GPU for inference

3. **HuggingFace Account** (Optional):
   - Create free account at [huggingface.co](https://huggingface.co)
   - Some models require authentication
   - Use HuggingFace CLI for authenticated downloads

4. **Understanding of GGUF Format**:
   - Local llama-server requires GGUF format
   - Models with .safetensor files need conversion
   - GGUF models can be used directly

### Model Sizes

Typical model size vs. RAM requirements:

| Model Size | Parameters | GGUF Size | RAM Required | Best For |
|------------|-----------|-----------|--------------|----------|
| **Tiny** | 1-3B | 2-3 GB | 4 GB+ | Quick responses, testing |
| **Small** | 3-7B | 3-6 GB | 8 GB+ | General purpose, lightweight |
| **Medium** | 7-13B | 6-12 GB | 16 GB+ | Good balance |
| **Large** | 13-30B | 12-25 GB | 32 GB+ | Advanced tasks |
| **Very Large** | 30-70B | 25-60 GB | 64 GB+ | Best quality |

**Quantization Impact:**
- `q4_K_M`: Smallest size, lower quality (~4-5 GB for 7B model)
- `q5_K_M`: Balanced size/quality (~5-6 GB for 7B model) ✅ Recommended
- `q6_K`: Higher quality, larger size (~7-8 GB for 7B model)
- `q8_0`: Very high quality (~8-10 GB for 7B model)
- `f16`: Full precision, largest (~14 GB for 7B model)

---

## Finding Models on HuggingFace

### Step 1: Visit HuggingFace

Go to [https://huggingface.co/models](https://huggingface.co/models)

### Step 2: Search for Models

**Filter criteria:**
- **Task**: Text Generation
- **Library**: transformers or gguf
- **License**: Check for usage restrictions
- **Size**: Match your hardware capabilities

**Search tips:**
```
Search terms to try:
- "GGUF" - Find pre-converted models (easiest!)
- "instruct" - Find instruction-tuned models (better for chat)
- "chat" - Find chat-optimized models
- "code" - Find coding-specialized models
```

### Step 3: Recommended Models

Here are proven models that work well with the LLM Framework:

#### Coding Models

| Model | HuggingFace ID | Size | Best For |
|-------|---------------|------|----------|
| **Qwen 2.5 Coder 7B** | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` | ~5 GB | Code generation, debugging |
| **Qwen 3 Coder 30B** | `Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF` | ~20 GB | Advanced coding |
| **DeepSeek Coder 6.7B** | `deepseek-ai/deepseek-coder-6.7b-instruct-GGUF` | ~4 GB | Code completion |
| **CodeLlama 7B** | `codellama/CodeLlama-7b-Instruct-hf` | ~5 GB | Code-specific tasks |

#### General Purpose Models

| Model | HuggingFace ID | Size | Best For |
|-------|---------------|------|----------|
| **Llama 3.2 3B** | `meta-llama/Llama-3.2-3B-Instruct-GGUF` | ~2 GB | Lightweight chat |
| **Llama 3.1 8B** | `meta-llama/Llama-3.1-8B-Instruct-GGUF` | ~5 GB | General chat |
| **Mistral 7B** | `mistralai/Mistral-7B-Instruct-v0.3-GGUF` | ~5 GB | General purpose |
| **Phi-3 Mini** | `microsoft/Phi-3-mini-4k-instruct-GGUF` | ~2 GB | Reasoning, lightweight |

#### Specialized Models

| Model | HuggingFace ID | Size | Best For |
|-------|---------------|------|----------|
| **Nous Hermes 2** | `NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO-GGUF` | ~25 GB | Advanced reasoning |
| **WizardLM 2** | `WizardLM/WizardLM-2-7B-GGUF` | ~5 GB | Complex instructions |

### Step 4: Check Model Format

When viewing a model on HuggingFace:

**✅ GGUF Format (Ready to Use)**:
- Look for `.gguf` files in the "Files and versions" tab
- Can download and use directly
- No conversion needed

**❌ Non-GGUF Format (Needs Conversion)**:
- Has `.safetensors` or `.bin` files
- Requires conversion to GGUF
- Extra step but often newer models

---

## Downloading Models

### Using llf model download

The `llf model download` command handles HuggingFace downloads automatically.

### Step 1: View Download Options

```bash
llf model -h
```

**Output:**
```
usage: llf model [-h] {download,list,info} ...

Download, list, and manage LLM models

positional arguments:
  download     Download a model from HuggingFace Hub or URL
  list         List all downloaded models
  info         Show detailed model information

Examples:
  llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf model list
  llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### Step 2: Download a GGUF Model (Recommended)

**Download pre-converted GGUF model:**
```bash
# Download Qwen 2.5 Coder (GGUF - ready to use)
llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

**What happens:**
- Model downloads to `models/` directory
- Progress bar shows download status
- Model saved as: `models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/`
- GGUF file ready to use immediately

### Step 3: Download Non-GGUF Model (Requires Conversion)

**Download model that needs conversion:**
```bash
# Download Llama model (will need GGUF conversion)
llf model download --huggingface-model meta-llama/Llama-3.1-8B-Instruct
```

**What happens:**
- Model downloads to `models/` directory
- Contains `.safetensors` files
- Needs conversion before use (see [Converting Models](#converting-models-to-gguf-format))

### Step 4: Verify Download

**List downloaded models:**
```bash
llf model list
```

**Example output:**
```
Available models in /path/to/models/:
  1. Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
     └─ qwen2.5-coder-7b-instruct-q5_k_m.gguf (4.8 GB)

  2. meta-llama--Llama-3.1-8B-Instruct/
     └─ model-00001-of-00004.safetensors (4.9 GB)
     └─ model-00002-of-00004.safetensors (4.9 GB)
     └─ ... (needs GGUF conversion)
```

### Step 5: Get Model Information

**View model details:**
```bash
# Default model info
llf model info

# Specific model info
llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

**Example output:**
```
Model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
Location: /path/to/models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF
Format: GGUF
Size: 4.8 GB
Status: Ready to use
```

### Alternative: Direct URL Download

For direct GGUF file links:

```bash
llf model download --url https://example.com/model.gguf --name my-custom-model
```

### Download to Custom Directory

```bash
# Use custom models directory
llf -d /custom/models model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

---

## Converting Models to GGUF Format

If you downloaded a model that is NOT in GGUF format, you need to convert it.

### When to Convert

**Check your model directory:**
```bash
ls -la models/your-model-name/
```

**If you see `.safetensors` or `.bin` files** → Need conversion
**If you see `.gguf` files** → Already ready to use

### Understanding the Conversion Script

The conversion script:
- Converts HuggingFace format (`.safetensors`) to GGUF
- Quantizes the model to reduce size
- Saves result in new directory

**Location:** `bin/tools/convert_huggingface_llm_2_gguf.sh`

### Step 1: View Conversion Help

```bash
./bin/tools/convert_huggingface_llm_2_gguf.sh -h
```

**Output:**
```
Usage: ./bin/tools/convert_huggingface_llm_2_gguf.sh -s <HuggingFace Model> -d <GGUF Model Name> [-f]

   -s <HuggingFace Model> - Name of the downloaded HuggingFace model to convert
   -d <GGUF Model Name>   - Name for the GGUF converted model
   -f                     - Force rebuild (delete existing GGUF and rebuild)

NOTE: Models are located in the "models" directory

EXAMPLE:
 ./bin/tools/convert_huggingface_llm_2_gguf.sh -s Qwen--Qwen2.5-Coder-7B-Instruct -d Qwen--Qwen2.5-Coder-7B-Instruct-GGUF
```

### Step 2: Understanding Quantization Types

The script uses `q5_K_M` quantization by default (good balance):

**Quantization comparison:**

| Type | Size | Quality | RAM Needed | Notes |
|------|------|---------|------------|-------|
| `f16` | 100% | Highest | 110-120 GB | Full precision, huge |
| `q8_0` | 50% | Very High | 55-60 GB | Near-perfect quality |
| `q6_K` | 40% | High | 45-50 GB | Excellent quality |
| `q5_K_M` | 35% | Good | 36-40 GB | ✅ **Recommended** |
| `q4_K_M` | 28% | Decent | 30-34 GB | Good for limited RAM |
| `q3_K_M` | 22% | Lower | 24-28 GB | Compact but quality loss |

**Note:** Percentages are relative to full f16 size for a 70B model. Smaller models have proportionally smaller sizes.

### Step 3: Convert the Model

**Basic conversion:**
```bash
./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s meta-llama--Llama-3.1-8B-Instruct \
  -d Llama-3.1-8B-Instruct-GGUF
```

**What happens:**
1. Reads HuggingFace model from `models/meta-llama--Llama-3.1-8B-Instruct/`
2. Converts to GGUF f16 format (intermediate)
3. Quantizes to q5_K_M (final)
4. Saves to `models/Llama-3.1-8B-Instruct-GGUF/`
5. Deletes intermediate f16 file

**Force rebuild (overwrite existing):**
```bash
./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s meta-llama--Llama-3.1-8B-Instruct \
  -d Llama-3.1-8B-Instruct-GGUF \
  -f
```

### Step 4: Monitor Conversion

**Expected output:**
```
Converting the HuggingFace LLM to GGUF format
Loading model from models/meta-llama--Llama-3.1-8B-Instruct/...
Writing GGUF format...
Successfully converted the model

Quantizing the GGUF formatted LLM
main: quantizing 'models/Llama-3.1-8B-Instruct-GGUF/Llama-3.1-8B-Instruct_f16' to 'models/Llama-3.1-8B-Instruct-GGUF/Llama-3.1-8B-Instruct_f16_q5_K_M.gguf' as q5_K_M
Successfully quantizing the model
```

**Conversion time:**
- Small models (3-7B): 5-15 minutes
- Medium models (7-13B): 15-30 minutes
- Large models (30-70B): 30-60+ minutes

### Step 5: Verify Conversion

```bash
# Check the GGUF directory
ls -lh models/Llama-3.1-8B-Instruct-GGUF/

# Should see a .gguf file
# Example: Llama-3.1-8B-Instruct_f16_q5_K_M.gguf
```

### Step 6: Test the Converted Model

**Optional: Test with llama.cpp directly:**
```bash
../llama.cpp/build/bin/llama-cli \
  -m models/Llama-3.1-8B-Instruct-GGUF/Llama-3.1-8B-Instruct_f16_q5_K_M.gguf \
  -p "Write a Python hello world program"
```

If this works, your model is ready for LLF!

### Step 7: Update Model List

```bash
llf model list
```

**Should now show the new GGUF model:**
```
Available models in /path/to/models/:
  1. Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
     └─ qwen2.5-coder-7b-instruct-q5_k_m.gguf (4.8 GB)

  2. Llama-3.1-8B-Instruct-GGUF/
     └─ Llama-3.1-8B-Instruct_f16_q5_K_M.gguf (5.2 GB)

  3. meta-llama--Llama-3.1-8B-Instruct/  (original - can be deleted)
     └─ model-00001-of-00004.safetensors (4.9 GB)
     └─ ...
```

---

## Configuring Single LLM Server

After downloading and optionally converting your model, configure it in `configs/config.json`.

### Understanding Configuration Structure

**Single server format:**
```json
{
  "local_llm_server": {
    "llama_server_path": "/path/to/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "model_dir": "Model-Directory-Name",
    "gguf_file": "model-file.gguf"
  },
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "model_name": "Model/Name"
  }
}
```

### Step 1: Find Required Information

**Find llama-server path:**
```bash
# If llama.cpp is in parent directory
ls ../llama.cpp/build/bin/llama-server

# Find absolute path
which llama-server
```

**Find model directory:**
```bash
llf model list
# Note the directory name (e.g., "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF")
```

**Find GGUF filename:**
```bash
ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
# Note the .gguf file name
```

### Step 2: Edit config.json

Open `configs/config.json` in your editor:

```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "healthcheck_interval": 2.0,
    "auto_start": false,
    "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
    "gguf_file": "qwen2.5-coder-7b-instruct-q5_k_m.gguf"
  },
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
  },
  "model_dir": "models",
  "cache_dir": ".cache",
  "log_level": "ERROR"
}
```

### Step 3: Key Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `llama_server_path` | Path to llama-server binary | `../llama.cpp/build/bin/llama-server` |
| `server_host` | Bind address (localhost) | `127.0.0.1` |
| `server_port` | Port number | `8000` |
| `model_dir` | Model directory name | `Qwen--Qwen2.5-Coder-7B-Instruct-GGUF` |
| `gguf_file` | GGUF filename | `qwen2.5-coder-7b-instruct-q5_k_m.gguf` |
| `api_base_url` | Server URL | `http://127.0.0.1:8000/v1` |
| `model_name` | Model identifier | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` |

The `model_dir` can be obtained by looking in the `models` directory by running `ls models`.

The `gguf_file` can be obtaind by looking in the directory in the `models` directory and find the .gguf file by running `ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF`

### Step 4: Verify Configuration

```bash
# This should show no errors
llf server status
```

**Expected output:**
```
Server is not running
```

That's correct - server isn't running yet, but config is valid!

### Step 5: Start the Server

```bash
llf server start --daemon
```

### Step 6: Test with Chat

```bash
llf chat
```

Type a message and verify the model responds correctly!

---

## Configuring Multiple LLM Servers

Running multiple LLM servers allows you to switch between different models easily.

### When to Use Multiple Servers

**Use multiple servers when:**
- You want different models for different tasks
- You're comparing model performance
- You have enough RAM to run multiple models
- You want to switch models without restarting

**Use single server when:**
- Limited RAM (< 16 GB)
- Only use one model
- Simpler setup preferred

### Understanding Multi-Server Configuration

**Multi-server format uses an array:**
```json
{
  "local_llm_servers": [
    {
      "name": "server-1",
      "server_port": 8000,
      "model_dir": "Model1-GGUF",
      "gguf_file": "model1.gguf"
    },
    {
      "name": "server-2",
      "server_port": 8001,
      "model_dir": "Model2-GGUF",
      "gguf_file": "model2.gguf"
    }
  ],
  "llm_endpoint": {
    "default_local_server": "server-1"
  }
}
```

### Step 1: Download Multiple Models

```bash
# Download coding model
llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

# Download general chat model
llf model download --huggingface-model meta-llama/Llama-3.1-8B-Instruct-GGUF

# Download lightweight model
llf model download --huggingface-model meta-llama/Llama-3.2-3B-Instruct-GGUF
```

**Wait for all downloads to complete:**
```bash
llf model list
```

### Step 2: Convert Models (if needed)

If any models need GGUF conversion:

```bash
./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s meta-llama--Llama-3.1-8B-Instruct \
  -d Llama-3.1-8B-Instruct-GGUF

./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s meta-llama--Llama-3.2-3B-Instruct \
  -d Llama-3.2-3B-Instruct-GGUF
```

### Step 3: Create Multi-Server Configuration

**Edit `configs/config.json`:**

In the below configuration the `model_dir` can be obtained by looking in the `models` directory by running `ls models`.  The `gguf_file` can be obtaind by looking in the directory in the `models` directory and find the .gguf file by running `ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF`

```json
{
  "local_llm_servers": [
    {
      "name": "qwen-coder",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8000,
      "healthcheck_interval": 2.0,
      "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
      "gguf_file": "qwen2.5-coder-7b-instruct-q5_k_m.gguf",
      "auto_start": false
    },
    {
      "name": "llama-chat",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8001,
      "healthcheck_interval": 2.0,
      "model_dir": "Llama-3.1-8B-Instruct-GGUF",
      "gguf_file": "Llama-3.1-8B-Instruct_f16_q5_K_M.gguf",
      "auto_start": false
    },
    {
      "name": "llama-small",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8002,
      "healthcheck_interval": 2.0,
      "model_dir": "Llama-3.2-3B-Instruct-GGUF",
      "gguf_file": "llama-3.2-3b-instruct-q5_k_m.gguf",
      "auto_start": false
    }
  ],
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
    "default_local_server": "qwen-coder"
  },
  "model_dir": "models",
  "cache_dir": ".cache",
  "log_level": "ERROR"
}
```

### Step 4: Important Multi-Server Requirements

**Each server must have:**
- ✅ Unique `name`
- ✅ Unique `server_port` (8000, 8001, 8002, etc.)
- ✅ Valid `model_dir` and `gguf_file`
- ✅ Same `llama_server_path`

**The llm_endpoint must have:**
- ✅ `default_local_server` matching one server's `name`
- ✅ `api_base_url` matching default server's port

### Step 5: Verify Multi-Server Configuration

```bash
llf server list
```

**Expected output:**
```
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ NAME         ┃ PORT ┃ STATUS  ┃ MODEL                      ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ qwen-coder   │ 8000 │ Stopped │ Qwen--Qwen2.5-Coder-7B-... │
│ llama-chat   │ 8001 │ Stopped │ Llama-3.1-8B-Instruct-GGUF │
│ llama-small  │ 8002 │ Stopped │ Llama-3.2-3B-Instruct-GGUF │
├──────────────┼──────┼─────────┼────────────────────────────┤
│ Active → qwen-coder │ 8000 │ Stopped │ Qwen--Qwen2.5-Coder... │
└──────────────┴──────┴─────────┴────────────────────────────┘
```

Perfect! All servers are configured.

---

## Managing Multiple Servers

Commands for controlling multiple LLM servers.

### List All Servers

```bash
llf server list
```

Shows all configured servers, their status, and which is active.

### Start Specific Server

**Start by name:**
```bash
# Start the coding model
llf server start qwen-coder

# Start the chat model
llf server start llama-chat

# Start the small model
llf server start llama-small
```

**Start in daemon mode (background):**
```bash
llf server start qwen-coder --daemon
```

**Start with force (skip RAM warning):**
```bash
llf server start llama-chat --force
```

### Check Server Status

**Check specific server:**
```bash
llf server status qwen-coder
```

**Check all servers:**
```bash
llf server list
```

**Example output with running servers:**
```
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ NAME         ┃ PORT ┃ STATUS  ┃ MODEL                      ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ qwen-coder   │ 8000 │ Running │ Qwen--Qwen2.5-Coder-7B-... │
│ llama-chat   │ 8001 │ Running │ Llama-3.1-8B-Instruct-GGUF │
│ llama-small  │ 8002 │ Stopped │ Llama-3.2-3B-Instruct-GGUF │
├──────────────┼──────┼─────────┼────────────────────────────┤
│ Active → qwen-coder │ 8000 │ Running │ Qwen--Qwen2.5-Coder... │
└──────────────┴──────┴─────────┴────────────────────────────┘
```

### Stop Specific Server

```bash
# Stop coding model
llf server stop qwen-coder

# Stop chat model
llf server stop llama-chat
```

### Restart Server

```bash
llf server restart qwen-coder
```

### Start Multiple Servers Simultaneously

**Start all servers you need:**
```bash
# Terminal 1
llf server start qwen-coder --daemon

# Terminal 2 (or same terminal)
llf server start llama-chat --daemon

# Both servers now running!
llf server list
```

---

## Switching Between LLMs

Change which LLM is active without stopping/starting servers.

### Understanding Server Switching

**The active server:**
- Defined by `default_local_server` in config.json
- Determines which model `llf chat` uses
- Can be changed with one command
- Updates `llm_endpoint` automatically

### Method 1: Use llf server switch (Recommended)

**Switch to different server:**
```bash
# Switch to coding model
llf server switch qwen-coder

# Switch to chat model
llf server switch llama-chat

# Switch to small model
llf server switch llama-small
```

**What happens:**
- Updates `default_local_server` in config.json
- Updates `api_base_url` to match server's port
- Changes take effect immediately
- No need to restart anything

**Verify the switch:**
```bash
llf server list
```

**Output shows active server:**
```
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ NAME         ┃ PORT ┃ STATUS  ┃ MODEL                      ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ qwen-coder   │ 8000 │ Running │ Qwen--Qwen2.5-Coder-7B-... │
│ llama-chat   │ 8001 │ Running │ Llama-3.1-8B-Instruct-GGUF │
│ llama-small  │ 8002 │ Stopped │ Llama-3.2-3B-Instruct-GGUF │
├──────────────┼──────┼─────────┼────────────────────────────┤
│ Active → llama-chat │ 8001 │ Running │ Llama-3.1-8B-Instru... │
└──────────────┴──────┴─────────┴────────────────────────────┘
```

### Method 2: Manual Configuration Edit

**Edit `configs/config.json` directly:**

```json
{
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8001/v1",
    "default_local_server": "llama-chat"
  }
}
```

**Remember to:**
- Update both `default_local_server` and `api_base_url`
- Match port number to server's `server_port`
- Save the file

### Testing the Active LLM

**Start chat to verify:**
```bash
llf chat
```

**Ask the model to identify itself:**
```
You: What model are you?
LLM: I am Llama 3.1 8B Instruct...
```

**Switch and test again:**
```bash
# Switch to coding model
llf server switch qwen-coder

# Chat again
llf chat
```

```
You: What model are you?
LLM: I am Qwen 2.5 Coder 7B...
```

### Example Workflow: Switching for Different Tasks

**Morning: Coding tasks**
```bash
llf server start qwen-coder --daemon
llf chat
# Work on code...
```

**Afternoon: General chat**
```bash
llf server start llama-chat --daemon  # Start if not running
llf server switch llama-chat
llf chat
# General conversation...
```

**Evening: Quick queries**
```bash
llf server start llama-small --daemon  # Start if not running
llf server switch llama-small
llf chat
# Fast responses...
```

---

## Cleanup and Disk Space Management

After converting models to GGUF, you can delete original downloads to save disk space.

You can use the following command to delete models that are not used or not needed:
```bash
#  List the existing models and select the one you want to delete
llf model list
#  Delete the model you no longer need
llf model delete <local LLM name>
```

### Understanding Disk Usage

**Typical sizes:**
- Original HuggingFace model: 7-14 GB (for 7B model)
- GGUF q5_K_M model: 4-6 GB (for 7B model)
- **Savings**: 3-8 GB per model

**Multiple models add up:**
- 3 models with originals: ~40-50 GB
- 3 models GGUF only: ~15-20 GB
- **Savings**: 25-30 GB

### Step 1: Verify GGUF Model Works

**Before deleting anything, test the GGUF model:**

```bash
# Start server with GGUF model
llf server start qwen-coder --daemon

# Test it works
llf chat
# Verify responses are correct

# Stop server
llf server stop qwen-coder
```

**Only proceed if GGUF model works perfectly!**

### Step 2: Identify Models to Delete

```bash
llf model list
```

**Example output:**
```
Available models in /path/to/models/:
  1. Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/     ← GGUF (KEEP)
     └─ qwen2.5-coder-7b-instruct-q5_k_m.gguf (4.8 GB)

  2. Qwen--Qwen2.5-Coder-7B-Instruct/          ← Original (DELETE)
     └─ model-00001-of-00004.safetensors (4.9 GB)
     └─ model-00002-of-00004.safetensors (4.9 GB)
     └─ config.json, tokenizer.json, etc.

  3. Llama-3.1-8B-Instruct-GGUF/               ← GGUF (KEEP)
     └─ Llama-3.1-8B-Instruct_f16_q5_K_M.gguf (5.2 GB)

  4. meta-llama--Llama-3.1-8B-Instruct/        ← Original (DELETE)
     └─ model.safetensors (8.5 GB)
```

**Keep directories ending in:**
- `-GGUF` ✅

**Delete directories:**
- Original HuggingFace models (without `-GGUF` suffix) ❌

### Step 3: Delete Original Models

**Delete original HuggingFace models:**

```bash
# Navigate to models directory
cd models

# Delete original Qwen model
rm -rf Qwen--Qwen2.5-Coder-7B-Instruct

# Delete original Llama model
rm -rf meta-llama--Llama-3.1-8B-Instruct

# Return to project root
cd ..
```

**Verify deletion:**
```bash
llf model list
```

**Should only show GGUF models:**
```
Available models in /path/to/models/:
  1. Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
     └─ qwen2.5-coder-7b-instruct-q5_k_m.gguf (4.8 GB)

  2. Llama-3.1-8B-Instruct-GGUF/
     └─ Llama-3.1-8B-Instruct_f16_q5_K_M.gguf (5.2 GB)
```

### Step 4: Check Disk Space Saved

```bash
# Check models directory size
du -sh models/

# Check individual model sizes
du -sh models/*/
```

### Safety Tips

**Before deleting:**
- ✅ Test GGUF model works completely
- ✅ Verify you can chat with it
- ✅ Test model generates good responses
- ✅ Make sure server starts without errors

**Don't delete:**
- ❌ GGUF models (directories ending in `-GGUF`)
- ❌ Models still in config.json
- ❌ Models you haven't tested yet

**Backup option:**
```bash
# Move to backup instead of deleting
mkdir -p models_backup
mv models/Qwen--Qwen2.5-Coder-7B-Instruct models_backup/

# Delete later after confirming GGUF works
```

---

## Troubleshooting

Common issues when setting up multiple LLMs.

### Problem: "Model not found" Error

**Symptoms:**
```
Error: Model file not found
Path: models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/model.gguf
```

**Solutions:**

1. **Check model directory exists:**
   ```bash
   ls models/
   # Verify directory name matches config
   ```

2. **Check GGUF file exists:**
   ```bash
   ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
   # Verify .gguf filename matches config
   ```

3. **Fix config.json:**
   ```json
   {
     "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
     "gguf_file": "qwen2.5-coder-7b-instruct-q5_k_m.gguf"
   }
   ```

4. **Use exact filenames:**
   - Directory names are case-sensitive
   - Use `llf model list` to get exact names

### Problem: "Port Already in Use"

**Error:**
```
Error: Address already in use (port 8000)
```

**Solutions:**

1. **Check which servers are running:**
   ```bash
   llf server list
   ```

2. **Stop conflicting server:**
   ```bash
   llf server stop qwen-coder
   ```

3. **Use different port:**
   ```json
   {
     "server_port": 8001
   }
   ```

4. **Kill process using port:**
   ```bash
   # Find process
   lsof -i :8000

   # Kill it
   kill -9 PID
   ```

### Problem: Conversion Script Fails

**Error:**
```
Error converting the model
```

**Solutions:**

1. **Check llama.cpp is compiled:**
   ```bash
   ls ../llama.cpp/build/bin/llama-quantize
   ls ../llama.cpp/convert_hf_to_gguf.py
   ```

2. **Verify source model exists:**
   ```bash
   ls models/meta-llama--Llama-3.1-8B-Instruct/
   # Should have .safetensors files
   ```

3. **Check disk space:**
   ```bash
   df -h .
   # Need at least 20GB free for 7B model
   ```

4. **Try with force flag:**
   ```bash
   ./bin/tools/convert_huggingface_llm_2_gguf.sh -s MODEL -d MODEL-GGUF -f
   ```

5. **Check Python environment:**
   ```bash
   source llf_venv/bin/activate
   python --version  # Should be 3.8+
   ```

### Problem: Server Won't Start

**Error:**
```
Failed to start server
```

**Solutions:**

1. **Check llama-server path:**
   ```bash
   ls ../llama.cpp/build/bin/llama-server
   # Should exist and be executable
   ```

2. **Check model file:**
   ```bash
   ls models/MODEL-DIR/model.gguf
   # Should exist
   ```

3. **Check RAM available:**
   ```bash
   # macOS
   vm_stat

   # Linux
   free -h
   ```

4. **Use force flag (skip RAM check):**
   ```bash
   llf server start qwen-coder --force
   ```

5. **Check config.json syntax:**
   ```bash
   python -m json.tool configs/config.json
   # Should show no errors
   ```

### Problem: "Server not responding"

**Symptoms:**
- Server starts but chat hangs
- No responses from LLM

**Solutions:**

1. **Check server status:**
   ```bash
   llf server status qwen-coder
   ```

2. **Check server logs:**
   ```bash
   # If running in foreground, check terminal output
   # Look for error messages
   ```

3. **Restart server:**
   ```bash
   llf server stop qwen-coder
   llf server start qwen-coder --daemon
   ```

4. **Test server directly:**
   ```bash
   curl http://127.0.0.1:8000/v1/models
   ```

5. **Check model loaded:**
   ```bash
   llf server status qwen-coder
   # Should show "Running"
   ```

### Problem: Wrong Model Responding

**Symptoms:**
- Asked for coding help, got general responses
- Model doesn't match expected behavior

**Solutions:**

1. **Check active server:**
   ```bash
   llf server list
   # Look at "Active →" line
   ```

2. **Switch to correct server:**
   ```bash
   llf server switch qwen-coder
   ```

3. **Verify model in config:**
   ```bash
   cat configs/config.json | grep default_local_server
   ```

4. **Restart chat:**
   ```bash
   # Exit current chat (Ctrl+C)
   llf chat
   ```

---

## Best Practices

### Model Selection

1. **Start Small**
   - Begin with 3-7B models
   - Easier to manage
   - Less RAM required
   - Faster responses

2. **Match Model to Task**
   - Coding: Qwen Coder, DeepSeek Coder, CodeLlama
   - Chat: Llama 3, Mistral, Nous Hermes
   - Lightweight: Phi-3, Llama 3.2 3B

3. **Test Before Committing**
   - Download and test one model first
   - Verify it works with your hardware
   - Then expand to more models

### Configuration Management

1. **Use Consistent Naming**
   ```
   Good:
   - qwen-coder (server name)
   - Qwen--Qwen2.5-Coder-7B-Instruct-GGUF (model dir)

   Avoid:
   - server1, server2 (not descriptive)
   - random names
   ```

2. **Document Your Setup**
   ```bash
   # Create a notes file
   cat > MODEL_NOTES.txt <<EOF
   qwen-coder: Port 8000, for coding tasks
   llama-chat: Port 8001, for general chat
   llama-small: Port 8002, for quick queries
   EOF
   ```

3. **Use Sequential Ports**
   ```
   Server 1: 8000
   Server 2: 8001
   Server 3: 8002
   (easier to remember)
   ```

4. **Backup Configurations**
   ```bash
   cp configs/config.json configs/config.backup.json
   ```

### Resource Management

1. **Monitor RAM Usage**
   ```bash
   # macOS
   top

   # Linux
   htop

   # Look for llama-server processes
   ```

2. **Don't Run All Servers Simultaneously**
   - Only run servers you're actively using
   - Stop servers when done
   - Save RAM for other applications

3. **Use Appropriate Quantization**
   - q5_K_M: Good balance (recommended)
   - q4_K_M: If RAM limited
   - q8_0: If RAM plentiful and want quality

### Disk Space Management

1. **Delete Original Models**
   - After GGUF conversion works
   - Save 50-70% disk space
   - Keep GGUF versions only

2. **Regular Cleanup**
   ```bash
   # Remove unused models
   llf model list
   # Delete models you don't use
   ```

3. **Use External Storage**
   - Store models on external drive
   - Update `model_dir` in config
   - Save main drive space

### Switching Workflow

1. **Plan Your Day**
   ```bash
   # Morning: Start coding model
   llf server start qwen-coder --daemon

   # Afternoon: Switch to chat
   llf server switch llama-chat

   # End of day: Stop all
   llf server stop qwen-coder
   llf server stop llama-chat
   ```

2. **Use Aliases**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias llf-code='llf server switch qwen-coder'
   alias llf-chat='llf server switch llama-chat'
   alias llf-small='llf server switch llama-small'
   ```

---

## Summary

You now know how to download, convert, and configure multiple LLM models for the Local LLM Framework.

### Key Takeaways

1. **Finding Models**:
   - HuggingFace is the primary source
   - Look for GGUF format (easiest)
   - Choose models matching your hardware

2. **Downloading Models**:
   ```bash
   llf model download --huggingface-model MODEL_ID
   llf model list
   ```

3. **Converting to GGUF**:
   ```bash
   ./bin/tools/convert_huggingface_llm_2_gguf.sh -s SOURCE -d DEST
   ```

4. **Single Server Config**:
   - Use `local_llm_server` (singular)
   - One model at a time
   - Simpler setup

5. **Multiple Server Config**:
   - Use `local_llm_servers` (array)
   - Unique name and port for each
   - Easy switching between models

6. **Managing Servers**:
   ```bash
   llf server list              # View all servers
   llf server start NAME        # Start specific server
   llf server stop NAME         # Stop specific server
   llf server switch NAME       # Switch active LLM
   ```

7. **Cleanup**:
   - Delete original models after GGUF conversion
   - Save 50-70% disk space
   - Only delete after testing GGUF works

### Quick Reference

**Download and setup workflow:**
```bash
# 1. Download model
llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

# 2. List models
llf model list

# 3. Convert if needed (skip if already GGUF)
./bin/tools/convert_huggingface_llm_2_gguf.sh -s SOURCE -d DEST-GGUF

# 4. Configure in config.json
# Edit configs/config.json

# 5. Verify configuration
llf server list

# 6. Start server
llf server start qwen-coder --daemon

# 7. Test
llf chat
```

**Multi-server workflow:**
```bash
# List all servers
llf server list

# Start server
llf server start qwen-coder --daemon

# Switch active model
llf server switch llama-chat

# Check status
llf server status qwen-coder

# Stop server
llf server stop qwen-coder
```

### Configuration Templates

**Single server template:**
```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server",
    "server_host": "127.0.0.1",
    "server_port": 8000,
    "model_dir": "MODEL-DIR-GGUF",
    "gguf_file": "model.gguf"
  },
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "model_name": "Model/Name"
  }
}
```

**Multi-server template:**
```json
{
  "local_llm_servers": [
    {
      "name": "server-1",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_port": 8000,
      "model_dir": "Model1-GGUF",
      "gguf_file": "model1.gguf"
    },
    {
      "name": "server-2",
      "llama_server_path": "../llama.cpp/build/bin/llama-server",
      "server_port": 8001,
      "model_dir": "Model2-GGUF",
      "gguf_file": "model2.gguf"
    }
  ],
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "default_local_server": "server-1"
  }
}
```

### Recommended Model Combinations

**For 16GB RAM:**
```
1. Qwen 2.5 Coder 7B (coding)
2. Llama 3.2 3B (lightweight chat)
```

**For 32GB RAM:**
```
1. Qwen 2.5 Coder 7B (coding)
2. Llama 3.1 8B (general chat)
3. Phi-3 Mini (quick queries)
```

**For 64GB+ RAM:**
```
1. Qwen 3 Coder 30B (advanced coding)
2. Llama 3.1 8B (general chat)
3. Mistral 7B (specialized tasks)
```

### Related Documentation

- [Basic User Guide](../Basic_User_Guide.md) - Getting started with single LLM
- [Setup External LLM](Setup_External_LLM.md) - Use ChatGPT, Claude instead of local
- [Setup Network Access - LLM](Setup_Network_Access_LLM.md) - Share LLM on network
- [Troubleshooting](Troubleshooting.md) - Solutions to common problems

---

**You're now ready to run multiple LLM models with the Local LLM Framework!**

Start small, test thoroughly, and expand as you learn what works best for your use case.

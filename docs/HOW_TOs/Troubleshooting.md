# Troubleshooting Guide

This guide helps you resolve common issues when using the Local LLM Framework.

---

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Server Issues](#server-issues)
- [Model Issues](#model-issues)
- [Configuration Issues](#configuration-issues)
- [Memory & RAG Issues](#memory--rag-issues)
- [Installation & Dependencies](#installation--dependencies)
- [Performance Issues](#performance-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Error Messages Reference](#error-messages-reference)

---

## Quick Diagnostics

### Check Your Environment

```bash
# Verify you're in the virtual environment
echo $VIRTUAL_ENV
# Should show: /path/to/local_llm_framework/llf_venv

# If empty, activate it:
source llf_venv/bin/activate

# Verify Python version
python --version
# Should be Python 3.7+

# Check LLF installation
llf --version
```

### Run Basic Tests

```bash
# Test configuration loading
llf info

# List downloaded models
llf list

# Check server status
llf server status

# List configured servers (if using multi-server)
llf server list
```

---

## Server Issues

### "llama-server binary not found"

**Error:**
```
llama-server binary not found at: /path/to/llama-server
Please compile llama.cpp first or configure the correct path.
```

**Solutions:**

1. **Build llama.cpp:**
   ```bash
   # Clone repository
   cd ..
   git clone https://github.com/ggml-org/llama.cpp.git

   # Build
   cd llama.cpp
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release

   # Verify
   ./bin/llama-server --version
   ```

2. **Update config path:**
   Edit `configs/config.json`:
   ```json
   {
     "local_llm_server": {
       "llama_server_path": "../llama.cpp/build/bin/llama-server"
     }
   }
   ```

---

### "Server failed to start" or "Connection refused"

**Possible Causes:**
- Port already in use
- llama-server crashed on startup
- Insufficient permissions
- Missing model file

**Diagnostics:**

```bash
# Check if port is in use
lsof -i :8000

# Check server logs
tail -f logs/llf.log

# Try starting with debug logging
llf --log-level DEBUG server start
```

**Solutions:**

1. **Port Conflict:**
   ```json
   // Change port in configs/config.json
   {
     "local_llm_server": {
       "server_port": 8001
     }
   }
   ```

2. **Kill existing process:**
   ```bash
   # Find process using port 8000
   lsof -i :8000

   # Kill it
   kill -9 <PID>

   # Or use LLF command
   llf server stop
   ```

3. **Check model file exists:**
   ```bash
   # Verify model path
   llf info

   # Download if missing
   llf download
   ```

---

### "Server timeout" - Server takes too long to start

**Error:**
```
llama-server failed to become ready within 120 seconds
```

**Causes:**
- Large model file (loading takes time)
- Insufficient GPU memory (falling back to CPU)
- Corrupted GGUF file

**Solutions:**

1. **Wait longer** - First startup with large models can take 2-3 minutes
2. **Check available memory:**
   ```bash
   # On macOS
   vm_stat

   # On Linux
   free -h
   ```

3. **Try smaller quantization:**
   - Use Q4 instead of Q8 models (faster loading)
   - Example: `qwen2.5-coder-7b-instruct-q4_k_m.gguf` instead of `q8_0.gguf`

4. **Check GGUF file integrity:**
   ```bash
   # File should be several GB
   ls -lh models/*/*.gguf

   # Re-download if suspiciously small
   llf download --force
   ```

---

### Multiple Servers Running - Memory Issues

**Warning:**
```
⚠️  WARNING: The following servers are already running:
  • server_1 (port 8000)
Running multiple LLM servers simultaneously may cause memory issues.
```

**What this means:**
- Each LLM server loads an entire model into memory (2-8 GB+)
- Running multiple servers can exhaust system RAM
- The framework warns you before starting another server

**Solutions:**

1. **Stop unused servers:**
   ```bash
   llf server stop server_1
   ```

2. **Check running servers:**
   ```bash
   llf server list
   ```

3. **If you need multiple models:**
   - Ensure you have enough RAM (8GB per model minimum)
   - Use smaller quantized models (Q4 instead of Q8)
   - Consider switching models instead of running both

---

## Model Issues

### "Model not downloaded"

**Error:**
```
Model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF is not downloaded.
Please download it first using model_manager.download_model()
```

**Solution:**
```bash
# Download default model
llf download

# Download specific model
llf download "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"

# Download from URL
llf download --url https://example.com/model.gguf --name my-model
```

---

### "GGUF model file not found"

**Error:**
```
GGUF model file not found: /path/to/model.gguf
Model directory: /path/to/models/
Available files: ['different-file.gguf']
```

**Cause:** Mismatch between configured `gguf_file` and actual filename.

**Solutions:**

1. **Check what files exist:**
   ```bash
   ls -la models/Qwen--*/
   ```

2. **Update config to match:**
   ```json
   {
     "local_llm_server": {
       "gguf_file": "actual-filename-here.gguf"
     }
   }
   ```

3. **Model directory structure:**
   ```
   models/
   └── Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
       └── qwen2.5-coder-7b-instruct-q4_k_m.gguf
   ```

---

### Download Failed or Interrupted

**Issues:**
- Network timeout
- Insufficient disk space
- HuggingFace rate limiting

**Solutions:**

1. **Resume download:**
   ```bash
   # LLF supports resume automatically
   llf download
   ```

2. **Check disk space:**
   ```bash
   df -h
   # Need 5-20GB free depending on model
   ```

3. **Use different HuggingFace mirror:**
   ```bash
   export HF_ENDPOINT=https://hf-mirror.com
   llf download
   ```

4. **Authenticate for gated models:**
   ```bash
   # Get token from https://huggingface.co/settings/tokens
   export HF_TOKEN=your_token_here
   llf download
   ```

---

### Wrong Model Format

**Issue:** Downloaded regular PyTorch model instead of GGUF.

**Identification:**
- No `.gguf` files in model directory
- Has `.bin` or `.safetensors` files instead

**Solution:**
```bash
# Ensure you download GGUF version
llf download "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
#                                              ^^^^^ GGUF suffix important

# If you have non-GGUF model, you need to convert it
# See: bin/tools/convert_huggingface_llm_2_gguf.sh
```

---

## Configuration Issues

### "Invalid JSON in config file"

**Common Mistakes:**

1. **Trailing commas:**
   ```json
   // ❌ WRONG
   {
     "model_name": "test",
   }

   // ✅ CORRECT
   {
     "model_name": "test"
   }
   ```

2. **Missing commas:**
   ```json
   // ❌ WRONG
   {
     "server_port": 8000
     "server_host": "127.0.0.1"
   }

   // ✅ CORRECT
   {
     "server_port": 8000,
     "server_host": "127.0.0.1"
   }
   ```

3. **Comments not allowed in JSON:**
   ```json
   // ❌ WRONG - JSON doesn't support // comments
   {
     // This is my config
     "model_name": "test"
   }

   // ✅ Use config examples instead
   ```

**Fix:**
```bash
# Validate JSON syntax
cat configs/config.json | python -m json.tool

# If errors, check line numbers shown
# Or use example configs:
cp configs/config_examples/config_local_gguf.json configs/config.json
```

---

### "Invalid tool_execution_mode"

**Error:**
```
Invalid tool_execution_mode 'dual_pass'. Must be one of: single_pass, dual_pass_write_only, dual_pass_all
```

**Valid modes:**
- `single_pass` - No streaming with tool calls (default, most reliable)
- `dual_pass_write_only` - Stream for write operations only
- `dual_pass_all` - Stream for all tool operations (experimental)

**Fix:**
```json
{
  "llm_endpoint": {
    "tool_execution_mode": "single_pass"
  }
}
```

---

### Relative Path Issues

**Understanding Path Resolution:**
- All relative paths resolve from `PROJECT_ROOT` (the repo directory)
- `../llama.cpp/` means one level above project root

**Example:**
```
/home/user/
├── local_llm_framework/      ← PROJECT_ROOT
│   ├── configs/config.json
│   └── models/
└── llama.cpp/                 ← "../llama.cpp" from PROJECT_ROOT
    └── build/bin/llama-server
```

**Config:**
```json
{
  "local_llm_server": {
    "llama_server_path": "../llama.cpp/build/bin/llama-server"
  }
}
```

---

### External API Configuration

**Using OpenAI/Anthropic instead of local server:**

```json
{
  "llm_endpoint": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": "sk-your-key-here",
    "model_name": "gpt-4"
  }
}
```

**Important:**
- No need for `local_llm_server` section when using external API
- No need to build llama.cpp
- Must have valid API key
- Internet connection required

**Test:**
```bash
llf chat "Hello"
# Should connect to external API, not local server
```

---

## Memory & RAG Issues

### "Memory manager not available"

**Error when using memory tools:**
```json
{
  "success": false,
  "error": "Memory manager not available"
}
```

**Solutions:**

1. **Check memory is enabled:**
   ```bash
   # View memory status
   llf memory list

   # Enable memory
   llf memory enable main_memory
   ```

2. **Verify registry:**
   ```bash
   cat memory/memory_registry.json
   ```

   Should have:
   ```json
   {
     "memories": [
       {
         "name": "main_memory",
         "enabled": true
       }
     ]
   }
   ```

3. **Create memory if missing:**
   ```bash
   ./bin/tools/create_memory.py main_memory
   llf memory enable main_memory
   ```

---

### "faiss-cpu is required"

**Error:**
```
ImportError: faiss-cpu is required. Install: pip install faiss-cpu
```

**Solution:**
```bash
source llf_venv/bin/activate
pip install faiss-cpu
```

**For Apple Silicon (M1/M2):**
```bash
# Use conda instead
conda install -c conda-forge faiss-cpu
```

---

### RAG Vector Store Not Found

**Error:**
```
FileNotFoundError: FAISS index not found: /path/to/index.faiss
```

**Solutions:**

1. **Check data store registry:**
   ```bash
   cat data_stores/data_store_registry.json
   ```

2. **Verify store files exist:**
   ```bash
   ls -la data_stores/your_store/
   # Should have: index.faiss, metadata.jsonl, config.json
   ```

3. **Create vector store if missing:**
   ```bash
   # See: bin/tools/data_store/CREATE_VECTOR_STORE.sh
   cd bin/tools/data_store
   ./CREATE_VECTOR_STORE.sh
   ```

4. **Detach store if not needed:**
   Edit `data_stores/data_store_registry.json`:
   ```json
   {
     "attached": false
   }
   ```

---

### Embedding Model Download Issues

**Error:**
```
Failed to load embedding model: sentence-transformers/all-MiniLM-L6-v2
```

**Solutions:**

1. **Download embedding models:**
   ```bash
   cd bin/tools/data_store
   ./download_embedding_models.py
   ```

2. **Check internet connection:**
   ```bash
   ping huggingface.co
   ```

3. **Use different cache directory:**
   ```bash
   ./download_embedding_models.py --cache-dir /path/to/cache
   ```

---

## Installation & Dependencies

### "No module named 'llf'"

**Cause:** LLF not installed or not in virtual environment.

**Solutions:**

1. **Activate virtual environment:**
   ```bash
   source llf_venv/bin/activate
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   pip show local-llm-framework
   ```

---

### Missing Python Packages

**Common errors:**
- `No module named 'openai'`
- `No module named 'gradio'`
- `No module named 'sentence_transformers'`

**Solutions:**

1. **Reinstall all dependencies:**
   ```bash
   source llf_venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install specific package:**
   ```bash
   pip install openai gradio sentence-transformers
   ```

3. **Check for conflicts:**
   ```bash
   pip check
   ```

---

### Virtual Environment Not Activated

**Symptoms:**
- Commands not found
- Wrong Python version
- Packages not found

**Check:**
```bash
# Should show path to llf_venv
echo $VIRTUAL_ENV

# Should be True
python -c "import sys; print(sys.prefix != sys.base_prefix)"
```

**Fix:**
```bash
# Activate
source llf_venv/bin/activate

# On Windows
llf_venv\Scripts\activate
```

---

### Permission Denied Errors

**Issue:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**Solutions:**

1. **Make scripts executable:**
   ```bash
   chmod +x bin/start_llama_server.sh
   chmod +x bin/tools/create_memory.py
   ```

2. **Check directory permissions:**
   ```bash
   ls -la models/
   ls -la logs/

   # Fix if needed
   chmod -R u+w models/ logs/ memory/
   ```

---

## Performance Issues

### Slow Response Times

**Causes:**
- Large model on CPU (no GPU acceleration)
- Insufficient RAM (swapping to disk)
- Too many concurrent requests
- High `max_tokens` setting

**Solutions:**

1. **Use smaller model:**
   - 7B models instead of 13B/30B
   - Q4 quantization instead of Q8

2. **Check GPU usage:**
   ```bash
   # On systems with NVIDIA GPU
   nvidia-smi
   ```

3. **Reduce max_tokens:**
   ```json
   {
     "inference_params": {
       "max_tokens": 1024
     }
   }
   ```

4. **Monitor system resources:**
   ```bash
   # Check memory usage
   top

   # Check if swapping
   vm_stat | grep swap  # macOS
   swapon --show         # Linux
   ```

---

### High Memory Usage

**Issue:** System running out of RAM.

**Check memory:**
```bash
# See model size
ls -lh models/*//*.gguf

# Monitor usage
top
```

**Solutions:**

1. **Use smaller quantization:**
   - Q4_K_M: ~4GB RAM
   - Q5_K_M: ~5GB RAM
   - Q8_0: ~8GB RAM

2. **Close other applications**

3. **Stop unused servers:**
   ```bash
   llf server list
   llf server stop unused_server
   ```

4. **Limit context size in server params:**
   ```json
   {
     "local_llm_server": {
       "server_params": {
         "--ctx-size": 2048
       }
     }
   }
   ```

---

## Platform-Specific Issues

### macOS

#### "xcrun: error: invalid active developer path"

**Cause:** Xcode command line tools not installed.

**Fix:**
```bash
xcode-select --install
```

#### Audio/TTS Issues

**Error:**
```
ModuleNotFoundError: No module named 'objc'
```

**Fix:**
```bash
pip install pyobjc-framework-Cocoa
```

---

### Linux

#### "libgomp.so.1: cannot open shared object file"

**Cause:** Missing OpenMP library (needed for PyTorch).

**Fix:**
```bash
# Ubuntu/Debian
sudo apt-get install libgomp1

# Fedora/RHEL
sudo dnf install libgomp

# Arch
sudo pacman -S gcc-libs
```

#### Permission Denied for Audio Devices

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/dev/snd/...'
```

**Fix:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and back in, or:
newgrp audio
```

---

### Windows

#### Path Length Limitations

**Error:** Paths too long (>260 characters).

**Fix:**
1. Enable long paths in registry
2. Use shorter installation path
3. Or use WSL2 (Linux on Windows)

#### Encoding Issues

**Error:** Unicode decode errors.

**Fix:**
```bash
# Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
```

---

## Error Messages Reference

### Configuration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Config file not found` | Missing config.json | Copy from config_examples/ |
| `Invalid JSON` | Syntax error in JSON | Validate with `python -m json.tool` |
| `Invalid tool_execution_mode` | Wrong mode value | Use: single_pass, dual_pass_write_only, or dual_pass_all |

### Server Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `llama-server not found` | Binary path wrong | Build llama.cpp, update path in config |
| `Port already in use` | Another server running | Change port or stop other server |
| `Connection refused` | Server not running | Start server with `llf server start` |
| `Server timeout` | Startup too slow | Wait longer, use smaller model |

### Model Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Model not downloaded` | Missing model files | Run `llf download` |
| `GGUF file not found` | Wrong filename in config | Check actual filename, update config |
| `HfHubHTTPError` | Network or auth issue | Check internet, use HF token for gated models |

### Memory/RAG Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Memory manager not available` | Memory not enabled | Enable in memory_registry.json |
| `faiss-cpu is required` | Missing dependency | `pip install faiss-cpu` |
| `FAISS index not found` | Missing vector store | Create store or detach in registry |
| `sentence-transformers required` | Missing dependency | `pip install sentence-transformers` |

### Installation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `No module named 'llf'` | Not installed | `pip install -e .` |
| `Not in virtual environment` | Wrong Python env | `source llf_venv/bin/activate` |
| `Permission denied` | File permissions | `chmod +x` or `chmod u+w` |

---

## Getting Additional Help

### Enable Debug Logging

```bash
llf --log-level DEBUG chat
```

This shows detailed information about what the framework is doing.

### Check Log Files

```bash
# View recent logs
tail -f logs/llf.log

# Search for errors
grep ERROR logs/llf.log
```

### Gather System Info

```bash
# Python version
python --version

# LLF version
llf --version

# Installed packages
pip list | grep -E 'openai|gradio|faiss|sentence'

# System resources
free -h  # Linux
vm_stat  # macOS
```

### Report Issues

When reporting issues, include:
1. Error message (full traceback)
2. `llf --version` output
3. Operating system and version
4. Relevant config.json sections (remove API keys!)
5. Steps to reproduce
6. Log output with `--log-level DEBUG`

**GitHub Issues:** https://github.com/anthropics/local-llm-framework/issues

---

## Quick Command Reference

```bash
# Server Management
llf server start              # Start default server
llf server stop               # Stop server
llf server status             # Check status
llf server list               # List all servers

# Model Management
llf download                  # Download default model
llf list                      # List downloaded models
llf info                      # Show model info

# Memory Management
llf memory list               # List memory instances
llf memory enable <name>      # Enable memory
llf memory disable <name>     # Disable memory

# Chat
llf                          # Start chat
llf chat                     # Start chat
llf --log-level DEBUG chat   # Debug mode

# Configuration
llf -c /path/to/config.json  # Use custom config
llf --help                   # Show help
```

---

## Common Workflows

### First-Time Setup That's Not Working

```bash
# 1. Verify environment
source llf_venv/bin/activate
pip install -e .

# 2. Check llama.cpp is built
ls -la ../llama.cpp/build/bin/llama-server

# 3. Download model
llf download

# 4. Verify config
cat configs/config.json | python -m json.tool

# 5. Try starting server
llf --log-level DEBUG server start

# 6. If successful, test chat
llf chat "Hello"
```

### Switching from Local to External API

```bash
# 1. Backup current config
cp configs/config.json configs/config.json.bak

# 2. Use OpenAI example
cp configs/config_examples/config_openai.json configs/config.json

# 3. Edit API key
nano configs/config.json

# 4. Test
llf chat "Hello"
```

### Resetting to Clean State

```bash
# Stop all servers
llf server stop

# Remove models (optional - will need to re-download)
rm -rf models/*

# Reset config
cp configs/config_examples/config_local_gguf.json configs/config.json

# Reinstall
pip install -e .

# Start fresh
llf download
llf server start
```

---

**Last Updated:** 2025-12-30

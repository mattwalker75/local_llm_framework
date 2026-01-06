# Basic User Guide

> **Get Started with Your Local LLM**
> This guide will walk you through the essential steps to download a model, configure your system, and start chatting with a locally running Large Language Model.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Finding and Downloading a Model](#finding-and-downloading-a-model)
3. [Converting Models to GGUF Format](#converting-models-to-gguf-format)
4. [Configuring Your LLM](#configuring-your-llm)
5. [Starting the LLM Server](#starting-the-llm-server)
6. [Chatting with Your LLM](#chatting-with-your-llm)
7. [Using the GUI Interface](#using-the-gui-interface)
8. [Stopping the LLM Server](#stopping-the-llm-server)
9. [Advanced Features](#advanced-features)
10. [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure you have:

1. **Completed Installation**: Follow the [QUICK_INSTALL.md](../QUICK_INSTALL.md) guide
2. **Active Virtual Environment**: Always activate the virtual environment before using LLF
   ```bash
   source llf_venv/bin/activate  # On macOS/Linux
   ```
   See [Virtual Environment Guide](virtual_environment.md) for details

3. **llama.cpp Compiled**: The llama-server binary must be available
   - See [llama.cpp setup](https://github.com/ggml-org/llama.cpp)
   - Setup and installion located in [QUICK_INSTALL.md](../QUICK_INSTALL.md)

4. **Basic Understanding**: Familiarity with terminal/command line usage

---

## Finding and Downloading a Model

### Step 1: Choose a Model from HuggingFace

Visit [HuggingFace](https://huggingface.co) to find models. Look for models that:
- Are in **GGUF format** (recommended) OR can be converted to GGUF
- Fit your hardware capabilities (RAM/VRAM requirements)
- Match your use case (coding, chat, reasoning, etc.)

### Recommended GGUF Models

Here are 5 excellent models that work well with the LLM Framework:

| Model | Size | RAM Required | Best For | HuggingFace ID |
|-------|------|--------------|----------|----------------|
| **Qwen 2.5 Coder 7B** | ~4-6 GB | 8 GB+ | Coding, general chat | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` |
| **Llama 3.2 3B** | ~2-3 GB | 4 GB+ | General chat, lightweight | `meta-llama/Llama-3.2-3B-Instruct-GGUF` |
| **Mistral 7B** | ~4-6 GB | 8 GB+ | General purpose, chat | `mistralai/Mistral-7B-Instruct-v0.3-GGUF` |
| **DeepSeek Coder 6.7B** | ~4-5 GB | 8 GB+ | Code generation | `deepseek-ai/deepseek-coder-6.7b-instruct-GGUF` |
| **Phi-3 Mini 3.8B** | ~2-3 GB | 4 GB+ | Reasoning, lightweight chat | `microsoft/Phi-3-mini-4k-instruct-GGUF` |

**Notes:**
- Smaller models (3B-7B parameters) run faster but may be less capable
- Larger models (13B-70B parameters) are more capable but require more RAM
- GGUF quantization (q4, q5, q8) affects size vs quality tradeoff

### Step 2: Download the Model

Use the `llf model download` command:

```bash
# Download a GGUF model from HuggingFace
llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

**What happens:**
- Model downloads to `models/` directory
- Progress bar shows download status
- Model is automatically organized in subdirectories

**Check download progress:**
```bash
# List all downloaded models
llf model list
```

**Example output:**
```
Available models in /path/to/models/:
  1. Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
     └─ qwen2.5-coder-7b-instruct-q5_k_m.gguf (4.2 GB)
```

**Get model information:**
```bash
# Show details about default model
llf model info

# Show details about specific model
llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### Alternative: Direct URL Download

If you have a direct link to a GGUF file:

```bash
llf model download --url https://example.com/model.gguf --name my-custom-model
```

### Advanced: Download to Custom Directory

```bash
# Use custom download directory
llf -d /custom/models model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

---

## Converting Models to GGUF Format

If you downloaded a model that is **NOT in GGUF format** (has .safetensor files instead), you need to convert it.

### When Do You Need Conversion?

Check your model directory:
```bash
ls -la models/YourModelName/
```

If you see `.safetensor` files instead of `.gguf` files, you need conversion.

### Step 1: Understand the Conversion Script

The conversion script requires:
- **Source**: HuggingFace model name (must already be downloaded)
- **Destination**: Name for the converted GGUF model
- **Force flag** (optional): Rebuild if GGUF already exists

### Step 2: Get Help Documentation

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

### Step 3: Convert the Model

```bash
# Convert HuggingFace model to GGUF
./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s Qwen--Qwen2.5-Coder-7B-Instruct \
  -d Qwen--Qwen2.5-Coder-7B-Instruct-GGUF
```

**What happens:**
- Script converts .safetensor files to GGUF format
- New GGUF model saved in `models/<GGUF Model Name>/`
- Original HuggingFace model remains unchanged

**Force rebuild if needed:**
```bash
# Delete existing GGUF and rebuild
./bin/tools/convert_huggingface_llm_2_gguf.sh \
  -s Qwen--Qwen2.5-Coder-7B-Instruct \
  -d Qwen--Qwen2.5-Coder-7B-Instruct-GGUF \
  -f
```

### Step 4: Test the Converted Model

After conversion, test the model with llama.cpp directly:

```bash
../llama.cpp/build/bin/llama-cli -st\
  -m models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/model.gguf \
  -p "Write a Python hello world"
```

If this works, your model is ready to use with LLF.

---

## Configuring Your LLM

After downloading (and optionally converting) your model, you need to configure the framework to use it.

### Understanding the Configuration File

The main configuration file is `configs/config.json`. It has two main sections:

1. **`local_llm_servers`** or **`local_llm_server`**: Defines the llama-server configuration
2. **`llm_endpoint`**: Defines how to connect to the LLM

### Single Server Configuration

Edit `configs/config.json`:

```json
{
  "local_llm_server": {
    "llama_server_path": "/path/to/llama.cpp/build/bin/llama-server",
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
  "model_dir": "/full/path/to/local_llm_framework/models",
  "cache_dir": "/full/path/to/local_llm_framework/.cache"
}
```

**Key Fields to Update:**

| Field | Description | Example |
|-------|-------------|---------|
| `llama_server_path` | Path to llama-server binary | `/path/to/llama.cpp/build/bin/llama-server` |
| `model_dir` | Directory name containing GGUF model | `Qwen--Qwen2.5-Coder-7B-Instruct-GGUF` |
| `gguf_file` | GGUF filename | `qwen2.5-coder-7b-instruct-q5_k_m.gguf` |
| `api_base_url` | Server URL (matches host:port) | `http://127.0.0.1:8000/v1` |
| `model_name` | Model identifier for API | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` |

The `model_dir` can be obtained by looking in the `models` directory by running `ls models`.

The `gguf_file` can be obtaind by looking in the directory in the `models` directory and find the .gguf file by running `ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF`

The `model_name` can be obtained by running `llf model list`.  Copy the name you want to use that matches up with the associated model you are configuration to be used by the server.

### Multiple Server Configuration

If you want to run multiple LLMs simultaneously:

```json
{
  "local_llm_servers": [
    {
      "name": "qwen-coder",
      "llama_server_path": "/path/to/llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8000,
      "model_dir": "Qwen--Qwen2.5-Coder-7B-Instruct-GGUF",
      "gguf_file": "qwen2.5-coder-7b-instruct-q5_k_m.gguf"
    },
    {
      "name": "mistral-chat",
      "llama_server_path": "/path/to/llama.cpp/build/bin/llama-server",
      "server_host": "127.0.0.1",
      "server_port": 8001,
      "model_dir": "Mistral--Mistral-7B-Instruct-GGUF",
      "gguf_file": "mistral-7b-instruct-v0.3-q5_k_m.gguf"
    }
  ],
  "llm_endpoint": {
    "api_base_url": "http://127.0.0.1:8000/v1",
    "api_key": "EMPTY",
    "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
    "default_local_server": "qwen-coder"
  }
}
```

**Multi-Server Notes:**
- Each server needs a unique `name` and `server_port`
- `default_local_server` specifies which server to use by default
- You can switch servers with `llf server switch <server-name>`

### Configuration Tips

1. **Find your llama-server path:**
   ```bash
   which llama-server
   # or if you built it locally:
   ls ../llama.cpp/build/bin/llama-server
   ```

2. **Find your GGUF file name:**
   ```bash
   ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/
   ```

3. **Use absolute paths for reliability:**
   ```bash
   pwd  # Shows current directory
   # Use full paths like /Users/yourname/local_llm_framework/models
   ```

4. **Validate your JSON:**
   - Ensure proper comma placement
   - Check for matching braces {}
   - Use a JSON validator if needed

---

## Starting the LLM Server

Once configured, you can start the llama-server backend.

### Understanding Server Modes

The server can run in different modes:

| Mode | Description | Command Flag | Use Case |
|------|-------------|--------------|----------|
| **Foreground** | Server runs in current terminal | (none) | Testing, debugging |
| **Daemon** | Server runs in background | `--daemon` | Normal use, keeps terminal free |
| **Localhost** | Only accessible from local machine | (default) | Secure local use |
| **Network** | Accessible on local network | `--share` | Share with other devices |

### Step 1: Check Server Status

Before starting, check if a server is already running:

```bash
llf server status
```

**Possible outputs:**
- `Server is running` - Server already active
- `Server is not running` - No server running, safe to start

### Step 2: Start the Server (Single Server)

**Basic start (foreground):**
```bash
llf server start
```
- Server runs in current terminal
- Press `Ctrl+C` to stop
- Good for testing

**Start in daemon mode (recommended):**
```bash
llf server start --daemon
```
- Server runs in background
- Terminal remains free for other commands
- Best for normal use

**Start with network access:**
```bash
llf server start --share --daemon
```
- Server accessible on local network (0.0.0.0)
- Other devices can connect
- See [Network Access Guide](HOW_TOs/Setup_Network_Access_LLM.md)

### Step 3: Start the Server (Multi-Server)

**List available servers:**
```bash
llf server list
```

**Example output:**
```
Configured Servers:
  1. qwen-coder (127.0.0.1:8000) - Status: Not Running
  2. mistral-chat (127.0.0.1:8001) - Status: Not Running

Default Server: qwen-coder
```

**Start a specific server:**
```bash
# Start by name
llf server start qwen-coder

# Start in daemon mode
llf server start qwen-coder --daemon

# Skip memory safety check
llf server start qwen-coder --force
```

**Switch default server:**
```bash
llf server switch mistral-chat
```

### Step 4: Verify Server is Running

```bash
# Check status
llf server status

# For multi-server setups
llf server status qwen-coder
```

**Successful output:**
```
Server is running at http://127.0.0.1:8000
Model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```

### Step 5: List Models from Server

Once the server is running, you can query available models:

```bash
llf server list_models
```

### Server Startup Options

**Override model at startup:**
```bash
# Use different HuggingFace model
llf server start --huggingface-model Mistral/Mistral-7B-Instruct-GGUF

# Use specific GGUF file
llf server start --gguf-dir Qwen--Qwen2.5-Coder-7B-Instruct-GGUF --gguf-file model.gguf
```

**Use custom config file:**
```bash
llf --config myconfig.json server start --daemon
```

### Troubleshooting Server Start

**Problem: "Port already in use"**
```bash
# Check if server is already running
llf server status

# If stuck, manually kill the process
pkill -f llama-server
```

**Problem: "llama-server not found"**
```bash
# Verify path in config.json
# Ensure llama.cpp is compiled with llama-server
ls /path/to/llama.cpp/build/bin/llama-server
```

**Problem: "Model file not found"**
```bash
# Verify model exists
ls models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/

# Verify gguf_file matches actual filename
```

---

## Chatting with Your LLM

Once the server is running, you can start an interactive chat session.

### Basic Chat

```bash
llf chat
```

**What happens:**
1. If server is not running, you'll be prompted to start it
2. Chat interface opens in your terminal
3. Type your messages and press Enter
4. LLM responds in real-time
5. Display helpful commands in chat `help`
6. Type `exit` or `quit` to end the session

### Chat with Auto-Start Server

```bash
# Automatically start server if not running (no prompt)
llf chat --auto-start-server
```

### Chat Without Starting Server

```bash
# Exit with error if server not running
llf chat --no-server-start
```

### Chat Interface Features

**During a chat session you can:**
- Type multi-line messages (the interface will wait for you to finish)
- Ask follow-up questions (LLM remembers conversation context)
- Use special commands (if enabled):
  - `/help` - Show available commands
  - `/clear` - Clear conversation history
  - `/save` - Save conversation
  - `exit` or `quit` - End session

**Example chat session:**
```
You: Hello! Can you help me write a Python function?

LLM: Of course! I'd be happy to help you write a Python function. What would you like the function to do?

You: I need a function that calculates the factorial of a number.

LLM: Here's a Python function that calculates the factorial of a number:

def factorial(n):
    """Calculate the factorial of n."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

This function handles negative numbers, zero, and positive integers correctly.

You: exit
```

### CLI Mode (Non-Interactive)

For scripting or one-off questions:

```bash
# Ask a single question and exit
llf chat --cli "What is 2+2?"

# Pipe data to LLM
cat myfile.txt | llf chat --cli "Summarize this file"

# Use in shell scripts
ANSWER=$(llf chat --cli "Generate a random password" 2>/dev/null)
echo "Generated: $ANSWER"
```

### Chat with Specific Model

```bash
# Use a different model for this session ( for non-GGUF models )
llf chat --huggingface-model Mistral/Mistral-7B-Instruct

# Use specific GGUF file
llf chat --gguf-dir MyModel-GGUF --gguf-file model.gguf
```

### Chat Tips

1. **Be specific**: Clear questions get better answers
2. **Use context**: The LLM remembers your conversation
3. **Iterate**: Refine your questions based on responses
4. **Save important chats**: Use `/save` to preserve conversations
5. **Experiment**: Try different phrasings if you don't get good results

---

## Using the GUI Interface

For a more user-friendly experience, you can use the web-based GUI.

### Understanding the GUI

The GUI provides:
- Web browser interface for chatting with the LLM
- Visual controls for server management
- Configuration management
- Memory and data store management
- No command line required

### Starting the GUI

**Basic start (opens browser automatically):**
```bash
llf gui
```
- GUI starts on http://localhost:7860
- Browser opens automatically
- Only accessible from your computer

**Start in daemon mode:**
```bash
llf gui start --daemon
```
- GUI runs in background
- Terminal remains free
- Access at http://localhost:7860

**Start with network access:**
```bash
llf gui start --share
```
- Accessible on local network (0.0.0.0:7860)
- Other devices can access the GUI
- See [Network Access GUI Guide](HOW_TOs/Setup_Network_Access_GUI.md)

**Start with authentication:**
```bash
llf gui start --key MySecretPassword
```
- Requires password to access GUI
- Provides additional security
- Combine with `--share` for network access with auth

### GUI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--port` | Custom port number | `llf gui start --port 8080` |
| `--daemon` | Run in background | `llf gui start --daemon` |
| `--share` | Network accessible | `llf gui start --share` |
| `--key` | Require authentication | `llf gui start --key PASSWORD` |
| `--no-browser` | Don't open browser | `llf gui start --no-browser` |

### Managing the GUI

**Check GUI status:**
```bash
llf gui status
```

**Stop the GUI daemon:**
```bash
llf gui stop
```

### Using the GUI

Once the GUI is running:

1. **Access in browser**: Navigate to http://localhost:7860
2. **Start chatting**: Use the chat interface to talk with your LLM
3. **Manage server**: Start/stop the LLM server from the GUI
4. **Configure**: Adjust settings visually
5. **View memory**: Browse and edit LLM memory

### GUI vs CLI

| Feature | CLI | GUI |
|---------|-----|-----|
| Speed | Fast | Moderate |
| Ease of use | Requires commands | Point and click |
| Scripting | Excellent | Limited |
| Visual feedback | Text only | Rich interface |
| Remote access | SSH required | Browser only |

**When to use CLI:**
- Scripting and automation
- Remote SSH sessions
- Debugging and testing
- Quick commands

**When to use GUI:**
- First-time setup
- Visual preference
- Non-technical users
- Remote browser access

---

## Stopping the LLM Server

When you're done using the LLM, always stop the server to free up resources.

### Check Server Status

```bash
# Single server
llf server status

# Multi-server
llf server status qwen-coder
```

### Stop the Server

**Single server:**
```bash
llf server stop
```

**Multi-server:**
```bash
# Stop specific server
llf server stop qwen-coder

# Stop all servers
llf server stop qwen-coder
llf server stop mistral-chat
```

**Verify shutdown:**
```bash
llf server status
```

Expected output: `Server is not running`

### Force Stop if Needed

If the server won't stop gracefully:

```bash
# Kill llama-server processes
pkill -f llama-server

# Verify they're gone
ps aux | grep llama-server
```

### Restart the Server

To restart with the same configuration:

```bash
# Single server
llf server restart

# Multi-server
llf server restart qwen-coder

# Restart with network access
llf server restart --share
```

---

## Advanced Features

The LLM Framework provides several advanced features to enhance your LLM experience.

### RAG Data Stores (llf datastore)

**What it provides:**
- Add custom documentation as context for the LLM
- Create RAG (Retrieval-Augmented Generation) vector stores
- Reference your own documentation, code, or knowledge bases
- LLM can search and cite your documents

**Quick start:**
```bash
# List available data stores
llf datastore list

# Attach a data store
llf datastore attach my_documentation

# Attach all data stores
llf datastore attach all

# List only attached stores
llf datastore list --attached

# Detach when done
llf datastore detach my_documentation
```

**Learn more:** See [Setup RAG Data Store Guide](HOW_TOs/Setup_Datastore_RAG.md)

### LLM Memory (llf memory)

**What it provides:**
- Long-term memory for the LLM across sessions
- Save facts, preferences, notes, tasks, and context
- LLM remembers information between conversations
- Fully managed by the LLM itself

**Quick start:**
```bash
# List available memory instances
llf memory list

# Enable a memory instance
llf memory enable main_memory

# List only enabled memory
llf memory list --enabled

# View memory details
llf memory info main_memory

# Disable when not needed
llf memory disable main_memory
```

**Example use cases:**
- "Remember that I prefer Python 3.12"
- "Store this API endpoint for later"
- "Note that I'm working on the authentication module"

**Learn more:** See [Setup Memory Guide](HOW_TOs/Setup_Memory.md)

### Voice Interaction (llf module)

**What it provides:**
- **Speech-to-Text**: Talk to the LLM using your microphone
- **Text-to-Speech**: LLM talks back through your speakers
- Hands-free interaction with your LLM
- Completely offline (no internet required)

**Quick start:**
```bash
# List available modules
llf module list

# Enable text-to-speech (LLM talks to you)
llf module enable text2speech

# Enable speech-to-text (you talk to LLM)
llf module enable speech2text

# Enable both
llf module enable all

# View module details
llf module info text2speech

# Disable when not needed
llf module disable text2speech
```

**Test your setup:**
```bash
# Test speakers
./bin/tools/test_text2speech.py "Hello, this is a test"

# Test microphone
./bin/tools/test_speech2text.py
```

**Learn more:** See [Setup Talking Guide](HOW_TOs/Setup_Talking.md)

### LLM Tools (llf tool)

**What it provides:**
- Enable the LLM to use external tools
- Internet access for research
- Local file system access (with whitelist protection)
- Command execution (with whitelist protection)
- Extends LLM capabilities beyond text generation

**Quick start:**
```bash
# List available tools
llf tool list

# Enable a tool
llf tool enable web_search

# Enable with auto mode
llf tool enable web_search --auto

# List only enabled tools
llf tool list --enabled

# View tool details
llf tool info web_search

# Disable when not needed
llf tool disable web_search
```

**Available tools:**
- **web_search**: LLM can search the internet
- **file_access**: LLM can read/write local files
- **command_execution**: LLM can run commands
- **calculator**: Enhanced math capabilities

**Security notes:**
- Tools use whitelist protection
- Review tool permissions before enabling
- Use `--auto` mode for autonomous tool use

**Learn more:** See [Tools Documentation](Tools.md)

---

## Next Steps

Now that you have the basics down, explore these topics:

### Essential Reading

1. **[Helpful Commands](Helpful_Commands.md)** - Quick reference for common commands
2. **[Fun With Chat](HOW_TOs/Fun_With_Chat.md)** - Cool things you can do with chat mode
3. **[Troubleshooting](HOW_TOs/Troubleshooting.md)** - Solutions to common problems

### Advanced Setup

4. **[Setup Memory](HOW_TOs/Setup_Memory.md)** - Give your LLM long-term memory
5. **[Setup RAG Data Store](HOW_TOs/Setup_Datastore_RAG.md)** - Add custom documentation
6. **[Setup Talking](HOW_TOs/Setup_Talking.md)** - Enable voice interaction
7. **[Setup Multiple LLMs](HOW_TOs/Setup_LLMs.md)** - Run multiple models

### Network and External Access

8. **[Network Access - LLM](HOW_TOs/Setup_Network_Access_LLM.md)** - Share your LLM on network
9. **[Network Access - GUI](HOW_TOs/Setup_Network_Access_GUI.md)** - Share GUI on network
10. **[External LLM](HOW_TOs/Setup_External_LLM.md)** - Use ChatGPT, Claude, etc.

### Reference

11. **[Directory Structure](Directory_Structure.md)** - Understand the project layout
12. **[Major Components](Major_Components.md)** - Learn about key components
13. **[Configuration Files](../configs/)** - Detailed config documentation

### Quick Tips

**Performance:**
- Smaller models (3B-7B) are faster but less capable
- Larger models (13B+) need more RAM but are smarter
- Adjust `temperature` in config for creativity vs consistency

**Memory Management:**
- Stop the server when not in use
- Use daemon mode for background operation
- Monitor RAM usage with large models

**Best Practices:**
- Always activate virtual environment: `source llf_venv/bin/activate`
- Keep config.json backed up
- Test models with `llf server start` before using daemon mode
- Use `llf model list` to track downloaded models

**Getting Help:**
- Use `-h` or `--help` with any command: `llf chat -h`
- Check the troubleshooting guide
- Review example configs in `configs/`

---

## Quick Reference

### Essential Commands

```bash
# Virtual Environment (ALWAYS REQUIRED)
source llf_venv/bin/activate

# Model Management
llf model download --huggingface-model MODEL_NAME
llf model list
llf model info

# Server Management
llf server start --daemon
llf server status
llf server stop

# Chat
llf chat
llf chat --auto-start-server
llf chat --cli "Your question here"

# GUI
llf gui start --daemon
llf gui status
llf gui stop

# Advanced Features
llf datastore list
llf memory list
llf module list
llf tool list
```

### Configuration Checklist

- [ ] Virtual environment activated
- [ ] llama.cpp compiled with llama-server
- [ ] Model downloaded to `models/` directory
- [ ] `configs/config.json` updated with:
  - [ ] llama_server_path
  - [ ] model_dir
  - [ ] gguf_file
  - [ ] api_base_url
  - [ ] model_name
- [ ] Server starts successfully
- [ ] Chat works correctly

### Typical Workflow

1. Activate virtual environment
2. Start server in daemon mode: `llf server start --daemon`
3. Start chatting: `llf chat`
4. When done: `llf server stop`

### Common Issues

| Problem | Solution |
|---------|----------|
| "Virtual environment not activated" | Run `source llf_venv/bin/activate` |
| "Server not running" | Run `llf server start --daemon` |
| "Model not found" | Check `configs/config.json` paths |
| "Port already in use" | Run `llf server stop` or `pkill -f llama-server` |
| "Out of memory" | Use smaller model or close other applications |

---

## Summary

You've learned how to:

1. **Find and download models** from HuggingFace
2. **Convert models** to GGUF format if needed
3. **Configure** your LLM in `configs/config.json`
4. **Start the server** in daemon or foreground mode
5. **Chat** with your LLM via CLI or GUI
6. **Stop the server** when finished
7. **Use advanced features** like memory, RAG, voice, and tools

**You're now ready to use your Local LLM Framework!**

For more advanced topics, explore the [documentation index](../README.md#index) or dive into the HOW_TO guides.

Happy chatting with your local LLM!
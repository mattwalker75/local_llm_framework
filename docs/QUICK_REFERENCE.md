# LLF Quick Reference Card

## Setup (One-Time)

```bash
cd local_llm_framework
source llf_venv/bin/activate
pip install -e .
```

## Basic Commands

| Command | Description |
|---------|-------------|
| `llf` | Start interactive chat |
| `llf -h` | Show help |
| `llf --version` | Show version |
| `llf gui` | Start web GUI |
| `llf model download` | Download default model |
| `llf model list` | List downloaded models |
| `llf model info` | Show model info |
| `llf server start` | Start llama-server |
| `llf server stop` | Stop llama-server |
| `llf server status` | Check server status |

## Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `-d PATH` | Set download directory | `llf -d /mnt/models download` |
| `-c FILE` | Use config file | `llf -c config.json chat` |
| `--cache-dir PATH` | Set cache directory | `llf --cache-dir /tmp/cache` |
| `--log-level LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) | `llf --log-level DEBUG` |
| `--log-file PATH` | Log to file (in addition to console) | `llf --log-file llf.log` |

## Model Commands

```bash
llf model download                              # Download default model
llf model download --huggingface-model "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
llf model download --url "https://..." --name "my-model"  # Download from URL
llf model download --force                      # Force re-download
llf model download --token "hf_xxx"             # Use API token
llf model list                                  # List downloaded models
llf model info                                  # Show model info
```

## Chat Modes

### Interactive Mode (Default)
Start interactive chat: `llf` or `llf chat`

### CLI Mode (Non-Interactive)
Ask a single question and exit (for scripting):
```bash
llf chat --cli "YOUR QUESTION HERE"
llf chat --cli "What is 2+2?" --auto-start-server
llf chat --cli "Explain Python decorators" --model "custom/model"
```

## Chat Interface Commands

| Command | Action |
|---------|--------|
| Type message + Enter | Send message to LLM |
| `START` ... `END` | Multiline input mode (see below) |
| `help` | Show help |
| `info` | Show model info |
| `clear` | Clear screen |
| `exit` or `quit` | Exit chat |
| `Ctrl+C` | Force quit |

### Multiline Input

To paste or type multiline content (e.g., from PDFs or documents):
1. Type `START` and press Enter
2. Paste or type your content (multiple lines)
3. Type `END` on a new line and press Enter

Example:
```
You> START
This is a long document
that spans multiple lines.
You can paste PDF content here.
END
```

## GUI Management

```bash
llf gui                                # Start GUI (port 7860)
llf gui start                          # Same as above
llf gui start --daemon                 # Start in background
llf gui start --port 8080              # Custom port
llf gui start --share                  # Network accessible
llf gui start --key SECRET             # With authentication
llf gui stop                           # Stop GUI daemon
llf gui status                         # Check status
```

## Server Management

```bash
llf server start                       # Start server (foreground)
llf server start --daemon              # Start in background
llf server start --share               # Network accessible
llf server stop                        # Stop server
llf server status                      # Check status
llf server restart                     # Restart server
llf server list_models                 # List available models

# Chat with server control
llf chat                               # Prompts to start if not running
llf chat --auto-start-server           # Auto-start without prompt
llf chat --no-server-start             # Exit if server not running
```

## Management Commands (Placeholders)

```bash
# Data Store management (future RAG support)
llf datastore list                     # List data stores
llf datastore list --attached          # List attached only
llf datastore attach                   # Attach data store
llf datastore detach                   # Detach data store
llf datastore info DATA_STORE_NAME     # Show info

# Module management (future extensions)
llf module list                        # List modules
llf module list --enabled              # List enabled only
llf module enable                      # Enable a module
llf module disable                     # Disable a module
llf module info MODULE_NAME            # Show info

# Tool management (future extensions)
llf tool list                          # List tools
llf tool list --enabled                # List enabled only
llf tool enable TOOL_NAME              # Enable a tool
llf tool disable TOOL_NAME             # Disable a tool
llf tool info TOOL_NAME                # Show info
```

## Examples

```bash
# Quick start (interactive mode)
llf

# Start web GUI
llf gui

# CLI mode (non-interactive, for scripting)
llf chat --cli "What is the capital of France?"
llf chat --cli "Explain Python generators" --auto-start-server

# CLI mode with specific model
llf chat --cli "Write a haiku" --huggingface-model "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"

# CLI mode in a script
#!/bin/bash
ANSWER=$(llf chat --cli "What is 2+2?" --no-server-start)
echo "The LLM says: $ANSWER"

# Long-running server workflow
llf server start --daemon
llf chat --no-server-start
llf server stop

# Network-accessible GUI with authentication
llf gui start --share --key MY_SECRET_KEY --daemon

# Custom model directory
llf -d ~/llm_models model download
llf -d ~/llm_models chat

# Debug mode with file logging
llf --log-level DEBUG model download
llf --log-level DEBUG --log-file llf.log chat
llf --log-file /var/log/llf/session.log server start

# Multiple models
llf model download --huggingface-model "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
llf model download --huggingface-model "mistralai/Mistral-7B-Instruct-v0.2"
llf model list
```

## Paths

| Item | Default Location |
|------|------------------|
| Models | `./models/` |
| Cache | `./.cache/` |
| Config (Infrastructure) | `./configs/config.json` |
| Config (Prompts) | `./configs/config_prompt.json` |
| Config Backups | `./configs/backups/` |
| Data Stores | `./data_stores/` |
| Modules | `./modules/` |
| Tools | `./tools/` |
| Script | `./bin/llf` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |

## Environment Variables

```bash
export HUGGING_FACE_HUB_TOKEN="hf_xxx"  # For private models
```

## Troubleshooting

```bash
# Virtual environment not active
source llf_venv/bin/activate

# Command not found
pip install -e .

# Or use directly
./bin/llf -h
python -m llf.cli -h
```

## More Information

- Full documentation: [README.md](README.md)
- Detailed usage: [USAGE.md](USAGE.md)
- Implementation details: [workflow/implementation_summary.md](workflow/implementation_summary.md)

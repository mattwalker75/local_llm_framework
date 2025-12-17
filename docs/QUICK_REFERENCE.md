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
| `llf download` | Download default model |
| `llf list` | List downloaded models |
| `llf info` | Show model info |
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

## Download Command

```bash
llf download                                    # Download default model
llf download --model "mistralai/Mistral-7B"     # Download specific model
llf download --force                            # Force re-download
llf download --token "hf_xxx"                   # Use API token
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

## Server Management

```bash
llf server start                       # Start server (foreground)
llf server start --daemon              # Start in background
llf server stop                        # Stop server
llf server status                      # Check status
llf server restart                     # Restart server

# Chat with server control
llf chat                               # Prompts to start if not running
llf chat --auto-start-server           # Auto-start without prompt
llf chat --no-server-start             # Exit if server not running
```

## Examples

```bash
# Quick start (interactive mode)
llf

# CLI mode (non-interactive, for scripting)
llf chat --cli "What is the capital of France?"
llf chat --cli "Explain Python generators" --auto-start-server

# CLI mode with specific model
llf chat --cli "Write a haiku about coding" --model "custom/model"

# CLI mode in a script
#!/bin/bash
ANSWER=$(llf chat --cli "What is 2+2?" --no-server-start)
echo "The LLM says: $ANSWER"

# Long-running server workflow
llf server start --daemon
llf chat --no-server-start
llf server stop

# Custom model directory
llf -d ~/llm_models download
llf -d ~/llm_models chat

# Debug mode with file logging
llf --log-level DEBUG download
llf --log-level DEBUG --log-file llf.log chat
llf --log-file /var/log/llf/session.log server start

# Multiple models
llf download --model "Qwen/Qwen3-Coder-30B-A3B-Instruct"
llf download --model "mistralai/Mistral-7B-Instruct-v0.2"
llf list
```

## Paths

| Item | Default Location |
|------|------------------|
| Models | `./models/` |
| Cache | `./.cache/` |
| Config | Use `-c` flag |
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

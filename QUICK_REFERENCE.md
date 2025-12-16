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

## Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `-d PATH` | Set download directory | `llf -d /mnt/models download` |
| `-c FILE` | Use config file | `llf -c config.json chat` |
| `--cache-dir PATH` | Set cache directory | `llf --cache-dir /tmp/cache` |
| `--log-level LEVEL` | Set log level | `llf --log-level DEBUG` |

## Download Command

```bash
llf download                                    # Download default model
llf download --model "mistralai/Mistral-7B"     # Download specific model
llf download --force                            # Force re-download
llf download --token "hf_xxx"                   # Use API token
```

## Chat Interface Commands

| Command | Action |
|---------|--------|
| Type message + Enter | Send message to LLM |
| `help` | Show help |
| `info` | Show model info |
| `clear` | Clear screen |
| `exit` or `quit` | Exit chat |
| `Ctrl+C` | Force quit |

## Examples

```bash
# Quick start
llf

# Custom model directory
llf -d ~/llm_models download
llf -d ~/llm_models chat

# Debug mode
llf --log-level DEBUG download

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

# CLI Improvements - Enhanced Command-Line Interface

## Summary

Enhanced the Local LLM Framework with a professional command-line interface that supports clean execution without `python -m`, comprehensive help system, and flexible configuration options.

## Changes Made

### 1. Enhanced CLI Module ([llf/cli.py](../llf/cli.py))

**Added Command-Line Arguments:**
- `-d, --download-dir PATH` - Set custom model download directory
- `-c, --config FILE` - Load configuration from JSON file
- `--cache-dir PATH` - Set custom cache directory
- `--log-level LEVEL` - Control logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `--version` - Display version information

**Enhanced Subcommands:**
- `chat` - Start interactive chat (now a proper subcommand)
- `download` - Enhanced with `--token` option for private models
- `list` - List downloaded models
- `info` - Show model information

**Improved Help System:**
- Comprehensive help text with examples
- Command-specific help for each subcommand
- Clear option descriptions and metavars
- Usage examples in epilog

### 2. Standalone Executable Script ([bin/llf](../bin/llf))

Created a standalone executable script that:
- Can be run directly without `python -m`
- Automatically sets up Python path
- Works from any directory when added to PATH
- Provides clean command-line interface

**Usage:**
```bash
./bin/llf -h
./bin/llf download
./bin/llf chat
```

### 3. Package Entry Point (setup.py)

Already configured in setup.py:
```python
entry_points={
    'console_scripts': [
        'llf=llf.cli:main',
    ],
}
```

After `pip install -e .`, users can run `llf` from anywhere.

### 4. Documentation

Created comprehensive documentation:

#### [USAGE.md](../USAGE.md) - Complete usage guide
- Installation methods (3 different ways)
- Detailed help system explanation
- All global options with examples
- All commands with examples
- Common use cases
- Advanced usage scenarios
- Troubleshooting guide
- Tips & tricks

#### [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Quick reference card
- Setup commands
- Basic command table
- Global options table
- Download command reference
- Chat interface commands
- Common examples
- Default paths
- Exit codes

#### [examples/demo_cli.sh](../examples/demo_cli.sh) - Demo script
- Shows version
- Demonstrates help system
- Lists models
- Shows info
- Explains usage patterns

### 5. Updated README.md

Enhanced usage section with:
- Quick start guide
- Three methods to run LLF
- Getting help instructions
- Common commands table
- Command-line options reference
- Link to detailed USAGE.md

## Usage Examples

### Basic Usage

```bash
# Activate virtual environment
source llf_venv/bin/activate

# Install LLF command (one-time)
pip install -e .

# Get help
llf -h
llf download -h

# Download model with custom directory
llf -d /mnt/storage/models download

# Start chat with custom directory
llf -d /mnt/storage/models chat

# Enable debug logging
llf --log-level DEBUG download

# Show version
llf --version
```

### Three Ways to Run

1. **Standalone script:**
   ```bash
   ./bin/llf -h
   ```

2. **Installed command (recommended):**
   ```bash
   pip install -e .
   llf -h
   ```

3. **Python module:**
   ```bash
   python -m llf.cli -h
   ```

## Command-Line Options

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--download-dir PATH` | `-d` | Set model download directory |
| `--config FILE` | `-c` | Load configuration from JSON |
| `--cache-dir PATH` | | Set HuggingFace cache directory |
| `--log-level LEVEL` | | Set logging level |
| `--version` | | Show version information |
| `--help` | `-h` | Show help message |

### Download Command Options

| Option | Description |
|--------|-------------|
| `--model NAME` | Model name from HuggingFace Hub |
| `--force` | Force re-download |
| `--token TOKEN` | HuggingFace API token |

## Help System

### General Help
```bash
$ llf -h
usage: llf [-h] [-d PATH] [-c FILE] [--cache-dir PATH] [--log-level LEVEL]
           [--version]
           COMMAND ...

Local LLM Framework - Run LLMs locally with vLLM

positional arguments:
  COMMAND               Available commands (default: chat)
    chat                Start interactive chat with LLM
    download            Download a model from HuggingFace Hub
    list                List all downloaded models
    info                Show detailed model information

options:
  -h, --help            show this help message and exit
  -d, --download-dir PATH
                        Directory for downloading and storing models
  -c, --config FILE     Path to configuration JSON file
  --cache-dir PATH      Directory for model cache
  --log-level LEVEL     Set logging level (default: INFO)
  --version             show program's version number and exit

Examples:
  llf                              Start interactive chat (default)
  llf chat                         Start interactive chat
  llf download                     Download default model
  llf download --model mistralai/Mistral-7B-Instruct-v0.2
  llf list                         List downloaded models
  llf info                         Show model information
  llf -d /custom/path              Set custom download directory
  llf --log-level DEBUG            Enable debug logging
```

### Command-Specific Help
```bash
$ llf download -h
usage: llf download [-h] [--model NAME] [--force] [--token TOKEN]

Download and cache a model locally for use with LLF.

options:
  -h, --help     show this help message and exit
  --model NAME   Model name to download
  --force        Force re-download even if model exists locally
  --token TOKEN  HuggingFace API token for private models
```

## Testing

All functionality tested:

```bash
# Test help
llf -h                  ✅
llf download -h         ✅
llf chat -h             ✅
llf list -h             ✅
llf info -h             ✅

# Test version
llf --version           ✅

# Test options
llf -d /tmp/models list ✅
llf --log-level DEBUG   ✅

# Test script directly
./bin/llf -h           ✅
```

## Benefits

1. **Clean Interface** - No need for `python -m` prefix
2. **Flexible** - Three different ways to run
3. **Professional** - Comprehensive help system
4. **Configurable** - Command-line overrides for all settings
5. **Documented** - Extensive documentation and examples
6. **User-Friendly** - Clear help messages and examples

## Files Modified/Created

### Modified
- [llf/cli.py](../llf/cli.py) - Enhanced argument parsing and help system
- [README.md](../README.md) - Updated usage section

### Created
- [bin/llf](../bin/llf) - Standalone executable script
- [USAGE.md](../USAGE.md) - Comprehensive usage guide
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Quick reference card
- [examples/demo_cli.sh](../examples/demo_cli.sh) - Demo script
- [workflow/cli_improvements.md](cli_improvements.md) - This document

## Future Enhancements

Potential future improvements:
- Shell completion (bash, zsh, fish)
- Interactive model selection
- Configuration file generator
- Model search functionality
- Batch operations
- Progress bars for downloads
- Model comparison tool

## Conclusion

The LLF command-line interface is now production-ready with:
- ✅ Clean execution (`llf` instead of `python -m llf.cli`)
- ✅ Comprehensive help system (`-h` on all commands)
- ✅ Flexible configuration (CLI args override config files)
- ✅ Professional documentation
- ✅ Multiple usage methods (script, package, module)

Users can now use LLF with a clean, intuitive command-line interface that follows Unix/Linux conventions and provides excellent documentation.

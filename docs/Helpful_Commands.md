# Helpful Commands

A quick reference guide for using the LLF (Local LLM Framework) command-line interface.

> **Note:** Make sure you've activated the virtual environment first:
> ```bash
> source llf_venv/bin/activate
> ```

This covers how to use the `llf` command, which is located in the `local_llm_framwork/bin` directory.

---

## General Commands

### Check LLF Version
```bash
llf --version
```

### Display General Help
```bash
llf -h
```

### Display Help for Specific Commands
```bash
llf download -h
llf chat -h
llf server -h
llf model -h
```

---

## Model Management

### List Downloaded Models
```bash
llf list
```

### Show Model Information
```bash
llf info
```

### Download a Model
```bash
llf download
```

### Download with Custom Directory
```bash
llf -d /custom/path download
```

---

## Chat & Interaction

### Start Interactive Chat
```bash
llf
```

### Chat with Custom Model Directory
```bash
llf -d /custom/path chat
```

---

## Server Management

### Start the Server
```bash
llf server start
```

### Stop the Server
```bash
llf server stop
```

### Check Server Status
```bash
llf server status
```

### List All Configured Servers
```bash
llf server list
```

---

## Logging Options

You can adjust the verbosity of log output using the `--log-level` flag:

### Debug Mode (Detailed Information)
```bash
llf --log-level DEBUG chat
```

### Info Mode (Normal Operations - Default)
```bash
llf --log-level INFO chat
```

### Warning Mode (Warnings and Errors Only)
```bash
llf --log-level WARNING chat
```

### Error Mode (Errors Only)
```bash
llf --log-level ERROR chat
```

---

## Advanced Usage

### Custom Configuration File
```bash
llf -c /path/to/config.json chat
```

### Combine Options
```bash
llf -d /custom/models --log-level DEBUG download
```

---

## Additional Resources

For more detailed information, see:
- **README.md** - Overview and setup instructions
- **USAGE.md** - Detailed usage guide
- **QUICK_REFERENCE.md** - Quick command reference

---

## Common Workflows

### First-Time Setup
```bash
# 1. Activate virtual environment
source llf_venv/bin/activate

# 2. Download a model
llf download

# 3. Start chatting
llf
```

### Using with Custom Models
```bash
# 1. Place your GGUF model in a custom directory
mkdir -p models/my_custom_model

# 2. Use it with LLF
llf -d models/my_custom_model chat
```

### Server Mode
```bash
# 1. Start the server
llf server start

# 2. In another terminal, interact with it
# (Server runs on http://127.0.0.1:8000/v1 by default)

# 3. Stop the server when done
llf server stop
```

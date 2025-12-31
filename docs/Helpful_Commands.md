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
llf chat -h
llf server -h
llf model -h
llf gui -h
llf datastore -h
llf memory -h
llf module -h
llf tool -h
```
NOTE:  The above online help sources should be used for command execution

---

## Chat with LLM

### Start Interactive Chat
```bash
llf chat
```
Helpful commands while in Interactive Chat:
   - View help menu:  `help`
   - Exit interactive chat:  `exit`
   - View the model you are using:  `info`

### Auto Start Server when Starting Interactive Chat
```bash
llf chat --auto-start-server
```

### Send single line chat request to LLM
```bash
llf chat --cli "what is the meaning of Christmas?"
```

---

## Local LLM Server Management ( Single server mode )


### Start the Server and run as background process
```bash
llf server start --daemon
``` 

### Stop the Server
```bash
llf server stop
```

### Check Server Status
```bash
llf server status
```

### Restart Server
```bash
llf server restart
```

### List available models associated with Server
```bash
llf server list_models
```

---

## Model Management

All models are located in the `models` directory

### List Downloaded Models
```bash
llf model list
```

### Show Model Information
```bash
llf model info <MODEL_NAME>
```

### Download a Model from https://huggingface.co/
```bash
llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
```
NOTE:  Model name being download is:  Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
   - Refer to the New Model setup documentation for details on model download

---

## Graphical User Interface

### Start GUI for use
```bash
llf gui
```

### Start GUI in background and manually connect browser to it
```bash
llf gui start --daemon
```
### Check if GUI process is running
```bash
llf gui status
```

### Stop background GUI process
```bash
llf gui stop
```

--- 

## Data Store Management ( Documentation for Model to use (RAG))


### List available Data Stores 
```bash
llf datastore list
```

### Attach Data Store for LLM to use
```bash
llf datastore attach DATA_STORE_NAME
```

### Detach Data Store from LLM 
```bash
llf datastore detach DATA_STORE_NAME
```

### Display information about Data Store
```bash
llf datastore info DATA_STORE_NAME
```

---

## Managing Long Term Memory

NOTE:  Only have ONE memory module enabled at 1 time

### List available Memory Modules
```bash
llf memory list
```

### Enable a Memory Module
```bash
llf memory enable MEMORY_NAME
```

### Disable a Memory Module
```bash
llf memory disable MEMORY_NAME
```

### Display information about Memory Module
```bash
llf memory info MEMORY_NAME
```

---

## Manage User Interactive Modules

NOTE:  Currently the following modules exist
   - Text-to-Speech : Enables the LLM to talk through your speakers
   - Speech-to-Text : Enables the user to speak to the LLM over the microphone

### List available Modules
```bash
llf module list
```

### Enable a Module
```bash
llf module enable MODULE_NAME
```

### Disable a Module
```bash
llf module disable MODULE_NAME
```

### Display information about a Module
```bash
llf module info MODULE_NAME
```

---

## Manage Tools for LLM to use

NOTE:  Tools are enablements for the LLM, such as allowing it to access files or the Internet

### List available Tools
```bash
llf tool list
```

### Enable a Tool for the LLM to use
```bash
llf tool enable TOOL_NAME
```

### Disable a Tool
```bash
llf tool disable TOOL_NAME
```

### Display information about a Tool
```bash
llf tool info TOOL_NAME
```

---

## Logging Options ( example using "chat" command )

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

### Debug Mode logged to a specific file
``` bash
llf --log-level DEBUG --log-file /tmp/debug.log chat
```



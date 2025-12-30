# Local LLM Framework - Directory Structure

This document provides a comprehensive outline of the directory structure for the Local LLM Framework project.

**Last Updated:** 2025-12-28

---

## Project Root Structure

```
local_llm_framework/
├── bin
│   ├── manual_tests      -> Scripts to help troubleshoot issues
│   ├── tools             -> Stand alone tools for specific tasks
│   │   └── data_store    -> Used to create Data Store files
│   ├── llf                    -> MAIN PROGRAM TO USE
│   └── start_llama_server.sh  -> Internally used
├── configs               -> Main config files 
│   ├── backups           -> Backs of config.json and config_prompt.json files
│   ├── config_examples   -> Example config.json files
│   ├── config_prompt_examples  -> Example config_prompt.json files
│   ├── config.json             -> Main configuration file
│   └── config_prompt.json      -> Prompt configuration
├── data_stores
│   ├── embedding_models  -> Local embedding models used for Data Stores 
│   ├── vector_stores     -> Location of data store files used by LLM
│   ├── data_store_registry.json   -> Registery file to track data store files
├── docs                  -> Documentation
├── llf                   -> Main program files
│   ├── cli.py            -> Command line interface commands
│   ├── config.py         -> Work with .json config files
│   ├── gui.py            -> Graphical user interface
│   ├── llm_runtime.py    -> Manage and commuicate with backend LLM llama.ccp server
│   ├── logging_config.py      -> Manages logging
│   ├── memory_manager.py      -> Manages files in "memory" directory
│   ├── memory_tools.py        -> Enables LLM models to work with "memory" data
│   ├── model_manager.py       -> Manage local LLM models
│   ├── operation_detector.py  -> Logic to determine if LLM needs "memory" access
│   ├── prompt_config.py       -> Manages prompt data when talking with LLM
│   ├── rag_retriever.py       -> Retrieve data from "data_stores" directory
│   ├── server_commands.py     -> Manage local multi-LLM server
│   ├── tools_manager.py       -> Manage tools in the "tools" directory
│   └── tts_stt_utils.py       -> Manage modules in the "modules" directory
├── logs                 -> Logs
├── memory               -> Where long term LLM memory is stored
│   ├── main_memory      -> Default long term memory
│   └── memory_registry.json   -> Registry file to track memory files 
├── models               -> Locally downloaded LLM's
├── modules              -> Modules that enhance end user engagement
│   ├── speech2text      -> Enable end user to talk to LLM (speech to text)
│   ├── text2speech      -> Enable LLM to talk to end user (text to speech)
│   └── modules_registry.json  -> Registry file to track module files
├── tests                -> Unit Tests for developer use
├── tools                -> Tools to extend LLM functionality
│   └── tools_registry.json    -> Registry file to track tool files
├── workflow             -> Author's notes 
├── QUICK_INSTALL.md     -> Install and setup document
├── README.md
├── RUN_UNIT_TESTS.sh    -> Runs Unit Tests (used for development)
├── pytest.ini           -> Used for Unit Testing (used for development)
├── setup.py             -> Needed for install
└── requirements.txt     -> Needed for install
```

---

## Directory Descriptions

### `/bin`
Contains executable scripts and command-line tools for running and testing the framework.

- **`llf`**: Main executable script to launch the framework
- **`start_llama_server.sh`**: Script to start the Llama server
- **`demo_cli.sh`**: Demo script for CLI usage
- **`manual_tests/`**: Manual testing scripts for CLI and server functionality
- **`tools/`**: Utility scripts for model conversion

### `/configs`
Configuration files for the LLM framework and prompt settings.

- **`config.json`**: Active configuration file for LLM settings
- **`config_prompt.json`**: Active prompt configuration file
- **`config_examples/`**: Example configurations for various LLM providers (OpenAI, Anthropic, local models)
- **`config_prompt_examples/`**: Example prompt configurations for different assistant personalities
- **`backups/`**: Timestamped configuration backups

### `/data_stores`
RAG (Retrieval-Augmented Generation) data storage and management.

- **`embedding_models/`**: Directory for storing downloaded embedding models
- **`vector_stores/`**: Directory for vector database storage
- **`data_store_registry.json`**: Registry of available data stores

### `/docs`
Project documentation and notes.

### `/llf`
Core Python package containing the main framework logic.

Key modules:
- **`cli.py`**: Command-line interface implementation
- **`gui.py`**: Gradio-based graphical user interface
- **`llm_runtime.py`**: Core LLM interaction logic and message handling
- **`config.py`**: Configuration management
- **`prompt_config.py`**: Prompt template management
- **`memory_manager.py`**: Long-term memory system
- **`memory_tools.py`**: Memory tool calling functions
- **`rag_retriever.py`**: RAG retrieval functionality
- **`server_commands.py`**: Server management commands
- **`model_manager.py`**: Model loading and management
- **`tools_manager.py`**: Tool system and compatibility layers
- **`tts_stt_utils.py`**: Text-to-Speech and Speech-to-Text utilities
- **`operation_detector.py`**: Detects user intent from messages
- **`logging_config.py`**: Centralized logging configuration

### `/logs`
Application log files.

### `/memory`
Persistent memory storage for conversations.

- **`main_memory/`**: Default memory store with JSONL format
- **`memory_registry.json`**: Registry of available memory stores

### `/models`
Local LLM model files (GGUF format).

Contains downloaded quantized models for local inference.

### `/modules`
Pluggable modules for extended functionality.

- **`speech2text/`**: Speech-to-text engine using Whisper
- **`text2speech/`**: Text-to-speech engine with multiple backend support
- **`modules_registry.json`**: Registry of available modules

### `/tests`
Comprehensive test suite using pytest.

Contains unit tests for all major components, integration tests, and test configuration.

### `/tools`
Tool system and compatibility layers.

- **`xml_format/`**: XML-to-JSON function call parser for models without native JSON tool calling
- **`tools_registry.json`**: Registry of available tools and their states

## Key Files

- **`README.md`**: Main project documentation and setup instructions
- **`QUICK_INSTALL.md`**: Quick installation guide
- **`requirements.txt`**: Python package dependencies
- **`setup.py`**: Package installation configuration
- **`pytest.ini`**: Pytest configuration
- **`.coveragerc`**: Code coverage configuration
- **`RUN_UNIT_TESTS.sh`**: Script to run the full test suite
# Local LLM Framework - Directory Structure

This document provides a comprehensive outline of the directory structure for the Local LLM Framework project.

**Last Updated:** 2025-12-28

---

## Project Root Structure

```
local_llm_framework/
├── bin
│   ├── manual_tests
│   │   ├── test_cli_mode.sh
│   │   └── test_server.sh
│   ├── tools
│   │   └── convert_huggingface_llm_2_gguf.sh
│   ├── README.md
│   ├── demo_cli.sh
│   ├── llf
│   └── start_llama_server.sh
├── configs
│   ├── backups
│   │   ├── REAME.md
│   │   ├── config_20251219_214450.json
│   │   ├── config_20251220_190537.json
│   │   └── config_prompt_20251219_214624.json
│   ├── config_examples
│   │   ├── README.md
│   │   ├── config.anthropic.example
│   │   ├── config.anthropic.json
│   │   ├── config.json.example
│   │   ├── config.local.example
│   │   ├── config.local.gguf.example
│   │   ├── config.local.gguf.json
│   │   ├── config.local.huggingface.example
│   │   ├── config.local.huggingface.json
│   │   ├── config.multi-server.json
│   │   ├── config.openai.example
│   │   └── config.openai.json
│   ├── config_prompt_examples
│   │   ├── config_prompt.coding_assistant.json
│   │   ├── config_prompt.creative_writer.json
│   │   ├── config_prompt.helpful_assistant.json
│   │   ├── config_prompt.minimal.json
│   │   ├── config_prompt.socratic_tutor.json
│   │   └── config_prompt.structured_conversation.json
│   ├── README.md
│   ├── config.json
│   ├── config.json.ORG
│   ├── config_multi_server.json
│   ├── config_prompt.json
│   └── config_single_server.json
├── data_stores
│   ├── embedding_models
│   │   └── README.md
│   ├── tools
│   │   ├── CREATE_VECTOR_STORE.sh
│   │   ├── Create_VectorStore.py
│   │   ├── Process_DOC.py
│   │   ├── Process_MD.py
│   │   ├── Process_PDF.py
│   │   ├── Process_TXT.py
│   │   ├── Process_WEB.py
│   │   └── Validate_JSONL.py
│   ├── vector_stores
│   │   └── README.md
│   ├── README_FOR_RAG.txt
│   ├── data_store_registry.json
│   ├── data_store_registry_EXAMPLE.json
│   └── download_embedding_models.py
├── docs
│   ├── archive
│   │   ├── CHANGELOG_TOOL_EXECUTION_MODES.md
│   │   ├── CLI_MODE_IMPLEMENTATION.md
│   │   ├── CODEBASE_REVIEW.md
│   │   ├── CONFIG_README.md
│   │   ├── COVERAGE_FIX_SUMMARY.md
│   │   ├── COVERAGE_IMPROVEMENT.md
│   │   ├── EMBEDDING_MODELS.md
│   │   ├── FINAL_TEST_STATUS.md
│   │   ├── GUI_CONTINUOUS_LISTENING.md
│   │   ├── GUI_MODULE_RELOAD.md
│   │   ├── GUI_STT_TTS_IMPROVEMENTS.md
│   │   ├── GUI_VOICE_FEATURES_COMPLETE.md
│   │   ├── HOUSEKEEPING_2025-12-17.md
│   │   ├── LOG_FILE_FEATURE.md
│   │   ├── MEMORY_DEBUG_GUIDE.md
│   │   ├── MEMORY_SOLUTION.md
│   │   ├── MEMORY_SYSTEM.md
│   │   ├── MODULE_ENABLE_DISABLE_ALL.md
│   │   ├── MODULE_ENHANCEMENTS_SUMMARY.md
│   │   ├── MULTI_SERVER_IMPLEMENTATION.md
│   │   ├── NEW_TEST_COVERAGE.md
│   │   ├── PERFORMANCE_REVIEW.md
│   │   ├── QUICK_REFERENCE.md
│   │   ├── QUICK_REFERENCE_2.md
│   │   ├── README.md
│   │   ├── README_2.md
│   │   ├── README_3.md
│   │   ├── README_RAG.md
│   │   ├── SIMPLEMOCK_SOLUTION.md
│   │   ├── TESTING_QUICK_REFERENCE.md
│   │   ├── TESTING_README.md
│   │   ├── TESTING_STATUS.md
│   │   ├── TEST_FIXES_SUMMARY.md
│   │   ├── TEST_HANG_FIX.md
│   │   ├── TOOL_EXECUTION_MODES.md
│   │   ├── USAGE.md
│   │   ├── VOICE_FEATURES_QUICK_START.md
│   │   ├── XML_FORMAT_GUIDE.md
│   │   ├── cli_improvements.md
│   │   ├── implementation_summary.md
│   │   └── workflow_README.md
│   ├── Directory_Structure.md
│   ├── Helpful_Commands.md
│   ├── Major_Components.md
│   ├── config_json.md
│   ├── config_prompt_json.md
│   ├── data_store_registry_json.md
│   ├── memory_registry_json.md
│   ├── modules_registry_json.md
│   ├── tools_registryi_json.md
│   └── virtual_environment.md
├── llf
│   ├── README.md
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── gui.py
│   ├── llm_runtime.py
│   ├── logging_config.py
│   ├── memory_manager.py
│   ├── memory_tools.py
│   ├── model_manager.py
│   ├── operation_detector.py
│   ├── prompt_config.py
│   ├── rag_retriever.py
│   ├── server_commands.py
│   ├── tools_manager.py
│   └── tts_stt_utils.py
├── logs
│   ├── README.md
│   └── gui.log
├── memory
│   ├── main_memory
│   │   ├── README.md
│   │   ├── index.json
│   │   ├── memory.jsonl
│   │   └── metadata.json
│   ├── README.md
│   └── memory_registry.json
├── models
│   ├── Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF
│   │   └── Qwen--Qwen3-Coder-30B-A3B-Instruct_f16_q5_K_M.gguf
│   ├── mradermacher--CodeLlama-70b-Instruct-hf-i1-GGUF
│   │   └── CodeLlama-70b-Instruct-hf.i1-Q5_K_M.gguf
│   └── README.md
├── modules
│   ├── speech2text
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── manual_test_sst.py
│   │   ├── module_info.json
│   │   ├── module_info.json.backup
│   │   ├── stt_engine.py
│   │   └── stt_engine.py.backup
│   ├── text2speech
│   │   ├── .coverage
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── list_voices.py
│   │   ├── module_info.json
│   │   ├── module_info.json.backup
│   │   ├── test_tts.py
│   │   ├── tts_base.py
│   │   ├── tts_macos.py
│   │   └── tts_pyttsx3.py
│   └── modules_registry.json
├── tests
│   ├── README.md
│   ├── __init__.py
│   ├── conftest.py
│   ├── manual_test_missing_config.py
│   ├── pytest_hooks.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_config_tool_execution_mode.py
│   ├── test_gui.py
│   ├── test_llm_runtime.py
│   ├── test_llm_runtime_multiserver.py
│   ├── test_llm_runtime_multiserver.py.bak
│   ├── test_logging_config.py
│   ├── test_memory_integration.py
│   ├── test_memory_tool_calling.py
│   ├── test_model_manager.py
│   ├── test_multiserver_config.py
│   ├── test_operation_detector.py
│   ├── test_prompt_config.py
│   ├── test_rag_retriever.py
│   ├── test_server_commands.py
│   ├── test_stt_engine.py
│   ├── test_text2speech_module.py.deprecated
│   ├── test_tools_manager.py
│   ├── test_tts_pyttsx3.py
│   ├── test_tts_stt_utils.py
│   └── test_xml_tool_parser.py
├── tools
│   ├── xml_format
│   │   ├── __init__.py
│   │   └── parser.py
│   ├── README.md
│   └── tools_registry.json
├── workflow
│   ├── 1_Create_PRD.txt
│   ├── 2_Multi_Line_Input_CLI.txt
│   ├── 3_Input_as_Parm.txt
│   ├── 4_Create_Mockup.txt
│   ├── 5_GUI.txt
│   ├── 6_Testing_Outline.txt
│   ├── 7_Text_to_Speech.txt
│   ├── 8_Data_Store.txt
│   ├── 9_Memory_Commands.txt
│   ├── ChatGPT_image.png
│   └── PRD.pdf
├── .coverage
├── .coveragerc
├── QUICK_INSTALL.md
├── README.md
├── RUN_UNIT_TESTS.sh
├── pytest.ini
├── requirements.txt
├── setup.py
├── test_memory_debug.py
└── test_results.txt
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
- **`tools/`**: Scripts for processing various document formats (PDF, DOC, MD, TXT, Web) and creating vector stores
- **`data_store_registry.json`**: Registry of available data stores

### `/docs`
Project documentation and archived implementation notes.

- **Configuration documentation**: Detailed guides for config files
- **`archive/`**: Historical implementation summaries and feature documentation
- **`Major_Components.md`**: Overview of system architecture
- **`Helpful_Commands.md`**: Quick reference for common operations

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

- **`gui.log`**: GUI application logs

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

### `/workflow`
Development workflow documentation and planning materials.

Contains PRD (Product Requirements Document) and implementation planning files.

---

## Key Files

- **`README.md`**: Main project documentation and setup instructions
- **`QUICK_INSTALL.md`**: Quick installation guide
- **`requirements.txt`**: Python package dependencies
- **`setup.py`**: Package installation configuration
- **`pytest.ini`**: Pytest configuration
- **`.coveragerc`**: Code coverage configuration
- **`RUN_UNIT_TESTS.sh`**: Script to run the full test suite

---

## Notes

- The `llf_venv/` directory (not shown) contains the Python virtual environment
- The `.cache/` directory (not shown) contains Hugging Face model cache
- `__pycache__/` directories (not shown) contain Python bytecode

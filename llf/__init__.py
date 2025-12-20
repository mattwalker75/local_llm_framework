"""
Local LLM Framework (LLF)

A Python framework for running Large Language Models locally using llama.cpp
or connecting to external LLM APIs (OpenAI, Anthropic, etc.).

Current Features:
- CLI-based interaction with local or remote LLMs
- Model management (download, verify, delete from HuggingFace)
- Flexible configuration (JSON-based, supports multiple LLM backends)
- Chat and completion APIs with streaming support

Future: API server, GUI, voice I/O, tool execution
"""

__version__ = "0.2.0"
__author__ = "LLF Development Team"

from .config import Config, get_config
from .model_manager import ModelManager
from .llm_runtime import LLMRuntime
from .cli import CLI

__all__ = [
    'Config',
    'get_config',
    'ModelManager',
    'LLMRuntime',
    'CLI',
]

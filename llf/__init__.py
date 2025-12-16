"""
Local LLM Framework (LLF)

A Python framework for running Large Language Models locally using vLLM.

Phase 1: CLI-based interaction with local LLMs
Future: API server, GUI, voice I/O, tool execution
"""

__version__ = "0.1.0"
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

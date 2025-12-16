"""
Configuration module for Local LLM Framework.

This module manages all configuration settings for the LLM framework,
including model settings, paths, and inference parameters.

Design: Built to be extensible for future multi-model support and
additional configuration options without breaking existing functionality.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class Config:
    """
    Configuration manager for LLF.

    Phase 1: Simple configuration with constants.
    Future: Will support loading from config files, environment variables,
    and multi-model configurations.
    """

    # Default model settings (GGUF format for llama.cpp)
    DEFAULT_MODEL_NAME: str = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    DEFAULT_MODEL_ALIAS: str = "qwen2.5-coder"
    DEFAULT_GGUF_FILE: str = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"  # Default quantized model file

    # Directory structure
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DEFAULT_MODEL_DIR: Path = PROJECT_ROOT / "models"
    DEFAULT_CACHE_DIR: Path = PROJECT_ROOT / ".cache"

    # Llama server settings (replaces vLLM)
    DEFAULT_LLAMA_SERVER_PATH: Path = PROJECT_ROOT.parent / "llama.cpp" / "build" / "bin" / "llama-server"
    SERVER_WRAPPER_SCRIPT: Path = PROJECT_ROOT / "bin" / "start_llama_server.sh"

    # Server connection settings
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    # Inference parameters
    DEFAULT_INFERENCE_PARAMS: Dict[str, Any] = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1,
    }

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to JSON configuration file.
                        If None, uses default values.
        """
        self.model_name = self.DEFAULT_MODEL_NAME
        self.model_alias = self.DEFAULT_MODEL_ALIAS
        self.gguf_file = self.DEFAULT_GGUF_FILE
        self.model_dir = self.DEFAULT_MODEL_DIR
        self.cache_dir = self.DEFAULT_CACHE_DIR
        self.llama_server_path = self.DEFAULT_LLAMA_SERVER_PATH
        self.server_wrapper_script = self.SERVER_WRAPPER_SCRIPT
        self.server_host = self.SERVER_HOST
        self.server_port = self.SERVER_PORT
        self.inference_params = self.DEFAULT_INFERENCE_PARAMS.copy()
        self.log_level = self.LOG_LEVEL

        # Load from config file if provided
        if config_file and config_file.exists():
            self._load_from_file(config_file)

        # Create necessary directories
        self._ensure_directories()

    def _load_from_file(self, config_file: Path) -> None:
        """
        Load configuration from JSON file.

        Args:
            config_file: Path to JSON configuration file.
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # Update configuration from file
            self.model_name = config_data.get('model_name', self.model_name)
            self.model_alias = config_data.get('model_alias', self.model_alias)
            self.gguf_file = config_data.get('gguf_file', self.gguf_file)

            if 'model_dir' in config_data:
                self.model_dir = Path(config_data['model_dir'])

            if 'cache_dir' in config_data:
                self.cache_dir = Path(config_data['cache_dir'])

            if 'llama_server_path' in config_data:
                self.llama_server_path = Path(config_data['llama_server_path'])

            if 'inference_params' in config_data:
                self.inference_params.update(config_data['inference_params'])

            self.server_host = config_data.get('server_host', self.server_host)
            self.server_port = config_data.get('server_port', self.server_port)
            self.log_level = config_data.get('log_level', self.log_level)

        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_file}: {e}")

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_server_url(self) -> str:
        """
        Get the full server URL.

        Returns:
            Full URL including protocol, host, and port.
        """
        return f"http://{self.server_host}:{self.server_port}"

    def get_openai_api_base(self) -> str:
        """
        Get the OpenAI-compatible API base URL for llama-server.

        Returns:
            Base URL for OpenAI-compatible endpoints.
        """
        return f"{self.get_server_url()}/v1"

    # Deprecated: Keep for backward compatibility
    def get_vllm_url(self) -> str:
        """
        Deprecated: Use get_server_url() instead.
        Kept for backward compatibility.
        """
        return self.get_server_url()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration.
        """
        return {
            'model_name': self.model_name,
            'model_alias': self.model_alias,
            'gguf_file': self.gguf_file,
            'model_dir': str(self.model_dir),
            'cache_dir': str(self.cache_dir),
            'llama_server_path': str(self.llama_server_path),
            'server_host': self.server_host,
            'server_port': self.server_port,
            'inference_params': self.inference_params,
            'log_level': self.log_level,
        }

    def save_to_file(self, config_file: Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            config_file: Path where configuration should be saved.
        """
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Global default configuration instance
_default_config: Optional[Config] = None


def get_config(config_file: Optional[Path] = None) -> Config:
    """
    Get configuration instance.

    Args:
        config_file: Optional path to configuration file.

    Returns:
        Configuration instance.
    """
    global _default_config
    if _default_config is None or config_file is not None:
        _default_config = Config(config_file)
    return _default_config

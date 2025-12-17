"""
Configuration module for Local LLM Framework.

This module manages all configuration settings for the LLM framework,
including model settings, paths, and inference parameters.

Design: Built to be extensible for future multi-model support and
additional configuration options without breaking existing functionality.
"""

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
    DEFAULT_GGUF_FILE: str = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"  # Default quantized model file

    # Directory structure
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DEFAULT_CONFIG_FILE: Path = PROJECT_ROOT / "config.json"
    DEFAULT_MODEL_DIR: Path = PROJECT_ROOT / "models"
    DEFAULT_CACHE_DIR: Path = PROJECT_ROOT / ".cache"

    # Llama server settings (replaces vLLM)
    DEFAULT_LLAMA_SERVER_PATH: Path = PROJECT_ROOT.parent / "llama.cpp" / "build" / "bin" / "llama-server"
    SERVER_WRAPPER_SCRIPT: Path = PROJECT_ROOT / "bin" / "start_llama_server.sh"

    # Server connection settings
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    # API settings (used for both local and external LLM providers)
    API_BASE_URL: str = "http://127.0.0.1:8000/v1"  # Default to local server
    API_KEY: str = "EMPTY"  # Used for external APIs (OpenAI, Anthropic, etc.)

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
                        If None, automatically looks for config.json in project root.
                        If that doesn't exist, uses default values.
        """
        self.model_name = self.DEFAULT_MODEL_NAME
        self.gguf_file = self.DEFAULT_GGUF_FILE
        self.model_dir = self.DEFAULT_MODEL_DIR
        self.cache_dir = self.DEFAULT_CACHE_DIR
        self.llama_server_path = self.DEFAULT_LLAMA_SERVER_PATH
        self.server_wrapper_script = self.SERVER_WRAPPER_SCRIPT
        self.server_host = self.SERVER_HOST
        self.server_port = self.SERVER_PORT
        self.api_base_url = self.API_BASE_URL
        self.api_key = self.API_KEY
        self.inference_params = self.DEFAULT_INFERENCE_PARAMS.copy()
        self.log_level = self.LOG_LEVEL

        # Determine which config file to use
        config_to_load = None
        if config_file is not None:
            # Explicit config file provided
            config_to_load = config_file
        elif self.DEFAULT_CONFIG_FILE.exists():
            # Use default config.json if it exists
            config_to_load = self.DEFAULT_CONFIG_FILE

        # Load from config file if available
        if config_to_load and config_to_load.exists():
            self._load_from_file(config_to_load)

        # Create necessary directories
        self._ensure_directories()

    def _load_from_file(self, config_file: Path) -> None:
        """
        Load configuration from JSON file.

        Relative paths in the config file are resolved relative to the project root.

        Args:
            config_file: Path to JSON configuration file.
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # ===== Server Configuration (for local llama-server) =====
            # These settings control the local llama-server process when started by LLF
            # Supports both nested 'local_llm_server' structure and flat structure for backward compatibility
            if 'local_llm_server' in config_data:
                server_config = config_data['local_llm_server']
                # Path to llama-server binary
                if 'llama_server_path' in server_config:
                    path = Path(server_config['llama_server_path'])
                    # Convert relative paths to absolute (relative to project root)
                    self.llama_server_path = path if path.is_absolute() else self.PROJECT_ROOT / path
                # Server bind address (127.0.0.1 for localhost only, 0.0.0.0 for network access)
                self.server_host = server_config.get('server_host', self.server_host)
                # Server port number
                self.server_port = server_config.get('server_port', self.server_port)
                # GGUF model file to load (quantized model format for llama.cpp)
                self.gguf_file = server_config.get('gguf_file', self.gguf_file)
            else:
                # Fallback to flat structure for backward compatibility with older config files
                if 'llama_server_path' in config_data:
                    path = Path(config_data['llama_server_path'])
                    self.llama_server_path = path if path.is_absolute() else self.PROJECT_ROOT / path
                self.server_host = config_data.get('server_host', self.server_host)
                self.server_port = config_data.get('server_port', self.server_port)
                self.gguf_file = config_data.get('gguf_file', self.gguf_file)

            # ===== LLM Endpoint Configuration (client-side) =====
            # These settings determine which LLM API to use for inference
            # Can point to local llama-server OR external APIs (OpenAI, Anthropic, etc.)
            if 'llm_endpoint' in config_data:
                endpoint_config = config_data['llm_endpoint']
                # API base URL - determines if using local or external LLM
                self.api_base_url = endpoint_config.get('api_base_url', self.api_base_url)
                # API key for authentication (use "EMPTY" for local server)
                self.api_key = endpoint_config.get('api_key', self.api_key)
                # Model name/identifier to use for requests
                self.model_name = endpoint_config.get('model_name', self.model_name)
            else:
                # Fallback to flat structure for backward compatibility with older config files
                self.api_base_url = config_data.get('api_base_url', self.api_base_url)
                self.api_key = config_data.get('api_key', self.api_key)
                self.model_name = config_data.get('model_name', self.model_name)

            # ===== Legacy Configuration Support =====
            # Support old 'default_llm' structure from earlier versions
            if 'default_llm' in config_data:
                llm_config = config_data['default_llm']
                # Only apply these if newer nested structures aren't present
                if 'model_name' in llm_config and 'llm_endpoint' not in config_data:
                    self.model_name = llm_config['model_name']
                if 'gguf_file' in llm_config and 'local_llm_server' not in config_data:
                    self.gguf_file = llm_config['gguf_file']

            # ===== Directory Paths =====
            # Resolve relative paths from project root for portability
            if 'model_dir' in config_data:
                path = Path(config_data['model_dir'])
                self.model_dir = path if path.is_absolute() else self.PROJECT_ROOT / path

            if 'cache_dir' in config_data:
                path = Path(config_data['cache_dir'])
                self.cache_dir = path if path.is_absolute() else self.PROJECT_ROOT / path

            # ===== Inference Parameters =====
            # IMPORTANT: We REPLACE (not merge) to give config file full control
            # This allows different parameter sets for local vs external LLMs
            # Example: OpenAI uses 'max_completion_tokens', llama.cpp uses 'max_tokens'
            if 'inference_params' in config_data:
                self.inference_params = config_data['inference_params'].copy()

            # ===== Logging Configuration =====
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
        Get the OpenAI-compatible API base URL.

        Returns the configured api_base_url, which can point to either
        local llama-server or external API (OpenAI, etc.).

        Returns:
            Base URL for OpenAI-compatible endpoints.
        """
        return self.api_base_url

    # Deprecated: Keep for backward compatibility
    def get_vllm_url(self) -> str:
        """
        Deprecated: Use get_server_url() instead.
        Kept for backward compatibility.
        """
        return self.get_server_url()

    def is_using_external_api(self) -> bool:
        """
        Check if configuration is using an external LLM API.

        This method determines whether the framework should:
        - Skip model downloads (external APIs host models remotely)
        - Skip local server start/stop operations
        - Use different parameter sets (external APIs may not support llama.cpp-specific params)

        Returns True if api_base_url points to an external service
        (OpenAI, Anthropic, etc.) instead of a local server.

        Returns:
            True if using external API, False if using local server.
        """
        # Simple heuristic: check if api_base_url contains localhost or 127.0.0.1
        # Any URL without these is assumed to be an external service
        api_url_lower = self.api_base_url.lower()
        return not ('localhost' in api_url_lower or '127.0.0.1' in api_url_lower)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration with nested structure.
        """
        return {
            'local_llm_server': {
                'llama_server_path': str(self.llama_server_path),
                'server_host': self.server_host,
                'server_port': self.server_port,
                'gguf_file': self.gguf_file,
            },
            'llm_endpoint': {
                'api_base_url': self.api_base_url,
                'api_key': self.api_key,
                'model_name': self.model_name,
            },
            'model_dir': str(self.model_dir),
            'cache_dir': str(self.cache_dir),
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

"""
LLM runtime module for Local LLM Framework.

This module manages the llama-server lifecycle and provides inference capabilities.

Design: Abstracts llama-server management and uses OpenAI-compatible API for inference.
Future: Can be extended to support different backends, streaming, and batch processing.
"""

import subprocess
import time
import signal
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from openai import OpenAI

from .logging_config import get_logger
from .config import Config
from .model_manager import ModelManager

logger = get_logger(__name__)


class LLMRuntime:
    """
    Manages llama-server lifecycle and provides inference interface.

    Responsibilities:
    - Start and stop llama-server via wrapper script
    - Health checking
    - Execute inference via OpenAI-compatible API
    - Handle errors and timeouts
    """

    def __init__(self, config: Config, model_manager: ModelManager):
        """
        Initialize LLM runtime.

        Args:
            config: Configuration instance.
            model_manager: Model manager instance.
        """
        self.config = config
        self.model_manager = model_manager
        self.server_process: Optional[subprocess.Popen] = None
        self.client: Optional[OpenAI] = None

    def _get_server_command(self, model_file_path: Path) -> List[str]:
        """
        Build llama-server command using wrapper script.

        Args:
            model_file_path: Path to the GGUF model file.

        Returns:
            Command as list of strings.
        """
        cmd = [
            str(self.config.server_wrapper_script),
            "--server-path", str(self.config.llama_server_path),
            "--model-file", str(model_file_path),
            "--host", self.config.server_host,
            "--port", str(self.config.server_port),
        ]

        return cmd

    def start_server(self, model_name: Optional[str] = None, gguf_file: Optional[str] = None, timeout: int = 120) -> None:
        """
        Start llama-server.

        Args:
            model_name: Model directory name. If None, uses config's default model.
            gguf_file: GGUF file name within the model directory. If None, uses config's default.
            timeout: Maximum seconds to wait for server to become ready.

        Raises:
            RuntimeError: If server fails to start or become ready.
            ValueError: If model is not downloaded or llama-server binary not found.
        """
        if model_name is None:
            model_name = self.config.model_name

        if gguf_file is None:
            gguf_file = self.config.gguf_file

        # Check if llama-server binary exists
        if not self.config.llama_server_path.exists():
            raise ValueError(
                f"llama-server binary not found at: {self.config.llama_server_path}\n"
                "Please compile llama.cpp first or configure the correct path."
            )

        # Check if model is downloaded
        if not self.model_manager.is_model_downloaded(model_name):
            raise ValueError(
                f"Model {model_name} is not downloaded. "
                "Please download it first using model_manager.download_model()"
            )

        # Check if server is already running
        if self.is_server_running():
            logger.warning("llama-server is already running")
            return

        # Get model directory and find GGUF file
        model_dir = self.model_manager.get_model_path(model_name)
        model_file_path = model_dir / gguf_file

        if not model_file_path.exists():
            raise ValueError(
                f"GGUF model file not found: {model_file_path}\n"
                f"Available files in {model_dir}: {list(model_dir.glob('*.gguf'))}"
            )

        cmd = self._get_server_command(model_file_path)

        logger.info(f"Starting llama-server with model: {model_name}")
        logger.info(f"GGUF file: {gguf_file}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            # Start llama-server as subprocess
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            logger.info("llama-server process started, waiting for readiness...")

            # Wait for server to become ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_server_ready():
                    logger.info("llama-server is ready!")
                    self._initialize_client()
                    return

                # Check if process has terminated
                if self.server_process.poll() is not None:
                    stderr = self.server_process.stderr.read() if self.server_process.stderr else "No error output"
                    raise RuntimeError(
                        f"llama-server process terminated unexpectedly:\n{stderr}"
                    )

                time.sleep(2)

            # Timeout reached
            self.stop_server()
            raise RuntimeError(
                f"llama-server failed to become ready within {timeout} seconds"
            )

        except Exception as e:
            self.stop_server()
            raise RuntimeError(f"Failed to start llama-server: {e}") from e

    def stop_server(self) -> None:
        """Stop llama-server gracefully."""
        if self.server_process is None:
            logger.debug("No llama-server process to stop")
            return

        logger.info("Stopping llama-server...")

        try:
            # Try graceful shutdown first
            self.server_process.send_signal(signal.SIGTERM)
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Graceful shutdown timed out, force killing...")
                self.server_process.kill()
                self.server_process.wait()

            logger.info("llama-server stopped")

        except Exception as e:
            logger.error(f"Error stopping llama-server: {e}")

        finally:
            self.server_process = None
            self.client = None

    def is_server_running(self) -> bool:
        """
        Check if llama-server is running and accessible.

        This checks if the server is responding to health checks, which works
        regardless of whether the server was started by this process or another.

        Returns:
            True if server is running and accessible, False otherwise.
        """
        # First check if we have a local process reference
        if self.server_process is not None and self.server_process.poll() is None:
            return True

        # If we don't have a local process, check if server is accessible via HTTP
        # This handles the case where the server was started in another terminal/process
        return self.is_server_ready()

    def is_server_ready(self) -> bool:
        """
        Check if llama-server is ready to accept requests.

        Returns:
            True if server is ready, False otherwise.
        """
        try:
            health_url = f"{self.config.get_server_url()}/health"
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _initialize_client(self) -> None:
        """Initialize OpenAI client for llama-server."""
        self.client = OpenAI(
            base_url=self.config.get_openai_api_base(),
            api_key="EMPTY",  # llama-server doesn't require API key
        )

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: Input prompt text.
            model: Model name (for multi-model setups). If None, uses loaded model.
            **kwargs: Additional parameters to override config defaults:
                - temperature: float
                - max_tokens: int
                - top_p: float
                - top_k: int
                - repetition_penalty: float
                - stop: List[str] (stop sequences)
                - stream: bool (not supported in Phase 1)

        Returns:
            Generated text completion.

        Raises:
            RuntimeError: If server is not running or request fails.
        """
        if not self.is_server_running():
            raise RuntimeError("llama-server is not running")

        if self.client is None:
            self._initialize_client()

        # Merge config defaults with kwargs
        params = self.config.inference_params.copy()
        params.update(kwargs)

        # Extract OpenAI-compatible parameters
        openai_params = {
            'model': model or self.config.model_name,
            'prompt': prompt,
            'temperature': params.get('temperature', 0.7),
            'max_tokens': params.get('max_tokens', 2048),
            'top_p': params.get('top_p', 0.9),
            'stop': params.get('stop', None),
        }

        # llama-server-specific parameters
        extra_body = {}
        if 'top_k' in params:
            extra_body['top_k'] = params['top_k']
        if 'repetition_penalty' in params:
            extra_body['repetition_penalty'] = params['repetition_penalty']

        if extra_body:
            openai_params['extra_body'] = extra_body

        try:
            logger.debug(f"Generating completion with params: {openai_params}")

            # Use completion API (not chat)
            response = self.client.completions.create(**openai_params)

            # Extract generated text
            generated_text = response.choices[0].text

            logger.debug(f"Generated {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"Failed to generate completion: {e}") from e

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate chat completion from conversation messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Example: [{'role': 'user', 'content': 'Hello!'}]
            model: Model name (for multi-model setups). If None, uses loaded model.
            **kwargs: Additional parameters (same as generate()).

        Returns:
            Generated response text.

        Raises:
            RuntimeError: If server is not running or request fails.
        """
        if not self.is_server_running():
            raise RuntimeError("llama-server is not running")

        if self.client is None:
            self._initialize_client()

        # Merge config defaults with kwargs
        params = self.config.inference_params.copy()
        params.update(kwargs)

        # Extract OpenAI-compatible parameters
        openai_params = {
            'model': model or self.config.model_name,
            'messages': messages,
            'temperature': params.get('temperature', 0.7),
            'max_tokens': params.get('max_tokens', 2048),
            'top_p': params.get('top_p', 0.9),
            'stop': params.get('stop', None),
        }

        # llama-server-specific parameters
        extra_body = {}
        if 'top_k' in params:
            extra_body['top_k'] = params['top_k']
        if 'repetition_penalty' in params:
            extra_body['repetition_penalty'] = params['repetition_penalty']

        if extra_body:
            openai_params['extra_body'] = extra_body

        try:
            logger.debug(f"Generating chat completion with {len(messages)} messages")

            # Use chat completion API
            response = self.client.chat.completions.create(**openai_params)

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"Generated {len(response_text)} characters")
            return response_text

        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise RuntimeError(f"Failed to generate chat completion: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures server is stopped."""
        self.stop_server()

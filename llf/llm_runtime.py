"""
LLM runtime module for Local LLM Framework.

This module manages the vLLM server lifecycle and provides inference capabilities.

Design: Abstracts vLLM server management and uses OpenAI-compatible API for inference.
Future: Can be extended to support different backends, streaming, and batch processing.
"""

import subprocess
import time
import signal
import sys
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
    Manages vLLM server lifecycle and provides inference interface.

    Responsibilities:
    - Start and stop vLLM server
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
        self.vllm_process: Optional[subprocess.Popen] = None
        self.client: Optional[OpenAI] = None

    def _get_vllm_command(self, model_path: Path) -> List[str]:
        """
        Build vLLM server command.

        Args:
            model_path: Path to the model directory.

        Returns:
            Command as list of strings.
        """
        cmd = [
            sys.executable,  # Use same Python as current environment
            "-m", "vllm.entrypoints.openai.api_server",
            "--model", str(model_path),
            "--host", self.config.vllm_host,
            "--port", str(self.config.vllm_port),
            "--gpu-memory-utilization", str(self.config.vllm_gpu_memory_utilization),
        ]

        # Optional max model length
        if self.config.vllm_max_model_len:
            cmd.extend(["--max-model-len", str(self.config.vllm_max_model_len)])

        return cmd

    def start_server(self, model_name: Optional[str] = None, timeout: int = 300) -> None:
        """
        Start vLLM server.

        Args:
            model_name: Model to load. If None, uses config's default model.
            timeout: Maximum seconds to wait for server to become ready.

        Raises:
            RuntimeError: If server fails to start or become ready.
            ValueError: If model is not downloaded.
        """
        if model_name is None:
            model_name = self.config.model_name

        # Check if model is downloaded
        if not self.model_manager.is_model_downloaded(model_name):
            raise ValueError(
                f"Model {model_name} is not downloaded. "
                "Please download it first using model_manager.download_model()"
            )

        # Check if server is already running
        if self.is_server_running():
            logger.warning("vLLM server is already running")
            return

        model_path = self.model_manager.get_model_path(model_name)
        cmd = self._get_vllm_command(model_path)

        logger.info(f"Starting vLLM server with model: {model_name}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            # Start vLLM server as subprocess
            self.vllm_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            logger.info("vLLM server process started, waiting for readiness...")

            # Wait for server to become ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_server_ready():
                    logger.info("vLLM server is ready!")
                    self._initialize_client()
                    return

                # Check if process has terminated
                if self.vllm_process.poll() is not None:
                    stderr = self.vllm_process.stderr.read() if self.vllm_process.stderr else "No error output"
                    raise RuntimeError(
                        f"vLLM server process terminated unexpectedly:\n{stderr}"
                    )

                time.sleep(2)

            # Timeout reached
            self.stop_server()
            raise RuntimeError(
                f"vLLM server failed to become ready within {timeout} seconds"
            )

        except Exception as e:
            self.stop_server()
            raise RuntimeError(f"Failed to start vLLM server: {e}") from e

    def stop_server(self) -> None:
        """Stop vLLM server gracefully."""
        if self.vllm_process is None:
            logger.debug("No vLLM server process to stop")
            return

        logger.info("Stopping vLLM server...")

        try:
            # Try graceful shutdown first
            self.vllm_process.send_signal(signal.SIGTERM)
            try:
                self.vllm_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Graceful shutdown timed out, force killing...")
                self.vllm_process.kill()
                self.vllm_process.wait()

            logger.info("vLLM server stopped")

        except Exception as e:
            logger.error(f"Error stopping vLLM server: {e}")

        finally:
            self.vllm_process = None
            self.client = None

    def is_server_running(self) -> bool:
        """
        Check if vLLM server process is running.

        Returns:
            True if server process is running, False otherwise.
        """
        return self.vllm_process is not None and self.vllm_process.poll() is None

    def is_server_ready(self) -> bool:
        """
        Check if vLLM server is ready to accept requests.

        Returns:
            True if server is ready, False otherwise.
        """
        try:
            health_url = f"{self.config.get_vllm_url()}/health"
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _initialize_client(self) -> None:
        """Initialize OpenAI client for vLLM server."""
        self.client = OpenAI(
            base_url=self.config.get_openai_api_base(),
            api_key="EMPTY",  # vLLM doesn't require API key
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
            raise RuntimeError("vLLM server is not running")

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

        # vLLM-specific parameters (if using vLLM directly)
        # For OpenAI API compatibility, some params may not be available
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
            raise RuntimeError("vLLM server is not running")

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

        # vLLM-specific parameters
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

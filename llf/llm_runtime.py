"""
LLM runtime module for Local LLM Framework.

This module manages the llama-server lifecycle and provides inference capabilities.

Design: Abstracts llama-server management and uses OpenAI-compatible API for inference.
Future: Can be extended to support different backends, streaming, and batch processing.
"""

import subprocess
import time
import signal
import psutil
from pathlib import Path
from typing import Optional, List, Dict
import requests

from openai import OpenAI

from .logging_config import get_logger
from .config import Config
from .model_manager import ModelManager
from .prompt_config import PromptConfig

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

    def __init__(self, config: Config, model_manager: ModelManager, prompt_config: Optional[PromptConfig] = None):
        """
        Initialize LLM runtime.

        Args:
            config: Configuration instance.
            model_manager: Model manager instance.
            prompt_config: Optional prompt configuration for formatting messages.
        """
        self.config = config
        self.model_manager = model_manager
        self.prompt_config = prompt_config
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

        # Add additional server parameters if configured
        if self.config.server_params:
            for key, value in self.config.server_params.items():
                cmd.extend(["--server-arg", key, str(value)])

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

        # Check if model is downloaded (skip if using custom model directory)
        if self.config.custom_model_dir is None:
            if not self.model_manager.is_model_downloaded(model_name):
                raise ValueError(
                    f"Model {model_name} is not downloaded. "
                    "Please download it first using model_manager.download_model()"
                )

        # Check if server is already running
        if self.is_server_running():
            logger.warning("llama-server is already running")
            return

        # Determine model file path
        # If custom_model_dir is set, use it directly
        if self.config.custom_model_dir is not None:
            model_file_path = self.config.custom_model_dir / gguf_file
            if not model_file_path.exists():
                raise ValueError(
                    f"GGUF model file not found: {model_file_path}\n"
                    f"Custom model directory: {self.config.custom_model_dir}\n"
                    f"Available files: {list(self.config.custom_model_dir.glob('*.gguf')) if self.config.custom_model_dir.exists() else 'Directory does not exist'}"
                )
        else:
            # Use HuggingFace model path
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

    def _find_llama_server_process(self) -> Optional[psutil.Process]:
        """
        Find the llama-server process by looking for running processes.

        Returns:
            psutil.Process if found, None otherwise.
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if this is a llama-server process
                    cmdline = proc.info['cmdline']
                    if cmdline and any('llama-server' in str(arg) for arg in cmdline):
                        # Verify it's running on our configured port
                        port = str(self.config.server_port)
                        if any(port in str(arg) for arg in cmdline):
                            logger.debug(f"Found llama-server process: PID={proc.pid}")
                            return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.debug(f"Error searching for llama-server process: {e}")
        return None

    def stop_server(self) -> None:
        """Stop llama-server gracefully."""
        # If we have a local process reference, use it
        if self.server_process is not None:
            logger.info("Stopping llama-server (local process)...")
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
            return

        # Otherwise, try to find and kill the process
        logger.info("Searching for llama-server process...")
        proc = self._find_llama_server_process()

        if proc is None:
            logger.debug("No llama-server process found to stop")
            return

        logger.info(f"Found llama-server process (PID={proc.pid}), stopping...")

        try:
            # Try graceful shutdown first
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Graceful shutdown timed out, force killing...")
                proc.kill()
                proc.wait()

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
        """
        Initialize OpenAI client.

        Uses configurable api_base_url and api_key from config.
        This allows connecting to external APIs (OpenAI, Anthropic, etc.)
        or local llama-server.
        """
        self.client = OpenAI(
            base_url=self.config.get_openai_api_base(),
            api_key=self.config.api_key,
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
        # ===== Server Availability Check =====
        # Only check if local llama-server is running when using local LLM
        # Skip this check for external APIs (OpenAI, Anthropic, etc.) since they don't need local server
        if not self.config.is_using_external_api() and not self.is_server_running():
            raise RuntimeError("llama-server is not running")

        if self.client is None:
            self._initialize_client()

        # ===== Parameter Handling =====
        # Start with config file parameters, then override with any kwargs passed to this method
        params = self.config.inference_params.copy()
        params.update(kwargs)

        # Build the API request parameters, starting with required fields
        openai_params = {
            'model': model or self.config.model_name,
            'prompt': prompt,
        }

        # ===== llama.cpp-Specific Parameters =====
        # These parameters are only supported by llama-server, not external APIs (OpenAI, Anthropic, etc.)
        # We put them in 'extra_body' to keep them separate from standard OpenAI parameters
        extra_body_params = {'top_k', 'repetition_penalty'}

        # ===== Pass Through All Parameters =====
        # This approach allows config files to control EXACTLY which parameters are sent
        # - For local llama-server: include max_tokens, top_k, repetition_penalty, etc.
        # - For OpenAI: include max_tokens or max_completion_tokens (depending on model), but NOT top_k
        # - For other APIs: include whatever parameters they support
        extra_body = {}
        for key, value in params.items():
            if key in extra_body_params:
                # llama.cpp-specific params go in extra_body
                extra_body[key] = value
            else:
                # All other params (temperature, max_tokens, max_completion_tokens, top_p, etc.)
                # are passed directly to the API
                openai_params[key] = value

        # Add extra_body to request if we have llama.cpp-specific parameters
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
        stream: bool = False,
        use_prompt_config: bool = True,
        **kwargs
    ):
        """
        Generate chat completion from conversation messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Example: [{'role': 'user', 'content': 'Hello!'}]
                     If use_prompt_config=True and a user message is detected, prompt config
                     will be applied to build the full message list.
            model: Model name (for multi-model setups). If None, uses loaded model.
            stream: If True, returns an iterator of response chunks. If False, returns complete text.
            use_prompt_config: If True and prompt_config is set, apply prompt formatting to messages.
                              Set to False to send raw messages without prompt config processing.
            **kwargs: Additional parameters (same as generate()).

        Returns:
            If stream=False: Generated response text (str).
            If stream=True: Iterator yielding response chunks (str).

        Raises:
            RuntimeError: If server is not running or request fails.
        """
        # ===== Server Availability Check =====
        # Only check if local llama-server is running when using local LLM
        # Skip this check for external APIs (OpenAI, Anthropic, etc.) since they don't need local server
        if not self.config.is_using_external_api() and not self.is_server_running():
            raise RuntimeError("llama-server is not running")

        if self.client is None:
            self._initialize_client()

        # ===== Prompt Configuration Processing =====
        # Apply prompt config to format/enhance messages if configured
        processed_messages = messages
        if use_prompt_config and self.prompt_config:
            # Check if this is a simple user message that needs full prompt config treatment
            # (single message or last message is from user)
            if messages and messages[-1].get('role') == 'user':
                # Extract user message and conversation history
                user_message = messages[-1]['content']
                conversation_history = messages[:-1] if len(messages) > 1 else None

                # Build complete message list with prompt config
                processed_messages = self.prompt_config.build_messages(
                    user_message=user_message,
                    conversation_history=conversation_history
                )
            # else: messages are already in full format, use as-is

        # ===== Parameter Handling =====
        # Start with config file parameters, then override with any kwargs passed to this method
        params = self.config.inference_params.copy()
        params.update(kwargs)

        # Build the API request parameters, starting with required fields
        openai_params = {
            'model': model or self.config.model_name,
            'messages': processed_messages,
            'stream': stream,
        }

        # ===== llama.cpp-Specific Parameters =====
        # These parameters are only supported by llama-server, not external APIs (OpenAI, Anthropic, etc.)
        # We put them in 'extra_body' to keep them separate from standard OpenAI parameters
        extra_body_params = {'top_k', 'repetition_penalty'}

        # ===== Pass Through All Parameters =====
        # This approach allows config files to control EXACTLY which parameters are sent
        # - For local llama-server: include max_tokens, top_k, repetition_penalty, etc.
        # - For OpenAI: include max_tokens or max_completion_tokens (depending on model), but NOT top_k
        # - For other APIs: include whatever parameters they support
        extra_body = {}
        for key, value in params.items():
            if key in extra_body_params:
                # llama.cpp-specific params go in extra_body
                extra_body[key] = value
            else:
                # All other params (temperature, max_tokens, max_completion_tokens, top_p, etc.)
                # are passed directly to the API
                openai_params[key] = value

        # Add extra_body to request if we have llama.cpp-specific parameters
        if extra_body:
            openai_params['extra_body'] = extra_body

        try:
            logger.debug(f"Generating chat completion with {len(messages)} messages (stream={stream})")

            # Use chat completion API
            response = self.client.chat.completions.create(**openai_params)

            if stream:
                # Return iterator for streaming
                def stream_generator():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return stream_generator()
            else:
                # Extract response text
                response_text = response.choices[0].message.content
                logger.debug(f"Generated {len(response_text)} characters")
                return response_text

        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise RuntimeError(f"Failed to generate chat completion: {e}") from e

    def list_models(self) -> list:
        """
        List available models from the LLM endpoint.

        Queries the OpenAI-compatible /v1/models endpoint to retrieve
        available models. Works with both local llama-server and external
        APIs (OpenAI, Anthropic, etc.).

        Returns:
            List of model dictionaries containing model information.
            Each dict typically contains 'id', 'object', 'created', 'owned_by'.

        Raises:
            RuntimeError: If the API call fails.
        """
        logger.info(f"Listing models from {self.config.api_base_url}")

        try:
            # Ensure client is initialized
            if self.client is None:
                self._initialize_client()

            # Call the models.list() API
            models_response = self.client.models.list()

            # Convert to list of dicts
            models = []
            for model in models_response.data:
                models.append({
                    'id': model.id,
                    'object': model.object,
                    'created': model.created,
                    'owned_by': model.owned_by
                })

            logger.info(f"Found {len(models)} available models")
            return models

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise RuntimeError(f"Failed to list models from {self.config.api_base_url}: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Context manager exit - ensures server is stopped."""
        self.stop_server()

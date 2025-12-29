"""
GUI interface for Local LLM Framework using Gradio.

This module provides a web-based graphical interface for:
- Chatting with LLMs
- Managing server (start/stop/status)
- Managing models (download/list/info)
- Editing configuration files
"""

import json
import gradio as gr
from pathlib import Path
from typing import List, Tuple, Optional
import threading
import time

from .config import Config, get_config
from .prompt_config import PromptConfig, get_prompt_config
from .model_manager import ModelManager
from .llm_runtime import LLMRuntime
from .logging_config import get_logger

logger = get_logger(__name__)

# Constants for download progress messages
DOWNLOAD_PROGRESS_MESSAGE = (
    "🔄 Download in progress...\n"
    "You will be notified when complete.\n\n"
    "⚠️  This process can take a while depending on the size of the model.\n"
    "Please do not close this window."
)


class LLMFrameworkGUI:
    """
    Gradio-based GUI for the LLM Framework.

    Provides tabbed interface for:
    - Chat: Interactive conversation with LLM
    - Server: Start/stop/status controls
    - Models: Download/list/info management
    - Config: Edit config.json and config_prompt.json
    """

    def __init__(self, config: Optional[Config] = None, prompt_config: Optional[PromptConfig] = None, auth_key: Optional[str] = None, share: bool = False):
        """
        Initialize GUI.

        Args:
            config: Configuration instance (defaults to global config)
            prompt_config: Prompt configuration instance (defaults to global)
            auth_key: Optional authentication key for securing GUI access
            share: Whether GUI is running in share mode (--share flag)
        """
        self.config = config or get_config()
        self.prompt_config = prompt_config or get_prompt_config()
        self.model_manager = ModelManager(self.config)
        self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)
        self.chat_history: List[Tuple[str, str]] = []
        self.started_server = False  # Track if GUI started the server
        self.auth_key = auth_key  # Authentication key (None = no auth required)
        self.is_share_mode = share  # Track if running in share mode

        # Load module registry and initialize text-to-speech and speech-to-text if enabled
        self.tts = None
        self.stt = None
        self.tts_enabled_state = True  # Track if user wants TTS enabled (separate from module availability)
        self.listening_mode_active = False  # Track if continuous listening mode is active
        self._load_modules()

    def _load_modules(self) -> None:
        """Load enabled modules from registry."""
        try:
            # Path to modules registry
            modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

            if not modules_registry_path.exists():
                return

            with open(modules_registry_path, 'r') as f:
                registry = json.load(f)

            modules = registry.get('modules', [])

            # Check if text2speech module is enabled
            for module in modules:
                if module.get('name') == 'text2speech' and module.get('enabled', False):
                    try:
                        # Import and initialize text2speech module
                        import sys
                        modules_path = Path(__file__).parent.parent / 'modules'
                        if str(modules_path) not in sys.path:
                            sys.path.insert(0, str(modules_path))

                        from text2speech import TextToSpeech

                        # Load settings from module info
                        settings = module.get('settings', {})
                        self.tts = TextToSpeech(
                            voice_id=settings.get('voice_id'),
                            rate=settings.get('rate', 200),
                            volume=settings.get('volume', 1.0)
                        )
                        logger.info("Text-to-Speech module loaded and enabled for GUI")
                    except Exception as e:
                        logger.warning(f"Failed to load text2speech module: {e}")
                    break

            # Check if speech2text module is enabled
            for module in modules:
                if module.get('name') == 'speech2text' and module.get('enabled', False):
                    try:
                        # Import and initialize speech2text module
                        import sys
                        modules_path = Path(__file__).parent.parent / 'modules'
                        if str(modules_path) not in sys.path:
                            sys.path.insert(0, str(modules_path))

                        from speech2text import SpeechToText
                        self.stt = SpeechToText()
                        logger.info("Speech-to-Text module loaded and enabled for GUI")
                    except Exception as e:
                        logger.warning(f"Failed to load speech2text module: {e}")
                    break
        except Exception as e:
            logger.warning(f"Failed to load module registry: {e}")

    def reload_modules(self):
        """
        Reload modules from registry (used when modules are enabled/disabled).

        Returns:
            Tuple of (status_message, tts_checkbox_visible, voice_controls_row_visible, stop_button_visible)
        """
        try:
            # Stop listening mode if active
            self.listening_mode_active = False

            # Clear existing TTS instance if it exists
            if self.tts:
                try:
                    self.tts.stop()
                except Exception:
                    pass
                self.tts = None

            # Clear existing STT instance if it exists
            if self.stt:
                self.stt = None

            # Reload modules using the same logic as initialization
            self._load_modules()

            # Build status message
            active_modules = []
            if self.tts:
                active_modules.append("Text-to-Speech")
            if self.stt:
                active_modules.append("Speech-to-Text")

            if active_modules:
                status_msg = f"✅ Modules reloaded: {', '.join(active_modules)}"
            else:
                status_msg = "⭕ No modules currently enabled"

            # Return UI visibility updates
            return (
                status_msg,
                gr.update(visible=self.tts is not None),  # TTS checkbox
                gr.update(visible=self.stt is not None),  # Voice controls row
                gr.update(visible=False)  # Stop listening button (hide on reload)
            )

        except Exception as e:
            logger.error(f"Error reloading modules: {e}")
            return (
                f"❌ Error reloading modules: {str(e)}",
                gr.update(),  # Keep TTS checkbox as-is
                gr.update(),  # Keep voice controls as-is
                gr.update()   # Keep stop button as-is
            )

    def check_server_on_startup(self) -> Tuple[bool, str]:
        """
        Check if server needs to be started on GUI launch (like llf chat).

        Returns:
            Tuple of (needs_start, message) where:
            - needs_start: True if server prompt should be shown
            - message: Status message to display
        """
        # Skip if using external API
        if self.config.is_using_external_api():
            logger.info("Using external API, no local server needed")
            return False, f"Using external API: {self.config.api_base_url}"

        # Check if local server is configured
        if not self.config.has_local_server_config():
            logger.warning("Local LLM server not configured")
            return False, "⚠️ Local LLM server not configured. Using external API or configure local server."

        # Check if the active server is running (multi-server aware)
        is_running = False
        if self.config.default_local_server:
            # Multi-server mode: Check if the active server is running
            is_running = self.runtime.is_server_running_by_name(self.config.default_local_server)
        else:
            # Legacy mode: Check if default server is running
            is_running = self.runtime.is_server_running()

        if is_running:
            logger.info("Server is already running")
            return False, "✅ Server is running"

        # Server is not running - needs user action
        logger.info("Server is not running")
        return True, "❌ Default server is not running. Would you like to start it?"

    def start_server_from_gui(self) -> str:
        """
        Start the LLM server from GUI.

        Returns:
            Status message
        """
        try:
            logger.info("Starting server from GUI...")
            self.runtime.start_server()
            self.started_server = True
            return "✅ Server started successfully!"
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return f"❌ Failed to start server: {str(e)}"

    # ===== Chat Tab Functions =====

    def chat_respond(self, message: str, history: List[dict]):
        """
        Process chat message and stream response.

        Args:
            message: User's message
            history: Chat history as list of message dicts with 'role' and 'content'

        Yields:
            Tuple of (empty string to clear input, updated history with streaming content)
        """
        if not message.strip():
            yield "", history
            return

        try:
            # Build conversation history for LLM
            messages = []
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Add current message to history
            messages.append({"role": "user", "content": message})
            history = history + [{"role": "user", "content": message}]

            # Check if tools are available
            tools_available = False
            if self.prompt_config:
                tools = self.prompt_config.get_memory_tools()
                tools_available = tools is not None and len(tools) > 0

            # Determine execution strategy based on configuration
            from llf.operation_detector import detect_operation_type, should_use_dual_pass

            operation_type = detect_operation_type(message)
            use_dual_pass = should_use_dual_pass(
                operation_type,
                self.config.tool_execution_mode,
                tools_available
            )

            response_text = ""

            if use_dual_pass:
                # Dual-pass mode: Stream first for UX, then execute with tools in background
                import threading

                # Pass 1: Streaming response for user (no tools)
                for chunk in self.runtime.chat(messages, stream=True, use_prompt_config=False):
                    response_text += chunk
                    # Update history with partial response
                    current_history = history + [{"role": "assistant", "content": response_text}]
                    yield "", current_history

                # Pass 2: Execute with tools in background (non-streaming)
                # This runs after streaming completes to ensure tool execution happens
                def execute_with_tools():
                    try:
                        # Run the same request with tools enabled
                        self.runtime.chat(messages, stream=False)
                    except Exception as e:
                        logger.warning(f"Background tool execution failed: {e}")

                # Execute in background thread
                tool_thread = threading.Thread(target=execute_with_tools, daemon=True)
                tool_thread.start()

            elif tools_available:
                # Single-pass mode with tools (no streaming, accurate)
                response_text = self.runtime.chat(messages, stream=False)
                # Update history with complete response
                current_history = history + [{"role": "assistant", "content": response_text}]
                yield "", current_history

            else:
                # Streaming mode (no tools available)
                for chunk in self.runtime.chat(messages, stream=True):
                    response_text += chunk
                    # Update history with partial response
                    current_history = history + [{"role": "assistant", "content": response_text}]
                    yield "", current_history

            # If TTS is enabled AND user has it toggled on, handle based on mode
            if self.tts and self.tts_enabled_state and response_text:
                if not self.is_share_mode:
                    # Local mode: Use platform-appropriate TTS backend
                    try:
                        # If STT is also enabled, ensure audio clearance before next input
                        if self.stt:
                            from .tts_stt_utils import wait_for_tts_clearance
                            logger.info("Speaking and waiting for audio clearance...")
                            wait_for_tts_clearance(self.tts, self.stt, response_text)
                            logger.info("Audio cleared, ready for next input")
                        else:
                            # No STT enabled, just speak normally
                            self.tts.speak(response_text)
                    except Exception as e:
                        logger.warning(f"Text-to-Speech error: {e}")
                # Note: Share mode TTS is handled by browser JavaScript (controlled by tts_enabled checkbox)
                # In share mode, browser handles both TTS and STT separately, so no feedback loop

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            # Add error response
            history = history + [{"role": "assistant", "content": error_msg}]
            yield "", history

    def clear_chat(self) -> List:
        """Clear chat history."""
        return []

    def shutdown_gui(self) -> str:
        """
        Shutdown the GUI gracefully.

        Returns:
            Status message
        """
        try:
            logger.info("Shutting down GUI...")
            # Only stop server if it was started by the GUI (not if started with --daemon)
            if self.started_server and self.config.has_local_server_config() and self.runtime.is_server_running():
                self.runtime.stop_server()
                logger.info("Server stopped (was started by GUI)")
            elif self.runtime.is_server_running():
                logger.info("Server left running (was started externally or in daemon mode)")

            # Schedule GUI shutdown
            import os
            import signal
            import threading

            def delayed_shutdown():
                import time
                time.sleep(1)  # Give time for the response to be sent
                os.kill(os.getpid(), signal.SIGINT)

            threading.Thread(target=delayed_shutdown, daemon=True).start()

            return "✅ Shutting down GUI... You can close this window."
        except Exception as e:
            return f"❌ Error during shutdown: {str(e)}"

    # ===== Server Tab Functions =====

    def get_server_status(self) -> str:
        """Get current server status."""
        try:
            if not self.config.has_local_server_config():
                return "❌ Local LLM server not configured\n\n" + \
                       f"Using external API: {self.config.api_base_url}\n" + \
                       f"Model: {self.config.model_name}"

            if self.runtime.is_server_running():
                return f"✅ Server is running\n\n" + \
                       f"URL: {self.config.get_server_url()}\n" + \
                       f"Model: {self.config.model_name}"
            else:
                return "⭕ Server is not running"
        except Exception as e:
            return f"❌ Error checking status: {str(e)}"

    def start_server(self) -> str:
        """Start the LLM server."""
        try:
            if not self.config.has_local_server_config():
                return "❌ Cannot start server: Local LLM server not configured\n\n" + \
                       "Please configure local_llm_server section in config.json"

            if self.runtime.is_server_running():
                return "ℹ️ Server is already running"

            # Check if model is downloaded
            if not self.model_manager.is_model_downloaded(self.config.model_name):
                return f"❌ Model not downloaded: {self.config.model_name}\n\n" + \
                       "Please download the model first in the Models tab"

            # Start server
            self.runtime.start_server()

            # Wait a bit for server to start
            time.sleep(2)

            if self.runtime.is_server_running():
                return f"✅ Server started successfully\n\n" + \
                       f"URL: {self.config.get_server_url()}"
            else:
                return "❌ Server failed to start (check logs for details)"

        except Exception as e:
            return f"❌ Error starting server: {str(e)}"

    def stop_server(self) -> str:
        """Stop the LLM server."""
        try:
            if not self.config.has_local_server_config():
                return "ℹ️ Local LLM server not configured (using external API)"

            if not self.runtime.is_server_running():
                return "ℹ️ Server is not running"

            self.runtime.stop_server()

            # Wait a bit for server to stop
            time.sleep(1)

            if not self.runtime.is_server_running():
                return "✅ Server stopped successfully"
            else:
                return "⚠️ Server may still be running (check status)"

        except Exception as e:
            return f"❌ Error stopping server: {str(e)}"

    def restart_server(self) -> str:
        """Restart the LLM server."""
        try:
            stop_msg = self.stop_server()
            time.sleep(2)
            start_msg = self.start_server()
            return f"Restart sequence:\n\n{stop_msg}\n\n{start_msg}"
        except Exception as e:
            return f"❌ Error restarting server: {str(e)}"

    # ===== Multi-Server Management Functions =====

    def get_available_servers(self) -> List[str]:
        """
        Get list of available server names for radio selection.

        Returns:
            List of server names.
        """
        try:
            servers = self.config.list_servers()
            if not servers:
                return ["No servers configured"]
            return servers
        except Exception as e:
            logger.error(f"Error getting available servers: {e}")
            return ["Error loading servers"]

    def get_server_info(self, server_name: str) -> str:
        """
        Get detailed information about a specific server.

        Args:
            server_name: Name of the server.

        Returns:
            Server information as formatted string.
        """
        try:
            if not server_name or server_name in ["No servers configured", "Error loading servers"]:
                return "No server selected"

            server_config = self.config.get_server_by_name(server_name)
            if not server_config:
                return f"❌ Server '{server_name}' not found in configuration"

            # Check if this is the active server
            is_active = self.config.default_local_server == server_name
            active_marker = " ⭐ ACTIVE" if is_active else ""

            # Check if server is running
            is_running = self.runtime.is_server_running_by_name(server_name)
            status = "🟢 Running" if is_running else "⭕ Stopped"

            # Build info string
            info = f"Server: {server_name}{active_marker}\n"
            info += f"Status: {status}\n"
            info += f"Host: {server_config.server_host}\n"
            info += f"Port: {server_config.server_port}\n"
            info += f"URL: http://{server_config.server_host}:{server_config.server_port}/v1\n"

            if server_config.model_dir:
                try:
                    rel_path = server_config.model_dir.relative_to(self.config.model_dir)
                    info += f"Model Dir: {rel_path}\n"
                except ValueError:
                    info += f"Model Dir: {server_config.model_dir}\n"

            if server_config.gguf_file:
                info += f"GGUF File: {server_config.gguf_file}\n"

            info += f"Auto-start: {'Yes' if server_config.auto_start else 'No'}\n"

            if server_config.server_params:
                info += f"\nServer Parameters:\n"
                for key, value in server_config.server_params.items():
                    info += f"  {key}: {value}\n"

            return info

        except Exception as e:
            return f"❌ Error getting server info: {str(e)}"

    def start_server_by_name(self, server_name: str) -> Tuple[str, str]:
        """
        Start a specific server by name.

        Args:
            server_name: Name of the server to start.

        Returns:
            Tuple of (status message, updated server info).
        """
        try:
            if not server_name or server_name in ["No servers configured", "Error loading servers"]:
                return "❌ No server selected", self.get_server_info(server_name)

            server_config = self.config.get_server_by_name(server_name)
            if not server_config:
                return f"❌ Server '{server_name}' not found in configuration", self.get_server_info(server_name)

            # Check if already running
            if self.runtime.is_server_running_by_name(server_name):
                return f"ℹ️ Server '{server_name}' is already running", self.get_server_info(server_name)

            # Start server (with force=True to skip memory warning in GUI)
            self.runtime.start_server_by_name(server_name, force=True)

            # Wait a bit for server to start
            time.sleep(2)

            # Get updated server info
            updated_info = self.get_server_info(server_name)

            # Verify started
            if self.runtime.is_server_running_by_name(server_name):
                status = f"✅ Server '{server_name}' started successfully\n\n" + \
                       f"URL: http://{server_config.server_host}:{server_config.server_port}/v1"
            else:
                status = f"❌ Server '{server_name}' failed to start (check logs for details)"

            return status, updated_info

        except Exception as e:
            return f"❌ Error starting server: {str(e)}", self.get_server_info(server_name)

    def stop_server_by_name(self, server_name: str) -> Tuple[str, str]:
        """
        Stop a specific server by name.

        Args:
            server_name: Name of the server to stop.

        Returns:
            Tuple of (status message, updated server info).
        """
        try:
            if not server_name or server_name in ["No servers configured", "Error loading servers"]:
                return "❌ No server selected", self.get_server_info(server_name)

            server_config = self.config.get_server_by_name(server_name)
            if not server_config:
                return f"❌ Server '{server_name}' not found in configuration", self.get_server_info(server_name)

            # Check if running
            if not self.runtime.is_server_running_by_name(server_name):
                return f"ℹ️ Server '{server_name}' is not running", self.get_server_info(server_name)

            # Stop server
            self.runtime.stop_server_by_name(server_name)

            # Wait a bit for server to stop
            time.sleep(1)

            # Get updated server info
            updated_info = self.get_server_info(server_name)

            # Verify stopped
            if not self.runtime.is_server_running_by_name(server_name):
                status = f"✅ Server '{server_name}' stopped successfully"
            else:
                status = f"⚠️ Server '{server_name}' may still be running (check status)"

            return status, updated_info

        except Exception as e:
            return f"❌ Error stopping server: {str(e)}", self.get_server_info(server_name)

    def restart_server_by_name(self, server_name: str) -> Tuple[str, str]:
        """
        Restart a specific server by name.

        Args:
            server_name: Name of the server to restart.

        Returns:
            Tuple of (status message, updated server info).
        """
        try:
            if not server_name or server_name in ["No servers configured", "Error loading servers"]:
                return "❌ No server selected", self.get_server_info(server_name)

            stop_msg, _ = self.stop_server_by_name(server_name)
            time.sleep(2)
            start_msg, updated_info = self.start_server_by_name(server_name)

            status = f"Restart sequence:\n\n{stop_msg}\n\n{start_msg}"
            return status, updated_info

        except Exception as e:
            return f"❌ Error restarting server: {str(e)}", self.get_server_info(server_name)

    # ===== Models Tab Functions =====

    def list_models(self) -> str:
        """List downloaded models."""
        try:
            models = self.model_manager.list_downloaded_models()

            if not models:
                return "No models downloaded yet.\n\nUse the download section below to get started."

            output = "📦 Downloaded Models:\n\n"
            for i, model in enumerate(models, 1):
                output += f"{i}. {model}\n"

            return output
        except Exception as e:
            return f"❌ Error listing models: {str(e)}"

    def list_models_for_radio(self) -> List[str]:
        """List downloaded models as a list for Radio component."""
        try:
            models = self.model_manager.list_downloaded_models()
            # Always include "Default" as the first option
            return ["Default"] + models
        except Exception as e:
            return ["Default"]

    def get_selected_model_info(self, selected_model: str) -> str:
        """Get information about the selected model from radio."""
        try:
            if not selected_model:
                return ""

            # If "Default" is selected, get info for the default model
            if selected_model == "Default":
                model_name = self.config.model_name
            else:
                model_name = selected_model

            return self.get_model_info(model_name)
        except Exception as e:
            return f"❌ Error getting model info: {str(e)}"

    def refresh_models_list(self) -> Tuple[gr.Radio, str]:
        """Refresh the models list and return updated Radio component."""
        try:
            models = self.list_models_for_radio()
            # Return updated radio choices and reset info
            return gr.Radio(choices=models, value="Default"), self.get_selected_model_info("Default")
        except Exception as e:
            return gr.Radio(choices=["Default"], value="Default"), f"❌ Error refreshing models: {str(e)}"

    def download_model(self, download_type: str, model_name: str, url: str, custom_name: str):
        """
        Download a model with progress updates.

        Args:
            download_type: Type of download ("HuggingFace" or "URL")
            model_name: HuggingFace model name (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
            url: Direct URL to GGUF file (alternative to model_name)
            custom_name: Custom name for URL-downloaded model

        Yields:
            Status messages during download
        """
        try:
            if download_type == "URL":
                # URL download
                if not url or not url.strip():
                    yield "❌ Please provide a URL"
                    return
                if not custom_name or not custom_name.strip():
                    yield "❌ Please provide a custom name for URL downloads"
                    return

                yield f"📥 Model is downloading from URL... ⏳\n\n{DOWNLOAD_PROGRESS_MESSAGE}"

                self.model_manager.download_from_url(
                    url=url.strip(),
                    name=custom_name.strip()
                )
                yield f"✅ Model downloaded successfully from URL! 🎉\n\nSaved as: {custom_name}"

            else:  # HuggingFace
                if not model_name or not model_name.strip():
                    yield "❌ Please provide a HuggingFace model name"
                    return

                yield f"📥 Model is downloading from HuggingFace... ⏳\n\n{DOWNLOAD_PROGRESS_MESSAGE}\n\nModel: {model_name.strip()}"

                # HuggingFace download
                self.model_manager.download_model(
                    model_name=model_name.strip(),
                    force=False
                )
                yield f"✅ Model downloaded successfully! 🎉\n\nModel: {model_name.strip()}"

        except Exception as e:
            yield f"❌ Error downloading model: {str(e)}"

    def get_model_info(self, model_name: str) -> str:
        """Get information about a model."""
        try:
            if not model_name or not model_name.strip():
                model_name = self.config.model_name

            info = self.model_manager.get_model_info(model_name.strip())

            if not info:
                return f"❌ Model not found: {model_name}"

            output = f"📊 Model Information: {model_name}\n\n"
            output += f"Downloaded: {'✅ Yes' if info.get('downloaded', False) else '❌ No'}\n"

            if info.get('path'):
                output += f"Path: {info['path']}\n"

            if info.get('size'):
                output += f"Size: {info['size']}\n"

            if info.get('files'):
                output += f"\nFiles:\n"
                for f in info['files'][:10]:  # Show first 10 files
                    output += f"  - {f}\n"
                if len(info['files']) > 10:
                    output += f"  ... and {len(info['files']) - 10} more\n"

            return output
        except Exception as e:
            return f"❌ Error getting model info: {str(e)}"

    # ===== Config Tab Functions =====

    def backup_config(self) -> str:
        """Create a backup of config.json."""
        try:
            backup_path = self.config.backup_config()
            return f"✅ Backup created successfully:\n{backup_path.name}"
        except FileNotFoundError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"❌ Error creating backup: {str(e)}"

    def backup_prompt_config(self) -> str:
        """Create a backup of config_prompt.json."""
        try:
            backup_path = self.prompt_config.backup_config()
            return f"✅ Backup created successfully:\n{backup_path.name}"
        except FileNotFoundError as e:
            return f"❌ {str(e)}"
        except Exception as e:
            return f"❌ Error creating backup: {str(e)}"

    def load_config(self) -> str:
        """Load config.json content."""
        try:
            config_file = Config.DEFAULT_CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    content = f.read()
                return content
            else:
                return "# config.json not found\n# Create one to get started"
        except Exception as e:
            return f"# Error loading config.json: {str(e)}"

    def save_config(self, content: str) -> str:
        """Save config.json content (validates JSON before saving)."""
        try:
            # Validate and parse JSON first
            config_data = json.loads(content)

            # Save file with pretty formatting (indent=2)
            config_file = Config.DEFAULT_CONFIG_FILE
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Reload config
            self.config = get_config(force_reload=True)
            self.model_manager = ModelManager(self.config)
            self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)

            return "✅ config.json saved and reloaded successfully"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"
        except Exception as e:
            return f"❌ Error saving config.json: {str(e)}"

    def load_prompt_config(self) -> str:
        """Load config_prompt.json content."""
        try:
            config_file = PromptConfig.DEFAULT_CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    content = f.read()
                return content
            else:
                return "# config_prompt.json not found\n# Create one to customize prompts"
        except Exception as e:
            return f"# Error loading config_prompt.json: {str(e)}"

    def save_prompt_config(self, content: str) -> str:
        """Save config_prompt.json content (validates JSON before saving)."""
        try:
            # Validate and parse JSON first
            config_data = json.loads(content)

            # Save file with pretty formatting (indent=2)
            config_file = PromptConfig.DEFAULT_CONFIG_FILE
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Reload prompt config
            self.prompt_config = get_prompt_config(force_reload=True)
            self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)

            return "✅ config_prompt.json saved and reloaded successfully"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"
        except Exception as e:
            return f"❌ Error saving config_prompt.json: {str(e)}"

    def reload_config_with_status(self) -> Tuple[str, str]:
        """Reload config.json and return both content and status message."""
        try:
            config_file = Config.DEFAULT_CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    content = f.read()
                return content, "✅ Successfully reloaded config.json"
            else:
                return "# config.json not found\n# Create one to get started", "❌ config.json not found"
        except Exception as e:
            return f"# Error loading config.json: {str(e)}", f"❌ Error reloading config.json: {str(e)}"

    def reload_prompt_config_with_status(self) -> Tuple[str, str]:
        """Reload config_prompt.json and return both content and status message."""
        try:
            config_file = PromptConfig.DEFAULT_CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    content = f.read()
                return content, "✅ Successfully reloaded config_prompt.json"
            else:
                return "# config_prompt.json not found\n# Create one to customize prompts", "❌ config_prompt.json not found"
        except Exception as e:
            return f"# Error loading config_prompt.json: {str(e)}", f"❌ Error reloading config_prompt.json: {str(e)}"

    @staticmethod
    def toggle_download_sections(choice: str) -> Tuple[dict, dict]:
        """
        Toggle visibility of download sections based on selected method.

        Args:
            choice: Download method ("HuggingFace" or "URL")

        Returns:
            Tuple of (hf_section_update, url_section_update)
        """
        if choice == "HuggingFace":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)

    # ===== Module Management Functions =====

    def get_available_modules(self) -> List[str]:
        """List available modules for Radio component."""
        try:
            modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

            if not modules_registry_path.exists():
                return []

            with open(modules_registry_path, 'r') as f:
                registry = json.load(f)

            modules = registry.get('modules', [])
            return [m.get('display_name', m.get('name', 'Unknown')) for m in modules]
        except Exception as e:
            logger.error(f"Error listing modules: {e}")
            return []

    def get_module_info(self, selected_module: str) -> str:
        """Get detailed information about the selected module."""
        try:
            if not selected_module:
                return "Select a module to view its details"

            modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

            if not modules_registry_path.exists():
                return "❌ Modules registry not found"

            with open(modules_registry_path, 'r') as f:
                registry = json.load(f)

            modules = registry.get('modules', [])

            # Find module by display name or name
            module = None
            for m in modules:
                if m.get('display_name') == selected_module or m.get('name') == selected_module:
                    module = m
                    break

            if not module:
                return f"❌ Module '{selected_module}' not found"

            # Build info display
            name = module.get('name', 'unknown')
            display_name = module.get('display_name', name)
            description = module.get('description', 'No description')
            enabled = module.get('enabled', False)
            version = module.get('version', '0.0.0')
            module_type = module.get('type', 'unknown')
            directory = module.get('directory', name)
            dependencies = module.get('dependencies', [])

            status = "✅ Enabled" if enabled else "⭕ Disabled"
            module_path = Path(__file__).parent.parent / 'modules' / directory

            info = f"""**{display_name}** ({name}) v{version}

**Status:** {status}
**Type:** {module_type}
**Description:** {description}
**Location:** {module_path}

**Dependencies:**
"""
            if dependencies:
                for dep in dependencies:
                    info += f"  • {dep}\n"
            else:
                info += "  • None\n"

            return info

        except Exception as e:
            return f"❌ Error getting module info: {str(e)}"

    def enable_module(self, selected_module: str) -> Tuple[str, str]:
        """Enable the selected module."""
        try:
            if not selected_module:
                return "Please select a module first", self.get_module_info(selected_module)

            modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

            with open(modules_registry_path, 'r') as f:
                registry = json.load(f)

            modules = registry.get('modules', [])

            # Find and enable module
            module_found = False
            for module in modules:
                if module.get('display_name') == selected_module or module.get('name') == selected_module:
                    if module.get('enabled', False):
                        return f"⚠️ Module '{selected_module}' is already enabled", self.get_module_info(selected_module)
                    else:
                        module['enabled'] = True
                        module_found = True
                        break

            if not module_found:
                return f"❌ Module '{selected_module}' not found", self.get_module_info(selected_module)

            # Write back to registry
            with open(modules_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            # Reload modules to apply changes immediately
            reload_status = self.reload_modules()

            return f"✅ Module '{selected_module}' enabled successfully\n{reload_status}", self.get_module_info(selected_module)

        except Exception as e:
            return f"❌ Error enabling module: {str(e)}", self.get_module_info(selected_module)

    def disable_module(self, selected_module: str) -> Tuple[str, str]:
        """Disable the selected module."""
        try:
            if not selected_module:
                return "Please select a module first", self.get_module_info(selected_module)

            modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

            with open(modules_registry_path, 'r') as f:
                registry = json.load(f)

            modules = registry.get('modules', [])

            # Find and disable module
            module_found = False
            for module in modules:
                if module.get('display_name') == selected_module or module.get('name') == selected_module:
                    if not module.get('enabled', False):
                        return f"⚠️ Module '{selected_module}' is already disabled", self.get_module_info(selected_module)
                    else:
                        module['enabled'] = False
                        module_found = True
                        break

            if not module_found:
                return f"❌ Module '{selected_module}' not found", self.get_module_info(selected_module)

            # Write back to registry
            with open(modules_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            # Reload modules to apply changes immediately
            reload_status = self.reload_modules()

            return f"✅ Module '{selected_module}' disabled successfully\n{reload_status}", self.get_module_info(selected_module)

        except Exception as e:
            return f"❌ Error disabling module: {str(e)}", self.get_module_info(selected_module)

    # ===== Data Store Management Methods =====

    def get_available_datastores(self) -> List[str]:
        """List available data stores for Radio component."""
        try:
            datastore_registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'

            if not datastore_registry_path.exists():
                return []

            with open(datastore_registry_path, 'r') as f:
                registry = json.load(f)

            data_stores = registry.get('data_stores', [])
            return [ds.get('display_name', ds.get('name', 'Unknown')) for ds in data_stores]
        except Exception as e:
            logger.error(f"Error listing data stores: {e}")
            return []

    def get_datastore_info(self, selected_datastore: str) -> str:
        """Get detailed information about the selected data store."""
        try:
            if not selected_datastore:
                return "Select a data store to view its details"

            datastore_registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'

            if not datastore_registry_path.exists():
                return "❌ Data store registry not found"

            with open(datastore_registry_path, 'r') as f:
                registry = json.load(f)

            data_stores = registry.get('data_stores', [])

            # Find data store by display name or name
            datastore = None
            for ds in data_stores:
                if ds.get('display_name') == selected_datastore or ds.get('name') == selected_datastore:
                    datastore = ds
                    break

            if not datastore:
                return f"❌ Data store '{selected_datastore}' not found"

            # Build info display
            name = datastore.get('name', 'unknown')
            display_name = datastore.get('display_name', name)
            description = datastore.get('description', 'No description')
            attached = datastore.get('attached', False)
            vector_store_path_rel = datastore.get('vector_store_path', 'N/A')
            embedding_model = datastore.get('embedding_model', 'N/A')
            num_vectors = datastore.get('num_vectors', 0)
            embedding_dimension = datastore.get('embedding_dimension', 'N/A')
            index_type = datastore.get('index_type', 'N/A')

            # Calculate full path
            if vector_store_path_rel != 'N/A':
                vector_store_path_obj = Path(vector_store_path_rel)
                if vector_store_path_obj.is_absolute():
                    vector_store_path = str(vector_store_path_obj.resolve())
                else:
                    vector_store_path = str((Path(__file__).parent.parent / vector_store_path_rel).resolve())
            else:
                vector_store_path = 'N/A'

            status = "✅ Attached" if attached else "⭕ Detached"

            info = f"""**{display_name}** ({name})

**Status:** {status}
**Description:** {description}
**Location:** {vector_store_path}
**Number of Vectors:** {num_vectors}

**Configuration:**
  • Embedding Model: {embedding_model}
  • Embedding Dimension: {embedding_dimension}
  • Index Type: {index_type}
"""
            return info

        except Exception as e:
            return f"❌ Error getting data store info: {str(e)}"

    def attach_datastore(self, selected_datastore: str) -> Tuple[str, str]:
        """Attach the selected data store."""
        try:
            if not selected_datastore:
                return "Please select a data store first", self.get_datastore_info(selected_datastore)

            datastore_registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'

            with open(datastore_registry_path, 'r') as f:
                registry = json.load(f)

            data_stores = registry.get('data_stores', [])

            # Find and attach data store
            datastore_found = False
            for datastore in data_stores:
                if datastore.get('display_name') == selected_datastore or datastore.get('name') == selected_datastore:
                    if datastore.get('attached', False):
                        return f"⚠️ Data store '{selected_datastore}' is already attached", self.get_datastore_info(selected_datastore)
                    else:
                        datastore['attached'] = True
                        datastore_found = True
                        break

            if not datastore_found:
                return f"❌ Data store '{selected_datastore}' not found", self.get_datastore_info(selected_datastore)

            # Write back to registry
            with open(datastore_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Data store '{selected_datastore}' attached successfully", self.get_datastore_info(selected_datastore)

        except Exception as e:
            return f"❌ Error attaching data store: {str(e)}", self.get_datastore_info(selected_datastore)

    def detach_datastore(self, selected_datastore: str) -> Tuple[str, str]:
        """Detach the selected data store."""
        try:
            if not selected_datastore:
                return "Please select a data store first", self.get_datastore_info(selected_datastore)

            datastore_registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'

            with open(datastore_registry_path, 'r') as f:
                registry = json.load(f)

            data_stores = registry.get('data_stores', [])

            # Find and detach data store
            datastore_found = False
            for datastore in data_stores:
                if datastore.get('display_name') == selected_datastore or datastore.get('name') == selected_datastore:
                    if not datastore.get('attached', False):
                        return f"⚠️ Data store '{selected_datastore}' is already detached", self.get_datastore_info(selected_datastore)
                    else:
                        datastore['attached'] = False
                        datastore_found = True
                        break

            if not datastore_found:
                return f"❌ Data store '{selected_datastore}' not found", self.get_datastore_info(selected_datastore)

            # Write back to registry
            with open(datastore_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Data store '{selected_datastore}' detached successfully", self.get_datastore_info(selected_datastore)

        except Exception as e:
            return f"❌ Error detaching data store: {str(e)}", self.get_datastore_info(selected_datastore)

    # ===== Memory Management Methods =====

    def get_available_memories(self) -> list:
        """
        Get list of available memory instances.

        Returns:
            List of memory display names
        """
        try:
            memory_registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'

            if not memory_registry_path.exists():
                return []

            with open(memory_registry_path, 'r') as f:
                registry = json.load(f)

            memories = registry.get('memories', [])
            return [mem.get('display_name', mem.get('name', 'Unknown')) for mem in memories]

        except Exception as e:
            logger.error(f"Error getting available memories: {e}")
            return []

    def get_memory_info(self, selected_memory: str) -> str:
        """
        Get information about a specific memory instance.

        Args:
            selected_memory: Display name of the memory

        Returns:
            Formatted string with memory information
        """
        if not selected_memory:
            return "No memory selected"

        try:
            memory_registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'

            if not memory_registry_path.exists():
                return "❌ Memory registry not found"

            with open(memory_registry_path, 'r') as f:
                registry = json.load(f)

            # Find the memory by display_name or name
            memory = None
            for mem in registry.get('memories', []):
                if mem.get('display_name') == selected_memory or mem.get('name') == selected_memory:
                    memory = mem
                    break

            if not memory:
                return f"❌ Memory '{selected_memory}' not found"

            # Build info string
            name = memory.get('name', 'Unknown')
            display_name = memory.get('display_name', name)
            description = memory.get('description', 'No description available')
            enabled = memory.get('enabled', False)
            status = "🟢 Enabled" if enabled else "⭕ Disabled"
            mem_type = memory.get('type', 'Unknown')
            directory = memory.get('directory', 'Not specified')
            created_date = memory.get('created_date', 'N/A')
            last_modified = memory.get('last_modified', 'N/A')

            info = f"""**Memory: {display_name}**

**Status:** {status}

**Description:** {description}

**Details:**
- Name: {name}
- Type: {mem_type}
- Directory: {directory}
- Created: {created_date}
- Last Modified: {last_modified}
"""

            # Add metadata if available
            metadata = memory.get('metadata', {})
            if metadata:
                info += "\n**Metadata:**\n"
                for key, value in metadata.items():
                    info += f"- {key}: {value}\n"

            return info

        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return f"❌ Error getting memory info: {str(e)}"

    def enable_memory(self, selected_memory: str) -> tuple:
        """
        Enable a memory instance.

        Args:
            selected_memory: Display name of the memory to enable

        Returns:
            Tuple of (status_message, updated_info)
        """
        if not selected_memory:
            return "⚠️ No memory selected", ""

        try:
            memory_registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'

            if not memory_registry_path.exists():
                return "❌ Memory registry not found", self.get_memory_info(selected_memory)

            with open(memory_registry_path, 'r') as f:
                registry = json.load(f)

            # Find and enable the memory
            memory_found = False
            for mem in registry.get('memories', []):
                if mem.get('display_name') == selected_memory or mem.get('name') == selected_memory:
                    if mem.get('enabled', False):
                        return f"⚠️ Memory '{selected_memory}' is already enabled", self.get_memory_info(selected_memory)
                    mem['enabled'] = True
                    memory_found = True
                    break

            if not memory_found:
                return f"❌ Memory '{selected_memory}' not found", self.get_memory_info(selected_memory)

            # Update last_updated timestamp
            from datetime import datetime
            registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Write back to registry
            with open(memory_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Memory '{selected_memory}' enabled successfully", self.get_memory_info(selected_memory)

        except Exception as e:
            return f"❌ Error enabling memory: {str(e)}", self.get_memory_info(selected_memory)

    def disable_memory(self, selected_memory: str) -> tuple:
        """
        Disable a memory instance.

        Args:
            selected_memory: Display name of the memory to disable

        Returns:
            Tuple of (status_message, updated_info)
        """
        if not selected_memory:
            return "⚠️ No memory selected", ""

        try:
            memory_registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'

            if not memory_registry_path.exists():
                return "❌ Memory registry not found", self.get_memory_info(selected_memory)

            with open(memory_registry_path, 'r') as f:
                registry = json.load(f)

            # Find and disable the memory
            memory_found = False
            for mem in registry.get('memories', []):
                if mem.get('display_name') == selected_memory or mem.get('name') == selected_memory:
                    if not mem.get('enabled', False):
                        return f"⚠️ Memory '{selected_memory}' is already disabled", self.get_memory_info(selected_memory)
                    mem['enabled'] = False
                    memory_found = True
                    break

            if not memory_found:
                return f"❌ Memory '{selected_memory}' not found", self.get_memory_info(selected_memory)

            # Update last_updated timestamp
            from datetime import datetime
            registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Write back to registry
            with open(memory_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Memory '{selected_memory}' disabled successfully", self.get_memory_info(selected_memory)

        except Exception as e:
            return f"❌ Error disabling memory: {str(e)}", self.get_memory_info(selected_memory)

    # ===== Tool Management Methods =====

    def get_available_tools(self) -> List[str]:
        """
        Get list of available tools from registry.

        Returns:
            List of tool display names
        """
        try:
            tools_registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'

            if not tools_registry_path.exists():
                return []

            with open(tools_registry_path, 'r') as f:
                registry = json.load(f)

            tools = registry.get('tools', [])
            return [tool.get('display_name', tool.get('name', 'Unknown')) for tool in tools]

        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return []

    def get_tool_info(self, selected_tool: str) -> str:
        """
        Get information about a specific tool.

        Args:
            selected_tool: Display name of the tool

        Returns:
            Formatted string with tool information
        """
        if not selected_tool:
            return "No tool selected"

        try:
            tools_registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'

            if not tools_registry_path.exists():
                return "❌ Tools registry not found"

            with open(tools_registry_path, 'r') as f:
                registry = json.load(f)

            # Find the tool by display_name or name
            tool = None
            for t in registry.get('tools', []):
                if t.get('display_name') == selected_tool or t.get('name') == selected_tool:
                    tool = t
                    break

            if not tool:
                return f"❌ Tool '{selected_tool}' not found"

            # Build info string
            name = tool.get('name', 'Unknown')
            display_name = tool.get('display_name', name)
            description = tool.get('description', 'No description available')
            enabled = tool.get('enabled', False)

            # Handle three-state status
            if enabled == 'auto':
                status = "🟡 Auto"
            elif enabled in [True, 'true']:
                status = "🟢 Enabled"
            else:
                status = "⭕ Disabled"

            tool_type = tool.get('type', 'Unknown')
            directory = tool.get('directory', 'Not specified')
            created_date = tool.get('created_date', 'N/A')
            last_modified = tool.get('last_modified', 'N/A')

            info = f"""**Tool: {display_name}**

**Status:** {status}

**Description:** {description}

**Details:**
- Name: {name}
- Type: {tool_type}
- Directory: {directory}
- Created: {created_date}
- Last Modified: {last_modified}
"""

            # Add metadata if available
            metadata = tool.get('metadata', {})
            if metadata:
                info += "\n**Metadata:**\n"
                for key, value in metadata.items():
                    info += f"- {key}: {value}\n"

            return info

        except Exception as e:
            logger.error(f"Error getting tool info: {e}")
            return f"❌ Error getting tool info: {str(e)}"

    def enable_tool(self, selected_tool: str) -> tuple:
        """
        Enable a tool.

        Args:
            selected_tool: Display name of the tool to enable

        Returns:
            Tuple of (status_message, updated_info)
        """
        if not selected_tool:
            return "⚠️ No tool selected", ""

        try:
            tools_registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'

            if not tools_registry_path.exists():
                return "❌ Tools registry not found", self.get_tool_info(selected_tool)

            with open(tools_registry_path, 'r') as f:
                registry = json.load(f)

            # Find and enable the tool
            tool_found = False
            for tool in registry.get('tools', []):
                if tool.get('display_name') == selected_tool or tool.get('name') == selected_tool:
                    # Check supported states
                    supported_states = tool.get('metadata', {}).get('supported_states', [])
                    if supported_states:
                        # Normalize supported states for comparison
                        normalized_supported = []
                        for state in supported_states:
                            if state is False or state == 'false':
                                normalized_supported.append('false')
                            elif state is True or state == 'true':
                                normalized_supported.append('true')
                            elif state == 'auto':
                                normalized_supported.append('auto')

                        # Check if 'true' is supported
                        if 'true' not in normalized_supported:
                            states_str = ', '.join(normalized_supported)
                            return f"❌ Tool '{selected_tool}' does not support enabled state: true\n\nSupported states: {states_str}", self.get_tool_info(selected_tool)

                    if tool.get('enabled', False) is True:
                        return f"⚠️ Tool '{selected_tool}' is already enabled", self.get_tool_info(selected_tool)
                    tool['enabled'] = True
                    from datetime import datetime
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                return f"❌ Tool '{selected_tool}' not found", self.get_tool_info(selected_tool)

            # Update last_updated timestamp
            from datetime import datetime
            registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Write back to registry
            with open(tools_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Tool '{selected_tool}' enabled successfully", self.get_tool_info(selected_tool)

        except Exception as e:
            return f"❌ Error enabling tool: {str(e)}", self.get_tool_info(selected_tool)

    def auto_tool(self, selected_tool: str) -> tuple:
        """
        Set a tool to 'auto' mode (load at init, use when needed).

        Args:
            selected_tool: Display name of the tool to set to auto

        Returns:
            Tuple of (status_message, updated_info)
        """
        if not selected_tool:
            return "⚠️ No tool selected", ""

        try:
            tools_registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'

            if not tools_registry_path.exists():
                return "❌ Tools registry not found", self.get_tool_info(selected_tool)

            with open(tools_registry_path, 'r') as f:
                registry = json.load(f)

            # Find and set tool to auto
            tool_found = False
            for tool in registry.get('tools', []):
                if tool.get('display_name') == selected_tool or tool.get('name') == selected_tool:
                    # Check supported states
                    supported_states = tool.get('metadata', {}).get('supported_states', [])
                    if supported_states:
                        # Normalize supported states for comparison
                        normalized_supported = []
                        for state in supported_states:
                            if state is False or state == 'false':
                                normalized_supported.append('false')
                            elif state is True or state == 'true':
                                normalized_supported.append('true')
                            elif state == 'auto':
                                normalized_supported.append('auto')

                        # Check if 'auto' is supported
                        if 'auto' not in normalized_supported:
                            states_str = ', '.join(normalized_supported)
                            return f"❌ Tool '{selected_tool}' does not support enabled state: auto\n\nSupported states: {states_str}", self.get_tool_info(selected_tool)

                    if tool.get('enabled') == 'auto':
                        return f"⚠️ Tool '{selected_tool}' is already set to auto", self.get_tool_info(selected_tool)
                    tool['enabled'] = 'auto'
                    from datetime import datetime
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                return f"❌ Tool '{selected_tool}' not found", self.get_tool_info(selected_tool)

            # Update last_updated timestamp
            from datetime import datetime
            registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Write back to registry
            with open(tools_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Tool '{selected_tool}' set to auto mode", self.get_tool_info(selected_tool)

        except Exception as e:
            return f"❌ Error setting tool to auto: {str(e)}", self.get_tool_info(selected_tool)

    def disable_tool(self, selected_tool: str) -> tuple:
        """
        Disable a tool.

        Args:
            selected_tool: Display name of the tool to disable

        Returns:
            Tuple of (status_message, updated_info)
        """
        if not selected_tool:
            return "⚠️ No tool selected", ""

        try:
            tools_registry_path = Path(__file__).parent.parent / 'tools' / 'tools_registry.json'

            if not tools_registry_path.exists():
                return "❌ Tools registry not found", self.get_tool_info(selected_tool)

            with open(tools_registry_path, 'r') as f:
                registry = json.load(f)

            # Find and disable the tool
            tool_found = False
            for tool in registry.get('tools', []):
                if tool.get('display_name') == selected_tool or tool.get('name') == selected_tool:
                    # Check supported states
                    supported_states = tool.get('metadata', {}).get('supported_states', [])
                    if supported_states:
                        # Normalize supported states for comparison
                        normalized_supported = []
                        for state in supported_states:
                            if state is False or state == 'false':
                                normalized_supported.append('false')
                            elif state is True or state == 'true':
                                normalized_supported.append('true')
                            elif state == 'auto':
                                normalized_supported.append('auto')

                        # Check if 'false' is supported
                        if 'false' not in normalized_supported:
                            states_str = ', '.join(normalized_supported)
                            return f"❌ Tool '{selected_tool}' does not support enabled state: false\n\nSupported states: {states_str}", self.get_tool_info(selected_tool)

                    if not tool.get('enabled', False):
                        return f"⚠️ Tool '{selected_tool}' is already disabled", self.get_tool_info(selected_tool)
                    tool['enabled'] = False
                    from datetime import datetime
                    tool['last_modified'] = datetime.now().strftime('%Y-%m-%d')
                    tool_found = True
                    break

            if not tool_found:
                return f"❌ Tool '{selected_tool}' not found", self.get_tool_info(selected_tool)

            # Update last_updated timestamp
            from datetime import datetime
            registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Write back to registry
            with open(tools_registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return f"✅ Tool '{selected_tool}' disabled successfully", self.get_tool_info(selected_tool)

        except Exception as e:
            return f"❌ Error disabling tool: {str(e)}", self.get_tool_info(selected_tool)

    def enable_tool_with_restart_check(self, selected_tool: str) -> tuple:
        """
        Enable tool and show restart dialog if using local LLM.

        Returns:
            Tuple of (status_message, updated_info, dialog_visibility_update, pending_change)
        """
        # Call the regular enable method
        status, info = self.enable_tool(selected_tool)

        # Check if we need to show restart dialog (local LLM and successful change)
        if not self.config.is_using_external_api() and "✅" in status:
            # Show the restart dialog
            return status, info, gr.update(visible=True), {"action": "enable", "tool": selected_tool}
        else:
            # Don't show dialog (external API or error occurred)
            return status, info, gr.update(visible=False), None

    def auto_tool_with_restart_check(self, selected_tool: str) -> tuple:
        """
        Set tool to auto and show restart dialog if using local LLM.

        Returns:
            Tuple of (status_message, updated_info, dialog_visibility_update, pending_change)
        """
        # Call the regular auto method
        status, info = self.auto_tool(selected_tool)

        # Check if we need to show restart dialog (local LLM and successful change)
        if not self.config.is_using_external_api() and "✅" in status:
            # Show the restart dialog
            return status, info, gr.update(visible=True), {"action": "auto", "tool": selected_tool}
        else:
            # Don't show dialog (external API or error occurred)
            return status, info, gr.update(visible=False), None

    def disable_tool_with_restart_check(self, selected_tool: str) -> tuple:
        """
        Disable tool and show restart dialog if using local LLM.

        Returns:
            Tuple of (status_message, updated_info, dialog_visibility_update, pending_change)
        """
        # Call the regular disable method
        status, info = self.disable_tool(selected_tool)

        # Check if we need to show restart dialog (local LLM and successful change)
        if not self.config.is_using_external_api() and "✅" in status:
            # Show the restart dialog
            return status, info, gr.update(visible=True), {"action": "disable", "tool": selected_tool}
        else:
            # Don't show dialog (external API or error occurred)
            return status, info, gr.update(visible=False), None

    def handle_tool_restart_yes(self) -> tuple:
        """
        Handle 'Yes' button click on restart dialog - restart the server.

        Returns:
            Tuple of (dialog_visibility_update, status_message)
        """
        try:
            # Get the active server name
            server_name = self.config.default_local_server if self.config.default_local_server else None

            if not server_name:
                # Legacy single-server mode - just restart default server
                stop_msg, _ = self.stop_server()
                time.sleep(2)
                start_msg, _ = self.start_server()
                status = f"Server restarted:\n{stop_msg}\n{start_msg}"
            else:
                # Multi-server mode - restart the active server
                stop_msg, _ = self.stop_server_by_name(server_name)
                time.sleep(2)
                start_msg, _ = self.start_server_by_name(server_name)
                status = f"Server '{server_name}' restarted:\n{stop_msg}\n{start_msg}"

            # Hide the dialog and show restart status
            return gr.update(visible=False), status

        except Exception as e:
            return gr.update(visible=False), f"❌ Error restarting server: {str(e)}"

    # ===== Main Interface Builder =====

    def create_interface(self) -> gr.Blocks:
        """
        Create and return the Gradio interface.

        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(title="LLM Framework GUI") as interface:

            # Authentication state - True if no auth required or successfully authenticated
            auth_state = gr.State(True if not self.auth_key else False)

            # Login UI (visible only when authentication is required and not authenticated)
            with gr.Group(visible=bool(self.auth_key)) as login_ui:
                gr.Markdown("# 🔒 Authentication Required")
                gr.Markdown("Please enter the secret key to access the LLM Framework GUI")
                with gr.Row():
                    with gr.Column(scale=3):
                        key_input = gr.Textbox(
                            label="Secret Key",
                            type="password",
                            placeholder="Enter your secret key...",
                            scale=4
                        )
                    with gr.Column(scale=1):
                        login_btn = gr.Button("Login", variant="primary", scale=1)
                login_status = gr.Textbox(label="Status", interactive=False, visible=False)

            # Main UI (visible only when authenticated)
            with gr.Group(visible=not bool(self.auth_key)) as main_ui:

                with gr.Row():
                    with gr.Column(scale=5):
                        gr.Markdown("# 🤖 Local LLM Framework")
                        gr.Markdown("Web interface for managing and chatting with local LLMs")
                    with gr.Column(scale=1, min_width=150):
                        shutdown_btn = gr.Button("🔴 Shutdown GUI", variant="stop", size="sm")
                    shutdown_status = gr.Textbox(
                        label="",
                        lines=1,
                        interactive=False,
                        visible=False,
                        container=False
                    )

                # Shutdown handler
                shutdown_btn.click(self.shutdown_gui, None, shutdown_status).then(
                    lambda: gr.update(visible=True), None, shutdown_status
                )

                # Server startup prompt (shown on load if server not running)
                needs_start, startup_msg = self.check_server_on_startup()
                with gr.Row(visible=needs_start) as server_prompt_row:
                    with gr.Column():
                        gr.Markdown(f"### {startup_msg}")
                        with gr.Row():
                            start_server_btn = gr.Button("Start Default Server", variant="primary")
                            skip_server_btn = gr.Button("Skip (use external API)", variant="secondary")
                        server_start_status = gr.Textbox(label="Status", lines=2, interactive=False)

                # Server startup handlers
                def handle_start_server():
                    status = self.start_server_from_gui()
                    return status, gr.update(visible=False)

                def handle_skip_server():
                    return "Using GUI without local server", gr.update(visible=False)

                start_server_btn.click(
                    handle_start_server,
                    None,
                    [server_start_status, server_prompt_row]
                )
                skip_server_btn.click(
                    handle_skip_server,
                    None,
                    [server_start_status, server_prompt_row]
                )

                with gr.Tabs():

                    # ===== Chat Tab =====
                    with gr.Tab("💬 Chat"):
                        gr.Markdown("### Chat with your LLM")
                        gr.Markdown("Have a conversation with your configured language model")
    
                        chatbot = gr.Chatbot(
                            value=[],
                            label="Conversation",
                            height=500
                        )
    
                        with gr.Row():
                            msg = gr.Textbox(
                                label="Your message",
                                placeholder="Type your message here...",
                                scale=4,
                                lines=1,
                                max_lines=10,
                                show_label=True
                            )
                            with gr.Column(scale=1):
                                with gr.Row():
                                    submit = gr.Button("Send", variant="primary", scale=3)
                                    submit_on_enter = gr.Checkbox(
                                        label="Enter to send",
                                        value=True,
                                        scale=1,
                                        container=False
                                    )
                                # TTS toggle (always create, hide if module not available)
                                tts_enabled = gr.Checkbox(
                                    label="🔊 Voice Output",
                                    value=True,  # Enabled by default
                                    container=False,
                                    info="Enable/disable spoken responses",
                                    visible=self.tts is not None
                                )
                                # Voice listening control buttons (always create, hide if module not available)
                                with gr.Row(visible=self.stt is not None) as voice_controls_row:
                                    start_listening_btn = gr.Button("🎤 Start Listening", size="sm", variant="primary")
                                    stop_listening_btn = gr.Button("🛑 Stop Listening", size="sm", variant="stop", visible=False)
                                clear = gr.Button("Clear Chat")
                                # Add reload modules button
                                reload_modules_btn = gr.Button("🔄 Reload Modules", size="sm", variant="secondary")

                        # Module reload status message
                        reload_status = gr.Textbox(
                            label="Module Status",
                            value="",
                            interactive=False,
                            visible=False,
                            lines=1,
                            show_label=False
                        )

                        # Voice input status message (always create, hide if STT not available)
                        voice_status = gr.Textbox(
                            label="Voice Status",
                            value="",
                            interactive=False,
                            visible=False,
                            lines=1,
                            show_label=False
                        )
    
                        # Chat interactions
                        # Submit button always works
                        submit_event = submit.click(self.chat_respond, [msg, chatbot], [msg, chatbot])

                        # Add browser TTS for share mode
                        if self.is_share_mode and self.tts:
                            submit_event.then(
                                None,
                                None,
                                None,
                                js="""
                                () => {
                                    console.log('[TTS] Browser TTS triggered');

                                    // Check if TTS is enabled via checkbox
                                    const ttsCheckbox = document.querySelector('input[type="checkbox"][aria-label*="Voice Output"]');
                                    if (ttsCheckbox && !ttsCheckbox.checked) {
                                        console.log('[TTS] Voice Output is disabled, skipping TTS');
                                        return;
                                    }

                                    if (!('speechSynthesis' in window)) {
                                        console.warn('[TTS] Web Speech API not supported');
                                        return;
                                    }

                                    console.log('[TTS] Web Speech API available');

                                    // Wait for DOM to update, then get last message
                                    setTimeout(() => {
                                        console.log('[TTS] Looking for chatbot messages...');

                                        // Try multiple selectors to find messages
                                        let messages = [];

                                        // Try Gradio's chatbot message structure
                                        messages = document.querySelectorAll('.message.bot, .bot, [data-testid="bot"], .chatbot .message:last-child');
                                        console.log('[TTS] Found ' + messages.length + ' potential message elements');

                                        if (messages.length === 0) {
                                            // Fallback: look for any message in chatbot
                                            const chatbot = document.querySelector('.chatbot');
                                            if (chatbot) {
                                                messages = chatbot.querySelectorAll('.message, p, div[class*="message"]');
                                                console.log('[TTS] Fallback found ' + messages.length + ' elements');
                                            }
                                        }

                                        if (messages.length === 0) {
                                            console.warn('[TTS] No messages found in chatbot');
                                            return;
                                        }

                                        const lastMessage = messages[messages.length - 1];
                                        const text = lastMessage.textContent || lastMessage.innerText;
                                        console.log('[TTS] Last message text:', text.substring(0, 100));

                                        if (!text || text.trim().length === 0) {
                                            console.warn('[TTS] Message text is empty');
                                            return;
                                        }

                                        // Cancel any ongoing speech
                                        window.speechSynthesis.cancel();

                                        // Create and speak utterance
                                        console.log('[TTS] Speaking message...');
                                        const utterance = new SpeechSynthesisUtterance(text);
                                        utterance.rate = 1.0;
                                        utterance.pitch = 1.0;
                                        utterance.volume = 1.0;

                                        utterance.onstart = () => console.log('[TTS] Speech started');
                                        utterance.onend = () => console.log('[TTS] Speech ended');
                                        utterance.onerror = (e) => console.error('[TTS] Speech error:', e);

                                        window.speechSynthesis.speak(utterance);
                                    }, 1000);
                                }
                                """
                            )

                        # Enter key submission - conditional based on checkbox
                        # When disabled, we want multiline input (Enter creates newline)
                        # Problem: Gradio's .submit() always intercepts Enter and clears the textbox
                        # Solution: Check checkbox, and if disabled, restore the message + add newline
                        def handle_enter_key(message, history, enter_enabled):
                            """Handle Enter key press based on checkbox state."""
                            if enter_enabled:
                                # Submit: process the message
                                for update in self.chat_respond(message, history):
                                    yield update
                            else:
                                # Don't submit: restore message with newline added
                                # Gradio cleared the textbox, so we put the text back with a newline
                                yield message + "\n", history

                        enter_event = msg.submit(
                            handle_enter_key,
                            inputs=[msg, chatbot, submit_on_enter],
                            outputs=[msg, chatbot]
                        )

                        # Add browser TTS for share mode on Enter key
                        if self.is_share_mode and self.tts:
                            enter_event.then(
                                None,
                                None,
                                None,
                                js="""
                                () => {
                                    console.log('[TTS] Browser TTS triggered (Enter key)');

                                    if (!('speechSynthesis' in window)) {
                                        console.warn('[TTS] Web Speech API not supported');
                                        return;
                                    }

                                    console.log('[TTS] Web Speech API available');

                                    // Wait for DOM to update, then get last message
                                    setTimeout(() => {
                                        console.log('[TTS] Looking for chatbot messages...');

                                        // Try multiple selectors to find messages
                                        let messages = [];

                                        // Try Gradio's chatbot message structure
                                        messages = document.querySelectorAll('.message.bot, .bot, [data-testid="bot"], .chatbot .message:last-child');
                                        console.log('[TTS] Found ' + messages.length + ' potential message elements');

                                        if (messages.length === 0) {
                                            // Fallback: look for any message in chatbot
                                            const chatbot = document.querySelector('.chatbot');
                                            if (chatbot) {
                                                messages = chatbot.querySelectorAll('.message, p, div[class*="message"]');
                                                console.log('[TTS] Fallback found ' + messages.length + ' elements');
                                            }
                                        }

                                        if (messages.length === 0) {
                                            console.warn('[TTS] No messages found in chatbot');
                                            return;
                                        }

                                        const lastMessage = messages[messages.length - 1];
                                        const text = lastMessage.textContent || lastMessage.innerText;
                                        console.log('[TTS] Last message text:', text.substring(0, 100));

                                        if (!text || text.trim().length === 0) {
                                            console.warn('[TTS] Message text is empty');
                                            return;
                                        }

                                        // Cancel any ongoing speech
                                        window.speechSynthesis.cancel();

                                        // Create and speak utterance
                                        console.log('[TTS] Speaking message...');
                                        const utterance = new SpeechSynthesisUtterance(text);
                                        utterance.rate = 1.0;
                                        utterance.pitch = 1.0;
                                        utterance.volume = 1.0;

                                        utterance.onstart = () => console.log('[TTS] Speech started');
                                        utterance.onend = () => console.log('[TTS] Speech ended');
                                        utterance.onerror = (e) => console.error('[TTS] Speech error:', e);

                                        window.speechSynthesis.speak(utterance);
                                    }, 1000);
                                }
                                """
                            )

                        clear.click(self.clear_chat, None, chatbot)

                        # Reload modules button event handler
                        def handle_reload_modules():
                            """Handle module reload and show status briefly."""
                            # Reload and get UI updates
                            status_msg, tts_vis, voice_row_vis, stop_btn_vis = self.reload_modules()

                            # Show status
                            yield (
                                gr.update(value=status_msg, visible=True),  # reload_status
                                tts_vis,  # tts_enabled visibility
                                voice_row_vis,  # voice_controls_row visibility
                                stop_btn_vis,  # stop_listening_btn visibility
                                gr.update(visible=True)  # start_listening_btn visibility (always show when row visible)
                            )

                            # Hide status after 3 seconds
                            import time
                            time.sleep(3)
                            yield (
                                gr.update(value="", visible=False),  # reload_status
                                gr.update(),  # tts_enabled unchanged
                                gr.update(),  # voice_controls_row unchanged
                                gr.update(),  # stop_listening_btn unchanged
                                gr.update()   # start_listening_btn unchanged
                            )

                        reload_modules_btn.click(
                            handle_reload_modules,
                            inputs=[],
                            outputs=[reload_status, tts_enabled, voice_controls_row, stop_listening_btn, start_listening_btn]
                        )

                        # TTS toggle event handler (always wire up, works even if TTS not initially loaded)
                        def toggle_tts(enabled):
                            """Update TTS enabled state when user toggles checkbox."""
                            self.tts_enabled_state = enabled
                            return None  # No UI update needed

                        tts_enabled.change(toggle_tts, inputs=[tts_enabled], outputs=[])

                        # Voice input event handlers (always wire up, work even if STT not initially loaded)
                        # We'll check self.stt and self.listening_mode_active inside the handlers
                        def start_listening_mode():
                            """Enable continuous listening mode. Returns (start_vis, stop_vis, status_vis, status_val, proceed_flag)."""
                            if not self.stt:
                                # Show error but don't proceed to listening loop
                                return (
                                    gr.update(visible=True),   # Keep start button visible
                                    gr.update(visible=False),  # Keep stop button hidden
                                    gr.update(visible=True),   # Show status
                                    "⚠️ Speech-to-Text module not enabled. Use 'llf module enable speech2text' and click Reload Modules.",
                                    False  # Don't proceed to loop
                                )

                            self.listening_mode_active = True
                            logger.info("Continuous listening mode activated")

                            return (
                                gr.update(visible=False),  # Hide Start button
                                gr.update(visible=True),   # Show Stop button
                                gr.update(visible=True),   # Show status
                                "🎤 Listening mode active - waiting for your voice...",
                                True  # Proceed to loop
                            )

                        def stop_listening_mode():
                            """Disable continuous listening mode."""
                            self.listening_mode_active = False
                            logger.info("Continuous listening mode deactivated")
                            return (
                                gr.update(visible=True),   # Show Start button
                                gr.update(visible=False),  # Hide Stop button
                                gr.update(visible=False, value="")  # Hide status
                            )

                        def listen_once():
                            """
                            Listen for voice input once (used in continuous mode).
                            Returns updates for: voice_status, msg, chatbot
                            """
                            if not self.listening_mode_active:
                                # Mode was turned off, don't listen
                                return (
                                    gr.update(visible=False, value=""),
                                    gr.update(),  # msg unchanged
                                    gr.update()   # chatbot unchanged
                                )

                            try:
                                # Show status: Listening
                                yield (
                                    gr.update(visible=True, value="🎤 Listening... (speak now, pause when done)"),
                                    gr.update(),  # msg unchanged
                                    gr.update()   # chatbot unchanged
                                )

                                # Record and transcribe
                                text = self.stt.listen()

                                if not text or not text.strip():
                                    # Empty transcription, show status and continue listening
                                    yield (
                                        gr.update(visible=True, value="⚠️ No speech detected, listening again..."),
                                        gr.update(),
                                        gr.update()
                                    )
                                    import time
                                    time.sleep(1)
                                    # Will re-trigger via continuous mode
                                    return

                                # Show status: Transcribed
                                transcribed_msg = f"✅ Transcribed: {text}"
                                yield (
                                    gr.update(visible=True, value=transcribed_msg),
                                    gr.update(value=text),  # Populate message box
                                    gr.update()
                                )

                                # Brief pause so user sees the transcription
                                import time
                                time.sleep(0.5)

                            except Exception as e:
                                logger.error(f"Voice input error: {e}")
                                error_msg = f"⚠️ Voice input failed: {str(e)}"
                                yield (
                                    gr.update(visible=True, value=error_msg),
                                    gr.update(value=""),  # Clear message box on error
                                    gr.update()
                                )

                                # Show error briefly
                                import time
                                time.sleep(2)

                                # If still in listening mode, show ready status
                                if self.listening_mode_active:
                                    yield (
                                        gr.update(visible=True, value="🎤 Ready to listen again..."),
                                        gr.update(),
                                        gr.update()
                                    )
                                else:
                                    yield (
                                        gr.update(visible=False, value=""),
                                        gr.update(),
                                        gr.update()
                                    )

                        def continuous_listen_respond_loop(chatbot_history):
                            """
                            Continuous loop: listen -> transcribe -> respond -> listen again.
                            Runs while listening_mode_active is True.
                            """
                            # Safety check: STT must be available
                            if not self.stt:
                                yield (
                                    gr.update(visible=True, value="⚠️ Speech-to-Text module not available"),
                                    gr.update(),
                                    chatbot_history if chatbot_history else []
                                )
                                return

                            current_history = chatbot_history if chatbot_history else []

                            while self.listening_mode_active:
                                try:
                                    # Show status: Listening
                                    yield (
                                        gr.update(visible=True, value="🎤 Listening... (speak now, pause when done)"),
                                        gr.update(),  # msg unchanged
                                        current_history  # chatbot unchanged
                                    )

                                    # Record and transcribe
                                    text = self.stt.listen()

                                    if not text or not text.strip():
                                        # Empty transcription, continue listening
                                        yield (
                                            gr.update(visible=True, value="⚠️ No speech detected, listening again..."),
                                            gr.update(),
                                            current_history
                                        )
                                        import time
                                        time.sleep(1)
                                        continue

                                    # Show status: Transcribed
                                    transcribed_msg = f"✅ Transcribed: {text}"
                                    yield (
                                        gr.update(visible=True, value=transcribed_msg),
                                        gr.update(value=text),  # Populate message box
                                        current_history
                                    )

                                    # Process with LLM
                                    if not text.strip():
                                        continue

                                    # Add user message to history
                                    messages = []
                                    for msg in current_history:
                                        if isinstance(msg, dict) and 'role' in msg:
                                            messages.append(msg)

                                    messages.append({"role": "user", "content": text})
                                    current_history = current_history + [{"role": "user", "content": text}]

                                    # Get LLM response
                                    response_text = ""
                                    for chunk in self.runtime.chat(messages, stream=True):
                                        response_text += chunk
                                        streaming_history = current_history + [{"role": "assistant", "content": response_text}]
                                        yield (
                                            gr.update(),  # status unchanged
                                            gr.update(value=""),  # Clear message box
                                            streaming_history
                                        )

                                    # Update history with complete response
                                    current_history = current_history + [{"role": "assistant", "content": response_text}]

                                    # Speak response if TTS enabled
                                    if self.tts and self.tts_enabled_state and response_text:
                                        if not self.is_share_mode:
                                            try:
                                                from .tts_stt_utils import wait_for_tts_clearance
                                                logger.info("Speaking and waiting for audio clearance...")
                                                yield (
                                                    gr.update(visible=True, value="🔊 Speaking..."),
                                                    gr.update(),
                                                    gr.update()
                                                )
                                                wait_for_tts_clearance(self.tts, self.stt, response_text)
                                                logger.info("Audio cleared, ready for next input")
                                            except Exception as e:
                                                logger.warning(f"Text-to-Speech error: {e}")

                                    # Brief pause before next listen cycle
                                    import time
                                    time.sleep(0.5)

                                except Exception as e:
                                    logger.error(f"Error in continuous listen loop: {e}")
                                    yield (
                                        gr.update(visible=True, value=f"⚠️ Error: {str(e)}"),
                                        gr.update(),
                                        current_history
                                    )
                                    import time
                                    time.sleep(2)

                            # Loop exited (listening mode stopped)
                            yield (
                                gr.update(visible=False, value=""),
                                gr.update(),
                                current_history
                            )

                        # Start listening button: activate continuous mode and conditionally start loop
                        def start_and_maybe_loop(chatbot_history):
                            """Start listening mode, and if successful, run the continuous loop."""
                            # Try to start listening mode
                            start_vis, stop_vis, status_vis, status_val, proceed = start_listening_mode()

                            # Combine status visibility and value
                            # status_vis is a gr.update() dict, we need to merge it with the value
                            if isinstance(status_vis, dict):
                                status_update = status_vis.copy()
                                status_update['value'] = status_val
                            else:
                                status_update = gr.update(visible=True, value=status_val)

                            # Update UI first
                            yield (
                                start_vis,
                                stop_vis,
                                status_update,
                                gr.update(),  # msg
                                chatbot_history if chatbot_history else []  # chatbot
                            )

                            # If STT is available, proceed with continuous loop
                            if proceed and self.stt:
                                # Run the continuous listen loop
                                for update in continuous_listen_respond_loop(chatbot_history):
                                    yield (
                                        gr.update(),  # start_btn
                                        gr.update(),  # stop_btn
                                        update[0],    # voice_status
                                        update[1],    # msg
                                        update[2]     # chatbot
                                    )

                        start_listening_btn.click(
                            start_and_maybe_loop,
                            inputs=[chatbot],
                            outputs=[start_listening_btn, stop_listening_btn, voice_status, msg, chatbot]
                        )

                        # Stop listening button: deactivate continuous mode
                        stop_listening_btn.click(
                            stop_listening_mode,
                            inputs=[],
                            outputs=[start_listening_btn, stop_listening_btn, voice_status]
                        )

                    # ===== Server Tab =====
                    with gr.Tab("🖥️ Server"):
                        gr.Markdown("### Server Management")
                        gr.Markdown("Start, stop, and monitor your local LLM servers")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Available Servers")
                                servers_radio = gr.Radio(
                                    label="Select a Server",
                                    choices=self.get_available_servers(),
                                    value=self.get_available_servers()[0] if self.get_available_servers() else None
                                )

                            with gr.Column():
                                gr.Markdown("#### Server Information")
                                server_info_output = gr.Textbox(
                                    label="Server Details",
                                    lines=12,
                                    interactive=False,
                                    value=self.get_server_info(self.get_available_servers()[0] if self.get_available_servers() else "")
                                )

                        with gr.Row():
                            start_server_btn = gr.Button("Start Server", variant="primary")
                            stop_server_btn = gr.Button("Stop Server", variant="stop")
                            restart_server_btn = gr.Button("Restart Server")
                            refresh_server_btn = gr.Button("🔄 Refresh", variant="secondary")

                        server_status = gr.Textbox(
                            label="Status",
                            lines=3,
                            interactive=False
                        )

                        # Server interactions
                        servers_radio.change(self.get_server_info, servers_radio, server_info_output)
                        start_server_btn.click(self.start_server_by_name, servers_radio, [server_status, server_info_output])
                        stop_server_btn.click(self.stop_server_by_name, servers_radio, [server_status, server_info_output])
                        restart_server_btn.click(self.restart_server_by_name, servers_radio, [server_status, server_info_output])
                        refresh_server_btn.click(self.get_server_info, servers_radio, server_info_output)
    
                    # ===== Models Tab =====
                    with gr.Tab("📦 Models"):
                        gr.Markdown("### Model Management")
                        gr.Markdown("Download and manage your LLM models")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Downloaded Models")
                                models_radio = gr.Radio(
                                    label="Select a Model",
                                    choices=self.list_models_for_radio(),
                                    value="Default"
                                )

                            with gr.Column():
                                gr.Markdown("#### Model Information")
                                model_info_output = gr.Textbox(
                                    label="Model Details",
                                    lines=10,
                                    interactive=False,
                                    value=self.get_selected_model_info("Default")
                                )

                        refresh_btn = gr.Button("Refresh List")
                        gr.Markdown("---")
                        gr.Markdown("#### Download New Model")

                        download_type = gr.Radio(
                            label="Download Method",
                            choices=["HuggingFace", "URL"],
                            value="HuggingFace"
                        )

                        with gr.Column(visible=True) as hf_section:
                            hf_model_input = gr.Textbox(
                                label="HuggingFace Model Name",
                                placeholder="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
                            )

                        with gr.Column(visible=False) as url_section:
                            url_input = gr.Textbox(
                                label="GGUF File URL",
                                placeholder="https://example.com/model.gguf"
                            )
                            url_name_input = gr.Textbox(
                                label="Custom Name",
                                placeholder="my-model"
                            )

                        download_btn = gr.Button("Download Model", variant="primary")
                        download_output = gr.Textbox(
                            label="Download Status",
                            lines=3,
                            interactive=False
                        )
    
                        # Model interactions
                        models_radio.change(self.get_selected_model_info, models_radio, model_info_output)
                        refresh_btn.click(self.refresh_models_list, None, [models_radio, model_info_output])

                        # Download method selector - show/hide sections
                        download_type.change(
                            self.toggle_download_sections,
                            download_type,
                            [hf_section, url_section]
                        )

                        download_btn.click(
                            self.download_model,
                            [download_type, hf_model_input, url_input, url_name_input],
                            download_output
                        )
    
                    # ===== Config Tab =====
                    with gr.Tab("⚙️ Configuration"):
                        gr.Markdown("### Configuration Editor")
                        gr.Markdown("Edit your configuration files (changes require saving)")
    
                        with gr.Tab("config.json"):
                            gr.Markdown("**Infrastructure Configuration** - Server, API, models, inference parameters")
    
                            config_editor = gr.Code(
                                label="config.json",
                                language="json",
                                lines=20,
                                value=self.load_config()
                            )
    
                            with gr.Row():
                                config_load_btn = gr.Button("Reload from File")
                                config_backup_btn = gr.Button("Create Backup", variant="secondary")
                                config_save_btn = gr.Button("Save to File", variant="primary")
    
                            config_status = gr.Textbox(
                                label="Status",
                                lines=2,
                                interactive=False
                            )
    
                            # Config interactions
                            config_load_btn.click(self.reload_config_with_status, None, [config_editor, config_status])
                            config_backup_btn.click(self.backup_config, None, config_status)
                            config_save_btn.click(self.save_config, config_editor, config_status)

                        with gr.Tab("config_prompt.json"):
                            gr.Markdown("**Prompt Configuration** - System prompts, conversation formatting")
    
                            prompt_editor = gr.Code(
                                label="config_prompt.json",
                                language="json",
                                lines=20,
                                value=self.load_prompt_config()
                            )
    
                            with gr.Row():
                                prompt_load_btn = gr.Button("Reload from File")
                                prompt_backup_btn = gr.Button("Create Backup", variant="secondary")
                                prompt_save_btn = gr.Button("Save to File", variant="primary")
    
                            prompt_status = gr.Textbox(
                                label="Status",
                                lines=2,
                                interactive=False
                            )
    
                            # Prompt config interactions
                            prompt_load_btn.click(self.reload_prompt_config_with_status, None, [prompt_editor, prompt_status])
                            prompt_backup_btn.click(self.backup_prompt_config, None, prompt_status)
                            prompt_save_btn.click(self.save_prompt_config, prompt_editor, prompt_status)

                    # ===== Data Stores Tab =====
                    with gr.Tab("📊 Data Stores"):
                        gr.Markdown("### Data Store Management")
                        gr.Markdown("Attach or detach RAG vector stores")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Available Data Stores")
                                datastores_radio = gr.Radio(
                                    label="Select a Data Store",
                                    choices=self.get_available_datastores(),
                                    value=self.get_available_datastores()[0] if self.get_available_datastores() else None
                                )

                            with gr.Column():
                                gr.Markdown("#### Data Store Information")
                                datastore_info_output = gr.Textbox(
                                    label="Data Store Details",
                                    lines=12,
                                    interactive=False,
                                    value=self.get_datastore_info(self.get_available_datastores()[0] if self.get_available_datastores() else "")
                                )

                        with gr.Row():
                            attach_btn = gr.Button("Attach Data Store", variant="primary")
                            detach_btn = gr.Button("Detach Data Store")

                        with gr.Row():
                            refresh_datastores_btn = gr.Button("Refresh")

                        datastore_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Data Store interactions
                        datastores_radio.change(self.get_datastore_info, datastores_radio, datastore_info_output)
                        attach_btn.click(self.attach_datastore, datastores_radio, [datastore_status, datastore_info_output])
                        detach_btn.click(self.detach_datastore, datastores_radio, [datastore_status, datastore_info_output])
                        refresh_datastores_btn.click(
                            lambda: (gr.update(choices=self.get_available_datastores(), value=self.get_available_datastores()[0] if self.get_available_datastores() else None),
                                   self.get_datastore_info(self.get_available_datastores()[0] if self.get_available_datastores() else "")),
                            None,
                            [datastores_radio, datastore_info_output]
                        )

                    # ===== Memory Tab =====
                    with gr.Tab("🧠 Memory"):
                        gr.Markdown("### Memory Management")
                        gr.Markdown("Enable or disable memory instances for persistent information storage")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Available Memory Instances")
                                memories_radio = gr.Radio(
                                    label="Select a Memory Instance",
                                    choices=self.get_available_memories(),
                                    value=self.get_available_memories()[0] if self.get_available_memories() else None
                                )

                            with gr.Column():
                                gr.Markdown("#### Memory Information")
                                memory_info_output = gr.Textbox(
                                    label="Memory Details",
                                    lines=12,
                                    interactive=False,
                                    value=self.get_memory_info(self.get_available_memories()[0] if self.get_available_memories() else "")
                                )

                        with gr.Row():
                            enable_memory_btn = gr.Button("Enable Memory", variant="primary")
                            disable_memory_btn = gr.Button("Disable Memory")

                        with gr.Row():
                            refresh_memories_btn = gr.Button("Refresh")

                        memory_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Memory interactions
                        memories_radio.change(self.get_memory_info, memories_radio, memory_info_output)
                        enable_memory_btn.click(self.enable_memory, memories_radio, [memory_status, memory_info_output])
                        disable_memory_btn.click(self.disable_memory, memories_radio, [memory_status, memory_info_output])
                        refresh_memories_btn.click(
                            lambda: (gr.update(choices=self.get_available_memories(), value=self.get_available_memories()[0] if self.get_available_memories() else None),
                                   self.get_memory_info(self.get_available_memories()[0] if self.get_available_memories() else "")),
                            None,
                            [memories_radio, memory_info_output]
                        )

                    # ===== Modules Tab =====
                    with gr.Tab("🔌 Modules"):
                        gr.Markdown("### Module Management")
                        gr.Markdown("Enable or disable framework modules")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Available Modules")
                                modules_radio = gr.Radio(
                                    label="Select a Module",
                                    choices=self.get_available_modules(),
                                    value=self.get_available_modules()[0] if self.get_available_modules() else None
                                )

                            with gr.Column():
                                gr.Markdown("#### Module Information")
                                module_info_output = gr.Textbox(
                                    label="Module Details",
                                    lines=12,
                                    interactive=False,
                                    value=self.get_module_info(self.get_available_modules()[0] if self.get_available_modules() else "")
                                )

                        with gr.Row():
                            enable_btn = gr.Button("Enable Module", variant="primary")
                            disable_btn = gr.Button("Disable Module")

                        with gr.Row():
                            refresh_modules_btn = gr.Button("Refresh")

                        module_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Module interactions
                        modules_radio.change(self.get_module_info, modules_radio, module_info_output)
                        enable_btn.click(self.enable_module, modules_radio, [module_status, module_info_output])
                        disable_btn.click(self.disable_module, modules_radio, [module_status, module_info_output])
                        refresh_modules_btn.click(
                            lambda: (gr.update(choices=self.get_available_modules(), value=self.get_available_modules()[0] if self.get_available_modules() else None),
                                   self.get_module_info(self.get_available_modules()[0] if self.get_available_modules() else "")),
                            None,
                            [modules_radio, module_info_output]
                        )

                    # ===== Tools Tab =====
                    with gr.Tab("🛠️ Tools"):
                        gr.Markdown("### Tool Management")
                        gr.Markdown("Enable or disable tool features and compatibility layers")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### Available Tools")
                                tools_radio = gr.Radio(
                                    label="Select a Tool",
                                    choices=self.get_available_tools(),
                                    value=self.get_available_tools()[0] if self.get_available_tools() else None
                                )

                            with gr.Column():
                                gr.Markdown("#### Tool Information")
                                tool_info_output = gr.Textbox(
                                    label="Tool Details",
                                    lines=12,
                                    interactive=False,
                                    value=self.get_tool_info(self.get_available_tools()[0] if self.get_available_tools() else "")
                                )

                        with gr.Row():
                            enable_tool_btn = gr.Button("Enable", variant="primary")
                            auto_tool_btn = gr.Button("Auto", variant="secondary")
                            disable_tool_btn = gr.Button("Disable")

                        with gr.Row():
                            refresh_tools_btn = gr.Button("Refresh")

                        tool_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Restart confirmation dialog components (initially hidden)
                        restart_dialog_visible = gr.State(False)
                        pending_tool_change = gr.State(None)  # Stores the tool change info

                        with gr.Group(visible=False) as restart_dialog:
                            gr.Markdown("### 🔄 Server Restart Required")
                            gr.Markdown("Tool settings have been changed. Would you like to restart the local server now for changes to take effect?")
                            with gr.Row():
                                restart_yes_btn = gr.Button("Yes, Restart Server", variant="primary")
                                restart_no_btn = gr.Button("No, I'll Restart Later")

                        # Tool interactions
                        tools_radio.change(self.get_tool_info, tools_radio, tool_info_output)

                        # Enable tool with restart prompt
                        enable_tool_btn.click(
                            self.enable_tool_with_restart_check,
                            tools_radio,
                            [tool_status, tool_info_output, restart_dialog, pending_tool_change]
                        )

                        # Auto tool with restart prompt
                        auto_tool_btn.click(
                            self.auto_tool_with_restart_check,
                            tools_radio,
                            [tool_status, tool_info_output, restart_dialog, pending_tool_change]
                        )

                        # Disable tool with restart prompt
                        disable_tool_btn.click(
                            self.disable_tool_with_restart_check,
                            tools_radio,
                            [tool_status, tool_info_output, restart_dialog, pending_tool_change]
                        )

                        # Handle restart confirmation
                        restart_yes_btn.click(
                            self.handle_tool_restart_yes,
                            None,
                            [restart_dialog, tool_status]
                        )

                        restart_no_btn.click(
                            lambda: gr.update(visible=False),
                            None,
                            restart_dialog
                        )

                        refresh_tools_btn.click(
                            lambda: (gr.update(choices=self.get_available_tools(), value=self.get_available_tools()[0] if self.get_available_tools() else None),
                                   self.get_tool_info(self.get_available_tools()[0] if self.get_available_tools() else "")),
                            None,
                            [tools_radio, tool_info_output]
                        )

            # Authentication handler
            def handle_login(entered_key, current_auth):
                """Handle login attempt."""
                if entered_key == self.auth_key:
                    # Authentication successful - hide login, show main UI
                    return (
                        True,  # Update auth_state
                        "",  # Clear key input
                        gr.update(visible=False),  # Hide status (don't show success message)
                        gr.update(visible=False),  # Hide login UI
                        gr.update(visible=True)  # Show main UI
                    )
                else:
                    # Authentication failed - show error
                    return (
                        False,  # Keep auth_state as False
                        "",  # Clear key input
                        gr.update(value="❌ Invalid secret key. Please try again.", visible=True),  # Show error
                        gr.update(visible=True),  # Keep login UI visible
                        gr.update(visible=False)  # Keep main UI hidden
                    )

            # Only set up login handler if authentication is required
            if self.auth_key:
                login_btn.click(
                    handle_login,
                    [key_input, auth_state],
                    [auth_state, key_input, login_status, login_ui, main_ui]
                )

        return interface

    def launch(self, server_name: str = "127.0.0.1", server_port: int = 7860, inbrowser: bool = True, **kwargs):
        """
        Launch the Gradio interface.

        Args:
            server_name: Host to bind the GUI server to (e.g., "127.0.0.1" for localhost, "0.0.0.0" for network)
            server_port: Port to run the server on
            inbrowser: Automatically open in browser (default: True)
            **kwargs: Additional arguments to pass to Gradio launch()
        """
        interface = self.create_interface()
        interface.launch(
            server_name=server_name,
            server_port=server_port,
            inbrowser=inbrowser,
            **kwargs
        )


def start_gui(config: Optional[Config] = None, prompt_config: Optional[PromptConfig] = None, auth_key: Optional[str] = None, **kwargs):
    """
    Start the GUI interface.

    Args:
        config: Optional configuration instance
        prompt_config: Optional prompt configuration instance
        auth_key: Optional authentication key for securing GUI access
        **kwargs: Additional arguments to pass to Gradio launch()
    """
    # Extract share parameter from kwargs to pass to GUI constructor
    share = kwargs.get('share', False)
    gui = LLMFrameworkGUI(config=config, prompt_config=prompt_config, auth_key=auth_key, share=share)
    gui.launch(**kwargs)

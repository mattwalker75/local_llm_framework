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

    def __init__(self, config: Optional[Config] = None, prompt_config: Optional[PromptConfig] = None, auth_key: Optional[str] = None):
        """
        Initialize GUI.

        Args:
            config: Configuration instance (defaults to global config)
            prompt_config: Prompt configuration instance (defaults to global)
            auth_key: Optional authentication key for securing GUI access
        """
        self.config = config or get_config()
        self.prompt_config = prompt_config or get_prompt_config()
        self.model_manager = ModelManager(self.config)
        self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)
        self.chat_history: List[Tuple[str, str]] = []
        self.started_server = False  # Track if GUI started the server
        self.auth_key = auth_key  # Authentication key (None = no auth required)

        # Load module registry and initialize text-to-speech if enabled
        self.tts = None
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
                        self.tts = TextToSpeech()
                        logger.info("Text-to-Speech module loaded and enabled for GUI")
                    except Exception as e:
                        logger.warning(f"Failed to load text2speech module: {e}")
                    break
        except Exception as e:
            logger.warning(f"Failed to load module registry: {e}")

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

        # Check if server is already running
        if self.runtime.is_server_running():
            logger.info("Server is already running")
            return False, "✅ Server is running"

        # Server is not running - needs user action
        logger.info("Server is not running")
        return True, "❌ Server is not running. Would you like to start it?"

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

            # Stream response from LLM
            response_text = ""
            for chunk in self.runtime.chat(messages, stream=True):
                response_text += chunk
                # Update history with partial response
                current_history = history + [{"role": "assistant", "content": response_text}]
                yield "", current_history

            # If TTS is enabled, speak the complete response
            if self.tts and response_text:
                try:
                    self.tts.speak(response_text)
                except Exception as e:
                    logger.warning(f"Text-to-Speech error: {e}")

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
                            start_server_btn = gr.Button("Start Server", variant="primary")
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
                                clear = gr.Button("Clear Chat")
    
                        # Chat interactions
                        # Submit button always works
                        submit.click(self.chat_respond, [msg, chatbot], [msg, chatbot])

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

                        msg.submit(
                            handle_enter_key,
                            inputs=[msg, chatbot, submit_on_enter],
                            outputs=[msg, chatbot]
                        )

                        clear.click(self.clear_chat, None, chatbot)
    
                    # ===== Server Tab =====
                    with gr.Tab("🖥️ Server"):
                        gr.Markdown("### Server Management")
                        gr.Markdown("Control your local LLM server")

                        status_output = gr.Textbox(
                            label="Server Status",
                            lines=5,
                            interactive=False,
                            value='Click on "Check Status"'
                        )
    
                        with gr.Row():
                            status_btn = gr.Button("Check Status", variant="secondary")
                            start_btn = gr.Button("Start Server", variant="primary")
                            stop_btn = gr.Button("Stop Server", variant="stop")
                            restart_btn = gr.Button("Restart Server")
    
                        # Server interactions
                        status_btn.click(self.get_server_status, None, status_output)
                        start_btn.click(self.start_server, None, status_output)
                        stop_btn.click(self.stop_server, None, status_output)
                        restart_btn.click(self.restart_server, None, status_output)
    
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
                    with gr.Tab("📚 Data Stores"):
                        gr.Markdown("### Data Store Management")
                        gr.Markdown("For future use...")

                    # ===== Modules Tab =====
                    with gr.Tab("🔌 Modules"):
                        gr.Markdown("### Module Management")
                        gr.Markdown("For future use...")

                    # ===== Tools Tab =====
                    with gr.Tab("🛠️ Tools"):
                        gr.Markdown("### Tool Management")
                        gr.Markdown("For future use...")

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
    gui = LLMFrameworkGUI(config=config, prompt_config=prompt_config, auth_key=auth_key)
    gui.launch(**kwargs)

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


class LLMFrameworkGUI:
    """
    Gradio-based GUI for the LLM Framework.

    Provides tabbed interface for:
    - Chat: Interactive conversation with LLM
    - Server: Start/stop/status controls
    - Models: Download/list/info management
    - Config: Edit config.json and config_prompt.json
    """

    def __init__(self, config: Optional[Config] = None, prompt_config: Optional[PromptConfig] = None):
        """
        Initialize GUI.

        Args:
            config: Configuration instance (defaults to global config)
            prompt_config: Prompt configuration instance (defaults to global)
        """
        self.config = config or get_config()
        self.prompt_config = prompt_config or get_prompt_config()
        self.model_manager = ModelManager(self.config)
        self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)
        self.chat_history: List[Tuple[str, str]] = []

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
            # Stop server if running
            if self.config.has_local_server_config() and self.runtime.is_server_running():
                self.runtime.stop_server()
                logger.info("Server stopped")

            # Schedule GUI shutdown
            import os
            import signal
            import threading

            def delayed_shutdown():
                import time
                time.sleep(1)  # Give time for the response to be sent
                os.kill(os.getpid(), signal.SIGINT)

            threading.Thread(target=delayed_shutdown, daemon=True).start()

            return "✅ Shutting down GUI... The window will close shortly."
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

    def download_model(self, model_name: str, url: str, custom_name: str) -> str:
        """
        Download a model.

        Args:
            model_name: HuggingFace model name (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
            url: Direct URL to GGUF file (alternative to model_name)
            custom_name: Custom name for URL-downloaded model

        Returns:
            Status message
        """
        try:
            if url and url.strip():
                # URL download
                if not custom_name or not custom_name.strip():
                    return "❌ Please provide a custom name for URL downloads"

                self.model_manager.download_model_from_url(
                    url=url.strip(),
                    model_dir_name=custom_name.strip()
                )
                return f"✅ Model downloaded successfully from URL\n\nSaved as: {custom_name}"

            elif model_name and model_name.strip():
                # HuggingFace download
                self.model_manager.download_model(
                    model_name=model_name.strip(),
                    force=False
                )
                return f"✅ Model downloaded successfully\n\nModel: {model_name}"

            else:
                return "❌ Please provide either a HuggingFace model name or a URL"

        except Exception as e:
            return f"❌ Error downloading model: {str(e)}"

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
        """Save config.json content."""
        try:
            # Validate JSON
            json.loads(content)

            # Save file
            config_file = Config.DEFAULT_CONFIG_FILE
            with open(config_file, 'w') as f:
                f.write(content)

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
        """Save config_prompt.json content."""
        try:
            # Validate JSON
            json.loads(content)

            # Save file
            config_file = PromptConfig.DEFAULT_CONFIG_FILE
            with open(config_file, 'w') as f:
                f.write(content)

            # Reload prompt config
            self.prompt_config = get_prompt_config(force_reload=True)
            self.runtime = LLMRuntime(self.config, self.model_manager, self.prompt_config)

            return "✅ config_prompt.json saved and reloaded successfully"
        except json.JSONDecodeError as e:
            return f"❌ Invalid JSON: {str(e)}"
        except Exception as e:
            return f"❌ Error saving config_prompt.json: {str(e)}"

    # ===== Main Interface Builder =====

    def create_interface(self) -> gr.Blocks:
        """
        Create and return the Gradio interface.

        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(title="LLM Framework GUI") as interface:

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
                            lines=2
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

                    # Chat interactions - conditionally enable submit on enter
                    def handle_submit(message, history, enter_enabled):
                        """Handle message submission."""
                        if enter_enabled:
                            return self.chat_respond(message, history)
                        return message, history

                    # Submit button always works
                    submit.click(self.chat_respond, [msg, chatbot], [msg, chatbot])

                    # Enter key only works when checkbox is enabled
                    msg.submit(
                        lambda m, h, enabled: self.chat_respond(m, h) if enabled else ("", h),
                        [msg, chatbot, submit_on_enter],
                        [msg, chatbot]
                    )

                    clear.click(self.clear_chat, None, chatbot)

                # ===== Server Tab =====
                with gr.Tab("🖥️ Server"):
                    gr.Markdown("### Server Management")
                    gr.Markdown("Control your local LLM server")

                    status_output = gr.Textbox(
                        label="Server Status",
                        lines=5,
                        interactive=False
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

                    # Auto-update status on load
                    interface.load(self.get_server_status, None, status_output)

                # ===== Models Tab =====
                with gr.Tab("📦 Models"):
                    gr.Markdown("### Model Management")
                    gr.Markdown("Download and manage your LLM models")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("#### Downloaded Models")
                            models_list = gr.Textbox(
                                label="Your Models",
                                lines=8,
                                interactive=False
                            )
                            refresh_btn = gr.Button("Refresh List")

                        with gr.Column():
                            gr.Markdown("#### Model Information")
                            model_info_input = gr.Textbox(
                                label="Model Name (leave empty for default)",
                                placeholder="e.g., Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
                            )
                            model_info_btn = gr.Button("Get Info")
                            model_info_output = gr.Textbox(
                                label="Model Details",
                                lines=8,
                                interactive=False
                            )

                    gr.Markdown("---")
                    gr.Markdown("#### Download New Model")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**Option 1: HuggingFace Model**")
                            hf_model_input = gr.Textbox(
                                label="HuggingFace Model Name",
                                placeholder="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
                            )

                        with gr.Column():
                            gr.Markdown("**Option 2: Direct URL**")
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
                    refresh_btn.click(self.list_models, None, models_list)
                    model_info_btn.click(self.get_model_info, model_info_input, model_info_output)
                    download_btn.click(
                        self.download_model,
                        [hf_model_input, url_input, url_name_input],
                        download_output
                    )

                    # Auto-load models list
                    interface.load(self.list_models, None, models_list)

                # ===== Config Tab =====
                with gr.Tab("⚙️ Configuration"):
                    gr.Markdown("### Configuration Editor")
                    gr.Markdown("Edit your configuration files (changes require saving)")

                    with gr.Tab("config.json"):
                        gr.Markdown("**Infrastructure Configuration** - Server, API, models, inference parameters")

                        config_editor = gr.Code(
                            label="config.json",
                            language="json",
                            lines=20
                        )

                        with gr.Row():
                            config_load_btn = gr.Button("Reload from File")
                            config_save_btn = gr.Button("Save to File", variant="primary")

                        config_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Config interactions
                        config_load_btn.click(self.load_config, None, config_editor)
                        config_save_btn.click(self.save_config, config_editor, config_status)
                        interface.load(self.load_config, None, config_editor)

                    with gr.Tab("config_prompt.json"):
                        gr.Markdown("**Prompt Configuration** - System prompts, conversation formatting")

                        prompt_editor = gr.Code(
                            label="config_prompt.json",
                            language="json",
                            lines=20
                        )

                        with gr.Row():
                            prompt_load_btn = gr.Button("Reload from File")
                            prompt_save_btn = gr.Button("Save to File", variant="primary")

                        prompt_status = gr.Textbox(
                            label="Status",
                            lines=2,
                            interactive=False
                        )

                        # Prompt config interactions
                        prompt_load_btn.click(self.load_prompt_config, None, prompt_editor)
                        prompt_save_btn.click(self.save_prompt_config, prompt_editor, prompt_status)
                        interface.load(self.load_prompt_config, None, prompt_editor)

        return interface

    def launch(self, share: bool = False, server_port: int = 7860, inbrowser: bool = True, **kwargs):
        """
        Launch the Gradio interface.

        Args:
            share: Create a public share link
            server_port: Port to run the server on
            inbrowser: Automatically open in browser (default: True)
            **kwargs: Additional arguments to pass to Gradio launch()
        """
        interface = self.create_interface()
        interface.launch(
            share=share,
            server_port=server_port,
            inbrowser=inbrowser,
            **kwargs
        )


def start_gui(config: Optional[Config] = None, prompt_config: Optional[PromptConfig] = None, **kwargs):
    """
    Start the GUI interface.

    Args:
        config: Optional configuration instance
        prompt_config: Optional prompt configuration instance
        **kwargs: Additional arguments to pass to Gradio launch()
    """
    gui = LLMFrameworkGUI(config=config, prompt_config=prompt_config)
    gui.launch(**kwargs)

#!/usr/bin/env python
"""
CLI Interface for Local LLM Framework

This module provides the command-line interface for interacting with both local
and external LLM services. It handles interactive chat, model management, server
control, and configuration management.

Architecture:
    - CLI class: Main interface handling interactive chat loop and user commands
    - Argparse-based command structure: model, server, datastore, module, tool commands
    - Rich library integration: Beautiful terminal output with colors and formatting
    - Multi-server support: Manages multiple local llama-server instances

Key Features:
    - Interactive chat with streaming responses
    - Model download and management (HuggingFace integration)
    - Server lifecycle management (start, stop, restart, status)
    - Tool/Module/Datastore configuration via CLI
    - Memory management with dual-pass execution modes
    - Question mode: Single-shot queries without entering chat loop

Execution Modes:
    - Single-pass: Non-streaming, accurate tool execution (default for READ operations)
    - Dual-pass: Stream response first, execute tools in background (WRITE operations)
    - Streaming-only: Fast responses without tool support (GENERAL conversation)

Design Philosophy:
    - Separation of concerns: CLI handles UI, managers handle business logic
    - Extensibility: Easy to add new commands and execution modes
    - User experience: Rich formatting, clear error messages, helpful prompts

Future Extensions:
    - Batch processing mode
    - Completion API (non-chat)
    - Plugin system for custom commands
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import signal
from datetime import datetime, UTC
import json
import shutil

from rich.console import Console
from rich.panel import Panel

from llf.trash_manager import TrashManager
from rich.markdown import Markdown
from rich.prompt import Prompt

from .logging_config import setup_logging, get_logger, disable_external_loggers
from .config import Config, get_config
from .model_manager import ModelManager
from .llm_runtime import LLMRuntime
from .prompt_config import PromptConfig, get_prompt_config
from .server_commands import (
    list_servers_command,
    start_server_command,
    stop_server_command,
    status_server_command,
    switch_server_command
)
from .prompt_commands import (
    list_templates_command,
    info_template_command,
    load_template_command,
    import_template_command,
    export_template_command,
    enable_template_command,
    disable_template_command,
    backup_templates_command,
    delete_template_command,
    create_template_command,
    show_active_template_command
)

logger = get_logger(__name__)
console = Console()


class CLI:
    """
    Command-line interface for LLF.

    Provides interactive prompt loop and command handling.
    """

    def __init__(self, config: Config, prompt_config: Optional[PromptConfig] = None, auto_start_server: bool = False, no_server_start: bool = False, save_history: bool = True, imported_session: Optional[Dict[str, Any]] = None):
        """
        Initialize CLI.

        Args:
            config: Configuration instance.
            prompt_config: Optional prompt configuration for formatting LLM messages.
            auto_start_server: Automatically start server if not running.
            no_server_start: Do not start server if not running (exit with error).
            save_history: Save chat conversations to history (default: True).
            imported_session: Optional session data to import and continue.
        """
        self.config = config
        self.prompt_config = prompt_config
        self.model_manager = ModelManager(config)
        self.runtime = LLMRuntime(config, self.model_manager, prompt_config)
        self.running = False
        self.auto_start_server = auto_start_server
        self.no_server_start = no_server_start
        self.started_server = False  # Track if this instance started the server
        self.save_history = save_history
        self.imported_session = imported_session

        # Initialize chat history manager
        from llf.chat_history import ChatHistory
        history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
        self.chat_history = ChatHistory(history_dir)

        # Load module registry and initialize text-to-speech and speech-to-text if enabled
        self.tts = None
        self.stt = None
        self._load_modules()

        # Setup signal handlers for graceful shutdown (skip during testing)
        # Pytest's coverage plugin interferes with signal handlers during teardown,
        # so we skip registration when running under pytest
        if not os.environ.get('PYTEST_CURRENT_TEST'):
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, _signum, _frame):
        """Handle shutdown signals gracefully."""
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.running = False
        self.shutdown()
        sys.exit(0)

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
                        logger.info("Text-to-Speech module loaded and enabled")
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
                        logger.info("Speech-to-Text module loaded and enabled")
                    except Exception as e:
                        logger.warning(f"Failed to load speech2text module: {e}")
                    break
        except Exception as e:
            logger.warning(f"Failed to load module registry: {e}")

    def print_welcome(self) -> None:
        """Print welcome message."""
        # Try to get the actual loaded model from the running server
        model_display = self.config.model_name  # Default to config

        # For local servers, query the actual loaded model
        if not self.config.is_using_external_api() and self.runtime.is_server_running():
            try:
                models = self.runtime.list_models()
                if models and len(models) > 0:
                    # Use the first model ID from the server
                    model_display = models[0]['id']
            except Exception:
                # If query fails, fall back to config model name
                pass

        # Build mode description
        mode_description = "Interactive Chat"
        if self.stt:
            mode_description += " (Voice Input)"
        if self.tts:
            if self.stt:
                mode_description += " + (Voice Output)"
            else:
                mode_description += " (Voice Output)"

        # Build input instructions
        input_instruction = "Speak your messages (pause when done)." if self.stt else "Type your messages and press Enter to send."

        welcome_text = f"""
# Local LLM Framework

**Model:** {model_display}
**Mode:** {mode_description}

{input_instruction}
For multiline input, type `START`, paste your content, then type `END`.

Commands:
- `exit` or `quit` - Exit the application
- `help` - Show this help message
- `info` - Show model information
- `clear` - Clear conversation history (Phase 1: just clears screen)

Press Ctrl+C to exit at any time.
        """
        console.print(Panel(Markdown(welcome_text), title="Welcome to LLF", border_style="green"))

    def print_help(self) -> None:
        """Print help information."""
        help_text = """
# Available Commands

- `exit`, `quit` - Exit the application
- `help` - Show this help message
- `info` - Show model and system information
- `clear` - Clear the screen and conversation history

# Multiline Input

To provide multiline input (e.g., paste document content):
1. Type `START` and press Enter
2. Paste or type your content (can be multiple lines)
3. Type `END` on a new line and press Enter

This is useful for pasting content from PDFs, documents, or code files.

# Chat Mode

"""
        # Add voice or text input instructions based on STT status
        if self.stt:
            help_text += "Simply speak your message and pause when done. The system will detect silence and process your speech.\n\n"
            help_text += """# Voice Input

Speech-to-Text is enabled. Speak clearly and pause for 1.5 seconds when done.
If STT fails, the system will automatically fall back to keyboard input.
"""
        else:
            help_text += "Simply type your message and press Enter to chat with the LLM.\n"

        console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))

    def print_info(self) -> None:
        """Print model and system information."""
        model_info = self.model_manager.get_model_info()

        info_lines = [
            f"**Configured Model:** {model_info['name']}",
        ]

        # Show actual loaded model if server is running
        if not self.config.is_using_external_api() and self.runtime.is_server_running():
            try:
                models = self.runtime.list_models()
                if models and len(models) > 0:
                    info_lines.append(f"**Loaded Model:** {models[0]['id']}")
            except Exception:
                pass

        info_lines.extend([
            f"**Path:** {model_info['path']}",
            f"**Downloaded:** {'Yes' if model_info['downloaded'] else 'No'}",
        ])

        if 'size_gb' in model_info:
            info_lines.append(f"**Size:** {model_info['size_gb']} GB")

        info_lines.extend([
            f"**Server Status:** {'Running' if self.runtime.is_server_running() else 'Stopped'}",
            f"\n**Inference Parameters:**",
            f"- Temperature: {self.config.inference_params['temperature']}",
            f"- Max Tokens: {self.config.inference_params['max_tokens']}",
            f"- Top P: {self.config.inference_params['top_p']}",
        ])

        info_text = "\n".join(info_lines)
        console.print(Panel(info_text, title="System Information", border_style="cyan"))

    def ensure_model_ready(self) -> bool:
        """
        Ensure model is downloaded and ready.

        For external APIs (OpenAI, Anthropic, etc.), this check is skipped
        since models are hosted remotely.

        Returns:
            True if model is ready, False otherwise.
        """
        # Skip model download check if using external API
        if self.config.is_using_external_api():
            logger.debug("Using external API, skipping model download check")
            return True

        # For local LLM, ensure model is downloaded
        if not self.model_manager.is_model_downloaded():
            console.print(f"[yellow]Model {self.config.model_name} is not downloaded.[/yellow]")
            console.print("[yellow]Downloading model... This may take a while.[/yellow]")

            try:
                self.model_manager.download_model()
                console.print("[green]Model downloaded successfully![/green]")
                return True
            except Exception as e:
                console.print(f"[red]Failed to download model: {e}[/red]")
                return False

        return True

    def start_server(self) -> bool:
        """
        Start LLM server.

        For external APIs (OpenAI, Anthropic, etc.), this is skipped
        since no local server is needed.

        Returns:
            True if server started successfully or not needed, False otherwise.
        """
        # Skip server start if using external API
        if self.config.is_using_external_api():
            logger.debug("Using external API, skipping local server start")
            return True

        # Check if local server is configured
        if not self.config.has_local_server_config():
            console.print(
                "[red]Error: Cannot start chat session[/red]\n"
                "Local LLM server is not configured and no server is running.\n\n"
                "Options:\n"
                "  1. Configure a local server:\n"
                "     [cyan]cp config_examples/config.local.gguf.example config.json[/cyan]\n"
                "  2. Use an external API (OpenAI, Anthropic):\n"
                "     [cyan]cp config_examples/config.openai.example config.json[/cyan]\n"
                "  3. Start server manually if configured:\n"
                "     [cyan]llf server start[/cyan]"
            )
            return False

        # Check if the active server is running (multi-server aware)
        # In multi-server setups, check if the default_local_server is running
        # In legacy setups, check if the default server is running
        is_running = False
        if self.config.default_local_server and isinstance(self.config.default_local_server, str) and self.config.get_server_by_name(self.config.default_local_server):
            # Multi-server mode: Check if the active server is running
            is_running = self.runtime.is_server_running_by_name(self.config.default_local_server)
        else:
            # Legacy mode: Check if default server is running
            is_running = self.runtime.is_server_running()

        if is_running:
            # Server is already running (started by another process)
            self.started_server = False
            return True

        # Check server control flags
        if self.no_server_start:
            console.print("[red]Server is not running and --no-server-start flag is set.[/red]")
            console.print("[yellow]Please start the server manually with: llf server start[/yellow]")
            return False

        # If auto-start is not enabled, prompt the user
        if not self.auto_start_server:
            console.print("[yellow]Server is not running.[/yellow]")
            # Determine which server will be started
            server_name = self.config.default_local_server if self.config.default_local_server else "default server"
            response = Prompt.ask(
                f"Would you like to start the server '{server_name}'?",
                choices=["y", "n"],
                default="y"
            )
            if response.lower() != 'y':
                console.print("[yellow]Server not started. Exiting.[/yellow]")
                return False

        console.print("[yellow]Starting LLM server...[/yellow]")
        console.print("[dim]This may take a minute or two...[/dim]")

        try:
            # Start the server specified in default_local_server, or default server if not set
            if self.config.default_local_server and isinstance(self.config.default_local_server, str) and self.config.get_server_by_name(self.config.default_local_server):
                self.runtime.start_server_by_name(self.config.default_local_server)
            else:
                self.runtime.start_server()
            console.print("[green]Server started successfully![/green]")
            self.started_server = True  # Mark that we started the server
            return True
        except Exception as e:
            console.print(f"[red]Failed to start server: {e}[/red]")
            logger.error(f"Server startup failed: {e}")
            return False

    def interactive_loop(self) -> None:
        """Run interactive chat loop."""
        self.running = True

        # Initialize conversation history from imported session if provided
        if self.imported_session and 'messages' in self.imported_session:
            conversation_history = self.imported_session['messages'].copy()
            console.print(f"[cyan]✓ Imported {len(conversation_history)} messages from previous session[/cyan]")
            if self.imported_session.get('metadata', {}).get('model'):
                console.print(f"[dim]Previous model: {self.imported_session['metadata']['model']}[/dim]")
            console.print(f"[dim]Current model: {self.config.model_name}[/dim]")
            console.print()
        else:
            conversation_history = []

        # Print initial separator before first user input
        console.print("[dim]" + "─" * 60 + "[/dim]")

        while self.running:
            try:
                # Print "You:" label on separate line with blank line after
                console.print("\n[green]You[/green]:\n")

                # Get user input - use STT if enabled, otherwise keyboard input
                if self.stt:
                    try:
                        console.print("[dim]🎤 Listening... (speak now, pause when done)[/dim]")
                        user_input = self.stt.listen()
                        console.print(f"[dim]Transcribed:[/dim] {user_input}")
                    except Exception as e:
                        logger.warning(f"Speech-to-Text error: {e}")
                        console.print("[yellow]⚠️  STT failed, falling back to keyboard input[/yellow]")
                        user_input = input()
                else:
                    user_input = input()

                if not user_input.strip():
                    continue

                # Check for multiline input mode
                if user_input.strip().upper() == "START":
                    console.print("[dim]Multiline input mode. Type your content and END on a new line when done.[/dim]")
                    lines = []
                    while True:
                        try:
                            line = input()
                            if line.strip().upper() == "END":
                                break
                            lines.append(line)
                        except EOFError:
                            break
                    user_input = "\n".join(lines)

                    if not user_input.strip():
                        console.print("[yellow]Empty multiline input, skipping.[/yellow]")
                        continue

                # Handle commands
                command = user_input.strip().lower()

                if command in ['exit', 'quit']:
                    console.print("\n[yellow]Goodbye![/yellow]")
                    break

                if command == 'help':
                    self.print_help()
                    continue

                if command == 'info':
                    self.print_info()
                    continue

                if command == 'clear':
                    console.clear()
                    self.print_welcome()
                    conversation_history = []  # Clear conversation history
                    continue

                # Print separator line
                console.print("[dim]" + "─" * 60 + "[/dim]")

                # Generate response with extra line after "Assistant:"
                console.print("\n[yellow]Assistant[/yellow]:\n")

                try:
                    # Build conversation context
                    conversation_history.append({
                        'role': 'user',
                        'content': user_input
                    })

                    # Generate response using chat API
                    # Check if tools are available
                    tools_available = False
                    if self.prompt_config:
                        tools = self.prompt_config.get_all_tools()
                        tools_available = tools is not None and len(tools) > 0

                    # Determine execution strategy based on configuration
                    from llf.operation_detector import detect_operation_type, should_use_dual_pass

                    operation_type = detect_operation_type(user_input)
                    use_dual_pass = should_use_dual_pass(
                        operation_type,
                        self.config.tool_execution_mode,
                        tools_available
                    )

                    if use_dual_pass:
                        # Dual-pass mode: Stream first for UX, then execute with tools in background
                        import threading

                        # Pass 1: Streaming response for user (no tools)
                        stream = self.runtime.chat(conversation_history, stream=True, use_prompt_config=False)

                        # Collect response chunks for history
                        response_chunks = []
                        for chunk in stream:
                            console.print(chunk, end="", markup=False)
                            response_chunks.append(chunk)

                        # Complete the line
                        console.print()

                        # Pass 2: Execute with tools in background (non-streaming)
                        # This runs after streaming completes to ensure tool execution happens
                        def execute_with_tools():
                            try:
                                # Run the same request with tools enabled
                                self.runtime.chat(conversation_history, stream=False)
                            except Exception as e:
                                logger.warning(f"Background tool execution failed: {e}")

                        # Execute in background thread
                        tool_thread = threading.Thread(target=execute_with_tools, daemon=True)
                        tool_thread.start()

                    elif tools_available:
                        # Single-pass mode with tools (no streaming, accurate)
                        response = self.runtime.chat(conversation_history, stream=False)
                        console.print(response, markup=False)
                        response_chunks = [response]
                    else:
                        # Streaming mode (no tools available)
                        stream = self.runtime.chat(conversation_history, stream=True)

                        # Collect response chunks for history
                        response_chunks = []
                        for chunk in stream:
                            console.print(chunk, end="", markup=False)
                            response_chunks.append(chunk)

                        # Complete the line
                        console.print()

                    # Combine chunks and add to history
                    full_response = "".join(response_chunks)
                    conversation_history.append({
                        'role': 'assistant',
                        'content': full_response
                    })

                    # Print separator line after response
                    console.print("\n[dim]" + "─" * 60 + "[/dim]")

                    # If TTS is enabled, speak the response BEFORE next loop iteration
                    # This ensures STT doesn't start listening until TTS finishes
                    if self.tts:
                        try:
                            # If STT is also enabled, ensure audio clearance before next input
                            if self.stt:
                                from .tts_stt_utils import wait_for_tts_clearance
                                console.print(f"[dim]🔊 Speaking...[/dim]")
                                wait_for_tts_clearance(self.tts, self.stt, full_response)
                                console.print(f"[dim]✅ Audio cleared, ready for next input[/dim]")
                            else:
                                # No STT enabled, just speak normally
                                self.tts.speak(full_response)
                        except Exception as e:
                            logger.warning(f"Text-to-Speech error: {e}")

                except Exception as e:
                    console.print(f"[red]Error generating response: {e}[/red]")
                    logger.error(f"Generation error: {e}")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Interactive loop error: {e}")

        # Save conversation history after loop ends
        if self.save_history and conversation_history and len(conversation_history) > 0:
            try:
                # Add timestamps to messages
                for msg in conversation_history:
                    if 'timestamp' not in msg:
                        msg['timestamp'] = datetime.now().isoformat()

                # Prepare metadata
                metadata = {
                    'model': self.config.model_name,
                    'timestamp': datetime.now().isoformat(),
                    'server_url': self.config.api_base_url
                }

                # Save to history
                filepath = self.chat_history.save_session(conversation_history, metadata)
                console.print(f"[dim]Conversation saved to: {filepath.name}[/dim]")
            except Exception as e:
                logger.warning(f"Failed to save chat history: {e}")

    def cli_question(self, question: str) -> int:
        """
        Handle non-interactive CLI question mode.

        Supports piped input: if stdin has data, it will be appended to the question.
        Example: cat file.txt | llf chat --cli "Summarize this"

        Args:
            question: The question to ask the LLM.

        Returns:
            Exit code (0 for success, non-zero for errors).
        """
        try:
            # Check if stdin has piped data
            if not sys.stdin.isatty():
                stdin_data = sys.stdin.read().strip()
                if stdin_data:
                    # Append stdin data to question as context
                    question = f"{question}\n\n{stdin_data}"
                    logger.debug(f"Appended {len(stdin_data)} bytes from stdin to question")

            # Ensure model is downloaded
            if not self.ensure_model_ready():
                return 1

            # Start server
            if not self.start_server():
                return 1

            # Build message for LLM
            messages = [{'role': 'user', 'content': question}]

            # Generate response (non-streaming for CLI mode)
            response = self.runtime.chat(messages, stream=False)

            # Print response
            console.print(response)

            # If TTS is enabled, speak the response
            if self.tts:
                try:
                    self.tts.speak(response)
                except Exception as e:
                    logger.warning(f"Text-to-Speech error: {e}")

            return 0

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logger.error(f"CLI question error: {e}")
            return 1

    def shutdown(self) -> None:
        """Cleanup and shutdown."""
        logger.info("Shutting down CLI...")
        # Only stop the server if this CLI instance started it
        if self.started_server:
            logger.info("Stopping server (started by this instance)...")
            self.runtime.stop_server()
        else:
            logger.info("Server was not started by this instance, leaving it running...")

    def run(self, cli_question: Optional[str] = None) -> int:
        """
        Run the CLI application.

        Args:
            cli_question: Optional question for non-interactive CLI mode.

        Returns:
            Exit code (0 for success, non-zero for errors).
        """
        try:
            # CLI mode: single question and exit
            if cli_question:
                return self.cli_question(cli_question)

            # Interactive mode
            # Ensure model is downloaded
            if not self.ensure_model_ready():
                return 1

            # Start server
            if not self.start_server():
                return 1

            # Print welcome message AFTER server is running
            self.print_welcome()

            # Run interactive loop
            self.interactive_loop()

            return 0

        except Exception as e:
            console.print(f"[red]Fatal error: {e}[/red]")
            logger.error(f"Fatal error: {e}")
            return 1

        finally:
            self.shutdown()


def download_command(args) -> int:
    """
    Handle download command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()
    model_manager = ModelManager(config)

    try:
        # Check if URL download or HuggingFace download
        if hasattr(args, 'url') and args.url:
            # URL download
            console.print(f"[yellow]Downloading from URL: {args.url}[/yellow]")
            console.print(f"[yellow]Saving as: {args.name}[/yellow]")

            model_path = model_manager.download_from_url(
                url=args.url,
                name=args.name,
                force=args.force
            )
            console.print(f"[green]Model downloaded successfully![/green]")
            console.print(f"[cyan]Path: {model_path}[/cyan]")

            # List files in the directory
            files = list(model_path.glob('*'))
            if files:
                console.print(f"[cyan]Downloaded files: {', '.join(f.name for f in files)}[/cyan]")

        else:
            # HuggingFace download
            model_name = args.huggingface_model or config.model_name
            token = getattr(args, 'token', None)

            console.print(f"[yellow]Downloading model: {model_name}[/yellow]")

            model_manager.download_model(
                model_name,
                force=args.force,
                token=token
            )
            console.print(f"[green]Model downloaded successfully![/green]")

            # Show model info
            info = model_manager.get_model_info(model_name)
            console.print(f"[cyan]Path: {info['path']}[/cyan]")
            if 'size_gb' in info:
                console.print(f"[cyan]Size: {info['size_gb']} GB[/cyan]")

        return 0

    except Exception as e:
        console.print(f"[red]Download failed: {e}[/red]")
        return 1


def list_command(args) -> int:
    """
    Handle list command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()
    model_manager = ModelManager(config)

    # If --imported flag is used, show only configured models
    if hasattr(args, 'imported') and args.imported:
        # Load current config to get imported models
        config_file = config.config_file or config.DEFAULT_CONFIG_FILE
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        # Check for multi-server config
        if 'local_llm_servers' in config_data:
            servers = config_data['local_llm_servers']

            if not servers:
                console.print("[yellow]No models currently imported in configuration.[/yellow]")
                console.print("[dim]Use 'llf model import MODEL_NAME' to import a model.[/dim]")
                return 0

            # Collect all unique models from servers
            # Convert model_dir format to HuggingFace format for display
            models_by_name = {}
            for server in servers:
                model_dir = server.get('model_dir')
                if model_dir:
                    # Convert format: "bartowski--Llama-3.3-70B-Instruct-GGUF" -> "bartowski/Llama-3.3-70B-Instruct-GGUF"
                    model_name = model_dir.replace('--', '/')
                    if model_name not in models_by_name:
                        models_by_name[model_name] = []
                    models_by_name[model_name].append({
                        'server_name': server.get('name', 'unknown'),
                        'model_dir': model_dir,
                        'gguf_file': server.get('gguf_file')
                    })

            if not models_by_name:
                console.print("[yellow]No models currently imported in configuration.[/yellow]")
                console.print("[dim]Use 'llf model import MODEL_NAME' to import a model.[/dim]")
                return 0

            # Display the imported models
            console.print("[bold]Imported Models (configured in config.json):[/bold]")

            for model_name, servers_info in sorted(models_by_name.items()):
                # Get size info if available
                size_str = ""
                if model_manager.is_model_downloaded(model_name):
                    info = model_manager.get_model_info(model_name)
                    if 'size_gb' in info:
                        size_str = f" ({info['size_gb']} GB)"

                console.print(f"  [green]✓[/green] {model_name}{size_str}")

                # Show which servers use this model
                if len(servers_info) == 1:
                    server_info = servers_info[0]
                    console.print(f"    [dim]Server:[/dim] {server_info['server_name']}")
                    if server_info['gguf_file']:
                        console.print(f"    [dim]GGUF File:[/dim] {server_info['gguf_file']}")
                else:
                    console.print(f"    [dim]Configured across {len(servers_info)} servers:[/dim]")
                    for server_info in servers_info:
                        console.print(f"      • {server_info['server_name']}")
                        if server_info['gguf_file']:
                            console.print(f"        GGUF File: {server_info['gguf_file']}")

        else:
            # Legacy single-server config
            configured_model = config_data.get('llm_endpoint', {}).get('model_name')

            if not configured_model:
                console.print("[yellow]No models currently imported in configuration.[/yellow]")
                console.print("[dim]Use 'llf model import MODEL_NAME' to import a model.[/dim]")
                return 0

            console.print("[bold]Imported Models (configured in config.json):[/bold]")

            # Get size info if available
            size_str = ""
            if model_manager.is_model_downloaded(configured_model):
                info = model_manager.get_model_info(configured_model)
                if 'size_gb' in info:
                    size_str = f" ({info['size_gb']} GB)"

            console.print(f"  [green]✓[/green] {configured_model}{size_str}")

        return 0

    # Default behavior: list all downloaded models
    models = model_manager.list_downloaded_models()

    if not models:
        console.print("[yellow]No models downloaded yet.[/yellow]")
        return 0

    console.print("[bold]Downloaded Models:[/bold]")
    for model in models:
        info = model_manager.get_model_info(model)
        size_str = f" ({info['size_gb']} GB)" if 'size_gb' in info else ""
        status = "[green]✓[/green]" if info['downloaded'] else "[red]✗[/red]"
        console.print(f"  {status} {model}{size_str}")

    return 0


def info_command(args) -> int:
    """
    Handle info command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()
    model_manager = ModelManager(config)

    model_name = args.model or config.model_name
    info = model_manager.get_model_info(model_name)

    console.print(Panel(
        f"""[bold]Model Information[/bold]

Name: {info['name']}
Path: {info['path']}
Downloaded: {'Yes' if info['downloaded'] else 'No'}
{'Size: ' + str(info['size_gb']) + ' GB' if 'size_gb' in info else ''}

Verification:
  - Exists: {'Yes' if info['verification']['exists'] else 'No'}
  - Has Config: {'Yes' if info['verification']['has_config'] else 'No'}
  - Has Tokenizer: {'Yes' if info['verification']['has_tokenizer'] else 'No'}
  - Has Weights: {'Yes' if info['verification']['has_weights'] else 'No'}
  - Valid: {'Yes' if info['verification']['valid'] else 'No'}
        """,
        title="Model Info",
        border_style="cyan"
    ))

    return 0


def delete_command(args) -> int:
    """
    Handle delete command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()
    model_manager = ModelManager(config)

    model_name = args.model_name

    # Check if model exists
    if not model_manager.is_model_downloaded(model_name):
        console.print(f"[red]Model '{model_name}' not found in models directory.[/red]")
        console.print(f"[yellow]Use 'llf model list' to see available models.[/yellow]")
        return 1

    # Get model info for confirmation
    info = model_manager.get_model_info(model_name)
    model_path = info['path']

    # Ask for confirmation unless --force is used
    if not args.force:
        console.print(f"[yellow]Are you sure you want to delete model '{model_name}'?[/yellow]")
        console.print(f"[dim]Path: {model_path}[/dim]")
        if 'size_gb' in info:
            console.print(f"[dim]Size: {info['size_gb']} GB[/dim]")

        confirm = Prompt.ask("[yellow]Type 'yes' to confirm[/yellow]", default="no")

        if confirm.lower() != 'yes':
            console.print("[cyan]Deletion cancelled.[/cyan]")
            return 0

    # Delete the model
    if model_manager.delete_model(model_name):
        console.print(f"[green]Successfully deleted model '{model_name}'.[/green]")
        return 0
    else:
        console.print(f"[red]Failed to delete model '{model_name}'.[/red]")
        return 1


def import_model_command(args) -> int:
    """
    Handle model import command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    import glob
    from datetime import datetime

    config = get_config()
    model_manager = ModelManager(config)

    model_name = args.model_name

    # Check if model exists
    if not model_manager.is_model_downloaded(model_name):
        console.print(f"[red]Model '{model_name}' not found in models directory.[/red]")
        console.print(f"[yellow]Use 'llf model list' to see available models.[/yellow]")
        return 1

    # Get model info
    info = model_manager.get_model_info(model_name)
    model_path = Path(info['path'])

    # Find Q5_K_M GGUF file in the model directory (case-insensitive)
    gguf_files = []
    for file in model_path.glob("*.gguf"):
        if "q5_k_m" in file.name.lower():
            gguf_files.append(str(file))

    if not gguf_files:
        console.print(f"[red]No Q5_K_M GGUF file found in {model_path}[/red]")
        console.print(f"[yellow]Looking for files matching pattern: *Q5_K_M*.gguf (case-insensitive)[/yellow]")
        return 1

    # Sort files to ensure we get the first one in multi-part series
    # Files like "model-q5_k_m-00001-of-00006.gguf" should come before "model-q5_k_m-00006-of-00006.gguf"
    gguf_files.sort()

    if len(gguf_files) > 1:
        console.print(f"[yellow]Multiple Q5_K_M GGUF files found:[/yellow]")
        for f in gguf_files:
            console.print(f"  - {Path(f).name}")
        console.print(f"[yellow]Selecting first file in series: {Path(gguf_files[0]).name}[/yellow]")

    gguf_file = Path(gguf_files[0]).name
    model_dir_name = model_path.name

    # Load current config
    config_file = config.config_file or config.DEFAULT_CONFIG_FILE
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    # Create backup
    backup_path = config.backup_config(config_file)
    console.print(f"[green]✓[/green] Backup created: {backup_path}")

    # Auto-detect and handle multi-server configuration
    if 'local_llm_servers' not in config_data:
        console.print(f"[red]Configuration does not have 'local_llm_servers' section.[/red]")
        console.print(f"[yellow]This configuration file is not in the expected multi-server format.[/yellow]")
        return 1

    # Multi-server configuration exists
    # Generate a unique server name based on the model
    server_name = model_name.split('/')[-1].lower().replace('-gguf', '').replace('/', '-')

    # Check if there's a default server with null model fields (first import case)
    default_server_with_null_model = None
    for server in config_data['local_llm_servers']:
        if (server.get('name') == 'default' and
            server.get('model_dir') is None and
            server.get('gguf_file') is None):
            default_server_with_null_model = server
            break

    # Check if a server with this model already exists
    existing_server = None
    for server in config_data['local_llm_servers']:
        if server.get('model_dir') == model_dir_name:
            existing_server = server
            break

    if existing_server:
        # Update existing server with the new GGUF file
        existing_server['gguf_file'] = gguf_file
        console.print(f"[green]✓[/green] Updated existing server '{existing_server['name']}' with new GGUF file")
        console.print(f"  Model Directory: {model_dir_name}")
        console.print(f"  GGUF File: {gguf_file}")
    elif default_server_with_null_model:
        # This is the first import - update the default server
        default_server_with_null_model['model_dir'] = model_dir_name
        default_server_with_null_model['gguf_file'] = gguf_file
        console.print(f"[green]✓[/green] Updated default server with first model")
        console.print(f"  Server Name: default")
        console.print(f"  Server Port: {default_server_with_null_model['server_port']}")
        console.print(f"  Model Directory: {model_dir_name}")
        console.print(f"  GGUF File: {gguf_file}")
    else:
        # Add a new server for this model
        # Find next available port
        used_ports = {server.get('server_port', 8000) for server in config_data['local_llm_servers']}
        next_port = 8000
        while next_port in used_ports:
            next_port += 1

        # Ensure unique server name
        existing_names = {server['name'] for server in config_data['local_llm_servers']}
        base_name = server_name
        counter = 1
        while server_name in existing_names:
            server_name = f"{base_name}-{counter}"
            counter += 1

        new_server = {
            'name': server_name,
            'llama_server_path': config_data['local_llm_servers'][0].get('llama_server_path', '../llama.cpp/build/bin/llama-server'),
            'server_host': '127.0.0.1',
            'server_port': next_port,
            'healthcheck_interval': 2.0,
            'auto_start': False,
            'model_dir': model_dir_name,
            'gguf_file': gguf_file
        }

        config_data['local_llm_servers'].append(new_server)

        console.print(f"[green]✓[/green] Added new server to multi-server configuration")
        console.print(f"  Server Name: {server_name}")
        console.print(f"  Server Port: {next_port}")
        console.print(f"  Model Directory: {model_dir_name}")
        console.print(f"  GGUF File: {gguf_file}")
        console.print(f"  Total Servers: {len(config_data['local_llm_servers'])}")

    # Note: We do NOT update llm_endpoint.model_name here
    # The model_name should only be updated via 'llf server switch' command

    # Save updated configuration
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    console.print(f"[green]✓[/green] Configuration saved: {config_file}")
    console.print(f"\n[cyan]Model '{model_name}' imported successfully![/cyan]")

    return 0


def export_model_command(args) -> int:
    """
    Handle model export command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from datetime import datetime

    config = get_config()
    model_name = args.model_name  # In HuggingFace format: "Qwen/Qwen2.5-32B-Instruct-GGUF"

    # Load current config
    config_file = config.config_file or config.DEFAULT_CONFIG_FILE
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    # Auto-detect and handle multi-server configuration
    if 'local_llm_servers' not in config_data:
        console.print(f"[red]Configuration does not have 'local_llm_servers' section.[/red]")
        console.print(f"[yellow]This configuration file is not in the expected multi-server format.[/yellow]")
        return 1

    # Convert HuggingFace format to directory format for matching
    # "Qwen/Qwen2.5-32B-Instruct-GGUF" -> "Qwen--Qwen2.5-32B-Instruct-GGUF"
    model_dir_format = model_name.replace('/', '--')

    # Find ALL servers that use this model
    servers_to_remove = []
    for i, server in enumerate(config_data['local_llm_servers']):
        server_model_dir = server.get('model_dir')
        if server_model_dir:
            # Extract just the directory name if it's a path
            if isinstance(server_model_dir, str):
                dir_name = server_model_dir.split('/')[-1]
            else:
                dir_name = str(server_model_dir)

            if dir_name == model_dir_format:
                servers_to_remove.append(i)

    if not servers_to_remove:
        console.print(f"[yellow]No servers found with model '{model_name}'.[/yellow]")
        console.print(f"[yellow]Nothing to export.[/yellow]")
        return 0

    # Create backup
    backup_path = config.backup_config(config_file)
    console.print(f"[green]✓[/green] Backup created: {backup_path}")

    # Check if we're removing all servers
    remaining_servers = len(config_data['local_llm_servers']) - len(servers_to_remove)

    if remaining_servers == 0:
        # This is the LAST model - reset the last server to default state
        # Keep the first server and reset it
        first_server = config_data['local_llm_servers'][0]
        first_server['model_dir'] = None
        first_server['gguf_file'] = None
        first_server['name'] = 'default'
        first_server['server_port'] = 8000

        # Remove all other servers
        config_data['local_llm_servers'] = [first_server]

        console.print(f"[green]✓[/green] Exported last model from configuration")
        console.print(f"  Model: {model_name}")
        console.print(f"  Reset to default server configuration (port 8000)")
    else:
        # Remove servers in reverse order to maintain indices
        for idx in reversed(servers_to_remove):
            removed_server = config_data['local_llm_servers'].pop(idx)
            console.print(f"[green]✓[/green] Removed server '{removed_server['name']}' from configuration")

        console.print(f"  Model: {model_name}")
        console.print(f"  Servers removed: {len(servers_to_remove)}")
        console.print(f"  Remaining servers: {remaining_servers}")

    # Clear model_name if we removed all servers or if it matches the exported model
    current_model_name = config_data.get('llm_endpoint', {}).get('model_name')
    if remaining_servers == 0 or current_model_name == model_name:
        config_data['llm_endpoint']['model_name'] = None

    # Save updated configuration
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    console.print(f"[green]✓[/green] Configuration saved: {config_file}")
    console.print(f"\n[cyan]Model configuration removed successfully![/cyan]")

    return 0


def server_command(args) -> int:
    """
    Handle server command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()

    # Commands that require local server configuration
    local_server_required = ['start', 'stop', 'restart', 'status']

    # Check if local server is configured for commands that require it
    if args.action in local_server_required and args.action != 'status':
        # status gets special handling below
        if not config.has_local_server_config():
            console.print(
                "[yellow]A local LLM server is not configured.[/yellow]\n"
                f"Command '[cyan]llf server {args.action}[/cyan]' requires a local llama-server setup.\n\n"
                "To use a local server:\n"
                "  1. Compile llama.cpp (see README)\n"
                "  2. Configure local_llm_server section in config.json\n"
                "  3. Use: [cyan]cp config_examples/config.local.gguf.example config.json[/cyan]\n\n"
                "Or use a cloud API instead:\n"
                "  • OpenAI: [cyan]cp config_examples/config.openai.example config.json[/cyan]\n"
                "  • Anthropic: [cyan]cp config_examples/config.anthropic.example config.json[/cyan]"
            )
            return 1

    # Override model settings if specified via CLI flags
    if hasattr(args, 'huggingface_model') and args.huggingface_model:
        config.model_name = args.huggingface_model
        config.custom_model_dir = None  # Clear custom dir when using HF model
    elif hasattr(args, 'gguf_dir') and args.gguf_dir and hasattr(args, 'gguf_file') and args.gguf_file:
        # Set custom model directory and GGUF file
        config.custom_model_dir = config.model_dir / args.gguf_dir
        config.gguf_file = args.gguf_file

    model_manager = ModelManager(config)
    runtime = LLMRuntime(config, model_manager)

    try:
        # New multi-server commands
        if args.action == 'list':
            return list_servers_command(config, runtime)

        elif args.action == 'switch':
            return switch_server_command(config, args)

        elif args.action == 'status':
            return status_server_command(config, runtime, args)

        elif args.action == 'start':
            return start_server_command(config, runtime, model_manager, args)

        elif args.action == 'stop':
            return stop_server_command(config, runtime, args)

        elif args.action == 'restart':
            # Restart server - use default_local_server if set
            default_server_name = config.default_local_server

            if default_server_name and isinstance(default_server_name, str) and config.get_server_by_name(default_server_name):
                # Restart the configured default server
                console.print(f"[yellow]Restarting default server '{default_server_name}'...[/yellow]")

                if runtime.is_server_running_by_name(default_server_name):
                    console.print("[dim]Stopping current server...[/dim]")
                    runtime.stop_server_by_name(default_server_name)

                console.print("[dim]Starting server...[/dim]")
                runtime.start_server_by_name(default_server_name)

                server_config = config.get_server_by_name(default_server_name)
                console.print(f"[green]✓ Server '{default_server_name}' restarted successfully[/green]")
                console.print(f"[cyan]URL: http://{server_config.server_host}:{server_config.server_port}/v1[/cyan]")
                return 0

            # Fallback to legacy mode if no default_local_server is set
            console.print("[yellow]Restarting server...[/yellow]")

            if runtime.is_server_running():
                console.print("[dim]Stopping current server...[/dim]")
                runtime.stop_server()

            # Ensure model is downloaded
            if not model_manager.is_model_downloaded():
                console.print(f"[yellow]Model {config.model_name} is not downloaded.[/yellow]")
                console.print("[yellow]Downloading model... This may take a while.[/yellow]")
                try:
                    model_manager.download_model()
                    console.print("[green]Model downloaded successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Failed to download model: {e}[/red]")
                    return 1

            # Determine server host based on --share flag
            server_host = "0.0.0.0" if args.share else None  # None uses config default (127.0.0.1)

            console.print("[dim]Starting server...[/dim]")
            runtime.start_server(server_host=server_host)

            # Display appropriate access message
            if args.share:
                console.print(f"[green]✓ Server restarted successfully on 0.0.0.0:{config.server_port}[/green]")
                console.print(f"[cyan]Access from network: http://YOUR_IP:{config.server_port}/v1[/cyan]")
            else:
                console.print(f"[green]✓ Server restarted successfully on {config.get_server_url()}[/green]")
            return 0

        elif args.action == 'list_models':
            # List available models from the endpoint
            if config.has_local_server_config():
                console.print(f"[cyan]Querying models from local server: {config.api_base_url}...[/cyan]")
            else:
                console.print(f"[cyan]Querying models from external API: {config.api_base_url}...[/cyan]")
            try:
                models = runtime.list_models()

                if not models:
                    console.print("[yellow]No models found[/yellow]")
                    return 0

                console.print(f"\n[green]✓ Found {len(models)} model(s):[/green]\n")

                # Display models in a table
                from rich.table import Table
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Model ID", style="green")
                table.add_column("Type", style="dim")
                table.add_column("Owner", style="dim")

                for model in models:
                    table.add_row(
                        model.get('id', 'N/A'),
                        model.get('object', 'N/A'),
                        model.get('owned_by', 'N/A')
                    )

                console.print(table)
                console.print(f"\n[dim]To use a model, update the 'model_name' in config.json under 'llm_endpoint'[/dim]")
                return 0

            except Exception as e:
                console.print(f"[red]Failed to list models: {e}[/red]")
                console.print("[yellow]Tip: Make sure the API endpoint is accessible and configured correctly[/yellow]")
                return 1

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Server command error: {e}")
        return 1


def prompt_command(args) -> int:
    """
    Handle prompt template command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    config = get_config()

    # Default to 'list' if no action provided
    action = args.action if args.action else 'list'

    # Route to appropriate command handler
    if action == 'list':
        return list_templates_command(config, args)
    elif action == 'info':
        return info_template_command(config, args)
    elif action == 'load':
        return load_template_command(config, args)
    elif action == 'import':
        return import_template_command(config, args)
    elif action == 'export':
        return export_template_command(config, args)
    elif action == 'enable':
        return enable_template_command(config, args)
    elif action == 'disable':
        return disable_template_command(config, args)
    elif action == 'backup':
        return backup_templates_command(config, args)
    elif action == 'delete':
        return delete_template_command(config, args)
    elif action == 'create':
        return create_template_command(config, args)
    elif action == 'active':
        return show_active_template_command(config, args)
    else:
        console.print(f"[red]Error:[/red] Unknown action '{action}'")
        console.print("[dim]Available actions: list, info, load, import, export, enable, disable, backup, delete, create, active[/dim]")
        return 1


def chat_history_list_command(config: Config, args) -> int:
    """
    List saved chat sessions.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from llf.chat_history import ChatHistory
    from rich.table import Table

    # Initialize chat history manager
    history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
    chat_history = ChatHistory(history_dir)

    # Get filter options
    days = getattr(args, 'days', None)
    limit = getattr(args, 'limit', None)

    # List sessions
    sessions = chat_history.list_sessions(limit=limit, days=days)

    if not sessions:
        console.print("[yellow]No chat sessions found[/yellow]")
        if days:
            console.print(f"[dim]No sessions in the last {days} days[/dim]")
        return 0

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("SESSION ID", style="green")
    table.add_column("DATE", style="cyan")
    table.add_column("MESSAGES", style="yellow")
    table.add_column("MODEL", style="dim")

    for session in sessions:
        # Parse timestamp
        timestamp = datetime.fromisoformat(session['timestamp'])
        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Get model name
        model_name = session['metadata'].get('model', 'Unknown')

        table.add_row(
            session['session_id'],
            date_str,
            str(session['message_count']),
            model_name
        )

    console.print(table)

    # Show total size
    total_size = chat_history.get_total_size()
    size_mb = total_size / (1024 * 1024)
    console.print(f"\n[dim]Total history size: {size_mb:.2f} MB[/dim]")
    console.print(f"[dim]History directory: {history_dir}[/dim]")

    return 0


def chat_history_info_command(config: Config, args) -> int:
    """
    Display detailed information about a chat session.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from llf.chat_history import ChatHistory
    from rich.panel import Panel
    from rich.markdown import Markdown

    session_id = args.session_id

    # Initialize chat history manager
    history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
    chat_history = ChatHistory(history_dir)

    # Load the session
    session_data = chat_history.load_session(session_id)
    if not session_data:
        console.print(f"[red]Session not found: {session_id}[/red]")
        console.print("[dim]Use 'llf chat history list' to see available sessions[/dim]")
        return 1

    # Display session header
    metadata = session_data.get('metadata', {})
    timestamp = session_data.get('timestamp', 'Unknown')
    try:
        dt = datetime.fromisoformat(timestamp)
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        timestamp_str = timestamp

    header = f"""[bold cyan]Session ID:[/bold cyan] {session_id}
[bold cyan]Date:[/bold cyan] {timestamp_str}
[bold cyan]Model:[/bold cyan] {metadata.get('model', 'Unknown')}
[bold cyan]Messages:[/bold cyan] {session_data.get('message_count', len(session_data.get('messages', [])))}"""

    console.print(Panel(header, title="Chat Session Info", border_style="cyan"))
    console.print()

    # Display conversation
    messages = session_data.get('messages', [])

    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', '')

        # Format role header
        if role == 'user':
            role_display = "👤 User"
            style = "bold green"
            border_style = "green"
        elif role == 'assistant':
            role_display = "🤖 Assistant"
            style = "bold blue"
            border_style = "blue"
        elif role == 'system':
            role_display = "⚙️ System"
            style = "bold yellow"
            border_style = "yellow"
        else:
            role_display = f"❓ {role.title()}"
            style = "bold white"
            border_style = "white"

        # Create message header
        header_parts = [f"[{style}]{role_display}[/{style}]"]
        if timestamp:
            header_parts.append(f"[dim]{timestamp}[/dim]")

        # Display message
        console.print(" ".join(header_parts))
        console.print(Panel(content, border_style=border_style, padding=(0, 1)))
        console.print()

    # Show footer with actions
    console.print("[dim]─" * 80 + "[/dim]")
    console.print(f"[dim]Actions:[/dim]")
    console.print(f"  • Continue this conversation: [cyan]llf chat --continue-session {session_id}[/cyan]")
    console.print(f"  • Export to file: [cyan]llf chat export {session_id}[/cyan]")
    console.print()

    return 0


def chat_history_cleanup_command(config: Config, args) -> int:
    """
    Cleanup old chat sessions (bulk operation).

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from llf.chat_history import ChatHistory

    # Initialize chat history manager
    history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
    chat_history = ChatHistory(history_dir)

    # Get options
    days = args.days
    dry_run = getattr(args, 'dry_run', False)

    # Confirm if not dry run
    if not dry_run:
        console.print(f"[yellow]This will delete all chat sessions older than {days} days.[/yellow]")
        response = input("Are you sure? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            console.print("[dim]Cancelled[/dim]")
            return 0

    # Purge sessions
    deleted_count = chat_history.purge_old_sessions(days=days, dry_run=dry_run)

    if dry_run:
        console.print(f"\n[cyan]Dry run complete: {deleted_count} sessions would be deleted[/cyan]")
    else:
        console.print(f"\n[green]✓ Cleaned up {deleted_count} sessions[/green]")

    return 0


def chat_history_delete_command(config: Config, args) -> int:
    """
    Delete a specific chat session (move to trash).

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from llf.chat_history import ChatHistory

    # Initialize chat history manager
    history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
    chat_history = ChatHistory(history_dir)

    # Initialize trash manager
    project_root = Path(__file__).parent.parent
    trash_dir = project_root / 'trash'
    trash_manager = TrashManager(trash_dir)

    # Get session ID
    session_id = args.session_id

    # Load session to verify it exists
    session_data = chat_history.load_session(session_id)
    if not session_data:
        console.print(f"[red]Session '{session_id}' not found[/red]")
        console.print("[dim]Use 'llf chat history list' to see available sessions[/dim]")
        return 1

    # Get session file path
    session_file = history_dir / f"{session_id}.json"

    if not session_file.exists():
        console.print(f"[red]Session file not found: {session_file}[/red]")
        return 1

    # Move to trash
    success, trash_id = trash_manager.move_to_trash(
        item_type='chat_history',
        item_name=session_id,
        paths=[session_file],
        original_metadata={
            'session_id': session_id,
            'title': session_data.get('title', 'No title'),
            'timestamp': session_data.get('timestamp', 'Unknown')
        }
    )

    if not success:
        console.print(f"[red]Error:[/red] Failed to move session to trash: {trash_id}")
        return 1

    console.print()
    console.print(f"[green]✓[/green] Chat session '{session_id}' moved to trash")
    console.print()
    console.print(f"[bold]Trash ID:[/bold] {trash_id}")
    console.print()
    console.print("[bold]Recovery Options:[/bold]")
    console.print(f"  - View trash: [cyan]llf trash list[/cyan]")
    console.print(f"  - Restore: [cyan]llf trash restore {trash_id}[/cyan]")
    console.print()
    console.print("[dim]Items in trash are automatically deleted after 30 days[/dim]")
    console.print()

    return 0


def chat_export_command(config: Config, args) -> int:
    """
    Export a chat session to a file.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    from llf.chat_history import ChatHistory
    from llf.chat_exporters import get_exporter

    # Initialize chat history manager
    history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
    chat_history = ChatHistory(history_dir)

    # Get session
    session_id = args.session_id
    session_data = chat_history.load_session(session_id)

    if not session_data:
        console.print(f"[red]Session '{session_id}' not found[/red]")
        console.print("[dim]Use 'llf chat history list' to see available sessions[/dim]")
        return 1

    # Get export options
    export_format = args.format
    output_path = args.output
    include_timestamps = not getattr(args, 'no_timestamps', False)
    include_system = not getattr(args, 'no_system', False)

    # Generate default output filename if not specified
    if not output_path:
        extension_map = {
            'markdown': 'md',
            'md': 'md',
            'json': 'json',
            'txt': 'txt',
            'text': 'txt',
            'pdf': 'pdf'
        }
        ext = extension_map.get(export_format, 'txt')
        output_path = f"chat_{session_id}.{ext}"

    output_path = Path(output_path)

    try:
        # Get exporter and export
        exporter = get_exporter(export_format, include_timestamps=include_timestamps, include_system=include_system)
        exporter.export(session_data, output_path)

        console.print(f"[green]✓ Exported session to: {output_path}[/green]")
        console.print(f"[dim]Format: {export_format}[/dim]")
        return 0

    except ImportError as e:
        console.print(f"[red]Export failed: {e}[/red]")
        if 'reportlab' in str(e):
            console.print("[yellow]Install reportlab for PDF export: pip install reportlab[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        return 1


def main():
    """Main entry point for CLI application."""
    parser = argparse.ArgumentParser(
        prog='llf',
        description='Local LLM Framework - Run LLMs locally with llama.cpp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chat commands (interactive mode)
  llf                              Start interactive chat (default)
  llf chat                         Start interactive chat (prompts to start server if not running)
  llf chat --auto-start-server     Auto-start server if not running (no prompt)
  llf chat --no-server-start       Exit with error if server not running
  llf chat --no-history            Start chat without saving conversation history
  llf chat --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf chat --gguf-dir test_gguf --gguf-file my-model.gguf

  # CLI mode (non-interactive, for scripting)
  llf chat --cli "What is 2+2?"                    Ask a single question and exit
  llf chat --cli "Explain Python" --auto-start-server
  llf chat --cli "Code review" --huggingface-model custom/model
  cat file.txt | llf chat --cli "Summarize this"  Pipe data to LLM with question

  # Resume and import conversations
  llf chat --continue-session SESSION_ID           Continue from a saved session
  llf chat --continue-session SESSION_ID --no-history  Resume without saving new history
  llf chat --import-session path/to/chat.json      Import external session from JSON
  llf chat --import-session path/to/chat.md        Import external session from Markdown
  llf chat --import-session path/to/chat.txt       Import external session from text

  # Chat history management
  llf chat history list                            List all saved chat sessions
  llf chat history list --days 7                   List sessions from last 7 days
  llf chat history list --limit 10                 List last 10 sessions
  llf chat history info SESSION_ID                 Display full conversation content
  llf chat history delete SESSION_ID               Delete a specific session (move to trash)
  llf chat history cleanup --days 30               Delete sessions older than 30 days (bulk)
  llf chat history cleanup --days 30 --dry-run     Preview what would be deleted

  # Chat export
  llf chat export SESSION_ID                       Export session to Markdown
  llf chat export SESSION_ID --format json         Export as JSON
  llf chat export SESSION_ID --format pdf          Export as PDF
  llf chat export SESSION_ID --output chat.md      Export to specific file
  llf chat export SESSION_ID --no-timestamps       Export without timestamps
  llf chat export SESSION_ID --no-system           Export without system messages

  # Local Server management
  llf server list                              List all configured servers and status
  llf server start                             Start default server (localhost, foreground)
  llf server start LOCAL_SERVER_NAME           Start specific server by name
  llf server start --force                     Start without memory safety prompt
  llf server start --share                     Start server on local network (0.0.0.0)
  llf server start --daemon                    Start server in background
  llf server start --share --daemon            Start server in background (network accessible)
  llf server start --huggingface-model MODEL   Start with specific model
  llf server start --gguf-dir DIR --gguf-file FILE  Start with custom GGUF file
  llf server stop                              Stop default server
  llf server stop LOCAL_SERVER_NAME            Stop specific server by name
  llf server status                            Check default server status
  llf server status LOCAL_SERVER_NAME          Check specific server status
  llf server restart                           Restart default server
  llf server restart --share                   Restart server with network access
  llf server switch LOCAL_SERVER_NAME          Switch default server
  llf server list_models                       List available models from configured endpoint

  # Model management
  llf model download               Download default HuggingFace model
  llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf model download --url https://example.com/model.gguf --name my-model
  llf model list                   List all downloaded models
  llf model list --imported        List models configured in config.json
  llf model info                   Show default model information
  llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf model delete MODEL_NAME      Delete a model and all its contents
  llf model import MODEL_NAME      Import model to config
  llf model export MODEL_NAME      Remove model from config

  # GUI interface
  llf gui                          Start web-based GUI (localhost only, port 7860)
  llf gui start                    Start web-based GUI (same as above)
  llf gui start --daemon           Start GUI in background (daemon mode)
  llf gui start --share            Start GUI accessible on local network (0.0.0.0)
  llf gui start --key MY_SECRET    Start GUI with authentication (requires secret key)
  llf gui start --share --key PASSWORD  Network-accessible GUI with authentication
  llf gui start --port 8080        Start GUI on custom port
  llf gui start --no-browser       Start GUI without opening browser
  llf gui stop                     Stop GUI daemon process
  llf gui status                   Check if GUI daemon is running

  # Data Store management
  llf datastore list                      List all available data stores
  llf datastore list --attached           List only attached data stores
  llf datastore import DIRECTORY_NAME     Import vector store from data_stores/vector_stores
  llf datastore export DATA_STORE_NAME    Export data store (remove from registry, keep data)
  llf datastore attach DATA_STORE_NAME    Attach data store to query
  llf datastore attach all                Attach all data stores
  llf datastore detach DATA_STORE_NAME    Detach data store
  llf datastore detach all                Detach all data stores
  llf datastore info DATA_STORE_NAME      Show data store information

  # Memory management
  llf memory list                         List all memory instances
  llf memory list --enabled               List only enabled memory instances
  llf memory create MEMORY_NAME           Create a new memory instance
  llf memory enable MEMORY_NAME           Enable a memory instance
  llf memory disable MEMORY_NAME          Disable a memory instance
  llf memory delete MEMORY_NAME           Delete a memory instance (must be disabled)
  llf memory info MEMORY_NAME             Show memory instance information

  # Module management
  llf module list                  List modules
  llf module list --enabled        List only enabled modules
  llf module enable MODULE_NAME    Enable a module
  llf module enable all            Enable all modules
  llf module disable MODULE_NAME   Disable a module
  llf module disable all           Disable all modules
  llf module info MODULE_NAME      Show module information

  # Tool management
  llf tool list                    List tools
  llf tool list --enabled          List only enabled tools
  llf tool enable TOOL_NAME        Enable a tool
  llf tool disable TOOL_NAME       Disable a tool
  llf tool info TOOL_NAME          Show tool information
  llf tool whitelist list TOOL_NAME           List whitelisted patterns for a tool
  llf tool whitelist add TOOL_NAME PATTERN    Add pattern to tool whitelist
  llf tool whitelist remove TOOL_NAME INDEX   Remove pattern from tool whitelist by index

  # Prompt Template management
  llf prompt list                             List all prompt templates
  llf prompt list --category development      List templates by category
  llf prompt list --enabled                   List only enabled templates
  llf prompt info coding_assistant            Show detailed template information
  llf prompt load coding_assistant            Load and apply template to active config
  llf prompt load socratic_tutor --var topic=Python   Load with variable substitution
  llf prompt create                           Create new template interactively
  llf prompt backup                           Backup all templates before changes
  llf prompt active                           Show currently active template

  # Global Configuration Flags (use with any command)
  llf --log-level DEBUG chat                           Enable debug logging for chat
  llf --log-level DEBUG --log-file debug.log chat      Log chat session to file
  llf server start --log-level DEBUG --log-file server.log  Debug server startup
  llf -d /custom/models model download                 Download to custom directory
  llf --config myconfig.json server start              Use different config file

Note: Requires llama.cpp compiled with llama-server binary.
For setup instructions, see: https://github.com/ggml-org/llama.cpp
        """
    )

    # Global arguments
    parser.add_argument(
        '-d', '--download-dir',
        type=Path,
        metavar='PATH',
        help='Directory for downloading and storing models (default: ./models/)'
    )

    parser.add_argument(
        '-c', '--config',
        type=Path,
        metavar='FILE',
        help='Path to configuration JSON file'
    )

    parser.add_argument(
        '--cache-dir',
        type=Path,
        metavar='PATH',
        help='Directory for model cache (default: ./.cache/)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        metavar='LEVEL',
        help='Set logging level (default: from config or INFO)'
    )

    parser.add_argument(
        '--log-file',
        type=Path,
        metavar='PATH',
        help='Path to log file. If specified, logs to both console and file.'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.2.0 (Phase 1)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        metavar='COMMAND',
        help='Available commands (default: chat)'
    )

    # Chat command (default)
    chat_parser = subparsers.add_parser(
        'chat',
        help='Start interactive chat with LLM or manage chat history',
        description='Start an interactive chat session with an LLM either locally running or remote, or manage chat history.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  llf chat                                     Start interactive chat session
  llf chat --auto-start-server                 Auto-start server if not running
  llf chat --no-server-start                   Exit with error if server not running
  llf chat --no-history                        Disable saving conversation history

  # CLI mode (non-interactive, for scripting)
  llf chat --cli "What is 2+2?"                Ask a single question and exit
  cat file.txt | llf chat --cli "Summarize this"  Pipe data to LLM with question

  # Resume and import conversations
  llf chat --continue-session SESSION_ID       Continue from a saved session ID
  llf chat --import-session path/to/chat.json  Import external session (JSON/MD/TXT)

  # Chat history management
  llf chat history list                        List saved chat sessions
  llf chat history list --days 7               List sessions from last 7 days
  llf chat history info SESSION_ID             Display full conversation content
  llf chat history delete SESSION_ID           Delete a specific session (move to trash)
  llf chat history cleanup --days 30           Delete sessions older than 30 days (bulk)
  llf chat history cleanup --days 30 --dry-run Preview what would be deleted

  # Export conversations
  llf chat export SESSION_ID                   Export session to markdown (default)
  llf chat export SESSION_ID --format json     Export to JSON format
  llf chat export SESSION_ID --format pdf --output chat.pdf
  llf chat export SESSION_ID --no-timestamps   Export without timestamps

  # Model selection
  llf chat --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf chat --gguf-dir test_gguf --gguf-file my-model.gguf
        """
    )

    # Model selection (mutually exclusive)
    model_group = chat_parser.add_argument_group(
        'Model Selection',
        'Specify model location (choose one method)'
    )
    model_group.add_argument(
        '--huggingface-model',
        metavar='NAME',
        help='HuggingFace model identifier (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"). Uses models/{sanitized_name}/ structure.'
    )
    model_group.add_argument(
        '--gguf-dir',
        metavar='DIR',
        help='GGUF model directory within models/ (e.g., "test_gguf"). Must be used with --gguf-file.'
    )
    model_group.add_argument(
        '--gguf-file',
        metavar='FILE',
        help='GGUF model filename (e.g., "model.gguf"). Must be used with --gguf-dir.'
    )

    chat_parser.add_argument(
        '--auto-start-server',
        action='store_true',
        help='Automatically start server if not running (skip interactive prompt)'
    )
    chat_parser.add_argument(
        '--no-server-start',
        action='store_true',
        help='Do not start server if not running (exit with error instead)'
    )
    chat_parser.add_argument(
        '--no-history',
        action='store_true',
        help='Disable saving conversation history for this session'
    )
    chat_parser.add_argument(
        '--continue-session',
        metavar='SESSION_ID',
        help='Continue a previous conversation from a saved session ID'
    )
    chat_parser.add_argument(
        '--import-session',
        metavar='FILE',
        help='Import and continue from an external session file (.json, .md, .txt)'
    )
    chat_parser.add_argument(
        '--cli',
        metavar='QUESTION',
        help='Non-interactive mode: ask a single question and exit (for scripting)'
    )

    # Chat subcommands for history and export management
    chat_subparsers = chat_parser.add_subparsers(
        dest='chat_action',
        metavar='ACTION',
        help='Chat management actions (history, export)'
    )

    # chat history command
    history_parser = chat_subparsers.add_parser(
        'history',
        help='Manage chat history',
        description='List, view, and purge saved chat sessions'
    )
    history_subparsers = history_parser.add_subparsers(
        dest='history_action',
        required=True,
        metavar='ACTION',
        help='History actions'
    )

    # history list
    list_history_parser = history_subparsers.add_parser(
        'list',
        help='List saved chat sessions'
    )
    list_history_parser.add_argument(
        '--days',
        type=int,
        help='Only show sessions from last N days'
    )
    list_history_parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of sessions to show'
    )

    # history info
    info_history_parser = history_subparsers.add_parser(
        'info',
        help='Display detailed information about a chat session'
    )
    info_history_parser.add_argument(
        'session_id',
        metavar='SESSION_ID',
        help='Session ID to display'
    )

    # history cleanup (bulk delete old sessions)
    cleanup_history_parser = history_subparsers.add_parser(
        'cleanup',
        help='Delete old chat sessions (bulk operation)'
    )
    cleanup_history_parser.add_argument(
        '--days',
        type=int,
        required=True,
        help='Delete sessions older than N days'
    )
    cleanup_history_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )

    # history delete (single session)
    delete_history_parser = history_subparsers.add_parser(
        'delete',
        help='Delete a specific chat session (move to trash with 30-day recovery)'
    )
    delete_history_parser.add_argument(
        'session_id',
        metavar='SESSION_ID',
        help='Session ID to delete'
    )

    # chat export command
    export_parser = chat_subparsers.add_parser(
        'export',
        help='Export chat session to file',
        description='Export a saved chat session to various formats (markdown, json, txt, pdf)'
    )
    export_parser.add_argument(
        'session_id',
        metavar='SESSION_ID',
        help='Session ID or filename to export (e.g., "20250109_143022" or "chat_20250109_143022.json")'
    )
    export_parser.add_argument(
        '--format',
        choices=['markdown', 'md', 'json', 'txt', 'text', 'pdf'],
        default='markdown',
        help='Export format (default: markdown)'
    )
    export_parser.add_argument(
        '--output',
        metavar='FILE',
        help='Output file path (default: auto-generated based on session ID and format)'
    )
    export_parser.add_argument(
        '--no-timestamps',
        action='store_true',
        help='Exclude timestamps from export'
    )
    export_parser.add_argument(
        '--no-system',
        action='store_true',
        help='Exclude system messages from export'
    )

    # Model command (with subcommands: download, list, info)
    model_parser = subparsers.add_parser(
        'model',
        help='Model management commands',
        description='Download, list, and manage LLM models that run locally via the local OpenAI compatible server.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Global options (specify before 'model'):
  -d, --download-dir PATH   Directory for downloading and storing models (default: ./models/)

Examples:
  # HuggingFace download
  llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

  # Direct link download
  llf model download --url https://example.com/model.gguf --name my-model

  # Download to custom directory
  llf -d /custom/models model download

  # List and info
  llf model list                        List all downloaded models
  llf model list --imported             List models currently configured in config.json
  llf model info                        Show default model information
  llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                                        View information about a specific downloaded model

  # Delete a model
  llf model delete Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                                        Delete a model and all its contents
  llf model delete Qwen/Qwen2.5-Coder-7B-Instruct-GGUF --force
                                        Delete without confirmation prompt

  # Import/Export models to configuration
  llf model import Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                                        Import model to configuration
  llf model export Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                                        Export (remove) model from configuration
        """
    )
    model_subparsers = model_parser.add_subparsers(dest='action', help='Model action to perform')

    # model download
    download_parser = model_subparsers.add_parser(
        'download',
        help='Download a model from HuggingFace Hub or URL',
        description='Download and cache a model locally for use with LLF from HuggingFace Hub or a direct URL.'
    )

    # Download source options (mutually exclusive)
    download_source = download_parser.add_argument_group(
        'Download Source',
        'Specify download source (choose one method)'
    )
    download_source.add_argument(
        '--huggingface-model',
        metavar='NAME',
        help='HuggingFace model identifier (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")'
    )
    download_source.add_argument(
        '--url',
        metavar='URL',
        help='Direct URL to GGUF model file (e.g., "https://example.com/model.gguf"). Requires --name.'
    )
    download_source.add_argument(
        '--name',
        metavar='NAME',
        help='Local directory name for URL download (e.g., "my-custom-model"). Required with --url.'
    )

    # Download options
    download_parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if model exists locally'
    )
    download_parser.add_argument(
        '--token',
        metavar='TOKEN',
        help='HuggingFace API token for private models (HuggingFace downloads only)'
    )

    # model list
    list_parser = model_subparsers.add_parser(
        'list',
        help='List all downloaded models',
        description='Display all models currently downloaded and cached locally. Use --imported to show only models configured in config.json.'
    )
    list_parser.add_argument(
        '--imported',
        action='store_true',
        help='Show only models that are currently imported/configured in config.json'
    )

    # model info
    info_parser = model_subparsers.add_parser(
        'info',
        help='Show detailed model information',
        description='Display detailed information about a specific model including size, location, and verification status.'
    )
    info_parser.add_argument(
        '--model',
        metavar='NAME',
        help='Model identifier to show info for (default: configured default model)'
    )

    # model delete
    delete_parser = model_subparsers.add_parser(
        'delete',
        help='Delete a model from local storage',
        description='Permanently delete a model directory and all its contents from local storage.'
    )
    delete_parser.add_argument(
        'model_name',
        metavar='MODEL_NAME',
        help='Model identifier to delete (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")'
    )
    delete_parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        help='Skip confirmation prompt and delete immediately'
    )

    # model import
    import_parser = model_subparsers.add_parser(
        'import',
        help='Import a model into the configuration',
        description='Import a downloaded model into the config.json file for use with the local LLM server. Creates a backup before making changes.'
    )
    import_parser.add_argument(
        'model_name',
        metavar='MODEL_NAME',
        help='Model identifier to import (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")'
    )

    # model export
    export_parser = model_subparsers.add_parser(
        'export',
        help='Export (remove) model from the configuration',
        description='Remove model configuration from config.json file. Validates model name matches current configuration before removal. Creates a backup before making changes.'
    )
    export_parser.add_argument(
        'model_name',
        metavar='MODEL_NAME',
        help='Model identifier to export (must match currently configured model, e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")'
    )

    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Manage llama-server',
        description='''Start, stop, or check status of the locally running OpenAI compatible LLM server ( llama.cpp ).

Positional arguments:
  list         List all configured servers and their status
  start        Start local LLM server (default or by name)
  stop         Stop local LLM server (default or by name)
  status       Display running status of local LLM server
  restart      Restart the local LLM server
  switch       Switch the default local server
  list_models  List available models hosted from LLM server
''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local Server management
  llf server list                              List all configured servers and status
  llf server start                             Start default server (localhost, foreground)
  llf server start LOCAL_SERVER_NAME           Start specific server by name
  llf server start --force                     Start without memory safety prompt
  llf server start --share                     Start server on local network (0.0.0.0)
  llf server start --daemon                    Start server in background
  llf server start --share --daemon            Start server in background (network accessible)
  llf server stop                              Stop default server
  llf server stop LOCAL_SERVER_NAME            Stop specific server by name
  llf server status                            Check default server status
  llf server status LOCAL_SERVER_NAME          Check specific server status
  llf server restart                           Restart default server
  llf server restart --share                   Restart server with network access
  llf server switch LOCAL_SERVER_NAME          Switch default server

  # Model selection
  llf server start --gguf-dir model_GGUF --gguf-file my-model.gguf
                                               Use local GGUF LLM model
  llf server start --huggingface-model My_Local_Model
                                               Use local HuggingFace LLM model

Note: The locally running server requires llama.cpp compiled with llama-server binary.
For setup instructions, see: https://github.com/ggml-org/llama.cpp
    """
    )
    server_parser.add_argument(
        'action',
        choices=['list', 'start', 'stop', 'status', 'restart', 'switch', 'list_models'],
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom description instead
    )

    # Optional server name
    server_parser.add_argument(
        'server_name',
        nargs='?',  # Optional
        help='Server name (optional). Specify to operate on a specific server, omit to use default server.'
    )

    # Model selection for server
    server_model_group = server_parser.add_argument_group(
        'Model Selection',
        'Specify model location (choose one method, for start/restart actions)'
    )
    server_model_group.add_argument(
        '--huggingface-model',
        metavar='NAME',
        help='HuggingFace model identifier (e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")'
    )
    server_model_group.add_argument(
        '--gguf-dir',
        metavar='DIR',
        help='GGUF model directory within models/ (e.g., "test_gguf"). Must be used with --gguf-file.'
    )
    server_model_group.add_argument(
        '--gguf-file',
        metavar='FILE',
        help='GGUF model filename (e.g., "model.gguf"). Must be used with --gguf-dir.'
    )

    server_parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run server in background (daemon mode)'
    )

    server_parser.add_argument(
        '--share',
        action='store_true',
        help='Make server accessible on local network (binds to 0.0.0.0). Default is localhost only (127.0.0.1).'
    )

    server_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Skip memory safety check when starting a server (use with caution)'
    )

    # GUI command
    gui_parser = subparsers.add_parser(
        'gui',
        help='Manage web-based GUI interface',
        description='''Start, stop, or check status of the web-based graphical interface for managing the LLM framework.

Actions:
  start   - Start the GUI (default action if not specified)
            Use --daemon to run in background
            Example: llf gui start --daemon
  stop    - Stop a running GUI daemon process
            Example: llf gui stop
  status  - Check if GUI daemon is running
            Example: llf gui status

For backward compatibility, 'llf gui' is equivalent to 'llf gui start'.
''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic GUI operations
  llf gui                                      Start GUI (opens browser automatically)
  llf gui start                                Same as above (explicit start)
  llf gui stop                                 Stop running GUI daemon
  llf gui status                               Check GUI daemon status

  # GUI with options
  llf gui start --share --key PASSWORD         Network-accessible GUI with authentication
  llf gui start --daemon                       Start GUI in background (daemon mode)
  llf gui start --port 8080                    Start GUI on custom port
  llf gui start --no-browser                   Start GUI without opening browser
    """
    )
    gui_parser.add_argument(
        'action',
        nargs='?',  # Optional - defaults to 'start' for backward compatibility
        choices=['start', 'stop', 'status'],
        default='start',
        help='GUI action to perform (default: start)'
    )

    gui_parser.add_argument(
        '--port',
        type=int,
        default=7860,
        metavar='PORT',
        help='Port to run the web server on (default: 7860, for start action)'
    )

    gui_parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run GUI in background (daemon mode, for start action)'
    )

    gui_parser.add_argument(
        '--share',
        action='store_true',
        help='Make GUI accessible on local network (binds to 0.0.0.0). Default is localhost only (127.0.0.1, for start action).'
    )

    gui_parser.add_argument(
        '--key',
        type=str,
        metavar='SECRET',
        help='Require authentication with a secret key to access the GUI (for start action). SECRET is any string value of your choosing that will be used to log into the GUI interface'
    )

    gui_parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not automatically open browser (for start action)'
    )

    # Data Store command
    datastore_parser = subparsers.add_parser(
        'datastore',
        help='Data Store Management',
        description='Manage data stores for RAG (Retrieval-Augmented Generation). Attach and detach data sources to provide context to LLM queries.',
        epilog='''
actions:
  list                      List data stores
  list --attached           List only attached data stores
  import DIRECTORY_NAME     Import a vector store from data_stores/vector_stores
  export DATA_STORE_NAME    Export a data store (remove from registry, keep data)
  delete DATA_STORE_NAME    Delete a data store (move to trash with 30-day recovery)
  attach DATA_STORE_NAME    Attach data store to query
  attach all                Attach all data stores
  detach DATA_STORE_NAME    Detach data store
  detach all                Detach all data stores
  info DATA_STORE_NAME      Show data store information
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    datastore_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    datastore_parser.add_argument(
        'datastore_name',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    datastore_parser.add_argument(
        '--attached',
        action='store_true',
        help='List only attached data stores (use with list action)'
    )

    # Module command
    module_parser = subparsers.add_parser(
        'module',
        help='Module Management',
        description='Manage modules that extend the engagement ability between the LLM and user.\n( An example of a module would be converting text from the LLM to audio words for the user. )',
        epilog='''
actions:
  list                      List modules
  list --enabled            List only enabled modules
  enable MODULE_NAME        Enable a module
  enable all                Enable all modules
  disable MODULE_NAME       Disable a module
  disable all               Disable all modules
  info MODULE_NAME          Show module information
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    module_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    module_parser.add_argument(
        'module_name',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    module_parser.add_argument(
        '--enabled',
        action='store_true',
        help='List only enabled modules (use with list action)'
    )

    # Memory command
    memory_parser = subparsers.add_parser(
        'memory',
        help='Memory Management',
        description='Manage long-term memory for the LLM.\n( Memory allows the LLM to store and retrieve persistent information across conversations. )',
        epilog='''
actions:
  list                      List memory instances
  list --enabled            List only enabled memory instances
  create MEMORY_NAME        Create a new memory instance
  enable MEMORY_NAME        Enable a memory instance
  disable MEMORY_NAME       Disable a memory instance
  delete MEMORY_NAME        Delete a memory instance (must be disabled first)
  info MEMORY_NAME          Show memory instance information
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    memory_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    memory_parser.add_argument(
        'memory_name',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    memory_parser.add_argument(
        '--enabled',
        action='store_true',
        help='List only enabled memory instances (use with list action)'
    )

    # Tool command
    tool_parser = subparsers.add_parser(
        'tool',
        help='Tool Management',
        description='Manage tools that extend the ability of the LLM.\n( An example of a tool would be to enable the LLM to perform searches on the Internet )',
        epilog='''
actions:
  list                             List tools
  list --enabled                   List only enabled tools
  enable TOOL_NAME                 Enable a tool (sets to true)
  enable TOOL_NAME --auto          Enable a tool with auto mode
  disable TOOL_NAME                Disable a tool (sets to false)
  info TOOL_NAME                   Show tool information
  import TOOL_NAME                 Import a tool from directory to registry
  export TOOL_NAME                 Export a tool from registry (keeps files)
  config get KEY                   Get a global configuration value
  config set KEY VALUE             Set a global configuration value
  config list                      List all global configuration settings
  whitelist list TOOL_NAME         List whitelisted items for a tool
  whitelist add TOOL_NAME PATTERN  Add pattern to tool whitelist
  whitelist remove TOOL_NAME INDEX Remove pattern from tool whitelist
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    tool_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    tool_parser.add_argument(
        'tool_name',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    tool_parser.add_argument(
        'config_value',
        nargs='?',
        help=argparse.SUPPRESS  # For config set VALUE or whitelist pattern/index
    )
    tool_parser.add_argument(
        'whitelist_value',
        nargs='?',
        help=argparse.SUPPRESS  # For whitelist pattern when tool_name is whitelist subaction
    )
    tool_parser.add_argument(
        '--enabled',
        action='store_true',
        help='List only enabled tools (use with list action)'
    )
    tool_parser.add_argument(
        '--auto',
        action='store_true',
        help='Enable tool with auto mode (use with enable action)'
    )

    # Prompt command
    prompt_parser = subparsers.add_parser(
        'prompt',
        help='Prompt Template Management',
        description='Manage prompt templates for different conversation contexts and tasks.',
        epilog='''
actions:
  list                             List all prompt templates
  list --category CATEGORY         List templates by category
  list --enabled                   List only enabled templates
  info TEMPLATE_NAME               Show detailed template information
  load TEMPLATE_NAME               Load and apply template to active config
  load TEMPLATE_NAME --var key=value  Load template with variable substitution
  import FILE_PATH                 Import external template file
  export TEMPLATE_NAME             Export template to file
  enable TEMPLATE_NAME             Enable a template
  disable TEMPLATE_NAME            Disable a template
  backup                           Create backup of all templates
  delete TEMPLATE_NAME             Delete a template (with confirmation)
  create                           Create a new template interactively
  active                           Show currently active template

Examples:
  llf prompt list                  List all available templates
  llf prompt list --category development
  llf prompt info coding_assistant
  llf prompt load coding_assistant
  llf prompt load socratic_tutor --var topic=Python
  llf prompt create                Start interactive template creation
  llf prompt backup                Create backup before making changes
  llf prompt active                Show which template is currently active
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    prompt_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    prompt_parser.add_argument(
        'template_name',
        nargs='?',
        help=argparse.SUPPRESS  # Template name or file path for various actions
    )
    prompt_parser.add_argument(
        '--category',
        type=str,
        help='Filter templates by category (use with list action)'
    )
    prompt_parser.add_argument(
        '--enabled',
        action='store_true',
        help='List only enabled templates (use with list action)'
    )
    prompt_parser.add_argument(
        '--var',
        action='append',
        help='Variable substitution in format key=value (use with load action)'
    )
    prompt_parser.add_argument(
        '--name',
        type=str,
        help='Custom name for imported template (use with import action)'
    )
    prompt_parser.add_argument(
        '--display-name',
        type=str,
        help='Display name for imported template (use with import action)'
    )
    prompt_parser.add_argument(
        '--description',
        type=str,
        help='Description for imported template (use with import action)'
    )
    prompt_parser.add_argument(
        '--author',
        type=str,
        help='Author name for imported template (use with import action)'
    )
    prompt_parser.add_argument(
        '--tags',
        type=str,
        help='Comma-separated tags for imported template (use with import action)'
    )
    prompt_parser.add_argument(
        '--output',
        type=str,
        help='Output file path for exported template (use with export action)'
    )

    # Dev command (for tool development)
    # Trash management command
    trash_parser = subparsers.add_parser(
        'trash',
        help='Trash Management',
        description='Manage deleted items with 30-day recovery. View, restore, or permanently delete items from trash.',
        epilog='''
actions:
  list                             List all items in trash
  list --type memory               List only memory items in trash
  list --older-than 30             List items older than 30 days
  info TRASH_ID                    Show detailed information about a trashed item
  restore TRASH_ID                 Restore an item from trash to original location
  empty                            Delete items older than 30 days (with confirmation)
  empty --all                      Delete all items in trash (with confirmation)
  empty --force                    Skip confirmation prompt
  empty --dry-run                  Preview what would be deleted

Examples:
  llf trash list                   View all trashed items
  llf trash list --type datastore  View only deleted datastores
  llf trash info 20260110_143022_my_memory
  llf trash restore 20260110_143022_my_memory
  llf trash empty --older-than 60  Delete items older than 60 days
  llf trash empty --all --dry-run  Preview deleting all trash

Note:
  Deleted items are kept in trash for 30 days before automatic removal.
  After restore, you must manually re-import items to update registries.
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    trash_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS
    )
    trash_parser.add_argument(
        'trash_id',
        nargs='?',
        help=argparse.SUPPRESS
    )
    trash_parser.add_argument(
        '--type',
        choices=['memory', 'datastore', 'chat_history', 'template'],
        help='Filter by item type'
    )
    trash_parser.add_argument(
        '--older-than',
        type=int,
        metavar='DAYS',
        help='Filter/delete items older than N days'
    )
    trash_parser.add_argument(
        '--all',
        action='store_true',
        help='Empty all items from trash (use with empty action)'
    )
    trash_parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt (use with empty action)'
    )
    trash_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted (use with empty action)'
    )

    dev_parser = subparsers.add_parser(
        'dev',
        help='Development Tools',
        description='Developer tools for creating and validating custom tools.',
        epilog='''
actions:
  create-tool                      Create a new tool with interactive wizard
  validate-tool TOOL_NAME          Validate tool structure and configuration

Examples:
  llf dev create-tool              Start interactive tool creation wizard
  llf dev validate-tool my_tool    Validate 'my_tool' structure
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    dev_parser.add_argument(
        'action',
        nargs='?',
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom actions section instead
    )
    dev_parser.add_argument(
        'tool_name',
        nargs='?',
        help=argparse.SUPPRESS  # Tool name for validate-tool action
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate model selection arguments
    def validate_model_args(args):
        """Validate mutually exclusive model arguments."""
        hf_model = getattr(args, 'huggingface_model', None)
        gguf_dir = getattr(args, 'gguf_dir', None)
        gguf_file = getattr(args, 'gguf_file', None)

        # Check if both HF and GGUF specified
        if hf_model and (gguf_dir or gguf_file):
            parser.error(
                "Cannot specify both --huggingface-model and --gguf-dir/--gguf-file.\n"
                "Use either HuggingFace OR GGUF flags, not both."
            )

        # Check if only one GGUF flag specified
        if (gguf_dir and not gguf_file) or (gguf_file and not gguf_dir):
            parser.error(
                "--gguf-dir and --gguf-file must be specified together.\n"
                "Both flags are required for GGUF models."
            )

    # Validate download arguments
    def validate_download_args(args):
        """Validate mutually exclusive download arguments."""
        hf_model = getattr(args, 'huggingface_model', None)
        url = getattr(args, 'url', None)
        name = getattr(args, 'name', None)

        # Check if both HF and URL specified
        if hf_model and url:
            parser.error(
                "Cannot specify both --huggingface-model and --url.\n"
                "Use either HuggingFace OR URL download, not both."
            )

        # Check if URL specified without name
        if url and not name:
            parser.error(
                "--url requires --name to specify the local directory name.\n"
                "Example: llf model download --url <URL> --name my-model"
            )

        # Check if name specified without URL
        if name and not url:
            parser.error(
                "--name can only be used with --url.\n"
                "Use --url <URL> --name <NAME> together for URL downloads."
            )

    # Validate if command uses model arguments
    if hasattr(args, 'huggingface_model') or hasattr(args, 'gguf_dir'):
        validate_model_args(args)

    # Validate if command uses download arguments
    if hasattr(args, 'url'):
        validate_download_args(args)

    # Load or create config first (to get log_level if not specified on CLI)
    # get_config() accepts None and uses default path, so we don't need to check args.config
    config = get_config(args.config)

    # Load prompt configuration (optional)
    # Use default config_prompt.json if it exists, otherwise no prompt config
    prompt_config = get_prompt_config()

    # Determine log level: CLI argument takes precedence over config
    log_level = args.log_level if args.log_level else getattr(config, 'log_level', 'INFO')

    # Setup logging
    log_file = getattr(args, 'log_file', None)
    setup_logging(level=log_level, log_file=log_file)
    disable_external_loggers()

    # Override config with command-line arguments
    if args.download_dir:
        config.model_dir = args.download_dir
        config.model_dir.mkdir(parents=True, exist_ok=True)

    if args.cache_dir:
        config.cache_dir = args.cache_dir
        config.cache_dir.mkdir(parents=True, exist_ok=True)

    # Handle commands
    if args.command == 'model':
        # Handle model subcommands
        if args.action == 'download':
            return download_command(args)
        elif args.action == 'list':
            return list_command(args)
        elif args.action == 'info':
            return info_command(args)
        elif args.action == 'delete':
            return delete_command(args)
        elif args.action == 'import':
            return import_model_command(args)
        elif args.action == 'export':
            return export_model_command(args)
        else:
            model_parser.print_help()
            return 0
    elif args.command == 'server':
        return server_command(args)
    elif args.command == 'gui':
        # GUI management (start, stop)
        if args.action == 'start':
            # Start GUI interface
            from .gui import start_gui
            import subprocess
            import sys

            # Check if GUI is already running (daemon mode check)
            gui_pid_file = config.cache_dir / 'gui.pid'
            if gui_pid_file.exists():
                try:
                    with open(gui_pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    # Check if process is still running
                    import psutil
                    if psutil.pid_exists(pid):
                        console.print(f"[yellow]GUI is already running (PID: {pid})[/yellow]")
                        console.print(f"[cyan]Access at: http://{'0.0.0.0' if args.share else '127.0.0.1'}:{args.port}[/cyan]")
                        console.print("[yellow]Use 'llf gui stop' to stop it[/yellow]")
                        return 0
                    else:
                        # Stale PID file
                        gui_pid_file.unlink()
                except (ValueError, FileNotFoundError):
                    # Invalid or missing PID file
                    if gui_pid_file.exists():
                        gui_pid_file.unlink()

            # Determine server_name based on --share flag
            server_name = "0.0.0.0" if args.share else "127.0.0.1"

            if args.daemon:
                # Start GUI in daemon mode (background)
                console.print("[cyan]Starting LLM Framework GUI in daemon mode...[/cyan]")
                console.print(f"[cyan]Port: {args.port}[/cyan]")

                if args.share:
                    console.print(f"[cyan]Access from this device: http://127.0.0.1:{args.port}[/cyan]")
                    console.print(f"[cyan]Access from network: http://YOUR_IP:{args.port}[/cyan]")
                else:
                    console.print(f"[cyan]Access at: http://127.0.0.1:{args.port}[/cyan]")

                if args.key:
                    console.print(f"[yellow]Authentication enabled with secret key[/yellow]")

                # Build command to run in background
                cmd = [
                    sys.executable, '-c',
                    f'''
import sys
import os
sys.path.insert(0, "{config.PROJECT_ROOT}")
from llf.gui import start_gui
from llf.config import get_config
from llf.prompt_config import get_prompt_config

# Save PID
with open("{gui_pid_file}", "w") as f:
    f.write(str(os.getpid()))

try:
    config = get_config()
    prompt_config = get_prompt_config()
    start_gui(
        config=config,
        prompt_config=prompt_config,
        server_name="{server_name}",
        server_port={args.port},
        auth_key={repr(args.key)},
        inbrowser=False
    )
except Exception as e:
    print(f"GUI error: {{e}}", file=sys.stderr)
    if os.path.exists("{gui_pid_file}"):
        os.remove("{gui_pid_file}")
finally:
    if os.path.exists("{gui_pid_file}"):
        os.remove("{gui_pid_file}")
'''
                ]

                # Start process in background
                log_file = config.logs_dir / 'gui.log'
                with open(log_file, 'w') as log:
                    process = subprocess.Popen(
                        cmd,
                        stdout=log,
                        stderr=log,
                        start_new_session=True  # Detach from parent
                    )

                console.print(f"[green]✓ GUI started in background (PID: {process.pid})[/green]")
                console.print(f"[cyan]Logs: {log_file}[/cyan]")
                console.print(f"[yellow]Use 'llf gui stop' to stop the GUI[/yellow]")
                return 0
            else:
                # Start GUI in foreground
                console.print("[cyan]Starting LLM Framework GUI...[/cyan]")
                console.print(f"Opening web interface on port {args.port}")

                if args.share:
                    console.print("[yellow]Making GUI accessible on local network...[/yellow]")
                    console.print(f"[cyan]Access from this device: http://127.0.0.1:{args.port}[/cyan]")
                    console.print(f"[cyan]Access from network: http://YOUR_IP:{args.port}[/cyan]")
                else:
                    console.print("[cyan]GUI accessible on localhost only[/cyan]")

                if args.key:
                    console.print(f"[yellow]Authentication enabled with secret key[/yellow]")

                try:
                    start_gui(
                        config=config,
                        prompt_config=prompt_config,
                        server_name=server_name,
                        server_port=args.port,
                        auth_key=args.key,
                        inbrowser=not args.no_browser
                    )
                    return 0
                except KeyboardInterrupt:
                    console.print("\n[yellow]GUI shutting down...[/yellow]")
                    return 0
                except Exception as e:
                    console.print(f"[red]Error starting GUI: {e}[/red]")
                    return 1

        elif args.action == 'stop':
            # Stop GUI
            gui_pid_file = config.cache_dir / 'gui.pid'
            if not gui_pid_file.exists():
                console.print("[yellow]No GUI daemon process found[/yellow]")
                return 1

            try:
                with open(gui_pid_file, 'r') as f:
                    pid = int(f.read().strip())

                import psutil
                if not psutil.pid_exists(pid):
                    console.print("[yellow]GUI process not running (stale PID file)[/yellow]")
                    gui_pid_file.unlink()
                    return 1

                # Send SIGTERM to the process
                import signal
                import time
                console.print(f"[cyan]Stopping GUI (PID: {pid})...[/cyan]")
                os.kill(pid, signal.SIGTERM)

                # Wait for process to terminate
                for _ in range(50):  # Wait up to 5 seconds
                    if not psutil.pid_exists(pid):
                        break
                    time.sleep(0.1)

                if psutil.pid_exists(pid):
                    console.print("[yellow]GUI didn't stop gracefully, forcing...[/yellow]")
                    os.kill(pid, signal.SIGKILL)

                gui_pid_file.unlink()
                console.print("[green]✓ GUI stopped successfully[/green]")
                return 0

            except (ValueError, FileNotFoundError, ProcessLookupError) as e:
                console.print(f"[red]Error stopping GUI: {e}[/red]")
                if gui_pid_file.exists():
                    gui_pid_file.unlink()
                return 1
            except Exception as e:
                console.print(f"[red]Error stopping GUI: {e}[/red]")
                return 1

        elif args.action == 'status':
            # Check GUI status
            gui_pid_file = config.cache_dir / 'gui.pid'

            if not gui_pid_file.exists():
                console.print("[yellow]GUI Status: Not running (no daemon process)[/yellow]")
                console.print("[dim]Start GUI with: llf gui start --daemon[/dim]")
                return 0

            try:
                with open(gui_pid_file, 'r') as f:
                    pid = int(f.read().strip())

                import psutil
                if psutil.pid_exists(pid):
                    # Check if it's actually our GUI process
                    try:
                        proc = psutil.Process(pid)
                        console.print(f"[green]GUI Status: Running (PID: {pid})[/green]")
                        console.print(f"[cyan]Port: {args.port}[/cyan]")
                        console.print(f"[cyan]Access at: http://127.0.0.1:{args.port}[/cyan]")
                        console.print(f"[dim]Started: {datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
                        return 0
                    except psutil.NoSuchProcess:
                        console.print("[yellow]GUI process not found (stale PID file)[/yellow]")
                        gui_pid_file.unlink()
                        return 1
                else:
                    console.print("[yellow]GUI Status: Not running (stale PID file)[/yellow]")
                    gui_pid_file.unlink()
                    return 0

            except (ValueError, FileNotFoundError) as e:
                console.print(f"[red]Error checking GUI status: {e}[/red]")
                if gui_pid_file.exists():
                    gui_pid_file.unlink()
                return 1

    elif args.command == 'datastore':
        # Data Store Management
        action = args.action if args.action else 'list'

        # Path to data stores registry
        datastore_registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'

        if action == 'list':
            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Filter by attached status if requested
                if args.attached:
                    data_stores = [ds for ds in data_stores if ds.get('attached', False)]

                if not data_stores:
                    if args.attached:
                        console.print("No attached data stores found")
                    else:
                        console.print("No data stores available")
                else:
                    for datastore in data_stores:
                        display_name = datastore.get('display_name', datastore.get('name', 'unknown'))
                        attached = datastore.get('attached', False)
                        status = "attached" if attached else "detached"
                        console.print(f"{display_name:<30} {status}")

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read data store registry: {e}")
                return 1

        elif action == 'attach':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store name required for attach command")
                console.print("[dim]Usage: llf datastore attach DATA_STORE_NAME[/dim]")
                console.print("[dim]       llf datastore attach all[/dim]")
                return 1

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Handle "all" keyword
                if args.datastore_name.lower() == 'all':
                    attached_count = 0
                    already_attached = []
                    for datastore in data_stores:
                        if datastore.get('attached', False):
                            already_attached.append(datastore.get('name'))
                        else:
                            datastore['attached'] = True
                            attached_count += 1

                    # Write back to registry
                    with open(datastore_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    if attached_count > 0:
                        console.print(f"[green]Attached {attached_count} data store(s) successfully[/green]")
                    if already_attached:
                        console.print(f"[dim]Already attached: {', '.join(already_attached)}[/dim]")
                    if attached_count == 0 and not already_attached:
                        console.print("[yellow]No data stores available to attach[/yellow]")
                else:
                    # Find the datastore by name or display_name
                    datastore_found = False
                    for datastore in data_stores:
                        if datastore.get('name') == args.datastore_name or datastore.get('display_name') == args.datastore_name:
                            if datastore.get('attached', False):
                                console.print(f"[yellow]Data store '{args.datastore_name}' is already attached[/yellow]")
                            else:
                                datastore['attached'] = True
                                # Write back to registry
                                with open(datastore_registry_path, 'w') as f:
                                    json.dump(registry, f, indent=2)
                                console.print(f"[green]Data store '{args.datastore_name}' attached successfully[/green]")
                            datastore_found = True
                            break

                    if not datastore_found:
                        console.print(f"[red]Error:[/red] Data store '{args.datastore_name}' not found")
                        return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to attach data store: {e}")
                return 1

        elif action == 'detach':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store name required for detach command")
                console.print("[dim]Usage: llf datastore detach DATA_STORE_NAME[/dim]")
                console.print("[dim]       llf datastore detach all[/dim]")
                return 1

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Handle "all" keyword
                if args.datastore_name.lower() == 'all':
                    detached_count = 0
                    already_detached = []
                    for datastore in data_stores:
                        if not datastore.get('attached', False):
                            already_detached.append(datastore.get('name'))
                        else:
                            datastore['attached'] = False
                            detached_count += 1

                    # Write back to registry
                    with open(datastore_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    if detached_count > 0:
                        console.print(f"[green]Detached {detached_count} data store(s) successfully[/green]")
                    if already_detached:
                        console.print(f"[dim]Already detached: {', '.join(already_detached)}[/dim]")
                    if detached_count == 0 and not already_detached:
                        console.print("[yellow]No data stores available to detach[/yellow]")
                else:
                    # Find the datastore by name or display_name
                    datastore_found = False
                    for datastore in data_stores:
                        if datastore.get('name') == args.datastore_name or datastore.get('display_name') == args.datastore_name:
                            if not datastore.get('attached', False):
                                console.print(f"[yellow]Data store '{args.datastore_name}' is already detached[/yellow]")
                            else:
                                datastore['attached'] = False
                                # Write back to registry
                                with open(datastore_registry_path, 'w') as f:
                                    json.dump(registry, f, indent=2)
                                console.print(f"[green]Data store '{args.datastore_name}' detached successfully[/green]")
                            datastore_found = True
                            break

                    if not datastore_found:
                        console.print(f"[red]Error:[/red] Data store '{args.datastore_name}' not found")
                        return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to detach data store: {e}")
                return 1

        elif action == 'info':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store name required for info command")
                console.print("[dim]Usage: llf datastore info DATA_STORE_NAME[/dim]")
                return 1

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Find the datastore by name or display_name
                datastore = None
                for ds in data_stores:
                    if ds.get('name') == args.datastore_name or ds.get('display_name') == args.datastore_name:
                        datastore = ds
                        break

                if not datastore:
                    console.print(f"[red]Error:[/red] Data store '{args.datastore_name}' not found")
                    return 1

                # Display detailed datastore information
                name = datastore.get('name', 'unknown')
                display_name = datastore.get('display_name', name)
                description = datastore.get('description', 'No description available')
                attached = datastore.get('attached', False)
                vector_store_path_rel = datastore.get('vector_store_path', 'N/A')
                embedding_model = datastore.get('embedding_model', 'N/A')
                num_vectors = datastore.get('num_vectors', 0)

                # Calculate full path relative to project root
                if vector_store_path_rel != 'N/A':
                    # If path is already absolute, use it; otherwise construct from project root
                    vector_store_path_obj = Path(vector_store_path_rel)
                    if vector_store_path_obj.is_absolute():
                        vector_store_path = str(vector_store_path_obj.resolve())
                    else:
                        vector_store_path = str((Path(__file__).parent.parent / vector_store_path_rel).resolve())
                else:
                    vector_store_path = 'N/A'

                console.print(f"\n[bold]{display_name}[/bold] ({name})")
                console.print(f"Description: {description}")
                console.print(f"Status: {'[green]attached[/green]' if attached else '[yellow]detached[/yellow]'}")
                console.print(f"Location: {vector_store_path}")
                console.print(f"Embedding Model: {embedding_model}")
                console.print(f"Number of Vectors: {num_vectors}")

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to get data store info: {e}")
                return 1

        elif action == 'import':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store directory name required for import command")
                console.print("[dim]Usage: llf datastore import DIRECTORY_NAME[/dim]")
                console.print("[dim]       (where DIRECTORY_NAME is under data_stores/vector_stores/)[/dim]")
                return 1

            directory_name = args.datastore_name
            project_root = Path(__file__).parent.parent
            vector_stores_dir = project_root / 'data_stores' / 'vector_stores'
            datastore_dir = vector_stores_dir / directory_name

            # Verify directory is under data_stores/vector_stores
            if not datastore_dir.exists():
                console.print(f"[red]Error:[/red] Directory '{directory_name}' not found in data_stores/vector_stores")
                console.print(f"[yellow]The data store must first be moved to data_stores/vector_stores before it can be imported[/yellow]")
                return 1

            # Verify it's actually under vector_stores
            try:
                # Resolve both paths and check if datastore_dir is under vector_stores_dir
                datastore_resolved = datastore_dir.resolve()
                vector_stores_resolved = vector_stores_dir.resolve()
                if not str(datastore_resolved).startswith(str(vector_stores_resolved)):
                    console.print(f"[red]Error:[/red] Directory must be located under data_stores/vector_stores")
                    console.print(f"[yellow]The data store must first be moved to data_stores/vector_stores before it can be imported[/yellow]")
                    return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to verify directory location: {e}")
                return 1

            # Read config.json from the vector store directory
            config_file = datastore_dir / 'config.json'
            if not config_file.exists():
                console.print(f"[red]Error:[/red] config.json not found in {datastore_dir}")
                console.print(f"[yellow]The directory must contain a valid vector store with config.json[/yellow]")
                return 1

            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                embedding_model = config.get('embedding_model')
                embedding_dimension = config.get('embedding_dimension')
                num_vectors = config.get('num_vectors', 0)
                index_type = config.get('index_type', 'IndexFlatIP')

                if not embedding_model or not embedding_dimension:
                    console.print(f"[red]Error:[/red] Invalid config.json - missing embedding_model or embedding_dimension")
                    return 1

            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in config.json: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read config.json: {e}")
                return 1

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Check if entry already exists
                for ds in data_stores:
                    if ds.get('name') == directory_name:
                        console.print(f"[red]Error:[/red] Data store '{directory_name}' already exists in registry")
                        console.print(f"[yellow]Cannot import - there is already an entry with that name[/yellow]")
                        return 1

                # Create new registry entry with default settings
                display_name = directory_name.replace('_', ' ').replace('-', ' ').title()
                current_date = datetime.now().strftime('%Y-%m-%d')

                new_entry = {
                    "name": directory_name,
                    "display_name": display_name,
                    "description": "Imported vector store",
                    "attached": False,
                    "vector_store_path": f"data_stores/vector_stores/{directory_name}",
                    "embedding_model": embedding_model,
                    "embedding_dimension": embedding_dimension,
                    "index_type": index_type,
                    "_comment2": "========== OPTIONAL PARAMETERS ==========",
                    "model_cache_dir": "data_stores/embedding_models",
                    "top_k_results": 5,
                    "similarity_threshold": 0.3,
                    "max_context_length": 4000,
                    "created_date": current_date,
                    "num_vectors": num_vectors,
                    "metadata": {
                        "source_type": "general",
                        "content_description": "general documentation",
                        "search_mode": "semantic"
                    }
                }

                # Add to registry
                data_stores.append(new_entry)
                registry['data_stores'] = data_stores
                registry['last_updated'] = current_date

                # Save registry
                with open(datastore_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)

                console.print()
                console.print(f"[green]✓[/green] Successfully imported data store '{directory_name}'")
                console.print()
                console.print("Registry entry added with default settings:")
                console.print(f"  - name: {directory_name}")
                console.print(f"  - display_name: {display_name}")
                console.print(f"  - embedding_model: {embedding_model}")
                console.print(f"  - embedding_dimension: {embedding_dimension}")
                console.print(f"  - num_vectors: {num_vectors}")
                console.print(f"  - attached: false")
                console.print()
                console.print("[bold]Note:[/bold] You can manually tweak the settings in data_stores/data_store_registry.json")
                console.print(f"[dim]Use 'llf datastore attach {directory_name}' to enable this data store[/dim]")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to import data store: {e}")
                return 1

        elif action == 'export':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store name required for export command")
                console.print("[dim]Usage: llf datastore export DATA_STORE_NAME[/dim]")
                return 1

            datastore_name = args.datastore_name
            project_root = Path(__file__).parent.parent
            vector_stores_dir = project_root / 'data_stores' / 'vector_stores'

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Find the datastore by name or display_name
                datastore_found = False
                datastore_to_remove = None
                for ds in data_stores:
                    if ds.get('name') == datastore_name or ds.get('display_name') == datastore_name:
                        datastore_found = True
                        datastore_to_remove = ds
                        break

                if not datastore_found:
                    console.print(f"[red]Error:[/red] Data store '{datastore_name}' not found in registry")
                    console.print(f"[yellow]The data store must exist in the registry to be exported[/yellow]")
                    return 1

                # Get the actual name and vector store path
                actual_name = datastore_to_remove.get('name')
                vector_store_path = datastore_to_remove.get('vector_store_path', f'data_stores/vector_stores/{actual_name}')

                # Remove from registry
                data_stores.remove(datastore_to_remove)
                registry['data_stores'] = data_stores
                current_date = datetime.now().strftime('%Y-%m-%d')
                registry['last_updated'] = current_date

                # Save updated registry
                with open(datastore_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)

                console.print()
                console.print(f"[green]✓[/green] Successfully exported data store '{datastore_name}'")
                console.print()
                console.print("The data store has been removed from the registry.")
                console.print()
                console.print(f"[bold]Data Location:[/bold]")
                console.print(f"  The vector store data is still located at:")
                console.print(f"  [cyan]{vector_store_path}[/cyan]")
                console.print()
                console.print("[bold]Next Steps:[/bold]")
                console.print(f"  - You can manually delete the directory if no longer needed")
                console.print(f"  - Or move it to another location for use elsewhere")
                console.print(f"  - To re-import later, use: [dim]llf datastore import {actual_name}[/dim]")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to export data store: {e}")
                return 1

        elif action == 'delete':
            if not args.datastore_name:
                console.print("[red]Error:[/red] Data store name required for delete command")
                console.print("[dim]Usage: llf datastore delete DATA_STORE_NAME[/dim]")
                return 1

            datastore_name = args.datastore_name
            project_root = Path(__file__).parent.parent
            trash_dir = project_root / 'trash'
            trash_manager = TrashManager(trash_dir)

            # Read datastore registry
            try:
                with open(datastore_registry_path, 'r') as f:
                    registry = json.load(f)

                data_stores = registry.get('data_stores', [])

                # Find the datastore by name or display_name
                datastore_found = False
                datastore_to_delete = None
                for ds in data_stores:
                    if ds.get('name') == datastore_name or ds.get('display_name') == datastore_name:
                        datastore_found = True
                        datastore_to_delete = ds
                        break

                if not datastore_found:
                    console.print(f"[red]Error:[/red] Data store '{datastore_name}' not found in registry")
                    return 1

                # Get the actual name and vector store path
                actual_name = datastore_to_delete.get('name')
                vector_store_path_rel = datastore_to_delete.get('vector_store_path', f'data_stores/vector_stores/{actual_name}')

                # Construct absolute path
                vector_store_path_obj = Path(vector_store_path_rel)
                if vector_store_path_obj.is_absolute():
                    vector_store_path = vector_store_path_obj
                else:
                    vector_store_path = project_root / vector_store_path_rel

                if not vector_store_path.exists():
                    console.print(f"[yellow]Warning:[/yellow] Vector store directory not found: {vector_store_path}")
                    console.print(f"[yellow]Removing from registry only[/yellow]")

                    # Remove from registry
                    data_stores.remove(datastore_to_delete)
                    registry['data_stores'] = data_stores
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    registry['last_updated'] = current_date

                    # Save updated registry
                    with open(datastore_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    console.print(f"[green]✓[/green] Data store '{datastore_name}' removed from registry")
                    return 0

                # Move to trash
                success, trash_id = trash_manager.move_to_trash(
                    item_type='datastore',
                    item_name=actual_name,
                    paths=[vector_store_path],
                    original_metadata=datastore_to_delete
                )

                if not success:
                    console.print(f"[red]Error:[/red] Failed to move datastore to trash: {trash_id}")
                    return 1

                # Remove from registry
                data_stores.remove(datastore_to_delete)
                registry['data_stores'] = data_stores
                current_date = datetime.now().strftime('%Y-%m-%d')
                registry['last_updated'] = current_date

                # Save updated registry
                with open(datastore_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)

                console.print()
                console.print(f"[green]✓[/green] Data store '{datastore_name}' moved to trash")
                console.print()
                console.print(f"[bold]Trash ID:[/bold] {trash_id}")
                console.print()
                console.print("[bold]Recovery Options:[/bold]")
                console.print(f"  - View trash: [cyan]llf trash list[/cyan]")
                console.print(f"  - Restore: [cyan]llf trash restore {trash_id}[/cyan]")
                console.print(f"  - After restore, re-import: [cyan]llf datastore import {actual_name}[/cyan]")
                console.print()
                console.print("[dim]Items in trash are automatically deleted after 30 days[/dim]")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Data store registry not found at {datastore_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in data store registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to delete data store: {e}")
                return 1

        else:
            console.print(f"[red]Error:[/red] Unknown action '{action}'")
            console.print("[dim]Available actions: list, attach, detach, info, import, export, delete[/dim]")
            return 1

        return 0

    elif args.command == 'memory':
        # Memory Management
        action = args.action if args.action else 'list'

        # Path to memory registry
        memory_registry_path = Path(__file__).parent.parent / 'memory' / 'memory_registry.json'

        if action == 'list':
            # Read memory registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Filter by enabled status if requested
                if args.enabled:
                    memories = [m for m in memories if m.get('enabled', False)]

                if not memories:
                    if args.enabled:
                        console.print("No enabled memory instances found")
                    else:
                        console.print("No memory instances available")
                else:
                    for memory in memories:
                        display_name = memory.get('display_name', memory.get('name', 'unknown'))
                        enabled = memory.get('enabled', False)
                        status = "enabled" if enabled else "disabled"
                        console.print(f"{display_name:<30} {status}")

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read memory registry: {e}")
                return 1

        elif action == 'enable':
            if not args.memory_name:
                console.print("[red]Error:[/red] Memory name required for enable command")
                console.print("[dim]Usage: llf memory enable MEMORY_NAME[/dim]")
                return 1

            # Read memory registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Find the memory instance by name or display_name
                memory_found = False
                for memory in memories:
                    if memory.get('name') == args.memory_name or memory.get('display_name') == args.memory_name:
                        if memory.get('enabled', False):
                            console.print(f"[yellow]Memory '{args.memory_name}' is already enabled[/yellow]")
                        else:
                            memory['enabled'] = True
                            # Write back to registry
                            with open(memory_registry_path, 'w') as f:
                                json.dump(registry, f, indent=2)
                            console.print(f"[green]Memory '{args.memory_name}' enabled successfully[/green]")
                        memory_found = True
                        break

                if not memory_found:
                    console.print(f"[red]Error:[/red] Memory '{args.memory_name}' not found")
                    return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to enable memory: {e}")
                return 1

        elif action == 'disable':
            if not args.memory_name:
                console.print("[red]Error:[/red] Memory name required for disable command")
                console.print("[dim]Usage: llf memory disable MEMORY_NAME[/dim]")
                return 1

            # Read memory registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Find the memory instance by name or display_name
                memory_found = False
                for memory in memories:
                    if memory.get('name') == args.memory_name or memory.get('display_name') == args.memory_name:
                        if not memory.get('enabled', False):
                            console.print(f"[yellow]Memory '{args.memory_name}' is already disabled[/yellow]")
                        else:
                            memory['enabled'] = False
                            # Write back to registry
                            with open(memory_registry_path, 'w') as f:
                                json.dump(registry, f, indent=2)
                            console.print(f"[green]Memory '{args.memory_name}' disabled successfully[/green]")
                        memory_found = True
                        break

                if not memory_found:
                    console.print(f"[red]Error:[/red] Memory '{args.memory_name}' not found")
                    return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to disable memory: {e}")
                return 1

        elif action == 'info':
            if not args.memory_name:
                console.print("[red]Error:[/red] Memory name required for info command")
                console.print("[dim]Usage: llf memory info MEMORY_NAME[/dim]")
                return 1

            # Read memory registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Find the memory instance by name or display_name
                memory = None
                for m in memories:
                    if m.get('name') == args.memory_name or m.get('display_name') == args.memory_name:
                        memory = m
                        break

                if not memory:
                    console.print(f"[red]Error:[/red] Memory '{args.memory_name}' not found")
                    return 1

                # Display detailed memory information
                name = memory.get('name', 'unknown')
                display_name = memory.get('display_name', name)
                description = memory.get('description', 'No description')
                enabled = memory.get('enabled', False)
                memory_type = memory.get('type', 'unknown')
                directory = memory.get('directory', name)
                created_date = memory.get('created_date', 'Not created')
                last_modified = memory.get('last_modified', 'Never modified')

                # Calculate memory path relative to project root
                memory_path = Path(__file__).parent.parent / 'memory' / directory

                # Get metadata
                metadata = memory.get('metadata', {})
                storage_type = metadata.get('storage_type', 'unknown')
                max_entries = metadata.get('max_entries', 'unlimited')
                compression = metadata.get('compression', False)

                # Status indicator
                status = "[green]✓ enabled[/green]" if enabled else "[dim]○ disabled[/dim]"

                console.print()
                console.print(f"[bold]{display_name}[/bold] ({name})")
                console.print(f"  {status}")
                console.print(f"  [dim]Type:[/dim] {memory_type}")
                console.print(f"  [dim]Description:[/dim] {description}")
                console.print(f"  [dim]Location:[/dim] {memory_path}")
                console.print(f"  [dim]Storage Type:[/dim] {storage_type}")
                console.print(f"  [dim]Max Entries:[/dim] {max_entries}")
                console.print(f"  [dim]Compression:[/dim] {'Yes' if compression else 'No'}")
                console.print(f"  [dim]Created:[/dim] {created_date}")
                console.print(f"  [dim]Last Modified:[/dim] {last_modified}")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to retrieve memory info: {e}")
                return 1

        elif action == 'create':
            if not args.memory_name:
                console.print("[red]Error:[/red] Memory name required for create command")
                console.print("[dim]Usage: llf memory create MEMORY_NAME[/dim]")
                return 1

            memory_name = args.memory_name

            # Validate memory name
            if not memory_name.replace('_', '').replace('-', '').isalnum():
                console.print("[red]Error:[/red] Memory name must contain only alphanumeric characters, underscores, and hyphens")
                return 1

            # Check if memory already exists in registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Check if memory name already exists in registry
                for memory in memories:
                    if memory.get('name') == memory_name:
                        console.print(f"[red]Error:[/red] Memory '{memory_name}' already exists in registry")
                        console.print(f"[yellow]Delete it first before creating a new one with the same name[/yellow]")
                        return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read memory registry: {e}")
                return 1

            # Define paths
            project_root = Path(__file__).parent.parent
            memory_dir = project_root / 'memory' / memory_name

            # Check if directory already exists
            if memory_dir.exists():
                console.print(f"[red]Error:[/red] Memory directory already exists: {memory_dir}")
                console.print(f"[yellow]Delete it first before creating a new one with the same name[/yellow]")
                return 1

            # Create memory structure
            console.print(f"Creating new memory instance: '{memory_name}'")
            console.print()

            # Create directory
            try:
                memory_dir.mkdir(parents=True, exist_ok=False)
                console.print(f"[green]✓[/green] Created directory: {memory_dir}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to create directory {memory_dir}: {e}")
                return 1

            # Create index.json (empty object)
            index_file = memory_dir / 'index.json'
            try:
                with open(index_file, 'w') as f:
                    json.dump({}, f, indent=2)
                console.print(f"[green]✓[/green] Created: {index_file.name}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to create index.json: {e}")
                return 1

            # Create memory.jsonl (empty file)
            memory_file = memory_dir / 'memory.jsonl'
            try:
                memory_file.touch()
                console.print(f"[green]✓[/green] Created: {memory_file.name}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to create memory.jsonl: {e}")
                return 1

            # Create metadata.json (initialized with defaults)
            metadata_file = memory_dir / 'metadata.json'
            current_time = datetime.now(UTC).isoformat() + "Z"

            metadata = {
                "total_entries": 0,
                "last_updated": current_time,
                "created_date": current_time,
                "size_bytes": 0,
                "oldest_entry": None,
                "newest_entry": None,
                "entry_types": {
                    "note": 0,
                    "fact": 0,
                    "preference": 0,
                    "task": 0,
                    "context": 0
                },
                "statistics": {
                    "average_importance": 0.0,
                    "most_accessed_id": None,
                    "total_accesses": 0
                }
            }

            try:
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                console.print(f"[green]✓[/green] Created: {metadata_file.name}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to create metadata.json: {e}")
                return 1

            # Create README.md
            readme_file = memory_dir / 'README.md'
            readme_content = """
Contains the memory data files

"""

            try:
                with open(readme_file, 'w') as f:
                    f.write(readme_content)
                console.print(f"[green]✓[/green] Created: {readme_file.name}")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to create README.md: {e}")
                return 1

            # Add to registry
            display_name = memory_name.replace('_', ' ').replace('-', ' ').title()
            current_date = datetime.now().strftime('%Y-%m-%d')

            new_entry = {
                "name": memory_name,
                "display_name": display_name,
                "description": "Custom memory instance",
                "directory": memory_name,
                "enabled": False,
                "type": "persistent",
                "created_date": current_date,
                "last_modified": None,
                "metadata": {
                    "storage_type": "json",
                    "max_entries": 10000,
                    "compression": False
                }
            }

            # Add to registry
            memories.append(new_entry)
            registry['memories'] = memories
            registry['last_updated'] = current_date

            # Save registry
            try:
                with open(memory_registry_path, 'w') as f:
                    json.dump(registry, f, indent=2)
                console.print(f"\n[green]✓[/green] Added entry to memory_registry.json")
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to update registry file: {e}")
                return 1

            # Print success message
            console.print()
            console.print("=" * 70)
            console.print("[green]SUCCESS! Memory instance created successfully.[/green]")
            console.print("=" * 70)
            console.print()
            console.print("Registry entry added with default values:")
            console.print(f"  - enabled: false (use 'llf memory enable {memory_name}' to activate)")
            console.print(f"  - display_name: {display_name}")
            console.print(f"  - description: Custom memory instance")
            console.print(f"  - type: persistent")
            console.print(f"  - max_entries: 10000")
            console.print()
            console.print("[bold]IMPORTANT:[/bold] Please review and edit the following fields in memory_registry.json:")
            console.print(f"  - description: Update to describe the purpose of this memory instance")
            console.print(f"  - display_name: Customize if desired")
            console.print(f"  - metadata.max_entries: Adjust based on your needs")
            console.print(f"  - enabled: Set to true when ready to use (or use 'llf memory enable {memory_name}')")
            console.print()
            console.print(f"Memory location: memory/{memory_name}/")
            console.print()

        elif action == 'delete':
            if not args.memory_name:
                console.print("[red]Error:[/red] Memory name required for delete command")
                console.print("[dim]Usage: llf memory delete MEMORY_NAME[/dim]")
                return 1

            memory_name = args.memory_name
            project_root = Path(__file__).parent.parent
            trash_dir = project_root / 'trash'
            trash_manager = TrashManager(trash_dir)

            # Read memory registry
            try:
                with open(memory_registry_path, 'r') as f:
                    registry = json.load(f)

                memories = registry.get('memories', [])

                # Find the memory instance by name or display_name
                memory = None
                memory_index = None
                for idx, m in enumerate(memories):
                    if m.get('name') == memory_name or m.get('display_name') == memory_name:
                        memory = m
                        memory_index = idx
                        break

                if not memory:
                    console.print(f"[red]Error:[/red] Memory '{memory_name}' not found")
                    return 1

                # Check if memory is enabled
                if memory.get('enabled', False):
                    console.print(f"[red]Error:[/red] Memory '{memory_name}' is currently enabled")
                    console.print(f"[yellow]Please disable it first using: llf memory disable {memory_name}[/yellow]")
                    return 1

                # Get directory path
                directory = memory.get('directory', memory_name)
                memory_dir = project_root / 'memory' / directory

                if not memory_dir.exists():
                    console.print(f"[yellow]Warning:[/yellow] Memory directory not found: {memory_dir}")
                    console.print(f"[yellow]Removing from registry only[/yellow]")

                    # Remove from registry
                    memories.pop(memory_index)
                    registry['memories'] = memories
                    registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

                    # Save registry
                    with open(memory_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    console.print(f"[green]✓[/green] Memory '{memory_name}' removed from registry")
                    return 0

                # Move to trash
                success, trash_id = trash_manager.move_to_trash(
                    item_type='memory',
                    item_name=memory_name,
                    paths=[memory_dir],
                    original_metadata=memory
                )

                if not success:
                    console.print(f"[red]Error:[/red] Failed to move memory to trash: {trash_id}")
                    return 1

                # Remove from registry
                memories.pop(memory_index)
                registry['memories'] = memories
                registry['last_updated'] = datetime.now().strftime('%Y-%m-%d')

                # Save registry
                try:
                    with open(memory_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)
                except Exception as e:
                    console.print(f"[red]Error:[/red] Failed to update registry file: {e}")
                    return 1

                console.print()
                console.print(f"[green]✓[/green] Memory instance '{memory_name}' moved to trash")
                console.print()
                console.print(f"[bold]Trash ID:[/bold] {trash_id}")
                console.print()
                console.print("[bold]Recovery Options:[/bold]")
                console.print(f"  - View trash: [cyan]llf trash list[/cyan]")
                console.print(f"  - Restore: [cyan]llf trash restore {trash_id}[/cyan]")
                console.print(f"  - After restore, re-enable: [cyan]llf memory enable {memory_name}[/cyan]")
                console.print()
                console.print("[dim]Items in trash are automatically deleted after 30 days[/dim]")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Memory registry not found at {memory_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in memory registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to delete memory: {e}")
                return 1

        else:
            console.print(f"[red]Error:[/red] Unknown action '{action}'")
            console.print("[dim]Available actions: list, enable, disable, info, create, delete[/dim]")
            return 1

        return 0

    elif args.command == 'module':
        # Module Management
        action = args.action if args.action else 'list'

        # Path to modules registry
        modules_registry_path = Path(__file__).parent.parent / 'modules' / 'modules_registry.json'

        if action == 'list':
            # Read modules registry
            try:
                with open(modules_registry_path, 'r') as f:
                    registry = json.load(f)

                modules = registry.get('modules', [])

                # Filter by enabled status if requested
                if args.enabled:
                    modules = [m for m in modules if m.get('enabled', False)]

                if not modules:
                    if args.enabled:
                        console.print("No enabled modules found")
                    else:
                        console.print("No modules available")
                else:
                    for module in modules:
                        display_name = module.get('display_name', module.get('name', 'unknown'))
                        enabled = module.get('enabled', False)
                        status = "enabled" if enabled else "disabled"
                        console.print(f"{display_name:<30} {status}")

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Modules registry not found at {modules_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in modules registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read modules registry: {e}")
                return 1

        elif action == 'enable':
            if not args.module_name:
                console.print("[red]Error:[/red] Module name required for enable command")
                console.print("[dim]Usage: llf module enable MODULE_NAME[/dim]")
                console.print("[dim]       llf module enable all[/dim]")
                return 1

            # Read modules registry
            try:
                with open(modules_registry_path, 'r') as f:
                    registry = json.load(f)

                modules = registry.get('modules', [])

                # Handle "all" keyword
                if args.module_name.lower() == 'all':
                    enabled_count = 0
                    already_enabled = []
                    for module in modules:
                        if module.get('enabled', False):
                            already_enabled.append(module.get('name'))
                        else:
                            module['enabled'] = True
                            enabled_count += 1

                    # Write back to registry
                    with open(modules_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    if enabled_count > 0:
                        console.print(f"[green]Enabled {enabled_count} module(s) successfully[/green]")
                    if already_enabled:
                        console.print(f"[dim]Already enabled: {', '.join(already_enabled)}[/dim]")
                    if enabled_count == 0 and not already_enabled:
                        console.print("[yellow]No modules available to enable[/yellow]")
                else:
                    # Find the module by name or display_name
                    module_found = False
                    for module in modules:
                        if module.get('name') == args.module_name or module.get('display_name') == args.module_name:
                            if module.get('enabled', False):
                                console.print(f"[yellow]Module '{args.module_name}' is already enabled[/yellow]")
                            else:
                                module['enabled'] = True
                                # Write back to registry
                                with open(modules_registry_path, 'w') as f:
                                    json.dump(registry, f, indent=2)
                                console.print(f"[green]Module '{args.module_name}' enabled successfully[/green]")
                            module_found = True
                            break

                    if not module_found:
                        console.print(f"[red]Error:[/red] Module '{args.module_name}' not found")
                        return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Modules registry not found at {modules_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in modules registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to enable module: {e}")
                return 1

        elif action == 'disable':
            if not args.module_name:
                console.print("[red]Error:[/red] Module name required for disable command")
                console.print("[dim]Usage: llf module disable MODULE_NAME[/dim]")
                console.print("[dim]       llf module disable all[/dim]")
                return 1

            # Read modules registry
            try:
                with open(modules_registry_path, 'r') as f:
                    registry = json.load(f)

                modules = registry.get('modules', [])

                # Handle "all" keyword
                if args.module_name.lower() == 'all':
                    disabled_count = 0
                    already_disabled = []
                    for module in modules:
                        if not module.get('enabled', False):
                            already_disabled.append(module.get('name'))
                        else:
                            module['enabled'] = False
                            disabled_count += 1

                    # Write back to registry
                    with open(modules_registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)

                    if disabled_count > 0:
                        console.print(f"[green]Disabled {disabled_count} module(s) successfully[/green]")
                    if already_disabled:
                        console.print(f"[dim]Already disabled: {', '.join(already_disabled)}[/dim]")
                    if disabled_count == 0 and not already_disabled:
                        console.print("[yellow]No modules available to disable[/yellow]")
                else:
                    # Find the module by name or display_name
                    module_found = False
                    for module in modules:
                        if module.get('name') == args.module_name or module.get('display_name') == args.module_name:
                            if not module.get('enabled', False):
                                console.print(f"[yellow]Module '{args.module_name}' is already disabled[/yellow]")
                            else:
                                module['enabled'] = False
                                # Write back to registry
                                with open(modules_registry_path, 'w') as f:
                                    json.dump(registry, f, indent=2)
                                console.print(f"[green]Module '{args.module_name}' disabled successfully[/green]")
                            module_found = True
                            break

                    if not module_found:
                        console.print(f"[red]Error:[/red] Module '{args.module_name}' not found")
                        return 1

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Modules registry not found at {modules_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in modules registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to disable module: {e}")
                return 1

        elif action == 'info':
            if not args.module_name:
                console.print("[red]Error:[/red] Module name required for info command")
                console.print("[dim]Usage: llf module info MODULE_NAME[/dim]")
                return 1

            # Read modules registry
            try:
                with open(modules_registry_path, 'r') as f:
                    registry = json.load(f)

                modules = registry.get('modules', [])

                # Find the module by name or display_name
                module = None
                for m in modules:
                    if m.get('name') == args.module_name or m.get('display_name') == args.module_name:
                        module = m
                        break

                if not module:
                    console.print(f"[red]Error:[/red] Module '{args.module_name}' not found")
                    return 1

                # Display detailed module information
                name = module.get('name', 'unknown')
                display_name = module.get('display_name', name)
                description = module.get('description', 'No description')
                enabled = module.get('enabled', False)
                version = module.get('version', '0.0.0')
                module_type = module.get('type', 'unknown')
                directory = module.get('directory', name)

                # Calculate module path relative to project root
                module_path = Path(__file__).parent.parent / 'modules' / directory

                # Status indicator
                status = "[green]✓ enabled[/green]" if enabled else "[dim]○ disabled[/dim]"

                console.print()
                console.print(f"[bold]{display_name}[/bold] ({name}) [dim]v{version}[/dim]")
                console.print(f"  {status}")
                console.print(f"  [dim]Type:[/dim] {module_type}")
                console.print(f"  [dim]Description:[/dim] {description}")
                console.print(f"  [dim]Location:[/dim] {module_path}")
                console.print()

            except FileNotFoundError:
                console.print(f"[red]Error:[/red] Modules registry not found at {modules_registry_path}")
                return 1
            except json.JSONDecodeError as e:
                console.print(f"[red]Error:[/red] Invalid JSON in modules registry: {e}")
                return 1
            except Exception as e:
                console.print(f"[red]Error:[/red] Failed to read module info: {e}")
                return 1

        else:
            console.print(f"[red]Error:[/red] Unknown action '{action}'")
            console.print("[dim]Valid actions: list, enable, disable, info[/dim]")
            return 1

        return 0

    elif args.command == 'tool':
        # Tool Management
        from llf.tools_manager import ToolsManager

        tools_manager = ToolsManager()

        action = getattr(args, 'action', None)
        tool_name = getattr(args, 'tool_name', None)
        show_enabled_only = getattr(args, 'enabled', False)

        if not action or action == 'list':
            # List all features
            features = tools_manager.list_features()

            if not features:
                if show_enabled_only:
                    console.print("No enabled tools found")
                else:
                    console.print("No tools available")
                return 0

            # Track if any tools were printed
            printed_any = False

            for feature_name, feature_info in features.items():
                enabled = feature_info.get('enabled', False)

                # Filter by enabled status if requested (include both 'auto' and true)
                if show_enabled_only:
                    if not (enabled == 'auto' or enabled in [True, 'true']):
                        continue

                # Determine status text
                if enabled == 'auto':
                    status = "auto"
                elif enabled in [True, 'true']:
                    status = "enabled"
                else:
                    status = "disabled"

                console.print(f"{feature_name:<30} {status}")
                printed_any = True

            # If filtering by enabled and nothing was printed, show message
            if show_enabled_only and not printed_any:
                console.print("No enabled tools found")

        elif action == 'enable':
            if not tool_name:
                console.print("[red]Error: Feature name required[/red]")
                console.print("Usage: llf tool enable <feature_name> [--auto]")
                return 1

            # Get tool info to check supported states
            tool_info = tools_manager.get_tool_info(tool_name)
            if not tool_info:
                console.print(f"[red]✗[/red] Tool '[bold]{tool_name}[/bold]' not found")
                console.print("[yellow]Check that the tool name is correct[/yellow]")
                console.print("\n[dim]Use 'llf tool list' to see available tools[/dim]")
                return 1

            # Check if --auto flag was used
            use_auto = getattr(args, 'auto', False)

            # Determine desired state string
            desired_state_str = 'auto' if use_auto else 'true'

            # Get supported states
            supported_states = tool_info.get('metadata', {}).get('supported_states', [])

            # Validate against supported states
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

                # Check if desired state is supported
                if desired_state_str not in normalized_supported:
                    console.print(f"[red]✗[/red] Tool '[bold]{tool_name}[/bold]' does not support enabled state: {desired_state_str}")
                    console.print(f"\n[yellow]Supported states for this tool:[/yellow] {', '.join(normalized_supported)}")
                    return 1

            # Enable the feature with appropriate method
            if use_auto:
                success = tools_manager.auto_feature(tool_name, session_only=False)
                mode_text = "auto mode"
            else:
                success = tools_manager.enable_feature(tool_name, session_only=False)
                mode_text = "enabled"

            if success:
                console.print(f"[green]✓[/green] Feature '[bold]{tool_name}[/bold]' {mode_text}")
                return 0
            else:
                console.print(f"[red]✗[/red] Failed to set feature '[bold]{tool_name}[/bold]' to {mode_text}")
                return 1

        elif action == 'disable':
            if not tool_name:
                console.print("[red]Error: Feature name required[/red]")
                console.print("Usage: llf tool disable <feature_name>")
                return 1

            # Get tool info to check supported states
            tool_info = tools_manager.get_tool_info(tool_name)
            if not tool_info:
                console.print(f"[red]✗[/red] Tool '[bold]{tool_name}[/bold]' not found")
                console.print("[yellow]Check that the tool name is correct[/yellow]")
                console.print("\n[dim]Use 'llf tool list' to see available tools[/dim]")
                return 1

            # Get supported states
            supported_states = tool_info.get('metadata', {}).get('supported_states', [])

            # Validate that 'false' is supported
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

                # Check if false is supported
                if 'false' not in normalized_supported:
                    console.print(f"[red]✗[/red] Tool '[bold]{tool_name}[/bold]' does not support enabled state: false")
                    console.print(f"\n[yellow]Supported states for this tool:[/yellow] {', '.join(normalized_supported)}")
                    return 1

            if tools_manager.disable_feature(tool_name, session_only=False):
                console.print(f"[green]✓[/green] Feature '[bold]{tool_name}[/bold]' disabled")
                return 0
            else:
                console.print(f"[red]✗[/red] Failed to disable feature '[bold]{tool_name}[/bold]'")
                return 1

        elif action == 'info':
            if not tool_name:
                console.print("[red]Error: Feature name required[/red]")
                console.print("Usage: llf tool info <feature_name>")
                return 1

            # Get full tool info from registry
            tool_info = tools_manager.get_tool_info(tool_name)
            if not tool_info:
                console.print(f"[red]Error: Unknown feature '[bold]{tool_name}[/bold]'[/red]")
                return 1

            enabled = tool_info.get('enabled', False)

            # Handle three-state display
            if enabled == 'auto':
                status_color = "yellow"
                status_text = "auto (recommended)"
            elif enabled in [True, 'true']:
                status_color = "green"
                status_text = "enabled (force active)"
            else:
                status_color = "red"
                status_text = "disabled"

            # Get tool type with description
            tool_type = tool_info.get('type', 'unknown')
            type_descriptions = {
                'postprocessor': 'postprocessor (modifies LLM output)',
                'preprocessor': 'preprocessor (modifies input to LLM)',
                'llm_invokable': 'llm_invokable (LLM can call as function)'
            }
            type_display = type_descriptions.get(tool_type, tool_type)

            console.print(f"\n[bold cyan]Feature: {tool_name}[/bold cyan]")
            console.print(f"Type: {type_display}")
            console.print(f"Status: [{status_color}]{status_text}[/{status_color}]")
            console.print(f"Description: {tool_info.get('description', 'No description')}")

            # Display supported states
            supported_states = tool_info.get('metadata', {}).get('supported_states', [])
            if supported_states:
                states_str = ", ".join([f"'{s}'" if isinstance(s, str) else str(s) for s in supported_states])
                console.print(f"Supported states: {states_str}")

            # Display use case from metadata
            use_case = tool_info.get('metadata', {}).get('use_case', '')
            if use_case:
                console.print(f"\n[dim]Note: {use_case}[/dim]")

            return 0

        elif action == 'config':
            # Global config management
            config_action = tool_name  # Second arg is the config action (get/set/list)

            if not config_action or config_action == 'list':
                # List all global config settings
                global_config = tools_manager.get_global_config()

                if not global_config:
                    console.print("No global configuration settings found")
                    return 0

                console.print("\n[bold cyan]Global Tool Configuration:[/bold cyan]")
                for key, value in global_config.items():
                    # Format value display
                    if isinstance(value, list):
                        value_str = ', '.join(str(v) for v in value)
                    elif isinstance(value, bool):
                        value_str = str(value).lower()
                    else:
                        value_str = str(value)

                    console.print(f"  {key:<25} {value_str}")

                return 0

            elif config_action == 'get':
                # Get specific config value
                config_key = getattr(args, 'config_value', None)

                if not config_key:
                    console.print("[red]Error: Configuration key required[/red]")
                    console.print("Usage: llf tool config get <key>")
                    return 1

                value = tools_manager.get_global_config(config_key)

                if value is None:
                    console.print(f"[yellow]Configuration key '{config_key}' not found[/yellow]")
                    console.print("\n[dim]Use 'llf tool config list' to see all settings[/dim]")
                    return 1

                # Format value display
                if isinstance(value, list):
                    value_str = ', '.join(str(v) for v in value)
                elif isinstance(value, bool):
                    value_str = str(value).lower()
                else:
                    value_str = str(value)

                console.print(f"{config_key}: {value_str}")
                return 0

            elif config_action == 'set':
                # Set config value
                config_key = getattr(args, 'config_value', None)

                if not config_key:
                    console.print("[red]Error: Configuration key and value required[/red]")
                    console.print("Usage: llf tool config set <key> <value>")
                    return 1

                # For 'set', we need one more argument (the value)
                # Since we only have 3 positional args (action, tool_name, config_value),
                # we need to handle this differently
                console.print("[yellow]Note: config set requires additional implementation[/yellow]")
                console.print("For now, please edit tools/tools_registry.json directly")
                console.print(f"Set 'global_config.{config_key}' in the registry file")
                return 0

            else:
                console.print(f"[red]Error: Unknown config action '{config_action}'[/red]")
                console.print("\nValid config actions: get, set, list")
                return 1

        elif action == 'whitelist':
            # Whitelist management for tools
            whitelist_action = tool_name  # Second arg is the whitelist action (list/add/remove)
            target_tool = getattr(args, 'config_value', None)  # Third arg is the tool name
            pattern_or_index = getattr(args, 'whitelist_value', None)  # Fourth arg is pattern/index

            if not whitelist_action:
                console.print("[red]Error: Whitelist action required[/red]")
                console.print("Usage: llf tool whitelist <list|add|remove> <tool_name> [pattern/index]")
                console.print("\nExamples:")
                console.print("  llf tool whitelist list command_exec")
                console.print("  llf tool whitelist add command_exec 'ls'")
                console.print("  llf tool whitelist add file_access '*.txt'")
                console.print("  llf tool whitelist remove command_exec 0")
                return 1

            if whitelist_action == 'list':
                # List whitelist for tool
                if not target_tool:
                    console.print("[red]Error: Tool name required[/red]")
                    console.print("Usage: llf tool whitelist list <tool_name>")
                    return 1

                # Get tool info
                tool_info = tools_manager.get_tool_info(target_tool)
                if not tool_info:
                    console.print(f"[red]✗[/red] Tool '[bold]{target_tool}[/bold]' not found")
                    return 1

                # Get whitelist from metadata
                whitelist = tool_info.get('metadata', {}).get('whitelist', [])

                if not whitelist:
                    console.print(f"[yellow]Tool '{target_tool}' has no whitelist entries[/yellow]")
                    console.print("\n[dim]Add entries with: llf tool whitelist add {target_tool} <pattern>[/dim]")
                    return 0

                console.print(f"\n[bold cyan]Whitelist for {target_tool}:[/bold cyan]")
                for idx, pattern in enumerate(whitelist):
                    console.print(f"  [{idx}] {pattern}")

                console.print(f"\n[dim]Total entries: {len(whitelist)}[/dim]")
                return 0

            elif whitelist_action == 'add':
                # Add pattern to whitelist
                if not target_tool or not pattern_or_index:
                    console.print("[red]Error: Tool name and pattern required[/red]")
                    console.print("Usage: llf tool whitelist add <tool_name> <pattern>")
                    console.print("\nExamples:")
                    console.print("  llf tool whitelist add command_exec 'ls'")
                    console.print("  llf tool whitelist add command_exec 'git*'")
                    console.print("  llf tool whitelist add file_access '*.txt'")
                    console.print("  llf tool whitelist add file_access 'docs/*'")
                    return 1

                # Get tool info
                tool_info = tools_manager.get_tool_info(target_tool)
                if not tool_info:
                    console.print(f"[red]✗[/red] Tool '[bold]{target_tool}[/bold]' not found")
                    return 1

                # Get current whitelist
                whitelist = tool_info.get('metadata', {}).get('whitelist', [])

                # Check if pattern already exists
                if pattern_or_index in whitelist:
                    console.print(f"[yellow]Pattern '{pattern_or_index}' already in whitelist[/yellow]")
                    return 0

                # Add pattern
                whitelist.append(pattern_or_index)

                # Update tool metadata in registry
                success = tools_manager.update_tool_metadata(target_tool, 'whitelist', whitelist)

                if success:
                    console.print(f"[green]✓[/green] Added pattern '[bold]{pattern_or_index}[/bold]' to {target_tool} whitelist")
                    return 0
                else:
                    console.print(f"[red]✗[/red] Failed to update whitelist for {target_tool}")
                    return 1

            elif whitelist_action == 'remove':
                # Remove pattern from whitelist by index
                if not target_tool or pattern_or_index is None:
                    console.print("[red]Error: Tool name and index required[/red]")
                    console.print("Usage: llf tool whitelist remove <tool_name> <index>")
                    console.print("\n[dim]Use 'llf tool whitelist list <tool_name>' to see indices[/dim]")
                    return 1

                # Get tool info
                tool_info = tools_manager.get_tool_info(target_tool)
                if not tool_info:
                    console.print(f"[red]✗[/red] Tool '[bold]{target_tool}[/bold]' not found")
                    return 1

                # Get current whitelist
                whitelist = tool_info.get('metadata', {}).get('whitelist', [])

                if not whitelist:
                    console.print(f"[yellow]Tool '{target_tool}' has no whitelist entries[/yellow]")
                    return 0

                # Parse index
                try:
                    index = int(pattern_or_index)
                except ValueError:
                    console.print(f"[red]Error: Invalid index '{pattern_or_index}'. Must be a number.[/red]")
                    console.print("\n[dim]Use 'llf tool whitelist list <tool_name>' to see indices[/dim]")
                    return 1

                # Validate index
                if index < 0 or index >= len(whitelist):
                    console.print(f"[red]Error: Index {index} out of range (0-{len(whitelist)-1})[/red]")
                    console.print("\n[dim]Use 'llf tool whitelist list <tool_name>' to see indices[/dim]")
                    return 1

                # Remove pattern
                removed_pattern = whitelist.pop(index)

                # Update tool metadata in registry
                success = tools_manager.update_tool_metadata(target_tool, 'whitelist', whitelist)

                if success:
                    console.print(f"[green]✓[/green] Removed pattern '[bold]{removed_pattern}[/bold]' from {target_tool} whitelist")
                    return 0
                else:
                    console.print(f"[red]✗[/red] Failed to update whitelist for {target_tool}")
                    return 1

            else:
                console.print(f"[red]Error: Unknown whitelist action '{whitelist_action}'[/red]")
                console.print("\nValid whitelist actions: list, add, remove")
                return 1

        elif action == 'import':
            if not tool_name:
                console.print("[red]Error: Tool name required[/red]")
                console.print("Usage: llf tool import <tool_name>")
                return 1

            success, message = tools_manager.import_tool(tool_name)
            if success:
                console.print(f"[green]✓[/green] {message}")
                return 0
            else:
                console.print(f"[red]✗[/red] {message}")
                return 1

        elif action == 'export':
            if not tool_name:
                console.print("[red]Error: Tool name required[/red]")
                console.print("Usage: llf tool export <tool_name>")
                return 1

            success, message = tools_manager.export_tool(tool_name)
            if success:
                console.print(f"[green]✓[/green] {message}")
                return 0
            else:
                console.print(f"[red]✗[/red] {message}")
                return 1

        elif action == 'whitelist':
            # Whitelist management: llf tool whitelist <add|remove|list> <tool_name> [pattern]
            whitelist_action = tool_name  # Second arg is whitelist action
            whitelist_tool = getattr(args, 'config_value', None)  # Third arg is tool name

            if not whitelist_action or whitelist_action not in ['add', 'remove', 'list']:
                console.print("[red]Error: Invalid whitelist action[/red]")
                console.print("Usage: llf tool whitelist <add|remove|list> <tool_name> [pattern]")
                return 1

            if not whitelist_tool:
                console.print("[red]Error: Tool name required[/red]")
                console.print("Usage: llf tool whitelist <add|remove|list> <tool_name> [pattern]")
                return 1

            if whitelist_action == 'list':
                patterns = tools_manager.list_whitelist_patterns(whitelist_tool)
                if patterns is None:
                    console.print(f"[red]✗[/red] Tool '{whitelist_tool}' not found")
                    return 1

                if not patterns:
                    console.print(f"\n[yellow]No whitelist patterns configured for '{whitelist_tool}'[/yellow]")
                    return 0

                console.print(f"\n[bold cyan]Whitelist patterns for '{whitelist_tool}':[/bold cyan]")
                for pattern in patterns:
                    console.print(f"  • {pattern}")
                return 0

            elif whitelist_action == 'add':
                # For add/remove, we need the pattern as fourth argument
                # This is tricky with current argparse setup - for now, show error
                console.print("[yellow]Note: Whitelist add/remove requires additional argument parsing[/yellow]")
                console.print("For now, please edit the tool's config.json or tools_registry.json directly")
                console.print(f"Add pattern to metadata.whitelist array for tool '{whitelist_tool}'")
                return 0

            elif whitelist_action == 'remove':
                console.print("[yellow]Note: Whitelist add/remove requires additional argument parsing[/yellow]")
                console.print("For now, please edit the tool's config.json or tools_registry.json directly")
                console.print(f"Remove pattern from metadata.whitelist array for tool '{whitelist_tool}'")
                return 0

        else:
            console.print(f"[red]Error: Unknown action '[bold]{action}[/bold]'[/red]")
            console.print("\nValid actions: list, enable, disable, info, config, import, export, whitelist")
            return 1

        return 0

    elif args.command == 'prompt':
        return prompt_command(args)

    elif args.command == 'trash':
        # Trash Management
        project_root = Path(__file__).parent.parent
        trash_dir = project_root / 'trash'
        trash_manager = TrashManager(trash_dir)

        action = getattr(args, 'action', 'list')
        trash_id = getattr(args, 'trash_id', None)
        item_type = getattr(args, 'type', None)
        older_than = getattr(args, 'older_than', None)
        force = getattr(args, 'force', False)
        dry_run = getattr(args, 'dry_run', False)
        empty_all = getattr(args, 'all', False)

        if action == 'list':
            # List trash items
            items = trash_manager.list_trash_items(item_type=item_type, older_than_days=older_than)

            if not items:
                console.print("[dim]Trash is empty[/dim]")
                return 0

            from rich.table import Table
            table = Table(show_header=True)
            table.add_column("Trash ID", style="cyan", width=30)
            table.add_column("Type", style="green", width=12)
            table.add_column("Name", style="white", width=25)
            table.add_column("Age (days)", style="yellow", width=12, justify="right")

            for item in items:
                trash_id_str = item.get('trash_id', 'Unknown')
                item_type_str = item.get('item_type', 'Unknown')
                item_name = item.get('item_name', 'Unknown')
                age_days = item.get('age_days', 0)

                table.add_row(trash_id_str, item_type_str, item_name, str(age_days))

            console.print()
            console.print(table)
            console.print()
            console.print(f"[dim]Total items: {len(items)}[/dim]")
            console.print()

            # Show stats
            stats = trash_manager.get_trash_stats()
            if stats['items_over_30_days'] > 0:
                console.print(f"[yellow]⚠ {stats['items_over_30_days']} item(s) are over 30 days old and can be permanently deleted[/yellow]")
                console.print(f"[dim]Use 'llf trash empty' to remove them[/dim]")
                console.print()

            return 0

        elif action == 'info':
            if not trash_id:
                console.print("[red]Error: Trash ID required[/red]")
                console.print("Usage: llf trash info <TRASH_ID>")
                return 1

            metadata = trash_manager.get_trash_info(trash_id)
            if not metadata:
                console.print(f"[red]Trash item not found: {trash_id}[/red]")
                return 1

            # Display detailed information
            from rich.panel import Panel

            item_type = metadata.get('item_type', 'Unknown')
            item_name = metadata.get('item_name', 'Unknown')
            deleted_date = metadata.get('deleted_date', 'Unknown')
            age_days = metadata.get('age_days', 0)
            moved_items = metadata.get('moved_items', [])

            info_text = f"""[bold]Item Type:[/bold] {item_type}
[bold]Item Name:[/bold] {item_name}
[bold]Deleted:[/bold] {deleted_date}
[bold]Age:[/bold] {age_days} days
[bold]Files:[/bold] {len(moved_items)} file(s)"""

            console.print()
            console.print(Panel(info_text, title=f"Trash Item: {trash_id}", border_style="cyan"))
            console.print()

            # Show file paths
            console.print("[bold]Original Locations:[/bold]")
            for item in moved_items:
                original_path = item.get('original_path', 'Unknown')
                console.print(f"  [dim]{original_path}[/dim]")
            console.print()

            # Show recovery instructions
            console.print("[bold]Recovery:[/bold]")
            console.print(f"  [cyan]llf trash restore {trash_id}[/cyan]")
            console.print()

            return 0

        elif action == 'restore':
            if not trash_id:
                console.print("[red]Error: Trash ID required[/red]")
                console.print("Usage: llf trash restore <TRASH_ID>")
                return 1

            success, message = trash_manager.restore_from_trash(trash_id)
            if success:
                console.print(f"[green]✓ {message}[/green]")
                return 0
            else:
                console.print(f"[red]✗ {message}[/red]")
                return 1

        elif action == 'empty':
            # Determine what to delete
            if empty_all:
                days = 0
            elif older_than:
                days = older_than
            else:
                days = 30

            # Get items that would be deleted
            items_to_delete = trash_manager.list_trash_items(older_than_days=days)

            if not items_to_delete:
                console.print(f"[dim]No items to delete (threshold: {days} days)[/dim]")
                return 0

            # Show what will be deleted
            console.print(f"\n[yellow]Items to be permanently deleted ({len(items_to_delete)}):[/yellow]\n")
            for item in items_to_delete:
                item_name = item.get('item_name', 'Unknown')
                item_type = item.get('item_type', 'Unknown')
                age_days = item.get('age_days', 0)
                console.print(f"  [dim]{item_type}:[/dim] {item_name} [dim]({age_days} days old)[/dim]")
            console.print()

            # Confirm if not forced or dry-run
            if dry_run:
                console.print(f"[cyan]Dry run complete: {len(items_to_delete)} items would be deleted[/cyan]")
                return 0

            if not force:
                console.print("[yellow]⚠ This action cannot be undone![/yellow]")
                response = input("Continue? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    console.print("[dim]Cancelled[/dim]")
                    return 0

            # Empty trash
            deleted_count, deleted_ids = trash_manager.empty_trash(
                older_than_days=days,
                force=empty_all,
                dry_run=False
            )

            console.print(f"\n[green]✓ Permanently deleted {deleted_count} item(s) from trash[/green]\n")
            return 0

        else:
            console.print(f"[red]Unknown trash action: {action}[/red]")
            console.print("\nValid actions: list, info, restore, empty")
            return 1

    elif args.command == 'dev':
        # Development Tools
        from llf.dev_commands import DevCommands

        # Get tools directory
        tools_dir = Path(__file__).parent.parent / 'tools'
        dev_commands = DevCommands(tools_dir)

        action = getattr(args, 'action', None)
        tool_name = getattr(args, 'tool_name', None)

        if not action or action == 'create-tool':
            # Interactive tool creation wizard
            return dev_commands.create_tool_interactive()

        elif action == 'validate-tool':
            if not tool_name:
                console.print("[red]Error: Tool name required[/red]")
                console.print("Usage: llf dev validate-tool <tool_name>")
                return 1

            return dev_commands.validate_tool(tool_name)

        else:
            console.print(f"[red]Unknown dev action: {action}[/red]")
            console.print("\nValid actions: create-tool, validate-tool")
            return 1

    elif args.command == 'chat' or args.command is None:
        # Check if this is a chat subcommand (history or export)
        chat_action = getattr(args, 'chat_action', None)

        if chat_action == 'history':
            # Handle chat history subcommands
            history_action = getattr(args, 'history_action', None)
            if history_action == 'list':
                return chat_history_list_command(config, args)
            elif history_action == 'info':
                return chat_history_info_command(config, args)
            elif history_action == 'cleanup':
                return chat_history_cleanup_command(config, args)
            elif history_action == 'delete':
                return chat_history_delete_command(config, args)
            else:
                console.print("[red]Unknown history action[/red]")
                return 1

        elif chat_action == 'export':
            # Handle chat export command
            return chat_export_command(config, args)

        # No subcommand - start interactive chat
        # Override model settings if specified via CLI flags
        if hasattr(args, 'huggingface_model') and args.huggingface_model:
            config.model_name = args.huggingface_model
            config.custom_model_dir = None  # Clear custom dir when using HF model
        elif hasattr(args, 'gguf_dir') and args.gguf_dir and hasattr(args, 'gguf_file') and args.gguf_file:
            # Set custom model directory and GGUF file
            config.custom_model_dir = config.model_dir / args.gguf_dir
            config.gguf_file = args.gguf_file

        # Get server control flags
        auto_start = getattr(args, 'auto_start_server', False)
        no_start = getattr(args, 'no_server_start', False)

        # Get history flag (default is True, disabled with --no-history)
        save_history = not getattr(args, 'no_history', False)

        # Get CLI question if provided
        cli_question = getattr(args, 'cli', None)

        # Handle session continuation and import
        imported_session = None
        continue_session_id = getattr(args, 'continue_session', None)
        import_session_file = getattr(args, 'import_session', None)

        # Check that both aren't specified
        if continue_session_id and import_session_file:
            console.print("[red]Error: Cannot use both --continue-session and --import-session[/red]")
            console.print("Use --continue-session for saved session IDs, --import-session for external files")
            return 1

        if continue_session_id or import_session_file:
            from llf.chat_history import ChatHistory
            history_dir = Path(config.config_file).parent / 'chat_history' if config.config_file else Path.cwd() / 'chat_history'
            chat_history_manager = ChatHistory(history_dir)

            if continue_session_id:
                # Continue from a saved session ID (not a file path)
                session_data = chat_history_manager.load_session(continue_session_id)
                if session_data:
                    imported_session = session_data
                else:
                    console.print(f"[red]Could not find session: {continue_session_id}[/red]")
                    console.print("[dim]Use 'llf chat history list' to see available sessions[/dim]")
                    return 1

            elif import_session_file:
                # Import from an external file (.json, .md, .txt)
                import_path = Path(import_session_file)
                if not import_path.exists():
                    console.print(f"[red]File not found: {import_session_file}[/red]")
                    return 1

                # Check file extension
                if import_path.suffix.lower() not in ['.json', '.md', '.markdown', '.txt']:
                    console.print(f"[red]Unsupported file format: {import_path.suffix}[/red]")
                    console.print("[yellow]Supported formats: .json, .md, .txt[/yellow]")
                    return 1

                imported_session = chat_history_manager.import_session(import_path)
                if not imported_session:
                    console.print(f"[red]Failed to import session from: {import_session_file}[/red]")
                    return 1

        # Default to chat
        cli = CLI(config, prompt_config=prompt_config, auto_start_server=auto_start, no_server_start=no_start, save_history=save_history, imported_session=imported_session)
        return cli.run(cli_question=cli_question)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())

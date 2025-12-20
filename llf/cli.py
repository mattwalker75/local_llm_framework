#!/usr/bin/env python
"""
CLI interface module for Local LLM Framework.

This module provides the command-line interface for interacting with LLMs.

Design: Modular CLI that separates UI from business logic for future extensibility.
Future: Can be extended to support different modes (chat, completion, batch, etc.).
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional
import signal
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from .logging_config import setup_logging, get_logger, disable_external_loggers
from .config import Config, get_config
from .model_manager import ModelManager
from .llm_runtime import LLMRuntime
from .prompt_config import PromptConfig, get_prompt_config

logger = get_logger(__name__)
console = Console()


class CLI:
    """
    Command-line interface for LLF.

    Provides interactive prompt loop and command handling.
    """

    def __init__(self, config: Config, prompt_config: Optional[PromptConfig] = None, auto_start_server: bool = False, no_server_start: bool = False):
        """
        Initialize CLI.

        Args:
            config: Configuration instance.
            prompt_config: Optional prompt configuration for formatting LLM messages.
            auto_start_server: Automatically start server if not running.
            no_server_start: Do not start server if not running (exit with error).
        """
        self.config = config
        self.prompt_config = prompt_config
        self.model_manager = ModelManager(config)
        self.runtime = LLMRuntime(config, self.model_manager, prompt_config)
        self.running = False
        self.auto_start_server = auto_start_server
        self.no_server_start = no_server_start
        self.started_server = False  # Track if this instance started the server

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, _signum, _frame):
        """Handle shutdown signals gracefully."""
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.running = False
        self.shutdown()
        sys.exit(0)

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

        welcome_text = f"""
# Local LLM Framework

**Model:** {model_display}
**Mode:** Interactive Chat

Type your messages and press Enter to send.
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

Simply type your message and press Enter to chat with the LLM.
        """
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

        if self.runtime.is_server_running():
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
            response = Prompt.ask(
                "Would you like to start the server?",
                choices=["y", "n"],
                default="y"
            )
            if response.lower() != 'y':
                console.print("[yellow]Server not started. Exiting.[/yellow]")
                return False

        console.print("[yellow]Starting LLM server...[/yellow]")
        console.print("[dim]This may take a minute or two...[/dim]")

        try:
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
        conversation_history = []

        # Print initial separator before first user input
        console.print("[dim]" + "─" * 60 + "[/dim]")

        while self.running:
            try:
                # Print "You:" label on separate line with blank line after
                console.print("\n[green]You[/green]:\n")

                # Get user input
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

                    # Generate response using streaming chat API
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

                except Exception as e:
                    console.print(f"[red]Error generating response: {e}[/red]")
                    logger.error(f"Generation error: {e}")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Interactive loop error: {e}")

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
        if args.action == 'status':
            # Check if local server is configured
            if not config.has_local_server_config():
                console.print("[yellow]Local LLM server is not configured[/yellow]")
                console.print(f"Using external API: [cyan]{config.api_base_url}[/cyan]")
                console.print(f"Model: [cyan]{config.model_name}[/cyan]")
                return 0

            # Check server status
            if runtime.is_server_running():
                console.print(f"[green]✓[/green] Server is running on {config.get_server_url()}")
                console.print(f"[cyan]Model: {config.model_name}[/cyan]")
                return 0
            else:
                console.print("[yellow]✗[/yellow] Server is not running")
                return 1

        elif args.action == 'start':
            # Start server
            if runtime.is_server_running():
                console.print(f"[yellow]Server is already running on {config.get_server_url()}[/yellow]")
                return 0

            # Ensure model is downloaded (only for HuggingFace models, not custom GGUF)
            if config.custom_model_dir is None and not model_manager.is_model_downloaded():
                console.print(f"[yellow]Model {config.model_name} is not downloaded.[/yellow]")
                console.print("[yellow]Downloading model... This may take a while.[/yellow]")
                try:
                    model_manager.download_model()
                    console.print("[green]Model downloaded successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Failed to download model: {e}[/red]")
                    return 1

            # Display appropriate model info based on configuration
            if config.custom_model_dir:
                model_display = f"{config.custom_model_dir.name}/{config.gguf_file}"
            else:
                model_display = config.model_name

            # Determine server host based on --share flag
            server_host = "0.0.0.0" if args.share else None  # None uses config default (127.0.0.1)

            if args.share:
                console.print(f"[yellow]Starting llama-server with model {model_display} (accessible on local network)...[/yellow]")
            else:
                console.print(f"[yellow]Starting llama-server with model {model_display} (localhost only)...[/yellow]")
            console.print("[dim]This may take a minute or two...[/dim]")

            runtime.start_server(server_host=server_host)

            # Display appropriate access message
            if args.share:
                console.print(f"[green]✓ Server started successfully on 0.0.0.0:{config.server_port}[/green]")
                console.print(f"[cyan]Access from this device: http://127.0.0.1:{config.server_port}/v1[/cyan]")
                console.print(f"[cyan]Access from network: http://YOUR_IP:{config.server_port}/v1[/cyan]")
            else:
                console.print(f"[green]✓ Server started successfully on {config.get_server_url()}[/green]")

            if args.daemon:
                console.print("[cyan]Server is running in daemon mode.[/cyan]")
                console.print(f"[cyan]Use 'llf server stop' to stop the server.[/cyan]")
            else:
                console.print("[cyan]Server is running. Press Ctrl+C to stop.[/cyan]")
                try:
                    # Keep the process alive
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping server...[/yellow]")
                    runtime.stop_server()
                    console.print("[green]Server stopped.[/green]")

            return 0

        elif args.action == 'stop':
            # Stop server
            if not runtime.is_server_running():
                console.print("[yellow]Server is not running[/yellow]")
                return 0

            console.print("[yellow]Stopping server...[/yellow]")
            runtime.stop_server()
            console.print("[green]✓ Server stopped successfully[/green]")
            return 0

        elif args.action == 'restart':
            # Restart server
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
  llf chat --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf chat --gguf-dir test_gguf --gguf-file my-model.gguf

  # CLI mode (non-interactive, for scripting)
  llf chat --cli "What is 2+2?"                    Ask a single question and exit
  llf chat --cli "Explain Python" --auto-start-server
  llf chat --cli "Code review" --huggingface-model custom/model
  cat file.txt | llf chat --cli "Summarize this"  Pipe data to LLM with question

  # Server management
  llf server start                 Start llama-server (localhost only, stays in foreground)
  llf server start --share         Start server accessible on local network (0.0.0.0)
  llf server start --daemon        Start server in background (localhost only)
  llf server start --share --daemon  Start server in background (network accessible)
  llf server start --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf server start --gguf-dir test_gguf --gguf-file my-model.gguf
  llf server stop                  Stop running server
  llf server status                Check if server is running
  llf server restart               Restart server with current model
  llf server restart --share       Restart server with network access
  llf server list_models           List available models from configured endpoint

  # Model management
  llf model download               Download default HuggingFace model
  llf model download --huggingface-model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf model download --url https://example.com/model.gguf --name my-model
  llf model list                   List downloaded models
  llf model info                   Show default model information
  llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

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
  llf datastore list               List all available data stores
  llf datastore list --attached    List only attached data stores
  llf datastore attach             Attach data store to query
  llf datastore detach             Detach data store
  llf datastore info DATA_STORE_NAME  Show data store information

  # Module management
  llf module list                  List modules
  llf module list --enabled        List only enabled modules
  llf module enable                Enable a module
  llf module disable               Disable a module
  llf module info MODULE_NAME      Show module information

  # Tool management
  llf tool list                    List tools
  llf tool list --enabled          List only enabled tools
  llf tool enable TOOL_NAME        Enable a tool
  llf tool disable TOOL_NAME       Disable a tool
  llf tool info TOOL_NAME          Show tool information

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
        help='Start interactive chat with LLM',
        description='Start an interactive chat session with an LLM either locally running or remote.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  llf chat                                     Start interactive chat session
  llf chat --auto-start-server                 Auto-start server if not running
  llf chat --no-server-start                   Exit with error if server not running

  # CLI mode (non-interactive, for scripting)
  llf chat --cli "What is 2+2?"                Ask a single question and exit
  cat file.txt | llf chat --cli "Summarize this"  Pipe data to LLM with question

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
        '--cli',
        metavar='QUESTION',
        help='Non-interactive mode: ask a single question and exit (for scripting)'
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
  llf model info                        Show default model information
  llf model info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
                                        View information about a specific downloaded model
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
        description='Display all models currently downloaded and cached locally.'
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

    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Manage llama-server',
        description='''Start, stop, or check status of the locally running OpenAI compatible LLM server ( llama.cpp ).

Positional arguments:
  start        Start local LLM server (llama-server)
  stop         Stop local LLM server (llama-server)
  status       Display running status of local LLM server
  restart      Restart the local LLM server
  list_models  List available models hosted from LLM server
''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic server operations
  llf server start                             Start server with default model
  llf server stop                              Stop the running server
  llf server status                            Check server status
  llf server restart                           Restart the server

  # Server with options
  llf server start --share --daemon            Start server in background (network accessible)

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
        choices=['start', 'stop', 'status', 'restart', 'list_models'],
        help=argparse.SUPPRESS  # Suppress auto-generated help - using custom description instead
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
  attach DATA_STORE_NAME    Attach data store to query
  detach DATA_STORE_NAME    Detach data store
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
  disable MODULE_NAME       Disable a module
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

    # Tool command
    tool_parser = subparsers.add_parser(
        'tool',
        help='Tool Management',
        description='Manage tools that extend the ability of the LLM.\n( An example of a tool would be to enable the LLM to perform searches on the Internet )',
        epilog='''
actions:
  list                      List tools
  list --enabled            List only enabled tools
  enable TOOL_NAME          Enable a tool
  disable TOOL_NAME         Disable a tool
  info TOOL_NAME            Show tool information
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
        '--enabled',
        action='store_true',
        help='List only enabled tools (use with list action)'
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
        # Data Store Management (placeholder for future functionality)
        console.print("[yellow]Data Store Management[/yellow]")
        console.print("This command is reserved for future functionality.")
        console.print("\n[dim]Planned features:[/dim]")
        console.print("  • List available data stores (RAG data)")
        console.print("  • Attach data store to active session")
        console.print("  • Detach data store from session")
        console.print("  • List currently attached data stores")
        if args.action:
            console.print(f"\n[dim]Action '{args.action}' not yet implemented[/dim]")
        return 0

    elif args.command == 'module':
        # Module Management (placeholder for future functionality)
        console.print("[yellow]Module Management[/yellow]")
        console.print("This command is reserved for future functionality.")
        console.print("\n[dim]Planned features:[/dim]")
        console.print("  • Install and manage framework modules")
        console.print("  • Enable/disable plugins and extensions")
        console.print("  • Module configuration and updates")
        console.print("  • List available and installed modules")
        if args.action:
            console.print(f"\n[dim]Action '{args.action}' not yet implemented[/dim]")
        return 0

    elif args.command == 'tool':
        # Tool Management (placeholder for future functionality)
        console.print("[yellow]Tool Management[/yellow]")
        console.print("This command is reserved for future functionality.")
        console.print("\n[dim]Planned features:[/dim]")
        console.print("  • Manage LLM tool definitions")
        console.print("  • Configure function calling")
        console.print("  • Register and manage external integrations")
        console.print("  • List and test available tools")
        if args.action:
            console.print(f"\n[dim]Action '{args.action}' not yet implemented[/dim]")
        return 0

    elif args.command == 'chat' or args.command is None:
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

        # Get CLI question if provided
        cli_question = getattr(args, 'cli', None)

        # Default to chat
        cli = CLI(config, prompt_config=prompt_config, auto_start_server=auto_start, no_server_start=no_start)
        return cli.run(cli_question=cli_question)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())

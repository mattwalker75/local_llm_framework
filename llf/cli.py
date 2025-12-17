#!/usr/bin/env python
"""
CLI interface module for Local LLM Framework.

This module provides the command-line interface for interacting with LLMs.

Design: Modular CLI that separates UI from business logic for future extensibility.
Future: Can be extended to support different modes (chat, completion, batch, etc.).
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import signal

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from .logging_config import setup_logging, get_logger, disable_external_loggers
from .config import Config, get_config
from .model_manager import ModelManager
from .llm_runtime import LLMRuntime

logger = get_logger(__name__)
console = Console()


class CLI:
    """
    Command-line interface for LLF.

    Provides interactive prompt loop and command handling.
    """

    def __init__(self, config: Config, auto_start_server: bool = False, no_server_start: bool = False):
        """
        Initialize CLI.

        Args:
            config: Configuration instance.
            auto_start_server: Automatically start server if not running.
            no_server_start: Do not start server if not running (exit with error).
        """
        self.config = config
        self.model_manager = ModelManager(config)
        self.runtime = LLMRuntime(config, self.model_manager)
        self.running = False
        self.auto_start_server = auto_start_server
        self.no_server_start = no_server_start
        self.started_server = False  # Track if this instance started the server

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.running = False
        self.shutdown()
        sys.exit(0)

    def print_welcome(self) -> None:
        """Print welcome message."""
        welcome_text = f"""
# Local LLM Framework

**Model:** {self.config.model_name}
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
- `clear` - Clear the screen

# Chat Mode

Simply type your message and press Enter to chat with the LLM.

# Multiline Input

To provide multiline input (e.g., paste document content):
1. Type `START` and press Enter
2. Paste or type your content (can be multiple lines)
3. Type `END` on a new line and press Enter

This is useful for pasting content from PDFs, documents, or code files.
        """
        console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))

    def print_info(self) -> None:
        """Print model and system information."""
        model_info = self.model_manager.get_model_info()

        info_lines = [
            f"**Model:** {model_info['name']}",
            f"**Path:** {model_info['path']}",
            f"**Downloaded:** {'Yes' if model_info['downloaded'] else 'No'}",
        ]

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

        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

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
                    console.print("[yellow]Goodbye![/yellow]")
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
                    continue

                # Generate response
                console.print("[bold blue]Assistant:[/bold blue] ", end="")

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
            self.print_welcome()

            # Ensure model is downloaded
            if not self.ensure_model_ready():
                return 1

            # Start server
            if not self.start_server():
                return 1

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

    model_name = args.model or config.model_name
    token = getattr(args, 'token', None)

    console.print(f"[yellow]Downloading model: {model_name}[/yellow]")

    try:
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

    # Override model if specified
    if hasattr(args, 'model') and args.model:
        config.model_name = args.model

    model_manager = ModelManager(config)
    runtime = LLMRuntime(config, model_manager)

    try:
        if args.action == 'status':
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

            console.print(f"[yellow]Starting llama-server with model {config.model_name}...[/yellow]")
            console.print("[dim]This may take a minute or two...[/dim]")

            runtime.start_server()
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

            console.print("[dim]Starting server...[/dim]")
            runtime.start_server()
            console.print(f"[green]✓ Server restarted successfully on {config.get_server_url()}[/green]")
            return 0

        elif args.action == 'list_models':
            # List available models from the endpoint
            console.print(f"[cyan]Querying models from {config.api_base_url}...[/cyan]")
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
  llf chat --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

  # CLI mode (non-interactive, for scripting)
  llf chat --cli "What is 2+2?"                    Ask a single question and exit
  llf chat --cli "Explain Python" --auto-start-server
  llf chat --cli "Code review" --model custom/model
  cat file.txt | llf chat --cli "Summarize this"  Pipe data to LLM with question

  # Server management
  llf server start                 Start llama-server (stays in foreground)
  llf server start --daemon        Start server in background
  llf server start --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf server stop                  Stop running server
  llf server status                Check if server is running
  llf server restart               Restart server with current model
  llf server list_models           List available models from configured endpoint

  # Model management (GGUF format)
  llf download                     Download default GGUF model
  llf download --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
  llf list                         List downloaded models
  llf info                         Show model information
  llf info --model Qwen/Qwen2.5-Coder-7B-Instruct-GGUF

  # Configuration
  llf -d /custom/path              Set custom download directory
  llf --log-level DEBUG            Enable debug logging
  llf --log-file llf.log           Log to file (in addition to console)
  llf --log-level DEBUG --log-file /var/log/llf.log

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
        version='%(prog)s 0.1.0 (Phase 1)'
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
        description='Start an interactive chat session with the locally running LLM.'
    )
    chat_parser.add_argument(
        '--model',
        metavar='NAME',
        help='Model to use for chat (e.g., "mistralai/Mistral-7B-Instruct-v0.2"). Must be downloaded first.'
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

    # Download command
    download_parser = subparsers.add_parser(
        'download',
        help='Download a model from HuggingFace Hub',
        description='Download and cache a model locally for use with LLF.'
    )
    download_parser.add_argument(
        '--model',
        metavar='NAME',
        help='Model name to download (e.g., "Qwen/Qwen3-Coder-30B-A3B-Instruct")'
    )
    download_parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if model exists locally'
    )
    download_parser.add_argument(
        '--token',
        metavar='TOKEN',
        help='HuggingFace API token for private models'
    )

    # List command
    list_parser = subparsers.add_parser(
        'list',
        help='List all downloaded models',
        description='Display all models currently downloaded and cached locally.'
    )

    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show detailed model information',
        description='Display detailed information about a specific model including size, location, and verification status.'
    )
    info_parser.add_argument(
        '--model',
        metavar='NAME',
        help='Model name to show info for (default: configured default model)'
    )

    # Server command
    server_parser = subparsers.add_parser(
        'server',
        help='Manage llama-server',
        description='Start, stop, or check status of the llama.cpp inference server.'
    )
    server_parser.add_argument(
        'action',
        choices=['start', 'stop', 'status', 'restart', 'list_models'],
        help='Server action to perform'
    )
    server_parser.add_argument(
        '--model',
        metavar='NAME',
        help='Model to load (for start/restart actions)'
    )
    server_parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run server in background (daemon mode)'
    )

    # Parse arguments
    args = parser.parse_args()

    # Load or create config first (to get log_level if not specified on CLI)
    if args.config:
        config = get_config(args.config)
    else:
        config = get_config()

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
    if args.command == 'download':
        return download_command(args)
    elif args.command == 'list':
        return list_command(args)
    elif args.command == 'info':
        return info_command(args)
    elif args.command == 'server':
        return server_command(args)
    elif args.command == 'chat' or args.command is None:
        # Override model if specified via --model parameter
        if hasattr(args, 'model') and args.model:
            config.model_name = args.model

        # Get server control flags
        auto_start = getattr(args, 'auto_start_server', False)
        no_start = getattr(args, 'no_server_start', False)

        # Get CLI question if provided
        cli_question = getattr(args, 'cli', None)

        # Default to chat
        cli = CLI(config, auto_start_server=auto_start, no_server_start=no_start)
        return cli.run(cli_question=cli_question)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())

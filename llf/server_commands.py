"""
Enhanced server management commands for multi-server support.

This module provides CLI commands for managing multiple local LLM servers.
"""

from rich.console import Console
from rich.table import Table

from .config import Config
from .llm_runtime import LLMRuntime
from .model_manager import ModelManager
from .logging_config import get_logger

logger = get_logger(__name__)
console = Console()


def list_servers_command(config: Config, runtime: LLMRuntime) -> int:
    """
    List all configured servers and their status.

    Args:
        config: Configuration instance.
        runtime: LLMRuntime instance.

    Returns:
        Exit code.
    """
    servers = config.list_servers()

    if not servers:
        console.print("[yellow]No local servers configured[/yellow]")
        return 0

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("NAME", style="green")
    table.add_column("PORT", style="cyan")
    table.add_column("STATUS", style="yellow")
    table.add_column("MODEL", style="dim")

    for server_name in servers:
        server_config = config.get_server_by_name(server_name)
        if not server_config:
            continue

        # Check status
        is_running = runtime.is_server_running_by_name(server_name)
        status = "[green]Running[/green]" if is_running else "[dim]Stopped[/dim]"

        # Get model info
        model_info = server_config.gguf_file or "Not configured"
        if server_config.model_dir:
            try:
                rel_path = server_config.model_dir.relative_to(config.model_dir)
                model_info = f"{rel_path}/{server_config.gguf_file}" if server_config.gguf_file else str(rel_path)
            except ValueError:
                pass

        table.add_row(
            server_name,
            str(server_config.server_port),
            status,
            model_info
        )

    # Add separator and active endpoint indicator
    table.add_section()

    # Determine active endpoint
    if config.is_using_external_api():
        # External API (ChatGPT, Claude, etc.)
        table.add_row(
            "[bold magenta]Active Endpoint[/bold magenta]",
            "[dim]N/A[/dim]",
            "[yellow]Remote[/yellow]",
            f"[dim]{config.api_base_url}[/dim]"
        )
    else:
        # Local server
        active_server_name = config.default_local_server or "default"
        active_server_config = config.get_server_by_name(active_server_name)

        if active_server_config:
            # Check if active server is running
            is_active_running = runtime.is_server_running_by_name(active_server_name)
            active_status = "[green]Running[/green]" if is_active_running else "[dim]Stopped[/dim]"

            # Get model info for active server
            active_model_info = active_server_config.gguf_file or "Not configured"
            if active_server_config.model_dir:
                try:
                    rel_path = active_server_config.model_dir.relative_to(config.model_dir)
                    active_model_info = f"{rel_path}/{active_server_config.gguf_file}" if active_server_config.gguf_file else str(rel_path)
                except ValueError:
                    pass

            table.add_row(
                f"[bold magenta]Active Endpoint → {active_server_name}[/bold magenta]",
                str(active_server_config.server_port),
                active_status,
                active_model_info
            )
        else:
            # Shouldn't happen, but handle gracefully
            table.add_row(
                "[bold magenta]Active Endpoint[/bold magenta]",
                "[dim]N/A[/dim]",
                "[red]Not Found[/red]",
                "[dim]Configuration error[/dim]"
            )

    console.print(table)
    return 0


def start_server_command(config: Config, runtime: LLMRuntime, model_manager: ModelManager, args) -> int:
    """
    Start a server (with optional name for multi-server setups).

    Args:
        config: Configuration instance.
        runtime: LLMRuntime instance.
        model_manager: ModelManager instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    server_name = getattr(args, 'server_name', None)
    force = getattr(args, 'force', False)

    # Multi-server mode: Start specific server by name
    if server_name:
        try:
            # Check if server is already running
            if runtime.is_server_running_by_name(server_name):
                server_config = config.get_server_by_name(server_name)
                console.print(f"[yellow]Server '{server_name}' is already running on http://{server_config.server_host}:{server_config.server_port}/v1[/yellow]")
                return 0

            console.print(f"[yellow]Starting server '{server_name}'...[/yellow]")
            console.print("[dim]This may take a minute or two...[/dim]")

            runtime.start_server_by_name(server_name, force=force)

            # Verify server actually started (user may have cancelled during memory safety prompt)
            if not runtime.is_server_running_by_name(server_name):
                # Server didn't start (user cancelled or error occurred)
                return 0

            server_config = config.get_server_by_name(server_name)
            console.print(f"[green]✓ Server '{server_name}' started successfully[/green]")
            console.print(f"[cyan]URL: http://{server_config.server_host}:{server_config.server_port}/v1[/cyan]")

            if args.daemon:
                console.print("[cyan]Server is running in daemon mode.[/cyan]")
                console.print(f"[cyan]Use 'llf server stop {server_name}' to stop it.[/cyan]")
            else:
                console.print("[cyan]Server is running. Press Ctrl+C to stop.[/cyan]")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    console.print(f"\n[yellow]Stopping server '{server_name}'...[/yellow]")
                    runtime.stop_server_by_name(server_name)
                    console.print("[green]Server stopped.[/green]")

            return 0

        except Exception as e:
            console.print(f"[red]Failed to start server '{server_name}': {e}[/red]")
            return 1

    # No server name specified - start default server from default_local_server setting
    default_server_name = config.default_local_server
    if default_server_name and isinstance(default_server_name, str) and config.get_server_by_name(default_server_name):
        # Use the configured default server
        if runtime.is_server_running_by_name(default_server_name):
            server_config = config.get_server_by_name(default_server_name)
            console.print(f"[yellow]Default server '{default_server_name}' is already running on http://{server_config.server_host}:{server_config.server_port}/v1[/yellow]")
            return 0

        console.print(f"[yellow]Starting default server '{default_server_name}'...[/yellow]")
        console.print("[dim]This may take a minute or two...[/dim]")

        runtime.start_server_by_name(default_server_name, force=force)

        # Verify server actually started
        if not runtime.is_server_running_by_name(default_server_name):
            return 0

        server_config = config.get_server_by_name(default_server_name)
        console.print(f"[green]✓ Server '{default_server_name}' started successfully[/green]")
        console.print(f"[cyan]URL: http://{server_config.server_host}:{server_config.server_port}/v1[/cyan]")

        if args.daemon:
            console.print("[cyan]Server is running in daemon mode.[/cyan]")
            console.print(f"[cyan]Use 'llf server stop' to stop it.[/cyan]")
        else:
            console.print("[cyan]Server is running. Press Ctrl+C to stop.[/cyan]")
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print(f"\n[yellow]Stopping server '{default_server_name}'...[/yellow]")
                runtime.stop_server_by_name(default_server_name)
                console.print("[green]Server stopped.[/green]")

        return 0

    # Fallback to legacy mode if no default_local_server is set
    if runtime.is_server_running():
        console.print(f"[yellow]Default server is already running on {config.get_server_url()}[/yellow]")
        return 0

    # Ensure model is downloaded
    if config.custom_model_dir is None and not model_manager.is_model_downloaded():
        console.print(f"[yellow]Model {config.model_name} is not downloaded.[/yellow]")
        console.print("[yellow]Downloading model... This may take a while.[/yellow]")
        try:
            model_manager.download_model()
            console.print("[green]Model downloaded successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to download model: {e}[/red]")
            return 1

    # Display model info
    if config.custom_model_dir:
        model_display = f"{config.custom_model_dir.name}/{config.gguf_file}"
    else:
        model_display = config.model_name

    # Determine server host
    server_host = "0.0.0.0" if args.share else None

    if args.share:
        console.print(f"[yellow]Starting llama-server with model {model_display} (accessible on local network)...[/yellow]")
    else:
        console.print(f"[yellow]Starting llama-server with model {model_display} (localhost only)...[/yellow]")
    console.print("[dim]This may take a minute or two...[/dim]")

    runtime.start_server(server_host=server_host)

    # Verify server actually started (user may have cancelled during memory safety prompt)
    if not runtime.is_server_running():
        # Server didn't start (user cancelled or error occurred)
        return 0

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
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping server...[/yellow]")
            runtime.stop_server()
            console.print("[green]Server stopped.[/green]")

    return 0


def stop_server_command(config: Config, runtime: LLMRuntime, args) -> int:
    """
    Stop a server (with optional name for multi-server setups).

    Args:
        config: Configuration instance.
        runtime: LLMRuntime instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    server_name = getattr(args, 'server_name', None)

    # Multi-server mode
    if server_name:
        if not runtime.is_server_running_by_name(server_name):
            console.print(f"[yellow]Server '{server_name}' is not running[/yellow]")
            return 0

        console.print(f"[yellow]Stopping server '{server_name}'...[/yellow]")
        runtime.stop_server_by_name(server_name)
        console.print(f"[green]✓ Server '{server_name}' stopped successfully[/green]")
        return 0

    # No server name specified - stop default server from default_local_server setting
    default_server_name = config.default_local_server
    if default_server_name and isinstance(default_server_name, str) and config.get_server_by_name(default_server_name):
        # Use the configured default server
        if not runtime.is_server_running_by_name(default_server_name):
            console.print(f"[yellow]Default server '{default_server_name}' is not running[/yellow]")
            return 0

        console.print(f"[yellow]Stopping default server '{default_server_name}'...[/yellow]")
        runtime.stop_server_by_name(default_server_name)
        console.print(f"[green]✓ Server '{default_server_name}' stopped successfully[/green]")
        return 0

    # Fallback to legacy mode if no default_local_server is set
    if not runtime.is_server_running():
        console.print("[yellow]Default server is not running[/yellow]")
        return 0

    console.print("[yellow]Stopping server...[/yellow]")
    runtime.stop_server()
    console.print("[green]✓ Server stopped successfully[/green]")
    return 0


def status_server_command(config: Config, runtime: LLMRuntime, args) -> int:
    """
    Show server status (with optional name for multi-server setups).

    Args:
        config: Configuration instance.
        runtime: LLMRuntime instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    server_name = getattr(args, 'server_name', None)

    # Multi-server mode: Show specific server status
    if server_name:
        server_config = config.get_server_by_name(server_name)
        if not server_config:
            console.print(f"[red]Server '{server_name}' not found in configuration[/red]")
            return 1

        is_running = runtime.is_server_running_by_name(server_name)
        if is_running:
            console.print(f"[green]✓[/green] Server '{server_name}' is running")
            console.print(f"[cyan]URL: http://{server_config.server_host}:{server_config.server_port}/v1[/cyan]")
            if server_config.gguf_file:
                console.print(f"[cyan]Model: {server_config.gguf_file}[/cyan]")
            return 0
        else:
            console.print(f"[yellow]✗[/yellow] Server '{server_name}' is not running")
            return 1

    # No server name specified - show all local servers status
    if not config.has_local_server_config():
        console.print("[yellow]Local LLM server is not configured[/yellow]")
        console.print(f"Using external API: [cyan]{config.api_base_url}[/cyan]")
        console.print(f"Model: [cyan]{config.model_name}[/cyan]")
        return 0

    # Show status of all configured servers
    from rich.table import Table
    table = Table(title="Local Server Status", show_header=True, header_style="bold cyan")
    table.add_column("Server Name", style="white")
    table.add_column("Port", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Model", style="dim")

    # Get default server for highlighting
    default_server_name = config.default_local_server

    # List all servers
    for name, server_config in config.servers.items():
        is_running = runtime.is_server_running_by_name(name)
        status = "[green]Running[/green]" if is_running else "[dim]Stopped[/dim]"

        # Get model info
        model_info = server_config.gguf_file or "Not configured"
        if server_config.model_dir:
            try:
                rel_path = server_config.model_dir.relative_to(config.model_dir)
                model_info = f"{rel_path}/{server_config.gguf_file}" if server_config.gguf_file else str(rel_path)
            except (ValueError, AttributeError):
                pass

        # Highlight default server
        name_display = f"[bold magenta]{name}[/bold magenta] (default)" if name == default_server_name else name

        table.add_row(name_display, str(server_config.server_port), status, model_info)

    console.print(table)
    return 0


def switch_server_command(config: Config, args) -> int:
    """
    Switch the default local server.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    server_name = args.server_name

    try:
        # Update default server (also updates model_name)
        config.update_default_server(server_name)

        # Save to config file
        config.save_to_file(config.DEFAULT_CONFIG_FILE)

        server_config = config.get_server_by_name(server_name)
        console.print(f"[green]✓ Switched to server '{server_name}'[/green]")
        console.print(f"[cyan]URL: {config.api_base_url}[/cyan]")
        console.print(f"[cyan]Port: {server_config.server_port}[/cyan]")
        console.print(f"[cyan]Model: {config.model_name}[/cyan]")
        console.print(f"\n[dim]Config file updated: {config.DEFAULT_CONFIG_FILE}[/dim]")

        return 0

    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Failed to switch server: {e}[/red]")
        return 1

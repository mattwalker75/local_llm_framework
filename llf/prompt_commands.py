"""
Prompt template CLI commands for the Local LLM Framework.

This module provides command handlers for prompt template management.
"""

import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from .prompt_manager import PromptManager
from .config import Config

console = Console()


def get_prompt_manager(config: Config) -> PromptManager:
    """
    Get or create a PromptManager instance.

    Args:
        config: Configuration instance.

    Returns:
        PromptManager instance.
    """
    config_dir = Path(config.config_file).parent if config.config_file else Path.cwd() / 'configs'
    templates_dir = config_dir / 'prompt_templates'
    registry_file = templates_dir / 'prompt_templates_registry.json'
    active_prompt_file = config_dir / 'config_prompt.json'

    return PromptManager(templates_dir, registry_file, active_prompt_file)


def list_templates_command(config: Config, args) -> int:
    """
    List available prompt templates.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)

    # Get filter options
    category = getattr(args, 'category', None)
    enabled_only = getattr(args, 'enabled', False)

    templates = manager.list_templates(category=category, enabled_only=enabled_only)

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        if category:
            console.print(f"[dim]No templates in category '{category}'[/dim]")
        return 0

    # Get active template
    active_template = manager.get_active_template()

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("NAME", style="green")
    table.add_column("DISPLAY NAME", style="cyan")
    table.add_column("CATEGORY", style="yellow")
    table.add_column("VERSION", style="dim")
    table.add_column("AUTHOR", style="dim")
    table.add_column("STATUS", style="white")

    for template in templates:
        status = ""
        if template["name"] == active_template:
            status = "[bold magenta]● ACTIVE[/bold magenta]"
        elif not template.get("enabled", True):
            status = "[dim]○ Disabled[/dim]"
        else:
            status = "[green]✓ Enabled[/green]"

        table.add_row(
            template["name"],
            template["display_name"],
            template["category"],
            template.get("version", "1.0"),
            template.get("author", "unknown"),
            status
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(templates)} templates[/dim]")

    if active_template:
        console.print(f"[dim]Active template: {active_template}[/dim]")

    return 0


def info_template_command(config: Config, args) -> int:
    """
    Show detailed information about a template.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name

    template = manager.get_template(template_name)
    if not template:
        console.print(f"[red]Template '{template_name}' not found[/red]")
        return 1

    # Load template config to show variables
    template_config = manager.load_template_config(template_name)

    # Display template info
    info_text = f"""[bold cyan]{template['display_name']}[/bold cyan]

[yellow]Name:[/yellow] {template['name']}
[yellow]Description:[/yellow] {template['description']}
[yellow]Category:[/yellow] {template['category']}
[yellow]Version:[/yellow] {template.get('version', '1.0')}
[yellow]Author:[/yellow] {template.get('author', 'unknown')}
[yellow]Status:[/yellow] {'[green]Enabled[/green]' if template.get('enabled', True) else '[dim]Disabled[/dim]'}
[yellow]Tags:[/yellow] {', '.join(template.get('tags', []))}

[yellow]Created:[/yellow] {template.get('created_date', 'unknown')}
[yellow]Modified:[/yellow] {template.get('last_modified', 'unknown')}
"""

    # Show variables if present
    if template_config and 'variables' in template_config:
        variables = template_config['variables']
        if variables:
            info_text += "\n[bold yellow]Variables:[/bold yellow]\n"
            for var_name, var_info in variables.items():
                default = var_info.get('default', '')
                required = var_info.get('required', False)
                desc = var_info.get('description', '')
                req_label = '[red]*required[/red]' if required else ''
                info_text += f"  • {var_name} {req_label}\n"
                if desc:
                    info_text += f"    {desc}\n"
                if default:
                    info_text += f"    [dim]Default: {default}[/dim]\n"

    # Show preview of prompts
    if template_config:
        info_text += "\n[bold yellow]Configuration:[/bold yellow]\n"
        if template_config.get('system_prompt'):
            preview = template_config['system_prompt'][:100]
            if len(template_config['system_prompt']) > 100:
                preview += "..."
            info_text += f"  [dim]System Prompt: {preview}[/dim]\n"
        if template_config.get('master_prompt'):
            preview = template_config['master_prompt'][:100]
            if len(template_config['master_prompt']) > 100:
                preview += "..."
            info_text += f"  [dim]Master Prompt: {preview}[/dim]\n"

    console.print(Panel(info_text, expand=False))
    return 0


def load_template_command(config: Config, args) -> int:
    """
    Load a template and apply it to the active prompt configuration.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name

    # Check if template exists
    template = manager.get_template(template_name)
    if not template:
        console.print(f"[red]Template '{template_name}' not found[/red]")
        console.print("[dim]Use 'llf prompt list' to see available templates[/dim]")
        return 1

    # Parse variables from --var arguments
    variables = {}
    var_args = getattr(args, 'var', [])
    if var_args:
        for var_assignment in var_args:
            if '=' in var_assignment:
                key, value = var_assignment.split('=', 1)
                variables[key.strip()] = value.strip()
            else:
                console.print(f"[yellow]Warning: Invalid variable format '{var_assignment}' (expected key=value)[/yellow]")

    # Apply template
    console.print(f"[yellow]Loading template '{template['display_name']}'...[/yellow]")

    if manager.apply_template(template_name, variables):
        console.print(f"[green]✓ Template '{template['display_name']}' loaded successfully[/green]")
        console.print(f"[dim]Active prompt config: {manager.active_prompt_file}[/dim]")

        if variables:
            console.print("\n[cyan]Applied variables:[/cyan]")
            for key, value in variables.items():
                console.print(f"  • {key} = {value}")

        return 0
    else:
        console.print(f"[red]Failed to load template '{template_name}'[/red]")
        return 1


def import_template_command(config: Config, args) -> int:
    """
    Import a new template from an external file.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)

    source_path = Path(args.template_name)
    name = getattr(args, 'name', None)
    display_name = getattr(args, 'display_name', None)
    description = getattr(args, 'description', None)
    category = getattr(args, 'category', 'general')
    tags = getattr(args, 'tags', None)

    # If name not provided, derive from filename
    if not name:
        name = source_path.stem.replace('config_prompt.', '').replace('.', '_')

    # If display name not provided, use name
    if not display_name:
        display_name = name.replace('_', ' ').title()

    # If description not provided, use default
    if not description:
        description = f"Imported template: {display_name}"

    # Parse tags
    tag_list = tags.split(',') if tags else []

    console.print(f"[yellow]Importing template from {source_path}...[/yellow]")

    if manager.import_template(
        source_path,
        name,
        display_name,
        description,
        category,
        author="user",
        tags=tag_list
    ):
        console.print(f"[green]✓ Template '{name}' imported successfully[/green]")
        console.print(f"[dim]Template directory: {manager.templates_dir / name}[/dim]")
        return 0
    else:
        return 1


def export_template_command(config: Config, args) -> int:
    """
    Export a template to an external file.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name
    output = getattr(args, 'output', None)

    # Generate default output filename if not provided
    if not output:
        output = f"prompt_{template_name}.json"

    output_path = Path(output)

    console.print(f"[yellow]Exporting template '{template_name}'...[/yellow]")

    if manager.export_template(template_name, output_path):
        console.print(f"[green]✓ Template exported to: {output_path}[/green]")
        return 0
    else:
        console.print(f"[red]Failed to export template '{template_name}'[/red]")
        return 1


def enable_template_command(config: Config, args) -> int:
    """
    Enable a template.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name

    if manager.enable_template(template_name):
        console.print(f"[green]✓ Template '{template_name}' enabled[/green]")
        return 0
    else:
        console.print(f"[red]Template '{template_name}' not found[/red]")
        return 1


def disable_template_command(config: Config, args) -> int:
    """
    Disable a template.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name

    if manager.disable_template(template_name):
        console.print(f"[green]✓ Template '{template_name}' disabled[/green]")
        return 0
    else:
        console.print(f"[red]Template '{template_name}' not found[/red]")
        return 1


def backup_templates_command(config: Config, args) -> int:
    """
    Create a backup of all templates.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)

    console.print("[yellow]Creating backup of all templates...[/yellow]")

    backup_path = manager.backup_templates()
    if backup_path:
        return 0
    else:
        return 1


def delete_template_command(config: Config, args) -> int:
    """
    Delete a template.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    template_name = args.template_name

    template = manager.get_template(template_name)
    if not template:
        console.print(f"[red]Template '{template_name}' not found[/red]")
        return 1

    # Confirm deletion
    console.print(f"[yellow]⚠ This will move template '{template['display_name']}' to trash (30-day recovery)[/yellow]")

    if not Confirm.ask("Are you sure?", default=False):
        console.print("[dim]Cancelled[/dim]")
        return 0

    success, trash_id = manager.delete_template(template_name)
    if success:
        if trash_id:
            console.print(f"[green]✓ Template '{template_name}' moved to trash[/green]")
            console.print()
            console.print(f"[bold]Trash ID:[/bold] {trash_id}")
            console.print()
            console.print("[bold]Recovery Options:[/bold]")
            console.print(f"  - View trash: [cyan]llf trash list[/cyan]")
            console.print(f"  - Restore: [cyan]llf trash restore {trash_id}[/cyan]")
            console.print()
            console.print("[dim]Items in trash are automatically deleted after 30 days[/dim]")
        else:
            console.print(f"[green]✓ Template '{template_name}' removed from registry[/green]")
        return 0
    else:
        return 1


def create_template_command(config: Config, args) -> int:
    """
    Interactively create a new template.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)

    console.print(Panel("[bold cyan]Create New Prompt Template[/bold cyan]\n\nThis wizard will guide you through creating a custom prompt template.", expand=False))

    # Gather template metadata
    name = Prompt.ask("\n[cyan]Template name[/cyan] (lowercase, underscores)", default="my_template")
    display_name = Prompt.ask("[cyan]Display name[/cyan]", default=name.replace('_', ' ').title())
    description = Prompt.ask("[cyan]Description[/cyan]", default=f"Custom template: {display_name}")

    # Category
    console.print("\n[cyan]Category:[/cyan]")
    console.print("  Predefined: " + ", ".join(PromptManager.PREDEFINED_CATEGORIES))
    category = Prompt.ask("Category", default="general")

    # Tags
    tags_input = Prompt.ask("[cyan]Tags[/cyan] (comma-separated)", default="custom")
    tags = [t.strip() for t in tags_input.split(',')]

    # Prompt configuration
    console.print("\n[bold yellow]Prompt Configuration:[/bold yellow]")
    console.print("[dim]You can use variables with format: {{variable::default_value}}[/dim]\n")

    console.print("[cyan]System Prompt[/cyan] [dim](Sets the AI's role and behavior)[/dim]")
    console.print("[dim]Example: You are a helpful assistant specialized in {{topic::general topics}}.[/dim]")
    system_prompt = Prompt.ask("System prompt", default=None)

    console.print("\n[cyan]Master Prompt[/cyan] [dim](Additional instructions)[/dim]")
    console.print("[dim]Example: Always provide {{detail_level::detailed}} explanations.[/dim]")
    master_prompt = Prompt.ask("Master prompt", default=None)

    console.print("\n[cyan]Assistant Prompt[/cyan] [dim](Response formatting)[/dim]")
    assistant_prompt = Prompt.ask("Assistant prompt", default=None)

    # Conversation format
    conversation_format = Prompt.ask("\n[cyan]Conversation format[/cyan]", default="standard")

    # Create template configuration
    template_config = {
        "system_prompt": system_prompt,
        "master_prompt": master_prompt,
        "assistant_prompt": assistant_prompt,
        "conversation_format": conversation_format,
        "prefix_messages": [],
        "suffix_messages": []
    }

    # Check if template already exists
    if manager.get_template(name):
        console.print(f"\n[red]✗ Template '{name}' already exists[/red]")
        return 1

    # Create template directory
    template_dir = manager.templates_dir / name
    template_dir.mkdir(parents=True, exist_ok=True)

    # Save template file
    template_file = template_dir / "prompt.json"
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"\n[red]Error saving template: {e}[/red]")
        return 1

    # Add to registry
    from datetime import datetime
    template_meta = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "category": category,
        "author": "user",
        "version": "1.0",
        "tags": tags,
        "enabled": True,
        "directory": name,
        "created_date": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat()
    }

    manager.registry["templates"].append(template_meta)
    manager._save_registry()

    console.print(f"\n[green]✓ Template '{name}' created successfully![/green]")
    console.print(f"[dim]Template directory: {template_dir}[/dim]")
    console.print(f"[dim]Use 'llf prompt load {name}' to activate it[/dim]")

    return 0


def show_active_template_command(config: Config, args) -> int:
    """
    Show the currently active template and its configuration.

    Args:
        config: Configuration instance.
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    manager = get_prompt_manager(config)
    active_name = manager.get_active_template()

    if not active_name:
        console.print("[yellow]No template is currently active[/yellow]")
        console.print("[dim]Load a template with: llf prompt load TEMPLATE_NAME[/dim]")
        return 0

    # Show active template info
    template = manager.get_template(active_name)
    if template:
        console.print(f"[bold cyan]Active Template: {template['display_name']}[/bold cyan]")
        console.print(f"[dim]Name: {template['name']}[/dim]")
        console.print(f"[dim]Category: {template['category']}[/dim]")
        console.print(f"[dim]Description: {template['description']}[/dim]")

    # Show current config
    console.print(f"\n[yellow]Current Configuration:[/yellow]")
    try:
        with open(manager.active_prompt_file, 'r') as f:
            current_config = json.load(f)

        for key, value in current_config.items():
            if value and key not in ['prefix_messages', 'suffix_messages']:
                preview = str(value)[:80]
                if len(str(value)) > 80:
                    preview += "..."
                console.print(f"  [cyan]{key}:[/cyan] {preview}")
    except Exception as e:
        console.print(f"[red]Error reading config: {e}[/red]")

    return 0

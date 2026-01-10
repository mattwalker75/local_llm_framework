"""
Development commands for tool creation and validation.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

from llf.tool_scaffolder import ToolScaffolder
from llf.logging_config import get_logger

console = Console()
logger = get_logger(__name__)


class DevCommands:
    """Handles development commands for tool creation and validation."""

    def __init__(self, tools_dir: Path):
        """
        Initialize dev commands handler.

        Args:
            tools_dir: Path to the tools directory
        """
        self.tools_dir = Path(tools_dir)
        self.scaffolder = ToolScaffolder(tools_dir)

    def create_tool_interactive(self) -> int:
        """
        Run interactive wizard to create a new tool.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        console.print("\n[bold cyan]Create New Tool - Interactive Wizard[/bold cyan]\n")

        # Step 1: Tool Type Selection
        console.print("[bold]Step 1: Select Tool Type[/bold]\n")

        table = Table(show_header=True)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")

        for idx, (type_key, type_info) in enumerate(ToolScaffolder.TOOL_TYPES.items(), 1):
            table.add_row(
                str(idx),
                type_info['display'],
                type_info['description']
            )

        console.print(table)

        type_choice = Prompt.ask("\nSelect tool type", choices=["1", "2", "3"], default="1")
        tool_types_list = list(ToolScaffolder.TOOL_TYPES.keys())
        tool_type = tool_types_list[int(type_choice) - 1]

        console.print(f"[green]✓[/green] Selected: {ToolScaffolder.TOOL_TYPES[tool_type]['display']}\n")

        # Step 2: Basic Information
        console.print("[bold]Step 2: Basic Information[/bold]\n")

        # Tool name
        while True:
            tool_name = Prompt.ask("Tool name (lowercase, underscores only)")
            if not self._validate_tool_name(tool_name):
                console.print("[red]Invalid tool name. Use lowercase letters, numbers, and underscores only.[/red]")
                continue

            # Check if tool directory already exists
            if (self.tools_dir / tool_name).exists():
                console.print(f"[red]Tool directory '{tool_name}' already exists.[/red]")
                continue

            break

        # Display name
        display_name = Prompt.ask("Display name", default=tool_name.replace('_', ' ').title())

        # Description
        console.print("\n[dim]Description (for LLM understanding - be specific and clear):[/dim]")
        description = Prompt.ask("Description")

        # Category
        console.print("\n[dim]Examples: internet, file_access, command_execution, data_processing, formatting[/dim]")
        category = Prompt.ask("Category", default="general")

        # Step 3: Parameters (only for llm_invokable)
        parameters = []
        if tool_type == 'llm_invokable':
            console.print("\n[bold]Step 3: Parameters[/bold]")
            console.print("[dim]Define parameters that the LLM can provide when calling this tool.[/dim]\n")

            # Display supported parameter types with OpenAI info
            console.print("[yellow]Supported Parameter Types:[/yellow]")
            console.print("  string  - Text values")
            console.print("  integer - Whole numbers (supports min/max constraints)")
            console.print("  number  - Decimal numbers (supports min/max constraints)")
            console.print("  boolean - true/false values")
            console.print("  array   - List of values")
            console.print("  object  - Nested structure")
            console.print("\n[dim]Note: OpenAI's function calling supports all these types.")
            console.print("Example with constraints:[/dim]")
            console.print('  {"type": "integer", "minimum": 1, "maximum": 100}')
            console.print('  {"type": "string", "enum": ["option1", "option2"]}\n')

            add_params = Confirm.ask("Add parameters?", default=True)

            while add_params:
                console.print(f"\n[cyan]Parameter {len(parameters) + 1}:[/cyan]")

                param_name = Prompt.ask("  Parameter name")
                param_type = Prompt.ask(
                    "  Type",
                    choices=["string", "integer", "number", "boolean", "array", "object"],
                    default="string"
                )
                param_desc = Prompt.ask("  Description")
                param_required = Confirm.ask("  Required?", default=True)

                param = {
                    "name": param_name,
                    "type": param_type,
                    "description": param_desc,
                    "required": param_required
                }

                # Ask for constraints if integer or number
                if param_type in ['integer', 'number']:
                    add_constraints = Confirm.ask("  Add min/max constraints?", default=False)
                    if add_constraints:
                        minimum = Prompt.ask("    Minimum value (press Enter to skip)", default="")
                        if minimum:
                            param['minimum'] = int(minimum) if param_type == 'integer' else float(minimum)

                        maximum = Prompt.ask("    Maximum value (press Enter to skip)", default="")
                        if maximum:
                            param['maximum'] = int(maximum) if param_type == 'integer' else float(maximum)

                parameters.append(param)

                add_params = Confirm.ask("\nAdd another parameter?", default=False)

            console.print(f"\n[green]✓[/green] Defined {len(parameters)} parameter(s)\n")
        else:
            console.print("\n[dim]Skipping parameters (not applicable for this tool type)[/dim]\n")

        # Step 4: Code Template Selection
        console.print("[bold]Step 4: Select Code Template[/bold]\n")

        table = Table(show_header=True)
        table.add_column("Option", style="cyan", width=4)
        table.add_column("Template", style="green")
        table.add_column("Description", style="white")

        for idx, (template_key, template_info) in enumerate(ToolScaffolder.CODE_TEMPLATES.items(), 1):
            table.add_row(
                str(idx),
                template_info['display'],
                template_info['description']
            )

        console.print(table)

        template_choice = Prompt.ask(
            "\nSelect code template",
            choices=["1", "2", "3", "4", "5", "6"],
            default="6"
        )
        templates_list = list(ToolScaffolder.CODE_TEMPLATES.keys())
        template_type = templates_list[int(template_choice) - 1]

        console.print(f"[green]✓[/green] Selected: {ToolScaffolder.CODE_TEMPLATES[template_type]['display']}\n")

        # Step 5: Summary and Confirmation
        console.print("[bold]Step 5: Review and Confirm[/bold]\n")

        summary = f"""[cyan]Tool Name:[/cyan] {tool_name}
[cyan]Display Name:[/cyan] {display_name}
[cyan]Description:[/cyan] {description}
[cyan]Type:[/cyan] {tool_type}
[cyan]Category:[/cyan] {category}
[cyan]Template:[/cyan] {template_type}
[cyan]Parameters:[/cyan] {len(parameters) if parameters else 0}
[cyan]Default State:[/cyan] Disabled (enabled: false)
"""

        console.print(Panel(summary, title="Tool Configuration", border_style="green"))

        if not Confirm.ask("\nCreate this tool?", default=True):
            console.print("[yellow]Tool creation cancelled.[/yellow]")
            return 1

        # Create the tool
        console.print("\n[yellow]Creating tool files...[/yellow]")

        success, message = self.scaffolder.create_tool(
            tool_name=tool_name,
            display_name=display_name,
            description=description,
            tool_type=tool_type,
            category=category,
            template_type=template_type,
            parameters=parameters
        )

        if success:
            console.print(f"\n[green]✓[/green] {message}\n")

            # Show next steps
            console.print("[bold cyan]Next Steps:[/bold cyan]\n")
            console.print(f"1. Review generated files in: [cyan]{self.tools_dir / tool_name}[/cyan]")
            console.print(f"2. Implement the execute() function in [cyan]__init__.py[/cyan]")
            console.print(f"3. Update [cyan]README.md[/cyan] with actual usage examples")
            console.print(f"4. Write tests in [cyan]tests/test_{tool_name}.py[/cyan]")
            console.print(f"5. Run tests: [cyan]pytest tests/test_{tool_name}.py[/cyan]")
            console.print(f"6. When ready, import to registry: [cyan]llf tool import {tool_name}[/cyan]")
            console.print(f"7. Enable the tool: [cyan]llf tool enable {tool_name}[/cyan]\n")

            return 0
        else:
            console.print(f"\n[red]✗[/red] {message}\n")
            return 1

    def validate_tool(self, tool_name: str) -> int:
        """
        Validate a tool's structure and configuration.

        Args:
            tool_name: Name of the tool to validate

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        console.print(f"\n[bold cyan]Validating Tool: {tool_name}[/bold cyan]\n")

        tool_dir = self.tools_dir / tool_name
        issues = []
        warnings = []

        # Check 1: Directory exists
        if not tool_dir.exists() or not tool_dir.is_dir():
            console.print(f"[red]✗ Tool directory not found: {tool_dir}[/red]")
            return 1

        console.print(f"[green]✓[/green] Tool directory exists: {tool_dir}")

        # Check 2: Required files exist
        required_files = {
            '__init__.py': 'Main implementation file',
            'execute.py': 'Execute wrapper file',
            'tool_definition.json': 'OpenAI function schema',
            'config.json': 'Tool configuration',
            'README.md': 'Documentation'
        }

        for filename, description in required_files.items():
            filepath = tool_dir / filename
            if not filepath.exists():
                issues.append(f"Missing file: {filename} ({description})")
            else:
                console.print(f"[green]✓[/green] {filename} exists")

        # Check 3: config.json validation
        config_file = tool_dir / 'config.json'
        if config_file.exists():
            try:
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)

                # Validate required fields
                required_fields = [
                    'name', 'display_name', 'description', 'type',
                    'enabled', 'directory', 'created_date', 'last_modified'
                ]

                for field in required_fields:
                    if field not in config:
                        issues.append(f"config.json missing required field: {field}")

                # Validate metadata
                if 'metadata' not in config:
                    issues.append("config.json missing 'metadata' section")
                else:
                    required_metadata = ['category', 'requires_approval', 'dependencies']
                    for field in required_metadata:
                        if field not in config['metadata']:
                            issues.append(f"config.json missing metadata.{field}")

                # Verify name matches directory
                if config.get('name') != tool_name:
                    issues.append(f"Name mismatch: directory='{tool_name}', config.name='{config.get('name')}'")

                if not issues:
                    console.print("[green]✓[/green] config.json has all required fields")

            except json.JSONDecodeError as e:
                issues.append(f"config.json is not valid JSON: {e}")

        # Check 4: tool_definition.json validation
        tool_def_file = tool_dir / 'tool_definition.json'
        if tool_def_file.exists():
            try:
                import json
                with open(tool_def_file, 'r') as f:
                    tool_def = json.load(f)

                # Check OpenAI function schema structure
                if 'type' not in tool_def or tool_def['type'] != 'function':
                    warnings.append("tool_definition.json should have type='function' for OpenAI schema")

                if 'function' not in tool_def:
                    warnings.append("tool_definition.json missing 'function' field")
                else:
                    if 'name' not in tool_def['function']:
                        warnings.append("tool_definition.json missing function.name")
                    if 'description' not in tool_def['function']:
                        warnings.append("tool_definition.json missing function.description")

                if not warnings:
                    console.print("[green]✓[/green] tool_definition.json has valid OpenAI schema structure")

            except json.JSONDecodeError as e:
                issues.append(f"tool_definition.json is not valid JSON: {e}")

        # Check 5: __init__.py validation
        init_file = tool_dir / '__init__.py'
        if init_file.exists():
            try:
                with open(init_file, 'r') as f:
                    content = f.read()

                # Check for execute function
                if 'def execute(' not in content:
                    issues.append("__init__.py missing execute() function")
                else:
                    console.print("[green]✓[/green] __init__.py has execute() function")

                # Check for __all__ export
                if '__all__' not in content:
                    warnings.append("__init__.py missing __all__ export list")
                else:
                    console.print("[green]✓[/green] __init__.py has __all__ exports")

            except Exception as e:
                issues.append(f"Failed to read __init__.py: {e}")

        # Check 6: execute.py validation
        execute_file = tool_dir / 'execute.py'
        if execute_file.exists():
            try:
                with open(execute_file, 'r') as f:
                    content = f.read()

                # Check for re-export
                if 'from . import execute' not in content and 'from .import execute' not in content:
                    warnings.append("execute.py should re-export execute function from __init__")
                else:
                    console.print("[green]✓[/green] execute.py re-exports execute function")

            except Exception as e:
                warnings.append(f"Failed to read execute.py: {e}")

        # Check 7: Test file exists
        test_file = self.tools_dir.parent / 'tests' / f'test_{tool_name}.py'
        if not test_file.exists():
            warnings.append(f"Test file not found: {test_file}")
        else:
            console.print(f"[green]✓[/green] Test file exists: {test_file}")

        # Summary
        console.print("\n[bold]Validation Summary:[/bold]\n")

        if issues:
            console.print(f"[red]✗ {len(issues)} issue(s) found:[/red]\n")
            for issue in issues:
                console.print(f"  [red]✗[/red] {issue}")
            console.print()

        if warnings:
            console.print(f"[yellow]⚠ {len(warnings)} warning(s):[/yellow]\n")
            for warning in warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
            console.print()

        if not issues and not warnings:
            console.print("[green]✓ Tool validation passed! No issues found.[/green]\n")
            console.print("[dim]The tool is ready to be imported with: llf tool import " + tool_name + "[/dim]\n")
            return 0
        elif issues:
            console.print("[red]Validation failed. Please fix the issues above.[/red]\n")
            return 1
        else:
            console.print("[yellow]Validation passed with warnings. Tool can be imported but consider addressing warnings.[/yellow]\n")
            return 0

    def _validate_tool_name(self, name: str) -> bool:
        """
        Validate tool name format.

        Args:
            name: Tool name to validate

        Returns:
            True if valid, False otherwise
        """
        # Must be lowercase, numbers, and underscores only
        pattern = r'^[a-z0-9_]+$'
        return bool(re.match(pattern, name))

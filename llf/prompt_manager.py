"""
Prompt template management for the Local LLM Framework.

This module provides functionality for creating, managing, and applying
prompt templates with variable substitution.

Features:
- Template library with metadata
- Variable substitution with defaults
- Import/export templates
- Template versioning and backup
- Category-based organization
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from llf.trash_manager import TrashManager

console = Console()


class PromptManager:
    """Manages prompt templates and their metadata."""

    # Predefined categories (custom categories also allowed)
    PREDEFINED_CATEGORIES = [
        "development",
        "writing",
        "analysis",
        "education",
        "general"
    ]

    def __init__(self, templates_dir: Path, registry_file: Path, active_prompt_file: Path):
        """
        Initialize PromptManager.

        Args:
            templates_dir: Directory containing prompt templates.
            registry_file: Path to the templates registry JSON file.
            active_prompt_file: Path to the active prompt config file.
        """
        self.templates_dir = Path(templates_dir)
        self.registry_file = Path(registry_file)
        self.active_prompt_file = Path(active_prompt_file)
        self.backup_dir = self.templates_dir / "backups"

        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load or create registry
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load the template registry from disk."""
        if not self.registry_file.exists():
            # Create default registry
            registry = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "active_template": None,
                "templates": []
            }
            self._save_registry(registry)
            return registry

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading registry: {e}[/red]")
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "active_template": None,
                "templates": []
            }

    def _save_registry(self, registry: Optional[Dict[str, Any]] = None) -> None:
        """Save the template registry to disk."""
        if registry is None:
            registry = self.registry

        registry["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[red]Error saving registry: {e}[/red]")

    def list_templates(self, category: Optional[str] = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all templates.

        Args:
            category: Filter by category.
            enabled_only: Only show enabled templates.

        Returns:
            List of template metadata dictionaries.
        """
        templates = self.registry.get("templates", [])

        if category:
            templates = [t for t in templates if t.get("category") == category]

        if enabled_only:
            templates = [t for t in templates if t.get("enabled", True)]

        return templates

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get template metadata by name.

        Args:
            name: Template name.

        Returns:
            Template metadata or None if not found.
        """
        templates = self.registry.get("templates", [])
        for template in templates:
            if template["name"] == name:
                return template
        return None

    def get_active_template(self) -> Optional[str]:
        """Get the name of the currently active template."""
        return self.registry.get("active_template")

    def load_template_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load template configuration from disk.

        Args:
            name: Template name.

        Returns:
            Template configuration or None if not found.
        """
        template_meta = self.get_template(name)
        if not template_meta:
            return None

        template_dir = self.templates_dir / template_meta["directory"]
        template_file = template_dir / "prompt.json"

        if not template_file.exists():
            console.print(f"[red]Template file not found: {template_file}[/red]")
            return None

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading template: {e}[/red]")
            return None

    def substitute_variables(self, text: Optional[str], variables: Dict[str, str]) -> Optional[str]:
        """
        Substitute variables in text with format {{variable::default}}.

        Args:
            text: Text containing variables.
            variables: Dictionary of variable values.

        Returns:
            Text with substituted variables.
        """
        if text is None:
            return None

        # Pattern: {{variable::default}} or {{variable}}
        pattern = r'\{\{(\w+)(?:::([^}]+))?\}\}'

        def replace(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""

            # Use provided value, or default, or empty string
            return variables.get(var_name, default_value)

        return re.sub(pattern, replace, text)

    def apply_template(self, name: str, variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Apply a template to the active prompt configuration.

        Args:
            name: Template name.
            variables: Optional variable substitutions.

        Returns:
            True if successful, False otherwise.
        """
        if variables is None:
            variables = {}

        # Load template
        template_config = self.load_template_config(name)
        if not template_config:
            console.print(f"[red]Failed to load template: {name}[/red]")
            return False

        # Substitute variables in all text fields
        prompt_config = {}
        for key, value in template_config.items():
            if key == "variables":
                # Skip variables metadata
                continue
            elif isinstance(value, str):
                prompt_config[key] = self.substitute_variables(value, variables)
            elif isinstance(value, list):
                # Handle prefix_messages and suffix_messages
                prompt_config[key] = []
                for item in value:
                    if isinstance(item, dict) and 'content' in item:
                        new_item = item.copy()
                        new_item['content'] = self.substitute_variables(item['content'], variables)
                        prompt_config[key].append(new_item)
                    else:
                        prompt_config[key].append(item)
            else:
                prompt_config[key] = value

        # Save to active prompt file
        try:
            with open(self.active_prompt_file, 'w', encoding='utf-8') as f:
                json.dump(prompt_config, f, indent=2, ensure_ascii=False)

            # Update active template in registry
            self.registry["active_template"] = name
            self._save_registry()

            return True
        except Exception as e:
            console.print(f"[red]Error saving prompt configuration: {e}[/red]")
            return False

    def import_template(self, source_path: Path, name: str, display_name: str,
                       description: str, category: str = "general",
                       author: str = "user", tags: Optional[List[str]] = None) -> bool:
        """
        Import a template from an external file.

        Args:
            source_path: Path to source prompt.json file.
            name: Template name (directory name).
            display_name: Human-readable display name.
            description: Template description.
            category: Template category.
            author: Template author.
            tags: Optional list of tags.

        Returns:
            True if successful, False otherwise.
        """
        # Validate source file
        if not source_path.exists():
            console.print(f"[red]Source file not found: {source_path}[/red]")
            return False

        # Check if template already exists
        if self.get_template(name):
            console.print(f"[red]Template '{name}' already exists[/red]")
            return False

        # Create template directory
        template_dir = self.templates_dir / name
        template_dir.mkdir(parents=True, exist_ok=True)

        # Copy template file
        dest_file = template_dir / "prompt.json"
        try:
            shutil.copy2(source_path, dest_file)
        except Exception as e:
            console.print(f"[red]Error copying template: {e}[/red]")
            return False

        # Add to registry
        template_meta = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "category": category,
            "author": author,
            "version": "1.0",
            "tags": tags or [],
            "enabled": True,
            "directory": name,
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }

        self.registry["templates"].append(template_meta)
        self._save_registry()

        return True

    def export_template(self, name: str, output_path: Path) -> bool:
        """
        Export a template to an external file.

        Args:
            name: Template name.
            output_path: Destination file path.

        Returns:
            True if successful, False otherwise.
        """
        template_config = self.load_template_config(name)
        if not template_config:
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            console.print(f"[red]Error exporting template: {e}[/red]")
            return False

    def enable_template(self, name: str) -> bool:
        """Enable a template."""
        template = self.get_template(name)
        if not template:
            return False

        template["enabled"] = True
        self._save_registry()
        return True

    def disable_template(self, name: str) -> bool:
        """Disable a template."""
        template = self.get_template(name)
        if not template:
            return False

        template["enabled"] = False
        self._save_registry()
        return True

    def backup_templates(self) -> Optional[Path]:
        """
        Create a backup of all templates and registry.

        Returns:
            Path to backup directory or None if failed.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"

        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy registry
            shutil.copy2(self.registry_file, backup_path / "prompt_templates_registry.json")

            # Copy all template directories
            for template in self.registry.get("templates", []):
                template_dir = self.templates_dir / template["directory"]
                if template_dir.exists():
                    dest_dir = backup_path / template["directory"]
                    shutil.copytree(template_dir, dest_dir)

            console.print(f"[green]✓ Backup created: {backup_path}[/green]")
            return backup_path
        except Exception as e:
            console.print(f"[red]Error creating backup: {e}[/red]")
            return None

    def delete_template(self, name: str) -> tuple[bool, Optional[str]]:
        """
        Delete a template (move to trash with 30-day recovery).

        Args:
            name: Template name.

        Returns:
            Tuple of (success, trash_id_or_error_message).
        """
        template = self.get_template(name)
        if not template:
            console.print(f"[red]Template '{name}' not found[/red]")
            return (False, None)

        # Get template directory
        template_dir = self.templates_dir / template["directory"]

        if not template_dir.exists():
            console.print(f"[yellow]Warning:[/yellow] Template directory not found: {template_dir}")
            console.print(f"[yellow]Removing from registry only[/yellow]")

            # Remove from registry
            self.registry["templates"] = [
                t for t in self.registry["templates"]
                if t["name"] != name
            ]

            # Clear active template if this was active
            if self.registry.get("active_template") == name:
                self.registry["active_template"] = None

            self._save_registry()
            return (True, None)

        # Initialize trash manager
        project_root = self.templates_dir.parent
        trash_dir = project_root / 'trash'
        trash_manager = TrashManager(trash_dir)

        # Move to trash
        success, trash_id = trash_manager.move_to_trash(
            item_type='template',
            item_name=name,
            paths=[template_dir],
            original_metadata=template
        )

        if not success:
            console.print(f"[red]Error:[/red] Failed to move template to trash: {trash_id}")
            return (False, trash_id)

        # Remove from registry
        self.registry["templates"] = [
            t for t in self.registry["templates"]
            if t["name"] != name
        ]

        # Clear active template if this was active
        if self.registry.get("active_template") == name:
            self.registry["active_template"] = None

        self._save_registry()
        return (True, trash_id)

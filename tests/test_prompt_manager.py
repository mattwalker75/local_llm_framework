"""
Tests for prompt template management.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, UTC

from llf.prompt_manager import PromptManager


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


@pytest.fixture
def templates_dir(temp_dir):
    """Create templates directory."""
    templates = temp_dir / "prompt_templates"
    templates.mkdir(parents=True)
    return templates


@pytest.fixture
def registry_file(templates_dir):
    """Create registry file path."""
    return templates_dir / "prompt_templates_registry.json"


@pytest.fixture
def active_prompt_file(temp_dir):
    """Create active prompt file path."""
    return temp_dir / "config_prompt.json"


@pytest.fixture
def prompt_manager(templates_dir, registry_file, active_prompt_file):
    """Create PromptManager instance."""
    return PromptManager(templates_dir, registry_file, active_prompt_file)


@pytest.fixture
def sample_template(templates_dir):
    """Create a sample template."""
    template_dir = templates_dir / "test_template"
    template_dir.mkdir()

    template_config = {
        "system_prompt": "You are a helpful assistant specialized in {{topic::general topics}}",
        "master_prompt": "Focus on {{focus_areas::best practices}}",
        "assistant_prompt": None,
        "conversation_format": "standard",
        "prefix_messages": [],
        "suffix_messages": []
    }

    with open(template_dir / "prompt.json", 'w') as f:
        json.dump(template_config, f, indent=2)

    return "test_template"


class TestPromptManager:
    """Test PromptManager class."""

    def _add_template_to_registry(self, prompt_manager, metadata):
        """Helper method to add a template to registry."""
        prompt_manager.registry['templates'].append(metadata)
        prompt_manager._save_registry()

    def test_initialization_creates_registry(self, prompt_manager, registry_file):
        """Test that initialization creates an empty registry if it doesn't exist."""
        assert registry_file.exists()

        with open(registry_file, 'r') as f:
            registry = json.load(f)

        assert "version" in registry
        assert "templates" in registry
        assert registry["active_template"] is None
        assert isinstance(registry["templates"], list)

    def test_list_templates_empty(self, prompt_manager):
        """Test listing templates when none exist."""
        templates = prompt_manager.list_templates()
        assert len(templates) == 0

    def test_add_template(self, prompt_manager, templates_dir):
        """Test adding a new template."""
        # Create template directory and file
        template_dir = templates_dir / "new_template"
        template_dir.mkdir()

        template_config = {
            "system_prompt": "Test system prompt",
            "master_prompt": None,
            "assistant_prompt": None,
            "conversation_format": "standard",
            "prefix_messages": [],
            "suffix_messages": []
        }

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f, indent=2)

        # Add to registry
        metadata = {
            "name": "new_template",
            "display_name": "New Template",
            "description": "Test template",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": ["test"],
            "enabled": True,
            "directory": "new_template"
        }

        self._add_template_to_registry(prompt_manager, metadata)

        # Verify template is in registry
        templates = prompt_manager.list_templates()
        assert len(templates) == 1
        assert templates[0]["name"] == "new_template"

    def test_get_template(self, prompt_manager, sample_template):
        """Test getting a specific template."""
        # First add the template to registry
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "enabled": True,
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        template = prompt_manager.get_template(sample_template)
        assert template is not None
        assert template["name"] == sample_template

    def test_get_nonexistent_template(self, prompt_manager):
        """Test getting a template that doesn't exist."""
        template = prompt_manager.get_template("nonexistent")
        assert template is None

    def test_variable_substitution_basic(self, prompt_manager):
        """Test basic variable substitution."""
        text = "Hello {{name}}, welcome to {{place::our platform}}"
        variables = {"name": "Alice"}

        result = prompt_manager.substitute_variables(text, variables)
        assert result == "Hello Alice, welcome to our platform"

    def test_variable_substitution_with_defaults(self, prompt_manager):
        """Test variable substitution using default values."""
        text = "Focus on {{topic::best practices}} and {{quality::high quality}}"
        variables = {}

        result = prompt_manager.substitute_variables(text, variables)
        assert result == "Focus on best practices and high quality"

    def test_variable_substitution_override_defaults(self, prompt_manager):
        """Test variable substitution overriding default values."""
        text = "Focus on {{topic::best practices}}"
        variables = {"topic": "Python programming"}

        result = prompt_manager.substitute_variables(text, variables)
        assert result == "Focus on Python programming"

    def test_variable_substitution_none_text(self, prompt_manager):
        """Test variable substitution with None text."""
        result = prompt_manager.substitute_variables(None, {})
        assert result is None

    def test_enable_template(self, prompt_manager, sample_template, active_prompt_file):
        """Test enabling a template (applying it)."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Enable it (which applies it)
        result = prompt_manager.apply_template(sample_template)
        assert result is True

        # Verify it's set as active
        assert prompt_manager.get_active_template() == sample_template

        # Verify config file was created
        assert active_prompt_file.exists()

    def test_disable_template(self, prompt_manager, sample_template, active_prompt_file):
        """Test disabling the active template."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Enable it first
        prompt_manager.apply_template(sample_template)
        assert prompt_manager.get_active_template() == sample_template

        # Disable it
        result = prompt_manager.disable_template()
        assert result is True

        # Verify no template is active
        assert prompt_manager.get_active_template() is None

        # Verify config was reset to blank
        with open(active_prompt_file, 'r') as f:
            config = json.load(f)
        assert config["system_prompt"] is None
        assert config["master_prompt"] is None

    def test_apply_template(self, prompt_manager, sample_template, active_prompt_file):
        """Test applying a template to active config."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Apply template
        variables = {"topic": "Python", "focus_areas": "testing"}
        result = prompt_manager.apply_template(sample_template, variables)
        assert result is True

        # Verify active prompt file was created
        assert active_prompt_file.exists()

        with open(active_prompt_file, 'r') as f:
            config = json.load(f)

        assert "You are a helpful assistant specialized in Python" in config["system_prompt"]
        assert "Focus on testing" in config["master_prompt"]

        # Verify active template is tracked
        template = prompt_manager.get_template(sample_template)
        assert prompt_manager.registry.get("active_template") == sample_template

    def test_apply_template_with_default_variables(self, prompt_manager, sample_template, active_prompt_file):
        """Test applying a template using default variable values."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Apply template without variables
        result = prompt_manager.apply_template(sample_template)
        assert result is True

        # Verify defaults were used
        with open(active_prompt_file, 'r') as f:
            config = json.load(f)

        assert "general topics" in config["system_prompt"]
        assert "best practices" in config["master_prompt"]

    def test_delete_template(self, prompt_manager, sample_template):
        """Test deleting a template."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "enabled": True,
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Delete it (now returns tuple)
        success, trash_id = prompt_manager.delete_template(sample_template)
        assert success is True
        assert trash_id is not None  # Should have trash ID

        # Verify it's gone from registry
        template = prompt_manager.get_template(sample_template)
        assert template is None

    def test_export_template(self, prompt_manager, sample_template, temp_dir):
        """Test exporting a template."""
        # Add template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "enabled": True,
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Export it
        output_path = temp_dir / "exported_template.json"
        result = prompt_manager.export_template(sample_template, output_path)
        assert result is True
        assert output_path.exists()

        # Verify exported content
        with open(output_path, 'r') as f:
            exported = json.load(f)

        assert exported["system_prompt"] == "You are a helpful assistant specialized in {{topic::general topics}}"

    def test_import_template(self, prompt_manager, temp_dir):
        """Test importing a template."""
        # Create a template file to import
        import_file = temp_dir / "import_template.json"
        template_config = {
            "system_prompt": "Imported system prompt",
            "master_prompt": None,
            "assistant_prompt": None,
            "conversation_format": "standard",
            "prefix_messages": [],
            "suffix_messages": []
        }

        with open(import_file, 'w') as f:
            json.dump(template_config, f)

        # Import it
        result = prompt_manager.import_template(
            source_path=import_file,
            name="imported_template",
            display_name="Imported Template",
            description="Test import",
            category="general",
            author="test",
            tags=["imported", "test"]
        )
        assert result is True

        # Verify it was imported
        template = prompt_manager.get_template("imported_template")
        assert template is not None
        assert template["name"] == "imported_template"

    def test_backup_templates(self, prompt_manager, sample_template):
        """Test creating a backup."""
        # Add a template
        metadata = {
            "name": sample_template,
            "display_name": "Test Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "enabled": True,
            "directory": sample_template
        }
        self._add_template_to_registry(prompt_manager, metadata)

        # Create backup
        backup_path = prompt_manager.backup_templates()
        assert backup_path is not None
        assert backup_path.exists()
        assert (backup_path / sample_template / "prompt.json").exists()

    def test_list_templates_with_filters(self, prompt_manager, sample_template):
        """Test listing templates with category filter."""
        # Add multiple templates
        for i, (name, category) in enumerate([
            ("template1", "development"),
            ("template2", "writing"),
            ("template3", "development"),
            ("template4", "writing"),
        ]):
            # Create template directory
            template_dir = prompt_manager.templates_dir / name
            template_dir.mkdir()

            with open(template_dir / "prompt.json", 'w') as f:
                json.dump({
                    "system_prompt": f"Template {i+1}",
                    "master_prompt": None,
                    "assistant_prompt": None,
                    "conversation_format": "standard",
                    "prefix_messages": [],
                    "suffix_messages": []
                }, f)

            metadata = {
                "name": name,
                "display_name": f"Template {i+1}",
                "description": "Test",
                "category": category,
                "author": "test",
                "version": "1.0",
                "tags": [],
                "directory": name
            }
            self._add_template_to_registry(prompt_manager, metadata)

        # Test category filter for development
        dev_templates = prompt_manager.list_templates(category="development")
        assert len(dev_templates) == 2

        # Test category filter for writing
        writing_templates = prompt_manager.list_templates(category="writing")
        assert len(writing_templates) == 2

        # Test listing all templates
        all_templates = prompt_manager.list_templates()
        assert len(all_templates) == 4

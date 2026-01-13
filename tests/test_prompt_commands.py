"""
Tests for prompt template CLI commands.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from llf.prompt_commands import (
    get_prompt_manager,
    list_templates_command,
    info_template_command,
    disable_template_command,
    create_template_command,
    backup_templates_command,
    enable_template_command,
    import_template_command,
    export_template_command,
    delete_template_command,
    show_enabled_command
)
from llf.config import Config
from llf.prompt_manager import PromptManager


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config_dir(temp_dir):
    """Create config directory."""
    cfg_dir = temp_dir / "configs"
    cfg_dir.mkdir(parents=True)
    return cfg_dir


@pytest.fixture
def templates_dir(config_dir):
    """Create templates directory."""
    templates = config_dir / "prompt_templates"
    templates.mkdir(parents=True)
    return templates


@pytest.fixture
def registry_file(templates_dir):
    """Create registry file with initial content."""
    registry = templates_dir / "prompt_templates_registry.json"
    registry_data = {
        "version": "1.0",
        "last_updated": "2026-01-12T00:00:00",
        "active_template": None,
        "templates": []
    }
    with open(registry, 'w') as f:
        json.dump(registry_data, f, indent=2)
    return registry


@pytest.fixture
def config_prompt_file(config_dir):
    """Create config_prompt.json file."""
    config_prompt = config_dir / "config_prompt.json"
    blank_config = {
        "system_prompt": None,
        "master_prompt": None,
        "assistant_prompt": None,
        "conversation_format": "standard",
        "prefix_messages": [],
        "suffix_messages": []
    }
    with open(config_prompt, 'w') as f:
        json.dump(blank_config, f, indent=2)
    return config_prompt


@pytest.fixture
def mock_config(config_dir):
    """Create mock Config instance."""
    config = Mock(spec=Config)
    config.config_file = str(config_dir / "config.json")
    return config


@pytest.fixture
def sample_template(templates_dir):
    """Create a sample template directory with files."""
    template_dir = templates_dir / "test_template"
    template_dir.mkdir()

    # Create prompt.json
    template_config = {
        "system_prompt": "You are a helpful assistant",
        "master_prompt": None,
        "assistant_prompt": None,
        "conversation_format": "standard",
        "prefix_messages": [],
        "suffix_messages": []
    }
    with open(template_dir / "prompt.json", 'w') as f:
        json.dump(template_config, f, indent=2)

    # Create config.json
    metadata = {
        "name": "test_template",
        "display_name": "Test Template",
        "description": "A test template",
        "category": "test",
        "author": "tester",
        "version": "1.0",
        "tags": ["test"],
        "created_date": "2026-01-12T00:00:00",
        "last_modified": "2026-01-12T00:00:00"
    }
    with open(template_dir / "config.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    return template_dir


class TestGetPromptManager:
    """Test get_prompt_manager utility function."""

    def test_get_prompt_manager_with_config_file(self, mock_config, config_dir):
        """Test getting prompt manager with config file."""
        manager = get_prompt_manager(mock_config)

        assert isinstance(manager, PromptManager)
        assert manager.templates_dir == config_dir / "prompt_templates"
        assert manager.registry_file == config_dir / "prompt_templates" / "prompt_templates_registry.json"
        assert manager.active_prompt_file == config_dir / "config_prompt.json"

    def test_get_prompt_manager_without_config_file(self, temp_dir):
        """Test getting prompt manager without config file."""
        config = Mock(spec=Config)
        config.config_file = None

        with patch('llf.prompt_commands.Path.cwd', return_value=temp_dir):
            manager = get_prompt_manager(config)

            assert isinstance(manager, PromptManager)
            assert manager.templates_dir == temp_dir / "configs" / "prompt_templates"


class TestListTemplatesCommand:
    """Test list_templates_command function."""

    def test_list_templates_empty(self, mock_config, registry_file):
        """Test listing templates when none exist."""
        args = Namespace(category=None)

        with patch('llf.prompt_commands.console') as mock_console:
            result = list_templates_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_any_call("[yellow]No templates found[/yellow]")

    def test_list_templates_with_category_filter_no_match(self, mock_config, registry_file, templates_dir):
        """Test listing templates with category filter that matches nothing."""
        # Add a template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test",
            "display_name": "Test",
            "description": "Test template",
            "category": "general",
            "author": "system",
            "version": "1.0",
            "tags": [],
            "directory": "test",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(category="nonexistent")

        with patch('llf.prompt_commands.console') as mock_console:
            result = list_templates_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_any_call("[yellow]No templates found[/yellow]")


class TestInfoTemplateCommand:
    """Test info_template_command function."""

    def test_info_template_not_found(self, mock_config, registry_file):
        """Test showing info for non-existent template."""
        args = Namespace(template_name="nonexistent")

        with patch('llf.prompt_commands.console') as mock_console:
            result = info_template_command(mock_config, args)

            assert result == 1
            mock_console.print.assert_called_with("[red]Template 'nonexistent' not found[/red]")

    def test_info_template_success(self, mock_config, registry_file, templates_dir):
        """Test showing info for existing template."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "general",
            "author": "tester",
            "version": "1.0",
            "tags": ["test", "demo"],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = info_template_command(mock_config, args)

            assert result == 0
            # Check that Panel was printed (info is displayed in a panel)
            assert mock_console.print.called


class TestDisableTemplateCommand:
    """Test disable_template_command function."""

    def test_disable_no_active_template(self, mock_config, registry_file, config_prompt_file):
        """Test disabling when no template is active."""
        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = disable_template_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_called_with("[yellow]No template is currently enabled[/yellow]")

    def test_disable_active_template(self, mock_config, registry_file, config_prompt_file, templates_dir):
        """Test disabling an active template."""
        # Set an active template in registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['active_template'] = 'test_template'
        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "general",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        # Set non-blank config_prompt
        config_data = {
            "system_prompt": "Test prompt",
            "master_prompt": None,
            "assistant_prompt": None,
            "conversation_format": "standard",
            "prefix_messages": [],
            "suffix_messages": []
        }
        with open(config_prompt_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = disable_template_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_any_call("[green]✓ Template 'test_template' disabled[/green]")
            mock_console.print.assert_any_call("[dim]Prompt configuration reset to blank[/dim]")

        # Verify config was reset
        with open(config_prompt_file, 'r') as f:
            config = json.load(f)
        assert config['system_prompt'] is None

        # Verify registry was updated
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert registry['active_template'] is None


class TestCreateTemplateCommand:
    """Test create_template_command function."""

    @patch('llf.prompt_commands.Prompt.ask')
    def test_create_template_success(self, mock_prompt, mock_config, registry_file, templates_dir):
        """Test successfully creating a template."""
        mock_prompt.side_effect = [
            "new_template",  # name
            "New Template",  # display_name
            "A new template",  # description
            "general",  # category
            "test",  # tags
            "You are a helper",  # system_prompt
            None,  # master_prompt
            None,  # assistant_prompt
            "standard"  # conversation_format
        ]

        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = create_template_command(mock_config, args)

            assert result == 0
            calls = [str(call) for call in mock_console.print.call_args_list]
            success_found = any("created successfully" in str(call).lower() for call in calls)
            assert success_found

        # Verify template directory was created
        assert (templates_dir / "new_template").exists()
        assert (templates_dir / "new_template" / "prompt.json").exists()

        # Verify registry was updated
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 1
        assert registry['templates'][0]['name'] == 'new_template'


class TestBackupTemplatesCommand:
    """Test backup_templates_command function."""

    def test_backup_templates_success(self, mock_config, registry_file, sample_template):
        """Test successfully creating a backup."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = backup_templates_command(mock_config, args)

            assert result == 0
            # Should print success message with backup path
            assert mock_console.print.called

    def test_backup_templates_failure(self, mock_config, registry_file):
        """Test backup failure."""
        args = Namespace()

        # Mock PromptManager.backup_templates to return None (failure)
        with patch('llf.prompt_commands.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.backup_templates.return_value = None
            mock_get_manager.return_value = mock_manager

            with patch('llf.prompt_commands.console') as mock_console:
                result = backup_templates_command(mock_config, args)

                assert result == 1
                # Check that the function printed the "Creating backup..." message
                # (the failure message is actually printed by the manager, not the command)
                assert mock_console.print.called


class TestEnableTemplateCommand:
    """Test enable_template_command function (MODERATE complexity)."""

    def test_enable_nonexistent_template(self, mock_config, registry_file):
        """Test enabling a template that doesn't exist."""
        args = Namespace(template_name="nonexistent", var=[])

        with patch('llf.prompt_commands.console') as mock_console:
            result = enable_template_command(mock_config, args)

            assert result == 1
            mock_console.print.assert_any_call("[red]Template 'nonexistent' not found[/red]")

    def test_enable_template_success(self, mock_config, registry_file, sample_template, config_prompt_file):
        """Test successfully enabling a template."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="test_template", var=[])

        with patch('llf.prompt_commands.console') as mock_console:
            result = enable_template_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_any_call("[green]✓ Template 'Test Template' enabled successfully[/green]")

    def test_enable_template_with_variables(self, mock_config, registry_file, config_prompt_file, templates_dir):
        """Test enabling a template with variable substitution."""
        # Create template with variables
        template_dir = templates_dir / "var_template"
        template_dir.mkdir()

        template_config = {
            "system_prompt": "You are a {{role::assistant}}",
            "master_prompt": None,
            "assistant_prompt": None,
            "conversation_format": "standard",
            "prefix_messages": [],
            "suffix_messages": []
        }
        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f, indent=2)

        # Add to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "var_template",
            "display_name": "Variable Template",
            "description": "Template with variables",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "var_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="var_template", var=["role=teacher"])

        with patch('llf.prompt_commands.console') as mock_console:
            result = enable_template_command(mock_config, args)

            assert result == 0
            # Check variables were applied
            mock_console.print.assert_any_call("\n[cyan]Applied variables:[/cyan]")

    def test_enable_template_invalid_var_format(self, mock_config, registry_file, sample_template):
        """Test enabling with invalid variable format."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="test_template", var=["invalid_format"])

        with patch('llf.prompt_commands.console') as mock_console:
            result = enable_template_command(mock_config, args)

            # Should still succeed but warn about invalid format
            assert result == 0
            # Check for warning about invalid format
            calls = [str(call) for call in mock_console.print.call_args_list]
            warning_found = any("Invalid variable format" in str(call) for call in calls)
            assert warning_found


class TestImportTemplateCommand:
    """Test import_template_command function (MODERATE complexity)."""

    def test_import_nonexistent_directory(self, mock_config, registry_file):
        """Test importing from a directory that doesn't exist."""
        args = Namespace(template_name="nonexistent")

        with patch('llf.prompt_commands.console') as mock_console:
            result = import_template_command(mock_config, args)

            assert result == 1
            # Should print error about directory not found
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_found = any("not found" in str(call).lower() for call in calls)
            assert error_found

    def test_import_directory_missing_config_json(self, mock_config, registry_file, templates_dir):
        """Test importing from directory without config.json."""
        # Create directory without config.json
        template_dir = templates_dir / "no_config"
        template_dir.mkdir()

        args = Namespace(template_name="no_config")

        with patch('llf.prompt_commands.console') as mock_console:
            result = import_template_command(mock_config, args)

            assert result == 1
            # Should print error about config.json not found
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_found = any("config.json not found" in str(call).lower() for call in calls)
            assert error_found

    def test_import_invalid_json(self, mock_config, registry_file, templates_dir):
        """Test importing with invalid JSON in config.json."""
        template_dir = templates_dir / "bad_json"
        template_dir.mkdir()

        # Write invalid JSON
        with open(template_dir / "config.json", 'w') as f:
            f.write("{invalid json")

        args = Namespace(template_name="bad_json")

        with patch('llf.prompt_commands.console') as mock_console:
            result = import_template_command(mock_config, args)

            assert result == 1
            # Should print error about invalid JSON
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_found = any("invalid json" in str(call).lower() for call in calls)
            assert error_found

    def test_import_already_exists(self, mock_config, registry_file, sample_template):
        """Test importing a template that already exists in registry."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = import_template_command(mock_config, args)

            assert result == 1
            # Should print error about already existing
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_found = any("already exists" in str(call).lower() for call in calls)
            assert error_found

    def test_import_success(self, mock_config, registry_file, sample_template):
        """Test successfully importing a template."""
        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = import_template_command(mock_config, args)

            assert result == 0
            # Should print success message
            calls = [str(call) for call in mock_console.print.call_args_list]
            success_found = any("successfully imported" in str(call).lower() for call in calls)
            assert success_found

        # Verify template was added to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 1
        assert registry['templates'][0]['name'] == 'test_template'


class TestExportTemplateCommand:
    """Test export_template_command function (MODERATE complexity)."""

    def test_export_nonexistent_template(self, mock_config, registry_file):
        """Test exporting a template that doesn't exist."""
        args = Namespace(template_name="nonexistent")

        with patch('llf.prompt_commands.console') as mock_console:
            result = export_template_command(mock_config, args)

            assert result == 1
            mock_console.print.assert_any_call("[red]Error:[/red] Template 'nonexistent' not found in registry")

    def test_export_template_directory_missing(self, mock_config, registry_file, templates_dir):
        """Test exporting when template directory doesn't exist."""
        # Add template to registry but don't create directory
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "missing_dir",
            "display_name": "Missing Dir",
            "description": "Template with missing directory",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "missing_dir",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="missing_dir")

        with patch('llf.prompt_commands.console') as mock_console:
            result = export_template_command(mock_config, args)

            # Should succeed and remove from registry
            assert result == 0
            # Should print warning about missing directory
            calls = [str(call) for call in mock_console.print.call_args_list]
            warning_found = any("not found" in str(call).lower() for call in calls)
            assert warning_found

        # Verify template was removed from registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 0

    def test_export_success(self, mock_config, registry_file, sample_template):
        """Test successfully exporting a template."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": ["test"],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = export_template_command(mock_config, args)

            assert result == 0
            # Should print success message
            calls = [str(call) for call in mock_console.print.call_args_list]
            success_found = any("successfully exported" in str(call).lower() for call in calls)
            assert success_found

        # Verify template was removed from registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 0

        # Verify config.json was created
        config_file = sample_template / "config.json"
        assert config_file.exists()

        with open(config_file, 'r') as f:
            config_data = json.load(f)
        assert config_data['name'] == 'test_template'


class TestDeleteTemplateCommand:
    """Test delete_template_command function (MODERATE complexity)."""

    def test_delete_nonexistent_template(self, mock_config, registry_file):
        """Test deleting a template that doesn't exist."""
        args = Namespace(template_name="nonexistent")

        with patch('llf.prompt_commands.console') as mock_console:
            result = delete_template_command(mock_config, args)

            assert result == 1
            mock_console.print.assert_called_with("[red]Template 'nonexistent' not found[/red]")

    @patch('llf.prompt_commands.Confirm.ask')
    def test_delete_cancelled(self, mock_confirm, mock_config, registry_file, sample_template):
        """Test deleting a template but cancelling."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        mock_confirm.return_value = False  # Cancel
        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = delete_template_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_called_with("[dim]Cancelled[/dim]")

        # Verify template still in registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 1

    @patch('llf.prompt_commands.Confirm.ask')
    def test_delete_success(self, mock_confirm, mock_config, registry_file, sample_template, templates_dir):
        """Test successfully deleting a template."""
        # Add template to registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        # Create trash directory
        trash_dir = templates_dir.parent / "trash"
        trash_dir.mkdir(exist_ok=True)

        mock_confirm.return_value = True  # Confirm
        args = Namespace(template_name="test_template")

        with patch('llf.prompt_commands.console') as mock_console:
            result = delete_template_command(mock_config, args)

            assert result == 0
            # Should print success message with trash ID
            calls = [str(call) for call in mock_console.print.call_args_list]
            success_found = any("moved to trash" in str(call).lower() for call in calls)
            assert success_found

        # Verify template was removed from registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        assert len(registry['templates']) == 0


class TestShowEnabledCommand:
    """Test show_enabled_command function."""

    def test_show_enabled_no_active_template(self, mock_config, registry_file, config_prompt_file):
        """Test showing enabled template when none is active."""
        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = show_enabled_command(mock_config, args)

            assert result == 0
            mock_console.print.assert_any_call("[yellow]No template is currently enabled[/yellow]")

    def test_show_enabled_with_active_template(self, mock_config, registry_file, config_prompt_file, templates_dir):
        """Test showing enabled template when one is active."""
        # Set active template in registry
        with open(registry_file, 'r') as f:
            registry = json.load(f)

        registry['active_template'] = 'test_template'
        registry['templates'].append({
            "name": "test_template",
            "display_name": "Test Template",
            "description": "A test template",
            "category": "test",
            "author": "tester",
            "version": "1.0",
            "tags": [],
            "directory": "test_template",
            "created_date": "2026-01-12T00:00:00",
            "last_modified": "2026-01-12T00:00:00"
        })

        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

        # Set config with prompt
        config_data = {
            "system_prompt": "Test prompt",
            "master_prompt": None,
            "assistant_prompt": None,
            "conversation_format": "standard",
            "prefix_messages": [],
            "suffix_messages": []
        }
        with open(config_prompt_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        args = Namespace()

        with patch('llf.prompt_commands.console') as mock_console:
            result = show_enabled_command(mock_config, args)

            assert result == 0
            # Should display panel with template info
            assert mock_console.print.called


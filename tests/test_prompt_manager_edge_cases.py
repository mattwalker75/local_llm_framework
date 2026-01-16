"""
Comprehensive edge case tests for PromptManager to improve coverage.

Tests cover:
- Registry loading/saving error conditions
- Template file loading errors (missing files, JSON errors)
- Template application with variables and list items
- Import/export error cases (missing files, duplicates, copy errors)
- Delete template edge cases (missing directory, trash failures)
- Backup error handling
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

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


class TestRegistryLoadingErrors:
    """Test _load_registry error handling."""

    def test_load_registry_json_decode_error(self, templates_dir, active_prompt_file):
        """Test loading registry with invalid JSON."""
        registry_file = templates_dir / "bad_registry.json"

        # Create invalid JSON file
        with open(registry_file, 'w') as f:
            f.write("{invalid json{{")

        # Create manager with bad registry - should handle error gracefully
        manager = PromptManager(templates_dir, registry_file, active_prompt_file)

        # Should have fallback default registry
        assert manager.registry is not None
        assert "version" in manager.registry
        assert "templates" in manager.registry
        assert manager.registry["active_template"] is None

    def test_load_registry_permission_error(self, templates_dir, active_prompt_file):
        """Test loading registry with permission error."""
        registry_file = templates_dir / "registry.json"

        # Create valid registry first
        with open(registry_file, 'w') as f:
            json.dump({"version": "1.0", "templates": []}, f)

        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            manager = PromptManager(templates_dir, registry_file, active_prompt_file)

            # Should have fallback default registry
            assert manager.registry is not None
            assert "templates" in manager.registry


class TestRegistrySavingErrors:
    """Test _save_registry error handling."""

    def test_save_registry_write_error(self, prompt_manager):
        """Test saving registry with write error."""
        # Mock open to raise PermissionError on write
        with patch('builtins.open', side_effect=PermissionError("Write denied")):
            # Should not raise, just print error
            prompt_manager._save_registry()
            # No exception means it handled the error gracefully


class TestLoadTemplateConfigErrors:
    """Test load_template_config error handling."""

    def test_load_template_config_not_found(self, prompt_manager):
        """Test loading template that doesn't exist in registry."""
        result = prompt_manager.load_template_config("nonexistent_template")
        assert result is None

    def test_load_template_config_file_missing(self, prompt_manager, templates_dir):
        """Test loading template when prompt.json file is missing."""
        # Add template to registry but don't create the file
        metadata = {
            "name": "missing_file_template",
            "display_name": "Missing File Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "missing_file_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Try to load - should fail gracefully
        result = prompt_manager.load_template_config("missing_file_template")
        assert result is None

    def test_load_template_config_invalid_json(self, prompt_manager, templates_dir):
        """Test loading template with invalid JSON."""
        # Create template directory with invalid JSON
        template_dir = templates_dir / "bad_json_template"
        template_dir.mkdir()

        with open(template_dir / "prompt.json", 'w') as f:
            f.write("{invalid json{{")

        # Add to registry
        metadata = {
            "name": "bad_json_template",
            "display_name": "Bad JSON Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "bad_json_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Try to load - should fail gracefully
        result = prompt_manager.load_template_config("bad_json_template")
        assert result is None


class TestApplyTemplateEdgeCases:
    """Test apply_template edge cases."""

    def test_apply_template_load_failure(self, prompt_manager):
        """Test applying template that fails to load."""
        result = prompt_manager.apply_template("nonexistent_template")
        assert result is False

    def test_apply_template_with_variables_key(self, prompt_manager, templates_dir):
        """Test applying template that has 'variables' key (should be skipped)."""
        # Create template with variables metadata
        template_dir = templates_dir / "vars_template"
        template_dir.mkdir()

        template_config = {
            "system_prompt": "Test with {{var1::default}}",
            "variables": {
                "var1": {
                    "description": "Variable 1",
                    "default": "default"
                }
            }
        }

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f)

        # Add to registry
        metadata = {
            "name": "vars_template",
            "display_name": "Vars Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "vars_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Apply template
        result = prompt_manager.apply_template("vars_template")
        assert result is True

        # Verify config was saved without variables key
        with open(prompt_manager.active_prompt_file, 'r') as f:
            config = json.load(f)
        assert "variables" not in config

    def test_apply_template_with_list_content_substitution(self, prompt_manager, templates_dir):
        """Test applying template with list items containing 'content' field."""
        # Create template with prefix_messages
        template_dir = templates_dir / "list_template"
        template_dir.mkdir()

        template_config = {
            "system_prompt": "Test",
            "prefix_messages": [
                {"role": "system", "content": "Hello {{name::user}}"},
                {"role": "user", "content": "I need help with {{topic::general}}"}
            ],
            "suffix_messages": [
                {"role": "assistant", "content": "I'm ready to help with {{topic::general}}"}
            ]
        }

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f)

        # Add to registry
        metadata = {
            "name": "list_template",
            "display_name": "List Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "list_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Apply with variables
        variables = {"name": "Alice", "topic": "Python"}
        result = prompt_manager.apply_template("list_template", variables)
        assert result is True

        # Verify substitutions in lists
        with open(prompt_manager.active_prompt_file, 'r') as f:
            config = json.load(f)

        assert config["prefix_messages"][0]["content"] == "Hello Alice"
        assert config["prefix_messages"][1]["content"] == "I need help with Python"
        assert config["suffix_messages"][0]["content"] == "I'm ready to help with Python"

    def test_apply_template_with_list_items_without_content(self, prompt_manager, templates_dir):
        """Test applying template with list items that don't have 'content' field."""
        # Create template with list items without content
        template_dir = templates_dir / "list_no_content_template"
        template_dir.mkdir()

        template_config = {
            "system_prompt": "Test",
            "prefix_messages": [
                {"role": "system", "content": "Hello"},
                "raw_string_item",  # String item without dict
                {"role": "user", "other_field": "value"}  # Dict without 'content'
            ]
        }

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f)

        # Add to registry
        metadata = {
            "name": "list_no_content_template",
            "display_name": "List No Content Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "list_no_content_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Apply template
        result = prompt_manager.apply_template("list_no_content_template")
        assert result is True

        # Verify items were preserved as-is
        with open(prompt_manager.active_prompt_file, 'r') as f:
            config = json.load(f)

        assert len(config["prefix_messages"]) == 3
        assert config["prefix_messages"][0]["content"] == "Hello"
        assert config["prefix_messages"][1] == "raw_string_item"
        assert config["prefix_messages"][2] == {"role": "user", "other_field": "value"}

    def test_apply_template_save_error(self, prompt_manager, templates_dir):
        """Test apply_template when saving config fails."""
        # Create valid template
        template_dir = templates_dir / "save_error_template"
        template_dir.mkdir()

        template_config = {"system_prompt": "Test"}
        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f)

        # Add to registry
        metadata = {
            "name": "save_error_template",
            "display_name": "Save Error Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "save_error_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Mock open to fail on write to active_prompt_file
        original_open = open
        def selective_open(path, *args, **kwargs):
            if str(path) == str(prompt_manager.active_prompt_file) and 'w' in args:
                raise PermissionError("Write denied")
            return original_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=selective_open):
            result = prompt_manager.apply_template("save_error_template")
            assert result is False


class TestImportTemplateEdgeCases:
    """Test import_template edge cases."""

    def test_import_template_source_not_found(self, prompt_manager, temp_dir):
        """Test importing from non-existent source file."""
        source_path = temp_dir / "nonexistent.json"

        result = prompt_manager.import_template(
            source_path=source_path,
            name="import_test",
            display_name="Import Test",
            description="Test",
            category="general"
        )
        assert result is False

    def test_import_template_already_exists(self, prompt_manager, temp_dir, templates_dir):
        """Test importing template with name that already exists."""
        # Create source file
        source_path = temp_dir / "import_source.json"
        with open(source_path, 'w') as f:
            json.dump({"system_prompt": "Test"}, f)

        # Add existing template to registry
        metadata = {
            "name": "duplicate_template",
            "display_name": "Duplicate",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "duplicate_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Try to import with same name
        result = prompt_manager.import_template(
            source_path=source_path,
            name="duplicate_template",
            display_name="Duplicate Test",
            description="Test",
            category="general"
        )
        assert result is False

    def test_import_template_copy_error(self, prompt_manager, temp_dir):
        """Test importing template when file copy fails."""
        # Create source file
        source_path = temp_dir / "import_source.json"
        with open(source_path, 'w') as f:
            json.dump({"system_prompt": "Test"}, f)

        # Mock shutil.copy2 to raise error
        with patch('shutil.copy2', side_effect=PermissionError("Copy denied")):
            result = prompt_manager.import_template(
                source_path=source_path,
                name="copy_error_template",
                display_name="Copy Error",
                description="Test",
                category="general"
            )
            assert result is False


class TestExportTemplateEdgeCases:
    """Test export_template edge cases."""

    def test_export_template_not_found(self, prompt_manager, temp_dir):
        """Test exporting non-existent template."""
        output_path = temp_dir / "export.json"
        result = prompt_manager.export_template("nonexistent", output_path)
        assert result is False

    def test_export_template_write_error(self, prompt_manager, templates_dir, temp_dir):
        """Test exporting template when write fails."""
        # Create valid template
        template_dir = templates_dir / "export_template"
        template_dir.mkdir()

        template_config = {"system_prompt": "Test"}
        with open(template_dir / "prompt.json", 'w') as f:
            json.dump(template_config, f)

        # Add to registry
        metadata = {
            "name": "export_template",
            "display_name": "Export Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "export_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        output_path = temp_dir / "export.json"

        # Mock open to fail on write
        original_open = open
        def selective_open(path, *args, **kwargs):
            if str(path) == str(output_path) and 'w' in args:
                raise PermissionError("Write denied")
            return original_open(path, *args, **kwargs)

        with patch('builtins.open', side_effect=selective_open):
            result = prompt_manager.export_template("export_template", output_path)
            assert result is False


class TestDisableTemplateEdgeCases:
    """Test disable_template edge cases."""

    def test_disable_template_write_error(self, prompt_manager):
        """Test disabling template when config write fails."""
        # Mock open to fail on write
        with patch('builtins.open', side_effect=PermissionError("Write denied")):
            result = prompt_manager.disable_template()
            assert result is False


class TestBackupTemplatesEdgeCases:
    """Test backup_templates edge cases."""

    def test_backup_templates_copy_error(self, prompt_manager, templates_dir):
        """Test backup when copy operations fail."""
        # Add a template
        template_dir = templates_dir / "backup_template"
        template_dir.mkdir()

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump({"system_prompt": "Test"}, f)

        metadata = {
            "name": "backup_template",
            "display_name": "Backup Template",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "backup_template"
        }
        prompt_manager.registry["templates"].append(metadata)
        prompt_manager._save_registry()

        # Mock shutil.copy2 to raise error
        with patch('shutil.copy2', side_effect=PermissionError("Copy denied")):
            result = prompt_manager.backup_templates()
            assert result is None


class TestDeleteTemplateEdgeCases:
    """Test delete_template edge cases."""

    def test_delete_template_not_found(self, prompt_manager):
        """Test deleting template that doesn't exist."""
        success, trash_id = prompt_manager.delete_template("nonexistent")
        assert success is False
        assert trash_id is None

    def test_delete_template_directory_missing(self, prompt_manager):
        """Test deleting template when directory doesn't exist."""
        # Add template to registry but don't create directory
        metadata = {
            "name": "missing_dir_template",
            "display_name": "Missing Dir",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "missing_dir_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Set as active template
        prompt_manager.registry["active_template"] = "missing_dir_template"
        prompt_manager._save_registry()

        # Delete should succeed and remove from registry
        success, trash_id = prompt_manager.delete_template("missing_dir_template")
        assert success is True
        assert trash_id is None  # No trash ID when directory doesn't exist

        # Verify removed from registry
        assert prompt_manager.get_template("missing_dir_template") is None

        # Verify active template was cleared
        assert prompt_manager.registry.get("active_template") is None

    def test_delete_template_trash_failure(self, prompt_manager, templates_dir):
        """Test deleting template when trash manager fails."""
        # Create template
        template_dir = templates_dir / "trash_fail_template"
        template_dir.mkdir()

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump({"system_prompt": "Test"}, f)

        metadata = {
            "name": "trash_fail_template",
            "display_name": "Trash Fail",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "trash_fail_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Mock TrashManager to fail
        with patch('llf.prompt_manager.TrashManager') as mock_trash_class:
            mock_trash = MagicMock()
            mock_trash.move_to_trash.return_value = (False, "Trash error")
            mock_trash_class.return_value = mock_trash

            success, error = prompt_manager.delete_template("trash_fail_template")
            assert success is False
            assert error == "Trash error"

    def test_delete_active_template_clears_active(self, prompt_manager, templates_dir):
        """Test deleting active template clears active_template field."""
        # Create template
        template_dir = templates_dir / "active_template"
        template_dir.mkdir()

        with open(template_dir / "prompt.json", 'w') as f:
            json.dump({"system_prompt": "Test"}, f)

        metadata = {
            "name": "active_template",
            "display_name": "Active",
            "description": "Test",
            "category": "general",
            "author": "test",
            "version": "1.0",
            "tags": [],
            "directory": "active_template"
        }
        prompt_manager.registry["templates"].append(metadata)

        # Set as active
        prompt_manager.registry["active_template"] = "active_template"
        prompt_manager._save_registry()

        # Delete it
        success, trash_id = prompt_manager.delete_template("active_template")
        assert success is True

        # Verify active template was cleared
        assert prompt_manager.registry.get("active_template") is None

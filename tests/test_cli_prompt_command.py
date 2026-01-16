"""
Comprehensive tests for prompt_command to improve CLI coverage.

Targets:
- prompt_command (lines 1420-1449) - routing to template sub-commands
"""

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

from llf.cli import prompt_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    return config


class TestPromptCommandRouting:
    """Test prompt_command action routing (lines 1420-1449)."""

    def test_list_action_routing(self, mock_config):
        """Test 'list' action routes to list_templates_command (lines 1426-1427)."""
        args = Namespace(action='list')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.list_templates_command') as mock_list_templates:
                mock_list_templates.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called list_templates_command
                mock_list_templates.assert_called_once_with(mock_config, args)

    def test_info_action_routing(self, mock_config):
        """Test 'info' action routes to info_template_command (lines 1428-1429)."""
        args = Namespace(action='info', name='test_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.info_template_command') as mock_info_template:
                mock_info_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called info_template_command
                mock_info_template.assert_called_once_with(mock_config, args)

    def test_enable_action_routing(self, mock_config):
        """Test 'enable' action routes to enable_template_command (lines 1430-1431)."""
        args = Namespace(action='enable', name='test_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.enable_template_command') as mock_enable_template:
                mock_enable_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called enable_template_command
                mock_enable_template.assert_called_once_with(mock_config, args)

    def test_disable_action_routing(self, mock_config):
        """Test 'disable' action routes to disable_template_command (lines 1432-1433)."""
        args = Namespace(action='disable', name='test_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.disable_template_command') as mock_disable_template:
                mock_disable_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called disable_template_command
                mock_disable_template.assert_called_once_with(mock_config, args)

    def test_import_action_routing(self, mock_config):
        """Test 'import' action routes to import_template_command (lines 1434-1435)."""
        args = Namespace(action='import', path='/path/to/template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.import_template_command') as mock_import_template:
                mock_import_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called import_template_command
                mock_import_template.assert_called_once_with(mock_config, args)

    def test_export_action_routing(self, mock_config):
        """Test 'export' action routes to export_template_command (lines 1436-1437)."""
        args = Namespace(action='export', name='test_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.export_template_command') as mock_export_template:
                mock_export_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called export_template_command
                mock_export_template.assert_called_once_with(mock_config, args)

    def test_backup_action_routing(self, mock_config):
        """Test 'backup' action routes to backup_templates_command (lines 1438-1439)."""
        args = Namespace(action='backup')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.backup_templates_command') as mock_backup_templates:
                mock_backup_templates.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called backup_templates_command
                mock_backup_templates.assert_called_once_with(mock_config, args)

    def test_delete_action_routing(self, mock_config):
        """Test 'delete' action routes to delete_template_command (lines 1440-1441)."""
        args = Namespace(action='delete', name='test_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.delete_template_command') as mock_delete_template:
                mock_delete_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called delete_template_command
                mock_delete_template.assert_called_once_with(mock_config, args)

    def test_create_action_routing(self, mock_config):
        """Test 'create' action routes to create_template_command (lines 1442-1443)."""
        args = Namespace(action='create', name='new_template')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.create_template_command') as mock_create_template:
                mock_create_template.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called create_template_command
                mock_create_template.assert_called_once_with(mock_config, args)

    def test_show_enabled_action_routing(self, mock_config):
        """Test 'show_enabled' action routes to show_enabled_command (lines 1444-1445)."""
        args = Namespace(action='show_enabled')

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.show_enabled_command') as mock_show_enabled:
                mock_show_enabled.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called show_enabled_command
                mock_show_enabled.assert_called_once_with(mock_config, args)

    def test_default_action_is_list(self, mock_config):
        """Test that no action defaults to 'list' (lines 1422-1423)."""
        args = Namespace(action=None)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.list_templates_command') as mock_list_templates:
                mock_list_templates.return_value = 0

                result = prompt_command(args)

                # Should return success
                assert result == 0
                # Should have called list_templates_command (default action)
                mock_list_templates.assert_called_once_with(mock_config, args)

    def test_unknown_action_returns_error(self, mock_config):
        """Test unknown action returns error code (lines 1446-1449)."""
        args = Namespace(action='unknown_action')

        with patch('llf.cli.get_config', return_value=mock_config):
            result = prompt_command(args)

            # Should return error code
            assert result == 1

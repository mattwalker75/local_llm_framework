"""
Tests for untested CLI commands to improve coverage.

Targets:
- import_model_command (lines 1016-1154)
- export_model_command (lines 1167-1250)
- chat_history_list_command (lines 1463-1513)
- chat_history_info_command (lines 1527-1604)
- chat_history_cleanup_command (lines 1618-1644)
- chat_history_delete_command (lines 1658-1714)
- chat_export_command (lines 1728-1781)
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from argparse import Namespace

from llf.cli import (
    import_model_command,
    export_model_command,
    chat_history_list_command,
    chat_history_info_command,
    chat_history_cleanup_command,
    chat_history_delete_command,
    chat_export_command
)
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.config_file = tmp_path / "config.json"
    config.model_dir = tmp_path / "models"
    config.chat_history_dir = tmp_path / "chat_history"
    config.chat_history_dir.mkdir(parents=True, exist_ok=True)
    return config


class TestImportModelCommand:
    """Test import_model_command (lines 1016-1154)."""

    def test_import_model_not_downloaded(self, tmp_path):
        """Test importing model that isn't downloaded."""
        args = Namespace(model_name="test/model")

        with patch('llf.cli.get_config') as mock_get_config:
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_config = Mock()
                mock_get_config.return_value = mock_config

                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = False
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return error code
                assert result == 1
                mock_manager.is_model_downloaded.assert_called_once_with("test/model")

    def test_import_model_no_q5km_file(self, tmp_path):
        """Test importing model with no Q5_K_M GGUF file."""
        args = Namespace(model_name="test/model")

        with patch('llf.cli.get_config') as mock_get_config:
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_config = Mock()
                mock_get_config.return_value = mock_config

                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True

                # Mock model info with path
                model_path = tmp_path / "models" / "test--model"
                model_path.mkdir(parents=True, exist_ok=True)

                mock_manager.get_model_info.return_value = {
                    'path': str(model_path)
                }
                MockModelManager.return_value = mock_manager

                result = import_model_command(args)

                # Should return error code (no Q5_K_M file found)
                assert result == 1


class TestExportModelCommand:
    """Test export_model_command (lines 1167-1250)."""

    def test_export_model_not_in_config(self, tmp_path):
        """Test exporting model not in config."""
        args = Namespace(model_name="test/model")

        config_file = tmp_path / "config.json"
        config_data = {"local_llm_servers": []}
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.config_file = config_file
            mock_config.DEFAULT_CONFIG_FILE = config_file
            mock_get_config.return_value = mock_config

            result = export_model_command(args)

            # Returns 0 but prints message (no servers found)
            assert result == 0

    def test_export_model_model_not_downloaded(self, tmp_path):
        """Test exporting model that isn't downloaded."""
        args = Namespace(model_name="test/model")

        config_file = tmp_path / "config.json"
        config_data = {
            "local_llm_servers": [
                {
                    "name": "test_server",
                    "model_dir": "test--model",
                    "gguf_file": "model.gguf"
                }
            ],
            "llm_endpoint": {
                "api_base_url": "http://localhost:8000/v1",
                "model_name": "test/model"
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.cli.get_config') as mock_get_config:
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_config = Mock()
                mock_config.config_file = config_file
                mock_config.DEFAULT_CONFIG_FILE = config_file
                mock_config.backup_config.return_value = str(tmp_path / "backup.json")
                mock_get_config.return_value = mock_config

                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = False
                MockModelManager.return_value = mock_manager

                result = export_model_command(args)

                # Returns 0 (exports successfully even if model not downloaded)
                assert result == 0


class TestChatHistoryListCommand:
    """Test chat_history_list_command (lines 1463-1513)."""

    def test_list_no_history_files(self, mock_config):
        """Test listing when no history files exist."""
        args = Namespace()

        result = chat_history_list_command(mock_config, args)

        # Should return success even with no files
        assert result == 0

    def test_list_with_history_files(self, mock_config):
        """Test listing with existing history files."""
        # Create some mock history files
        history_file1 = mock_config.chat_history_dir / "chat_20260115_100000_123456.json"
        history_file2 = mock_config.chat_history_dir / "chat_20260115_110000_234567.json"

        history_data = {
            "session_id": "test_session",
            "messages": [{"role": "user", "content": "test"}],
            "metadata": {"model": "test-model"}
        }

        for file in [history_file1, history_file2]:
            with open(file, 'w') as f:
                json.dump(history_data, f)

        args = Namespace()

        result = chat_history_list_command(mock_config, args)

        # Should return success
        assert result == 0


class TestChatHistoryInfoCommand:
    """Test chat_history_info_command (lines 1527-1604)."""

    def test_info_file_not_found(self, mock_config):
        """Test getting info for non-existent file."""
        args = Namespace(session_id="nonexistent")

        result = chat_history_info_command(mock_config, args)

        # Should return error code
        assert result == 1

    def test_info_with_valid_file(self, mock_config):
        """Test getting info for valid history file."""
        # Create a mock history file with proper session_id format
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id)

        result = chat_history_info_command(mock_config, args)

        # Should return success
        assert result == 0


class TestChatHistoryCleanupCommand:
    """Test chat_history_cleanup_command (lines 1618-1644)."""

    def test_cleanup_no_files(self, mock_config):
        """Test cleanup when no files exist."""
        args = Namespace(days=30, dry_run=False)

        with patch('llf.cli.TrashManager') as MockTrashManager:
            with patch('builtins.input', return_value='yes'):
                mock_trash = Mock()
                MockTrashManager.return_value = mock_trash

                result = chat_history_cleanup_command(mock_config, args)

                # Should return success
                assert result == 0

    def test_cleanup_with_user_confirmation(self, mock_config):
        """Test cleanup with user confirmation."""
        # Create an old mock history file
        from datetime import datetime, timedelta
        old_date = datetime.now() - timedelta(days=40)
        session_id = old_date.strftime('%Y%m%d_%H%M%S') + "_123456"
        filename = f"chat_{session_id}.json"
        history_file = mock_config.chat_history_dir / filename

        history_data = {
            "session_id": session_id,
            "messages": [],
            "metadata": {},
            "timestamp": old_date.isoformat()
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(days=30, dry_run=False)

        with patch('llf.cli.TrashManager') as MockTrashManager:
            with patch('builtins.input', return_value='yes'):
                mock_trash = Mock()
                MockTrashManager.return_value = mock_trash

                result = chat_history_cleanup_command(mock_config, args)

                # Should return success
                assert result == 0


class TestChatHistoryDeleteCommand:
    """Test chat_history_delete_command (lines 1658-1714)."""

    def test_delete_file_not_found(self, mock_config):
        """Test deleting non-existent file."""
        args = Namespace(session_id="nonexistent", force=False)

        result = chat_history_delete_command(mock_config, args)

        # Should return error code
        assert result == 1

    def test_delete_with_force_flag(self, mock_config):
        """Test delete with force flag."""
        # Create a mock history file with proper session_id
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [],
            "metadata": {},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        args = Namespace(session_id=session_id, force=True)

        with patch('llf.cli.TrashManager') as MockTrashManager:
            mock_trash = Mock()
            # TrashManager.move_to_trash returns a tuple (success, trash_id)
            mock_trash.move_to_trash.return_value = (True, "trash_123")
            MockTrashManager.return_value = mock_trash

            result = chat_history_delete_command(mock_config, args)

            # Should return success
            assert result == 0


class TestChatExportCommand:
    """Test chat_export_command (lines 1728-1781)."""

    def test_export_file_not_found(self, mock_config):
        """Test exporting non-existent file."""
        args = Namespace(session_id="nonexistent", format="markdown", output=None)

        result = chat_export_command(mock_config, args)

        # Should return error code
        assert result == 1

    def test_export_to_markdown(self, mock_config, tmp_path):
        """Test exporting to markdown format."""
        # Create a mock history file with proper session_id
        session_id = "20260115_100000_123456"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T10:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        output_file = tmp_path / "export.md"
        args = Namespace(session_id=session_id, format="markdown", output=str(output_file))

        result = chat_export_command(mock_config, args)

        # Should return success
        assert result == 0
        # Output file should exist
        assert output_file.exists()

    def test_export_to_json(self, mock_config, tmp_path):
        """Test exporting to JSON format."""
        # Create a mock history file with proper session_id
        session_id = "20260115_110000_234567"
        history_file = mock_config.chat_history_dir / f"chat_{session_id}.json"

        history_data = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "metadata": {"model": "test-model"},
            "timestamp": "2026-01-15T11:00:00"
        }

        with open(history_file, 'w') as f:
            json.dump(history_data, f)

        output_file = tmp_path / "export.json"
        args = Namespace(session_id=session_id, format="json", output=str(output_file))

        result = chat_export_command(mock_config, args)

        # Should return success
        assert result == 0
        # Output file should exist
        assert output_file.exists()

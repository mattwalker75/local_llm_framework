"""
Tests for 'llf model delete' command to improve CLI coverage.

Targets lines 959-1038 in cli.py (delete_command function).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

from llf.cli import delete_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.model_dir = tmp_path / "models"
    config.model_dir.mkdir(parents=True, exist_ok=True)
    return config


class TestDeleteCommand:
    """Test 'llf model delete' command (lines 959-1038)."""

    def test_delete_model_not_downloaded(self, mock_config):
        """Test deleting a model that isn't downloaded (lines 970-974)."""
        args = Namespace(model_name="test/model")

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = False
                MockModelManager.return_value = mock_manager

                result = delete_command(args)

                # Should return error code when model not downloaded
                assert result == 1
                mock_manager.is_model_downloaded.assert_called_once_with("test/model")

    def test_delete_model_user_confirms(self, mock_config, tmp_path):
        """Test deleting model with user confirmation (lines 985-999)."""
        args = Namespace(model_name="test/model", force=False)

        # Create a fake model directory
        model_dir = mock_config.model_dir / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.Prompt.ask', return_value='yes'):
                    mock_manager = Mock()
                    mock_manager.is_model_downloaded.return_value = True
                    mock_manager.get_model_info.return_value = {
                        'name': 'test/model',
                        'path': str(model_dir),
                        'size_gb': '5.2'
                    }
                    mock_manager.delete_model.return_value = True
                    MockModelManager.return_value = mock_manager

                    result = delete_command(args)

                    # Should return success
                    assert result == 0
                    # Should call delete_model
                    mock_manager.delete_model.assert_called_once_with("test/model")

    def test_delete_model_user_declines(self, mock_config, tmp_path):
        """Test deleting model when user declines confirmation (lines 993-995)."""
        args = Namespace(model_name="test/model", force=False)

        model_dir = mock_config.model_dir / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.Prompt.ask', return_value='no'):
                    mock_manager = Mock()
                    mock_manager.is_model_downloaded.return_value = True
                    mock_manager.get_model_info.return_value = {
                        'name': 'test/model',
                        'path': str(model_dir),
                        'size_gb': '5.2'
                    }
                    MockModelManager.return_value = mock_manager

                    result = delete_command(args)

                    # Should return 0 but not delete
                    assert result == 0
                    # Should NOT call delete_model
                    mock_manager.delete_model.assert_not_called()

    def test_delete_model_with_force_flag(self, mock_config, tmp_path):
        """Test deleting model with --force flag (skips confirmation, lines 985-999)."""
        args = Namespace(model_name="test/model", force=True)

        model_dir = mock_config.model_dir / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                # No Prompt.ask call should happen with force=True
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {
                    'name': 'test/model',
                    'path': str(model_dir),
                    'size_gb': '5.2'
                }
                mock_manager.delete_model.return_value = True
                MockModelManager.return_value = mock_manager

                result = delete_command(args)

                # Should return success
                assert result == 0
                # Should call delete_model
                mock_manager.delete_model.assert_called_once_with("test/model")

    def test_delete_model_fails(self, mock_config, tmp_path):
        """Test deletion when delete_model operation fails (lines 1001-1003)."""
        args = Namespace(model_name="test/model", force=True)

        model_dir = mock_config.model_dir / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.is_model_downloaded.return_value = True
                mock_manager.get_model_info.return_value = {
                    'name': 'test/model',
                    'path': str(model_dir)
                }
                # delete_model fails
                mock_manager.delete_model.return_value = False
                MockModelManager.return_value = mock_manager

                result = delete_command(args)

                # Should return error code
                assert result == 1

    def test_delete_model_without_size_info(self, mock_config, tmp_path):
        """Test deleting model when size info not available (lines 988-989)."""
        args = Namespace(model_name="test/model", force=False)

        model_dir = mock_config.model_dir / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                with patch('llf.cli.Prompt.ask', return_value='yes'):
                    mock_manager = Mock()
                    mock_manager.is_model_downloaded.return_value = True
                    # No size_gb in info
                    mock_manager.get_model_info.return_value = {
                        'name': 'test/model',
                        'path': str(model_dir)
                    }
                    mock_manager.delete_model.return_value = True
                    MockModelManager.return_value = mock_manager

                    result = delete_command(args)

                    # Should still succeed
                    assert result == 0

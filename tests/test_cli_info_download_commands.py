"""
Tests for 'llf model info' and 'llf model download' commands to improve CLI coverage.

Targets:
- info_command (lines 921-956)
- download_command (lines 746-807)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from argparse import Namespace

from llf.cli import info_command, download_command
from llf.config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config = Config()
    config.model_dir = tmp_path / "models"
    config.model_dir.mkdir(parents=True, exist_ok=True)
    config.model_name = "default/model"
    return config


class TestInfoCommand:
    """Test 'llf model info' command (lines 921-956)."""

    def test_info_with_specific_model(self, mock_config):
        """Test showing info for a specific model (lines 934-935)."""
        args = Namespace(model="test/model")

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.get_model_info.return_value = {
                    'name': 'test/model',
                    'path': '/path/to/model',
                    'downloaded': True,
                    'size_gb': '5.2',
                    'verification': {
                        'exists': True,
                        'has_config': True,
                        'has_tokenizer': True,
                        'has_weights': True,
                        'valid': True
                    }
                }
                MockModelManager.return_value = mock_manager

                result = info_command(args)

                # Should return success
                assert result == 0
                mock_manager.get_model_info.assert_called_once_with("test/model")

    def test_info_with_default_model(self, mock_config):
        """Test showing info for default model when none specified (line 934)."""
        args = Namespace(model=None)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.get_model_info.return_value = {
                    'name': 'default/model',
                    'path': '/path/to/default',
                    'downloaded': True,
                    'verification': {
                        'exists': True,
                        'has_config': False,
                        'has_tokenizer': True,
                        'has_weights': True,
                        'valid': False
                    }
                }
                MockModelManager.return_value = mock_manager

                result = info_command(args)

                # Should return success
                assert result == 0
                # Should use config.model_name
                mock_manager.get_model_info.assert_called_once_with("default/model")

    def test_info_model_not_downloaded(self, mock_config):
        """Test showing info for model that's not downloaded (line 942)."""
        args = Namespace(model="notdownloaded/model")

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.get_model_info.return_value = {
                    'name': 'notdownloaded/model',
                    'path': '/path/to/model',
                    'downloaded': False,
                    'verification': {
                        'exists': False,
                        'has_config': False,
                        'has_tokenizer': False,
                        'has_weights': False,
                        'valid': False
                    }
                }
                MockModelManager.return_value = mock_manager

                result = info_command(args)

                # Should still return success (just shows downloaded: No)
                assert result == 0

    def test_info_model_without_size(self, mock_config):
        """Test showing info when size_gb not available (line 943)."""
        args = Namespace(model="test/model")

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.get_model_info.return_value = {
                    'name': 'test/model',
                    'path': '/path/to/model',
                    'downloaded': True,
                    # No size_gb field
                    'verification': {
                        'exists': True,
                        'has_config': True,
                        'has_tokenizer': True,
                        'has_weights': True,
                        'valid': True
                    }
                }
                MockModelManager.return_value = mock_manager

                result = info_command(args)

                # Should still return success
                assert result == 0


class TestDownloadCommand:
    """Test 'llf model download' command (lines 746-807)."""

    def test_download_from_huggingface_with_model_arg(self, mock_config):
        """Test downloading from HuggingFace with specific model (lines 780-791)."""
        args = Namespace(
            url=None,
            huggingface_model="test/model",
            force=False,
            token=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.return_value = None
                mock_manager.get_model_info.return_value = {
                    'path': '/path/to/model',
                    'size_gb': '5.2'
                }
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                mock_manager.download_model.assert_called_once_with(
                    "test/model",
                    force=False,
                    token=None
                )

    def test_download_from_huggingface_default_model(self, mock_config):
        """Test downloading default model (line 781)."""
        args = Namespace(
            url=None,
            huggingface_model=None,
            force=False,
            token=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.return_value = None
                mock_manager.get_model_info.return_value = {
                    'path': '/path/to/default',
                    'size_gb': '3.8'
                }
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                # Should use config.model_name
                mock_manager.download_model.assert_called_once_with(
                    "default/model",
                    force=False,
                    token=None
                )

    def test_download_with_force_flag(self, mock_config):
        """Test downloading with force flag (lines 787-789)."""
        args = Namespace(
            url=None,
            huggingface_model="test/model",
            force=True,
            token=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.return_value = None
                mock_manager.get_model_info.return_value = {
                    'path': '/path/to/model'
                }
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                mock_manager.download_model.assert_called_once_with(
                    "test/model",
                    force=True,
                    token=None
                )

    def test_download_with_token(self, mock_config):
        """Test downloading with HuggingFace token (lines 782, 789)."""
        args = Namespace(
            url=None,
            huggingface_model="private/model",
            force=False,
            token="hf_secret_token"
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.return_value = None
                mock_manager.get_model_info.return_value = {
                    'path': '/path/to/private/model',
                    'size_gb': '10.5'
                }
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                mock_manager.download_model.assert_called_once_with(
                    "private/model",
                    force=False,
                    token="hf_secret_token"
                )

    def test_download_from_url(self, mock_config, tmp_path):
        """Test downloading from URL (lines 761-777)."""
        args = Namespace(
            url="https://example.com/model.gguf",
            name="custom_model",
            force=False
        )

        model_path = tmp_path / "models" / "custom_model"
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "model.gguf").write_text("fake model data")

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_from_url.return_value = model_path
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                mock_manager.download_from_url.assert_called_once_with(
                    url="https://example.com/model.gguf",
                    name="custom_model",
                    force=False
                )

    def test_download_url_with_force(self, mock_config, tmp_path):
        """Test downloading from URL with force flag (line 769)."""
        args = Namespace(
            url="https://example.com/model.gguf",
            name="custom_model",
            force=True
        )

        model_path = tmp_path / "models" / "custom_model"
        model_path.mkdir(parents=True, exist_ok=True)

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_from_url.return_value = model_path
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return success
                assert result == 0
                mock_manager.download_from_url.assert_called_once_with(
                    url="https://example.com/model.gguf",
                    name="custom_model",
                    force=True
                )

    def test_download_error_handling(self, mock_config):
        """Test download error handling (lines 799-807)."""
        args = Namespace(
            url=None,
            huggingface_model="test/model",
            force=False,
            token=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.side_effect = Exception("Download failed")
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should return error code
                assert result == 1

    def test_download_model_without_size_in_info(self, mock_config):
        """Test download when model info doesn't have size_gb (line 796)."""
        args = Namespace(
            url=None,
            huggingface_model="test/model",
            force=False,
            token=None
        )

        with patch('llf.cli.get_config', return_value=mock_config):
            with patch('llf.cli.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.download_model.return_value = None
                # No size_gb in info
                mock_manager.get_model_info.return_value = {
                    'path': '/path/to/model'
                }
                MockModelManager.return_value = mock_manager

                result = download_command(args)

                # Should still return success
                assert result == 0

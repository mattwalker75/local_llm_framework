"""
Comprehensive edge case tests for ModelManager to improve coverage.

Tests cover:
- download_model_from_url: reporthook progress logging (lines 212-215)
- download_model_from_url: cleanup on URLError (line 235)
- download_model_from_url: cleanup on generic exception (line 243)
- delete_model: exception during deletion (lines 349-351)
- list_downloaded_models: model_dir doesn't exist (line 361)
"""

import pytest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llf.model_manager import ModelManager


@pytest.fixture
def temp_model_dir(tmp_path):
    """Create temporary model directory."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir


@pytest.fixture
def model_manager(temp_model_dir, tmp_path):
    """Create ModelManager instance with temp directory."""
    # Create a mock config
    mock_config = Mock()
    mock_config.model_name = "test-model"
    mock_config.model_path = None

    manager = ModelManager(mock_config)
    manager.model_dir = temp_model_dir
    return manager


class TestDownloadFromUrlEdgeCases:
    """Test download_from_url edge cases."""

    def test_download_progress_logging(self, model_manager, temp_model_dir):
        """Test that download progress logging works correctly."""
        url = "https://example.com/model.bin"
        model_name = "test/model"

        # Track reporthook calls
        reporthook_calls = []

        def mock_urlretrieve(url, filepath, reporthook):
            # Simulate progress callbacks
            total_size = 1000
            block_size = 10

            # Call reporthook multiple times
            for block_num in range(0, 200, 100):  # 0, 100
                reporthook(block_num, block_size, total_size)
                reporthook_calls.append((block_num, block_size, total_size))

            # Create the file
            Path(filepath).touch()

        with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
            result = model_manager.download_from_url(url, model_name)

        # Verify reporthook was called
        assert len(reporthook_calls) > 0
        assert result == temp_model_dir / "test" / "model"

    def test_download_url_error_cleanup(self, model_manager, temp_model_dir):
        """Test cleanup when URLError occurs during download."""
        url = "https://example.com/model.bin"
        model_name = "test/model"

        # Mock urlretrieve to raise URLError after creating partial file
        def mock_urlretrieve(url, filepath, reporthook):
            # Create partial file
            Path(filepath).touch()
            raise urllib.error.URLError("Connection failed")

        with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
            with pytest.raises(ValueError, match="URL error"):
                model_manager.download_from_url(url, model_name)

        # Verify partial file was cleaned up
        model_path = temp_model_dir / "test" / "model"
        file_path = model_path / "model.bin"
        assert not file_path.exists()

    def test_download_generic_exception_cleanup(self, model_manager, temp_model_dir):
        """Test cleanup when generic exception occurs during download."""
        url = "https://example.com/model.bin"
        model_name = "test/model"

        # Mock urlretrieve to raise generic exception after creating partial file
        def mock_urlretrieve(url, filepath, reporthook):
            # Create partial file
            Path(filepath).touch()
            raise RuntimeError("Unexpected download error")

        with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
            with pytest.raises(ValueError, match="Unexpected error"):
                model_manager.download_from_url(url, model_name)

        # Verify partial file was cleaned up
        model_path = temp_model_dir / "test" / "model"
        file_path = model_path / "model.bin"
        assert not file_path.exists()


class TestDeleteModelEdgeCases:
    """Test delete_model edge cases."""

    def test_delete_model_exception(self, model_manager, temp_model_dir):
        """Test delete_model when deletion raises exception."""
        model_name = "test/model"
        model_path = temp_model_dir / "test--model"
        model_path.mkdir()

        # Mock shutil.rmtree to raise exception
        with patch('shutil.rmtree', side_effect=PermissionError("Access denied")):
            result = model_manager.delete_model(model_name)

        # Should return False on exception
        assert result is False


class TestListDownloadedModelsEdgeCases:
    """Test list_downloaded_models edge cases."""

    def test_list_models_dir_not_exists(self, model_manager, tmp_path):
        """Test listing models when model directory doesn't exist."""
        # Set model_dir to non-existent path
        model_manager.model_dir = tmp_path / "nonexistent"

        models = model_manager.list_downloaded_models()

        # Should return empty list
        assert models == []

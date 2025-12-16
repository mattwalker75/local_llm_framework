"""
Unit tests for model_manager module.
"""

import pytest
from pathlib import Path
import shutil
from unittest.mock import Mock, patch, MagicMock

from llf.config import Config
from llf.model_manager import ModelManager


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config(temp_dir):
    """Create test configuration."""
    config = Config()
    config.model_dir = temp_dir / "models"
    config.cache_dir = temp_dir / ".cache"
    config.model_name = "test/model"
    return config


@pytest.fixture
def model_manager(config):
    """Create model manager instance."""
    return ModelManager(config)


class TestModelManager:
    """Test ModelManager class."""

    def test_initialization(self, model_manager, config):
        """Test model manager initialization."""
        assert model_manager.config == config
        assert model_manager.model_dir == config.model_dir
        assert model_manager.cache_dir == config.cache_dir
        assert model_manager.model_dir.exists()
        assert model_manager.cache_dir.exists()

    def test_get_model_path_default(self, model_manager, config):
        """Test getting model path with default model."""
        path = model_manager.get_model_path()
        expected = config.model_dir / "test--model"
        assert path == expected

    def test_get_model_path_custom(self, model_manager, config):
        """Test getting model path with custom model name."""
        path = model_manager.get_model_path("custom/model")
        expected = config.model_dir / "custom--model"
        assert path == expected

    def test_get_model_path_special_chars(self, model_manager, config):
        """Test getting model path with special characters in name."""
        path = model_manager.get_model_path("org/model-name")
        expected = config.model_dir / "org--model-name"
        assert path == expected

    def test_is_model_downloaded_false_not_exists(self, model_manager):
        """Test is_model_downloaded when model doesn't exist."""
        assert not model_manager.is_model_downloaded()

    def test_is_model_downloaded_false_missing_config(self, model_manager, config):
        """Test is_model_downloaded when config.json is missing."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        # Create some other file but not config.json
        (model_path / "other.txt").write_text("test")

        assert not model_manager.is_model_downloaded()

    def test_is_model_downloaded_true(self, model_manager):
        """Test is_model_downloaded when model is properly downloaded."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        assert model_manager.is_model_downloaded()

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_success(self, mock_snapshot, model_manager):
        """Test successful model download."""
        model_path = model_manager.get_model_path()

        # Mock download that creates the model structure
        def create_model(*args, **kwargs):
            model_path.mkdir(parents=True, exist_ok=True)
            (model_path / "config.json").write_text("{}")
            return str(model_path)

        mock_snapshot.side_effect = create_model

        result = model_manager.download_model()

        assert result == model_path
        mock_snapshot.assert_called_once()
        call_kwargs = mock_snapshot.call_args.kwargs
        assert call_kwargs['repo_id'] == "test/model"
        assert call_kwargs['local_dir'] == model_path

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_already_downloaded(self, mock_snapshot, model_manager):
        """Test download_model when model already exists."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        result = model_manager.download_model()

        assert result == model_path
        # Should not call snapshot_download if already downloaded
        mock_snapshot.assert_not_called()

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_force(self, mock_snapshot, model_manager):
        """Test download_model with force flag."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        mock_snapshot.return_value = str(model_path)

        result = model_manager.download_model(force=True)

        assert result == model_path
        # Should call snapshot_download even if already downloaded
        mock_snapshot.assert_called_once()

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_with_token(self, mock_snapshot, model_manager):
        """Test download_model with authentication token."""
        model_path = model_manager.get_model_path()

        # Mock download that creates the model structure
        def create_model(*args, **kwargs):
            model_path.mkdir(parents=True, exist_ok=True)
            (model_path / "config.json").write_text("{}")
            return str(model_path)

        mock_snapshot.side_effect = create_model

        result = model_manager.download_model(token="test_token")

        assert result == model_path
        call_kwargs = mock_snapshot.call_args.kwargs
        assert call_kwargs['token'] == "test_token"

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_failure(self, mock_snapshot, model_manager):
        """Test download_model when download fails."""
        from huggingface_hub.utils import HfHubHTTPError

        mock_snapshot.side_effect = HfHubHTTPError("Download failed")

        with pytest.raises(ValueError, match="Failed to download model"):
            model_manager.download_model()

    def test_verify_model_not_exists(self, model_manager):
        """Test verify_model when model doesn't exist."""
        result = model_manager.verify_model()

        assert not result['exists']
        assert not result['has_config']
        assert not result['has_tokenizer']
        assert not result['has_weights']
        assert not result['valid']

    def test_verify_model_minimal(self, model_manager):
        """Test verify_model with minimal model files."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")
        (model_path / "tokenizer.json").write_text("{}")
        (model_path / "model.safetensors").write_text("weights")

        result = model_manager.verify_model()

        assert result['exists']
        assert result['has_config']
        assert result['has_tokenizer']
        assert result['has_weights']
        assert result['valid']

    def test_verify_model_partial(self, model_manager):
        """Test verify_model with incomplete model."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")
        # Missing tokenizer and weights

        result = model_manager.verify_model()

        assert result['exists']
        assert result['has_config']
        assert not result['has_tokenizer']
        assert not result['has_weights']
        assert not result['valid']

    def test_delete_model_success(self, model_manager):
        """Test successful model deletion."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        result = model_manager.delete_model()

        assert result is True
        assert not model_path.exists()

    def test_delete_model_not_exists(self, model_manager):
        """Test deleting non-existent model."""
        result = model_manager.delete_model()

        assert result is False

    def test_list_downloaded_models_empty(self, model_manager):
        """Test listing models when none are downloaded."""
        models = model_manager.list_downloaded_models()

        assert models == []

    def test_list_downloaded_models(self, model_manager, config):
        """Test listing downloaded models."""
        # Create multiple model directories
        (config.model_dir / "org1--model1").mkdir(parents=True)
        (config.model_dir / "org2--model2").mkdir(parents=True)

        models = model_manager.list_downloaded_models()

        assert len(models) == 2
        assert "org1/model1" in models
        assert "org2/model2" in models

    def test_get_model_info_not_downloaded(self, model_manager):
        """Test get_model_info for non-existent model."""
        info = model_manager.get_model_info()

        assert info['name'] == "test/model"
        assert not info['downloaded']
        assert 'size_bytes' not in info

    def test_get_model_info_downloaded(self, model_manager):
        """Test get_model_info for downloaded model."""
        model_path = model_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")
        (model_path / "tokenizer.json").write_text("{}")
        # Create a file with some actual size
        (model_path / "model.safetensors").write_text("w" * 10000)

        info = model_manager.get_model_info()

        assert info['name'] == "test/model"
        assert info['downloaded']
        assert 'size_bytes' in info
        assert 'size_gb' in info
        assert info['size_bytes'] > 0

    def test_get_model_info_custom_model(self, model_manager, config):
        """Test get_model_info for custom model name."""
        custom_path = config.model_dir / "custom--model"
        custom_path.mkdir(parents=True)
        (custom_path / "config.json").write_text("{}")
        (custom_path / "tokenizer.json").write_text("{}")
        (custom_path / "model.safetensors").write_text("weights")

        info = model_manager.get_model_info("custom/model")

        assert info['name'] == "custom/model"
        assert info['downloaded']

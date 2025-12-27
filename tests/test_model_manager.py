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
        # Use a generic exception instead of HfHubHTTPError to avoid API changes
        mock_snapshot.side_effect = Exception("Download failed")

        with pytest.raises(ValueError, match="Unexpected error downloading model"):
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

    def test_is_model_downloaded_gguf_model_with_files(self, model_manager, config):
        """Test GGUF model detection with .gguf files."""
        # Create a GGUF model
        gguf_manager = ModelManager(config)
        gguf_manager.config.model_name = "test/model-GGUF"

        model_path = gguf_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "model.gguf").write_text("gguf content")

        assert gguf_manager.is_model_downloaded()

    def test_is_model_downloaded_gguf_model_no_files(self, model_manager, config):
        """Test GGUF model detection without .gguf files."""
        # Create a GGUF model directory without .gguf files
        gguf_manager = ModelManager(config)
        gguf_manager.config.model_name = "test/model-GGUF"

        model_path = gguf_manager.get_model_path()
        model_path.mkdir(parents=True)
        (model_path / "other.txt").write_text("not a gguf")

        assert not gguf_manager.is_model_downloaded()

    @patch('llf.model_manager.snapshot_download')
    def test_download_model_hfhub_http_error(self, mock_snapshot, model_manager):
        """Test download_model with HfHubHTTPError."""
        from huggingface_hub.errors import HfHubHTTPError

        # Create a mock HfHubHTTPError
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        mock_snapshot.side_effect = HfHubHTTPError("Not found", response=mock_response)

        with pytest.raises(ValueError, match="Failed to download model"):
            model_manager.download_model()

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_success(self, mock_urlretrieve, model_manager):
        """Test successful URL download."""
        url = "https://example.com/model.gguf"
        name = "test-model"

        # Mock successful download
        mock_urlretrieve.return_value = (None, None)

        result = model_manager.download_from_url(url, name)

        assert result == model_manager.model_dir / name
        mock_urlretrieve.assert_called_once()
        # Check file path in call
        call_args = mock_urlretrieve.call_args[0]
        assert call_args[0] == url
        assert "model.gguf" in str(call_args[1])

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_with_query_params(self, mock_urlretrieve, model_manager):
        """Test URL download with query parameters in URL."""
        url = "https://example.com/model.gguf?download=true&token=abc"
        name = "test-model"

        mock_urlretrieve.return_value = (None, None)

        result = model_manager.download_from_url(url, name)

        # Should strip query parameters from filename
        call_args = mock_urlretrieve.call_args[0]
        assert "model.gguf" in str(call_args[1])
        assert "?" not in str(call_args[1])

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_already_exists(self, mock_urlretrieve, model_manager):
        """Test URL download when file already exists."""
        url = "https://example.com/model.gguf"
        name = "test-model"

        # Create existing file
        model_path = model_manager.model_dir / name
        model_path.mkdir(parents=True)
        (model_path / "model.gguf").write_text("existing")

        result = model_manager.download_from_url(url, name)

        # Should not download if exists
        mock_urlretrieve.assert_not_called()
        assert result == model_path

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_force_redownload(self, mock_urlretrieve, model_manager):
        """Test URL download with force flag."""
        url = "https://example.com/model.gguf"
        name = "test-model"

        # Create existing file
        model_path = model_manager.model_dir / name
        model_path.mkdir(parents=True)
        (model_path / "model.gguf").write_text("existing")

        mock_urlretrieve.return_value = (None, None)

        result = model_manager.download_from_url(url, name, force=True)

        # Should download even if exists
        mock_urlretrieve.assert_called_once()
        assert result == model_path

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_http_error(self, mock_urlretrieve, model_manager):
        """Test URL download with HTTP error."""
        import urllib.error

        url = "https://example.com/model.gguf"
        name = "test-model"

        # Mock HTTP error
        mock_urlretrieve.side_effect = urllib.error.HTTPError(
            url, 404, "Not Found", {}, None
        )

        with pytest.raises(ValueError, match="HTTP error downloading"):
            model_manager.download_from_url(url, name)

        # Verify partial file is cleaned up
        file_path = model_manager.model_dir / name / "model.gguf"
        assert not file_path.exists()

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_network_error(self, mock_urlretrieve, model_manager):
        """Test URL download with network error."""
        import urllib.error

        url = "https://example.com/model.gguf"
        name = "test-model"

        # Mock URL error
        mock_urlretrieve.side_effect = urllib.error.URLError("Network unreachable")

        with pytest.raises(ValueError, match="URL error downloading"):
            model_manager.download_from_url(url, name)

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_unexpected_error(self, mock_urlretrieve, model_manager):
        """Test URL download with unexpected error."""
        url = "https://example.com/model.gguf"
        name = "test-model"

        # Mock unexpected error
        mock_urlretrieve.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(ValueError, match="Unexpected error downloading"):
            model_manager.download_from_url(url, name)

    @patch('urllib.request.urlretrieve')
    def test_download_from_url_cleanup_on_error(self, mock_urlretrieve, model_manager):
        """Test that partial downloads are cleaned up on error."""
        import urllib.error

        url = "https://example.com/model.gguf"
        name = "test-model"

        # Create partial download
        model_path = model_manager.model_dir / name
        model_path.mkdir(parents=True)
        file_path = model_path / "model.gguf"
        file_path.write_text("partial")

        # Mock error during download
        mock_urlretrieve.side_effect = urllib.error.HTTPError(
            url, 500, "Server Error", {}, None
        )

        with pytest.raises(ValueError):
            model_manager.download_from_url(url, name, force=True)

        # Verify file was cleaned up
        assert not file_path.exists()

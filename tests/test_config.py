"""
Unit tests for config module.
"""

import pytest
from pathlib import Path
import json

from llf.config import Config, get_config


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


class TestConfig:
    """Test Config class."""

    def test_default_initialization(self):
        """Test config initialization with defaults."""
        config = Config()

        assert config.model_name == Config.DEFAULT_MODEL_NAME
        assert config.model_alias == Config.DEFAULT_MODEL_ALIAS
        assert config.gguf_file == Config.DEFAULT_GGUF_FILE
        assert config.model_dir == Config.DEFAULT_MODEL_DIR
        assert config.cache_dir == Config.DEFAULT_CACHE_DIR
        assert config.llama_server_path == Config.DEFAULT_LLAMA_SERVER_PATH
        assert config.server_wrapper_script == Config.SERVER_WRAPPER_SCRIPT
        assert config.inference_params == Config.DEFAULT_INFERENCE_PARAMS
        assert config.server_host == Config.SERVER_HOST
        assert config.server_port == Config.SERVER_PORT

    def test_directories_created(self):
        """Test that directories are created on init."""
        config = Config()

        assert config.model_dir.exists()
        assert config.cache_dir.exists()

    def test_load_from_file(self, temp_dir):
        """Test loading config from file."""
        config_data = {
            'model_name': 'custom/model',
            'model_alias': 'custom',
            'gguf_file': 'custom-model.gguf',
            'model_dir': str(temp_dir / 'custom_models'),
            'cache_dir': str(temp_dir / 'custom_cache'),
            'llama_server_path': str(temp_dir / 'custom_llama_server'),
            'inference_params': {
                'temperature': 0.5,
                'max_tokens': 1000
            },
            'server_host': '0.0.0.0',
            'server_port': 9000,
            'log_level': 'DEBUG'
        }

        config_file = temp_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.model_name == 'custom/model'
        assert config.model_alias == 'custom'
        assert config.gguf_file == 'custom-model.gguf'
        assert config.model_dir == temp_dir / 'custom_models'
        assert config.cache_dir == temp_dir / 'custom_cache'
        assert config.llama_server_path == temp_dir / 'custom_llama_server'
        assert config.inference_params['temperature'] == 0.5
        assert config.inference_params['max_tokens'] == 1000
        assert config.server_host == '0.0.0.0'
        assert config.server_port == 9000
        assert config.log_level == 'DEBUG'

    def test_load_partial_config(self, temp_dir):
        """Test loading partial config (merges with defaults)."""
        config_data = {
            'model_name': 'partial/model',
            'server_port': 7000
        }

        config_file = temp_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        # Should have custom values
        assert config.model_name == 'partial/model'
        assert config.server_port == 7000

        # Should have defaults for others
        assert config.model_alias == Config.DEFAULT_MODEL_ALIAS
        assert config.server_host == Config.SERVER_HOST

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading from non-existent file."""
        config_file = temp_dir / 'nonexistent.json'

        # Should use defaults when file doesn't exist
        config = Config(config_file)

        assert config.model_name == Config.DEFAULT_MODEL_NAME

    def test_load_invalid_json(self, temp_dir):
        """Test loading invalid JSON file."""
        config_file = temp_dir / 'invalid.json'
        config_file.write_text("not valid json {")

        with pytest.raises(ValueError, match="Failed to load configuration"):
            Config(config_file)

    def test_get_server_url(self):
        """Test getting server URL."""
        config = Config()
        url = config.get_server_url()

        assert url == f"http://{config.server_host}:{config.server_port}"

    def test_get_vllm_url_deprecated(self):
        """Test deprecated get_vllm_url method."""
        config = Config()
        url = config.get_vllm_url()

        # Should return same as get_server_url()
        assert url == config.get_server_url()
        assert url == f"http://{config.server_host}:{config.server_port}"

    def test_get_openai_api_base(self):
        """Test getting OpenAI API base URL."""
        config = Config()
        base = config.get_openai_api_base()

        assert base == f"http://{config.server_host}:{config.server_port}/v1"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        assert config_dict['model_name'] == config.model_name
        assert config_dict['model_alias'] == config.model_alias
        assert config_dict['gguf_file'] == config.gguf_file
        assert config_dict['model_dir'] == str(config.model_dir)
        assert config_dict['cache_dir'] == str(config.cache_dir)
        assert config_dict['llama_server_path'] == str(config.llama_server_path)
        assert config_dict['inference_params'] == config.inference_params
        assert config_dict['server_host'] == config.server_host
        assert config_dict['server_port'] == config.server_port

    def test_save_to_file(self, temp_dir):
        """Test saving config to file."""
        config = Config()
        config.model_name = "saved/model"
        config.server_port = 8888

        save_file = temp_dir / 'saved_config.json'
        config.save_to_file(save_file)

        assert save_file.exists()

        # Load and verify
        with open(save_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data['model_name'] == "saved/model"
        assert loaded_data['server_port'] == 8888

    def test_save_creates_parent_dirs(self, temp_dir):
        """Test that save_to_file creates parent directories."""
        config = Config()
        save_file = temp_dir / 'subdir' / 'config.json'

        config.save_to_file(save_file)

        assert save_file.exists()
        assert save_file.parent.exists()

    def test_inference_params_independent(self):
        """Test that inference params are independent copies."""
        config1 = Config()
        config2 = Config()

        config1.inference_params['temperature'] = 0.1

        # Should not affect config2
        assert config2.inference_params['temperature'] == Config.DEFAULT_INFERENCE_PARAMS['temperature']


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_singleton(self):
        """Test that get_config returns singleton."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_with_file(self, temp_dir):
        """Test get_config with config file."""
        config_data = {'model_name': 'file/model'}
        config_file = temp_dir / 'test_config.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = get_config(config_file)

        assert config.model_name == 'file/model'

    def test_get_config_creates_new_with_file(self, temp_dir):
        """Test that providing a file creates new config."""
        # Get default config
        config1 = get_config()
        original_name = config1.model_name

        # Get config with file
        config_data = {'model_name': 'different/model'}
        config_file = temp_dir / 'different.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config2 = get_config(config_file)

        # Should be different from original
        assert config2.model_name == 'different/model'
        assert config2.model_name != original_name

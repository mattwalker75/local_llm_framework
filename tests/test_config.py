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
        """Test config initialization with defaults (when no config.json exists)."""
        # Temporarily rename config.json if it exists so we can test defaults
        config_backup = None
        if Config.DEFAULT_CONFIG_FILE.exists():
            config_backup = Config.DEFAULT_CONFIG_FILE.with_suffix('.json.test_backup')
            Config.DEFAULT_CONFIG_FILE.rename(config_backup)

        try:
            config = Config()

            assert config.model_name == Config.DEFAULT_MODEL_NAME
            assert config.gguf_file == Config.DEFAULT_GGUF_FILE
            assert config.model_dir == Config.DEFAULT_MODEL_DIR
            assert config.cache_dir == Config.DEFAULT_CACHE_DIR
            assert config.llama_server_path == Config.DEFAULT_LLAMA_SERVER_PATH
            assert config.server_wrapper_script == Config.SERVER_WRAPPER_SCRIPT
            assert config.inference_params == Config.DEFAULT_INFERENCE_PARAMS
            assert config.server_host == Config.SERVER_HOST
            assert config.server_port == Config.SERVER_PORT
            assert config.healthcheck_interval == Config.HEALTHCHECK_INTERVAL
        finally:
            # Restore config.json if it was backed up
            if config_backup and config_backup.exists():
                config_backup.rename(Config.DEFAULT_CONFIG_FILE)

    def test_directories_created(self):
        """Test that directories are created on init."""
        config = Config()

        assert config.model_dir.exists()
        assert config.cache_dir.exists()

    def test_load_from_file(self, temp_dir):
        """Test loading config from file."""
        config_data = {
            'model_name': 'custom/model',
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
            'healthcheck_interval': 1.5,
            'log_level': 'DEBUG'
        }

        config_file = temp_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.model_name == 'custom/model'
        assert config.gguf_file == 'custom-model.gguf'
        assert config.model_dir == temp_dir / 'custom_models'
        assert config.cache_dir == temp_dir / 'custom_cache'
        assert config.llama_server_path == temp_dir / 'custom_llama_server'
        assert config.inference_params['temperature'] == 0.5
        assert config.inference_params['max_tokens'] == 1000
        assert config.server_host == '0.0.0.0'
        assert config.server_port == 9000
        assert config.healthcheck_interval == 1.5
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
        """Test getting OpenAI API base URL (local server)."""
        config = Config()
        base = config.get_openai_api_base()

        assert base == f"http://{config.server_host}:{config.server_port}/v1"

    def test_get_openai_api_base_external(self, temp_dir):
        """Test getting OpenAI API base URL with external API configured."""
        config_data = {
            'api_base_url': 'https://api.openai.com/v1'
        }

        config_file = temp_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)
        base = config.get_openai_api_base()

        # Should use configured api_base_url instead of local server
        assert base == 'https://api.openai.com/v1'

    def test_api_key_configuration(self, temp_dir):
        """Test API key configuration for external services."""
        config_data = {
            'api_key': 'sk-test-key-12345'
        }

        config_file = temp_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.api_key == 'sk-test-key-12345'

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        config_dict = config.to_dict()

        # Test nested structure - server-side settings
        assert 'local_llm_server' in config_dict
        assert config_dict['local_llm_server']['llama_server_path'] == str(config.llama_server_path)
        assert config_dict['local_llm_server']['server_host'] == config.server_host
        assert config_dict['local_llm_server']['server_port'] == config.server_port
        assert config_dict['local_llm_server']['gguf_file'] == config.gguf_file

        # Test nested structure - client-side settings
        assert 'llm_endpoint' in config_dict
        assert config_dict['llm_endpoint']['api_base_url'] == config.api_base_url
        assert config_dict['llm_endpoint']['api_key'] == config.api_key
        assert config_dict['llm_endpoint']['model_name'] == config.model_name

        # Test top-level settings
        assert config_dict['model_dir'] == str(config.model_dir)
        assert config_dict['cache_dir'] == str(config.cache_dir)
        assert config_dict['inference_params'] == config.inference_params

    def test_save_to_file(self, temp_dir):
        """Test saving config to file."""
        config = Config()
        config.model_name = "saved/model"
        config.server_port = 8888

        save_file = temp_dir / 'saved_config.json'
        config.save_to_file(save_file)

        assert save_file.exists()

        # Load and verify - should use nested structure
        with open(save_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data['llm_endpoint']['model_name'] == "saved/model"
        assert loaded_data['local_llm_server']['server_port'] == 8888

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

    def test_server_params_default(self):
        """Test that server_params defaults to empty dict."""
        config = Config()
        assert config.server_params == {}

    def test_server_params_loading(self, temp_dir):
        """Test loading server_params from config file."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_params': {
                    'ctx-size': 8192,
                    'n-gpu-layers': 35,
                    'threads': 8
                }
            }
        }
        config_file = temp_dir / 'config_with_params.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.server_params == {
            'ctx-size': 8192,
            'n-gpu-layers': 35,
            'threads': 8
        }

    def test_server_params_optional(self, temp_dir):
        """Test that server_params is optional in config."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_host': '127.0.0.1',
                'server_port': 8000
                # No server_params field
            }
        }
        config_file = temp_dir / 'config_no_params.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        # Should default to empty dict
        assert config.server_params == {}

    def test_server_params_empty(self, temp_dir):
        """Test that empty server_params is handled correctly."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_params': {}
            }
        }
        config_file = temp_dir / 'config_empty_params.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.server_params == {}

    def test_server_params_in_to_dict(self, temp_dir):
        """Test that server_params is included in to_dict when not empty."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_params': {
                    'ctx-size': 4096
                }
            }
        }
        config_file = temp_dir / 'config_params_dict.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)
        config_dict = config.to_dict()

        assert 'server_params' in config_dict['local_llm_server']
        assert config_dict['local_llm_server']['server_params'] == {'ctx-size': 4096}

    def test_server_params_not_in_to_dict_when_empty(self):
        """Test that server_params is not in to_dict when empty."""
        config = Config()
        config_dict = config.to_dict()

        # Empty server_params should not be included
        assert 'server_params' not in config_dict['local_llm_server']

    def test_healthcheck_interval_loading(self, temp_dir):
        """Test loading healthcheck_interval from config file."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_host': '127.0.0.1',
                'server_port': 8000,
                'healthcheck_interval': 1.0
            }
        }
        config_file = temp_dir / 'config_healthcheck.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        assert config.healthcheck_interval == 1.0

    def test_healthcheck_interval_default(self, temp_dir):
        """Test that healthcheck_interval defaults to 2.0 when not specified."""
        config_data = {
            'local_llm_server': {
                'llama_server_path': str(temp_dir / 'llama-server'),
                'server_host': '127.0.0.1',
                'server_port': 8000
                # No healthcheck_interval specified
            }
        }
        config_file = temp_dir / 'config_no_healthcheck.json'

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(config_file)

        # Should use default value
        assert config.healthcheck_interval == Config.HEALTHCHECK_INTERVAL
        assert config.healthcheck_interval == 2.0

    def test_backup_config_success(self, temp_dir):
        """Test successful config backup."""
        # Create a config file
        config_file = temp_dir / "config.json"
        config_data = {"model_name": "test-model", "log_level": "INFO"}
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Create backup directory
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        config = Config(config_file)
        config.CONFIG_BACKUPS_DIR = backup_dir
        backup_path = config.backup_config(config_file)

        # Verify backup was created
        assert backup_path.exists()
        assert backup_path.parent == backup_dir
        assert backup_path.stem.startswith("config_")
        assert backup_path.suffix == ".json"

        # Verify backup content matches original file
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        with open(config_file, 'r') as f:
            original_data = json.load(f)
        assert backup_data == original_data

    def test_backup_config_file_not_found(self, temp_dir):
        """Test backup fails when config file doesn't exist."""
        config_file = temp_dir / "configs" / "nonexistent.json"
        config = Config()

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            config.backup_config(config_file)

    def test_backup_config_custom_file(self, temp_dir):
        """Test backup of custom config file."""
        custom_file = temp_dir / "custom_config.json"
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {"custom": "data"}
        with open(custom_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.CONFIG_BACKUPS_DIR = temp_dir / "backups"
        backup_path = config.backup_config(custom_file)

        # Verify backup was created with correct name
        assert backup_path.exists()
        assert backup_path.stem.startswith("custom_config_")
        assert backup_path.suffix == ".json"

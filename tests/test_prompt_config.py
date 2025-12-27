"""
Tests for prompt configuration management.
"""

import json
import pytest
from pathlib import Path

from llf.prompt_config import PromptConfig, get_prompt_config


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


class TestPromptConfig:
    """Test PromptConfig class."""

    def test_default_initialization(self):
        """Test default initialization."""
        config = PromptConfig()
        assert config.system_prompt is None
        assert config.master_prompt is None
        assert config.assistant_prompt is None
        assert config.conversation_format == "standard"
        assert config.prefix_messages == []
        assert config.suffix_messages == []

    def test_build_messages_simple(self):
        """Test building messages with simple user message."""
        config = PromptConfig()
        messages = config.build_messages("Hello, how are you?")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, how are you?"

    def test_build_messages_with_system_prompt(self):
        """Test building messages with system prompt."""
        config = PromptConfig()
        config.system_prompt = "You are a helpful assistant."

        messages = config.build_messages("Hello!")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello!"

    def test_build_messages_with_all_prompts(self):
        """Test building messages with all prompt types."""
        config = PromptConfig()
        config.system_prompt = "You are a helpful assistant."
        config.master_prompt = "Always be concise."
        config.assistant_prompt = "I'm ready to help!"

        messages = config.build_messages("What is 2+2?")

        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."
        assert messages[1]["role"] == "system"
        assert messages[1]["content"] == "Always be concise."
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "What is 2+2?"
        assert messages[3]["role"] == "assistant"
        assert messages[3]["content"] == "I'm ready to help!"

    def test_build_messages_with_conversation_history(self):
        """Test building messages with conversation history."""
        config = PromptConfig()
        config.system_prompt = "You are helpful."

        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ]

        messages = config.build_messages("How are you?", conversation_history=history)

        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hi"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Hello!"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "How are you?"

    def test_build_messages_with_prefix_and_suffix(self):
        """Test building messages with prefix and suffix messages."""
        config = PromptConfig()
        config.prefix_messages = [{"role": "system", "content": "Prefix instruction"}]
        config.suffix_messages = [{"role": "system", "content": "Suffix instruction"}]

        messages = config.build_messages("Test")

        assert len(messages) == 3
        assert messages[0]["content"] == "Prefix instruction"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test"
        assert messages[2]["content"] == "Suffix instruction"

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from file."""
        config_data = {
            "system_prompt": "Test system prompt",
            "master_prompt": "Test master prompt",
            "assistant_prompt": "Test assistant prompt",
            "conversation_format": "structured",
            "prefix_messages": [{"role": "system", "content": "Prefix"}],
            "suffix_messages": [{"role": "system", "content": "Suffix"}]
        }

        config_file = tmp_path / "test_prompt_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = PromptConfig(config_file)

        assert config.system_prompt == "Test system prompt"
        assert config.master_prompt == "Test master prompt"
        assert config.assistant_prompt == "Test assistant prompt"
        assert config.conversation_format == "structured"
        assert len(config.prefix_messages) == 1
        assert len(config.suffix_messages) == 1

    def test_save_to_file(self, tmp_path):
        """Test saving configuration to file."""
        config = PromptConfig()
        config.system_prompt = "Save test"
        config.master_prompt = "Master"

        config_file = tmp_path / "saved_config.json"
        config.save_to_file(config_file)

        assert config_file.exists()

        # Load and verify
        with open(config_file, 'r') as f:
            data = json.load(f)

        assert data["system_prompt"] == "Save test"
        assert data["master_prompt"] == "Master"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = PromptConfig()
        config.system_prompt = "Test"
        config.prefix_messages = [{"role": "system", "content": "Pre"}]

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["system_prompt"] == "Test"
        assert len(data["prefix_messages"]) == 1

    def test_load_from_file_with_custom_format(self, temp_dir):
        """Test loading config with custom_format field."""
        config_file = temp_dir / "config_prompt.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            "system_prompt": "Test prompt",
            "custom_format": "custom value"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        config = PromptConfig(config_file)

        assert config.system_prompt == "Test prompt"
        assert config.custom_format == "custom value"



class TestGetPromptConfig:
    """Test get_prompt_config singleton function."""

    def test_get_prompt_config_singleton(self):
        """Test that get_prompt_config returns same instance."""
        # Force reload to ensure clean state
        config1 = get_prompt_config(force_reload=True)
        config2 = get_prompt_config()

        assert config1 is config2

    def test_get_prompt_config_force_reload(self):
        """Test force reload creates new instance."""
        config1 = get_prompt_config(force_reload=True)
        config2 = get_prompt_config(force_reload=True)

        # Different instances due to force reload
        assert config1 is not config2

    def test_backup_config_success(self, temp_dir):
        """Test successful prompt config backup."""
        # Create a config file
        config_file = temp_dir / "config_prompt.json"
        config_data = {
            "system_prompt": "Test system prompt",
            "conversation_format": "standard"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Create backup directory
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        config = PromptConfig(config_file)
        config.CONFIG_BACKUPS_DIR = backup_dir
        backup_path = config.backup_config(config_file)

        # Verify backup was created
        assert backup_path.exists()
        assert backup_path.parent == backup_dir
        assert backup_path.stem.startswith("config_prompt_")
        assert backup_path.suffix == ".json"

        # Verify backup content matches original file
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        with open(config_file, 'r') as f:
            original_data = json.load(f)
        assert backup_data == original_data

    def test_backup_config_file_not_found(self, temp_dir):
        """Test backup fails when config file doesn't exist."""
        config_file = temp_dir / "nonexistent.json"
        config = PromptConfig()

        with pytest.raises(FileNotFoundError, match="Prompt config file not found"):
            config.backup_config(config_file)

    def test_backup_config_custom_file(self, temp_dir):
        """Test backup of custom prompt config file."""
        custom_file = temp_dir / "custom_prompt.json"
        custom_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {"system_prompt": "Custom prompt"}
        with open(custom_file, 'w') as f:
            json.dump(config_data, f)

        config = PromptConfig()
        config.CONFIG_BACKUPS_DIR = temp_dir / "backups"
        backup_path = config.backup_config(custom_file)

        # Verify backup was created with correct name
        assert backup_path.exists()
        assert backup_path.stem.startswith("custom_prompt_")
        assert backup_path.suffix == ".json"

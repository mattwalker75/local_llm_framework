"""
Prompt Configuration Management for LLM Framework.

This module handles loading and managing prompt configurations that control
how prompts are structured and formatted when sent to LLMs.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class PromptConfig:
    """
    Manage prompt configuration for LLM interactions.

    Prompt configurations define how user messages are structured and formatted
    when sent to the LLM, including system prompts, conversation formatting,
    and additional context that should be included with every request.
    """

    # Default configuration file path
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    CONFIGS_DIR: Path = PROJECT_ROOT / "configs"
    DEFAULT_CONFIG_FILE: Path = CONFIGS_DIR / "config_prompt.json"
    CONFIG_BACKUPS_DIR: Path = CONFIGS_DIR / "backups"

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize prompt configuration.

        Args:
            config_file: Optional path to JSON prompt configuration file.
                        If None, automatically looks for config_prompt.json in project root.
                        If that doesn't exist, uses minimal defaults.
        """
        # Default values - minimal configuration
        self.system_prompt: Optional[str] = None
        self.master_prompt: Optional[str] = None
        self.assistant_prompt: Optional[str] = None
        self.conversation_format: str = "standard"  # standard, chat, or custom
        self.prefix_messages: List[Dict[str, str]] = []  # Messages to prepend to every conversation
        self.suffix_messages: List[Dict[str, str]] = []  # Messages to append after user message
        self.custom_format: Optional[Dict[str, Any]] = None  # Custom formatting rules

        # Determine which config file to use
        config_to_load = None
        if config_file is not None:
            # Explicit config file provided
            config_to_load = config_file
        elif self.DEFAULT_CONFIG_FILE.exists():
            # Use default config_prompt.json if it exists
            config_to_load = self.DEFAULT_CONFIG_FILE

        # Load from config file if available
        if config_to_load and config_to_load.exists():
            self._load_from_file(config_to_load)

    def _load_from_file(self, config_file: Path) -> None:
        """
        Load prompt configuration from JSON file.

        Args:
            config_file: Path to JSON prompt configuration file.
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # Load system prompt (high-level instructions for the LLM)
            if 'system_prompt' in config_data:
                self.system_prompt = config_data['system_prompt']

            # Load master prompt (overarching context/guidelines)
            if 'master_prompt' in config_data:
                self.master_prompt = config_data['master_prompt']

            # Load assistant prompt (assistant's persona/behavior)
            if 'assistant_prompt' in config_data:
                self.assistant_prompt = config_data['assistant_prompt']

            # Load conversation format
            if 'conversation_format' in config_data:
                self.conversation_format = config_data['conversation_format']

            # Load prefix messages (added before user message)
            if 'prefix_messages' in config_data:
                self.prefix_messages = config_data['prefix_messages']

            # Load suffix messages (added after user message)
            if 'suffix_messages' in config_data:
                self.suffix_messages = config_data['suffix_messages']

            # Load custom format rules
            if 'custom_format' in config_data:
                self.custom_format = config_data['custom_format']

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in prompt config file {config_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading prompt config from {config_file}: {e}")

    def build_messages(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        Build the complete message list to send to the LLM.

        This method constructs the full conversation including system prompts,
        conversation history, prefix/suffix messages, and the user's message.

        Args:
            user_message: The user's current message
            conversation_history: Optional list of previous messages in the conversation

        Returns:
            List of message dictionaries in OpenAI chat format
        """
        messages = []

        # Add system prompt if configured
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add master prompt as system message if configured
        if self.master_prompt:
            messages.append({
                "role": "system",
                "content": self.master_prompt
            })

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add prefix messages (injected before user message)
        if self.prefix_messages:
            messages.extend(self.prefix_messages)

        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Add suffix messages (injected after user message)
        if self.suffix_messages:
            messages.extend(self.suffix_messages)

        # Add assistant prompt as assistant message if configured
        # This primes the assistant to respond in a certain way
        if self.assistant_prompt:
            messages.append({
                "role": "assistant",
                "content": self.assistant_prompt
            })

        return messages

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert prompt configuration to dictionary.

        Returns:
            Dictionary representation of the prompt configuration.
        """
        return {
            "system_prompt": self.system_prompt,
            "master_prompt": self.master_prompt,
            "assistant_prompt": self.assistant_prompt,
            "conversation_format": self.conversation_format,
            "prefix_messages": self.prefix_messages,
            "suffix_messages": self.suffix_messages,
            "custom_format": self.custom_format,
        }

    def backup_config(self, config_file: Optional[Path] = None) -> Path:
        """
        Create a backup of the prompt configuration file with pretty formatting.

        Args:
            config_file: Path to config file to backup. If None, uses DEFAULT_CONFIG_FILE.

        Returns:
            Path to the backup file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
        """
        from datetime import datetime

        if config_file is None:
            config_file = self.DEFAULT_CONFIG_FILE

        if not config_file.exists():
            raise FileNotFoundError(f"Prompt config file not found: {config_file}")

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_file.stem}_{timestamp}{config_file.suffix}"
        backup_path = self.CONFIG_BACKUPS_DIR / backup_name

        # Ensure backup directory exists
        self.CONFIG_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        # Load JSON and save with pretty formatting (indent=2)
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        with open(backup_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        return backup_path

    def save_to_file(self, config_file: Path) -> None:
        """
        Save prompt configuration to JSON file.

        Args:
            config_file: Path to save the prompt configuration.
        """
        # Create parent directories if they don't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Singleton instance
_prompt_config_instance: Optional[PromptConfig] = None


def get_prompt_config(config_file: Optional[Path] = None, force_reload: bool = False) -> PromptConfig:
    """
    Get the global PromptConfig instance (singleton pattern).

    Args:
        config_file: Optional path to prompt configuration file.
        force_reload: If True, force reload the configuration even if already loaded.

    Returns:
        Global PromptConfig instance.
    """
    global _prompt_config_instance

    if _prompt_config_instance is None or force_reload:
        _prompt_config_instance = PromptConfig(config_file)

    return _prompt_config_instance

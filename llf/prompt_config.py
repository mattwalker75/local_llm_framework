"""
Prompt Configuration Management for LLM Framework.

This module handles loading and managing prompt configurations that control
how prompts are structured and formatted when sent to LLMs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


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

        # RAG retriever (lazy loaded when needed)
        self._rag_retriever = None

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

    def _init_rag_retriever(self):
        """Lazy initialization of RAG retriever."""
        if self._rag_retriever is not None:
            return

        try:
            from llf.rag_retriever import RAGRetriever
            self._rag_retriever = RAGRetriever()
            logger.info("RAG retriever initialized successfully")
        except ImportError as e:
            logger.warning(f"RAG dependencies not available: {e}")
            self._rag_retriever = None
        except Exception as e:
            logger.warning(f"Failed to initialize RAG retriever: {e}")
            self._rag_retriever = None

    def _extract_user_message(self, user_message: Optional[str], conversation_history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        """
        Extract the latest user message for RAG querying.

        Args:
            user_message: Direct user message parameter
            conversation_history: Conversation history list

        Returns:
            User message string, or None if not found
        """
        if user_message:
            return user_message
        elif conversation_history:
            # Get the last user message from history
            for msg in reversed(conversation_history):
                if msg.get('role') == 'user':
                    return msg.get('content', '')
        return None

    def _build_system_prompt_with_rag(self, rag_context: Optional[str]) -> Optional[str]:
        """
        Construct the final system prompt, optionally including RAG context.

        Args:
            rag_context: Retrieved context from vector stores (None if no stores attached)

        Returns:
            Final system prompt string, or None if no system prompt needed
        """
        user_system_prompt = self.system_prompt  # From config_prompt.json

        # Case 1: No RAG context - return user's prompt as-is
        if not rag_context:
            return user_system_prompt

        # Case 2: RAG context exists - build RAG section
        rag_section = f"""---

# Knowledge Base Context

The following information has been retrieved from attached knowledge bases and may be relevant to the user's question:

{rag_context}

# RAG Instructions

- Use the context above when it's relevant to the user's question
- Cite specific information from the context when applicable
- If the context doesn't contain relevant information, rely on your general knowledge
"""

        # Case 2a: User has system prompt - append RAG
        if user_system_prompt:
            return f"{user_system_prompt}\n\n{rag_section}"

        # Case 2b: No user system prompt - create RAG-only prompt
        else:
            return f"""You have access to a knowledge base with relevant information. Use it to answer questions accurately.

{rag_section}"""

    def build_messages(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        Build the complete message list to send to the LLM.

        This method constructs the full conversation including system prompts,
        conversation history, prefix/suffix messages, RAG context (if applicable),
        and the user's message.

        Args:
            user_message: The user's current message
            conversation_history: Optional list of previous messages in the conversation

        Returns:
            List of message dictionaries in OpenAI chat format
        """
        messages = []

        # Step 1: Determine if we need RAG and retrieve context
        user_message_text = self._extract_user_message(user_message, conversation_history)
        rag_context = None

        if user_message_text:
            # Lazy load RAG retriever only if needed
            self._init_rag_retriever()

            # Check if any stores are attached and query them
            if self._rag_retriever and self._rag_retriever.has_attached_stores():
                try:
                    rag_context = self._rag_retriever.query_all_stores(user_message_text)
                    if rag_context:
                        logger.debug(f"Retrieved RAG context: {len(rag_context)} chars")
                except Exception as e:
                    logger.error(f"Error querying RAG stores: {e}")
                    rag_context = None

        # Step 2: Build system prompt (with or without RAG)
        final_system_prompt = self._build_system_prompt_with_rag(rag_context)

        if final_system_prompt:
            messages.append({
                "role": "system",
                "content": final_system_prompt
            })

        # Step 3: Add master prompt as system message if configured
        if self.master_prompt:
            messages.append({
                "role": "system",
                "content": self.master_prompt
            })

        # Step 4: Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Step 5: Add prefix messages (injected before user message)
        if self.prefix_messages:
            messages.extend(self.prefix_messages)

        # Step 6: Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Step 7: Add suffix messages (injected after user message)
        if self.suffix_messages:
            messages.extend(self.suffix_messages)

        # Step 8: Add assistant prompt as assistant message if configured
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

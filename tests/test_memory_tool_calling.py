"""
Test memory tool calling integration with LLMRuntime.

This test verifies that the LLM can actually execute memory tools through
the chat interface.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from llf.llm_runtime import LLMRuntime
from llf.config import Config
from llf.model_manager import ModelManager
from llf.prompt_config import PromptConfig
from llf.memory_manager import MemoryManager


class TestToolCallingIntegration:
    """Test that tool calling works end-to-end in LLMRuntime."""

    def test_chat_gets_memory_tools(self, tmp_path):
        """Test that chat method retrieves memory tools from prompt_config."""
        # Setup memory
        memory_dir = tmp_path / "memory" / "test"
        memory_dir.mkdir(parents=True)

        registry_data = {
            "memories": [
                {"name": "test", "enabled": True, "directory": "test"}
            ]
        }

        registry_path = tmp_path / "memory" / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        # Setup config
        config_file = tmp_path / "config_prompt.json"
        config_file.write_text('{"system_prompt": "Test"}')

        # Create prompt config with memory
        prompt_config = PromptConfig(config_file=config_file)
        prompt_config._memory_manager = MemoryManager(registry_path=registry_path)
        prompt_config._memory_manager.project_root = tmp_path

        # Verify tools are available
        tools = prompt_config.get_memory_tools()
        assert tools is not None
        assert len(tools) == 6

        memory_manager = prompt_config.get_memory_manager()
        assert memory_manager is not None

    @patch('llf.llm_runtime.LLMRuntime._ensure_server_ready')
    def test_chat_handles_tool_calls(self, mock_ensure_server, tmp_path):
        """Test that chat method can handle tool call responses from LLM."""
        # Setup memory
        memory_dir = tmp_path / "memory" / "test"
        memory_dir.mkdir(parents=True)

        registry_data = {
            "memories": [
                {"name": "test", "enabled": True, "directory": "test"}
            ]
        }

        registry_path = tmp_path / "memory" / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        # Setup config
        config_file = tmp_path / "config_prompt.json"
        config_file.write_text('{"system_prompt": "Test"}')

        # Create mock runtime
        config = Config()
        model_manager = Mock(spec=ModelManager)
        prompt_config = PromptConfig(config_file=config_file)
        prompt_config._memory_manager = MemoryManager(registry_path=registry_path)
        prompt_config._memory_manager.project_root = tmp_path

        runtime = LLMRuntime(config, model_manager, prompt_config)

        # Mock the client to simulate tool calling
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "add_memory"
        mock_tool_call.function.arguments = json.dumps({
            "content": "Test memory",
            "memory_type": "note",
            "tags": ["test"],
            "importance": 0.5
        })
        mock_response_1.choices[0].message.content = None
        mock_response_1.choices[0].message.tool_calls = [mock_tool_call]

        # Second response after tool execution
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = "Memory added successfully!"
        mock_response_2.choices[0].message.tool_calls = None

        runtime.client = MagicMock()
        runtime.client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

        # Execute chat
        result = runtime.chat(
            messages=[{"role": "user", "content": "Remember that I like Python"}],
            stream=False
        )

        # Verify tool was called and final response returned
        assert result == "Memory added successfully!"
        assert runtime.client.chat.completions.create.call_count == 2

    def test_chat_no_tools_when_memory_disabled(self, tmp_path):
        """Test that tools are not passed when memory is disabled."""
        # Setup memory disabled
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True)

        registry_data = {
            "memories": [
                {"name": "test", "enabled": False, "directory": "test"}
            ]
        }

        registry_path = tmp_path / "memory" / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        # Setup config
        config_file = tmp_path / "config_prompt.json"
        config_file.write_text('{"system_prompt": "Test"}')

        prompt_config = PromptConfig(config_file=config_file)
        prompt_config._memory_manager = MemoryManager(registry_path=registry_path)

        # Verify tools are NOT available
        tools = prompt_config.get_memory_tools()
        assert tools is None

        memory_manager = prompt_config.get_memory_manager()
        assert memory_manager is None

    def test_execute_memory_tool_from_runtime(self, tmp_path):
        """Test that execute_memory_tool works when called from runtime."""
        from llf.memory_tools import execute_memory_tool

        # Setup memory
        memory_dir = tmp_path / "memory" / "test"
        memory_dir.mkdir(parents=True)

        registry_data = {
            "memories": [
                {"name": "test", "enabled": True, "directory": "test"}
            ]
        }

        registry_path = tmp_path / "memory" / "memory_registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        manager = MemoryManager(registry_path=registry_path)
        manager.project_root = tmp_path

        # Execute add_memory tool
        result = execute_memory_tool(
            "add_memory",
            {
                "content": "Python is my favorite language",
                "memory_type": "preference",
                "tags": ["programming"],
                "importance": 0.9
            },
            manager
        )

        assert result["success"] is True
        assert "memory_id" in result

        # Verify memory was actually saved
        memory_id = result["memory_id"]
        memory = manager.get_memory(memory_id, memory_name="test")
        assert memory is not None
        assert memory["content"] == "Python is my favorite language"

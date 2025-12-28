"""
Integration tests for Memory System

Tests the integration of memory manager with prompt config and tool execution.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llf.memory_manager import MemoryManager
from llf.memory_tools import MEMORY_TOOLS, execute_memory_tool, get_memory_system_prompt
from llf.prompt_config import PromptConfig


class TestMemoryTools:
    """Test memory tool definitions and execution."""

    def test_memory_tools_defined(self):
        """Test that all memory tools are properly defined."""
        assert len(MEMORY_TOOLS) == 6

        tool_names = [tool['function']['name'] for tool in MEMORY_TOOLS]
        assert 'add_memory' in tool_names
        assert 'search_memories' in tool_names
        assert 'get_memory' in tool_names
        assert 'update_memory' in tool_names
        assert 'delete_memory' in tool_names
        assert 'get_memory_stats' in tool_names

    def test_get_memory_system_prompt(self):
        """Test that system prompt is returned."""
        prompt = get_memory_system_prompt()
        assert prompt is not None
        assert "Long-Term Memory" in prompt
        assert "add_memory" in prompt


class TestPromptConfigMemoryIntegration:
    """Test PromptConfig integration with memory."""

    def test_prompt_config_initializes_memory(self):
        """Test that PromptConfig can initialize memory manager."""
        pc = PromptConfig()

        # The memory manager should initialize but may have no memories enabled
        pc._init_memory_manager()

        # Should have initialized memory manager (even if no memories enabled)
        assert pc._memory_manager is not None

    def test_get_memory_tools_when_enabled(self, tmp_path):
        """Test getting memory tools when memory is enabled."""
        config_file = tmp_path / "config_prompt.json"
        config_file.write_text('{"system_prompt": "Test"}')

        pc = PromptConfig(config_file=config_file)

        # Mock a memory manager
        mock_manager = Mock()
        mock_manager.has_enabled_memories.return_value = True
        mock_manager.enabled_memories = {"main_memory": {}}  # Mock the enabled_memories dict
        pc._memory_manager = mock_manager

        tools = pc.get_memory_tools()
        assert tools is not None
        assert len(tools) == 6

    def test_get_memory_tools_when_disabled(self):
        """Test getting memory tools when memory is disabled."""
        pc = PromptConfig()

        # Mock a memory manager with no enabled memories
        mock_manager = Mock()
        mock_manager.has_enabled_memories.return_value = False
        pc._memory_manager = mock_manager

        tools = pc.get_memory_tools()
        assert tools is None


class TestMemoryToolExecution:
    """Test executing memory tools."""

    def test_execute_add_memory(self, tmp_path):
        """Test executing add_memory tool."""
        # Setup test memory
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

        # Execute add_memory
        result = execute_memory_tool(
            "add_memory",
            {
                "content": "Test memory",
                "memory_type": "note",
                "tags": ["test"],
                "importance": 0.8
            },
            manager
        )

        assert result["success"] is True
        assert "memory_id" in result

    def test_execute_search_memories(self, tmp_path):
        """Test executing search_memories tool."""
        memory_dir = tmp_path / "memory" / "test"
        memory_dir.mkdir(parents=True)

        # Create some test memories
        memories = [
            {"id": "mem_1", "content": "Python programming", "type": "note", "tags": [], "importance": 0.5}
        ]

        with open(memory_dir / "memory.jsonl", 'w') as f:
            for mem in memories:
                f.write(json.dumps(mem) + '\n')

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

        # Execute search
        result = execute_memory_tool(
            "search_memories",
            {"query": "python"},
            manager
        )

        assert result["success"] is True
        assert result["count"] == 1

    def test_execute_unknown_tool(self, tmp_path):
        """Test executing unknown tool returns error."""
        registry_path = tmp_path / "registry.json"
        registry_path.write_text('{"memories": []}')

        manager = MemoryManager(registry_path=registry_path)

        result = execute_memory_tool("unknown_tool", {}, manager)

        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestEndToEndMemory:
    """End-to-end tests for memory functionality."""

    def test_full_memory_workflow(self, tmp_path):
        """Test a complete workflow: add, search, update, delete."""
        # Setup
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

        # Use execute_memory_tool which handles memory_name automatically
        # Step 1: Add a memory
        add_result = execute_memory_tool(
            "add_memory",
            {
                "content": "User likes Python",
                "memory_type": "preference",
                "tags": ["programming"],
                "importance": 0.9
            },
            manager
        )

        assert add_result["success"] is True
        memory_id = add_result["memory_id"]
        assert memory_id is not None

        # Step 2: Search for it
        search_result = execute_memory_tool(
            "search_memories",
            {"query": "Python"},
            manager
        )
        assert search_result["success"] is True
        assert search_result["count"] == 1
        assert search_result["memories"][0]["id"] == memory_id

        # Step 3: Update it
        update_result = execute_memory_tool(
            "update_memory",
            {"memory_id": memory_id, "content": "User loves Python"},
            manager
        )
        assert update_result["success"] is True

        # Step 4: Verify update
        get_result = execute_memory_tool(
            "get_memory",
            {"memory_id": memory_id},
            manager
        )
        assert get_result["success"] is True
        assert get_result["memory"]["content"] == "User loves Python"

        # Step 5: Delete it
        delete_result = execute_memory_tool(
            "delete_memory",
            {"memory_id": memory_id},
            manager
        )
        assert delete_result["success"] is True

        # Step 6: Verify deletion
        get_result2 = execute_memory_tool(
            "get_memory",
            {"memory_id": memory_id},
            manager
        )
        assert get_result2["success"] is False

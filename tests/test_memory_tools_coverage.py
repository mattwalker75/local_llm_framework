"""
Comprehensive unit tests for memory_tools to improve coverage.
"""

import pytest
from unittest.mock import MagicMock, patch
from llf.memory_tools import execute_memory_tool, get_memory_system_prompt, MEMORY_TOOL_NAMES


class TestMemoryToolsErrorCases:
    """Test error cases and edge conditions in memory_tools."""

    def test_update_memory_not_found(self):
        """Test update_memory when memory doesn't exist."""
        # Create mock memory manager
        mock_manager = MagicMock()
        mock_manager.enabled_memories = {"main_memory": True}
        mock_manager.update_memory.return_value = False  # Memory not found

        result = execute_memory_tool(
            'update_memory',
            {'memory_id': 'nonexistent', 'content': 'new content'},
            mock_manager
        )

        assert result['success'] is False
        assert 'Failed to update' in result['error']
        assert 'nonexistent' in result['error']

    def test_delete_memory_not_found(self):
        """Test delete_memory when memory doesn't exist."""
        # Create mock memory manager
        mock_manager = MagicMock()
        mock_manager.enabled_memories = {"main_memory": True}
        mock_manager.delete_memory.return_value = False  # Memory not found

        result = execute_memory_tool(
            'delete_memory',
            {'memory_id': 'nonexistent'},
            mock_manager
        )

        assert result['success'] is False
        assert 'Failed to delete' in result['error']
        assert 'nonexistent' in result['error']

    def test_get_memory_stats_success(self):
        """Test get_memory_stats returns statistics."""
        # Create mock memory manager
        mock_manager = MagicMock()
        mock_manager.enabled_memories = {"main_memory": True}
        mock_manager.get_stats.return_value = {
            'total_memories': 10,
            'by_type': {'note': 5, 'fact': 3, 'task': 2}
        }

        result = execute_memory_tool(
            'get_memory_stats',
            {},
            mock_manager
        )

        assert result['success'] is True
        assert 'stats' in result
        assert result['stats']['total_memories'] == 10

    def test_exception_during_tool_execution(self):
        """Test exception handling in execute_memory_tool."""
        # Create mock memory manager that raises exception
        mock_manager = MagicMock()
        mock_manager.enabled_memories = {"main_memory": True}
        mock_manager.add_memory.side_effect = Exception("Database error")

        result = execute_memory_tool(
            'add_memory',
            {'content': 'test', 'memory_type': 'note'},
            mock_manager
        )

        assert result['success'] is False
        assert 'Database error' in result['error']

    def test_unknown_tool_name(self):
        """Test execute_memory_tool with unknown tool name."""
        mock_manager = MagicMock()
        mock_manager.enabled_memories = {"main_memory": True}

        result = execute_memory_tool(
            'unknown_tool',
            {},
            mock_manager
        )

        assert result['success'] is False
        assert 'Unknown tool' in result['error']


class TestMemoryToolsHelpers:
    """Test helper functions in memory_tools."""

    def test_get_memory_system_prompt(self):
        """Test that get_memory_system_prompt returns prompt text."""
        prompt = get_memory_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'Long-Term Memory' in prompt
        assert 'search_memories' in prompt

    def test_memory_tool_names_constant(self):
        """Test MEMORY_TOOL_NAMES contains all expected tools."""
        expected_tools = {
            'add_memory',
            'search_memories',
            'get_memory',
            'update_memory',
            'delete_memory',
            'get_memory_stats'
        }

        assert MEMORY_TOOL_NAMES == expected_tools

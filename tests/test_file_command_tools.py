"""
Unit tests for File Access and Command Execution Tools.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from llf.tools_manager import ToolsManager


class TestFileAccessTool:
    """Test file_access tool."""

    def test_load_tool_module(self):
        """Test loading the file_access tool module."""
        manager = ToolsManager()
        # First import the tool
        manager.import_tool('file_access')

        module = manager.load_tool_module('file_access')

        assert module is not None
        assert hasattr(module, 'TOOL_DEFINITION')
        assert hasattr(module, 'execute')

    def test_tool_definition_structure(self):
        """Test that TOOL_DEFINITION has correct structure."""
        manager = ToolsManager()
        manager.import_tool('file_access')
        module = manager.load_tool_module('file_access')

        tool_def = module.TOOL_DEFINITION
        assert tool_def['type'] == 'function'
        assert 'function' in tool_def
        assert tool_def['function']['name'] == 'file_access'
        assert 'parameters' in tool_def['function']
        assert 'operation' in tool_def['function']['parameters']['properties']
        assert 'path' in tool_def['function']['parameters']['properties']

    def test_execute_missing_parameters(self):
        """Test execute with missing parameters."""
        manager = ToolsManager()
        manager.import_tool('file_access')
        module = manager.load_tool_module('file_access')

        # Missing operation
        result = module.execute({'path': '/test.txt'})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

        # Missing path
        result = module.execute({'operation': 'read'})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

    def test_execute_read_not_whitelisted(self, tmp_path):
        """Test read operation on non-whitelisted path."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        manager = ToolsManager()
        manager.import_tool('file_access')

        # Set empty whitelist
        tool_info = manager.get_tool_info('file_access')
        tool_info['metadata']['whitelist'] = []
        manager._save_registry()

        module = manager.load_tool_module('file_access')

        result = module.execute({
            'operation': 'read',
            'path': str(test_file)
        })

        assert result['success'] is False
        assert 'not whitelisted' in result['error']

    def test_execute_write_ro_mode(self, tmp_path):
        """Test write operation in read-only mode."""
        test_file = tmp_path / "test.txt"

        manager = ToolsManager()
        manager.import_tool('file_access')

        # Set mode to ro and whitelist the path
        tool_info = manager.get_tool_info('file_access')
        tool_info['metadata']['mode'] = 'ro'
        tool_info['metadata']['whitelist'] = [str(tmp_path / "*")]
        manager._save_registry()

        module = manager.load_tool_module('file_access')

        result = module.execute({
            'operation': 'write',
            'path': str(test_file),
            'content': 'test content'
        })

        assert result['success'] is False
        assert 'not permitted' in result['error']
        assert 'ro' in result['error']


class TestCommandExecTool:
    """Test command_exec tool."""

    def test_load_tool_module(self):
        """Test loading the command_exec tool module."""
        manager = ToolsManager()
        manager.import_tool('command_exec')

        module = manager.load_tool_module('command_exec')

        assert module is not None
        assert hasattr(module, 'TOOL_DEFINITION')
        assert hasattr(module, 'execute')

    def test_tool_definition_structure(self):
        """Test that TOOL_DEFINITION has correct structure."""
        manager = ToolsManager()
        manager.import_tool('command_exec')
        module = manager.load_tool_module('command_exec')

        tool_def = module.TOOL_DEFINITION
        assert tool_def['type'] == 'function'
        assert 'function' in tool_def
        assert tool_def['function']['name'] == 'command_exec'
        assert 'parameters' in tool_def['function']
        assert 'command' in tool_def['function']['parameters']['properties']

    def test_execute_missing_command(self):
        """Test execute with missing command."""
        manager = ToolsManager()
        manager.import_tool('command_exec')
        module = manager.load_tool_module('command_exec')

        result = module.execute({})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

    def test_execute_not_whitelisted(self):
        """Test execute with non-whitelisted command."""
        manager = ToolsManager()
        manager.import_tool('command_exec')

        # Set empty whitelist
        tool_info = manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = []
        manager._save_registry()

        module = manager.load_tool_module('command_exec')

        result = module.execute({'command': 'ls'})
        assert result['success'] is False
        assert 'not whitelisted' in result['error']

    def test_execute_whitelisted_command(self):
        """Test execute with whitelisted command."""
        manager = ToolsManager()
        manager.import_tool('command_exec')

        # Whitelist 'echo' command
        tool_info = manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        manager._save_registry()

        module = manager.load_tool_module('command_exec')

        result = module.execute({
            'command': 'echo',
            'arguments': ['hello', 'world']
        })

        assert result['success'] is True
        assert result['return_code'] == 0
        assert 'hello world' in result['stdout']

    def test_execute_dangerous_command(self):
        """Test execute with dangerous command (rm)."""
        manager = ToolsManager()
        manager.import_tool('command_exec')

        # Whitelist rm (but should still be blocked)
        tool_info = manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['rm']
        tool_info['metadata']['requires_approval'] = False
        manager._save_registry()

        module = manager.load_tool_module('command_exec')

        result = module.execute({'command': 'rm', 'arguments': ['/tmp/test.txt']})
        assert result['success'] is False
        assert 'requires approval' in result['error']

    def test_execute_with_timeout(self):
        """Test execute with timeout parameter."""
        manager = ToolsManager()
        manager.import_tool('command_exec')

        # Whitelist sleep command
        tool_info = manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['sleep']
        manager._save_registry()

        module = manager.load_tool_module('command_exec')

        # This should timeout
        result = module.execute({
            'command': 'sleep',
            'arguments': ['10'],
            'timeout': 1
        })

        assert result['success'] is False
        assert result.get('timed_out') is True


class TestToolsRegistry:
    """Test that file_access and command_exec tools can be registered."""

    def test_file_access_config_exists(self):
        """Test that file_access has a config.json."""
        config_path = Path(__file__).parent.parent / 'tools' / 'file_access' / 'config.json'
        assert config_path.exists()

        with open(config_path) as f:
            config = json.load(f)

        assert config['name'] == 'file_access'
        assert config['type'] == 'llm_invokable'
        assert 'whitelist' in config['metadata']
        assert 'mode' in config['metadata']
        assert 'root_dir' in config['metadata']

    def test_command_exec_config_exists(self):
        """Test that command_exec has a config.json."""
        config_path = Path(__file__).parent.parent / 'tools' / 'command_exec' / 'config.json'
        assert config_path.exists()

        with open(config_path) as f:
            config = json.load(f)

        assert config['name'] == 'command_exec'
        assert config['type'] == 'llm_invokable'
        assert 'whitelist' in config['metadata']

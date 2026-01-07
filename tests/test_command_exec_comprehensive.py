"""
Comprehensive unit tests for Command Execution Tool to improve coverage.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from llf.tools_manager import ToolsManager


class TestCommandExecOperations:
    """Test all command_exec operations."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = ToolsManager()
        if not self.manager.get_tool_info('command_exec'):
            self.manager.import_tool('command_exec')
        self.module = self.manager.load_tool_module('command_exec')

    def test_execute_simple_command(self):
        """Test executing a simple whitelisted command."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'echo',
            'arguments': ['hello']
        })

        assert result['success'] is True
        assert result['return_code'] == 0
        assert 'hello' in result['stdout']

    def test_execute_command_with_multiple_arguments(self):
        """Test executing command with multiple arguments."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'echo',
            'arguments': ['hello', 'world', 'test']
        })

        assert result['success'] is True
        assert 'hello world test' in result['stdout']

    def test_execute_command_without_arguments(self):
        """Test executing command without arguments."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['pwd']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'pwd'
        })

        assert result['success'] is True
        assert result['return_code'] == 0

    def test_execute_command_nonzero_exit(self):
        """Test executing command that returns non-zero exit code."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['false']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'false'
        })

        assert result['success'] is True  # Success means command ran
        assert result['return_code'] != 0  # But exit code is non-zero

    def test_execute_timeout(self):
        """Test command timeout."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['sleep']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'sleep',
            'arguments': ['10'],
            'timeout': 1
        })

        assert result['success'] is False
        assert result.get('timed_out') is True
        assert 'timed out' in result['error'].lower()

    def test_execute_timeout_clamping(self):
        """Test that timeout is clamped to valid range."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        # Test max timeout (should be clamped to 300)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            result = self.module.execute({
                'command': 'echo',
                'arguments': ['test'],
                'timeout': 500  # Should be clamped to 300
            })

            # Check that subprocess.run was called with clamped timeout
            call_args = mock_run.call_args
            assert call_args[1]['timeout'] == 300

        # Test min timeout (should be clamped to 1)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            result = self.module.execute({
                'command': 'echo',
                'arguments': ['test'],
                'timeout': 0  # Should be clamped to 1
            })

            call_args = mock_run.call_args
            assert call_args[1]['timeout'] >= 1

    def test_execute_command_not_found(self):
        """Test executing non-existent command."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['nonexistent_command_12345']
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'nonexistent_command_12345'
        })

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_execute_captures_stderr(self):
        """Test that stderr is captured."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['sh']
        self.manager._save_registry()

        # Run command that writes to stderr
        result = self.module.execute({
            'command': 'sh',
            'arguments': ['-c', 'echo error >&2']
        })

        assert result['success'] is True
        assert 'error' in result['stderr']


class TestCommandExecSecurity:
    """Test security features of command_exec tool."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = ToolsManager()
        if not self.manager.get_tool_info('command_exec'):
            self.manager.import_tool('command_exec')
        self.module = self.manager.load_tool_module('command_exec')

    def test_command_not_whitelisted(self):
        """Test executing non-whitelisted command."""
        # Configure empty whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = []
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'echo'
        })

        assert result['success'] is False
        assert 'not whitelisted' in result['error']

    def test_pattern_whitelist_exact_match(self):
        """Test pattern whitelisting with exact match."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        # Should succeed
        result = self.module.execute({'command': 'echo'})
        assert result['success'] is True

        # Should fail
        result = self.module.execute({'command': 'cat'})
        assert result['success'] is False

    def test_pattern_whitelist_glob_match(self):
        """Test pattern whitelisting with glob patterns."""
        # Configure whitelist with pattern
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['git*']
        self.manager._save_registry()

        # Mock subprocess to avoid actual git calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            # Should succeed for git
            result = self.module.execute({'command': 'git'})
            assert result['success'] is True

            # Should succeed for git-log
            result = self.module.execute({'command': 'git-log'})
            assert result['success'] is True

        # Should fail for cat (doesn't match pattern)
        result = self.module.execute({'command': 'cat'})
        assert result['success'] is False

    def test_dangerous_command_rm(self):
        """Test dangerous command detection for rm."""
        # Configure whitelist with rm
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['rm']
        tool_info['metadata']['requires_approval'] = False
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'rm',
            'arguments': ['/tmp/test.txt']
        })

        assert result['success'] is False
        assert 'requires approval' in result['error'].lower()

    def test_dangerous_command_del(self):
        """Test dangerous command detection for del."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['del']
        tool_info['metadata']['requires_approval'] = False
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'del'
        })

        assert result['success'] is False
        assert 'requires approval' in result['error'].lower()

    def test_dangerous_command_format(self):
        """Test dangerous command detection for format."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['format']
        tool_info['metadata']['requires_approval'] = False
        self.manager._save_registry()

        result = self.module.execute({
            'command': 'format'
        })

        assert result['success'] is False
        assert 'requires approval' in result['error'].lower()

    def test_dangerous_command_with_approval(self):
        """Test dangerous command with approval enabled."""
        # Configure whitelist with approval
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['rm']
        tool_info['metadata']['requires_approval'] = True
        self.manager._save_registry()

        # Mock subprocess to avoid actual rm
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

            result = self.module.execute({
                'command': 'rm',
                'arguments': ['/tmp/test.txt']
            })

            # With approval enabled, should succeed
            assert result['success'] is True


class TestCommandExecErrorHandling:
    """Test error handling in command_exec tool."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = ToolsManager()
        if not self.manager.get_tool_info('command_exec'):
            self.manager.import_tool('command_exec')
        self.module = self.manager.load_tool_module('command_exec')

    def test_missing_command_parameter(self):
        """Test execution without command parameter."""
        result = self.module.execute({})

        assert result['success'] is False
        assert 'required' in result['error'].lower()

    def test_arguments_not_list(self):
        """Test handling when arguments is not a list."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        # Pass string instead of list
        result = self.module.execute({
            'command': 'echo',
            'arguments': 'hello'  # String instead of list
        })

        # Should convert to list
        assert result['success'] is True

    def test_exception_during_execution(self):
        """Test exception handling during command execution."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['echo']
        self.manager._save_registry()

        # Mock subprocess.run to raise exception
        with patch('subprocess.run', side_effect=Exception("Unexpected error")):
            result = self.module.execute({
                'command': 'echo',
                'arguments': ['test']
            })

            assert result['success'] is False
            assert 'failed' in result['error'].lower()

    def test_file_not_found_error(self):
        """Test FileNotFoundError is handled properly."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['nonexistent']
        self.manager._save_registry()

        # Mock subprocess.run to raise FileNotFoundError
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            result = self.module.execute({
                'command': 'nonexistent'
            })

            assert result['success'] is False
            assert 'not found' in result['error'].lower()

    def test_timeout_expired_error(self):
        """Test TimeoutExpired error is handled properly."""
        # Configure whitelist
        tool_info = self.manager.get_tool_info('command_exec')
        tool_info['metadata']['whitelist'] = ['sleep']
        self.manager._save_registry()

        # Mock subprocess.run to raise TimeoutExpired
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('sleep', 1)):
            result = self.module.execute({
                'command': 'sleep',
                'arguments': ['10'],
                'timeout': 1
            })

            assert result['success'] is False
            assert result.get('timed_out') is True
            assert 'timed out' in result['error'].lower()

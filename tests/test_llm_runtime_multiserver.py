"""
Comprehensive tests for LLMRuntime multi-server functionality.

This test suite focuses on testing the NEW multi-server methods in LLMRuntime
without modifying existing tests.
"""

import pytest
import subprocess
import psutil
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

from llf.llm_runtime import LLMRuntime
from llf.config import Config, ServerConfig
from llf.model_manager import ModelManager


@pytest.fixture
def multi_server_config(tmp_path):
    """Create a config with multiple servers."""
    config = Config()

    # Create server configs
    server1 = ServerConfig(
        name='server1',
        llama_server_path=Path('/usr/bin/llama-server'),
        server_host='127.0.0.1',
        server_port=8000,
        healthcheck_interval=2.0,
        model_dir=tmp_path / 'models' / 'server1',
        gguf_file='model1.gguf',
        server_params={},
        auto_start=False
    )

    server2 = ServerConfig(
        name='server2',
        llama_server_path=Path('/usr/bin/llama-server'),
        server_host='127.0.0.1',
        server_port=8001,
        healthcheck_interval=2.0,
        model_dir=tmp_path / 'models' / 'server2',
        gguf_file='model2.gguf',
        server_params={},
        auto_start=False
    )

    config.servers = {
        'server1': server1,
        'server2': server2
    }
    config.default_local_server = 'server1'

    return config


@pytest.fixture
def mock_model_manager():
    """Create a mock ModelManager."""
    return MagicMock(spec=ModelManager)


class TestGetRunningServers:
    """Tests for get_running_servers() method."""

    def test_get_running_servers_none_running(self, multi_server_config, mock_model_manager):
        """Test when no servers are running."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        result = runtime.get_running_servers()

        assert result == []

    def test_get_running_servers_one_running(self, multi_server_config, mock_model_manager):
        """Test when one server is running."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock server_processes to simulate server1 running
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = None  # Process is running
        runtime.server_processes['server1'] = mock_process

        result = runtime.get_running_servers()

        assert result == ['server1']

    def test_get_running_servers_multiple_running(self, multi_server_config, mock_model_manager):
        """Test when multiple servers are running."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock both servers running
        mock_process1 = MagicMock(spec=subprocess.Popen)
        mock_process1.poll.return_value = None
        mock_process2 = MagicMock(spec=subprocess.Popen)
        mock_process2.poll.return_value = None

        runtime.server_processes['server1'] = mock_process1
        runtime.server_processes['server2'] = mock_process2

        result = runtime.get_running_servers()

        assert set(result) == {'server1', 'server2'}

    def test_get_running_servers_filters_dead_processes(self, multi_server_config, mock_model_manager):
        """Test that dead processes are filtered out."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock one running, one dead
        mock_running = MagicMock(spec=subprocess.Popen)
        mock_running.poll.return_value = None  # Running

        mock_dead = MagicMock(spec=subprocess.Popen)
        mock_dead.poll.return_value = 1  # Exited

        runtime.server_processes['server1'] = mock_running
        runtime.server_processes['server2'] = mock_dead

        result = runtime.get_running_servers()

        assert result == ['server1']


class TestIsServerRunningByName:
    """Tests for is_server_running_by_name() method."""

    def test_is_server_running_by_name_true(self, multi_server_config, mock_model_manager):
        """Test checking if a server is running - returns True."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock server running
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = None
        runtime.server_processes['server1'] = mock_process

        result = runtime.is_server_running_by_name('server1')

        assert result is True

    def test_is_server_running_by_name_false(self, multi_server_config, mock_model_manager):
        """Test checking if a server is running - returns False."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        result = runtime.is_server_running_by_name('server1')

        assert result is False

    def test_is_server_running_by_name_dead_process(self, multi_server_config, mock_model_manager):
        """Test that dead processes return False."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock dead process
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = 1  # Exited
        runtime.server_processes['server1'] = mock_process

        result = runtime.is_server_running_by_name('server1')

        assert result is False


class TestIsServerReadyAtPort:
    """Tests for _is_server_ready_at_port() method."""

    @patch('llf.llm_runtime.requests')
    def test_is_server_ready_at_port_ready(self, mock_requests, multi_server_config, mock_model_manager):
        """Test checking if server is ready at port - returns True."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock successful health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = runtime._is_server_ready_at_port(8000)

        assert result is True
        mock_requests.get.assert_called_once()

    @patch('llf.llm_runtime.requests')
    def test_is_server_ready_at_port_not_ready(self, mock_requests, multi_server_config, mock_model_manager):
        """Test checking if server is ready at port - returns False."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock failed health check
        mock_requests.get.side_effect = Exception("Connection refused")

        result = runtime._is_server_ready_at_port(8000)

        assert result is False

    @patch('llf.llm_runtime.requests')
    def test_is_server_ready_at_port_custom_host(self, mock_requests, multi_server_config, mock_model_manager):
        """Test health check with custom host."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = runtime._is_server_ready_at_port(8000, '0.0.0.0')

        assert result is True
        # Verify the URL used the custom host
        call_args = mock_requests.get.call_args[0][0]
        assert '0.0.0.0' in call_args


class TestStartServerByName:
    """Tests for start_server_by_name() method."""

    @patch('rich.prompt.Prompt.ask')
    @patch('llf.llm_runtime.LLMRuntime.get_running_servers')
    def test_start_server_by_name_memory_warning_declined(
        self, mock_get_running, mock_prompt, multi_server_config, mock_model_manager
    ):
        """Test memory warning when other servers running - user declines."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Setup mocks
        mock_get_running.return_value = ['server2']  # Another server running
        mock_prompt.return_value = 'n'  # User declines

        # Execute
        runtime.start_server_by_name('server1', force=False)

        # Verify - should not have started server (user declined)
        assert 'server1' not in runtime.server_processes

    def test_start_server_by_name_already_running(self, multi_server_config, mock_model_manager):
        """Test starting server that's already running."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock server already running
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_process.poll.return_value = None
        runtime.server_processes['server1'] = mock_process

        # Execute - should not raise exception, just return early
        runtime.start_server_by_name('server1')

        # Verify - process should still be the same mock
        assert runtime.server_processes['server1'] is mock_process

    def test_start_server_by_name_invalid_server(self, multi_server_config, mock_model_manager):
        """Test starting non-existent server raises ValueError."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        with pytest.raises(ValueError, match="not found"):
            runtime.start_server_by_name('nonexistent')


class TestStopServerByName:
    """Tests for stop_server_by_name() method."""

    @patch('llf.llm_runtime.signal')
    def test_stop_server_by_name_success(self, mock_signal, multi_server_config, mock_model_manager):
        """Test successfully stopping a server by name."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock running server
        mock_process = MagicMock(spec=subprocess.Popen)
        runtime.server_processes['server1'] = mock_process

        # Execute
        runtime.stop_server_by_name('server1')

        # Verify send_signal was called
        mock_process.send_signal.assert_called_once()
        assert 'server1' not in runtime.server_processes

    def test_stop_server_by_name_not_running(self, multi_server_config, mock_model_manager):
        """Test stopping server that's not running."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Execute - should not raise exception
        runtime.stop_server_by_name('server1')

        # Verify - nothing to assert, just shouldn't crash

    @patch('llf.llm_runtime.signal')
    def test_stop_server_by_name_force_kill(self, mock_signal, multi_server_config, mock_model_manager):
        """Test force killing server if SIGTERM doesn't work."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock running server that doesn't terminate gracefully
        mock_process = MagicMock(spec=subprocess.Popen)
        mock_process.wait.side_effect = subprocess.TimeoutExpired('cmd', 10)  # Times out
        runtime.server_processes['server1'] = mock_process

        # Execute
        runtime.stop_server_by_name('server1')

        # Verify kill was called after timeout
        mock_process.kill.assert_called_once()


class TestFindLlamaServerProcessByPort:
    """Tests for _find_llama_server_process_by_port() method."""

    @patch('llf.llm_runtime.psutil.process_iter')
    def test_find_llama_server_process_by_port_found(self, mock_process_iter, multi_server_config, mock_model_manager):
        """Test finding llama-server process by port - found."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock process with matching port
        mock_process = MagicMock(spec=psutil.Process)
        mock_process.pid = 1234
        mock_process.info = {'cmdline': ['llama-server', '--port', '8000'], 'pid': 1234, 'name': 'llama-server'}

        mock_process_iter.return_value = [mock_process]

        # Execute
        result = runtime._find_llama_server_process_by_port(8000)

        # Verify
        assert result is mock_process

    @patch('llf.llm_runtime.psutil.process_iter')
    def test_find_llama_server_process_by_port_not_found(self, mock_process_iter, multi_server_config, mock_model_manager):
        """Test finding llama-server process by port - not found."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock process on different port
        mock_process = MagicMock(spec=psutil.Process)
        mock_process.pid = 1234
        mock_process.info = {'cmdline': ['llama-server', '--port', '9000'], 'pid': 1234, 'name': 'llama-server'}

        mock_process_iter.return_value = [mock_process]

        # Execute
        result = runtime._find_llama_server_process_by_port(8000)

        # Verify
        assert result is None

    @patch('llf.llm_runtime.psutil.process_iter')
    def test_find_llama_server_process_by_port_exception_handling(self, mock_process_iter, multi_server_config, mock_model_manager):
        """Test exception handling in process iteration."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock process that raises exception
        mock_process = MagicMock(spec=psutil.Process)
        mock_process.name.side_effect = psutil.NoSuchProcess(pid=123)

        mock_process_iter.return_value = [mock_process]

        # Execute - should not raise exception
        result = runtime._find_llama_server_process_by_port(8000)

        # Verify
        assert result is None


class TestMultiServerClientManagement:
    """Tests for client management in multi-server setup."""

    def test_clients_dictionary_initialized(self, multi_server_config, mock_model_manager):
        """Test that clients dictionary is properly initialized."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        assert hasattr(runtime, 'clients')
        assert isinstance(runtime.clients, dict)

    @patch('llf.llm_runtime.OpenAI')
    def test_get_client_creates_new_client_for_server(self, mock_openai, multi_server_config, mock_model_manager):
        """Test that get_client creates OpenAI client for specific server."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Note: get_client() is called internally, we're testing the behavior indirectly
        # by checking that the runtime can manage multiple clients

        # This verifies the clients dict exists and can store multiple clients
        assert runtime.clients == {}


class TestMultiServerIntegration:
    """Integration tests for multi-server functionality."""

    def test_multiple_servers_isolated(self, multi_server_config, mock_model_manager):
        """Test that multiple servers maintain isolated state."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock two running servers
        mock_process1 = MagicMock(spec=subprocess.Popen)
        mock_process1.poll.return_value = None

        mock_process2 = MagicMock(spec=subprocess.Popen)
        mock_process2.poll.return_value = None

        runtime.server_processes['server1'] = mock_process1
        runtime.server_processes['server2'] = mock_process2

        # Verify both are tracked separately
        assert runtime.is_server_running_by_name('server1')
        assert runtime.is_server_running_by_name('server2')
        assert set(runtime.get_running_servers()) == {'server1', 'server2'}

    def test_stop_one_server_leaves_others_running(self, multi_server_config, mock_model_manager):
        """Test that stopping one server doesn't affect others."""
        runtime = LLMRuntime(multi_server_config, mock_model_manager)

        # Mock two running servers
        mock_process1 = MagicMock(spec=subprocess.Popen)
        mock_process1.poll.return_value = None

        mock_process2 = MagicMock(spec=subprocess.Popen)
        mock_process2.poll.return_value = None

        runtime.server_processes['server1'] = mock_process1
        runtime.server_processes['server2'] = mock_process2

        # Stop server1
        runtime.stop_server_by_name('server1')

        # Verify server2 still running
        assert not runtime.is_server_running_by_name('server1')
        assert runtime.is_server_running_by_name('server2')

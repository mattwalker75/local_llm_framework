"""
Simplified tests to improve coverage for llm_runtime.py missing lines.

Focus on edge cases that can be tested without complex server setup.
"""

import pytest
import psutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from llf.llm_runtime import LLMRuntime
from llf.config import Config


@pytest.fixture
def config(tmp_path):
    """Create test configuration."""
    config = Config()
    config.model_dir = tmp_path / "models"
    config.cache_dir = tmp_path / ".cache"
    config.model_name = "test/model"
    config.gguf_file = "test-model.gguf"
    config.server_host = "127.0.0.1"
    config.server_port = 8080
    config.llama_server_path = tmp_path / "llama-server"
    config.server_wrapper_script = tmp_path / "wrapper.sh"
    config.custom_model_dir = None
    config.default_local_server = None
    config.inference_params = {}
    config.api_base_url = "http://127.0.0.1:8080/v1"
    return config


@pytest.fixture
def model_manager():
    """Create mock model manager."""
    manager = Mock()
    manager.get_model_path = Mock(return_value=Path("/models/test-model"))
    manager.is_model_downloaded = Mock(return_value=True)
    return manager


@pytest.fixture
def runtime(config, model_manager):
    """Create LLM runtime instance."""
    return LLMRuntime(config, model_manager)


class TestProcessSearchException:
    """Test process search exception handling (lines 247-248)."""

    def test_find_process_with_general_exception(self, runtime):
        """Test handling general exception when searching processes (lines 247-248)."""
        # Mock process iteration to raise exception
        with patch('psutil.process_iter', side_effect=RuntimeError("Process error")):
            with patch('llf.llm_runtime.logger') as mock_logger:
                result = runtime._find_llama_server_process()

                # Should log error and return None (lines 247-248)
                assert result is None
                assert any('Error searching for llama-server process' in str(call)
                          for call in mock_logger.debug.call_args_list)


class TestStopServerWithProcess:
    """Test stop_server when process is found (lines 285-305)."""

    def test_stop_server_by_port_graceful(self, runtime):
        """Test graceful server stop by port (lines 285-298)."""
        # Mock finding a process
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.pid = 12345
        mock_proc.send_signal = Mock()
        mock_proc.wait = Mock()

        with patch.object(runtime, '_find_llama_server_process', return_value=mock_proc):
            with patch('llf.llm_runtime.logger') as mock_logger:
                runtime.stop_server()

                # Should send SIGTERM and wait (lines 289-291)
                mock_proc.send_signal.assert_called_once()
                mock_proc.wait.assert_called()
                assert any('llama-server stopped' in str(call)
                          for call in mock_logger.info.call_args_list)

    def test_stop_server_force_kill_after_timeout(self, runtime):
        """Test force kill when graceful shutdown times out (lines 292-296)."""
        # Mock process that times out on graceful shutdown
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.pid = 12345
        mock_proc.send_signal = Mock()
        mock_proc.wait = Mock(side_effect=[psutil.TimeoutExpired(10), None])
        mock_proc.kill = Mock()

        with patch.object(runtime, '_find_llama_server_process', return_value=mock_proc):
            with patch('llf.llm_runtime.logger') as mock_logger:
                runtime.stop_server()

                # Should force kill after timeout (lines 294-296)
                mock_proc.kill.assert_called_once()
                assert any('force killing' in str(call).lower()
                          for call in mock_logger.warning.call_args_list)

    def test_stop_server_exception_during_stop(self, runtime):
        """Test exception handling during server stop (lines 300-305)."""
        # Mock process that raises exception
        mock_proc = Mock(spec=psutil.Process)
        mock_proc.pid = 12345
        mock_proc.send_signal = Mock(side_effect=Exception("Stop error"))

        with patch.object(runtime, '_find_llama_server_process', return_value=mock_proc):
            with patch('llf.llm_runtime.logger') as mock_logger:
                # Should handle exception gracefully (lines 300-305)
                runtime.stop_server()

                assert any('Error stopping llama-server' in str(call)
                          for call in mock_logger.error.call_args_list)
                # Server process should be cleared in finally block
                assert runtime.server_process is None
                assert runtime.client is None


class TestGenerateErrorPaths:
    """Test generate method error paths."""

    def test_generate_with_server_but_api_error(self, runtime):
        """Test generate with API error."""
        runtime.server_process = Mock()
        runtime.server_process.poll = Mock(return_value=None)
        runtime.client = Mock()

        # Mock completion to raise exception
        runtime.client.completions.create = Mock(side_effect=Exception("API error"))

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to generate completion"):
            runtime.generate("test prompt")


class TestChatErrorPaths:
    """Test chat method error paths."""

    def test_chat_with_api_error_streaming(self, runtime):
        """Test chat with API error in streaming mode."""
        runtime.server_process = Mock()
        runtime.server_process.poll = Mock(return_value=None)
        runtime.client = Mock()

        # Mock chat to raise exception
        runtime.client.chat.completions.create = Mock(side_effect=Exception("API error"))

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to generate chat completion"):
            runtime.chat([{"role": "user", "content": "test"}], stream=True)


class TestListModelsErrors:
    """Test list_models error paths."""

    def test_list_models_with_api_error(self, runtime):
        """Test list_models with API error."""
        # Initialize client
        runtime.client = Mock()
        runtime.client.models = Mock()
        runtime.client.models.list = Mock(side_effect=Exception("API error"))

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to list models"):
            runtime.list_models()


class TestServerAlreadyRunning:
    """Test server already running scenario."""

    def test_start_server_when_already_running(self, runtime, tmp_path):
        """Test starting server when already running logs warning."""
        # Create llama-server binary to get past that check
        runtime.config.llama_server_path.parent.mkdir(parents=True, exist_ok=True)
        runtime.config.llama_server_path.touch()

        # Set server_process to simulate already running
        runtime.server_process = Mock()
        runtime.server_process.poll = Mock(return_value=None)  # Process is running

        with patch('llf.llm_runtime.logger') as mock_logger:
            # Try to start server again
            runtime.start_server()

            # Should log warning and return early (lines 132-133)
            assert any('already running' in str(call).lower()
                      for call in mock_logger.warning.call_args_list)

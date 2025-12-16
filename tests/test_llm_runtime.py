"""
Unit tests for llm_runtime module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from llf.config import Config
from llf.model_manager import ModelManager
from llf.llm_runtime import LLMRuntime


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config(temp_dir):
    """Create test configuration."""
    config = Config()
    config.model_dir = temp_dir / "models"
    config.cache_dir = temp_dir / ".cache"
    config.model_name = "test/model"
    config.vllm_host = "127.0.0.1"
    config.vllm_port = 8000
    return config


@pytest.fixture
def model_manager(config):
    """Create model manager instance."""
    return ModelManager(config)


@pytest.fixture
def runtime(config, model_manager):
    """Create LLM runtime instance."""
    return LLMRuntime(config, model_manager)


class TestLLMRuntime:
    """Test LLMRuntime class."""

    def test_initialization(self, runtime, config, model_manager):
        """Test runtime initialization."""
        assert runtime.config == config
        assert runtime.model_manager == model_manager
        assert runtime.vllm_process is None
        assert runtime.client is None

    def test_get_vllm_command(self, runtime, temp_dir):
        """Test vLLM command generation."""
        model_path = temp_dir / "models" / "test--model"
        cmd = runtime._get_vllm_command(model_path)

        assert "-m" in cmd
        assert "vllm.entrypoints.openai.api_server" in cmd
        assert "--model" in cmd
        assert str(model_path) in cmd
        assert "--host" in cmd
        assert "127.0.0.1" in cmd
        assert "--port" in cmd
        assert "8000" in cmd

    def test_get_vllm_command_with_max_len(self, runtime, config, temp_dir):
        """Test vLLM command with max model length."""
        config.vllm_max_model_len = 4096
        model_path = temp_dir / "models" / "test--model"
        cmd = runtime._get_vllm_command(model_path)

        assert "--max-model-len" in cmd
        assert "4096" in cmd

    def test_is_server_running_false(self, runtime):
        """Test is_server_running when no server."""
        assert not runtime.is_server_running()

    def test_is_server_running_true(self, runtime):
        """Test is_server_running when server is running."""
        # Mock a running process
        runtime.vllm_process = MagicMock()
        runtime.vllm_process.poll.return_value = None  # None means running

        assert runtime.is_server_running()

    def test_is_server_running_terminated(self, runtime):
        """Test is_server_running when process terminated."""
        runtime.vllm_process = MagicMock()
        runtime.vllm_process.poll.return_value = 1  # Non-None means terminated

        assert not runtime.is_server_running()

    @patch('llf.llm_runtime.requests.get')
    def test_is_server_ready_true(self, mock_get, runtime):
        """Test is_server_ready when server responds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert runtime.is_server_ready()

    @patch('llf.llm_runtime.requests.get')
    def test_is_server_ready_false_bad_status(self, mock_get, runtime):
        """Test is_server_ready when server responds with error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        assert not runtime.is_server_ready()

    @patch('llf.llm_runtime.requests.get')
    def test_is_server_ready_false_exception(self, mock_get, runtime):
        """Test is_server_ready when request fails."""
        mock_get.side_effect = Exception("Connection failed")

        assert not runtime.is_server_ready()

    def test_start_server_model_not_downloaded(self, runtime):
        """Test start_server when model is not downloaded."""
        with pytest.raises(ValueError, match="not downloaded"):
            runtime.start_server()

    @patch('llf.llm_runtime.subprocess.Popen')
    @patch.object(LLMRuntime, 'is_server_ready')
    def test_start_server_success(self, mock_ready, mock_popen, runtime, model_manager, temp_dir):
        """Test successful server start."""
        # Setup model
        model_path = temp_dir / "models" / "test--model"
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        # Mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock server becoming ready
        mock_ready.return_value = True

        runtime.start_server()

        assert runtime.vllm_process is not None
        mock_popen.assert_called_once()

    @patch('llf.llm_runtime.subprocess.Popen')
    @patch.object(LLMRuntime, 'is_server_ready')
    def test_start_server_timeout(self, mock_ready, mock_popen, runtime, model_manager, temp_dir):
        """Test server start timeout."""
        # Setup model
        model_path = temp_dir / "models" / "test--model"
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        # Mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock server never becoming ready
        mock_ready.return_value = False

        with pytest.raises(RuntimeError, match="failed to become ready"):
            runtime.start_server(timeout=1)  # Short timeout for test

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_start_server_process_terminates(self, mock_popen, runtime, model_manager, temp_dir):
        """Test server start when process terminates early."""
        # Setup model
        model_path = temp_dir / "models" / "test--model"
        model_path.mkdir(parents=True)
        (model_path / "config.json").write_text("{}")

        # Mock process that terminates
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Terminated
        mock_process.stderr.read.return_value = "Error message"
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError, match="terminated unexpectedly"):
            runtime.start_server()

    def test_stop_server_no_process(self, runtime):
        """Test stop_server when no server is running."""
        # Should not raise an exception
        runtime.stop_server()

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_stop_server_graceful(self, mock_popen, runtime):
        """Test graceful server stop."""
        mock_process = MagicMock()
        mock_process.wait.return_value = None
        runtime.vllm_process = mock_process

        runtime.stop_server()

        mock_process.send_signal.assert_called_once()
        mock_process.wait.assert_called_once()
        assert runtime.vllm_process is None

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_stop_server_force_kill(self, mock_popen, runtime):
        """Test force kill when graceful stop fails."""
        mock_process = MagicMock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("cmd", 10), None]
        runtime.vllm_process = mock_process

        runtime.stop_server()

        mock_process.kill.assert_called_once()
        assert runtime.vllm_process is None

    def test_generate_no_server(self, runtime):
        """Test generate when server is not running."""
        with pytest.raises(RuntimeError, match="not running"):
            runtime.generate("test prompt")

    @patch.object(LLMRuntime, 'is_server_running')
    def test_generate_success(self, mock_running, runtime):
        """Test successful text generation."""
        mock_running.return_value = True

        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Generated text")]
        mock_client.completions.create.return_value = mock_response
        runtime.client = mock_client

        result = runtime.generate("test prompt")

        assert result == "Generated text"
        mock_client.completions.create.assert_called_once()

    @patch.object(LLMRuntime, 'is_server_running')
    def test_generate_with_params(self, mock_running, runtime):
        """Test generation with custom parameters."""
        mock_running.return_value = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Generated text")]
        mock_client.completions.create.return_value = mock_response
        runtime.client = mock_client

        result = runtime.generate(
            "test prompt",
            temperature=0.5,
            max_tokens=1000
        )

        assert result == "Generated text"
        call_kwargs = mock_client.completions.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_tokens'] == 1000

    @patch.object(LLMRuntime, 'is_server_running')
    def test_generate_failure(self, mock_running, runtime):
        """Test generation failure."""
        mock_running.return_value = True

        mock_client = MagicMock()
        mock_client.completions.create.side_effect = Exception("API error")
        runtime.client = mock_client

        with pytest.raises(RuntimeError, match="Failed to generate"):
            runtime.generate("test prompt")

    def test_chat_no_server(self, runtime):
        """Test chat when server is not running."""
        with pytest.raises(RuntimeError, match="not running"):
            runtime.chat([{"role": "user", "content": "Hello"}])

    @patch.object(LLMRuntime, 'is_server_running')
    def test_chat_success(self, mock_running, runtime):
        """Test successful chat generation."""
        mock_running.return_value = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello back!"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        result = runtime.chat(messages)

        assert result == "Hello back!"
        mock_client.chat.completions.create.assert_called_once()

    @patch.object(LLMRuntime, 'is_server_running')
    def test_chat_with_params(self, mock_running, runtime):
        """Test chat with custom parameters."""
        mock_running.return_value = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        result = runtime.chat(messages, temperature=0.3)

        assert result == "Response"
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.3

    @patch.object(LLMRuntime, 'stop_server')
    def test_context_manager(self, mock_stop, runtime):
        """Test runtime as context manager."""
        with runtime as rt:
            assert rt == runtime

        mock_stop.assert_called_once()

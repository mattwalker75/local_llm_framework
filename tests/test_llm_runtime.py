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
    config.gguf_file = "test-model.gguf"
    config.server_host = "127.0.0.1"
    config.server_port = 8000
    config.llama_server_path = temp_dir / "llama-server"
    config.server_wrapper_script = temp_dir / "wrapper.sh"
    config.custom_model_dir = None  # Ensure tests don't use real config's custom_model_dir
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
        assert runtime.server_process is None
        assert runtime.client is None

    def test_get_server_command(self, runtime, temp_dir):
        """Test server command generation."""
        model_file = temp_dir / "models" / "test--model" / "test-model.gguf"
        cmd = runtime._get_server_command(model_file)

        assert str(runtime.config.server_wrapper_script) in cmd
        assert "--server-path" in cmd
        assert "--model-file" in cmd
        assert str(model_file) in cmd
        assert "--host" in cmd
        assert "127.0.0.1" in cmd
        assert "--port" in cmd
        assert "8000" in cmd

    @patch.object(LLMRuntime, 'is_server_ready')
    def test_is_server_running_false(self, mock_ready, runtime):
        """Test is_server_running when no server."""
        # Mock is_server_ready to return False (no HTTP server responding)
        mock_ready.return_value = False
        assert not runtime.is_server_running()

    def test_is_server_running_true(self, runtime):
        """Test is_server_running when server is running."""
        # Mock a running process
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None  # None means running

        assert runtime.is_server_running()

    @patch.object(LLMRuntime, 'is_server_ready')
    def test_is_server_running_terminated(self, mock_ready, runtime):
        """Test is_server_running when process terminated."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = 1  # Non-None means terminated
        # Mock is_server_ready to return False (no HTTP server responding)
        mock_ready.return_value = False

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
        """Test is_server_ready with bad status code."""
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
        """Test start_server fails when model not downloaded."""
        # Create llama-server binary so we get past that check
        runtime.config.llama_server_path.parent.mkdir(parents=True, exist_ok=True)
        runtime.config.llama_server_path.touch()

        runtime.model_manager.is_model_downloaded = Mock(return_value=False)

        with pytest.raises(ValueError, match="is not downloaded"):
            runtime.start_server()

    def test_start_server_llama_server_not_found(self, runtime, config):
        """Test start_server fails when llama-server binary not found."""
        runtime.model_manager.is_model_downloaded = Mock(return_value=True)
        # llama_server_path points to non-existent file

        with pytest.raises(ValueError, match="llama-server binary not found"):
            runtime.start_server()

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_start_server_success(self, mock_popen, runtime, temp_dir):
        """Test successful server start."""
        # Setup
        runtime.model_manager.is_model_downloaded = Mock(return_value=True)
        runtime.config.llama_server_path.parent.mkdir(parents=True, exist_ok=True)
        runtime.config.llama_server_path.touch()  # Create fake binary

        model_dir = temp_dir / "models" / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_dir / "test-model.gguf"
        model_file.touch()

        runtime.model_manager.get_model_path = Mock(return_value=model_dir)

        # Mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock server ready check - should be False initially, then True after server starts
        runtime.is_server_ready = Mock(side_effect=[False, True])

        # Test
        runtime.start_server()

        assert mock_popen.called
        assert runtime.server_process is not None

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_start_server_timeout(self, mock_popen, runtime, temp_dir):
        """Test server start timeout."""
        # Setup
        runtime.model_manager.is_model_downloaded = Mock(return_value=True)
        runtime.config.llama_server_path.parent.mkdir(parents=True, exist_ok=True)
        runtime.config.llama_server_path.touch()

        model_dir = temp_dir / "models" / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_dir / "test-model.gguf"
        model_file.touch()

        runtime.model_manager.get_model_path = Mock(return_value=model_dir)

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Server never becomes ready
        runtime.is_server_ready = Mock(return_value=False)

        with pytest.raises(RuntimeError, match="failed to become ready"):
            runtime.start_server(timeout=1)  # Short timeout for test

    @patch('llf.llm_runtime.subprocess.Popen')
    def test_start_server_process_terminates(self, mock_popen, runtime, temp_dir):
        """Test server start when process terminates unexpectedly."""
        # Setup
        runtime.model_manager.is_model_downloaded = Mock(return_value=True)
        runtime.config.llama_server_path.parent.mkdir(parents=True, exist_ok=True)
        runtime.config.llama_server_path.touch()

        model_dir = temp_dir / "models" / "test--model"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_file = model_dir / "test-model.gguf"
        model_file.touch()

        runtime.model_manager.get_model_path = Mock(return_value=model_dir)

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process terminated
        mock_process.stderr = MagicMock()
        mock_process.stderr.read.return_value = "Error output"
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError, match="terminated unexpectedly"):
            runtime.start_server()

    def test_stop_server_no_process(self, runtime):
        """Test stop_server when no process running."""
        runtime.stop_server()
        # Should not raise exception

    def test_stop_server_graceful(self, runtime):
        """Test graceful server shutdown."""
        mock_process = MagicMock()
        mock_process.wait = Mock()
        runtime.server_process = mock_process

        runtime.stop_server()

        mock_process.send_signal.assert_called_once()
        mock_process.wait.assert_called_once()
        assert runtime.server_process is None

    def test_stop_server_force_kill(self, runtime):
        """Test force kill when graceful shutdown fails."""
        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired('cmd', 10)
        runtime.server_process = mock_process

        runtime.stop_server()

        mock_process.kill.assert_called_once()
        assert runtime.server_process is None

    def test_generate_no_server(self, runtime):
        """Test generate fails when server not running."""
        with pytest.raises(RuntimeError, match="llama-server is not running"):
            runtime.generate("test prompt")

    @patch('llf.llm_runtime.OpenAI')
    def test_generate_success(self, mock_openai_class, runtime):
        """Test successful generation."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Generated text")]
        mock_client.completions.create.return_value = mock_response
        runtime.client = mock_client

        result = runtime.generate("test prompt")

        assert result == "Generated text"
        mock_client.completions.create.assert_called_once()

    @patch('llf.llm_runtime.OpenAI')
    def test_generate_with_params(self, mock_openai_class, runtime):
        """Test generation with custom parameters."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(text="Generated text")]
        mock_client.completions.create.return_value = mock_response
        runtime.client = mock_client

        result = runtime.generate("test prompt", temperature=0.5, max_tokens=100)

        call_args = mock_client.completions.create.call_args
        assert call_args[1]['temperature'] == 0.5
        assert call_args[1]['max_tokens'] == 100

    @patch('llf.llm_runtime.OpenAI')
    def test_generate_failure(self, mock_openai_class, runtime):
        """Test generation failure."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()
        mock_client.completions.create.side_effect = Exception("API Error")
        runtime.client = mock_client

        with pytest.raises(RuntimeError, match="Failed to generate completion"):
            runtime.generate("test prompt")

    def test_chat_no_server(self, runtime):
        """Test chat fails when server not running."""
        with pytest.raises(RuntimeError, match="llama-server is not running"):
            runtime.chat([{"role": "user", "content": "Hello"}])

    @patch('llf.llm_runtime.OpenAI')
    def test_chat_success(self, mock_openai_class, runtime):
        """Test successful chat."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock(content="Response text")
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        result = runtime.chat(messages)

        assert result == "Response text"
        mock_client.chat.completions.create.assert_called_once()

    @patch('llf.llm_runtime.OpenAI')
    def test_chat_with_params(self, mock_openai_class, runtime):
        """Test chat with custom parameters."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock(content="Response text")
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        result = runtime.chat(messages, temperature=0.3, top_p=0.95)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['top_p'] == 0.95

    @patch('llf.llm_runtime.OpenAI')
    def test_chat_streaming(self, mock_openai_class, runtime):
        """Test chat with streaming enabled."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()

        # Mock streaming response chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " world"

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = "!"

        mock_client.chat.completions.create.return_value = [chunk1, chunk2, chunk3]
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        stream = runtime.chat(messages, stream=True)

        # Collect streamed chunks
        chunks = list(stream)
        assert chunks == ["Hello", " world", "!"]

        # Verify stream parameter was passed
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['stream'] is True

    @patch('llf.llm_runtime.OpenAI')
    def test_chat_streaming_with_none_content(self, mock_openai_class, runtime):
        """Test chat streaming handles chunks with no content."""
        runtime.server_process = MagicMock()
        runtime.server_process.poll.return_value = None

        mock_client = MagicMock()

        # Mock streaming response with some None content chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = None  # Empty chunk

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "Hello"

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None  # Empty chunk

        mock_client.chat.completions.create.return_value = [chunk1, chunk2, chunk3]
        runtime.client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        stream = runtime.chat(messages, stream=True)

        # Should only yield non-None chunks
        chunks = list(stream)
        assert chunks == ["Hello"]

    def test_context_manager(self, runtime):
        """Test context manager stops server on exit."""
        runtime.stop_server = Mock()

        with runtime:
            pass

        runtime.stop_server.assert_called_once()

    def test_list_models_success(self, runtime):
        """Test listing models successfully."""
        # Mock the OpenAI client
        mock_client = MagicMock()

        # Mock model objects
        mock_model1 = MagicMock()
        mock_model1.id = "gpt-4"
        mock_model1.object = "model"
        mock_model1.created = 1687882410
        mock_model1.owned_by = "openai"

        mock_model2 = MagicMock()
        mock_model2.id = "gpt-3.5-turbo"
        mock_model2.object = "model"
        mock_model2.created = 1677610602
        mock_model2.owned_by = "openai"

        # Mock the models.list() response
        mock_response = MagicMock()
        mock_response.data = [mock_model1, mock_model2]
        mock_client.models.list.return_value = mock_response

        runtime.client = mock_client

        models = runtime.list_models()

        assert len(models) == 2
        assert models[0]['id'] == "gpt-4"
        assert models[0]['object'] == "model"
        assert models[0]['owned_by'] == "openai"
        assert models[1]['id'] == "gpt-3.5-turbo"

    def test_list_models_empty(self, runtime):
        """Test listing models when none available."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.models.list.return_value = mock_response

        runtime.client = mock_client

        models = runtime.list_models()

        assert len(models) == 0

    def test_list_models_initializes_client(self, runtime):
        """Test that list_models initializes client if needed."""
        runtime.client = None
        runtime._initialize_client = Mock()

        # Mock the client after initialization
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.models.list.return_value = mock_response

        def init_client():
            runtime.client = mock_client
        runtime._initialize_client.side_effect = init_client

        models = runtime.list_models()

        runtime._initialize_client.assert_called_once()
        assert models == []

    def test_list_models_failure(self, runtime):
        """Test list_models when API call fails."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("API Error")

        runtime.client = mock_client

        with pytest.raises(RuntimeError, match="Failed to list models"):
            runtime.list_models()

"""
Unit tests for multi-server configuration.
"""

import json
import pytest
from pathlib import Path
from llf.config import Config, ServerConfig


class TestMultiServerConfig:
    """Test multi-server configuration loading and management."""

    def test_multi_server_configuration(self, tmp_path):
        """Test loading multiple servers from config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "qwen-coder",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "healthcheck_interval": 2.0,
                    "model_dir": "Qwen--Qwen3-Coder",
                    "gguf_file": "qwen.gguf",
                    "auto_start": True
                },
                {
                    "name": "llama-3",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "healthcheck_interval": 2.0,
                    "model_dir": "Llama-3-8B",
                    "gguf_file": "llama3.gguf",
                    "auto_start": False
                }
            ],
            "llm_endpoint": {
                "default_local_server": "qwen-coder",
                "api_base_url": "http://127.0.0.1:8000/v1",
                "api_key": "EMPTY",
                "model_name": "Qwen3-Coder"
            }
        }))

        config = Config(config_file)

        # Check servers are loaded
        assert len(config.servers) == 2
        assert "qwen-coder" in config.servers
        assert "llama-3" in config.servers

        # Check server details
        qwen = config.servers["qwen-coder"]
        assert qwen.server_port == 8000
        assert qwen.gguf_file == "qwen.gguf"
        assert qwen.auto_start == True

        llama = config.servers["llama-3"]
        assert llama.server_port == 8001
        assert llama.gguf_file == "llama3.gguf"
        assert llama.auto_start == False

        # Check default_local_server
        assert config.default_local_server == "qwen-coder"

    def test_get_server_by_name(self, tmp_path):
        """Test retrieving server by name."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000,
                    "gguf_file": "model1.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8001,
                    "gguf_file": "model2.gguf"
                }
            ]
        }))

        config = Config(config_file)

        server1 = config.get_server_by_name("server1")
        assert server1 is not None
        assert server1.server_port == 8000

        server2 = config.get_server_by_name("server2")
        assert server2 is not None
        assert server2.server_port == 8001

        # Non-existent server
        server3 = config.get_server_by_name("server3")
        assert server3 is None

    def test_get_server_by_port(self, tmp_path):
        """Test retrieving server by port number."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000,
                    "gguf_file": "model1.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8001,
                    "gguf_file": "model2.gguf"
                }
            ]
        }))

        config = Config(config_file)

        server = config.get_server_by_port(8000)
        assert server is not None
        assert server.name == "server1"

        server = config.get_server_by_port(8001)
        assert server is not None
        assert server.name == "server2"

        # Non-existent port
        server = config.get_server_by_port(9999)
        assert server is None

    def test_get_active_server_with_default(self, tmp_path):
        """Test getting active server when default_local_server is set."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "qwen",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000,
                    "gguf_file": "qwen.gguf"
                },
                {
                    "name": "llama",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8001,
                    "gguf_file": "llama.gguf"
                }
            ],
            "llm_endpoint": {
                "default_local_server": "llama",
                "api_base_url": "http://127.0.0.1:8001/v1"
            }
        }))

        config = Config(config_file)

        active = config.get_active_server()
        assert active is not None
        assert active.name == "llama"
        assert active.server_port == 8001

    def test_list_servers(self, tmp_path):
        """Test listing all server names."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {"name": "s1", "llama_server_path": "/usr/bin/llama-server", "server_port": 8000},
                {"name": "s2", "llama_server_path": "/usr/bin/llama-server", "server_port": 8001},
                {"name": "s3", "llama_server_path": "/usr/bin/llama-server", "server_port": 8002}
            ]
        }))

        config = Config(config_file)

        servers = config.list_servers()
        assert len(servers) == 3
        assert "s1" in servers
        assert "s2" in servers
        assert "s3" in servers

    def test_update_default_server(self, tmp_path):
        """Test updating the default server."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8000,
                    "gguf_file": "model1.gguf"
                },
                {
                    "name": "server2",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_host": "127.0.0.1",
                    "server_port": 8001,
                    "gguf_file": "model2.gguf"
                }
            ],
            "llm_endpoint": {
                "default_local_server": "server1",
                "api_base_url": "http://127.0.0.1:8000/v1"
            }
        }))

        config = Config(config_file)

        # Initially server1
        assert config.default_local_server == "server1"
        assert config.api_base_url == "http://127.0.0.1:8000/v1"

        # Update to server2
        config.update_default_server("server2")

        assert config.default_local_server == "server2"
        assert config.api_base_url == "http://127.0.0.1:8001/v1"
        assert config.server_port == 8001

    def test_update_default_server_invalid(self, tmp_path):
        """Test updating to non-existent server raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "server1",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000
                }
            ]
        }))

        config = Config(config_file)

        with pytest.raises(ValueError, match="not found in configuration"):
            config.update_default_server("nonexistent")

    def test_to_dict_multi_server(self, tmp_path):
        """Test converting multi-server config to dict."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "s1",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000,
                    "gguf_file": "m1.gguf",
                    "auto_start": True
                },
                {
                    "name": "s2",
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8001,
                    "gguf_file": "m2.gguf",
                    "auto_start": False
                }
            ],
            "llm_endpoint": {
                "default_local_server": "s1",
                "api_base_url": "http://127.0.0.1:8000/v1"
            }
        }))

        config = Config(config_file)
        config_dict = config.to_dict()

        # Check structure
        assert "local_llm_servers" in config_dict
        assert len(config_dict["local_llm_servers"]) == 2

        # Check default_local_server in llm_endpoint
        assert "llm_endpoint" in config_dict
        assert config_dict["llm_endpoint"]["default_local_server"] == "s1"

    def test_missing_server_name_raises_error(self, tmp_path):
        """Test that server without name raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "llama_server_path": "/usr/bin/llama-server",
                    "server_port": 8000
                }
            ]
        }))

        with pytest.raises(ValueError, match="must have a 'name' field"):
            Config(config_file)

    def test_missing_llama_server_path_raises_error(self, tmp_path):
        """Test that server without llama_server_path raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": [
                {
                    "name": "server1",
                    "server_port": 8000
                }
            ]
        }))

        with pytest.raises(ValueError, match="missing 'llama_server_path'"):
            Config(config_file)

    def test_invalid_servers_array_raises_error(self, tmp_path):
        """Test that non-array local_llm_servers raises error."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "local_llm_servers": "not an array"
        }))

        with pytest.raises(ValueError, match="must be an array"):
            Config(config_file)

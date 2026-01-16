"""
Additional tests for GUI module - Phases 1-4 (Coverage improvement).

Phase 1: Error branches and simple conditionals
Phase 2: Module management (enable/disable)
Phase 3: Datastore operations (attach/detach)
Phase 4: TTS/STT module loading and reload
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from llf.gui import LLMFrameworkGUI
from llf.config import Config
from llf.prompt_config import PromptConfig


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config for testing."""
    config_file = tmp_path / "config.json"
    config_data = {
        "models_dir": str(tmp_path / "models"),
        "external_api": {
            "provider": "openai",
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    config = Config(config_file)
    return config


@pytest.fixture
def mock_prompt_config(tmp_path):
    """Create mock prompt config for testing."""
    config_file = tmp_path / "config_prompt.json"
    config_data = {
        "system_prompt": "Test system prompt",
        "conversation_format": "standard"
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    return PromptConfig(config_file)


@pytest.fixture
def gui(mock_config, mock_prompt_config):
    """Create GUI instance for testing."""
    with patch.object(LLMFrameworkGUI, '_load_modules'):
        gui_instance = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)
        gui_instance.tts = None
        gui_instance.stt = None
        return gui_instance


# ============================================================================
# PHASE 1: Error Branches and Simple Conditionals
# ============================================================================

class TestPhase1ErrorBranches:
    """Test error branches and simple conditionals."""

    def test_check_server_on_startup_server_running(self, gui):
        """Test check_server_on_startup when server is running (line 252)."""
        with patch.object(gui.runtime, 'is_server_running') as mock_check:
            mock_check.return_value = True
            with patch.object(gui.config, 'is_using_external_api', return_value=False):
                with patch.object(gui.config, 'has_local_server_config', return_value=True):
                    gui.config.default_local_server = None

                    needs_start, message = gui.check_server_on_startup()

                    assert needs_start is False
                    assert "running" in message.lower()

    def test_save_config_exception(self, gui):
        """Test save_config exception handling (line 874-875)."""
        with patch('builtins.open', side_effect=IOError("Write failed")):
            result = gui.save_config('{"test": "data"}')

            assert "error" in result.lower() or "❌" in result

    def test_save_prompt_config_exception(self, gui):
        """Test save_prompt_config exception handling (line 908-909)."""
        with patch('builtins.open', side_effect=IOError("Write failed")):
            result = gui.save_prompt_config('{"test": "data"}')

            assert "error" in result.lower() or "❌" in result

    def test_backup_config_exception(self, gui):
        """Test backup_config exception handling (line 829-830)."""
        with patch.object(gui.config, 'backup_config') as mock_backup:
            mock_backup.side_effect = Exception("Backup failed")

            result = gui.backup_config()

            assert "error" in result.lower() or "❌" in result


# ============================================================================
# PHASE 2: Module Management (Enable/Disable)
# ============================================================================

class TestPhase2ModuleManagement:
    """Test module enable/disable operations (Lines 1033-1107)."""

    def test_enable_module_no_selection(self, gui, tmp_path):
        """Test enable_module with no module selected (line 1035)."""
        status, info = gui.enable_module("")

        assert "select a module" in status.lower()

    def test_enable_module_success(self, gui, tmp_path):
        """Test successfully enabling a module (lines 1037-1065)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'test_module',
                    'display_name': 'Test Module',
                    'enabled': False,
                    'settings': {}
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'reload_modules', return_value=("Reloaded", Mock(), Mock(), Mock())):
                with patch.object(gui, 'get_module_info', return_value="Module info"):
                    status, info = gui.enable_module("Test Module")

                    assert "✅" in status or "enabled" in status.lower()

                    # Verify registry was updated
                    with open(registry_path, 'r') as f:
                        updated = json.load(f)
                        assert updated['modules'][0]['enabled'] is True

    def test_enable_module_already_enabled(self, gui, tmp_path):
        """Test enabling already enabled module (line 1049)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'test_module',
                    'display_name': 'Test Module',
                    'enabled': True
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_module_info', return_value="Module info"):
                status, info = gui.enable_module("Test Module")

                assert "⚠️" in status or "already enabled" in status.lower()

    def test_enable_module_not_found(self, gui, tmp_path):
        """Test enabling non-existent module (line 1056)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {'modules': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_module_info', return_value="Module info"):
                status, info = gui.enable_module("Nonexistent Module")

                assert "❌" in status or "not found" in status.lower()

    def test_enable_module_exception(self, gui, tmp_path):
        """Test enable_module exception handling (line 1068)."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=IOError("Read failed")):
                with patch.object(gui, 'get_module_info', return_value="Module info"):
                    status, info = gui.enable_module("Test Module")

                    assert "❌" in status or "error" in status.lower()

    def test_disable_module_no_selection(self, gui, tmp_path):
        """Test disable_module with no module selected (line 1074)."""
        status, info = gui.disable_module("")

        assert "select a module" in status.lower()

    def test_disable_module_success(self, gui, tmp_path):
        """Test successfully disabling a module (lines 1076-1104)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'test_module',
                    'display_name': 'Test Module',
                    'enabled': True,
                    'settings': {}
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'reload_modules', return_value=("Reloaded", Mock(), Mock(), Mock())):
                with patch.object(gui, 'get_module_info', return_value="Module info"):
                    status, info = gui.disable_module("Test Module")

                    assert "✅" in status or "disabled" in status.lower()

                    # Verify registry was updated
                    with open(registry_path, 'r') as f:
                        updated = json.load(f)
                        assert updated['modules'][0]['enabled'] is False

    def test_disable_module_already_disabled(self, gui, tmp_path):
        """Test disabling already disabled module (line 1088)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'test_module',
                    'display_name': 'Test Module',
                    'enabled': False
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_module_info', return_value="Module info"):
                status, info = gui.disable_module("Test Module")

                assert "⚠️" in status or "already disabled" in status.lower()

    def test_disable_module_not_found(self, gui, tmp_path):
        """Test disabling non-existent module (line 1095)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {'modules': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_module_info', return_value="Module info"):
                status, info = gui.disable_module("Nonexistent Module")

                assert "❌" in status or "not found" in status.lower()

    def test_disable_module_exception(self, gui, tmp_path):
        """Test disable_module exception handling (line 1107)."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=IOError("Read failed")):
                with patch.object(gui, 'get_module_info', return_value="Module info"):
                    status, info = gui.disable_module("Test Module")

                    assert "❌" in status or "error" in status.lower()


# ============================================================================
# PHASE 3: Datastore Operations (Attach/Detach)
# ============================================================================

class TestPhase3DatastoreOperations:
    """Test datastore attach/detach operations (Lines 1194-1264)."""

    def test_attach_datastore_no_selection(self, gui):
        """Test attach_datastore with no selection (line 1198)."""
        status, info = gui.attach_datastore("")

        assert "select a data store" in status.lower()

    def test_attach_datastore_success(self, gui, tmp_path):
        """Test successfully attaching a datastore (lines 1194-1225)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {
            'data_stores': [
                {
                    'name': 'test_datastore',
                    'display_name': 'Test Datastore',
                    'type': 'chromadb',
                    'attached': False,
                    'path': str(tmp_path / 'test_db')
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.attach_datastore("Test Datastore")

                assert "✅" in status or "attached" in status.lower()

                # Verify registry was updated
                with open(registry_path, 'r') as f:
                    updated = json.load(f)
                    assert updated['data_stores'][0]['attached'] is True

    def test_attach_datastore_already_attached(self, gui, tmp_path):
        """Test attaching already attached datastore (line 1212)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {
            'data_stores': [
                {
                    'name': 'test_datastore',
                    'display_name': 'Test Datastore',
                    'type': 'chromadb',
                    'attached': True
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.attach_datastore("Test Datastore")

                assert "⚠️" in status or "already attached" in status.lower()

    def test_attach_datastore_not_found(self, gui, tmp_path):
        """Test attaching non-existent datastore (line 1219)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {'data_stores': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.attach_datastore("nonexistent")

                assert "❌" in status or "not found" in status.lower()

    def test_attach_datastore_exception(self, gui, tmp_path):
        """Test attach_datastore exception handling (line 1228)."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=IOError("Read failed")):
                with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                    status, info = gui.attach_datastore("test")

                    assert "❌" in status or "error" in status.lower()

    def test_detach_datastore_no_selection(self, gui):
        """Test detach_datastore with no selection (line 1234)."""
        status, info = gui.detach_datastore("")

        assert "select a data store" in status.lower()

    def test_detach_datastore_success(self, gui, tmp_path):
        """Test successfully detaching a datastore (lines 1230-1261)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {
            'data_stores': [
                {
                    'name': 'test_datastore',
                    'display_name': 'Test Datastore',
                    'type': 'chromadb',
                    'attached': True
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.detach_datastore("Test Datastore")

                assert "✅" in status or "detached" in status.lower()

                # Verify registry was updated
                with open(registry_path, 'r') as f:
                    updated = json.load(f)
                    assert updated['data_stores'][0]['attached'] is False

    def test_detach_datastore_not_attached(self, gui, tmp_path):
        """Test detaching not attached datastore (line 1248)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {
            'data_stores': [
                {
                    'name': 'test_datastore',
                    'display_name': 'Test Datastore',
                    'type': 'chromadb',
                    'attached': False
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.detach_datastore("Test Datastore")

                assert "⚠️" in status or "already detached" in status.lower()

    def test_detach_datastore_not_found(self, gui, tmp_path):
        """Test detaching non-existent datastore (line 1255)."""
        data_stores_dir = tmp_path / 'data_stores'
        data_stores_dir.mkdir(parents=True, exist_ok=True)
        registry_path = data_stores_dir / 'data_store_registry.json'

        registry = {'data_stores': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                status, info = gui.detach_datastore("nonexistent")

                assert "❌" in status or "not found" in status.lower()

    def test_detach_datastore_exception(self, gui, tmp_path):
        """Test detach_datastore exception handling (line 1264)."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=IOError("Read failed")):
                with patch.object(gui, 'get_datastore_info', return_value="Datastore info"):
                    status, info = gui.detach_datastore("test")

                    assert "❌" in status or "error" in status.lower()


# ============================================================================
# PHASE 4: TTS/STT Module Loading and Reload
# ============================================================================

class TestPhase4ModuleLoading:
    """Test TTS/STT module loading and reload (Lines 134-172, 181-222)."""

    def test_load_modules_tts_enabled(self, mock_config, mock_prompt_config, tmp_path):
        """Test loading TTS module when enabled (lines 134-153)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'text2speech',
                    'enabled': True,
                    'settings': {
                        'voice_id': 'test_voice',
                        'rate': 180,
                        'volume': 0.8
                    }
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            # Mock the dynamic import
            mock_tts_module = MagicMock()
            mock_tts_instance = Mock()
            mock_tts_module.TextToSpeech.return_value = mock_tts_instance

            with patch.dict('sys.modules', {'text2speech': mock_tts_module}):
                gui = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)

                # Verify TTS was initialized
                assert gui.tts is not None
                mock_tts_module.TextToSpeech.assert_called_once_with(
                    voice_id='test_voice',
                    rate=180,
                    volume=0.8
                )

    def test_load_modules_tts_import_error(self, mock_config, mock_prompt_config, tmp_path):
        """Test TTS loading with import error (lines 151-152)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'text2speech',
                    'enabled': True,
                    'settings': {}
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            # Don't add text2speech to sys.modules - will cause ImportError
            gui = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)

            # Should handle error gracefully
            assert gui.tts is None

    def test_load_modules_stt_enabled(self, mock_config, mock_prompt_config, tmp_path):
        """Test loading STT module when enabled (lines 158-170)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'speech2text',
                    'enabled': True,
                    'settings': {}
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            # Mock the dynamic import
            mock_stt_module = MagicMock()
            mock_stt_instance = Mock()
            mock_stt_module.SpeechToText.return_value = mock_stt_instance

            with patch.dict('sys.modules', {'speech2text': mock_stt_module}):
                gui = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)

                # Verify STT was initialized
                assert gui.stt is not None
                mock_stt_module.SpeechToText.assert_called_once()

    def test_load_modules_registry_error(self, mock_config, mock_prompt_config, tmp_path):
        """Test _load_modules with registry read error (lines 171-172)."""
        with patch('llf.gui.Path') as mock_path:
            # Make registry path not exist
            mock_path.return_value.parent.parent = tmp_path
            # Should not raise exception
            gui = LLMFrameworkGUI(config=mock_config, prompt_config=mock_prompt_config)

            assert gui.tts is None
            assert gui.stt is None

    def test_reload_modules_with_tts_active(self, gui, tmp_path):
        """Test reload_modules when TTS is active (lines 186-191)."""
        # Set up active TTS
        mock_tts = Mock()
        gui.tts = mock_tts

        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {'modules': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path

            status, tts_update, voice_update, stop_update = gui.reload_modules()

            # Should have stopped TTS
            mock_tts.stop.assert_called_once()
            # Should have cleared TTS
            assert gui.tts is None
            assert "⭕" in status or "no modules" in status.lower()

    def test_reload_modules_with_stt_active(self, gui, tmp_path):
        """Test reload_modules when STT is active (lines 194-195)."""
        # Set up active STT
        mock_stt = Mock()
        gui.stt = mock_stt
        gui.listening_mode_active = True

        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {'modules': []}

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path

            status, tts_update, voice_update, stop_update = gui.reload_modules()

            # Should have cleared STT and stopped listening mode
            assert gui.stt is None
            assert gui.listening_mode_active is False

    def test_reload_modules_with_active_modules(self, gui, tmp_path):
        """Test reload_modules with active modules showing success message (lines 207-210)."""
        modules_dir = tmp_path / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        registry_path = modules_dir / 'modules_registry.json'

        registry = {
            'modules': [
                {
                    'name': 'text2speech',
                    'enabled': True,
                    'settings': {}
                }
            ]
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f)

        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            # Mock the dynamic import
            mock_tts_module = MagicMock()
            mock_tts_instance = Mock()
            mock_tts_module.TextToSpeech.return_value = mock_tts_instance

            with patch.dict('sys.modules', {'text2speech': mock_tts_module}):
                status, tts_update, voice_update, stop_update = gui.reload_modules()

                assert "✅" in status or "reloaded" in status.lower()
                assert "Text-to-Speech" in status

    def test_reload_modules_exception_handling(self, gui, tmp_path):
        """Test reload_modules exception handling (lines 220-227)."""
        with patch('llf.gui.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=FileNotFoundError("Registry error")):
                status, tts_update, voice_update, stop_update = gui.reload_modules()

                # When file not found, it returns "no modules" not an error
                assert "⭕" in status or "no modules" in status.lower()

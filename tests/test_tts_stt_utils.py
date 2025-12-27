"""
Tests for TTS/STT utility functions.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

from llf.tts_stt_utils import (
    _load_tts_config,
    _load_stt_config,
    wait_for_tts_clearance
)


class TestLoadTTSConfig:
    """Test _load_tts_config function."""

    def test_load_config_success(self, tmp_path):
        """Test successfully loading TTS config."""
        config_data = {
            "settings": {
                "audio_clearance_buffer_macos": 0.5,
                "audio_clearance_buffer_pyttsx3": 1.0
            }
        }

        modules_path = tmp_path / "modules" / "text2speech"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_tts_config()

        assert result == config_data["settings"]

    def test_load_config_file_not_found(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_tts_config()

        assert result == {}

    def test_load_config_invalid_json(self, tmp_path):
        """Test loading config with invalid JSON."""
        modules_path = tmp_path / "modules" / "text2speech"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        with open(config_file, 'w') as f:
            f.write("invalid json {")

        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_tts_config()

        assert result == {}

    def test_load_config_no_settings_key(self, tmp_path):
        """Test loading config without settings key."""
        config_data = {"other_key": "value"}

        modules_path = tmp_path / "modules" / "text2speech"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_tts_config()

        assert result == {}


class TestLoadSTTConfig:
    """Test _load_stt_config function."""

    def test_load_config_success(self, tmp_path):
        """Test successfully loading STT config."""
        config_data = {
            "settings": {
                "silence_threshold": 500,
                "silence_timeout": 1.5
            }
        }

        modules_path = tmp_path / "modules" / "speech2text"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_stt_config()

        assert result == config_data["settings"]

    def test_load_config_file_not_found(self, tmp_path):
        """Test loading config when file doesn't exist."""
        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            result = _load_stt_config()

        assert result == {}

    def test_load_config_exception(self, tmp_path):
        """Test loading config with exception during read."""
        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = _load_stt_config()

        assert result == {}


class TestWaitForTTSClearance:
    """Test wait_for_tts_clearance function."""

    def test_macos_backend_accurate_timing(self):
        """Test clearance with macOS backend (accurate timing)."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time.return_value = 2.5

        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:

            result = wait_for_tts_clearance(mock_tts, mock_stt, "Hello world")

        # Verify TTS was called
        mock_tts.speak_and_get_clearance_time.assert_called_once_with("Hello world")

        # Verify sleep was called with default buffer (0.5s)
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] == 0.5

        # Verify total time = actual + buffer
        assert result == 3.0  # 2.5 + 0.5

    def test_macos_backend_with_custom_buffer(self):
        """Test macOS backend with custom buffer time."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time.return_value = 1.0

        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:

            result = wait_for_tts_clearance(mock_tts, mock_stt, "Test", macos_buffer=1.5)

        mock_sleep.assert_called_once_with(1.5)
        assert result == 2.5  # 1.0 + 1.5

    def test_pyttsx3_backend_with_verification(self):
        """Test pyttsx3 backend with verification."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time.return_value = 3.0

        mock_stt = Mock()
        mock_stt.wait_for_audio_clearance.return_value = 0.5

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:

            result = wait_for_tts_clearance(mock_tts, mock_stt, "Hello")

        # Verify speak was called
        mock_tts.speak_and_get_clearance_time.assert_called_once_with("Hello")

        # Verify verification was called
        mock_stt.wait_for_audio_clearance.assert_called_once_with(timeout=10.0, startup_delay=0)

        # Verify sleep calls: estimate wait + buffer
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 3.0  # Estimate wait
        assert mock_sleep.call_args_list[1][0][0] == 1.0  # Buffer

        # Total: estimate + verification + buffer
        assert result == 4.5  # 3.0 + 0.5 + 1.0

    def test_pyttsx3_backend_no_audio_detected(self):
        """Test pyttsx3 backend when no audio is detected."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time.return_value = 2.0

        mock_stt = Mock()
        mock_stt.wait_for_audio_clearance.return_value = 0  # No audio detected

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:

            result = wait_for_tts_clearance(mock_tts, mock_stt, "Test")

        # Only estimate wait, no buffer since no audio detected
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args[0][0] == 2.0

        # Total: estimate + 0
        assert result == 2.0

    def test_pyttsx3_backend_with_custom_parameters(self):
        """Test pyttsx3 backend with custom parameters."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time.return_value = 1.5

        mock_stt = Mock()
        mock_stt.wait_for_audio_clearance.return_value = 0.3

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:

            result = wait_for_tts_clearance(
                mock_tts, mock_stt, "Test",
                pyttsx3_buffer=0.5,
                verification_timeout=5.0
            )

        # Verify verification used custom timeout
        mock_stt.wait_for_audio_clearance.assert_called_once_with(timeout=5.0, startup_delay=0)

        # Verify buffer used custom value
        assert mock_sleep.call_args_list[1][0][0] == 0.5

        # Total: 1.5 + 0.3 + 0.5 = 2.3
        assert result == 2.3

    def test_invalid_text_empty_string(self):
        """Test with empty string raises ValueError."""
        mock_tts = Mock()
        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}):

            with pytest.raises(ValueError, match="Invalid text provided"):
                wait_for_tts_clearance(mock_tts, mock_stt, "")

    def test_invalid_text_none(self):
        """Test with None text raises ValueError."""
        mock_tts = Mock()
        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}):

            with pytest.raises(ValueError, match="Invalid text provided"):
                wait_for_tts_clearance(mock_tts, mock_stt, None)

    def test_invalid_text_not_string(self):
        """Test with non-string text raises ValueError."""
        mock_tts = Mock()
        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}):

            with pytest.raises(ValueError, match="Invalid text provided"):
                wait_for_tts_clearance(mock_tts, mock_stt, 123)

    def test_runtime_error_from_tts(self):
        """Test RuntimeError from TTS is propagated."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time.side_effect = RuntimeError("TTS failed")

        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}):

            with pytest.raises(RuntimeError, match="TTS failed"):
                wait_for_tts_clearance(mock_tts, mock_stt, "Test")

    def test_runtime_error_from_stt_verification(self):
        """Test RuntimeError from STT verification is propagated."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time.return_value = 1.0

        mock_stt = Mock()
        mock_stt.wait_for_audio_clearance.side_effect = RuntimeError("STT verification failed")

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}), \
             patch('llf.tts_stt_utils.time.sleep'):

            with pytest.raises(RuntimeError, match="STT verification failed"):
                wait_for_tts_clearance(mock_tts, mock_stt, "Test")

    def test_unexpected_exception_wrapped(self):
        """Test unexpected exceptions are wrapped in RuntimeError."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time.side_effect = KeyError("Unexpected")

        mock_stt = Mock()

        with patch('llf.tts_stt_utils._load_tts_config', return_value={}), \
             patch('llf.tts_stt_utils._load_stt_config', return_value={}):

            with pytest.raises(RuntimeError, match="TTS/STT clearance failed unexpectedly"):
                wait_for_tts_clearance(mock_tts, mock_stt, "Test")

    def test_config_loaded_from_files(self, tmp_path):
        """Test that configuration is loaded from module_info.json files."""
        # Create TTS config
        tts_config = {
            "settings": {
                "audio_clearance_buffer_macos": 0.8,
                "audio_clearance_buffer_pyttsx3": 1.5,
                "audio_verification_timeout": 15.0
            }
        }
        modules_path = tmp_path / "modules" / "text2speech"
        modules_path.mkdir(parents=True)
        with open(modules_path / "module_info.json", 'w') as f:
            json.dump(tts_config, f)

        # Create STT config
        stt_config = {"settings": {}}
        stt_modules_path = tmp_path / "modules" / "speech2text"
        stt_modules_path.mkdir(parents=True)
        with open(stt_modules_path / "module_info.json", 'w') as f:
            json.dump(stt_config, f)

        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time.return_value = 1.0

        mock_stt = Mock()

        with patch('llf.tts_stt_utils.Path') as mock_path, \
             patch('llf.tts_stt_utils.time.sleep') as mock_sleep:
            mock_path.return_value.parent.parent = tmp_path

            result = wait_for_tts_clearance(mock_tts, mock_stt, "Test")

        # Verify custom buffer from config was used
        mock_sleep.assert_called_once_with(0.8)
        assert result == 1.8  # 1.0 + 0.8

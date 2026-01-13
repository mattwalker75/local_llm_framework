"""
Comprehensive edge case tests for TTS/STT utilities to improve coverage.

Tests cover:
- _load_stt_config exception handling (lines 62-64)
- wait_for_tts_clearance ValueError and RuntimeError exception handling (lines 170-171)
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from llf.tts_stt_utils import (
    _load_stt_config,
    wait_for_tts_clearance
)


class TestLoadSTTConfigEdgeCases:
    """Test _load_stt_config edge cases."""

    def test_load_stt_config_exception(self, tmp_path):
        """Test _load_stt_config when exception occurs during loading."""
        modules_path = tmp_path / "modules" / "speech2text"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        # Create invalid JSON that will cause error
        with open(config_file, 'w') as f:
            f.write("invalid json {")

        with patch('llf.tts_stt_utils.Path') as mock_path:
            # Make Path work correctly
            mock_path.return_value.parent.parent = tmp_path
            mock_path.__file__ = str(tmp_path / "llf" / "tts_stt_utils.py")

            result = _load_stt_config()

        # Should return empty dict on exception
        assert result == {}

    def test_load_stt_config_read_error(self, tmp_path):
        """Test _load_stt_config with file read permission error."""
        modules_path = tmp_path / "modules" / "speech2text"
        modules_path.mkdir(parents=True)
        config_file = modules_path / "module_info.json"

        # Create valid config
        config_data = {"settings": {"test": "value"}}
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        with patch('llf.tts_stt_utils.Path') as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            mock_path.__file__ = str(tmp_path / "llf" / "tts_stt_utils.py")

            # Mock open to raise PermissionError
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = _load_stt_config()

        # Should return empty dict on exception
        assert result == {}


class TestWaitForTTSClearanceEdgeCases:
    """Test wait_for_tts_clearance edge cases."""

    def test_clearance_value_error(self):
        """Test wait_for_tts_clearance when ValueError is raised."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time = Mock(side_effect=ValueError("Invalid duration"))

        mock_stt = Mock()

        with pytest.raises(ValueError, match="Invalid duration"):
            wait_for_tts_clearance(mock_tts, mock_stt, "test text")

    def test_clearance_runtime_error(self):
        """Test wait_for_tts_clearance when RuntimeError is raised."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time = Mock(side_effect=RuntimeError("Speech failed"))

        mock_stt = Mock()

        with pytest.raises(RuntimeError, match="Speech failed"):
            wait_for_tts_clearance(mock_tts, mock_stt, "test text")

    def test_clearance_unexpected_exception(self):
        """Test wait_for_tts_clearance with unexpected exception."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = True
        mock_tts.speak_and_get_clearance_time = Mock(side_effect=Exception("Unexpected error"))

        mock_stt = Mock()

        with pytest.raises(RuntimeError, match="TTS/STT clearance failed unexpectedly"):
            wait_for_tts_clearance(mock_tts, mock_stt, "test text")

    def test_clearance_value_error_pyttsx3_backend(self):
        """Test wait_for_tts_clearance ValueError with pyttsx3 backend."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time = Mock(side_effect=ValueError("Invalid text"))

        mock_stt = Mock()

        with pytest.raises(ValueError, match="Invalid text"):
            wait_for_tts_clearance(mock_tts, mock_stt, "test text")

    def test_clearance_runtime_error_pyttsx3_backend(self):
        """Test wait_for_tts_clearance RuntimeError with pyttsx3 backend."""
        mock_tts = Mock()
        mock_tts.uses_accurate_timing = False
        mock_tts.speak_and_get_clearance_time = Mock(side_effect=RuntimeError("Audio system error"))

        mock_stt = Mock()

        with pytest.raises(RuntimeError, match="Audio system error"):
            wait_for_tts_clearance(mock_tts, mock_stt, "test text")

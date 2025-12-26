"""
Unit tests for the text2speech module.

Run with:
    pytest tests/test_text2speech_module.py -v
    pytest tests/test_text2speech_module.py -v --cov=modules/text2speech --cov-report=term-missing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add modules directory to path to import the text2speech module
sys.path.insert(0, str(Path(__file__).parent.parent / 'modules'))

from text2speech import TextToSpeech


class TestTextToSpeechInitialization:
    """Test TextToSpeech initialization."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_initialization_default_settings(self, mock_pyttsx3_init):
        """Test initialization with default settings."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Should initialize pyttsx3
        mock_pyttsx3_init.assert_called_once()

        # Should set default rate (200)
        mock_engine.setProperty.assert_any_call('rate', 200)

        # Should set default volume (1.0)
        mock_engine.setProperty.assert_any_call('volume', 1.0)

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_initialization_custom_settings(self, mock_pyttsx3_init):
        """Test initialization with custom settings."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech(voice_id="test-voice", rate=150, volume=0.5)

        # Should set custom voice
        mock_engine.setProperty.assert_any_call('voice', 'test-voice')

        # Should set custom rate
        mock_engine.setProperty.assert_any_call('rate', 150)

        # Should set custom volume
        mock_engine.setProperty.assert_any_call('volume', 0.5)

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_initialization_error_handling(self, mock_pyttsx3_init):
        """Test initialization error handling."""
        mock_pyttsx3_init.side_effect = Exception("Init failed")

        with pytest.raises(Exception) as exc_info:
            TextToSpeech()

        assert "Init failed" in str(exc_info.value)


class TestTextToSpeechSpeak:
    """Test TextToSpeech speak method."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_speak_basic(self, mock_pyttsx3_init):
        """Test basic speak functionality."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        tts.speak("Hello, world!")

        # Should call say with the text
        mock_engine.say.assert_called_once_with("Hello, world!")

        # Should call runAndWait for blocking mode
        mock_engine.runAndWait.assert_called_once()

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_speak_empty_string(self, mock_pyttsx3_init):
        """Test speak with empty string."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        tts.speak("")

        # Should not call say for empty string
        mock_engine.say.assert_not_called()

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_speak_whitespace_only(self, mock_pyttsx3_init):
        """Test speak with whitespace only."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        tts.speak("   ")

        # Should not call say for whitespace only
        mock_engine.say.assert_not_called()

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_speak_error_handling(self, mock_pyttsx3_init):
        """Test speak error handling."""
        mock_engine = Mock()
        mock_engine.say.side_effect = Exception("Speech error")
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        with pytest.raises(Exception) as exc_info:
            tts.speak("Test")

        assert "Speech error" in str(exc_info.value)


class TestTextToSpeechVoices:
    """Test TextToSpeech voice management."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_get_available_voices(self, mock_pyttsx3_init):
        """Test getting available voices."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        # Create mock voices
        mock_voice1 = Mock()
        mock_voice1.id = "voice1"
        mock_voice1.name = "Voice One"
        mock_voice1.languages = ["en_US"]

        mock_voice2 = Mock()
        mock_voice2.id = "voice2"
        mock_voice2.name = "Voice Two"
        mock_voice2.languages = ["es_ES"]

        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]

        tts = TextToSpeech()
        voices = tts.get_available_voices()

        # Should return list of voice dictionaries
        assert len(voices) == 2
        assert voices[0]['id'] == "voice1"
        assert voices[0]['name'] == "Voice One"
        assert voices[0]['languages'] == ["en_US"]
        assert voices[1]['id'] == "voice2"
        assert voices[1]['name'] == "Voice Two"

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_get_available_voices_no_languages_attribute(self, mock_pyttsx3_init):
        """Test getting voices when voice object has no languages attribute."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        mock_voice = Mock(spec=['id', 'name'])  # No 'languages' attribute
        mock_voice.id = "voice1"
        mock_voice.name = "Voice One"

        mock_engine.getProperty.return_value = [mock_voice]

        tts = TextToSpeech()
        voices = tts.get_available_voices()

        # Should handle missing languages attribute
        assert len(voices) == 1
        assert voices[0]['languages'] == []

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_get_available_voices_error(self, mock_pyttsx3_init):
        """Test error handling when getting voices."""
        mock_engine = Mock()
        mock_engine.getProperty.side_effect = Exception("Voice error")
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        voices = tts.get_available_voices()

        # Should return empty list on error
        assert voices == []

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_voice_success(self, mock_pyttsx3_init):
        """Test setting voice successfully."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        result = tts.set_voice("new-voice-id")

        # Should call setProperty with voice
        mock_engine.setProperty.assert_called_with('voice', 'new-voice-id')

        # Should return True on success
        assert result is True

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_voice_error(self, mock_pyttsx3_init):
        """Test error handling when setting voice."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Now make setProperty fail for voice setting
        mock_engine.setProperty.side_effect = Exception("Set voice error")

        result = tts.set_voice("invalid-voice")

        # Should return False on error
        assert result is False


class TestTextToSpeechSettings:
    """Test TextToSpeech settings methods."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_rate_success(self, mock_pyttsx3_init):
        """Test setting rate successfully."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        result = tts.set_rate(150)

        # Should call setProperty with rate
        mock_engine.setProperty.assert_called_with('rate', 150)

        # Should return True on success
        assert result is True

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_rate_error(self, mock_pyttsx3_init):
        """Test error handling when setting rate."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Now make setProperty fail for rate setting
        mock_engine.setProperty.side_effect = Exception("Set rate error")

        result = tts.set_rate(200)

        # Should return False on error
        assert result is False

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_volume_success(self, mock_pyttsx3_init):
        """Test setting volume successfully."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        result = tts.set_volume(0.8)

        # Should call setProperty with volume
        mock_engine.setProperty.assert_called_with('volume', 0.8)

        # Should return True on success
        assert result is True

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_volume_invalid_range(self, mock_pyttsx3_init):
        """Test setting volume with invalid range."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Test volume > 1.0
        result = tts.set_volume(1.5)
        assert result is False

        # Test volume < 0.0
        result = tts.set_volume(-0.5)
        assert result is False

        # Should not have called setProperty
        # (called 2 times during init, but not for invalid volumes)
        assert mock_engine.setProperty.call_count == 2

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_set_volume_error(self, mock_pyttsx3_init):
        """Test error handling when setting volume."""
        mock_engine = Mock()
        # Make it succeed during init but fail when called directly
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 2:  # Fail after init calls
                raise Exception("Set volume error")

        mock_engine.setProperty.side_effect = side_effect
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        result = tts.set_volume(0.5)

        # Should return False on error
        assert result is False


class TestTextToSpeechStop:
    """Test TextToSpeech stop method."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_stop_success(self, mock_pyttsx3_init):
        """Test stopping speech successfully."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()
        tts.stop()

        # Should call engine.stop()
        mock_engine.stop.assert_called_once()

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_stop_error_handling(self, mock_pyttsx3_init):
        """Test error handling when stopping."""
        mock_engine = Mock()
        mock_engine.stop.side_effect = Exception("Stop error")
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Should not raise exception
        tts.stop()


class TestTextToSpeechCleanup:
    """Test TextToSpeech cleanup."""

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_destructor_cleanup(self, mock_pyttsx3_init):
        """Test destructor calls stop."""
        mock_engine = Mock()
        mock_pyttsx3_init.return_value = mock_engine

        tts = TextToSpeech()

        # Call destructor
        tts.__del__()

        # Should call stop
        mock_engine.stop.assert_called()

    @patch('text2speech.tts_engine.pyttsx3.init')
    def test_destructor_no_engine(self, mock_pyttsx3_init):
        """Test destructor when engine doesn't exist."""
        mock_pyttsx3_init.return_value = Mock()

        tts = TextToSpeech()
        del tts.engine  # Remove engine attribute

        # Should not raise exception
        tts.__del__()


class TestModuleImport:
    """Test module import."""

    def test_module_import(self):
        """Test that the module can be imported."""
        from text2speech import TextToSpeech

        assert TextToSpeech is not None

    def test_module_version(self):
        """Test that the module has a version."""
        import text2speech

        assert hasattr(text2speech, '__version__')
        assert text2speech.__version__ == "0.1.0"

    def test_module_all(self):
        """Test that __all__ exports TextToSpeech."""
        import text2speech

        assert hasattr(text2speech, '__all__')
        assert 'TextToSpeech' in text2speech.__all__

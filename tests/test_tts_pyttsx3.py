"""
Unit tests for text2speech/tts_pyttsx3.py module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging


@pytest.fixture
def mock_pyttsx3_engine():
    """Create a mock pyttsx3 engine."""
    mock_engine = MagicMock()
    mock_engine.setProperty = Mock()
    mock_engine.say = Mock()
    mock_engine.runAndWait = Mock()
    mock_engine.stop = Mock()
    mock_engine.getProperty = Mock(return_value=[])
    return mock_engine


@pytest.fixture
def mock_pyttsx3_init(mock_pyttsx3_engine):
    """Mock pyttsx3.init() to return mock engine."""
    with patch('pyttsx3.init', return_value=mock_pyttsx3_engine):
        yield mock_pyttsx3_engine


class TestPyttsx3TTSInitialization:
    """Test Pyttsx3TTS initialization."""

    def test_default_initialization(self, mock_pyttsx3_init):
        """Test initialization with default parameters."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()

        assert tts.rate == 200
        assert tts.volume == 1.0
        assert tts.voice_id is None
        mock_pyttsx3_init.setProperty.assert_any_call('rate', 200)
        mock_pyttsx3_init.setProperty.assert_any_call('volume', 1.0)

    def test_custom_initialization(self, mock_pyttsx3_init):
        """Test initialization with custom parameters."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS(voice_id="test_voice", rate=150, volume=0.8)

        assert tts.rate == 150
        assert tts.volume == 0.8
        assert tts.voice_id == "test_voice"
        mock_pyttsx3_init.setProperty.assert_any_call('voice', 'test_voice')
        mock_pyttsx3_init.setProperty.assert_any_call('rate', 150)
        mock_pyttsx3_init.setProperty.assert_any_call('volume', 0.8)

    def test_initialization_failure(self):
        """Test that initialization failure is handled."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        with patch('pyttsx3.init', side_effect=Exception("Init failed")):
            with pytest.raises(Exception, match="Init failed"):
                Pyttsx3TTS()

    def test_voice_not_set_when_none(self, mock_pyttsx3_init):
        """Test that voice is not set when voice_id is None."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS(voice_id=None)

        # Verify setProperty was NOT called with 'voice'
        voice_calls = [call for call in mock_pyttsx3_init.setProperty.call_args_list
                       if call[0][0] == 'voice']
        assert len(voice_calls) == 0


class TestPyttsx3TTSSpeak:
    """Test speak method."""

    def test_speak_blocking(self, mock_pyttsx3_init):
        """Test speak with blocking mode."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.speak("Hello world", block=True)

        mock_pyttsx3_init.say.assert_called_once_with("Hello world")
        mock_pyttsx3_init.runAndWait.assert_called_once()

    def test_speak_non_blocking(self, mock_pyttsx3_init):
        """Test speak with non-blocking mode (still blocks in pyttsx3)."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.speak("Hello world", block=False)

        mock_pyttsx3_init.say.assert_called_once_with("Hello world")
        # Should still call runAndWait because pyttsx3 requires it
        mock_pyttsx3_init.runAndWait.assert_called_once()

    def test_speak_empty_text(self, mock_pyttsx3_init):
        """Test speak with empty text."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.speak("")

        # Should not call say or runAndWait
        mock_pyttsx3_init.say.assert_not_called()
        mock_pyttsx3_init.runAndWait.assert_not_called()

    def test_speak_whitespace_only(self, mock_pyttsx3_init):
        """Test speak with whitespace-only text."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.speak("   ")

        # Should not call say or runAndWait
        mock_pyttsx3_init.say.assert_not_called()
        mock_pyttsx3_init.runAndWait.assert_not_called()

    def test_speak_error(self, mock_pyttsx3_init):
        """Test speak when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        mock_pyttsx3_init.runAndWait.side_effect = Exception("Speech failed")

        tts = Pyttsx3TTS()

        with pytest.raises(Exception, match="Speech failed"):
            tts.speak("Hello")


class TestPyttsx3TTSSpeakAndGetClearanceTime:
    """Test speak_and_get_clearance_time method."""

    def test_clearance_time_calculation(self, mock_pyttsx3_init):
        """Test clearance time calculation based on word count."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS(rate=200)  # 200 words per minute

        # Text with 10 words should take 3 seconds (10 / 200 * 60)
        text = "one two three four five six seven eight nine ten"

        with patch('time.time', side_effect=[0.0, 0.1]):  # runAndWait takes 0.1s
            clearance_time = tts.speak_and_get_clearance_time(text)

        expected_time = (10 / 200) * 60  # 3.0 seconds
        assert clearance_time == expected_time

    def test_clearance_time_custom_rate(self, mock_pyttsx3_init):
        """Test clearance time with custom rate."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS(rate=100)  # 100 words per minute

        text = "one two three four five"  # 5 words

        with patch('time.time', side_effect=[0.0, 0.1]):
            clearance_time = tts.speak_and_get_clearance_time(text)

        expected_time = (5 / 100) * 60  # 3.0 seconds
        assert clearance_time == expected_time

    def test_clearance_time_empty_text(self, mock_pyttsx3_init):
        """Test clearance time with empty text."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        clearance_time = tts.speak_and_get_clearance_time("")

        assert clearance_time == 0.0

    def test_clearance_time_on_error(self, mock_pyttsx3_init):
        """Test clearance time when speak raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        mock_pyttsx3_init.runAndWait.side_effect = Exception("Error")

        tts = Pyttsx3TTS()
        clearance_time = tts.speak_and_get_clearance_time("test")

        # Should return safe default of 0.5 on error
        assert clearance_time == 0.5


class TestPyttsx3TTSGetAvailableVoices:
    """Test get_available_voices method."""

    def test_get_voices_success(self, mock_pyttsx3_init):
        """Test getting available voices."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        # Create mock voice objects
        mock_voice1 = Mock()
        mock_voice1.id = "voice1"
        mock_voice1.name = "Voice 1"
        mock_voice1.languages = ["en_US"]

        mock_voice2 = Mock()
        mock_voice2.id = "voice2"
        mock_voice2.name = "Voice 2"
        mock_voice2.languages = ["es_ES"]

        mock_pyttsx3_init.getProperty.return_value = [mock_voice1, mock_voice2]

        tts = Pyttsx3TTS()
        voices = tts.get_available_voices()

        assert len(voices) == 2
        assert voices[0]['id'] == "voice1"
        assert voices[0]['name'] == "Voice 1"
        assert voices[0]['languages'] == ["en_US"]
        assert voices[1]['id'] == "voice2"

    def test_get_voices_no_languages_attribute(self, mock_pyttsx3_init):
        """Test getting voices when voice object has no languages attribute."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        mock_voice = Mock(spec=['id', 'name'])  # No 'languages' attribute
        mock_voice.id = "voice1"
        mock_voice.name = "Voice 1"

        mock_pyttsx3_init.getProperty.return_value = [mock_voice]

        tts = Pyttsx3TTS()
        voices = tts.get_available_voices()

        assert len(voices) == 1
        assert voices[0]['languages'] == []

    def test_get_voices_error(self, mock_pyttsx3_init):
        """Test get_available_voices when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        mock_pyttsx3_init.getProperty.side_effect = Exception("Error")

        tts = Pyttsx3TTS()
        voices = tts.get_available_voices()

        assert voices == []


class TestPyttsx3TTSSetVoice:
    """Test set_voice method."""

    def test_set_voice_success(self, mock_pyttsx3_init):
        """Test setting voice successfully."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        result = tts.set_voice("new_voice")

        assert result is True
        # Called once in __init__ and once in set_voice
        voice_calls = [call for call in mock_pyttsx3_init.setProperty.call_args_list
                       if call[0][0] == 'voice']
        assert voice_calls[-1][0][1] == "new_voice"

    def test_set_voice_error(self, mock_pyttsx3_init):
        """Test set_voice when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        mock_pyttsx3_init.setProperty.side_effect = Exception("Error")

        result = tts.set_voice("voice_id")

        assert result is False


class TestPyttsx3TTSSetRate:
    """Test set_rate method."""

    def test_set_rate_success(self, mock_pyttsx3_init):
        """Test setting rate successfully."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        result = tts.set_rate(150)

        assert result is True
        assert tts.rate == 150
        # Verify setProperty was called with new rate
        rate_calls = [call for call in mock_pyttsx3_init.setProperty.call_args_list
                      if call[0][0] == 'rate']
        assert rate_calls[-1][0][1] == 150

    def test_set_rate_error(self, mock_pyttsx3_init):
        """Test set_rate when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        mock_pyttsx3_init.setProperty.side_effect = Exception("Error")

        result = tts.set_rate(150)

        assert result is False


class TestPyttsx3TTSSetVolume:
    """Test set_volume method."""

    def test_set_volume_success(self, mock_pyttsx3_init):
        """Test setting volume successfully."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        result = tts.set_volume(0.5)

        assert result is True
        assert tts.volume == 0.5
        # Verify setProperty was called with new volume
        volume_calls = [call for call in mock_pyttsx3_init.setProperty.call_args_list
                        if call[0][0] == 'volume']
        assert volume_calls[-1][0][1] == 0.5

    def test_set_volume_invalid_range(self, mock_pyttsx3_init):
        """Test setting volume with invalid range."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        result = tts.set_volume(1.5)

        assert result is False

    def test_set_volume_negative(self, mock_pyttsx3_init):
        """Test setting volume with negative value."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        result = tts.set_volume(-0.1)

        assert result is False

    def test_set_volume_error(self, mock_pyttsx3_init):
        """Test set_volume when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        mock_pyttsx3_init.setProperty.side_effect = Exception("Error")

        result = tts.set_volume(0.5)

        assert result is False


class TestPyttsx3TTSStop:
    """Test stop method."""

    def test_stop_success(self, mock_pyttsx3_init):
        """Test stopping speech successfully."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.stop()

        mock_pyttsx3_init.stop.assert_called_once()

    def test_stop_error(self, mock_pyttsx3_init):
        """Test stop when engine raises error."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        mock_pyttsx3_init.stop.side_effect = Exception("Error")

        tts = Pyttsx3TTS()
        # Should not raise exception, just log error
        tts.stop()


class TestPyttsx3TTSDestructor:
    """Test __del__ destructor."""

    def test_destructor_cleanup(self, mock_pyttsx3_init):
        """Test that destructor stops engine."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()
        tts.__del__()

        mock_pyttsx3_init.stop.assert_called()

    def test_destructor_no_engine(self):
        """Test destructor when engine doesn't exist."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        with patch('pyttsx3.init', side_effect=Exception("Init failed")):
            try:
                tts = Pyttsx3TTS()
            except:
                pass

        # Should not raise exception even if engine wasn't initialized
        # (This is implicitly tested by the exception handler in __del__)


class TestPyttsx3TTSUsesAccurateTiming:
    """Test uses_accurate_timing property."""

    def test_uses_accurate_timing_false(self, mock_pyttsx3_init):
        """Test that pyttsx3 backend returns False for accurate timing."""
        from modules.text2speech.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS()

        # Pyttsx3 uses word-count estimation, not accurate timing
        assert tts.uses_accurate_timing is False

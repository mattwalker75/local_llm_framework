"""
Unit tests for text2speech/tts_macos.py module.

Tests the macOS-specific TTS engine using NSSpeechSynthesizer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import logging


@pytest.fixture
def mock_ns_speech_synthesizer():
    """Create a mock NSSpeechSynthesizer."""
    mock_synth = MagicMock()

    # Mock initialization chain: alloc().init()
    mock_synth.alloc.return_value.init.return_value = mock_synth

    # Mock voice and property setters
    mock_synth.setVoice_ = Mock(return_value=True)
    mock_synth.setVolume_ = Mock()
    mock_synth.setRate_ = Mock()

    # Mock speech methods
    mock_synth.startSpeakingString_ = Mock()
    mock_synth.stopSpeaking = Mock()
    mock_synth.isSpeaking = Mock(return_value=False)

    # Mock voice enumeration
    mock_synth.availableVoices = Mock(return_value=[])
    mock_synth.attributesForVoice_ = Mock(return_value={})

    return mock_synth


@pytest.fixture
def mock_appkit(mock_ns_speech_synthesizer):
    """Mock the AppKit module with NSSpeechSynthesizer."""
    with patch.dict('sys.modules', {'AppKit': MagicMock()}):
        with patch('modules.text2speech.tts_macos.NSSpeechSynthesizer', mock_ns_speech_synthesizer):
            with patch('modules.text2speech.tts_macos.MACOS_TTS_AVAILABLE', True):
                yield mock_ns_speech_synthesizer


class TestMacOSTTSImportGuard:
    """Test import guard behavior."""

    def test_import_unavailable_raises_error(self):
        """Test that ImportError is raised when AppKit is not available."""
        with patch('modules.text2speech.tts_macos.MACOS_TTS_AVAILABLE', False):
            from modules.text2speech.tts_macos import MacOSTTS

            with pytest.raises(ImportError, match="pyobjc-framework-Cocoa is required"):
                MacOSTTS()


class TestMacOSTTSInitialization:
    """Test MacOSTTS initialization."""

    def test_default_initialization(self, mock_appkit):
        """Test initialization with default parameters."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()

        assert tts.rate == 200
        assert tts.volume == 1.0
        assert tts.voice_id is None

        # Verify synthesizer was initialized
        mock_appkit.alloc.assert_called_once()
        mock_appkit.alloc.return_value.init.assert_called_once()

        # Verify properties were set
        mock_appkit.setVolume_.assert_called_once_with(1.0)
        mock_appkit.setRate_.assert_called_once_with(200)

    def test_custom_initialization(self, mock_appkit):
        """Test initialization with custom parameters."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS(voice_id="com.apple.speech.synthesis.voice.samantha", rate=150, volume=0.8)

        assert tts.rate == 150
        assert tts.volume == 0.8
        assert tts.voice_id == "com.apple.speech.synthesis.voice.samantha"

        # Verify voice was set
        mock_appkit.setVoice_.assert_called_once_with("com.apple.speech.synthesis.voice.samantha")
        mock_appkit.setVolume_.assert_called_once_with(0.8)
        mock_appkit.setRate_.assert_called_once_with(150)

    def test_initialization_without_voice(self, mock_appkit):
        """Test that voice is not set when voice_id is None."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS(voice_id=None)

        # Verify setVoice_ was NOT called
        mock_appkit.setVoice_.assert_not_called()

    def test_initialization_failure(self, mock_appkit):
        """Test that initialization failure is handled."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.alloc.return_value.init.side_effect = Exception("Init failed")

        with pytest.raises(Exception, match="Init failed"):
            MacOSTTS()


class TestMacOSTTSUsesAccurateTiming:
    """Test uses_accurate_timing property."""

    def test_uses_accurate_timing_returns_true(self, mock_appkit):
        """Test that macOS backend reports accurate timing."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()

        assert tts.uses_accurate_timing is True


class TestMacOSTTSSpeak:
    """Test speak method."""

    def test_speak_blocking(self, mock_appkit):
        """Test speak with blocking mode."""
        from modules.text2speech.tts_macos import MacOSTTS

        # Mock isSpeaking to return True twice, then False (simulates speech)
        mock_appkit.isSpeaking.side_effect = [True, True, False]

        tts = MacOSTTS()

        with patch('time.sleep'):  # Mock sleep to avoid delays
            tts.speak("Hello world", block=True)

        mock_appkit.startSpeakingString_.assert_called_once_with("Hello world")
        # Should have polled isSpeaking 3 times
        assert mock_appkit.isSpeaking.call_count == 3

    def test_speak_non_blocking(self, mock_appkit):
        """Test speak with non-blocking mode."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        tts.speak("Hello world", block=False)

        mock_appkit.startSpeakingString_.assert_called_once_with("Hello world")
        # Should NOT poll isSpeaking in non-blocking mode
        mock_appkit.isSpeaking.assert_not_called()

    def test_speak_empty_text(self, mock_appkit):
        """Test speak with empty text."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        tts.speak("", block=True)

        # Should not call startSpeakingString_ for empty text
        mock_appkit.startSpeakingString_.assert_not_called()

    def test_speak_whitespace_only(self, mock_appkit):
        """Test speak with whitespace-only text."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        tts.speak("   ", block=True)

        # Should not call startSpeakingString_ for whitespace
        mock_appkit.startSpeakingString_.assert_not_called()

    def test_speak_error_handling(self, mock_appkit):
        """Test error handling during speech."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.startSpeakingString_.side_effect = Exception("Speech error")

        tts = MacOSTTS()

        with pytest.raises(Exception, match="Speech error"):
            tts.speak("Test", block=False)


class TestMacOSTTSSpeakAndGetClearanceTime:
    """Test speak_and_get_clearance_time method."""

    def test_speak_and_get_clearance_time_returns_actual_duration(self, mock_appkit):
        """Test that method returns actual speech duration."""
        from modules.text2speech.tts_macos import MacOSTTS

        # Mock isSpeaking to return False immediately
        mock_appkit.isSpeaking.return_value = False

        tts = MacOSTTS()

        # Mock time.time to simulate 2.5 second duration
        with patch('time.time', side_effect=[0.0, 2.5]):
            with patch('time.sleep'):
                duration = tts.speak_and_get_clearance_time("Hello world")

        assert duration == 2.5
        mock_appkit.startSpeakingString_.assert_called_once_with("Hello world")

    def test_speak_and_get_clearance_time_empty_text(self, mock_appkit):
        """Test with empty text returns 0.0."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        duration = tts.speak_and_get_clearance_time("")

        assert duration == 0.0
        mock_appkit.startSpeakingString_.assert_not_called()

    def test_speak_and_get_clearance_time_whitespace(self, mock_appkit):
        """Test with whitespace returns 0.0."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        duration = tts.speak_and_get_clearance_time("   ")

        assert duration == 0.0
        mock_appkit.startSpeakingString_.assert_not_called()

    def test_speak_and_get_clearance_time_error_handling(self, mock_appkit):
        """Test error handling returns safe default."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.startSpeakingString_.side_effect = Exception("Error")

        tts = MacOSTTS()
        duration = tts.speak_and_get_clearance_time("Test")

        # Should return safe default on error
        assert duration == 0.5


class TestMacOSTTSGetAvailableVoices:
    """Test get_available_voices method."""

    def test_get_available_voices_returns_voice_list(self, mock_appkit):
        """Test getting available voices."""
        from modules.text2speech.tts_macos import MacOSTTS

        # Mock available voices
        mock_voices = [
            "com.apple.speech.synthesis.voice.samantha",
            "com.apple.speech.synthesis.voice.alex"
        ]
        mock_appkit.availableVoices.return_value = mock_voices

        # Mock voice attributes
        def mock_attrs(voice_id):
            if "samantha" in voice_id:
                return {
                    'VoiceName': 'Samantha',
                    'VoiceLanguage': 'en-US'
                }
            else:
                return {
                    'VoiceName': 'Alex',
                    'VoiceLanguage': 'en-US'
                }

        mock_appkit.attributesForVoice_.side_effect = mock_attrs

        tts = MacOSTTS()
        voices = tts.get_available_voices()

        assert len(voices) == 2
        assert voices[0]['id'] == "com.apple.speech.synthesis.voice.samantha"
        assert voices[0]['name'] == "Samantha"
        assert voices[0]['languages'] == ['en-US']
        assert voices[1]['id'] == "com.apple.speech.synthesis.voice.alex"
        assert voices[1]['name'] == "Alex"

    def test_get_available_voices_missing_attributes(self, mock_appkit):
        """Test voice with missing attributes uses defaults."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_voices = ["com.apple.speech.synthesis.voice.test"]
        mock_appkit.availableVoices.return_value = mock_voices

        # Return attributes without VoiceName or VoiceLanguage
        mock_appkit.attributesForVoice_.return_value = {}

        tts = MacOSTTS()
        voices = tts.get_available_voices()

        assert len(voices) == 1
        assert voices[0]['id'] == "com.apple.speech.synthesis.voice.test"
        assert voices[0]['name'] == "com.apple.speech.synthesis.voice.test"  # Falls back to ID
        assert voices[0]['languages'] == ['en-US']  # Default language

    def test_get_available_voices_error_handling(self, mock_appkit):
        """Test error handling returns empty list."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.availableVoices.side_effect = Exception("Error")

        tts = MacOSTTS()
        voices = tts.get_available_voices()

        assert voices == []


class TestMacOSTTSSetVoice:
    """Test set_voice method."""

    def test_set_voice_success(self, mock_appkit):
        """Test setting voice successfully."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.setVoice_.return_value = True

        tts = MacOSTTS()
        result = tts.set_voice("com.apple.speech.synthesis.voice.samantha")

        assert result is True
        assert tts.voice_id == "com.apple.speech.synthesis.voice.samantha"
        mock_appkit.setVoice_.assert_called_with("com.apple.speech.synthesis.voice.samantha")

    def test_set_voice_failure(self, mock_appkit):
        """Test setting voice fails."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.setVoice_.return_value = False

        tts = MacOSTTS()
        result = tts.set_voice("invalid_voice")

        assert result is False

    def test_set_voice_error_handling(self, mock_appkit):
        """Test error handling during set_voice."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.setVoice_.side_effect = Exception("Error")

        tts = MacOSTTS()
        result = tts.set_voice("test_voice")

        assert result is False


class TestMacOSTTSSetRate:
    """Test set_rate method."""

    def test_set_rate_success(self, mock_appkit):
        """Test setting rate successfully."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        result = tts.set_rate(250)

        assert result is True
        assert tts.rate == 250
        mock_appkit.setRate_.assert_called_with(250)

    def test_set_rate_error_handling(self, mock_appkit):
        """Test error handling during set_rate."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        mock_appkit.setRate_.side_effect = Exception("Error")

        result = tts.set_rate(300)

        assert result is False


class TestMacOSTTSSetVolume:
    """Test set_volume method."""

    def test_set_volume_success(self, mock_appkit):
        """Test setting volume successfully."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        result = tts.set_volume(0.5)

        assert result is True
        assert tts.volume == 0.5
        mock_appkit.setVolume_.assert_called_with(0.5)

    def test_set_volume_invalid_too_low(self, mock_appkit):
        """Test setting volume below 0.0 fails."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        result = tts.set_volume(-0.1)

        assert result is False

    def test_set_volume_invalid_too_high(self, mock_appkit):
        """Test setting volume above 1.0 fails."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        result = tts.set_volume(1.5)

        assert result is False

    def test_set_volume_boundary_values(self, mock_appkit):
        """Test boundary values 0.0 and 1.0."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()

        # Test 0.0
        result = tts.set_volume(0.0)
        assert result is True
        assert tts.volume == 0.0

        # Test 1.0
        result = tts.set_volume(1.0)
        assert result is True
        assert tts.volume == 1.0

    def test_set_volume_error_handling(self, mock_appkit):
        """Test error handling during set_volume."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        mock_appkit.setVolume_.side_effect = Exception("Error")

        result = tts.set_volume(0.5)

        assert result is False


class TestMacOSTTSStop:
    """Test stop method."""

    def test_stop_success(self, mock_appkit):
        """Test stopping speech."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        tts.stop()

        mock_appkit.stopSpeaking.assert_called_once()

    def test_stop_error_handling(self, mock_appkit):
        """Test that stop handles errors gracefully."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.stopSpeaking.side_effect = Exception("Error")

        tts = MacOSTTS()
        # Should not raise exception
        tts.stop()


class TestMacOSTTSCleanup:
    """Test cleanup (__del__) behavior."""

    def test_del_calls_stop(self, mock_appkit):
        """Test that __del__ calls stop."""
        from modules.text2speech.tts_macos import MacOSTTS

        tts = MacOSTTS()
        tts.__del__()

        mock_appkit.stopSpeaking.assert_called()

    def test_del_handles_errors_gracefully(self, mock_appkit):
        """Test that __del__ handles errors gracefully."""
        from modules.text2speech.tts_macos import MacOSTTS

        mock_appkit.stopSpeaking.side_effect = Exception("Error")

        tts = MacOSTTS()
        # Should not raise exception
        tts.__del__()

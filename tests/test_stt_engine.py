"""
Unit tests for speech2text/stt_engine.py module.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, mock_open
import logging
import tempfile
import os


# Mock the external dependencies before importing
@pytest.fixture(autouse=True)
def mock_external_libs():
    """Mock sounddevice, whisper, and scipy to avoid real audio/model dependencies."""
    with patch('sounddevice.InputStream'), \
         patch('whisper.load_model'), \
         patch('scipy.io.wavfile.write'):
        yield


@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Hello world"}
    return mock_model


class TestSpeechToTextInitialization:
    """Test SpeechToText initialization and parameter validation."""

    def test_default_initialization(self, mock_whisper_model):
        """Test initialization with default parameters."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText()

            assert stt.sample_rate == 16000
            assert stt.channels == 1
            assert stt.dtype == "int16"
            assert stt.max_duration == 60
            assert stt.silence_timeout == 1.5
            assert stt.silence_threshold == 500
            assert stt.chunk_duration == 0.1
            assert stt.min_speech_duration == 0.3
            assert stt.whisper_language is None
            assert stt.required_silence_duration == 0.5

    def test_custom_initialization(self, mock_whisper_model):
        """Test initialization with custom parameters."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText(
                sample_rate=22050,
                channels=2,
                dtype="float32",
                max_duration=30,
                silence_timeout=2.0,
                silence_threshold=0.5,  # Changed to 0.5 for float32 (must be between 0.0 and 1.0)
                chunk_duration=0.2,
                min_speech_duration=0.5,
                whisper_model="small",
                whisper_language="en",
                required_silence_duration=1.0
            )

            assert stt.sample_rate == 22050
            assert stt.channels == 2
            assert stt.dtype == "float32"
            assert stt.silence_timeout == 2.0
            assert stt.whisper_language == "en"

    def test_invalid_sample_rate_type(self):
        """Test that invalid sample_rate type raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="sample_rate must be an integer"):
            SpeechToText(sample_rate="invalid")

    def test_invalid_sample_rate_range(self):
        """Test that sample_rate out of range raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="sample_rate must be between 8000 and 48000"):
            SpeechToText(sample_rate=5000)

    def test_invalid_channels(self):
        """Test that invalid channels value raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="channels must be 1 \\(mono\\) or 2 \\(stereo\\)"):
            SpeechToText(channels=3)

    def test_invalid_dtype(self):
        """Test that invalid dtype raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="dtype must be one of"):
            SpeechToText(dtype="invalid")

    def test_invalid_max_duration(self):
        """Test that invalid max_duration raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="max_duration must be between 1 and 600"):
            SpeechToText(max_duration=1000)

    def test_invalid_silence_timeout(self):
        """Test that invalid silence_timeout raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="silence_timeout must be between 0.1 and 10.0"):
            SpeechToText(silence_timeout=15.0)

    def test_invalid_silence_threshold_int16(self):
        """Test that invalid silence_threshold for int16 raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="silence_threshold must be between 10 and 32767 for int16"):
            SpeechToText(dtype="int16", silence_threshold=50000)

    def test_invalid_silence_threshold_float32(self):
        """Test that invalid silence_threshold for float32 raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="silence_threshold must be between 0.0 and 1.0 for float32"):
            SpeechToText(dtype="float32", silence_threshold=2.0)

    def test_invalid_chunk_duration(self):
        """Test that invalid chunk_duration raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="chunk_duration must be between 0.01 and 1.0"):
            SpeechToText(chunk_duration=5.0)

    def test_invalid_min_speech_duration(self):
        """Test that invalid min_speech_duration raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="min_speech_duration must be between 0.1 and 5.0"):
            SpeechToText(min_speech_duration=10.0)

    def test_invalid_whisper_model(self):
        """Test that invalid whisper_model raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="whisper_model must be one of"):
            SpeechToText(whisper_model="invalid")

    def test_invalid_whisper_language(self):
        """Test that invalid whisper_language raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="whisper_language must be a valid language code"):
            SpeechToText(whisper_language="x")

    def test_invalid_required_silence_duration(self):
        """Test that invalid required_silence_duration raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="required_silence_duration must be between 0.1 and 5.0"):
            SpeechToText(required_silence_duration=10.0)

    def test_debug_logging_enabled(self, mock_whisper_model):
        """Test that debug_logging parameter sets logger level."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText(debug_logging=True)
            assert stt.logger.level == logging.DEBUG

    def test_log_level_string(self, mock_whisper_model):
        """Test log_level parameter with string value."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText(log_level="WARNING")
            assert stt.logger.level == logging.WARNING

    def test_log_level_int(self, mock_whisper_model):
        """Test log_level parameter with int value."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText(log_level=logging.ERROR)
            assert stt.logger.level == logging.ERROR

    def test_invalid_log_level_string(self):
        """Test that invalid log_level string raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="Invalid log_level string"):
            SpeechToText(log_level="INVALID")

    def test_invalid_log_level_type(self):
        """Test that invalid log_level type raises ValueError."""
        from modules.speech2text.stt_engine import SpeechToText

        with pytest.raises(ValueError, match="log_level must be int or str"):
            SpeechToText(log_level=[])

    def test_whisper_model_loading_failure(self):
        """Test that whisper model loading failure raises RuntimeError."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', side_effect=Exception("Model load failed")):
            with pytest.raises(RuntimeError, match="STT engine initialization failed"):
                SpeechToText()


class TestRecordUntilSilence:
    """Test record_until_silence method."""

    def test_record_with_speech_then_silence(self, mock_whisper_model):
        """Test recording with speech followed by silence."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        # Create mock audio chunks (speech then silence)
        speech_chunk = np.array([[1000], [1000], [1000]], dtype=np.int16)
        silence_chunk = np.array([[100], [100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=[
            (speech_chunk, False),  # Speech detected
            (speech_chunk, False),  # More speech
            (speech_chunk, False),  # More speech
            (silence_chunk, False),  # Start silence
            (silence_chunk, False),  # Continue silence (triggers stop)
        ])

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText(chunk_duration=0.1, min_speech_duration=0.2, silence_timeout=0.15)
            audio_data = stt.record_until_silence()

            assert audio_data is not None
            assert len(audio_data) > 0

    def test_record_buffer_overflow(self, mock_whisper_model):
        """Test recording with buffer overflow warning."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        chunk = np.array([[1000], [1000]], dtype=np.int16)
        silence_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=[
            (chunk, True),  # Overflow
            (chunk, False),
            (silence_chunk, False),
            (silence_chunk, False),
        ])

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText(chunk_duration=0.1, min_speech_duration=0.1, silence_timeout=0.1)
            audio_data = stt.record_until_silence()

            assert audio_data is not None

    def test_record_no_audio_captured(self, mock_whisper_model):
        """Test recording when no audio is captured."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=RuntimeError("No audio"))

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText()

            with pytest.raises(RuntimeError, match="Failed to read audio from microphone"):
                stt.record_until_silence()

    def test_record_portaudio_error(self, mock_whisper_model):
        """Test recording with PortAudio error."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', side_effect=sd.PortAudioError("Device error")):

            stt = SpeechToText()

            with pytest.raises(RuntimeError, match="Audio device error"):
                stt.record_until_silence()


class TestTranscribeAudio:
    """Test transcribe_audio method."""

    def test_transcribe_success(self, mock_whisper_model):
        """Test successful audio transcription."""
        from modules.speech2text.stt_engine import SpeechToText

        audio_data = np.array([1000, 2000, 3000], dtype=np.int16)
        mock_whisper_model.transcribe.return_value = {"text": "  Test transcription  "}

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', mock_open()):

            stt = SpeechToText()
            result = stt.transcribe_audio(audio_data)

            assert result == "Test transcription"
            mock_whisper_model.transcribe.assert_called_once()

    def test_transcribe_with_language(self, mock_whisper_model):
        """Test transcription with specified language."""
        from modules.speech2text.stt_engine import SpeechToText

        audio_data = np.array([1000, 2000], dtype=np.int16)
        mock_whisper_model.transcribe.return_value = {"text": "Hello"}

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', mock_open()):

            stt = SpeechToText(whisper_language="en")
            result = stt.transcribe_audio(audio_data)

            assert result == "Hello"
            # Verify language parameter was passed
            call_kwargs = mock_whisper_model.transcribe.call_args.kwargs
            assert call_kwargs.get('language') == 'en'

    def test_transcribe_none_audio(self, mock_whisper_model):
        """Test transcription with None audio data."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText()

            with pytest.raises(ValueError, match="Audio data is None"):
                stt.transcribe_audio(None)

    def test_transcribe_empty_audio(self, mock_whisper_model):
        """Test transcription with empty audio data."""
        from modules.speech2text.stt_engine import SpeechToText

        audio_data = np.array([], dtype=np.int16)

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText()

            with pytest.raises(ValueError, match="Audio data is empty"):
                stt.transcribe_audio(audio_data)

    def test_transcribe_missing_text_field(self, mock_whisper_model):
        """Test transcription when Whisper returns invalid result."""
        from modules.speech2text.stt_engine import SpeechToText

        audio_data = np.array([1000, 2000], dtype=np.int16)
        mock_whisper_model.transcribe.return_value = {"invalid": "result"}

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', mock_open()):

            stt = SpeechToText()

            with pytest.raises(RuntimeError, match="Whisper transcription returned invalid result"):
                stt.transcribe_audio(audio_data)

    def test_transcribe_cleanup_temp_file(self, mock_whisper_model):
        """Test that temporary file is cleaned up after transcription."""
        from modules.speech2text.stt_engine import SpeechToText

        audio_data = np.array([1000, 2000], dtype=np.int16)
        mock_whisper_model.transcribe.return_value = {"text": "Test"}

        temp_file_path = "/tmp/test.wav"
        mock_tempfile = MagicMock()
        mock_tempfile.name = temp_file_path
        mock_tempfile.__enter__ = Mock(return_value=mock_tempfile)
        mock_tempfile.__exit__ = Mock(return_value=False)

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', return_value=mock_tempfile), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:

            stt = SpeechToText()
            stt.transcribe_audio(audio_data)

            mock_remove.assert_called_once_with(temp_file_path)


class TestWaitForAudioClearance:
    """Test wait_for_audio_clearance method."""

    def test_audio_clearance_success(self, mock_whisper_model):
        """Test successful audio clearance detection."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        # Simulate audio playing then clearing
        loud_chunk = np.array([[1000], [1000]], dtype=np.int16)
        quiet_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=[
            (loud_chunk, False),  # Audio detected
            (loud_chunk, False),  # Still playing
            (quiet_chunk, False),  # Start clearing
            (quiet_chunk, False),  # Clearing
            (quiet_chunk, False),  # Cleared
        ])

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText(chunk_duration=0.1, required_silence_duration=0.2)
            clearance_time = stt.wait_for_audio_clearance(timeout=5.0)

            assert clearance_time >= 0.0

    def test_audio_clearance_no_audio_detected(self, mock_whisper_model):
        """Test audio clearance when no audio is detected."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        quiet_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(return_value=(quiet_chunk, False))

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText(chunk_duration=0.1, required_silence_duration=0.1)
            clearance_time = stt.wait_for_audio_clearance(timeout=1.0)

            assert clearance_time == 0.0  # Immediate clearance

    def test_audio_clearance_timeout(self, mock_whisper_model):
        """Test audio clearance timeout."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        loud_chunk = np.array([[1000], [1000]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(return_value=(loud_chunk, False))

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream):

            stt = SpeechToText(chunk_duration=0.05)
            clearance_time = stt.wait_for_audio_clearance(timeout=1.0)  # Changed to 1.0 (minimum is 1.0)

            assert clearance_time > 0.0  # Timed out but returns elapsed time

    def test_audio_clearance_invalid_timeout(self, mock_whisper_model):
        """Test audio clearance with invalid timeout."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText()

            with pytest.raises(ValueError, match="timeout must be between 1.0 and 600.0"):
                stt.wait_for_audio_clearance(timeout=1000.0)

    def test_audio_clearance_invalid_startup_delay(self, mock_whisper_model):
        """Test audio clearance with invalid startup_delay."""
        from modules.speech2text.stt_engine import SpeechToText

        with patch('whisper.load_model', return_value=mock_whisper_model):
            stt = SpeechToText()

            with pytest.raises(ValueError, match="startup_delay must be between 0.0 and 10.0"):
                stt.wait_for_audio_clearance(startup_delay=20.0)

    def test_audio_clearance_with_startup_delay(self, mock_whisper_model):
        """Test audio clearance with startup delay."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd
        import time

        quiet_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(return_value=(quiet_chunk, False))

        # Mock time.time to return fixed values to prevent infinite loop
        # Need enough values for: start_time, loop checks, and final elapsed calculations
        time_values = [0.0] + [i * 0.1 for i in range(1, 10)] + [121.0] * 10
        mock_time = Mock(side_effect=time_values)

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream), \
             patch('time.sleep') as mock_sleep, \
             patch('time.time', mock_time):

            stt = SpeechToText(chunk_duration=0.1)

            # Call with startup delay - should complete without hanging
            result = stt.wait_for_audio_clearance(startup_delay=0.5)

            # Verify it completed and returned an elapsed time
            assert result >= 0

            # Verify startup delay was applied
            assert any(call[0][0] == 0.5 for call in mock_sleep.call_args_list)


class TestListen:
    """Test listen method."""

    def test_listen_success(self, mock_whisper_model):
        """Test successful listen operation."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        chunk = np.array([[1000], [1000]], dtype=np.int16)
        silence_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=[
            (chunk, False),
            (chunk, False),
            (silence_chunk, False),
            (silence_chunk, False),
        ])

        mock_whisper_model.transcribe.return_value = {"text": "Test speech"}

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', mock_open()), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):

            stt = SpeechToText(chunk_duration=0.1, min_speech_duration=0.1, silence_timeout=0.1)
            result = stt.listen()

            assert result == "Test speech"

    def test_listen_empty_transcription(self, mock_whisper_model):
        """Test listen when transcription returns empty text."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        chunk = np.array([[1000], [1000]], dtype=np.int16)
        silence_chunk = np.array([[100], [100]], dtype=np.int16)

        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.read = Mock(side_effect=[
            (chunk, False),
            (silence_chunk, False),
            (silence_chunk, False),
        ])

        mock_whisper_model.transcribe.return_value = {"text": "   "}

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', return_value=mock_stream), \
             patch('scipy.io.wavfile.write'), \
             patch('tempfile.NamedTemporaryFile', mock_open()), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):

            stt = SpeechToText(chunk_duration=0.1, min_speech_duration=0.1, silence_timeout=0.1)  # Changed min_speech_duration to 0.1 (minimum allowed)
            result = stt.listen()

            assert result == ""

    def test_listen_recording_failure(self, mock_whisper_model):
        """Test listen when recording fails."""
        from modules.speech2text.stt_engine import SpeechToText
        import sounddevice as sd

        with patch('whisper.load_model', return_value=mock_whisper_model), \
             patch('sounddevice.InputStream', side_effect=sd.PortAudioError("Device error")):

            stt = SpeechToText()

            with pytest.raises(RuntimeError):
                stt.listen()

"""
Speech-to-Text Engine using the following:

Python packages:
sounddevice
openai-whisper
scipy

on Mac:  brew install ffmpeg

This module provides a simple, clean interface for converting speech to text.
"""

import sounddevice as sd
import numpy as np
import whisper
import tempfile
import os
from scipy.io.wavfile import write
import time
from typing import Optional, List, Dict, Union
import logging


class SpeechToText:
    """
    Speech-to-Text engine using openai-whisper.

    Provides a simple interface for converting speech to text with customizable
    speech recognition settings.

    Example:
        stt = SpeechToText(whisper_model="base", debug_logging=True)
        text = stt.listen()
    """
    def __init__(self,
                 sample_rate: int = 16000,
                 channels: int = 1,
                 dtype: str = "int16",
                 max_duration: int = 60,
                 silence_timeout: float = 1.5,
                 silence_threshold: int = 500,
                 chunk_duration: float = 0.1,
                 min_speech_duration: float = 0.3,
                 whisper_model: str = "base",
                 whisper_language: Optional[str] = None,
                 debug_logging: bool = False,
                 log_level: Optional[Union[int, str]] = None,
                 required_silence_duration: float = 0.5):
        """
        Initialize the Speech-to-Text engine.

        Args:
            sample_rate: Sample rate for audio recording in Hz (default: 16000).
                Must be between 8000 and 48000.
            channels: Number of audio channels (default: 1).
                Must be 1 (mono) or 2 (stereo).
            dtype: Data type for audio recording (default: "int16").
                Supported: "int16", "int32", "float32".
            max_duration: Maximum duration to record in seconds (default: 60).
                Must be between 1 and 600 seconds.
            silence_timeout: Duration of silence to stop recording in seconds (default: 1.5).
                Must be between 0.1 and 10.0 seconds.
            silence_threshold: Amplitude threshold to detect silence (default: 500).
                Must be between 10 and 32767 for int16.
            chunk_duration: Duration of each audio chunk to process in seconds (default: 0.1).
                Must be between 0.01 and 1.0 seconds.
            min_speech_duration: Minimum speech duration before detecting silence in seconds (default: 0.3).
                Must be between 0.1 and 5.0 seconds.
            whisper_model: Whisper model size to use (default: "base").
                Options: "tiny", "base", "small", "medium", "large".
            whisper_language: Language code for Whisper transcription (default: None for auto-detect).
                Examples: "en", "es", "fr", "de", "ja", "zh", etc.
            debug_logging: Enable debug-level logging (default: False).
            log_level: Explicit log level override (default: None).
                Can be int (logging.DEBUG, logging.INFO, etc.) or string ("DEBUG", "INFO", etc.).
            required_silence_duration: Duration of silence required for audio clearance in seconds (default: 0.5).
                Must be between 0.1 and 5.0 seconds.

        Raises:
            ValueError: If any parameter is invalid or out of acceptable range.
            RuntimeError: If Whisper model loading fails.
        """
        # Configure logger first so we can use it for validation errors
        self.logger = logging.getLogger(__name__)

        # Configure log level based on parameters
        if log_level is not None:
            # Explicit log level takes precedence
            if isinstance(log_level, str):
                numeric_level = getattr(logging, log_level.upper(), None)
                if not isinstance(numeric_level, int):
                    raise ValueError(f"Invalid log_level string: {log_level}. "
                                   f"Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
                self.logger.setLevel(numeric_level)
            elif isinstance(log_level, int):
                self.logger.setLevel(log_level)
            else:
                raise ValueError(f"log_level must be int or str, not {type(log_level).__name__}")
        elif debug_logging:
            # Debug logging flag sets DEBUG level
            self.logger.setLevel(logging.DEBUG)
        else:
            # Default to INFO level
            self.logger.setLevel(logging.INFO)

        self.logger.debug("Validating initialization parameters...")

        # Validate sample_rate
        if not isinstance(sample_rate, int):
            raise ValueError(f"sample_rate must be an integer, not {type(sample_rate).__name__}")
        if not 8000 <= sample_rate <= 48000:
            raise ValueError(f"sample_rate must be between 8000 and 48000 Hz, got {sample_rate}")

        # Validate channels
        if not isinstance(channels, int):
            raise ValueError(f"channels must be an integer, not {type(channels).__name__}")
        if channels not in (1, 2):
            raise ValueError(f"channels must be 1 (mono) or 2 (stereo), got {channels}")

        # Validate dtype
        valid_dtypes = ["int16", "int32", "float32"]
        if dtype not in valid_dtypes:
            raise ValueError(f"dtype must be one of {valid_dtypes}, got '{dtype}'")

        # Validate max_duration
        if not isinstance(max_duration, (int, float)):
            raise ValueError(f"max_duration must be numeric, not {type(max_duration).__name__}")
        if not 1 <= max_duration <= 600:
            raise ValueError(f"max_duration must be between 1 and 600 seconds, got {max_duration}")

        # Validate silence_timeout
        if not isinstance(silence_timeout, (int, float)):
            raise ValueError(f"silence_timeout must be numeric, not {type(silence_timeout).__name__}")
        if not 0.1 <= silence_timeout <= 10.0:
            raise ValueError(f"silence_timeout must be between 0.1 and 10.0 seconds, got {silence_timeout}")

        # Validate silence_threshold
        if not isinstance(silence_threshold, (int, float)):
            raise ValueError(f"silence_threshold must be numeric, not {type(silence_threshold).__name__}")
        if dtype == "int16" and not 10 <= silence_threshold <= 32767:
            raise ValueError(f"silence_threshold must be between 10 and 32767 for int16, got {silence_threshold}")
        elif dtype == "int32" and not 10 <= silence_threshold <= 2147483647:
            raise ValueError(f"silence_threshold must be between 10 and 2147483647 for int32, got {silence_threshold}")
        elif dtype == "float32" and not 0.0 <= silence_threshold <= 1.0:
            raise ValueError(f"silence_threshold must be between 0.0 and 1.0 for float32, got {silence_threshold}")

        # Validate chunk_duration
        if not isinstance(chunk_duration, (int, float)):
            raise ValueError(f"chunk_duration must be numeric, not {type(chunk_duration).__name__}")
        if not 0.01 <= chunk_duration <= 1.0:
            raise ValueError(f"chunk_duration must be between 0.01 and 1.0 seconds, got {chunk_duration}")

        # Validate min_speech_duration
        if not isinstance(min_speech_duration, (int, float)):
            raise ValueError(f"min_speech_duration must be numeric, not {type(min_speech_duration).__name__}")
        if not 0.1 <= min_speech_duration <= 5.0:
            raise ValueError(f"min_speech_duration must be between 0.1 and 5.0 seconds, got {min_speech_duration}")

        # Validate whisper_model
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if not isinstance(whisper_model, str):
            raise ValueError(f"whisper_model must be a string, not {type(whisper_model).__name__}")
        if whisper_model not in valid_models:
            raise ValueError(f"whisper_model must be one of {valid_models}, got '{whisper_model}'")

        # Validate whisper_language (if provided)
        if whisper_language is not None:
            if not isinstance(whisper_language, str):
                raise ValueError(f"whisper_language must be a string or None, not {type(whisper_language).__name__}")
            if len(whisper_language) < 2:
                raise ValueError(f"whisper_language must be a valid language code (e.g., 'en', 'es'), got '{whisper_language}'")

        # Validate required_silence_duration
        if not isinstance(required_silence_duration, (int, float)):
            raise ValueError(f"required_silence_duration must be numeric, not {type(required_silence_duration).__name__}")
        if not 0.1 <= required_silence_duration <= 5.0:
            raise ValueError(f"required_silence_duration must be between 0.1 and 5.0 seconds, got {required_silence_duration}")

        self.logger.debug("All parameters validated successfully")

        try:
            # Store configuration parameters
            self.sample_rate = sample_rate
            self.channels = channels
            self.dtype = dtype
            self.max_duration = max_duration
            self.silence_timeout = silence_timeout
            self.silence_threshold = silence_threshold
            self.chunk_duration = chunk_duration
            self.min_speech_duration = min_speech_duration
            self.whisper_language = whisper_language
            self.required_silence_duration = required_silence_duration

            self.logger.debug(f"Configuration: sample_rate={sample_rate}, channels={channels}, "
                            f"dtype={dtype}, max_duration={max_duration}, silence_timeout={silence_timeout}, "
                            f"silence_threshold={silence_threshold}, chunk_duration={chunk_duration}, "
                            f"min_speech_duration={min_speech_duration}, whisper_model={whisper_model}, "
                            f"whisper_language={whisper_language}, required_silence_duration={required_silence_duration}")

            # Load Whisper model once during initialization (CRITICAL FIX)
            # This prevents 5-10 second hangs on every transcription
            self.logger.info(f"Loading Whisper model '{whisper_model}' (this may take a few seconds)...")
            self.logger.debug(f"Calling whisper.load_model('{whisper_model}')...")

            self.whisper_model_obj = whisper.load_model(whisper_model)

            self.logger.debug(f"Whisper model '{whisper_model}' loaded successfully")
            self.logger.info("Whisper model loaded successfully")

            self.logger.info("Speech-to-Text engine initialized successfully")
            self.logger.debug("Initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize STT engine: {e}", exc_info=True)
            raise RuntimeError(f"STT engine initialization failed: {e}. "
                             f"Ensure Whisper model '{whisper_model}' can be downloaded and loaded.")

    def record_until_silence(self) -> np.ndarray:
        """
        Record audio from the microphone until silence is detected.

        Returns:
            Recorded audio data as a NumPy array.

        Raises:
            RuntimeError: If audio recording fails or times out.
        """
        self.logger.info("Starting audio recording...")
        self.logger.debug(f"Recording parameters: chunk_duration={self.chunk_duration}s, "
                         f"max_duration={self.max_duration}s, silence_timeout={self.silence_timeout}s, "
                         f"silence_threshold={self.silence_threshold}, min_speech_duration={self.min_speech_duration}s")

        recorded_chunks = []
        silence_start = None
        speech_start = None
        total_duration = 0.0
        chunk_size = int(self.sample_rate * self.chunk_duration)

        self.logger.debug(f"Calculated chunk_size: {chunk_size} samples")

        try:
            self.logger.debug(f"Opening audio input stream: samplerate={self.sample_rate}, "
                            f"channels={self.channels}, dtype={self.dtype}")

            with sd.InputStream(samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype=self.dtype) as stream:

                # Give audio device a moment to stabilize
                self.logger.debug("Waiting 0.1s for audio device to stabilize...")
                time.sleep(0.1)
                self.logger.debug("Audio stream ready, beginning recording loop")

                while total_duration < self.max_duration:
                    try:
                        # Read with timeout to prevent indefinite hangs
                        chunk, overflowed = stream.read(chunk_size)

                        if overflowed:
                            self.logger.warning("Audio buffer overflow detected - some audio may be lost")

                        recorded_chunks.append(chunk)

                        amplitude = np.max(np.abs(chunk))
                        self.logger.debug(f"Chunk amplitude: {amplitude}, threshold: {self.silence_threshold}")

                        # Detect when speech starts
                        if amplitude >= self.silence_threshold:
                            if speech_start is None:
                                speech_start = time.time()
                                self.logger.debug(f"Speech detected (amplitude={amplitude}), starting recording timer")
                                self.logger.info("Speech detected, listening...")
                            silence_start = None  # Reset silence timer
                            self.logger.debug("Audio above threshold - resetting silence timer")
                        else:
                            # Only start silence detection after minimum speech duration
                            if speech_start is not None:
                                speech_duration = time.time() - speech_start
                                self.logger.debug(f"Speech duration so far: {speech_duration:.2f}s, "
                                               f"min required: {self.min_speech_duration}s")

                                if speech_duration >= self.min_speech_duration:
                                    if silence_start is None:
                                        silence_start = time.time()
                                        self.logger.debug("Minimum speech duration reached, starting silence detection")
                                    else:
                                        silence_duration = time.time() - silence_start
                                        self.logger.debug(f"Silence duration: {silence_duration:.2f}s, "
                                                       f"timeout: {self.silence_timeout}s")

                                        if silence_duration >= self.silence_timeout:
                                            self.logger.debug(f"Silence timeout reached ({silence_duration:.2f}s >= {self.silence_timeout}s)")
                                            self.logger.info("Silence detected after speech, stopping recording.")
                                            break

                        total_duration += self.chunk_duration

                    except Exception as read_error:
                        self.logger.error(f"Error reading audio chunk: {read_error}", exc_info=True)
                        # Try to continue recording unless we have no data at all
                        if len(recorded_chunks) == 0:
                            raise RuntimeError(f"Failed to read audio from microphone: {read_error}. "
                                             f"Check if microphone is connected and has proper permissions.")
                        self.logger.warning("Continuing with partial recording due to read error")
                        break

                self.logger.debug(f"Recording loop ended. Total chunks recorded: {len(recorded_chunks)}")

            if len(recorded_chunks) == 0:
                raise RuntimeError("No audio data recorded. Microphone may not be working or no speech detected.")

            self.logger.debug("Concatenating audio chunks...")
            audio_data = np.concatenate(recorded_chunks, axis=0)

            # Validate we have some actual audio
            if len(audio_data) == 0:
                raise RuntimeError("Recorded audio is empty. No audio data captured from microphone.")

            self.logger.debug(f"Audio data shape: {audio_data.shape}, dtype: {audio_data.dtype}")
            self.logger.info(f"Audio recording completed. Duration: {total_duration:.2f}s, Samples: {len(audio_data)}")
            return audio_data

        except sd.PortAudioError as e:
            self.logger.error(f"PortAudio error: {e}", exc_info=True)
            raise RuntimeError(f"Audio device error: {e}. "
                             f"Ensure microphone is connected, not in use by another application, "
                             f"and the application has microphone permissions.")
        except Exception as e:
            self.logger.error(f"Unexpected error during recording: {e}", exc_info=True)
            raise RuntimeError(f"Recording failed: {e}")

    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text using Whisper.

        Args:
            audio_data: Recorded audio data as a NumPy array.

        Returns:
            Transcribed text from the audio data.

        Raises:
            ValueError: If audio_data is invalid.
            RuntimeError: If transcription fails.
        """
        self.logger.info("Transcribing audio data...")
        self.logger.debug(f"Audio data shape: {audio_data.shape if audio_data is not None else 'None'}")

        temp_wav_path = None
        try:
            # Validate audio data
            if audio_data is None:
                raise ValueError("Audio data is None. Cannot transcribe empty audio.")
            if len(audio_data) == 0:
                raise ValueError("Audio data is empty (length 0). Cannot transcribe empty audio.")

            self.logger.debug(f"Audio data validated: {len(audio_data)} samples, dtype={audio_data.dtype}")

            # Create temporary WAV file
            self.logger.debug("Creating temporary WAV file...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                write(temp_wav.name, self.sample_rate, audio_data)
                temp_wav_path = temp_wav.name

            self.logger.debug(f"Temporary WAV file created: {temp_wav_path}")

            # Use pre-loaded model (CRITICAL FIX - prevents hang)
            # Prepare transcription options
            transcribe_options = {"fp16": False}
            if self.whisper_language is not None:
                transcribe_options["language"] = self.whisper_language
                self.logger.debug(f"Using language code: {self.whisper_language}")
            else:
                self.logger.debug("Using auto-detect for language")

            self.logger.debug(f"Transcribing audio file: {temp_wav_path} with options: {transcribe_options}")
            result = self.whisper_model_obj.transcribe(temp_wav_path, **transcribe_options)
            self.logger.debug("Whisper transcription completed")

            # Extract text from result
            if "text" not in result:
                self.logger.error(f"Whisper result missing 'text' field. Result keys: {result.keys()}")
                raise RuntimeError("Whisper transcription returned invalid result (missing 'text' field). "
                                 "This may indicate a problem with the Whisper model or audio file.")

            transcribed_text = result["text"].strip()

            self.logger.debug(f"Transcribed text (first 100 chars): {transcribed_text[:100]}")
            self.logger.info(f"Transcription completed. Length: {len(transcribed_text)} chars")
            return transcribed_text

        except ValueError as e:
            # Re-raise validation errors
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Transcription error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to transcribe audio: {e}. "
                             f"This may be caused by corrupted audio data or Whisper model issues.")

        finally:
            # Always clean up temp file, even if transcription fails
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    self.logger.debug(f"Cleaned up temp file: {temp_wav_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to cleanup temp file {temp_wav_path}: {cleanup_error}")

    def wait_for_audio_clearance(self, timeout: float = 120.0, startup_delay: float = 0.0) -> float:
        """
        Monitor microphone and wait until audio amplitude drops below silence threshold.

        This is used to detect when TTS has finished playing through speakers by
        monitoring the microphone for residual audio.

        Args:
            timeout: Maximum time to wait in seconds (default: 120s).
                Must be between 1.0 and 600.0 seconds.
            startup_delay: Seconds to wait before monitoring to let audio start (default: 0.0s).
                Must be between 0.0 and 10.0 seconds.

        Returns:
            Actual time waited in seconds (including startup delay).

        Raises:
            ValueError: If timeout or startup_delay is invalid.
            RuntimeError: If monitoring fails or times out.
        """
        # Validate parameters
        if not isinstance(timeout, (int, float)):
            raise ValueError(f"timeout must be numeric, not {type(timeout).__name__}")
        if not 1.0 <= timeout <= 600.0:
            raise ValueError(f"timeout must be between 1.0 and 600.0 seconds, got {timeout}")

        if not isinstance(startup_delay, (int, float)):
            raise ValueError(f"startup_delay must be numeric, not {type(startup_delay).__name__}")
        if not 0.0 <= startup_delay <= 10.0:
            raise ValueError(f"startup_delay must be between 0.0 and 10.0 seconds, got {startup_delay}")

        self.logger.info("Monitoring audio for clearance...")
        self.logger.debug(f"Monitor parameters: timeout={timeout}s, startup_delay={startup_delay}s, "
                         f"required_silence={self.required_silence_duration}s, threshold={self.silence_threshold}")

        start_time = time.time()

        # Give TTS audio time to actually start playing
        # pyttsx3 on macOS returns from runAndWait() immediately, but audio plays async
        if startup_delay > 0:
            self.logger.debug(f"Waiting {startup_delay}s for TTS audio to start...")
            time.sleep(startup_delay)
            self.logger.debug("Startup delay completed, beginning audio monitoring")

        chunk_size = int(self.sample_rate * self.chunk_duration)
        silence_duration = 0.0
        audio_detected = False  # Track if we've detected any audio yet

        self.logger.debug(f"Chunk size: {chunk_size} samples")

        try:
            self.logger.debug(f"Opening audio input stream for monitoring: samplerate={self.sample_rate}, "
                            f"channels={self.channels}, dtype={self.dtype}")

            with sd.InputStream(samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype=self.dtype) as stream:

                self.logger.debug("Audio monitoring stream opened, starting detection loop")

                while (time.time() - start_time) < timeout:
                    try:
                        chunk, _ = stream.read(chunk_size)
                        amplitude = np.max(np.abs(chunk))

                        self.logger.debug(f"Chunk amplitude: {amplitude}, threshold: {self.silence_threshold}, "
                                       f"audio_detected: {audio_detected}, silence_duration: {silence_duration:.2f}s")

                        if amplitude >= self.silence_threshold:
                            # Audio detected - TTS is playing
                            if not audio_detected:
                                self.logger.debug("Audio first detected - TTS is playing")
                            audio_detected = True
                            silence_duration = 0.0  # Reset silence counter
                            self.logger.debug(f"Audio detected: amplitude={amplitude} (resetting silence counter)")
                        else:
                            # Below threshold - might be silence
                            if audio_detected:
                                # We've already detected audio, so now we're waiting for it to clear
                                silence_duration += self.chunk_duration
                                self.logger.debug(f"Silence accumulating: {silence_duration:.2f}s / {self.required_silence_duration}s")

                                if silence_duration >= self.required_silence_duration:
                                    elapsed = time.time() - start_time
                                    self.logger.debug(f"Required silence duration reached: {silence_duration:.2f}s >= {self.required_silence_duration}s")
                                    self.logger.info(f"Audio cleared after {elapsed:.2f}s")
                                    return elapsed
                            else:
                                # Still waiting for audio to start playing
                                self.logger.debug("No audio detected yet, waiting for TTS to start...")

                    except Exception as read_error:
                        self.logger.error(f"Error reading audio chunk during monitoring: {read_error}", exc_info=True)
                        break

                # Timeout reached or loop exited
                elapsed = time.time() - start_time
                self.logger.debug(f"Monitoring loop ended. Elapsed: {elapsed:.2f}s, audio_detected: {audio_detected}")

                if not audio_detected:
                    # No audio detected means it already cleared before we started monitoring
                    # This is actually SUCCESS - the estimate was accurate
                    self.logger.debug("No audio detected during entire monitoring period")
                    self.logger.info(f"No audio detected - already cleared (verified in {elapsed:.2f}s)")
                    return 0.0  # Return 0 to indicate immediate clearance
                else:
                    # Audio was detected but didn't clear within timeout - this is unusual
                    self.logger.warning(f"Audio detected but clearance timeout reached after {elapsed:.2f}s. "
                                      f"Audio may still be playing or background noise is too high.")
                    return elapsed

        except sd.PortAudioError as e:
            self.logger.error(f"PortAudio error during monitoring: {e}", exc_info=True)
            raise RuntimeError(f"Audio monitoring failed due to device error: {e}. "
                             f"Ensure microphone is accessible and not in use by another application.")
        except Exception as e:
            self.logger.error(f"Unexpected error during audio monitoring: {e}", exc_info=True)
            raise RuntimeError(f"Audio monitoring failed: {e}")

    def listen(self) -> str:
        """
        Listen to microphone input and convert speech to text.

        Returns:
            Transcribed text from the recorded speech.

        Raises:
            RuntimeError: If recording or transcription fails.
        """
        try:
            self.logger.info("Listening for speech...")
            self.logger.debug("Starting listen() - calling record_until_silence()")

            audio_data = self.record_until_silence()

            self.logger.debug(f"Recording complete, audio_data length: {len(audio_data) if audio_data is not None else 'None'}")
            self.logger.debug("Calling transcribe_audio()")

            text = self.transcribe_audio(audio_data)

            # Validate we got some text
            if not text or text.strip() == "":
                self.logger.warning("Transcription returned empty text - no speech detected or recognition failed")
                self.logger.debug("Returning empty string")
                return ""

            self.logger.debug(f"Transcription successful: '{text[:100]}...' ({len(text)} chars)")
            self.logger.info(f"Transcribed Text: {text}")
            return text

        except RuntimeError as e:
            # Re-raise runtime errors (already logged in sub-methods)
            self.logger.debug(f"RuntimeError in listen(): {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in listen(): {e}", exc_info=True)
            raise RuntimeError(f"Speech-to-text failed unexpectedly: {e}")

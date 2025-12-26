"""
Cross-platform Text-to-Speech Engine using pyttsx3.

This backend is used for Windows and Linux platforms where pyttsx3
works correctly. For macOS, use tts_macos.py instead (solves the
runAndWait() timing bug).
"""

import pyttsx3
from typing import Optional, List, Dict
import logging
import time
from .tts_base import TTSBase


class Pyttsx3TTS(TTSBase):
    """
    Cross-platform TTS engine using pyttsx3 (Windows/Linux).

    NOTE: On Windows/Linux, pyttsx3 works correctly and runAndWait() blocks
    until speech completes. This backend uses word-based estimation for
    consistency with the macOS backend.

    Example:
        tts = Pyttsx3TTS()
        tts.speak("Hello, world!")
    """

    def __init__(self,
                 voice_id: Optional[str] = None,
                 rate: int = 200,
                 volume: float = 1.0):
        """
        Initialize the pyttsx3 TTS engine.

        Args:
            voice_id: Optional voice identifier. If None, uses default system voice.
            rate: Speech rate in words per minute (default: 200).
            volume: Volume level from 0.0 to 1.0 (default: 1.0).
        """
        super().__init__(voice_id, rate, volume)

        try:
            self.engine = pyttsx3.init()

            # Set voice if specified
            if voice_id:
                self.engine.setProperty('voice', voice_id)

            # Set speech rate
            self.engine.setProperty('rate', rate)

            # Set volume
            self.engine.setProperty('volume', volume)

            self.logger.info("pyttsx3 TTS engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize pyttsx3 TTS engine: {e}")
            raise

    def speak(self, text: str, block: bool = True) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to convert to speech.
            block: If True, waits for speech to complete. If False, returns immediately.

        Note:
            Non-blocking mode (block=False) is not fully supported by pyttsx3.
            The engine requires runAndWait() to process the speech queue.
            For true non-blocking behavior, consider using a separate thread.
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided to speak()")
            return

        try:
            self.engine.say(text)
            if block:
                self.engine.runAndWait()
            else:
                # pyttsx3 requires runAndWait() to actually speak
                # For non-blocking, this should be called in a separate thread
                # For now, we log a warning and block anyway
                self.logger.warning("Non-blocking mode not fully supported by pyttsx3, blocking anyway")
                self.engine.runAndWait()

        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")
            raise

    def speak_and_get_clearance_time(self, text: str) -> float:
        """
        Speak text and return estimated speech duration based on word count.

        This is used in hybrid clearance mode: wait for estimated duration,
        then verify audio has cleared by monitoring microphone.

        Args:
            text: The text to convert to speech.

        Returns:
            Float representing estimated seconds for speech.
            Returns 0.0 if text is empty or on error.
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided to speak_and_get_clearance_time()")
            return 0.0

        try:
            # Start TTS playback
            start_time = time.time()
            self.speak(text, block=True)
            runAndWait_duration = time.time() - start_time

            # Calculate estimated speech duration based purely on word count
            # No artificial buffers - just the actual speech time
            word_count = len(text.split())

            # Standard speech rate: self.rate words per minute (default 200 WPM)
            # Convert to seconds: (words / words_per_minute) * 60 seconds
            estimated_speech_duration = (word_count / self.rate) * 60.0

            return estimated_speech_duration

        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")
            # On error, return a safe default
            return 0.5

    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get list of available voices on the system.

        Returns:
            List of voice dictionaries with 'id', 'name', and 'languages' keys.
        """
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []

            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages if hasattr(voice, 'languages') else []
                }
                voice_list.append(voice_info)

            return voice_list

        except Exception as e:
            self.logger.error(f"Error getting available voices: {e}")
            return []

    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice to use for speech synthesis.

        Args:
            voice_id: The voice identifier to use.

        Returns:
            True if voice was set successfully, False otherwise.
        """
        try:
            self.engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice set to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting voice: {e}")
            return False

    def set_rate(self, rate: int) -> bool:
        """
        Set the speech rate.

        Args:
            rate: Speech rate in words per minute.

        Returns:
            True if rate was set successfully, False otherwise.
        """
        try:
            self.engine.setProperty('rate', rate)
            self.rate = rate  # Update stored rate for duration calculations
            self.logger.info(f"Speech rate set to: {rate}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting rate: {e}")
            return False

    def set_volume(self, volume: float) -> bool:
        """
        Set the volume level.

        Args:
            volume: Volume level from 0.0 to 1.0.

        Returns:
            True if volume was set successfully, False otherwise.
        """
        if not 0.0 <= volume <= 1.0:
            self.logger.error(f"Invalid volume level: {volume}. Must be between 0.0 and 1.0")
            return False

        try:
            self.engine.setProperty('volume', volume)
            self.volume = volume  # Update stored volume
            self.logger.info(f"Volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False

    def stop(self) -> None:
        """Stop the current speech synthesis."""
        try:
            self.engine.stop()
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")

    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            if hasattr(self, 'engine'):
                self.engine.stop()
        except:
            pass

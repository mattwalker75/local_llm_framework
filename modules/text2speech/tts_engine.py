"""
Text-to-Speech Engine using pyttsx3.

This module provides a simple, clean interface for converting text to speech.
"""

import pyttsx3
from typing import Optional, List, Dict
import logging


class TextToSpeech:
    """
    Text-to-Speech engine using pyttsx3.

    Provides a simple interface for converting text to speech with customizable
    voice, rate, and volume settings.

    Example:
        tts = TextToSpeech()
        tts.speak("Hello, world!")
    """

    def __init__(self,
                 voice_id: Optional[str] = None,
                 rate: int = 200,
                 volume: float = 1.0):
        """
        Initialize the Text-to-Speech engine.

        Args:
            voice_id: Optional voice identifier. If None, uses default system voice.
            rate: Speech rate in words per minute (default: 200).
            volume: Volume level from 0.0 to 1.0 (default: 1.0).
        """
        self.logger = logging.getLogger(__name__)

        try:
            self.engine = pyttsx3.init()

            # Set voice if specified
            if voice_id:
                self.engine.setProperty('voice', voice_id)

            # Set speech rate
            self.engine.setProperty('rate', rate)

            # Set volume
            self.engine.setProperty('volume', volume)

            self.logger.info("Text-to-Speech engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            raise

    def speak(self, text: str, block: bool = True) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to convert to speech.
            block: If True, waits for speech to complete. If False, returns immediately.
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided to speak()")
            return

        try:
            self.engine.say(text)
            if block:
                self.engine.runAndWait()
            else:
                # For non-blocking mode, you need to handle the event loop differently
                self.engine.runAndWait()

        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")
            raise

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

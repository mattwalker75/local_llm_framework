"""
Base interface for Text-to-Speech engines.

All TTS backends must implement this interface to ensure consistent API
across different platforms.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging


class TTSBase(ABC):
    """
    Abstract base class for Text-to-Speech engines.

    All TTS backends (macOS, Windows, Linux) must implement these methods
    to ensure a consistent API for the CLI and GUI interfaces.
    """

    def __init__(self,
                 voice_id: Optional[str] = None,
                 rate: int = 200,
                 volume: float = 1.0):
        """
        Initialize the TTS engine.

        Args:
            voice_id: Optional voice identifier. If None, uses default system voice.
            rate: Speech rate in words per minute (default: 200).
            volume: Volume level from 0.0 to 1.0 (default: 1.0).
        """
        self.logger = logging.getLogger(__name__)
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id

    @property
    def uses_accurate_timing(self) -> bool:
        """
        Indicates whether this backend provides accurate speech timing.

        Returns:
            True if speak_and_get_clearance_time() returns actual duration.
            False if it returns an estimate based on word count.
        """
        # Default: backends provide estimates unless overridden
        return False

    @abstractmethod
    def speak(self, text: str, block: bool = True) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to convert to speech.
            block: If True, waits for speech to complete. If False, returns immediately.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get list of available voices on the system.

        Returns:
            List of voice dictionaries with 'id', 'name', and 'languages' keys.
        """
        pass

    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice to use for speech synthesis.

        Args:
            voice_id: The voice identifier to use.

        Returns:
            True if voice was set successfully, False otherwise.
        """
        pass

    @abstractmethod
    def set_rate(self, rate: int) -> bool:
        """
        Set the speech rate.

        Args:
            rate: Speech rate in words per minute.

        Returns:
            True if rate was set successfully, False otherwise.
        """
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> bool:
        """
        Set the volume level.

        Args:
            volume: Volume level from 0.0 to 1.0.

        Returns:
            True if volume was set successfully, False otherwise.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the current speech synthesis."""
        pass

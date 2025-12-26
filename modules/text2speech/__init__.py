"""
Text-to-Speech Module for LLM Framework.

This module provides platform-aware text-to-speech capabilities:
- macOS: Uses NSSpeechSynthesizer via pyobjc (proper completion callbacks)
- Windows/Linux: Uses pyttsx3 (works correctly on these platforms)

The module automatically detects the platform and loads the appropriate backend.
"""

import platform
import logging
from typing import Optional

__version__ = "0.1.0"

# Platform detection logger
logger = logging.getLogger(__name__)


def create_tts(voice_id: Optional[str] = None,
               rate: int = 200,
               volume: float = 1.0):
    """
    Factory function to create the appropriate TTS engine for the current platform.

    Args:
        voice_id: Optional voice identifier. If None, uses default system voice.
        rate: Speech rate in words per minute (default: 200).
        volume: Volume level from 0.0 to 1.0 (default: 1.0).

    Returns:
        Platform-specific TTS engine instance (MacOSTTS or Pyttsx3TTS).

    Raises:
        ImportError: If required dependencies are not installed.
        RuntimeError: If TTS engine initialization fails.
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        logger.info("Detected macOS - using NSSpeechSynthesizer backend")
        try:
            from .tts_macos import MacOSTTS
            return MacOSTTS(
                voice_id=voice_id,
                rate=rate,
                volume=volume
            )
        except ImportError as e:
            logger.warning(
                f"Failed to load macOS TTS backend: {e}. "
                "Falling back to pyttsx3 (may have timing issues)."
            )
            # Fall through to pyttsx3 backend

    # Windows, Linux, or fallback from macOS
    logger.info(f"Using pyttsx3 backend for {system}")
    from .tts_pyttsx3 import Pyttsx3TTS
    return Pyttsx3TTS(
        voice_id=voice_id,
        rate=rate,
        volume=volume
    )


# Backward compatibility: TextToSpeech is now an alias for the factory function
# This allows existing code to work without changes
class TextToSpeech:
    """
    Backward-compatible wrapper for platform-aware TTS.

    This class maintains the same API as the original TextToSpeech class,
    but internally uses the platform-specific backend.

    Example:
        tts = TextToSpeech()  # Automatically selects correct backend
        tts.speak("Hello, world!")
    """

    def __new__(cls,
                voice_id: Optional[str] = None,
                rate: int = 200,
                volume: float = 1.0):
        """
        Create platform-specific TTS instance.

        Returns the actual backend instance (MacOSTTS or Pyttsx3TTS),
        not a TextToSpeech wrapper.
        """
        return create_tts(
            voice_id=voice_id,
            rate=rate,
            volume=volume
        )


__all__ = ["TextToSpeech", "create_tts"]

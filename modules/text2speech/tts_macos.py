"""
macOS-specific Text-to-Speech engine using pyobjc and NSSpeechSynthesizer.

This backend properly handles speech completion callbacks, solving the
pyttsx3 runAndWait() bug on macOS where it returns immediately instead
of blocking until speech completes.
"""

import time
import logging
from typing import List, Dict, Optional
from .tts_base import TTSBase

try:
    from AppKit import NSSpeechSynthesizer
    MACOS_TTS_AVAILABLE = True
except ImportError:
    MACOS_TTS_AVAILABLE = False


class MacOSTTS(TTSBase):
    """
    macOS-specific Text-to-Speech engine using NSSpeechSynthesizer.

    This backend uses native macOS APIs via pyobjc-framework-Cocoa, providing
    proper speech completion callbacks that solve the pyttsx3 timing bug.
    """

    def __init__(self,
                 voice_id: Optional[str] = None,
                 rate: int = 200,
                 volume: float = 1.0):
        """
        Initialize the macOS TTS engine.

        Args:
            voice_id: Optional voice identifier. If None, uses default system voice.
            rate: Speech rate in words per minute (default: 200).
            volume: Volume level from 0.0 to 1.0 (default: 1.0).
        """
        super().__init__(voice_id, rate, volume)

        if not MACOS_TTS_AVAILABLE:
            raise ImportError(
                "pyobjc-framework-Cocoa is required for macOS TTS. "
                "Install with: pip install pyobjc-framework-Cocoa"
            )

        try:
            # Create speech synthesizer
            self.synthesizer = NSSpeechSynthesizer.alloc().init()

            # Set voice if specified
            if voice_id:
                self.synthesizer.setVoice_(voice_id)

            # Set volume (0.0 to 1.0)
            self.synthesizer.setVolume_(volume)

            # Convert WPM to macOS speech rate
            # macOS uses a rate from 90 to 720 (default ~200)
            # Our default is 200 WPM, macOS default is ~200
            self.synthesizer.setRate_(rate)

            self.logger.info("macOS TTS engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize macOS TTS engine: {e}")
            raise

    @property
    def uses_accurate_timing(self) -> bool:
        """
        macOS backend provides accurate timing via proper blocking.

        Returns:
            True - NSSpeechSynthesizer blocks until speech completes.
        """
        return True

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
            self.synthesizer.startSpeakingString_(text)

            # If blocking, poll isSpeaking() directly instead of relying on delegate
            # The delegate callback requires a run loop which we don't have in CLI
            if block:
                while self.synthesizer.isSpeaking():
                    time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")
            raise

    def speak_and_get_clearance_time(self, text: str) -> float:
        """
        Speak text and return actual speech duration.

        Unlike pyttsx3, this method can return the ACTUAL speech duration
        because NSSpeechSynthesizer properly blocks until completion.

        Args:
            text: The text to convert to speech.

        Returns:
            Float representing actual seconds for speech.
            Returns 0.0 if text is empty or on error.
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided to speak_and_get_clearance_time()")
            return 0.0

        try:
            # Start TTS playback
            start_time = time.time()
            self.speak(text, block=True)
            actual_duration = time.time() - start_time

            # Return actual duration (no estimation needed!)
            return actual_duration

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
            voices = NSSpeechSynthesizer.availableVoices()
            voice_list = []

            for voice_id in voices:
                # Get voice attributes
                attrs = NSSpeechSynthesizer.attributesForVoice_(voice_id)
                voice_info = {
                    'id': str(voice_id),
                    'name': str(attrs.get('VoiceName', voice_id)),
                    'languages': [str(attrs.get('VoiceLanguage', 'en-US'))]
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
            result = self.synthesizer.setVoice_(voice_id)
            if result:
                self.voice_id = voice_id
                self.logger.info(f"Voice set to: {voice_id}")
                return True
            else:
                self.logger.error(f"Failed to set voice: {voice_id}")
                return False
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
            self.synthesizer.setRate_(rate)
            self.rate = rate  # Update stored rate
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
            self.synthesizer.setVolume_(volume)
            self.volume = volume
            self.logger.info(f"Volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False

    def stop(self) -> None:
        """Stop the current speech synthesis."""
        try:
            self.synthesizer.stopSpeaking()
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")

    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            self.stop()
        except:
            pass

"""
Shared utility functions for TTS/STT integration.

This module contains helper functions to prevent audio feedback loops
when both Text-to-Speech and Speech-to-Text modules are enabled.

Configuration parameters are loaded from the module_info.json files in the
respective module directories.
"""

import time
import logging
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from modules.text2speech.tts_base import TTSBase
    from modules.speech2text.stt_engine import SpeechToText

logger = logging.getLogger(__name__)


def _load_tts_config() -> dict:
    """
    Load TTS module configuration from module_info.json.

    Returns:
        Dictionary containing TTS configuration settings.
    """
    try:
        config_path = Path(__file__).parent.parent / "modules" / "text2speech" / "module_info.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("settings", {})
        else:
            logger.warning(f"TTS module_info.json not found at {config_path}, using defaults")
            return {}
    except Exception as e:
        logger.warning(f"Failed to load TTS config: {e}, using defaults")
        return {}


def _load_stt_config() -> dict:
    """
    Load STT module configuration from module_info.json.

    Returns:
        Dictionary containing STT configuration settings.
    """
    try:
        config_path = Path(__file__).parent.parent / "modules" / "speech2text" / "module_info.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("settings", {})
        else:
            logger.warning(f"STT module_info.json not found at {config_path}, using defaults")
            return {}
    except Exception as e:
        logger.warning(f"Failed to load STT config: {e}, using defaults")
        return {}


def wait_for_tts_clearance(tts: 'TTSBase', stt: 'SpeechToText', text: str,
                           macos_buffer: Optional[float] = None,
                           pyttsx3_buffer: Optional[float] = None,
                           verification_timeout: Optional[float] = None) -> float:
    """
    Speak text and wait for audio to clear before allowing STT to listen.

    This prevents the STT microphone from picking up TTS speaker output,
    which would cause the AI to "hear itself" as input.

    The function uses different strategies based on the TTS backend:
    - macOS (NSSpeechSynthesizer): Blocks accurately, just adds small buffer
    - pyttsx3 (Windows/Linux): Estimates duration, verifies clearance, adds buffer

    Args:
        tts: The TTS engine instance.
        stt: The STT engine instance (used for audio monitoring on estimate-based backends).
        text: The text to speak.
        macos_buffer: Optional override for macOS buffer time in seconds.
            If None, loads from module_info.json (default: 0.5).
        pyttsx3_buffer: Optional override for pyttsx3 buffer time in seconds.
            If None, loads from module_info.json (default: 1.0).
        verification_timeout: Optional override for audio verification timeout in seconds.
            If None, loads from module_info.json (default: 10.0).

    Returns:
        Total time waited in seconds.

    Raises:
        RuntimeError: If speech synthesis or audio clearance verification fails.
    """
    # Load configuration from module_info.json if not provided
    tts_config = _load_tts_config()
    stt_config = _load_stt_config()

    # Get configurable parameters with fallback defaults
    macos_buffer_time = macos_buffer if macos_buffer is not None else tts_config.get("audio_clearance_buffer_macos", 0.5)
    pyttsx3_buffer_time = pyttsx3_buffer if pyttsx3_buffer is not None else tts_config.get("audio_clearance_buffer_pyttsx3", 1.0)
    verify_timeout = verification_timeout if verification_timeout is not None else tts_config.get("audio_verification_timeout", 10.0)

    logger.debug(f"Clearance config: macos_buffer={macos_buffer_time}s, "
                f"pyttsx3_buffer={pyttsx3_buffer_time}s, verification_timeout={verify_timeout}s")

    # Validate text
    if not text or not isinstance(text, str):
        raise ValueError(f"Invalid text provided: {text}. Must be non-empty string.")

    try:
        if tts.uses_accurate_timing:
            # macOS backend: speak_and_get_clearance_time() already blocks accurately
            logger.debug("Using macOS backend - accurate timing mode")
            logger.info("Speaking with accurate timing backend...")

            actual_duration = tts.speak_and_get_clearance_time(text)

            logger.debug(f"Speech completed in {actual_duration:.2f}s")

            # Small buffer to let macOS audio system fully drain
            logger.debug(f"Adding {macos_buffer_time}s buffer for audio system drain")
            time.sleep(macos_buffer_time)

            total_time = actual_duration + macos_buffer_time
            logger.info(f"Audio cleared (actual: {actual_duration:.1f}s + buffer: {macos_buffer_time}s = {total_time:.1f}s)")
            logger.debug("Clearance complete - ready for STT input")
            return total_time

        else:
            # pyttsx3 backend: Use hybrid approach (estimate + verify + buffer)
            logger.debug("Using pyttsx3 backend - estimation + verification mode")
            logger.info("Speaking with estimation backend...")

            clearance_time = tts.speak_and_get_clearance_time(text)

            logger.debug(f"Estimated speech duration: {clearance_time:.2f}s")

            # Wait for estimated time
            logger.info(f"Waiting {clearance_time:.1f}s for estimated speech duration...")
            logger.debug("Starting estimation wait...")
            time.sleep(clearance_time)
            logger.debug("Estimation wait complete")

            # Verify audio has actually cleared
            logger.info("Verifying audio clearance...")
            logger.debug(f"Starting audio verification (timeout={verify_timeout}s)")

            verification_time = stt.wait_for_audio_clearance(timeout=verify_timeout, startup_delay=0)

            logger.debug(f"Verification complete: {verification_time:.2f}s")

            # Add small buffer after verification
            if verification_time > 0:
                logger.debug(f"Audio was detected, adding {pyttsx3_buffer_time}s buffer")
                logger.info(f"Buffer: waiting {pyttsx3_buffer_time}s for audio buffers to drain...")
                time.sleep(pyttsx3_buffer_time)
                total_time = clearance_time + verification_time + pyttsx3_buffer_time
            else:
                logger.debug("No audio detected - clearance was immediate")
                total_time = clearance_time + verification_time

            logger.info(f"Audio fully cleared (estimate: {clearance_time:.1f}s + verify: {verification_time:.1f}s = {total_time:.1f}s)")
            logger.debug("Clearance complete - ready for STT input")
            return total_time

    except ValueError as e:
        logger.error(f"Invalid parameter in clearance: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Audio clearance failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during TTS clearance: {e}", exc_info=True)
        raise RuntimeError(f"TTS/STT clearance failed unexpectedly: {e}")

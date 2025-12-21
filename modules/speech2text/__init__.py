"""
Text-to-Speech Module for LLM Framework.

This module provides text-to-speech capabilities using pyttsx3.
It can be used standalone or integrated with the LLM Framework.
"""

from .stt_engine import SpeechToText

__version__ = "0.1.0"
__all__ = ["SpeechToText"]

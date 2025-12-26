"""
Speech-to-Text Module for LLM Framework.

This module provides speech-to-text capabilities using OpenAI Whisper.
Works completely offline with no internet connection required.
It can be used standalone or integrated with the LLM Framework.
"""

from .stt_engine import SpeechToText

__version__ = "0.1.0"
__all__ = ["SpeechToText"]

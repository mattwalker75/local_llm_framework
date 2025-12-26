"""
DEPRECATED TEST FILE - DO NOT USE

This test file tests the old TTS architecture (text2speech.tts_engine.pyttsx3)
which was replaced with a platform-specific architecture:
  - text2speech.tts_macos.MacOSTTS (macOS with NSSpeechSynthesizer)
  - text2speech.tts_pyttsx3.Pyttsx3TTS (Windows/Linux with pyttsx3)

The original test file has been renamed to test_text2speech_module.py.deprecated

TTS functionality is now tested through integration tests in:
  - tests/test_cli.py
  - tests/test_gui.py

If you need to test the new TTS backends directly, create new test files:
  - tests/test_tts_macos.py
  - tests/test_tts_pyttsx3.py
  - tests/test_tts_factory.py
"""

# This file intentionally left minimal to prevent pytest from collecting tests
# The actual deprecated tests are in test_text2speech_module.py.deprecated

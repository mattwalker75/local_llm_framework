# Text-to-Speech Module

A text-to-speech module for the Local LLM Framework that converts LLM text output into spoken audio.

## Overview

This module uses **pyttsx3** to provide offline, cross-platform text-to-speech capabilities. It integrates with the LLM Framework to automatically speak LLM responses during interactive chat sessions.

## Features

- **Offline Operation**: Works without internet connection
- **Cross-Platform**: Compatible with macOS, Windows, and Linux
- **Customizable**: Adjust voice, speech rate, and volume
- **Simple Integration**: Clean API for standalone or integrated use
- **Multiple Voices**: Support for all system-installed voices

## Installation

Install the required dependency:

```bash
pip install pyttsx3
```

## Standalone Usage

### Basic Test

```bash
# Simple text-to-speech
python test_tts.py "Hello, world!"

# Or using the --text flag
python test_tts.py --text "Welcome to the LLM Framework"
```

### List Available Voices

There are two ways to list available voices:

**Using test_tts.py:**
```bash
python test_tts.py --list-voices
```

**Using the dedicated list_voices.py script:**
```bash
# Table format (default)
python list_voices.py

# JSON format
python list_voices.py --format json

# Simple list format
python list_voices.py --format simple
```

### Custom Settings

```bash
# Adjust speech rate and volume
python test_tts.py --text "Testing custom settings" --rate 150 --volume 0.8

# Use a specific voice
python test_tts.py --text "Hello" --voice "com.apple.speech.synthesis.voice.samantha"
```

## Python API Usage

```python
from text2speech import TextToSpeech

# Initialize with default settings
tts = TextToSpeech()

# Speak some text
tts.speak("Hello, world!")

# Initialize with custom settings
tts = TextToSpeech(rate=150, volume=0.8)
tts.speak("Custom speech rate and volume")

# Get available voices
voices = tts.get_available_voices()
for voice in voices:
    print(f"{voice['name']}: {voice['id']}")

# Change voice during runtime
tts.set_voice("com.apple.speech.synthesis.voice.alex")
tts.speak("This is Alex speaking")
```

## Configuration

The module can be configured through the `module_info.json` file:

- **voice_id**: Voice identifier (null for system default)
- **rate**: Speech rate in words per minute (50-400, default: 200)
- **volume**: Volume level (0.0-1.0, default: 1.0)
- **auto_speak**: Automatically speak LLM responses (true/false)

## Integration with LLM Framework

### Future Integration (Planned)

Once integrated with the LLM Framework:

```bash
# Enable the module
llf module enable text2speech

# Start chat with TTS enabled
llf chat

# Disable the module
llf module disable text2speech

# View module info
llf module info text2speech
```

## Dependencies

- **pyttsx3** (>= 2.90): Text-to-speech library
  - macOS: Uses NSSpeechSynthesizer
  - Windows: Uses SAPI5
  - Linux: Uses eSpeak

## Troubleshooting

### macOS

If you encounter issues on macOS, ensure you have the system speech synthesis available:

```bash
# Test system speech
say "Hello, world!"
```

### Linux

On Linux, you may need to install eSpeak:

```bash
# Ubuntu/Debian
sudo apt-get install espeak

# Fedora
sudo dnf install espeak
```

## Testing

The module includes comprehensive unit tests with 96% code coverage.

### Run Unit Tests

```bash
# Run all tests (from repository root)
pytest tests/test_text2speech_module.py -v

# Run tests with coverage report
pytest tests/test_text2speech_module.py -v --cov=modules/text2speech --cov-report=term-missing

# Run specific test class
pytest tests/test_text2speech_module.py::TestTextToSpeechSpeak -v
```

### Test Coverage

The test suite includes 24 tests covering:
- **Initialization** (3 tests): Default settings, custom settings, error handling
- **Speech Synthesis** (4 tests): Basic speak, empty strings, whitespace, errors
- **Voice Management** (5 tests): List voices, set voices, error handling
- **Settings** (5 tests): Rate, volume, validation, error handling
- **Cleanup** (4 tests): Stop method, destructor, error handling
- **Module Import** (3 tests): Import verification, version, exports

**Coverage Statistics:**
- **tts_engine.py**: 96% coverage (77 statements, 3 missed)
- **Overall Module**: 72% coverage (includes test scripts)
- **All 24 tests passing**

### Test Files

- `../../tests/test_text2speech_module.py` - Comprehensive unit tests with mocking (24 tests)
- `test_tts.py` - Manual integration test script
- `list_voices.py` - Voice listing utility script

## Module Structure

```
text2speech/
├── __init__.py              # Module exports
├── tts_engine.py            # Main TTS engine (96% coverage)
├── test_tts.py              # Standalone test/demo script
├── list_voices.py           # Voice listing utility
├── module_info.json         # Module metadata and configuration
└── README.md                # This file

Unit tests:
└── tests/test_text2speech_module.py  # Unit tests (24 tests, 96% coverage)
```

## License

Part of the Local LLM Framework project.

## Version

**0.1.0** - Initial release
- Text-to-speech using pyttsx3
- Cross-platform support (macOS, Windows, Linux)
- 24 unit tests with 96% coverage
- Standalone test scripts
- Voice management utilities

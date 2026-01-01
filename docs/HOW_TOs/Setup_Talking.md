# Setup Talking: Speech-to-Text & Text-to-Speech

> **Voice-Enable Your LLM Experience**
> Enable two-way voice communication with your local LLM using Speech-to-Text (microphone input) and Text-to-Speech (audio output).

---

## Table of Contents

1. [What is Talking?](#what-is-talking)
2. [Quick Start](#quick-start)
3. [Understanding the Modules](#understanding-the-modules)
4. [Testing Your System](#testing-your-system)
5. [Managing Modules](#managing-modules)
6. [Module Configuration](#module-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Topics](#advanced-topics)

---

## What is Talking?

The LLM Framework provides two complementary modules for voice interaction:

### Speech-to-Text (STT)
- **What it does**: Converts your spoken words into text input for the LLM
- **How it works**: Uses your computer's microphone to capture audio and OpenAI Whisper to transcribe it
- **Key benefit**: Completely offline - no internet connection required
- **Use case**: Speak to the LLM instead of typing

### Text-to-Speech (TTS)
- **What it does**: Converts the LLM's text responses into spoken audio
- **How it works**: Uses platform-native speech engines (macOS NSSpeechSynthesizer or pyttsx3)
- **Key benefit**: Hear the LLM's responses through your speakers or headphones
- **Use case**: Have the LLM talk back to you

**Together, these modules enable natural voice conversations with your local LLM.**

```
┌─────────────────────────────────────────────────────┐
│                  Voice Interaction                   │
└─────────────────────────────────────────────────────┘

  You Speak          Speech-to-Text          LLM Processes
  (Microphone)   →   (Whisper Engine)    →   (Local Model)
                                                    ↓
  You Hear      ←   Text-to-Speech        ←   LLM Responds
  (Speakers)        (Platform TTS)           (Text Output)
```

---

## Quick Start

### Prerequisites

Before enabling voice modules, ensure you have:

1. **Active Virtual Environment**
   ```bash
   source llf_venv/bin/activate  # On macOS/Linux
   ```

2. **Working Microphone** (for Speech-to-Text)
3. **Working Speakers/Headphones** (for Text-to-Speech)
4. **ffmpeg Installed** (for Speech-to-Text)
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # Windows (using chocolatey)
   choco install ffmpeg
   ```

### Enable Voice Modules

```bash
# Enable Text-to-Speech (LLM talks to you)
llf module enable text2speech

# Enable Speech-to-Text (you talk to LLM)
llf module enable speech2text

# Enable both at once
llf module enable all

# Verify they're enabled
llf module list --enabled
```

Expected output:
```
Enabled Modules:
  ✓ text2speech (Text-to-Speech) - Converts LLM text output to spoken audio
  ✓ speech2text (Speech-to-Text) - Converts user voice to text input for the LLM
```

### Test It Out

After enabling the modules:

1. **Test Text-to-Speech**:
   ```bash
   ./bin/tools/test_text2speech.py "Hello, I am your local LLM assistant"
   ```

2. **Test Speech-to-Text**:
   ```bash
   ./bin/tools/test_speech2text.py
   # Speak when prompted, then wait for silence detection
   ```

3. **Use with LLM Chat**:
   ```bash
   llf chat
   # Now speak instead of typing (if speech2text is enabled)
   # The LLM will speak responses (if text2speech is enabled)
   ```

---

## Understanding the Modules

### Module Architecture

The LLM Framework uses a registry-based module system:

```
modules/
├── modules_registry.json          # Central registry tracking all modules
├── speech2text/                   # Speech-to-Text module
│   ├── __init__.py
│   ├── stt_engine.py             # Core Whisper transcription engine
│   └── module_info.json          # Module metadata and settings
└── text2speech/                   # Text-to-Speech module
    ├── __init__.py               # Platform detection and factory
    ├── tts_base.py               # Base TTS interface
    ├── tts_macos.py              # macOS NSSpeechSynthesizer
    ├── tts_pyttsx3.py            # Windows/Linux pyttsx3
    ├── list_voices.py            # Voice enumeration utility
    └── module_info.json          # Module metadata and settings
```

### Module Registry

The `modules/modules_registry.json` file tracks all available modules:

```json
{
  "version": "2.0",
  "modules": [
    {
      "name": "text2speech",
      "display_name": "Text-to-Speech",
      "description": "Converts LLM text output to spoken audio",
      "type": "output_processor",
      "enabled": false,
      "dependencies": ["pyttsx3>=2.90"]
    },
    {
      "name": "speech2text",
      "display_name": "Speech-to-Text",
      "description": "Converts user voice to text input for the LLM",
      "type": "input_processor",
      "enabled": false,
      "dependencies": [
        "sounddevice>=0.5.3",
        "scipy>=1.16.3",
        "openai-whisper>=20250625"
      ]
    }
  ]
}
```

**Key Fields:**
- `name`: Internal module identifier
- `display_name`: Human-readable name
- `type`: Module category (`input_processor` or `output_processor`)
- `enabled`: Whether the module is currently active
- `dependencies`: Required Python packages

---

## Testing Your System

Before using voice modules with your LLM, verify your hardware and software work correctly.

### Test Text-to-Speech (Speakers)

#### Basic Test
```bash
./bin/tools/test_text2speech.py "Testing speakers and text to speech"
```

#### List Available Voices
```bash
./bin/tools/test_text2speech.py --list-voices
```

Example output:
```
Available voices on your system:

1. Alex
   ID: com.apple.voice.compact.en-US.Alex
   Languages: en_US

2. Samantha
   ID: com.apple.voice.compact.en-US.Samantha
   Languages: en_US
```

#### Test with Custom Settings
```bash
# Use specific voice
./bin/tools/test_text2speech.py --text "Hello world" \
  --voice "com.apple.voice.compact.en-US.Alex"

# Adjust speech rate (words per minute)
./bin/tools/test_text2speech.py --text "Speaking slowly" --rate 150

# Adjust volume (0.0 to 1.0)
./bin/tools/test_text2speech.py --text "Quiet voice" --volume 0.5

# Combine settings
./bin/tools/test_text2speech.py \
  --text "Custom speech test" \
  --voice "com.apple.voice.compact.en-US.Samantha" \
  --rate 180 \
  --volume 0.8
```

**Script Options:**
- `--text` / `-t`: Text to speak
- `--list-voices`: Show all available voices
- `--voice` / `-v`: Voice ID to use
- `--rate` / `-r`: Speech rate in WPM (default: 200)
- `--volume`: Volume level 0.0-1.0 (default: 1.0)

### Test Speech-to-Text (Microphone)

#### Basic Test
```bash
./bin/tools/test_speech2text.py
```

When you run this:
1. The script will print current settings
2. You'll see "We are starting to listen... Start talking..."
3. Speak into your microphone
4. Stop talking and wait (1.5 seconds of silence by default)
5. Your transcribed text will be displayed

#### Test with Custom Settings
```bash
# Longer recording time (default: 60 seconds)
./bin/tools/test_speech2text.py --max_time 120

# More sensitive silence detection (lower = more sensitive)
./bin/tools/test_speech2text.py --s_timeout 1.0 --s_threshold 300

# Higher quality audio (higher sample rate)
./bin/tools/test_speech2text.py --sample 44100

# Combine settings
./bin/tools/test_speech2text.py \
  --max_time 90 \
  --s_timeout 2.0 \
  --s_threshold 400 \
  --sample 22050
```

**Script Options:**
- `--sample`: Sample rate in Hz (default: 16000)
- `--data_type`: Audio data type (default: "int16")
- `--max_time`: Max recording duration in seconds (default: 60)
- `--s_timeout`: Silence duration to stop recording (default: 1.5)
- `--s_threshold`: Amplitude threshold for silence (default: 500)
- `--c_duration`: Audio chunk duration (default: 0.1)

**Troubleshooting Test Issues:**

| Problem | Solution |
|---------|----------|
| "No default input device found" | Check microphone is connected and recognized by OS |
| Cuts off speech too early | Increase `--s_timeout` to 2.0 or 3.0 |
| Doesn't detect end of speech | Decrease `--s_threshold` to 300 or 200 |
| Poor transcription quality | Try higher `--sample` rate (22050 or 44100) |
| Voice too quiet | Speak closer to mic or increase system input volume |

---

## Managing Modules

Use the `llf module` command to control voice modules.

### List Modules

```bash
# List all available modules
llf module list
```

Output:
```
Available Modules:
  [ ] text2speech (Text-to-Speech) - Converts LLM text output to spoken audio
  [ ] speech2text (Speech-to-Text) - Converts user voice to text input for the LLM

Legend: [✓] Enabled  [ ] Disabled
```

```bash
# List only enabled modules
llf module list --enabled
```

### Enable Modules

```bash
# Enable a specific module
llf module enable text2speech
llf module enable speech2text

# Enable all modules at once
llf module enable all
```

Success output:
```
✓ Module 'text2speech' enabled successfully
```

### Disable Modules

```bash
# Disable a specific module
llf module disable text2speech
llf module disable speech2text

# Disable all modules at once
llf module disable all
```

### Get Module Information

```bash
# Show detailed information about a module
llf module info text2speech
llf module info speech2text
```

Example output:
```
Module: text2speech (Text-to-Speech)
Version: 0.1.0
Type: output_processor
Status: Enabled
Description: Platform-aware text-to-speech using NSSpeechSynthesizer (macOS) or pyttsx3

Dependencies:
  - pyttsx3>=2.90
  - pyobjc-framework-Cocoa>=10.0 (macOS only)

Settings:
  voice_id: null (system default)
  rate: 200 words/minute
  volume: 1.0
  auto_speak: true
```

### Module Command Reference

```bash
llf module -h
```

```
usage: llf module [-h] [--enabled]

Manage modules that extend the engagement ability between the LLM and user.

options:
  -h, --help  show this help message and exit
  --enabled   List only enabled modules (use with list action)

actions:
  list                      List modules
  list --enabled            List only enabled modules
  enable MODULE_NAME        Enable a module
  enable all                Enable all modules
  disable MODULE_NAME       Disable a module
  disable all               Disable all modules
  info MODULE_NAME          Show module information
```

---

## Module Configuration

Each module has configurable settings stored in `modules/<module_name>/module_info.json`.

### Text-to-Speech Settings

Location: `modules/text2speech/module_info.json`

**Key Settings:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `voice_id` | string | null | Voice ID to use (null = system default) |
| `rate` | integer | 200 | Speech rate in words per minute (50-400) |
| `volume` | float | 1.0 | Volume level from 0.0 to 1.0 |
| `auto_speak` | boolean | true | Automatically speak LLM responses |
| `debug_logging` | boolean | false | Enable detailed debug logs |
| `log_level` | string | "INFO" | Logging level (DEBUG/INFO/WARNING/ERROR) |

**Platform-Specific Settings:**

| Setting | Platform | Default | Description |
|---------|----------|---------|-------------|
| `audio_clearance_buffer_macos` | macOS | 0.5 | Buffer time after speech completion (seconds) |
| `audio_clearance_buffer_pyttsx3` | Windows/Linux | 1.0 | Buffer time after audio verification (seconds) |
| `audio_verification_timeout` | All | 10.0 | Max wait time for audio clearance (seconds) |
| `required_silence_duration` | All | 0.5 | Silence duration to confirm audio cleared (seconds) |

**Example Configuration:**
```json
{
  "settings": {
    "voice_id": "com.apple.voice.compact.en-US.Alex",
    "rate": 180,
    "volume": 0.8,
    "auto_speak": true,
    "debug_logging": false,
    "log_level": "INFO"
  }
}
```

### Speech-to-Text Settings

Location: `modules/speech2text/module_info.json`

**Key Settings:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `sample_rate` | integer | 16000 | Sample rate for audio recording (Hz) |
| `channels` | integer | 1 | Number of audio channels (1=mono, 2=stereo) |
| `dtype` | string | "int16" | Audio data type (int16/int32/float32) |
| `max_duration` | integer | 60 | Max recording duration before auto-stop (seconds) |
| `silence_timeout` | float | 1.5 | Silence duration before stopping (seconds) |
| `silence_threshold` | integer | 500 | Amplitude threshold for silence detection (100-2000) |
| `chunk_duration` | float | 0.1 | Duration of each audio chunk (seconds) |
| `min_speech_duration` | float | 0.3 | Minimum speech before detecting silence (seconds) |
| `whisper_model` | string | "base" | Whisper model size (tiny/base/small/medium/large) |
| `whisper_language` | string | null | Language code (null = auto-detect) |
| `debug_logging` | boolean | false | Enable detailed debug logs |
| `log_level` | string | "INFO" | Logging level |

**Advanced Settings:**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `audio_stabilization_delay` | float | 0.1 | Delay after opening stream for device stabilization |
| `required_silence_clearance` | float | 0.5 | Silence duration to confirm TTS audio cleared |
| `audio_clearance_timeout` | float | 120.0 | Max wait time for TTS clearance (seconds) |

**Whisper Model Selection:**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39M | Fastest | Good | Quick testing, lower-end hardware |
| base | 74M | Fast | Better | Default - balanced speed/accuracy |
| small | 244M | Medium | Good | Higher accuracy needed |
| medium | 769M | Slow | Very Good | Professional transcription |
| large | 1550M | Slowest | Best | Maximum accuracy, powerful hardware |

**Example Configuration:**
```json
{
  "settings": {
    "sample_rate": 16000,
    "max_duration": 120,
    "silence_timeout": 2.0,
    "silence_threshold": 400,
    "whisper_model": "small",
    "whisper_language": "en",
    "debug_logging": false
  }
}
```

### Modifying Settings

To change module settings:

1. **Edit the module_info.json file**:
   ```bash
   # Text-to-Speech
   nano modules/text2speech/module_info.json

   # Speech-to-Text
   nano modules/speech2text/module_info.json
   ```

2. **Update the desired settings** in the `"settings"` section

3. **Disable and re-enable the module** to apply changes:
   ```bash
   llf module disable text2speech
   llf module enable text2speech
   ```

4. **Verify changes**:
   ```bash
   llf module info text2speech
   ```

**Important Notes:**
- Changes only take effect after disabling/enabling the module
- Invalid settings may prevent module from loading
- Test with standalone test scripts after making changes
- Keep backups of working configurations

---

## Troubleshooting

### Common Issues

#### Text-to-Speech Issues

**Problem: No audio output**
```bash
# Test speakers with system sound
# macOS: System Settings > Sound > Test
# Linux: speaker-test -t wav -c 2

# Verify TTS works standalone
./bin/tools/test_text2speech.py "Testing audio output"

# Check volume setting in module_info.json
llf module info text2speech
```

**Problem: Speech is too fast/slow**
```bash
# Test different rates
./bin/tools/test_text2speech.py --text "Rate test" --rate 150  # Slower
./bin/tools/test_text2speech.py --text "Rate test" --rate 250  # Faster

# Update module setting
# Edit modules/text2speech/module_info.json
# Set "rate": 180 (or desired value)
```

**Problem: Wrong voice is used**
```bash
# List available voices
./bin/tools/test_text2speech.py --list-voices

# Test a specific voice
./bin/tools/test_text2speech.py \
  --text "Voice test" \
  --voice "com.apple.voice.compact.en-US.Samantha"

# Update module setting
# Edit modules/text2speech/module_info.json
# Set "voice_id": "com.apple.voice.compact.en-US.Samantha"
```

**Problem: Speech cuts off or overlaps**
```bash
# Increase audio clearance buffer
# Edit modules/text2speech/module_info.json
# macOS: Set "audio_clearance_buffer_macos": 1.0
# Windows/Linux: Set "audio_clearance_buffer_pyttsx3": 2.0
```

#### Speech-to-Text Issues

**Problem: "No default input device found"**
```bash
# Check microphone is connected
# macOS: System Settings > Sound > Input > Microphone
# Linux: arecord -l

# Test microphone with system tools
# macOS: Use QuickTime Player > New Audio Recording
# Linux: arecord -d 5 test.wav && aplay test.wav
```

**Problem: Transcription is inaccurate**
```bash
# Try a better Whisper model (slower but more accurate)
# Edit modules/speech2text/module_info.json
# Set "whisper_model": "small" or "medium"

# Ensure you're speaking clearly and close to microphone
# Reduce background noise

# Try higher sample rate for better quality
./bin/tools/test_speech2text.py --sample 22050
```

**Problem: Cuts off speech too early**
```bash
# Increase silence timeout
./bin/tools/test_speech2text.py --s_timeout 3.0

# Or update module setting
# Edit modules/speech2text/module_info.json
# Set "silence_timeout": 2.5
```

**Problem: Doesn't detect end of speech**
```bash
# Make silence detection more sensitive (lower threshold)
./bin/tools/test_speech2text.py --s_threshold 300

# Or update module setting
# Edit modules/speech2text/module_info.json
# Set "silence_threshold": 350
```

**Problem: ffmpeg not found**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# Windows (chocolatey)
choco install ffmpeg

# Verify installation
ffmpeg -version
```

**Problem: Recording too quiet**
```bash
# Increase system microphone input level
# macOS: System Settings > Sound > Input > Input volume
# Linux: alsamixer (select capture device, increase level)

# Speak closer to microphone
# Reduce silence threshold for better sensitivity
./bin/tools/test_speech2text.py --s_threshold 200
```

### Debugging

#### Enable Debug Logging

Edit the module's `module_info.json`:

```json
{
  "settings": {
    "debug_logging": true,
    "log_level": "DEBUG"
  }
}
```

Then disable/enable the module:
```bash
llf module disable text2speech
llf module enable text2speech
```

#### Check Module Status

```bash
# Verify module is enabled
llf module list --enabled

# Get detailed module info
llf module info text2speech
llf module info speech2text

# Check dependencies are installed
pip list | grep pyttsx3
pip list | grep sounddevice
pip list | grep openai-whisper
```

#### Test Hardware Independently

```bash
# Test speakers
./bin/tools/test_text2speech.py "Hardware test"

# Test microphone
./bin/tools/test_speech2text.py

# Test both together
llf chat
# (with both modules enabled)
```

#### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Module not found" | Module name misspelled | Use exact names: `text2speech` or `speech2text` |
| "Dependencies not installed" | Missing Python packages | Run `pip install -r requirements.txt` |
| "Audio device error" | Hardware not connected | Check microphone/speakers are connected |
| "Whisper model not found" | Model not downloaded | First run downloads model automatically |
| "Invalid voice ID" | Voice doesn't exist | Use `--list-voices` to see available voices |

---

## Advanced Topics

### Platform Differences

#### Text-to-Speech

**macOS:**
- Uses `NSSpeechSynthesizer` (native Apple TTS)
- Better audio synchronization
- Faster speech start/stop
- Requires: `pyobjc-framework-Cocoa>=10.0`

**Windows/Linux:**
- Uses `pyttsx3` (cross-platform TTS)
- May have slight timing delays
- Works on all platforms
- Requires: `pyttsx3>=2.90`

**Automatic Platform Detection:**
```python
# The module automatically selects the correct backend
from modules.text2speech import TextToSpeech

tts = TextToSpeech()  # Uses MacOSTTS on macOS, Pyttsx3TTS elsewhere
tts.speak("Platform-aware speech")
```

#### Speech-to-Text

**All Platforms:**
- Uses OpenAI Whisper (cross-platform)
- Completely offline transcription
- Requires: `sounddevice`, `scipy`, `openai-whisper`, `ffmpeg`

**Platform-Specific Audio:**
- macOS: CoreAudio
- Linux: ALSA/PulseAudio
- Windows: WASAPI

### Using Modules in Custom Scripts

#### Text-to-Speech Example
```python
#!/usr/bin/env python3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.text2speech import TextToSpeech

# Initialize TTS
tts = TextToSpeech(
    voice_id=None,        # Use system default
    rate=200,             # Words per minute
    volume=1.0            # 0.0 to 1.0
)

# Speak text
tts.speak("Hello from my custom script!")

# List available voices
voices = tts.get_available_voices()
for voice in voices:
    print(f"{voice['name']}: {voice['id']}")
```

#### Speech-to-Text Example
```python
#!/usr/bin/env python3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.speech2text import SpeechToText

# Initialize STT
stt = SpeechToText(
    sample_rate=16000,
    dtype="int16",
    max_duration=60,
    silence_timeout=1.5,
    silence_threshold=500,
    chunk_duration=0.1
)

# Listen for speech
print("Speak now...")
transcribed_text = stt.listen()
print(f"You said: {transcribed_text}")
```

### Module Lifecycle Hooks

Modules can hook into LLM response processing:

**Text-to-Speech Hooks:**
```json
{
  "hooks": {
    "on_llm_response_chunk": "process_chunk",
    "on_llm_response_complete": "process_complete"
  }
}
```

- `on_llm_response_chunk`: Process each chunk of streaming LLM output
- `on_llm_response_complete`: Process the complete LLM response

**Speech-to-Text Hooks:**
```json
{
  "hooks": {
    "on_llm_response_chunk": "process_chunk",
    "on_llm_response_complete": "process_complete"
  }
}
```

These hooks ensure:
- TTS speaks LLM responses automatically
- STT waits for TTS to finish before listening
- No overlap between speaking and listening

### Performance Tuning

#### Optimize Speech-to-Text Performance

**For Speed (Lower Latency):**
```json
{
  "settings": {
    "whisper_model": "tiny",      // Fastest model
    "sample_rate": 16000,          // Lower sample rate
    "chunk_duration": 0.05         // Smaller chunks
  }
}
```

**For Accuracy (Better Transcription):**
```json
{
  "settings": {
    "whisper_model": "medium",     // More accurate model
    "sample_rate": 44100,          // Higher quality audio
    "chunk_duration": 0.2          // Larger chunks
  }
}
```

**For Long Recordings:**
```json
{
  "settings": {
    "max_duration": 300,           // 5 minutes max
    "silence_timeout": 3.0,        // Longer pauses allowed
    "min_speech_duration": 0.5     // Prevent false stops
  }
}
```

#### Optimize Text-to-Speech Performance

**For Speed (Fast Response):**
```json
{
  "settings": {
    "rate": 250,                              // Faster speech
    "audio_clearance_buffer_macos": 0.3,      // Shorter buffer
    "audio_clearance_buffer_pyttsx3": 0.5
  }
}
```

**For Clarity (Better Understanding):**
```json
{
  "settings": {
    "rate": 160,                              // Slower, clearer speech
    "volume": 0.9,                            // Slightly quieter
    "audio_clearance_buffer_macos": 1.0       // Longer buffer
  }
}
```

### Integration with LLM Chat

When both modules are enabled during `llf chat`:

1. **You speak** → Speech-to-Text captures and transcribes
2. **Transcription sent to LLM** → LLM processes your request
3. **LLM responds** → Text-to-Speech speaks the response
4. **TTS finishes** → Speech-to-Text ready for next input

**Workflow Diagram:**
```
┌──────────────────────────────────────────────────────────┐
│                    Voice Chat Loop                        │
└──────────────────────────────────────────────────────────┘

1. User Speaks
   └─> Microphone captures audio
   └─> Whisper transcribes to text
   └─> Text sent to LLM

2. LLM Processing
   └─> Local model generates response
   └─> Response text generated

3. LLM Speaks
   └─> TTS converts response to audio
   └─> Speakers play audio
   └─> Wait for audio to finish

4. Ready for Next Input
   └─> Loop back to step 1
```

### Customizing Voice Personalities

You can create different voice profiles by adjusting settings:

**Professional Voice:**
```json
{
  "settings": {
    "voice_id": "com.apple.voice.compact.en-US.Alex",
    "rate": 180,
    "volume": 0.8
  }
}
```

**Friendly Voice:**
```json
{
  "settings": {
    "voice_id": "com.apple.voice.compact.en-US.Samantha",
    "rate": 200,
    "volume": 1.0
  }
}
```

**Technical Voice:**
```json
{
  "settings": {
    "voice_id": "com.apple.voice.compact.en-US.Tom",
    "rate": 160,
    "volume": 0.9
  }
}
```

---

## Best Practices

### 1. Test Before Using

Always test modules standalone before enabling them in chat:
```bash
# Test TTS
./bin/tools/test_text2speech.py "Testing before chat"

# Test STT
./bin/tools/test_speech2text.py

# Then enable for chat
llf module enable all
llf chat
```

### 2. Optimize for Your Environment

Adjust settings based on your setup:
- **Quiet room**: Lower `silence_threshold` (300-400)
- **Noisy environment**: Higher `silence_threshold` (600-800)
- **Fast conversations**: Shorter `silence_timeout` (1.0-1.5)
- **Thoughtful pauses**: Longer `silence_timeout` (2.0-3.0)

### 3. Choose the Right Whisper Model

| Situation | Recommended Model |
|-----------|-------------------|
| Quick testing | tiny |
| Daily use (default) | base |
| Important transcription | small or medium |
| Professional accuracy | large |
| Low-end hardware | tiny or base |
| High-end hardware | medium or large |

### 4. Monitor Resource Usage

Speech recognition can be resource-intensive:
```bash
# Check CPU/memory during transcription
top -pid $(pgrep -f "llf chat")

# If resources are constrained:
# - Use smaller Whisper model (tiny or base)
# - Lower sample rate (16000 instead of 44100)
# - Reduce max_duration
```

### 5. Keep Dependencies Updated

```bash
# Update speech-related packages
pip install --upgrade pyttsx3 sounddevice scipy openai-whisper

# Verify versions
pip list | grep -E "pyttsx3|sounddevice|scipy|whisper"
```

### 6. Backup Working Configurations

Before modifying settings:
```bash
# Backup module configs
cp modules/text2speech/module_info.json \
   modules/text2speech/module_info.json.backup

cp modules/speech2text/module_info.json \
   modules/speech2text/module_info.json.backup

# Restore if needed
cp modules/text2speech/module_info.json.backup \
   modules/text2speech/module_info.json
```

---

## Summary

You now have comprehensive knowledge of the Speech-to-Text and Text-to-Speech modules:

**Key Takeaways:**
1. **Enable/Disable**: Use `llf module enable/disable <module_name>`
2. **Test First**: Always test with standalone scripts before using in chat
3. **Configure**: Adjust settings in `modules/<module>/module_info.json`
4. **Troubleshoot**: Check hardware, test independently, enable debug logging
5. **Optimize**: Choose appropriate Whisper model and timing settings

**Quick Reference Commands:**
```bash
# Module management
llf module list                    # List all modules
llf module enable text2speech      # Enable TTS
llf module enable speech2text      # Enable STT
llf module enable all              # Enable both
llf module info text2speech        # Show TTS details

# Testing
./bin/tools/test_text2speech.py "Test"
./bin/tools/test_speech2text.py

# Usage
llf chat                           # Chat with voice (if enabled)
```

**Important File Locations:**
- Registry: `modules/modules_registry.json`
- TTS Module: `modules/text2speech/`
- STT Module: `modules/speech2text/`
- TTS Config: `modules/text2speech/module_info.json`
- STT Config: `modules/speech2text/module_info.json`
- TTS Test: `bin/tools/test_text2speech.py`
- STT Test: `bin/tools/test_speech2text.py`

**For More Help:**
- Review module_info.json for all available settings
- Check debug logs with `"debug_logging": true`
- Test hardware with standalone test scripts
- Adjust timing settings for your environment

Happy talking with your LLM! 🎤🔊

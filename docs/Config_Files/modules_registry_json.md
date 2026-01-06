# Modules Registry Guide: modules_registry.json

This document explains how to configure and manage pluggable modules using the `modules/modules_registry.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Parameters Reference](#parameters-reference)
4. [Enabled vs Disabled States](#enabled-vs-disabled-states)
5. [Module Types](#module-types)
6. [Configuration Examples](#configuration-examples)
7. [CLI Commands](#cli-commands)
8. [Built-in Modules](#built-in-modules)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Related Documentation](#related-documentation)

---

## Overview

The `modules_registry.json` file manages pluggable modules that extend the interaction capabilities between the LLM and user. It allows you to:

- Register multiple modules for different functionalities
- Enable/disable modules without removing them
- Configure module-specific settings
- Track module versions and dependencies
- **Automatically load and integrate modules when enabled**

**Location:** `modules/modules_registry.json`

**Key Concept:** Modules extend how the user interacts with the LLM by processing inputs or outputs. Examples include converting text to speech (output processor) or speech to text (input processor).

---

## Configuration Structure

A minimal module entry looks like this:

```json
{
  "version": "2.0",
  "last_updated": "2025-12-28",
  "modules": [
    {
      "name": "text2speech",
      "display_name": "Text-to-Speech",
      "description": "Converts LLM text output to spoken audio",
      "type": "output_processor",
      "directory": "text2speech",
      "enabled": false,
      "loaded": false,
      "info_file": "text2speech/module_info.json",
      "main_module": "text2speech",
      "version": "0.1.0",
      "dependencies": [
        "pyttsx3>=2.90"
      ]
    }
  ],
  "metadata": {
    "description": "Registry of all available modules for the LLM Framework",
    "schema_version": "2.0"
  }
}
```

---

## Parameters Reference

### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | Yes | - | Unique identifier for the module (lowercase, no spaces) |
| `display_name` | String | Yes | - | Human-readable name shown in CLI and UI |
| `description` | String | Yes | - | Brief description of the module's functionality |
| `type` | String | Yes | - | Module type: `output_processor`, `input_processor` |
| `directory` | String | Yes | - | Directory path where module code is stored (relative to `modules/`) |
| `enabled` | Boolean | Yes | `false` | Whether to load and use this module (true = active, false = inactive) |
| `loaded` | Boolean | Yes | `false` | Runtime status indicating if module is currently loaded |

### Optional Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `info_file` | String | No | `null` | Path to module info JSON file (relative to project root) |
| `main_module` | String | No | Same as `name` | Python module name to import |
| `version` | String | No | `"0.0.0"` | Module version number (semver format) |
| `dependencies` | Array | No | `[]` | List of Python package dependencies (pip format) |

---

## Enabled vs Disabled States

### Enabled (`"enabled": true`)

When a module is **enabled**:
- The module is loaded at framework startup
- Module functionality is available during LLM interactions
- For output processors: LLM responses are passed through the module
- For input processors: User inputs are processed by the module before sending to LLM
- The `loaded` field is set to `true` when successfully loaded

**Example Flow (Text-to-Speech enabled):**
```
User: "Tell me a joke"
LLM: "Why did the programmer quit his job? Because he didn't get arrays!"
[Text-to-Speech module speaks the response aloud]
```

### Disabled (`"enabled": false`)

When a module is **disabled**:
- The module code exists but is not loaded
- No processing occurs for that module type
- Useful for temporarily turning off functionality
- Can be re-enabled at any time via CLI or by editing the JSON

**Use Cases for Disabled:**
- When you don't want audio output (text2speech)
- When you prefer typing over speaking (speech2text)
- Testing without module processing
- Development and debugging
- Performance optimization

---

## Module Types

### Output Processor (`"type": "output_processor"`)

**Purpose:** Process or transform LLM output before presenting it to the user

**Flow:**
```
LLM generates response → Output Processor → User receives result
```

**Example Modules:**
- **Text-to-Speech**: Converts text responses to spoken audio
- **Markdown Formatter**: Renders markdown in a rich display
- **Translation**: Translates LLM response to another language
- **Code Highlighter**: Applies syntax highlighting to code blocks

**When It Runs:**
- After LLM generates a complete response
- Before displaying to the user
- Can modify or augment the output

---

### Input Processor (`"type": "input_processor"`)

**Purpose:** Process or transform user input before sending it to the LLM

**Flow:**
```
User provides input → Input Processor → Transformed input → LLM
```

**Example Modules:**
- **Speech-to-Text**: Converts spoken audio to text for the LLM
- **Image OCR**: Extracts text from images
- **File Parser**: Extracts content from uploaded files
- **Translation**: Translates user input to LLM's preferred language

**When It Runs:**
- After user provides input
- Before sending to LLM
- Can transform or augment the input

---

## Configuration Examples

### Example 1: Text-to-Speech Module

Enable audio output for LLM responses:

```json
{
  "name": "text2speech",
  "display_name": "Text-to-Speech",
  "description": "Converts LLM text output to spoken audio using pyttsx3",
  "type": "output_processor",
  "directory": "text2speech",
  "enabled": true,
  "loaded": false,
  "info_file": "text2speech/module_info.json",
  "main_module": "text2speech",
  "version": "0.1.0",
  "dependencies": [
    "pyttsx3>=2.90"
  ],
  "settings": {
    "voice_id": null,
    "rate": 200,
    "volume": 1.0
  }
}
```

**Use Case:** Have the LLM speak its responses aloud. Great for hands-free operation or accessibility.

---

### Example 2: Speech-to-Text Module

Enable voice input for conversations:

```json
{
  "name": "speech2text",
  "display_name": "Speech-to-Text",
  "description": "Converts user voice to text input for the LLM using openai-whisper",
  "type": "input_processor",
  "directory": "speech2text",
  "enabled": true,
  "loaded": false,
  "info_file": "speech2text/module_info.json",
  "main_module": "speech2text",
  "version": "0.1.0",
  "dependencies": [
    "sounddevice>=0.5.3",
    "scipy>=1.16.3",
    "openai-whisper>=20250625",
    "brew install ffmpeg"
  ],
  "settings": {
    "model_size": "base",
    "language": "en",
    "sample_rate": 16000
  }
}
```

**Use Case:** Speak your questions instead of typing them. Great for hands-free operation or when typing is inconvenient.

---

### Example 3: Both Modules Enabled

Full voice interaction (speak questions, hear responses):

```json
{
  "version": "2.0",
  "last_updated": "2025-12-28",
  "modules": [
    {
      "name": "text2speech",
      "display_name": "Text-to-Speech",
      "description": "Converts LLM text output to spoken audio using pyttsx3",
      "type": "output_processor",
      "directory": "text2speech",
      "enabled": true,
      "loaded": false,
      "info_file": "text2speech/module_info.json",
      "main_module": "text2speech",
      "version": "0.1.0",
      "dependencies": [
        "pyttsx3>=2.90"
      ]
    },
    {
      "name": "speech2text",
      "display_name": "Speech-to-Text",
      "description": "Converts user voice to text input for the LLM using openai-whisper",
      "type": "input_processor",
      "directory": "speech2text",
      "enabled": true,
      "loaded": false,
      "info_file": "speech2text/module_info.json",
      "main_module": "speech2text",
      "version": "0.1.0",
      "dependencies": [
        "sounddevice>=0.5.3",
        "scipy>=1.16.3",
        "openai-whisper>=20250625"
      ]
    }
  ]
}
```

**Use Case:** Completely hands-free LLM interaction. Speak your questions and hear the responses.

---

## CLI Commands

The framework provides convenient CLI commands for managing modules:

### List All Modules

```bash
# List all registered modules
llf module list

# List only enabled modules
llf module list --enabled
```

**Output:**
```
Text-to-Speech                 enabled
Speech-to-Text                 disabled
```

---

### Enable a Module

```bash
# Enable a specific module by name
llf module enable text2speech

# Enable by display name
llf module enable "Text-to-Speech"

# Enable all modules at once
llf module enable all
```

**Result:** Sets `"enabled": true` in the registry. The module will be loaded on next framework start or restart.

**Note:** You typically need to restart the CLI or application for module changes to take effect.

---

### Disable a Module

```bash
# Disable a specific module by name
llf module disable text2speech

# Disable by display name
llf module disable "Text-to-Speech"

# Disable all modules at once
llf module disable all
```

**Result:** Sets `"enabled": false` in the registry. The module will not be loaded on next framework start.

---

### Show Module Info

```bash
# Show detailed information about a module
llf module info text2speech

# Or use display name
llf module info "Text-to-Speech"
```

**Output:**
```
Text-to-Speech (text2speech) v0.1.0
  ✓ enabled
  Type: output_processor
  Description: Converts LLM text output to spoken audio using pyttsx3
  Location: /path/to/project/modules/text2speech
```

---

## Built-in Modules

### Text-to-Speech (text2speech)

**Type:** Output Processor
**Purpose:** Convert LLM text responses to spoken audio
**Technology:** pyttsx3 (offline text-to-speech)

**Features:**
- Offline processing (no internet required)
- Multiple voice options
- Adjustable speed and volume
- Cross-platform support

**Dependencies:**
```bash
pip install pyttsx3>=2.90
```

**Configuration:**
```json
{
  "name": "text2speech",
  "enabled": true,
  "settings": {
    "voice_id": null,       // null = default voice
    "rate": 200,            // Words per minute (150-300)
    "volume": 1.0           // Volume (0.0-1.0)
  }
}
```

**Usage:**
- Enable the module
- Start a chat session
- LLM responses are automatically spoken aloud

---

### Speech-to-Text (speech2text)

**Type:** Input Processor
**Purpose:** Convert user voice to text input for the LLM
**Technology:** OpenAI Whisper (high-quality speech recognition)

**Features:**
- High accuracy speech recognition
- Support for multiple languages
- Offline processing after model download
- Automatic voice activity detection

**Dependencies:**
```bash
pip install sounddevice>=0.5.3
pip install scipy>=1.16.3
pip install openai-whisper>=20250625

# On macOS (required for audio encoding)
brew install ffmpeg

# On Ubuntu/Debian
sudo apt-get install ffmpeg

# On Windows
# Download ffmpeg from https://ffmpeg.org/download.html
```

**Configuration:**
```json
{
  "name": "speech2text",
  "enabled": true,
  "settings": {
    "model_size": "base",    // tiny, base, small, medium, large
    "language": "en",        // Language code (en, es, fr, etc.)
    "sample_rate": 16000     // Audio sample rate
  }
}
```

**Usage:**
- Enable the module
- Start a chat session
- Press designated key to start recording
- Speak your question
- Press key again to stop and transcribe

---

## Best Practices

### Module Selection

**Enable Only What You Need:**
- Don't enable all modules by default
- Each module adds processing overhead
- Consider your actual workflow needs

**Combine Complementary Modules:**
- text2speech + speech2text = full voice interaction
- But only enable if you actually use voice

---

### Dependency Management

**Install Dependencies Before Enabling:**
```bash
# Check module requirements first
llf module info text2speech

# Install dependencies
pip install pyttsx3>=2.90

# Then enable
llf module enable text2speech
```

**Keep Dependencies Updated:**
```bash
# Update specific package
pip install --upgrade pyttsx3

# Update all packages in requirements
pip install --upgrade -r requirements.txt
```

---

### Performance Considerations

**Text-to-Speech:**
- First use may be slower (voice initialization)
- Subsequent responses are faster
- Minimal CPU overhead
- No internet required

**Speech-to-Text:**
- First use downloads Whisper model (~100MB-3GB depending on size)
- Model runs locally (no internet after download)
- CPU/GPU usage during transcription
- Larger models = better accuracy but slower

**Model Size Tradeoff:**
- `tiny`: Fastest, lowest accuracy, ~75MB
- `base`: Good balance, recommended, ~142MB
- `small`: Better accuracy, ~466MB
- `medium`: Very good accuracy, ~1.5GB
- `large`: Best accuracy, ~2.9GB

---

### Module Configuration

**Store Settings in module_info.json:**
```json
{
  "name": "text2speech",
  "version": "0.1.0",
  "settings": {
    "voice_id": "com.apple.speech.synthesis.voice.samantha",
    "rate": 180,
    "volume": 0.9
  }
}
```

**Benefits:**
- Settings persist across sessions
- Easy to modify without code changes
- Can be version controlled

---

## Troubleshooting

### Problem: Module not loading

**Solution:**
1. Check that `"enabled": true` in the registry
2. Verify all dependencies are installed: `pip list`
3. Check for errors in the logs
4. Restart the framework/CLI
5. Verify module directory exists: `modules/[module_name]/`

---

### Problem: Text-to-Speech not speaking

**Solution:**
1. Check audio output is not muted
2. Verify audio drivers are working (play other audio)
3. Check module settings (volume should be > 0)
4. Look for errors in logs
5. Try a different voice_id

**List available voices:**
```python
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(voice.id)
```

---

### Problem: Speech-to-Text not recognizing voice

**Solution:**
1. Check microphone is connected and working
2. Verify microphone permissions (macOS/Windows)
3. Check input volume levels
4. Try a larger Whisper model (`small` or `medium`)
5. Ensure ffmpeg is installed: `ffmpeg -version`
6. Speak clearly and reduce background noise

---

### Problem: Dependencies won't install

**Solution:**
1. Update pip: `pip install --upgrade pip`
2. Check Python version (3.8+ required)
3. For pyttsx3 on macOS: Install using system Python or ensure pyobjc is installed
4. For Whisper: Ensure you have enough disk space for models
5. For ffmpeg: Follow platform-specific installation instructions

---

### Problem: Module enabled but "loaded": false

**Solution:**
1. Check for import errors in logs
2. Verify all dependencies are installed correctly
3. Check module directory has `__init__.py`
4. Verify main_module name matches actual Python module
5. Check for syntax errors in module code

---

### Problem: High CPU usage with speech2text

**Solution:**
1. Use a smaller Whisper model: `"model_size": "tiny"` or `"base"`
2. Reduce sample_rate: `"sample_rate": 8000`
3. Ensure you're not recording continuously
4. Close other CPU-intensive applications
5. Consider using GPU acceleration if available

---

## Related Documentation

- [Main Configuration](config_json.md) - LLM endpoint and server configuration
- [Prompt Configuration](config_prompt_json.md) - System prompts and message formatting
- [Data Store Registry](data_store_registry_json.md) - RAG vector store configuration
- [Memory Registry](memory_registry_json.md) - Long-term memory configuration
- [Tools Registry](tools_registry_json.md) - Tool system configuration

---

## Additional Resources

### Module Directory Structure

Each module directory typically contains:
```
modules/
├── modules_registry.json          # This registry file
├── text2speech/                   # Example module
│   ├── __init__.py                # Module entry point
│   ├── module_info.json           # Module metadata and settings
│   ├── text2speech.py             # Main implementation
│   └── README.md                  # Module documentation
└── speech2text/                   # Another module
    ├── __init__.py
    ├── module_info.json
    ├── speech2text.py
    └── README.md
```

### Creating Custom Modules

To create a custom module:

1. Create directory in `modules/[your_module_name]/`
2. Add `__init__.py` with module class
3. Add `module_info.json` with metadata
4. Register in `modules_registry.json`
5. Install dependencies
6. Enable via CLI

**Example module class structure:**
```python
class MyModule:
    def __init__(self, settings=None):
        self.settings = settings or {}

    def process(self, input_data):
        # Your processing logic
        return processed_data
```

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.

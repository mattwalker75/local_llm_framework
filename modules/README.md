# Modules Directory

This directory is designated for storing modules that extend the **engagement ability between the LLM and user**.

## Purpose

Modules enhance the interaction experience between users and the LLM by adding capabilities such as:
- Text-to-speech (TTS) for audio output
- Speech-to-text (STT) for voice input
- Audio processing and streaming
- Alternative input/output methods
- User interface extensions

## Current Status

**This feature is currently a placeholder.** The module management commands are available in the CLI but not yet implemented:

```bash
llf module list                  # List modules
llf module list --enabled        # List only enabled modules
llf module enable                # Enable a module
llf module disable               # Disable a module
llf module info MODULE_NAME      # Show module information
```

## Future Implementation

When implemented, this directory will contain:
- Module plugin files (Python modules)
- Module configuration files
- Audio processing modules
- Voice interface modules
- Custom UI extension modules

## Module Types (Planned)

### Input Modules
- **Speech-to-Text**: Convert voice input to text for LLM processing
- **Image Input**: Process images for multimodal interaction
- **File Upload**: Handle file-based inputs

### Output Modules
- **Text-to-Speech**: Convert LLM responses to audio
- **Audio Streaming**: Real-time audio output
- **Rich Media**: Display formatted content, images, or videos

### Interaction Modules
- **Multi-modal Chat**: Combine text, voice, and visual interactions
- **Accessibility**: Screen readers, keyboard shortcuts, alternative interfaces
- **Notifications**: Audio/visual alerts for LLM responses

## Usage

For now, this directory serves as a placeholder. Future versions of LLF will support:
1. Installing modules from a module registry
2. Enabling/disabling modules dynamically
3. Configuring module-specific settings
4. Chaining multiple modules together

## Related Documentation

- See [README.md](../README.md) for general LLF information
- See [docs/USAGE.md](../docs/USAGE.md) for command usage
- See [docs/CONFIG_README.md](../docs/CONFIG_README.md) for configuration options

---

**Note:** This feature is planned for a future release. The current version (v0.1.0) focuses on core LLM interaction capabilities.

# Voice Features Quick Start Guide

## Setup (One-Time)

### Enable Voice Modules
```bash
# Enable Text-to-Speech (voice output)
llf module enable text2speech

# Enable Speech-to-Text (voice input)
llf module enable speech2text

# Check status
llf module list
```

---

## Terminal Usage (llf chat)

### Start Interactive Chat
```bash
llf chat
```

### With Voice Input Enabled:
1. You'll see: `🎤 Listening... (speak now, pause when done)`
2. Speak your question
3. Pause for 1.5 seconds
4. You'll see: `Transcribed: [your text]`
5. LLM processes and responds
6. If TTS enabled: Response is spoken aloud

### Disable Voice Features:
```bash
llf module disable text2speech   # Turn off voice output
llf module disable speech2text   # Turn off voice input
```

---

## GUI Usage (llf gui)

### Start GUI
```bash
llf gui
# Or with share mode (for remote access)
llf gui --share
```

### Interface Elements:

#### 🔊 Voice Output Checkbox
- **Location**: Right sidebar, below "Enter to send"
- **Purpose**: Toggle spoken responses on/off
- **Default**: Checked (enabled)
- **Only shows if**: text2speech module is enabled

#### 🎤 Record Voice Button
- **Location**: Right sidebar, below Voice Output checkbox
- **Purpose**: Click to record voice input
- **Only shows if**: speech2text module is enabled

#### Voice Status (Hidden by default)
- **Appears when**: Recording voice
- **Shows**:
  - `🎤 Listening... (speak now, pause when done)`
  - `✅ Transcribed: [your text]`
  - `⚠️ Voice input failed: [error]`

---

## Usage Workflows

### Workflow 1: Voice Input Only
```bash
llf module enable speech2text
llf module disable text2speech
llf gui
```

**Result**:
- "🎤 Record Voice" button visible
- Click to speak
- Text appears in message box
- LLM response shown as text (not spoken)

---

### Workflow 2: Voice Output Only
```bash
llf module disable speech2text
llf module enable text2speech
llf gui
```

**Result**:
- "🔊 Voice Output" checkbox visible
- Type messages normally
- LLM responses are spoken aloud
- Uncheck to disable speech

---

### Workflow 3: Both Voice Features
```bash
llf module enable speech2text
llf module enable text2speech
llf gui
```

**Result**:
- Both "🔊 Voice Output" and "🎤 Record Voice" visible
- Speak questions → Hear responses
- Full hands-free conversation
- Toggle voice output on/off as needed

---

### Workflow 4: No Voice Features
```bash
llf module disable speech2text
llf module disable text2speech
llf gui
```

**Result**:
- No voice controls shown
- Standard text-only chat interface
- Type messages, read responses

---

## Example: Complete Voice Conversation

```bash
# Setup
llf module enable text2speech
llf module enable speech2text
llf gui
```

**In GUI**:

1. **Click** "🎤 Record Voice"
2. **Status shows**: `🎤 Listening... (speak now, pause when done)`
3. **Speak**: "What is the weather like today?"
4. **Status shows**: `✅ Transcribed: What is the weather like today?`
5. **Message auto-submits** to LLM
6. **LLM responds** (text in chat + spoken aloud)
7. **Audio clears** (no feedback loop)
8. **Click** "🎤 Record Voice" again for next question

**Toggle Voice Output Mid-Conversation**:

1. **Uncheck** "🔊 Voice Output" checkbox
2. **Ask another question** (via voice or text)
3. **LLM responds** with text only (no speech)
4. **Check** "🔊 Voice Output" again
5. **Next response** is spoken aloud

---

## Troubleshooting

### Voice Input Not Working

**Check Module Status**:
```bash
llf module list
# Ensure speech2text shows "enabled: true"
```

**Check Microphone Permission**:
- macOS: System Settings → Privacy & Security → Microphone
- Ensure your terminal/Python has permission

**Check Audio Input**:
```bash
# Test microphone in terminal
python -c "import sounddevice as sd; print(sd.query_devices())"
```

**Error Message Shows**:
- Read the error in the status box
- Common issues:
  - No microphone detected
  - Whisper model not downloaded
  - Audio timeout (spoke too long)

---

### Voice Output Not Working

**Check Module Status**:
```bash
llf module list
# Ensure text2speech shows "enabled: true"
```

**Check Checkbox**:
- Look for "🔊 Voice Output" checkbox in GUI
- Ensure it's checked

**Check Audio Output**:
```bash
# Test TTS in terminal
llf chat
# Should hear responses when enabled
```

**No Sound**:
- Check system volume
- Check if headphones are connected
- macOS: Check Sound settings

---

### "Record Voice" Button Missing

**Reason**: speech2text module not enabled

**Fix**:
```bash
llf module enable speech2text
# Restart GUI
llf gui
```

---

### "Voice Output" Checkbox Missing

**Reason**: text2speech module not enabled

**Fix**:
```bash
llf module enable text2speech
# Restart GUI
llf gui
```

---

### Audio Feedback Loop

**Symptoms**: LLM "hears itself" and transcribes its own speech

**Should NOT happen** if both modules enabled correctly - the system uses `wait_for_tts_clearance()` to prevent this.

**If it does happen**:
1. Uncheck "🔊 Voice Output"
2. Report the issue (this is a bug)

---

## Performance Notes

### First Voice Input (Slower)
- **First time**: ~10-30 seconds
- **Reason**: Downloading/loading Whisper model
- **Subsequent uses**: ~1-3 seconds

### Voice Output Speed
- **macOS**: Natural, accurate timing
- **Windows/Linux**: May have slight delay (estimation-based)

### Voice Input Timeout
- **Default**: 60 seconds max recording
- **Silence timeout**: 1.5 seconds of silence = end of speech
- **Configurable**: Edit `modules/speech2text/module_info.json`

---

## Module Configuration

### Speech-to-Text Settings
**File**: `modules/speech2text/module_info.json`

```json
{
  "settings": {
    "whisper_model": "base",           // tiny, base, small, medium, large
    "silence_timeout": 1.5,            // Seconds of silence to end recording
    "max_duration": 60,                // Max recording length (seconds)
    "silence_threshold": 500,          // Audio level threshold
    "debug_logging": false             // Enable debug logs
  }
}
```

### Text-to-Speech Settings
**File**: `modules/text2speech/module_info.json`

```json
{
  "settings": {
    "rate": 200,                       // Speech rate (words per minute)
    "volume": 1.0,                     // Volume (0.0 to 1.0)
    "debug_logging": false             // Enable debug logs
  }
}
```

---

## Quick Command Reference

```bash
# Enable/Disable Modules
llf module enable text2speech
llf module enable speech2text
llf module disable text2speech
llf module disable speech2text

# List Modules
llf module list

# Module Info
llf module info text2speech
llf module info speech2text

# Start Chat/GUI
llf chat              # Terminal with voice
llf gui               # GUI with voice
llf gui --share       # GUI with voice (shareable URL)
```

---

## Summary

| Feature | Terminal | GUI | How to Enable |
|---------|----------|-----|---------------|
| **Voice Input (STT)** | Automatic on every input | Click "🎤 Record Voice" button | `llf module enable speech2text` |
| **Voice Output (TTS)** | Always on (if enabled) | Toggle "🔊 Voice Output" checkbox | `llf module enable text2speech` |
| **Status Messages** | Console text | Status textbox (appears during recording) | Automatic |
| **Error Handling** | Fallback to keyboard | Clear error message in status box | Automatic |

**Enjoy hands-free conversations with your LLM!** 🎤🔊

# GUI Dynamic Module Reload

## Overview

The GUI now supports **dynamic module reloading** - you can enable/disable TTS and STT modules from the terminal and reload them in the GUI without restarting! The voice controls appear and disappear based on which modules are currently enabled.

---

## Quick Guide

### Enable/Disable Modules:
```bash
# In a separate terminal (while GUI is running)
llf module enable text2speech
llf module enable speech2text

# Or disable
llf module disable text2speech
llf module disable speech2text
```

### Reload in GUI:
1. Click **"🔄 Reload Modules"** button in the Chat tab
2. Voice controls appear/disappear based on enabled modules
3. Status message shows which modules were loaded

**No restart required!** ✨

---

## User Interface

### New Button:

**🔄 Reload Modules** (Secondary button, gray)
- **Location**: Chat tab, below "Clear Chat" button
- **Purpose**: Reload module registry and update voice controls
- **Shows**: Temporary status message (3 seconds)

### Dynamic Elements:

**🔊 Voice Output** (Checkbox)
- **Visible when**: text2speech module enabled
- **Hidden when**: text2speech module disabled
- **Updates**: Automatically when "Reload Modules" clicked

**🎤 Start Listening / 🛑 Stop Listening** (Buttons)
- **Visible when**: speech2text module enabled
- **Hidden when**: speech2text module disabled
- **Updates**: Automatically when "Reload Modules" clicked

---

## Status Messages

After clicking "🔄 Reload Modules", you'll see:

### Both Modules Enabled:
```
✅ Modules reloaded: Text-to-Speech, Speech-to-Text
```

### Only TTS Enabled:
```
✅ Modules reloaded: Text-to-Speech
```

### Only STT Enabled:
```
✅ Modules reloaded: Speech-to-Text
```

### No Modules Enabled:
```
⭕ No modules currently enabled
```

### Error:
```
❌ Error reloading modules: [error message]
```

---

## Example Workflows

### Workflow 1: Start with No Modules, Enable Dynamically

**Initial State:**
```bash
# Modules disabled
llf module disable text2speech
llf module disable speech2text
llf gui
```

**In GUI:**
- No voice controls visible
- Only text chat available

**Enable STT:**
```bash
# In terminal
llf module enable speech2text
```

**In GUI:**
1. Click "🔄 Reload Modules"
2. Status shows: "✅ Modules reloaded: Speech-to-Text"
3. "🎤 Start Listening" button appears!
4. Can now use voice input

**Enable TTS:**
```bash
# In terminal
llf module enable text2speech
```

**In GUI:**
1. Click "🔄 Reload Modules"
2. Status shows: "✅ Modules reloaded: Text-to-Speech, Speech-to-Text"
3. "🔊 Voice Output" checkbox appears!
4. Can now use voice input AND output

---

### Workflow 2: Disable Modules Mid-Session

**Initial State:**
```bash
# Both modules enabled
llf module enable text2speech
llf module enable speech2text
llf gui
```

**In GUI:**
- Both voice controls visible
- Can use voice conversation

**Disable TTS:**
```bash
# In terminal
llf module disable text2speech
```

**In GUI:**
1. Click "🔄 Reload Modules"
2. Status shows: "✅ Modules reloaded: Speech-to-Text"
3. "🔊 Voice Output" checkbox disappears
4. Voice input still works, but no spoken output

**Disable STT:**
```bash
# In terminal
llf module disable speech2text
```

**In GUI:**
1. Click "🔄 Reload Modules"
2. Status shows: "⭕ No modules currently enabled"
3. All voice controls disappear
4. Back to text-only chat

---

### Workflow 3: Change Module Settings

**Update STT Settings:**
```bash
# Edit settings
vim modules/speech2text/module_info.json
# Change whisper_model from "base" to "small"
```

**In GUI:**
1. Click "🔄 Reload Modules"
2. Status shows: "✅ Modules reloaded: Speech-to-Text"
3. STT now uses new settings (larger model, better accuracy)

---

## Technical Details

### What Happens on Reload:

1. **Stops active operations**:
   - Exits listening mode (if active)
   - Stops TTS playback (if active)

2. **Clears old instances**:
   - Cleans up TTS engine
   - Cleans up STT engine

3. **Reloads module registry**:
   - Reads `modules/modules_registry.json`
   - Checks which modules are enabled

4. **Initializes new instances**:
   - Creates new TTS engine (if enabled)
   - Creates new STT engine (if enabled)
   - Loads settings from `module_info.json`

5. **Updates UI**:
   - Shows/hides TTS checkbox
   - Shows/hides STT buttons
   - Displays status message

### Safety Features:

**Module Not Available**:
- If you click "🎤 Start Listening" but STT module isn't loaded:
  ```
  ⚠️ Speech-to-Text module not enabled. Use 'llf module enable speech2text' and click Reload Modules.
  ```

**Listening Mode Auto-Stop**:
- If listening mode is active when you click "Reload Modules"
- Automatically stops listening
- Prevents errors from missing STT instance

**Graceful Fallback**:
- If reload fails, UI keeps existing state
- Shows error message
- Can retry reload

---

## Comparison: Before vs After

### Before (Old Behavior):
1. Enable/disable modules in terminal
2. **Restart entire GUI** to see changes
3. Lose chat history
4. Reconnect to server

### After (New Behavior):
1. Enable/disable modules in terminal
2. **Click "🔄 Reload Modules"** button
3. Voice controls appear/disappear instantly
4. Chat history preserved
5. Server connection maintained

**Result**: Seamless module management without disrupting your session!

---

## Module Registry

The reload button reads from:
```
modules/modules_registry.json
```

Example:
```json
{
  "modules": [
    {
      "name": "text2speech",
      "enabled": true,
      "path": "modules/text2speech"
    },
    {
      "name": "speech2text",
      "enabled": true,
      "path": "modules/speech2text"
    }
  ]
}
```

---

## Troubleshooting

### Button Doesn't Respond

**Check**:
- Is GUI still running?
- Any errors in terminal?

**Fix**:
- Refresh browser (Gradio GUI)
- Restart if needed: `Ctrl+C` then `llf gui`

---

### Modules Not Appearing After Reload

**Check Module Status**:
```bash
llf module list
```

**Verify Enabled**:
```bash
llf module info text2speech
llf module info speech2text
```

**Common Issues**:
- Module not actually enabled (shows `enabled: false`)
- Module dependencies missing
- Syntax error in `module_info.json`

**Fix**:
```bash
# Re-enable module
llf module enable text2speech

# Check logs for errors
llf gui
# Look for "Failed to load..." warnings
```

---

### Chat History Lost

**This should NOT happen!**

The reload only affects voice modules, not chat history.

If history is lost:
- This is a bug - please report
- Workaround: Use "Clear Chat" button before reload

---

## Benefits

✅ **No Restart Required**: Enable/disable modules without restarting GUI
✅ **Preserved State**: Chat history and server connection maintained
✅ **Instant Feedback**: Status message shows what loaded
✅ **Clean UI**: Controls appear/disappear based on module availability
✅ **Safe**: Auto-stops listening mode, prevents errors
✅ **Flexible**: Change module settings mid-session

---

## Summary

| Action | Terminal Command | GUI Action | Result |
|--------|------------------|------------|---------|
| **Enable TTS** | `llf module enable text2speech` | Click "🔄 Reload Modules" | 🔊 checkbox appears |
| **Disable TTS** | `llf module disable text2speech` | Click "🔄 Reload Modules" | 🔊 checkbox disappears |
| **Enable STT** | `llf module enable speech2text` | Click "🔄 Reload Modules" | 🎤 buttons appear |
| **Disable STT** | `llf module disable speech2text` | Click "🔄 Reload Modules" | 🎤 buttons disappear |
| **Update Settings** | Edit `module_info.json` | Click "🔄 Reload Modules" | New settings applied |

**Enjoy dynamic module management!** 🔄

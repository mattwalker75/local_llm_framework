# GUI Speech-to-Text and Text-to-Speech Improvements

## Overview

Redesigned the GUI's STT/TTS interface to match the clean, terminal-like experience with simple status notifications instead of bulky audio players.

---

## Problems Solved

### Before (Issues)
1. **Bulky Audio Player**: `gr.Audio` component showed full waveform display, playback controls, and timeline (as seen in SCREENSHOT.png)
2. **No Status Messages**: Users didn't see clear "Listening..." or "Transcribed:" notifications
3. **No TTS Control**: Users couldn't easily enable/disable voice output without changing module settings
4. **Complex Interface**: Too many controls for simple voice input

### After (Solutions)
1. **Simple Button**: Clean "🎤 Record Voice" button
2. **Status Notifications**: Terminal-style status messages:
   - "🎤 Listening... (speak now, pause when done)"
   - "✅ Transcribed: [your text]"
   - "⚠️ Voice input failed: [error]"
3. **TTS Toggle**: "🔊 Voice Output" checkbox to enable/disable spoken responses
4. **Clean Interface**: Minimal, focused controls

---

## Changes Made

### File: `llf/gui.py`

#### 1. Replaced Audio Player with Button (Lines 919-933)

**Before**:
```python
# Add microphone toggle if STT is enabled
if self.stt:
    mic_toggle = gr.Checkbox(
        label="🎤 Voice Input",
        value=False,
        container=False
    )

# Audio input component (only visible when mic toggle is on and STT enabled)
if self.stt:
    audio_input = gr.Audio(
        sources=["microphone"] if self.is_share_mode else None,
        type="filepath",
        label="Voice Input",
        visible=False
    )
```

**After**:
```python
# Add voice recording button if STT is enabled
if self.stt:
    voice_btn = gr.Button("🎤 Record Voice", size="sm")

# Voice input status message (only show when STT is enabled)
if self.stt:
    voice_status = gr.Textbox(
        label="Voice Status",
        value="",
        interactive=False,
        visible=False,
        lines=1,
        show_label=False
    )
```

**Reason**: Simple button + hidden status textbox replaces bulky audio player interface.

---

#### 2. Added TTS Toggle Checkbox (Lines 919-926)

**New Code**:
```python
# Add TTS toggle if TTS module is available
if self.tts:
    tts_enabled = gr.Checkbox(
        label="🔊 Voice Output",
        value=True,  # Enabled by default
        container=False,
        info="Enable/disable spoken responses"
    )
```

**Reason**: Allows users to toggle voice output without changing module settings.

---

#### 3. Added TTS State Tracking (Line 68)

**New Code**:
```python
self.tts_enabled_state = True  # Track if user wants TTS enabled (separate from module availability)
```

**Reason**: Separate state for user preference vs module availability.

---

#### 4. Updated chat_respond to Check TTS State (Line 247)

**Before**:
```python
if self.tts and response_text:
```

**After**:
```python
if self.tts and self.tts_enabled_state and response_text:
```

**Reason**: Only speak if module is loaded AND user has toggle enabled.

---

#### 5. Added TTS Toggle Event Handler (Lines 1113-1120)

**New Code**:
```python
# TTS toggle event handler (if TTS is available)
if self.tts:
    def toggle_tts(enabled):
        """Update TTS enabled state when user toggles checkbox."""
        self.tts_enabled_state = enabled
        return None  # No UI update needed

    tts_enabled.change(toggle_tts, inputs=[tts_enabled], outputs=[])
```

**Reason**: Update internal state when user toggles checkbox.

---

#### 6. Implemented Clean Voice Recording (Lines 1123-1175)

**New Code**:
```python
def record_and_transcribe():
    """
    Record voice input and transcribe it to text.
    Returns updates for: voice_status (visible, value), msg (value), voice_status (visible, value)
    """
    try:
        # Show status: Listening
        yield (
            gr.update(visible=True, value="🎤 Listening... (speak now, pause when done)"),
            gr.update(),  # msg unchanged
            gr.update()   # Keep status showing
        )

        # Record and transcribe
        text = self.stt.listen()

        # Show status: Transcribed
        transcribed_msg = f"✅ Transcribed: {text}"
        yield (
            gr.update(visible=True, value=transcribed_msg),
            gr.update(value=text),  # Populate message box
            gr.update()
        )

        # Hide status after a moment (user will see it before auto-submit)
        import time
        time.sleep(0.5)
        yield (
            gr.update(visible=False, value=""),
            gr.update(),  # msg unchanged
            gr.update()
        )

    except Exception as e:
        logger.error(f"Voice input error: {e}")
        error_msg = f"⚠️ Voice input failed: {str(e)}"
        yield (
            gr.update(visible=True, value=error_msg),
            gr.update(value=""),  # Clear message box on error
            gr.update()
        )

        # Hide error after a moment
        import time
        time.sleep(2)
        yield (
            gr.update(visible=False, value=""),
            gr.update(),
            gr.update()
        )

# Voice button click: record -> transcribe -> populate textbox -> auto-submit
voice_btn.click(
    record_and_transcribe,
    inputs=[],
    outputs=[voice_status, msg, voice_status]
).then(
    # Auto-submit the transcribed text
    self.chat_respond,
    inputs=[msg, chatbot],
    outputs=[msg, chatbot]
)
```

**Reason**: Clean status updates matching terminal experience, with generator pattern for real-time UI updates.

---

#### 7. Updated Browser TTS to Check Checkbox (Lines 958-963)

**New Code**:
```javascript
// Check if TTS is enabled via checkbox
const ttsCheckbox = document.querySelector('input[type="checkbox"][aria-label*="Voice Output"]');
if (ttsCheckbox && !ttsCheckbox.checked) {
    console.log('[TTS] Voice Output is disabled, skipping TTS');
    return;
}
```

**Reason**: Browser TTS (share mode) respects the user's toggle preference.

---

## User Experience Flow

### Voice Input (STT):

1. User clicks "🎤 Record Voice" button
2. Status appears: "🎤 Listening... (speak now, pause when done)"
3. User speaks, then pauses (1.5 second default silence)
4. Status updates: "✅ Transcribed: Hello, how are you?"
5. Text populates in message box
6. Status disappears after 0.5 seconds
7. Message auto-submits to LLM
8. LLM response appears

### Voice Output (TTS):

**Enabled (checkbox checked)**:
- LLM response is spoken aloud
- If STT also enabled: waits for audio clearance before next input

**Disabled (checkbox unchecked)**:
- LLM response appears in chat (text only, no speech)
- User can toggle on/off at any time

### Error Handling:

If voice recording fails:
- Status shows: "⚠️ Voice input failed: [error message]"
- Message box cleared
- Status disappears after 2 seconds
- User can try again

---

## Comparison: Terminal vs GUI

| Feature | Terminal (llf chat) | GUI (llf gui) |
|---------|---------------------|---------------|
| **STT Trigger** | Automatic on every input | Click "🎤 Record Voice" button |
| **Listening Status** | `🎤 Listening...` | `🎤 Listening...` (in status box) |
| **Transcription** | `Transcribed: [text]` | `✅ Transcribed: [text]` (in status box) |
| **TTS Control** | Always on (if module enabled) | Toggle checkbox "🔊 Voice Output" |
| **Error Display** | `⚠️ STT failed, falling back...` | `⚠️ Voice input failed: [error]` |
| **Interface** | Text-based console | Clean button + status messages |

**Result**: Both interfaces now provide the same clean, status-message-based experience.

---

## Configuration

### Enable Modules:
```bash
llf module enable text2speech   # For voice output
llf module enable speech2text   # For voice input
```

### Disable Modules:
```bash
llf module disable text2speech
llf module disable speech2text
```

### GUI Behavior Based on Module State:

| TTS Module | STT Module | GUI Shows |
|------------|------------|-----------|
| ❌ Disabled | ❌ Disabled | No voice features |
| ✅ Enabled | ❌ Disabled | "🔊 Voice Output" checkbox only |
| ❌ Disabled | ✅ Enabled | "🎤 Record Voice" button only |
| ✅ Enabled | ✅ Enabled | Both checkbox and button |

---

## Testing

### Test STT in GUI:
```bash
llf module enable speech2text
llf gui
```

1. Click "🎤 Record Voice" button
2. Verify status shows "🎤 Listening..."
3. Speak clearly
4. Verify status shows "✅ Transcribed: [your text]"
5. Verify text populates in message box
6. Verify message auto-submits to LLM

### Test TTS in GUI:
```bash
llf module enable text2speech
llf gui
```

1. Type a message and send
2. Verify LLM response is spoken aloud
3. Uncheck "🔊 Voice Output"
4. Type another message
5. Verify response is NOT spoken (text only)
6. Re-check "🔊 Voice Output"
7. Verify next response IS spoken

### Test Both Together:
```bash
llf module enable text2speech
llf module enable speech2text
llf gui
```

1. Click "🎤 Record Voice"
2. Speak a question
3. Verify transcription appears
4. Verify LLM responds (text + speech)
5. Verify audio clearance works (no feedback loop)
6. Toggle "🔊 Voice Output" off
7. Record another question
8. Verify response is text-only (no speech)

---

## Benefits

1. **Clean Interface**: No bulky audio players or waveform displays
2. **Terminal Parity**: GUI now matches terminal experience for voice features
3. **User Control**: Easy toggle for voice output without changing module settings
4. **Clear Feedback**: Status messages keep user informed at each step
5. **Error Handling**: Graceful fallback with clear error messages
6. **No Feedback Loops**: Proper audio clearance when both TTS and STT enabled

---

## Technical Notes

### Generator Pattern:
The `record_and_transcribe()` function uses Python generators with `yield` to provide real-time UI updates:
- Shows "Listening..." immediately
- Updates to "Transcribed: [text]" when done
- Hides status after brief delay

This creates a smooth, responsive user experience matching the terminal's real-time status messages.

### Browser TTS Checkbox Detection:
The JavaScript code searches for the checkbox by aria-label to respect user preferences in share mode:
```javascript
const ttsCheckbox = document.querySelector('input[type="checkbox"][aria-label*="Voice Output"]');
if (ttsCheckbox && !ttsCheckbox.checked) {
    return;  // Skip TTS if disabled
}
```

### State Management:
- `self.tts`: TTS module instance (None if module disabled)
- `self.tts_enabled_state`: User's toggle preference (boolean)
- TTS only speaks if: `self.tts and self.tts_enabled_state and response_text`

---

## Summary

✅ **Clean Interface**: Removed bulky audio player, added simple button + status
✅ **Terminal Parity**: GUI now matches terminal experience
✅ **TTS Control**: Easy toggle for voice output
✅ **Status Messages**: Clear feedback at each step
✅ **Error Handling**: Graceful fallback with helpful messages
✅ **User-Friendly**: Intuitive controls, no configuration needed

The GUI now provides a clean, terminal-like voice experience with simple controls and clear status notifications!

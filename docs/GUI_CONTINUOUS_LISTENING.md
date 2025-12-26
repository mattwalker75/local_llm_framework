# GUI Continuous Listening Mode

## Overview

The GUI now features **continuous listening mode** that works exactly like the terminal version - once activated, it automatically listens for your voice after the LLM finishes responding, creating a seamless hands-free conversation flow.

---

## User Interface

### Buttons (when STT module enabled):

**🎤 Start Listening** (Primary, blue button)
- Click to enter continuous listening mode
- Button hides when listening mode is active
- Remains highlighted/active during the session

**🛑 Stop Listening** (Stop, red button)
- Only visible when listening mode is active
- Click to exit continuous listening mode
- Returns to manual text input

**🔊 Voice Output** (Checkbox)
- Toggle spoken responses on/off
- Independent of listening mode
- Works in both text and voice modes

---

## How It Works

### Workflow:

1. **User clicks "🎤 Start Listening"**
   - Listening mode activates
   - Start button hides, Stop button appears
   - Status shows: "🎤 Listening... (speak now, pause when done)"

2. **User speaks**
   - Pause for 1.5 seconds when done
   - Status shows: "✅ Transcribed: [your text]"
   - Message auto-submits to LLM

3. **LLM responds**
   - Response streams in chat
   - If TTS enabled: Response is spoken aloud
   - Status shows: "🔊 Speaking..."

4. **Auto-loop: Immediately listens again**
   - After TTS completes (or immediately if TTS disabled)
   - Status shows: "🎤 Listening... (speak now, pause when done)"
   - **Repeats from step 2**

5. **User clicks "🛑 Stop Listening"**
   - Exits continuous mode
   - Stop button hides, Start button appears
   - Returns to normal text input

---

## Comparison: Terminal vs GUI

| Feature | Terminal (`llf chat`) | GUI (`llf gui`) |
|---------|----------------------|----------------|
| **Activation** | Automatic (if STT enabled) | Click "🎤 Start Listening" |
| **Deactivation** | Disable module | Click "🛑 Stop Listening" |
| **Continuous Mode** | Always on | Toggle on/off |
| **Status Messages** | Console output | Status textbox |
| **TTS Control** | Module setting only | Checkbox + module setting |
| **Manual Input** | Fallback on error | Always available (when not listening) |

**Result**: Both provide seamless continuous conversation, GUI adds flexibility to switch between modes.

---

## Status Messages

The GUI shows clear status messages during the listening loop:

### Listening:
```
🎤 Listening... (speak now, pause when done)
```

### Transcribed:
```
✅ Transcribed: What is the weather today?
```

### Speaking (if TTS enabled):
```
🔊 Speaking...
```

### Error:
```
⚠️ Voice input failed: [error message]
```

### No Speech Detected:
```
⚠️ No speech detected, listening again...
```

---

## Example Session

```
User: *clicks "🎤 Start Listening"*

[Status: 🎤 Listening... (speak now, pause when done)]

User: *speaks* "What is machine learning?"

[Status: ✅ Transcribed: What is machine learning?]

[LLM responds with explanation...]

[Status: 🔊 Speaking...]

[TTS speaks the response]

[Status: 🎤 Listening... (speak now, pause when done)]

User: *speaks* "Give me an example"

[Status: ✅ Transcribed: Give me an example]

[LLM responds with example...]

[Status: 🔊 Speaking...]

[TTS speaks the example]

[Status: 🎤 Listening... (speak now, pause when done)]

User: *clicks "🛑 Stop Listening"*

[Listening mode ends, status hidden]

User: *types manually or clicks Start again*
```

---

## Technical Implementation

### State Management:

```python
self.listening_mode_active = False  # Tracks if continuous mode is on
```

### Continuous Loop Function:

```python
def continuous_listen_respond_loop(chatbot_history):
    """
    Continuous loop: listen -> transcribe -> respond -> listen again.
    Runs while listening_mode_active is True.
    """
    while self.listening_mode_active:
        # 1. Listen for voice
        text = self.stt.listen()

        # 2. Get LLM response
        response = self.runtime.chat(messages)

        # 3. Speak response (if TTS enabled)
        if self.tts and self.tts_enabled_state:
            wait_for_tts_clearance(self.tts, self.stt, response)

        # 4. Loop continues automatically
```

### Event Chain:

```python
start_listening_btn.click(
    start_listening_mode,  # Activate mode, show/hide buttons
    outputs=[start_btn, stop_btn, status]
).then(
    continuous_listen_respond_loop,  # Start the loop
    inputs=[chatbot],
    outputs=[status, msg, chatbot]
)

stop_listening_btn.click(
    stop_listening_mode,  # Deactivate mode (breaks loop)
    outputs=[start_btn, stop_btn, status]
)
```

---

## Audio Feedback Prevention

When both TTS and STT are enabled, the system uses `wait_for_tts_clearance()` to prevent audio feedback loops:

1. **TTS speaks** the response
2. **Wait for audio clearance** (ensures microphone doesn't pick up TTS output)
3. **STT listens** for next input
4. **No feedback loop** ✅

This is the same mechanism used in the terminal version.

---

## Configuration

### Enable Modules:
```bash
llf module enable text2speech   # For voice output
llf module enable speech2text   # For voice input
```

### Module Settings:

**Speech-to-Text** (`modules/speech2text/module_info.json`):
```json
{
  "settings": {
    "silence_timeout": 1.5,     // Pause duration to end recording
    "max_duration": 60,          // Max recording length
    "whisper_model": "base"      // tiny, base, small, medium, large
  }
}
```

**Text-to-Speech** (`modules/text2speech/module_info.json`):
```json
{
  "settings": {
    "rate": 200,                 // Speech rate (words per minute)
    "volume": 1.0                // Volume (0.0 to 1.0)
  }
}
```

---

## Usage Scenarios

### Scenario 1: Hands-Free Conversation
```bash
llf module enable text2speech
llf module enable speech2text
llf gui
```

**In GUI:**
1. Click "🎤 Start Listening"
2. Have full conversation without touching keyboard/mouse
3. Click "🛑 Stop Listening" when done

---

### Scenario 2: Voice Input, Text Output
```bash
llf module disable text2speech
llf module enable speech2text
llf gui
```

**In GUI:**
1. Click "🎤 Start Listening"
2. Speak questions
3. Read responses (no speech)
4. Listens again automatically

---

### Scenario 3: Mixed Mode
```bash
llf module enable text2speech
llf module enable speech2text
llf gui
```

**In GUI:**
1. Start with text input (type messages)
2. Click "🎤 Start Listening" for voice mode
3. Uncheck "🔊 Voice Output" if responses too long
4. Click "🛑 Stop Listening" to type again
5. Switch between modes as needed

---

## Troubleshooting

### Listening Mode Won't Start

**Check Module Status:**
```bash
llf module list
# Ensure speech2text shows "enabled: true"
```

**Check Microphone Permission:**
- macOS: System Settings → Privacy & Security → Microphone
- Ensure browser/terminal has permission

---

### Loop Stops After Error

**Expected Behavior:**
- On error, shows error message for 2 seconds
- If still in listening mode, shows "🎤 Ready to listen again..."
- Continues listening

**If Loop Exits:**
- Check logs for error details
- Click "🎤 Start Listening" again

---

### TTS Not Speaking in Loop

**Check:**
1. "🔊 Voice Output" checkbox is checked
2. System volume is up
3. text2speech module is enabled

**Debug:**
```bash
# Check module status
llf module list

# Test TTS separately
llf chat  # Should hear responses
```

---

### Can't Stop Listening

**Click "🛑 Stop Listening" button**

If button doesn't work:
1. Refresh page (Gradio GUI)
2. Restart GUI: `Ctrl+C` and run `llf gui` again

---

## Benefits

✅ **Hands-Free**: No need to click after each response
✅ **Terminal Parity**: Works exactly like `llf chat`
✅ **Flexible**: Toggle between voice and text modes
✅ **Clear Feedback**: Status messages at every step
✅ **Error Resilient**: Graceful error handling, continues listening
✅ **No Feedback Loops**: Proper audio clearance built-in

---

## Summary

The GUI continuous listening mode provides:

- **One-click activation**: Click "🎤 Start Listening" to start
- **Auto-loop**: Automatically listens after each LLM response
- **One-click deactivation**: Click "🛑 Stop Listening" to stop
- **Clear status**: Terminal-style status messages
- **Full control**: Toggle TTS on/off independently

**Experience seamless, hands-free conversations with your LLM!** 🎤🔊

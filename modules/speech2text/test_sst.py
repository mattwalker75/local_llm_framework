#!/usr/bin/env python
"""
Standalone test script for the Text-to-Speech module.

Usage:
    python test_tts.py "Your text here"
    python test_tts.py --text "Your text here"
    python test_tts.py --list-voices
    python test_tts.py --text "Hello" --voice "voice_id" --rate 150 --volume 0.8
"""

import sys
import argparse
from pathlib import Path

# Add the modules directory to the path so we can import text2speech
sys.path.insert(0, str(Path(__file__).parent.parent))

from speech2text import SpeechToText

my_mic = SpeechToText()

print("We are starting to listen...  Start talking....")

output_text = my_mic.listen()

print("This is your text output:")
print(output_text)


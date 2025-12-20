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

from text2speech import TextToSpeech


def list_voices():
    """List all available voices on the system."""
    print("Available voices on your system:\n")
    print("-" * 80)

    tts = TextToSpeech()
    voices = tts.get_available_voices()

    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice['name']}")
        print(f"   ID: {voice['id']}")
        if voice['languages']:
            print(f"   Languages: {', '.join(voice['languages'])}")
        print()

    print(f"Total voices found: {len(voices)}")
    print("-" * 80)


def speak_text(text: str, voice_id: str = None, rate: int = 200, volume: float = 1.0):
    """
    Convert text to speech and play it.

    Args:
        text: The text to speak.
        voice_id: Optional voice ID to use.
        rate: Speech rate in words per minute.
        volume: Volume level from 0.0 to 1.0.
    """
    print(f"Initializing Text-to-Speech engine...")
    print(f"  Rate: {rate} words/minute")
    print(f"  Volume: {volume}")
    if voice_id:
        print(f"  Voice ID: {voice_id}")
    print()

    try:
        # Initialize TTS engine
        tts = TextToSpeech(voice_id=voice_id, rate=rate, volume=volume)

        print(f"Speaking: \"{text}\"\n")

        # Speak the text
        tts.speak(text)

        print("✓ Speech completed successfully!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test the Text-to-Speech module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Hello, world!"
  %(prog)s --text "Welcome to the LLM Framework"
  %(prog)s --list-voices
  %(prog)s --text "Testing different voice" --rate 150 --volume 0.8
        """
    )

    parser.add_argument(
        'text',
        nargs='?',
        help='Text to convert to speech (can be passed as positional argument)'
    )

    parser.add_argument(
        '--text', '-t',
        dest='text_flag',
        help='Text to convert to speech (alternative to positional argument)'
    )

    parser.add_argument(
        '--list-voices',
        action='store_true',
        help='List all available voices and exit'
    )

    parser.add_argument(
        '--voice', '-v',
        help='Voice ID to use (use --list-voices to see available voices)'
    )

    parser.add_argument(
        '--rate', '-r',
        type=int,
        default=200,
        help='Speech rate in words per minute (default: 200)'
    )

    parser.add_argument(
        '--volume',
        type=float,
        default=1.0,
        help='Volume level from 0.0 to 1.0 (default: 1.0)'
    )

    args = parser.parse_args()

    # Handle --list-voices
    if args.list_voices:
        list_voices()
        return

    # Get text from either positional argument or --text flag
    text = args.text or args.text_flag

    if not text:
        parser.error("Please provide text to speak (either as argument or with --text flag)")

    # Validate volume
    if not 0.0 <= args.volume <= 1.0:
        parser.error("Volume must be between 0.0 and 1.0")

    # Speak the text
    speak_text(text, voice_id=args.voice, rate=args.rate, volume=args.volume)


if __name__ == "__main__":
    main()

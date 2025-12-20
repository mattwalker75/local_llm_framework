#!/usr/bin/env python
"""
Utility script to list all available TTS voices on the system.

This is a simple standalone script that displays all available voices
with their IDs, names, and supported languages.

Usage:
    python list_voices.py
    python list_voices.py --format json
    python list_voices.py --format table
"""

import sys
import json
import argparse
from pathlib import Path

# Add the modules directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from text2speech import TextToSpeech


def list_voices_table():
    """List all available voices in table format."""
    print("\n" + "=" * 80)
    print("Available Text-to-Speech Voices")
    print("=" * 80 + "\n")

    tts = TextToSpeech()
    voices = tts.get_available_voices()

    if not voices:
        print("No voices found on this system.")
        return

    for i, voice in enumerate(voices, 1):
        print(f"{i}. {voice['name']}")
        print(f"   ID: {voice['id']}")
        if voice['languages']:
            langs = ', '.join(voice['languages']) if isinstance(voice['languages'], list) else voice['languages']
            print(f"   Languages: {langs}")
        print()

    print("=" * 80)
    print(f"Total: {len(voices)} voice(s) available")
    print("=" * 80)
    print("\nTo use a voice, copy its ID and pass it to the TTS module:")
    print('  python test_tts.py --text "Hello" --voice "VOICE_ID_HERE"')
    print()


def list_voices_json():
    """List all available voices in JSON format."""
    tts = TextToSpeech()
    voices = tts.get_available_voices()

    output = {
        "total_voices": len(voices),
        "voices": voices
    }

    print(json.dumps(output, indent=2))


def list_voices_simple():
    """List all available voices in simple format (one per line)."""
    tts = TextToSpeech()
    voices = tts.get_available_voices()

    for voice in voices:
        print(f"{voice['name']} | {voice['id']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all available text-to-speech voices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Table format (default)
  %(prog)s --format json      # JSON format
  %(prog)s --format simple    # Simple list format
        """
    )

    parser.add_argument(
        '--format', '-f',
        choices=['table', 'json', 'simple'],
        default='table',
        help='Output format (default: table)'
    )

    args = parser.parse_args()

    try:
        if args.format == 'json':
            list_voices_json()
        elif args.format == 'simple':
            list_voices_simple()
        else:
            list_voices_table()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

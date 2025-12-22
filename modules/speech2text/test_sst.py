#!/usr/bin/env python
"""
Standalone test script for the Speech-to-Text module.

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


def print_args(cl_args):
    """Print out command line parms and settings""" 
    print("Parms:")
    print("Chunk Duration: ", cl_args.c_duration)
    print("Sample Rate: ", cl_args.sample)
    print("Maximum recording duration: ", cl_args.max_time)
    print("Data Type: ", cl_args.data_type)
    print("Duration of Silence: ", cl_args.s_timeout)
    print("Amplitude threshold: ", cl_args.s_threshold)


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Test the Speech-to-Text module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 
  %(prog)s --max_time 30 --s_timeout 1.0
        """
    )

    parser.add_argument(
        '--sample',
        type=int,
        default=16000,
        help='Sample rate for audio recording (default: 16000)'
    )

    parser.add_argument(
        '--data_type',
        dest='data_type',
        default="int16",
        help='Data type for audio recording (default: "int16")'
    )

    parser.add_argument(
        '--max_time',
        type=int,
        default=60,
        help='Maximum duration to record in seconds (default: 60)'
    )

    parser.add_argument(
        '--s_timeout',
        type=float,
        default=1.5,
        help='Duration of silence to stop recording (default: 1.5 seconds)'
    )

    parser.add_argument(
        '--s_threshold',
        type=int,
        default=500,
        help='Amplitude threshold to detect silence (default: 500)'
    )

    parser.add_argument(
        '--c_duration',
        type=float,
        default=0.1,
        help='Duration of each audio chunk to process (default: 0.1 seconds)'
    )

    args = parser.parse_args()

    print_args(args)

    local_mic = SpeechToText(
            sample_rate = args.sample, 
            dtype = args.data_type,
            max_duration = args.max_time,
            silence_timeout = args.s_timeout,
            silence_threshold = args.s_threshold,
            chunk_duration = args.c_duration )

    print("\nWe are starting to listen...  Start talking....\n")

    output_text = local_mic.listen()

    print("This is your text output:")
    print(output_text,"\n")


if __name__ == "__main__":
    main()


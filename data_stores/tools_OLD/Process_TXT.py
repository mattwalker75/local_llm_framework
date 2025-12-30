#!/usr/bin/env python3
"""
Process_TXT.py - Convert plain text files to clean, structured text for RAG ingestion.

This script processes plain text files (.txt, .log, .md, etc.) and converts them to
clean, structured formats suitable for loading into RAG (Retrieval-Augmented Generation)
data stores.

Features:
- Multiple output formats: text, JSON, JSONL (line-delimited JSON)
- Smart paragraph detection and chunking
- Metadata extraction (filename, line count, character count)
- Text normalization (Unicode, whitespace, encoding handling)
- Preserves document structure (paragraphs, sections)
- Multiple encoding support (UTF-8, Latin-1, Windows-1252, etc.)
- Markdown heading detection
- Error handling with helpful messages

Usage:
    # Basic text normalization
    ./Process_TXT.py -i document.txt -o output.txt

    # JSONL format (recommended for RAG)
    ./Process_TXT.py -i document.txt -o output.jsonl -f jsonl

    # JSON format with metadata
    ./Process_TXT.py -i document.txt -o output.json -f json

    # Process markdown files with heading detection
    ./Process_TXT.py -i README.md -o output.jsonl -f jsonl --detect-headings

    # Verbose output for debugging
    ./Process_TXT.py -i document.txt -o output.txt --verbose

Author: Local LLM Framework
License: MIT
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def detect_encoding(file_path: str) -> str:
    """
    Detect the encoding of a text file.

    Tries multiple common encodings and returns the first one that works.

    Args:
        file_path: Path to the text file

    Returns:
        str: Detected encoding name (e.g., 'utf-8', 'latin-1')
    """
    encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'ascii']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue

    # Default fallback
    return 'utf-8'


def normalize_text(text: str) -> str:
    """
    Normalize text by cleaning whitespace and Unicode characters.

    Args:
        text: Raw text string

    Returns:
        str: Normalized text
    """
    # Unicode NFC normalization (compose characters)
    text = unicodedata.normalize('NFC', text)

    # Remove control characters except newline and tab
    text = ''.join(char for char in text if char == '\n' or char == '\t' or not unicodedata.category(char).startswith('C'))

    # Replace various types of spaces with regular space
    text = text.replace('\u00A0', ' ')  # Non-breaking space
    text = text.replace('\u200B', '')   # Zero-width space
    text = text.replace('\u2003', ' ')  # Em space
    text = text.replace('\u2002', ' ')  # En space

    # Replace tabs with spaces
    text = text.replace('\t', '    ')

    # Normalize line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces (but preserve indentation)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        # Preserve leading spaces, collapse internal multiple spaces
        stripped = line.lstrip()
        leading_spaces = len(line) - len(stripped)
        collapsed = ' '.join(stripped.split())
        normalized_lines.append(' ' * leading_spaces + collapsed)

    text = '\n'.join(normalized_lines)

    return text.strip()


def detect_heading(line: str) -> Tuple[bool, int]:
    """
    Detect if a line is a markdown heading.

    Args:
        line: Text line to check

    Returns:
        Tuple[bool, int]: (is_heading, heading_level)
            - is_heading: True if line is a heading
            - heading_level: 1-6 for markdown headings, 0 otherwise
    """
    line = line.strip()

    # Markdown ATX-style headings (# Heading)
    match = re.match(r'^(#{1,6})\s+(.+)$', line)
    if match:
        level = len(match.group(1))
        return True, level

    # Markdown Setext-style headings (underlined with = or -)
    # This would need to check the next line, so we skip it for now
    # Could be enhanced in future versions

    return False, 0


def split_into_paragraphs(text: str, detect_headings: bool = False) -> List[Dict[str, any]]:
    """
    Split text into paragraphs with metadata.

    Args:
        text: Normalized text content
        detect_headings: Whether to detect markdown headings

    Returns:
        List of dictionaries with paragraph data:
            - para_number: Sequential paragraph number (1-indexed)
            - text: Paragraph text content
            - char_count: Character count
            - line_count: Number of lines in paragraph
            - is_heading: True if paragraph is a heading (only if detect_headings=True)
            - heading_level: Heading level 1-6 (only if is_heading=True)
    """
    paragraphs = []
    current_para = []
    para_number = 0

    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()

        # Empty line marks paragraph boundary
        if not stripped:
            if current_para:
                para_number += 1
                para_text = '\n'.join(current_para)

                para_data = {
                    'para_number': para_number,
                    'text': para_text,
                    'char_count': len(para_text),
                    'line_count': len(current_para)
                }

                # Check if it's a heading
                if detect_headings and len(current_para) == 1:
                    is_heading, heading_level = detect_heading(current_para[0])
                    if is_heading:
                        para_data['is_heading'] = True
                        para_data['heading_level'] = heading_level
                        # Clean the heading text (remove # markers)
                        para_data['text'] = re.sub(r'^#+\s+', '', para_text)
                    else:
                        para_data['is_heading'] = False
                        para_data['heading_level'] = 0
                else:
                    para_data['is_heading'] = False
                    para_data['heading_level'] = 0

                paragraphs.append(para_data)
                current_para = []
        else:
            current_para.append(line)

    # Don't forget the last paragraph
    if current_para:
        para_number += 1
        para_text = '\n'.join(current_para)

        para_data = {
            'para_number': para_number,
            'text': para_text,
            'char_count': len(para_text),
            'line_count': len(current_para)
        }

        if detect_headings and len(current_para) == 1:
            is_heading, heading_level = detect_heading(current_para[0])
            if is_heading:
                para_data['is_heading'] = True
                para_data['heading_level'] = heading_level
                para_data['text'] = re.sub(r'^#+\s+', '', para_text)
            else:
                para_data['is_heading'] = False
                para_data['heading_level'] = 0
        else:
            para_data['is_heading'] = False
            para_data['heading_level'] = 0

        paragraphs.append(para_data)

    return paragraphs


def extract_text_file(file_path: str, detect_headings: bool = False, verbose: bool = False) -> Tuple[str, List[Dict[str, any]], str]:
    """
    Extract and process text from a text file.

    Args:
        file_path: Path to the text file
        detect_headings: Whether to detect markdown-style headings
        verbose: Print detailed progress information

    Returns:
        Tuple[str, List[Dict], str]:
            - Normalized full text content
            - List of paragraph dictionaries
            - Detected encoding
    """
    if verbose:
        print(f"Reading file: {file_path}")

    # Detect encoding
    encoding = detect_encoding(file_path)
    if verbose:
        print(f"Detected encoding: {encoding}")

    # Read file
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            raw_text = f.read()
    except Exception as e:
        raise IOError(f"Failed to read file: {e}")

    if verbose:
        print(f"Read {len(raw_text)} characters")

    # Normalize text
    normalized_text = normalize_text(raw_text)
    if verbose:
        print(f"Normalized to {len(normalized_text)} characters")

    # Split into paragraphs
    paragraphs = split_into_paragraphs(normalized_text, detect_headings=detect_headings)
    if verbose:
        print(f"Extracted {len(paragraphs)} paragraphs")

    return normalized_text, paragraphs, encoding


def write_text_output(output_path: str, text: str, verbose: bool = False) -> None:
    """
    Write normalized text to output file.

    Args:
        output_path: Path to output file
        text: Text content to write
        verbose: Print progress information
    """
    if verbose:
        print(f"\nWriting text output to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        if verbose:
            print(f"Successfully wrote {len(text)} characters")
    except Exception as e:
        raise IOError(f"Failed to write output file: {e}")


def write_json_output(output_path: str, file_path: str, paragraphs: List[Dict[str, any]],
                      encoding: str, verbose: bool = False) -> None:
    """
    Write structured JSON output with metadata.

    Args:
        output_path: Path to output JSON file
        file_path: Original input file path
        paragraphs: List of paragraph dictionaries
        encoding: Detected file encoding
        verbose: Print progress information
    """
    if verbose:
        print(f"\nWriting JSON output to: {output_path}")

    # Calculate total statistics
    total_chars = sum(p['char_count'] for p in paragraphs)
    total_lines = sum(p['line_count'] for p in paragraphs)

    output_data = {
        'metadata': {
            'source_file': Path(file_path).name,
            'source_path': str(Path(file_path).resolve()),
            'encoding': encoding,
            'para_count': len(paragraphs),
            'total_chars': total_chars,
            'total_lines': total_lines
        },
        'paragraphs': paragraphs
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"Successfully wrote {len(paragraphs)} paragraphs")
    except Exception as e:
        raise IOError(f"Failed to write JSON output: {e}")


def write_jsonl_output(output_path: str, file_path: str, paragraphs: List[Dict[str, any]],
                       encoding: str, verbose: bool = False) -> None:
    """
    Write JSONL (JSON Lines) output - one JSON object per line.

    This format is recommended for RAG ingestion as it allows streaming
    and easy parallel processing.

    Args:
        output_path: Path to output JSONL file
        file_path: Original input file path
        paragraphs: List of paragraph dictionaries
        encoding: Detected file encoding
        verbose: Print progress information
    """
    if verbose:
        print(f"\nWriting JSONL output to: {output_path}")

    source_filename = Path(file_path).name

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for para in paragraphs:
                # Add metadata to each record
                record = {
                    'source_file': source_filename,
                    'encoding': encoding,
                    **para  # Include all paragraph fields
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        if verbose:
            print(f"Successfully wrote {len(paragraphs)} records")
    except Exception as e:
        raise IOError(f"Failed to write JSONL output: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert text files to clean, structured text for RAG ingestion.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text normalization
  %(prog)s -i document.txt -o output.txt

  # JSONL format (recommended for RAG)
  %(prog)s -i document.txt -o output.jsonl -f jsonl

  # JSON format with metadata
  %(prog)s -i document.txt -o output.json -f json

  # Process markdown with heading detection
  %(prog)s -i README.md -o output.jsonl -f jsonl --detect-headings

Output Formats:
  text  - Normalized plain text
  json  - Structured JSON with metadata and paragraphs
  jsonl - JSON Lines (one record per paragraph, recommended for RAG)
"""
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Text file to read as input (.txt, .md, .log, etc.)'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output file path'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json', 'jsonl'],
        default='text',
        help='Output format: text, json, or jsonl (default: text)'
    )

    parser.add_argument(
        '--detect-headings',
        action='store_true',
        help='Detect and mark markdown-style headings in output'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: Input path is not a file: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract text from file
        full_text, paragraphs, encoding = extract_text_file(
            str(input_path),
            detect_headings=args.detect_headings,
            verbose=args.verbose
        )

        if not full_text.strip():
            print("Warning: No text content extracted from file", file=sys.stderr)

        # Write output based on format
        if args.format == 'text':
            write_text_output(args.output, full_text, verbose=args.verbose)
        elif args.format == 'json':
            write_json_output(args.output, str(input_path), paragraphs, encoding, verbose=args.verbose)
        elif args.format == 'jsonl':
            write_jsonl_output(args.output, str(input_path), paragraphs, encoding, verbose=args.verbose)

        if args.verbose:
            print("\n✅ Processing complete!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

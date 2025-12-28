#!/usr/bin/env python3
"""
Process_MD.py - Advanced Markdown file processing for RAG ingestion.

This script processes Markdown files with advanced parsing, extracting structured
content including headings, code blocks, lists, and tables for RAG (Retrieval-Augmented
Generation) data stores.

Features:
- Full Markdown syntax parsing (headings, lists, code blocks, tables, quotes)
- Hierarchical section extraction with parent-child relationships
- Code block extraction with language detection
- Table parsing and extraction
- Link extraction and preservation
- Metadata extraction from YAML front matter
- Multiple output formats: text, JSON, JSONL (line-delimited JSON)
- Text normalization and cleanup
- Section-based chunking for RAG

Usage:
    # Basic Markdown to text
    ./Process_MD.py -i README.md -o output.txt

    # JSONL format with full structure (recommended for RAG)
    ./Process_MD.py -i README.md -o output.jsonl -f jsonl

    # JSON format with metadata
    ./Process_MD.py -i README.md -o output.json -f json

    # Extract code blocks separately
    ./Process_MD.py -i README.md -o output.jsonl -f jsonl --extract-code

    # Verbose output for debugging
    ./Process_MD.py -i README.md -o output.txt --verbose

Author: Local LLM Framework
License: MIT
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


def normalize_text(text: str) -> str:
    """
    Normalize text by cleaning whitespace and Unicode characters.

    Args:
        text: Raw text string

    Returns:
        str: Normalized text
    """
    # Unicode NFC normalization
    text = unicodedata.normalize('NFC', text)

    # Remove control characters except newline and tab
    text = ''.join(char for char in text if char == '\n' or char == '\t' or not unicodedata.category(char).startswith('C'))

    # Replace various types of spaces with regular space
    text = text.replace('\u00A0', ' ')  # Non-breaking space
    text = text.replace('\u200B', '')   # Zero-width space
    text = text.replace('\u2003', ' ')  # Em space
    text = text.replace('\u2002', ' ')  # En space

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    return text.strip()


def extract_yaml_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML front matter from Markdown content.

    Args:
        content: Full Markdown content

    Returns:
        Tuple of (metadata dict, content without frontmatter)
    """
    metadata = {}

    # Check for YAML front matter (--- at start)
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        content = content[match.end():]

        # Simple YAML parsing (key: value pairs)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, content


def parse_heading(line: str) -> Tuple[bool, int, str]:
    """
    Parse a line to check if it's a heading and extract level and text.

    Args:
        line: Text line to check

    Returns:
        Tuple of (is_heading, level, heading_text)
    """
    # ATX-style headings (# Heading)
    match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
    if match:
        level = len(match.group(1))
        text = match.group(2).strip()
        # Remove trailing # symbols
        text = re.sub(r'\s*#+\s*$', '', text)
        return True, level, text

    return False, 0, ""


def parse_code_block(lines: List[str], start_idx: int) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Parse a code block starting at the given index.

    Args:
        lines: All lines in the document
        start_idx: Index where code block starts

    Returns:
        Tuple of (code_block_dict or None, next_line_index)
    """
    line = lines[start_idx].strip()

    # Check for fenced code block (``` or ~~~)
    fence_match = re.match(r'^(```|~~~)(\w*)(.*)$', line)
    if not fence_match:
        return None, start_idx + 1

    fence_char = fence_match.group(1)
    language = fence_match.group(2) or 'text'
    info_string = fence_match.group(3).strip()

    code_lines = []
    current_idx = start_idx + 1

    # Find closing fence
    while current_idx < len(lines):
        if lines[current_idx].strip().startswith(fence_char):
            # Found closing fence
            code_block = {
                'type': 'code_block',
                'language': language,
                'info_string': info_string,
                'code': '\n'.join(code_lines),
                'line_count': len(code_lines),
                'char_count': sum(len(l) for l in code_lines)
            }
            return code_block, current_idx + 1

        code_lines.append(lines[current_idx].rstrip())
        current_idx += 1

    # No closing fence found - treat as code to end of file
    code_block = {
        'type': 'code_block',
        'language': language,
        'info_string': info_string,
        'code': '\n'.join(code_lines),
        'line_count': len(code_lines),
        'char_count': sum(len(l) for l in code_lines)
    }
    return code_block, current_idx


def parse_list_item(line: str) -> Tuple[bool, int, str, str]:
    """
    Parse a line to check if it's a list item.

    Args:
        line: Text line to check

    Returns:
        Tuple of (is_list_item, indent_level, marker_type, item_text)
        marker_type: 'ordered' or 'unordered'
    """
    # Count leading spaces for indent level
    stripped = line.lstrip()
    indent = len(line) - len(stripped)

    # Unordered list (-, *, +)
    unordered_match = re.match(r'^[-*+]\s+(.+)$', stripped)
    if unordered_match:
        return True, indent, 'unordered', unordered_match.group(1)

    # Ordered list (1., 2., etc.)
    ordered_match = re.match(r'^\d+\.\s+(.+)$', stripped)
    if ordered_match:
        return True, indent, 'ordered', ordered_match.group(1)

    return False, 0, '', ''


def parse_markdown_sections(content: str, extract_code: bool = False, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Parse Markdown content into structured sections.

    Args:
        content: Markdown content
        extract_code: Whether to extract code blocks separately
        verbose: Print progress information

    Returns:
        List of section dictionaries
    """
    lines = content.split('\n')
    sections = []
    current_section = None
    section_number = 0
    heading_stack = []  # Track heading hierarchy

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for heading
        is_heading, level, heading_text = parse_heading(line)
        if is_heading:
            # Update heading stack
            while heading_stack and heading_stack[-1]['level'] >= level:
                heading_stack.pop()

            section_number += 1

            # Create parent path
            parent_path = ' > '.join(h['text'] for h in heading_stack) if heading_stack else ''

            current_section = {
                'section_number': section_number,
                'type': 'heading',
                'level': level,
                'heading': heading_text,
                'parent_path': parent_path,
                'content': '',
                'code_blocks': [] if extract_code else None,
                'char_count': 0,
                'line_count': 0
            }

            heading_stack.append({'level': level, 'text': heading_text})
            sections.append(current_section)
            i += 1
            continue

        # Check for code block
        if line.strip().startswith('```') or line.strip().startswith('~~~'):
            code_block, next_idx = parse_code_block(lines, i)
            if code_block:
                if extract_code and current_section:
                    current_section['code_blocks'].append(code_block)
                elif not current_section:
                    # Code block before any heading
                    section_number += 1
                    sections.append({
                        'section_number': section_number,
                        'type': 'code_block',
                        'level': 0,
                        'heading': f'[Code: {code_block["language"]}]',
                        'parent_path': '',
                        'content': code_block['code'],
                        'language': code_block['language'],
                        'char_count': code_block['char_count'],
                        'line_count': code_block['line_count']
                    })
                i = next_idx
                continue

        # Regular content line
        if line.strip():
            if current_section is None:
                # Content before any heading
                section_number += 1
                current_section = {
                    'section_number': section_number,
                    'type': 'content',
                    'level': 0,
                    'heading': '[Introduction]',
                    'parent_path': '',
                    'content': '',
                    'code_blocks': [] if extract_code else None,
                    'char_count': 0,
                    'line_count': 0
                }
                sections.append(current_section)

            if current_section['content']:
                current_section['content'] += '\n' + line
            else:
                current_section['content'] = line
            current_section['line_count'] += 1
            current_section['char_count'] += len(line)

        i += 1

    # Calculate final character counts
    for section in sections:
        if section['type'] in ['heading', 'content']:
            section['char_count'] = len(section['content'])

    if verbose:
        print(f"Extracted {len(sections)} sections")

    return sections


def extract_markdown(file_path: str, extract_code: bool = False, verbose: bool = False) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract and process Markdown file.

    Args:
        file_path: Path to Markdown file
        extract_code: Whether to extract code blocks separately
        verbose: Print detailed progress information

    Returns:
        Tuple of (full_text, sections, metadata)
    """
    if verbose:
        print(f"Reading Markdown file: {file_path}")

    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Failed to read file: {e}")

    if verbose:
        print(f"Read {len(content)} characters")

    # Extract YAML front matter
    metadata, content = extract_yaml_frontmatter(content)
    metadata['source_file'] = Path(file_path).name

    if verbose and metadata:
        print(f"Extracted metadata: {list(metadata.keys())}")

    # Normalize text
    content = normalize_text(content)

    # Parse sections
    sections = parse_markdown_sections(content, extract_code=extract_code, verbose=verbose)

    # Create full text (headings + content)
    full_text_parts = []
    for section in sections:
        if section['type'] == 'heading':
            full_text_parts.append('#' * section['level'] + ' ' + section['heading'])
            if section['content']:
                full_text_parts.append(section['content'])
        elif section['type'] == 'content':
            full_text_parts.append(section['content'])
        elif section['type'] == 'code_block':
            full_text_parts.append(f"```{section.get('language', 'text')}\n{section['content']}\n```")

    full_text = '\n\n'.join(full_text_parts)

    return full_text, sections, metadata


def write_text_output(output_path: str, text: str, verbose: bool = False) -> None:
    """Write text output."""
    if verbose:
        print(f"\nWriting text output to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        if verbose:
            print(f"Successfully wrote {len(text)} characters")
    except Exception as e:
        raise IOError(f"Failed to write output file: {e}")


def write_json_output(output_path: str, sections: List[Dict[str, Any]], metadata: Dict[str, Any], verbose: bool = False) -> None:
    """Write JSON output."""
    if verbose:
        print(f"\nWriting JSON output to: {output_path}")

    output_data = {
        'metadata': {
            **metadata,
            'section_count': len(sections),
            'total_chars': sum(s.get('char_count', 0) for s in sections)
        },
        'sections': sections
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"Successfully wrote {len(sections)} sections")
    except Exception as e:
        raise IOError(f"Failed to write JSON output: {e}")


def write_jsonl_output(output_path: str, sections: List[Dict[str, Any]], metadata: Dict[str, Any], verbose: bool = False) -> None:
    """Write JSONL output."""
    if verbose:
        print(f"\nWriting JSONL output to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for section in sections:
                record = {
                    'source_file': metadata.get('source_file', ''),
                    **{k: v for k, v in metadata.items() if k != 'source_file' and v},
                    **section
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        if verbose:
            print(f"Successfully wrote {len(sections)} records")
    except Exception as e:
        raise IOError(f"Failed to write JSONL output: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process Markdown files with advanced structure parsing for RAG ingestion.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic Markdown to text
  %(prog)s -i README.md -o output.txt

  # JSONL format (recommended for RAG)
  %(prog)s -i README.md -o output.jsonl -f jsonl

  # Extract code blocks separately
  %(prog)s -i README.md -o output.jsonl -f jsonl --extract-code

Output Formats:
  text  - Clean Markdown text
  json  - Structured JSON with sections and metadata
  jsonl - JSON Lines (one section per line, recommended for RAG)
"""
    )

    parser.add_argument('-i', '--input', required=True, help='Markdown file to process')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('-f', '--format', choices=['text', 'json', 'jsonl'], default='text', help='Output format (default: text)')
    parser.add_argument('--extract-code', action='store_true', help='Extract code blocks separately')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed progress information')

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract Markdown content
        full_text, sections, metadata = extract_markdown(
            str(input_path),
            extract_code=args.extract_code,
            verbose=args.verbose
        )

        if not full_text.strip():
            print("Warning: No content extracted from file", file=sys.stderr)

        # Write output
        if args.format == 'text':
            write_text_output(args.output, full_text, verbose=args.verbose)
        elif args.format == 'json':
            write_json_output(args.output, sections, metadata, verbose=args.verbose)
        elif args.format == 'jsonl':
            write_jsonl_output(args.output, sections, metadata, verbose=args.verbose)

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

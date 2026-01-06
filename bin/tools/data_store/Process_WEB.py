#!/usr/bin/env python3
"""
Process_WEB.py - Extract clean text from web pages for RAG ingestion.

This script fetches web pages and extracts clean, structured text suitable for
loading into RAG (Retrieval-Augmented Generation) data stores.

Features:
- Multiple output formats: text, JSON, JSONL (line-delimited JSON)
- HTML parsing and text extraction using BeautifulSoup
- Automatic title and metadata extraction
- Paragraph-level chunking
- Heading detection (h1-h6)
- Text normalization (Unicode, whitespace, encoding handling)
- Link preservation (optional)
- User-agent support to avoid blocking
- Error handling with helpful messages

Usage:
    # Basic text extraction
    ./Process_WEB.py -i https://example.com -o output.txt

    # JSONL format (recommended for RAG)
    ./Process_WEB.py -i https://example.com -o output.jsonl -f jsonl

    # JSON format with metadata
    ./Process_WEB.py -i https://example.com -o output.json -f json

    # Extract with heading detection
    ./Process_WEB.py -i https://example.com -o output.jsonl -f jsonl --detect-headings

    # Verbose output for debugging
    ./Process_WEB.py -i https://example.com -o output.txt --verbose

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
from urllib.parse import urlparse, urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required libraries not found.", file=sys.stderr)
    print("Please install: pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# Default user agent to avoid being blocked
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; RAGBot/1.0; +http://example.com/bot)"


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

    # Collapse multiple spaces
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        collapsed = ' '.join(line.split())
        if collapsed:  # Skip empty lines
            normalized_lines.append(collapsed)

    text = '\n\n'.join(normalized_lines)

    return text.strip()


def fetch_webpage(url: str, user_agent: str = DEFAULT_USER_AGENT, timeout: int = 30, verbose: bool = False) -> Tuple[str, requests.Response]:
    """
    Fetch a webpage and return its HTML content.

    Args:
        url: URL to fetch
        user_agent: User-Agent header to use
        timeout: Request timeout in seconds
        verbose: Print progress information

    Returns:
        Tuple[str, requests.Response]: HTML content and response object

    Raises:
        requests.RequestException: If request fails
    """
    if verbose:
        print(f"Fetching URL: {url}")

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        if verbose:
            print(f"Status code: {response.status_code}")
            print(f"Content length: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('Content-Type', 'unknown')}")

        return response.text, response

    except requests.exceptions.Timeout:
        raise requests.RequestException(f"Request timed out after {timeout} seconds")
    except requests.exceptions.ConnectionError:
        raise requests.RequestException(f"Connection error - could not reach {url}")
    except requests.exceptions.HTTPError as e:
        raise requests.RequestException(f"HTTP error {response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Request failed: {e}")


def extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """
    Extract metadata from HTML page.

    Args:
        soup: BeautifulSoup parsed HTML
        url: Original URL

    Returns:
        Dict with metadata fields
    """
    metadata = {
        'url': url,
        'domain': urlparse(url).netloc,
        'title': '',
        'description': '',
        'author': '',
    }

    # Extract title
    title_tag = soup.find('title')
    if title_tag:
        metadata['title'] = title_tag.get_text().strip()

    # Extract meta description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and desc_tag.get('content'):
        metadata['description'] = desc_tag.get('content').strip()

    # Extract author
    author_tag = soup.find('meta', attrs={'name': 'author'})
    if author_tag and author_tag.get('content'):
        metadata['author'] = author_tag.get('content').strip()

    # Try og:title if title is empty
    if not metadata['title']:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            metadata['title'] = og_title.get('content').strip()

    # Try og:description if description is empty
    if not metadata['description']:
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            metadata['description'] = og_desc.get('content').strip()

    return metadata


def extract_paragraphs(soup: BeautifulSoup, detect_headings: bool = False, verbose: bool = False) -> List[Dict[str, any]]:
    """
    Extract paragraphs and headings from HTML.

    Args:
        soup: BeautifulSoup parsed HTML
        detect_headings: Whether to detect and mark headings
        verbose: Print progress information

    Returns:
        List of paragraph dictionaries with metadata
    """
    paragraphs = []
    para_number = 0

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()

    # Try to find main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I)) or soup.body or soup

    # Process all text-containing elements
    for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
        text = element.get_text(separator=' ', strip=True)

        if not text or len(text) < 10:  # Skip very short elements
            continue

        para_number += 1

        # Determine if it's a heading
        is_heading = False
        heading_level = 0

        if detect_headings and element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            is_heading = True
            heading_level = int(element.name[1])

        para_data = {
            'para_number': para_number,
            'text': text,
            'char_count': len(text),
            'is_heading': is_heading,
            'heading_level': heading_level,
            'element_type': element.name
        }

        paragraphs.append(para_data)

    if verbose:
        print(f"Extracted {len(paragraphs)} text elements")

    return paragraphs


def extract_webpage(url: str, detect_headings: bool = False, user_agent: str = DEFAULT_USER_AGENT,
                   timeout: int = 30, verbose: bool = False) -> Tuple[str, List[Dict[str, any]], Dict[str, str]]:
    """
    Extract and process text from a webpage.

    Args:
        url: URL to fetch
        detect_headings: Whether to detect heading elements
        user_agent: User-Agent header
        timeout: Request timeout in seconds
        verbose: Print detailed progress information

    Returns:
        Tuple[str, List[Dict], Dict]:
            - Normalized full text content
            - List of paragraph dictionaries
            - Metadata dictionary
    """
    # Fetch webpage
    html_content, response = fetch_webpage(url, user_agent=user_agent, timeout=timeout, verbose=verbose)

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    if verbose:
        print("Parsing HTML content...")

    # Extract metadata
    metadata = extract_metadata(soup, url)

    if verbose:
        print(f"Title: {metadata['title']}")

    # Extract paragraphs
    paragraphs = extract_paragraphs(soup, detect_headings=detect_headings, verbose=verbose)

    # Create normalized full text
    full_text = '\n\n'.join(p['text'] for p in paragraphs)
    full_text = normalize_text(full_text)

    if verbose:
        print(f"Extracted {len(full_text)} characters of text")

    return full_text, paragraphs, metadata


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


def write_json_output(output_path: str, paragraphs: List[Dict[str, any]],
                      metadata: Dict[str, str], verbose: bool = False) -> None:
    """
    Write structured JSON output with metadata.

    Args:
        output_path: Path to output JSON file
        paragraphs: List of paragraph dictionaries
        metadata: Metadata dictionary
        verbose: Print progress information
    """
    if verbose:
        print(f"\nWriting JSON output to: {output_path}")

    # Calculate total statistics
    total_chars = sum(p['char_count'] for p in paragraphs)

    output_data = {
        'metadata': {
            **metadata,
            'para_count': len(paragraphs),
            'total_chars': total_chars
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


def write_jsonl_output(output_path: str, paragraphs: List[Dict[str, any]],
                       metadata: Dict[str, str], verbose: bool = False) -> None:
    """
    Write JSONL (JSON Lines) output - one JSON object per line.

    This format is recommended for RAG ingestion as it allows streaming
    and easy parallel processing.

    Args:
        output_path: Path to output JSONL file
        paragraphs: List of paragraph dictionaries
        metadata: Metadata dictionary
        verbose: Print progress information
    """
    if verbose:
        print(f"\nWriting JSONL output to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for para in paragraphs:
                # Add metadata to each record
                record = {
                    'url': metadata['url'],
                    'domain': metadata['domain'],
                    'title': metadata['title'],
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
        description='Extract clean text from web pages for RAG ingestion.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text extraction
  %(prog)s -i https://example.com -o output.txt

  # JSONL format (recommended for RAG)
  %(prog)s -i https://example.com -o output.jsonl -f jsonl

  # JSON format with metadata
  %(prog)s -i https://example.com -o output.json -f json

  # With heading detection
  %(prog)s -i https://example.com -o output.jsonl -f jsonl --detect-headings

Output Formats:
  text  - Normalized plain text
  json  - Structured JSON with metadata and paragraphs
  jsonl - JSON Lines (one record per paragraph, recommended for RAG)
"""
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='URL to fetch (e.g., https://example.com)'
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
        help='Detect and mark HTML heading elements (h1-h6)'
    )

    parser.add_argument(
        '--user-agent',
        default=DEFAULT_USER_AGENT,
        help=f'User-Agent header (default: {DEFAULT_USER_AGENT})'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds (default: 30)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )

    args = parser.parse_args()

    # Validate URL
    parsed_url = urlparse(args.input)
    if not parsed_url.scheme or not parsed_url.netloc:
        print(f"Error: Invalid URL: {args.input}", file=sys.stderr)
        print("URL must include scheme (http:// or https://)", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract text from webpage
        full_text, paragraphs, metadata = extract_webpage(
            args.input,
            detect_headings=args.detect_headings,
            user_agent=args.user_agent,
            timeout=args.timeout,
            verbose=args.verbose
        )

        if not full_text.strip():
            print("Warning: No text content extracted from webpage", file=sys.stderr)

        # Write output based on format
        if args.format == 'text':
            write_text_output(args.output, full_text, verbose=args.verbose)
        elif args.format == 'json':
            write_json_output(args.output, paragraphs, metadata, verbose=args.verbose)
        elif args.format == 'jsonl':
            write_jsonl_output(args.output, paragraphs, metadata, verbose=args.verbose)

        if args.verbose:
            print("\n✅ Processing complete!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except requests.RequestException as e:
        print(f"\n❌ Network error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

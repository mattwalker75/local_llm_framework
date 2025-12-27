#!/usr/bin/env python3
"""
PDF to Text Converter for RAG Data Store Preparation

This script extracts and cleans text from PDF files, preparing them for ingestion
into a Retrieval-Augmented Generation (RAG) data store. It handles text extraction,
normalization, and optionally preserves document structure for better RAG performance.

Features:
- Robust text extraction with error handling
- Unicode normalization and whitespace cleanup
- Page number removal (optional)
- Metadata extraction for RAG context
- Multiple output formats (text, JSON, JSONL)
- Structured output with page numbers for citation

Usage:
    # Basic text output
    ./Process_PDF.py -i document.pdf -o output.txt

    # JSONL format (recommended for RAG - one record per page)
    ./Process_PDF.py -i document.pdf -o output.jsonl -f jsonl

    # JSON format with metadata
    ./Process_PDF.py -i document.pdf -o output.json -f json

    # Keep page numbers for reference tracking
    ./Process_PDF.py -i document.pdf -o output.txt --keep-page-numbers

    # Verbose output for debugging
    ./Process_PDF.py -i document.pdf -o output.txt --verbose

Dependencies:
    - PyMuPDF (fitz): pip install pymupdf

Author: Local LLM Framework
License: MIT
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
import re
import unicodedata

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# PDF EXTRACTION FUNCTIONS
# ============================================================================

def extract_pdf_text(path: str, verbose: bool = False) -> str:
    """
    Extract text from all pages of a PDF file.

    This function reads a PDF file and extracts text content from each page,
    combining them with double newlines between pages.

    Args:
        path: Path to the PDF file
        verbose: If True, print progress information

    Returns:
        Combined text from all pages

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: If PDF processing fails

    Example:
        >>> text = extract_pdf_text("report.pdf")
        >>> print(f"Extracted {len(text)} characters")
    """
    try:
        # Validate file exists
        if not Path(path).exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if verbose:
            print(f"Opening PDF: {path}", file=sys.stderr)

        doc = fitz.open(path)
        pages = []
        total_pages = len(doc)

        if verbose:
            print(f"Processing {total_pages} pages...", file=sys.stderr)

        # Extract text from each page
        for page_num, page in enumerate(doc, start=1):
            try:
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
                    if verbose and page_num % 10 == 0:
                        print(f"  Processed {page_num}/{total_pages} pages", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to extract page {page_num}: {e}", file=sys.stderr)
                continue

        doc.close()

        if not pages:
            print(f"Warning: No text extracted from {path}", file=sys.stderr)
        elif verbose:
            print(f"✓ Successfully extracted text from {len(pages)} pages", file=sys.stderr)

        return "\n\n".join(pages)

    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"Error processing PDF '{path}': {e}", file=sys.stderr)
        sys.exit(1)


def extract_pdf_with_structure(path: str, verbose: bool = False) -> List[Dict[str, any]]:
    """
    Extract text with page structure preserved for RAG chunking.

    This function extracts text from each page separately, preserving page
    numbers and metadata. This is ideal for RAG systems that need to cite
    sources or chunk by page.

    Args:
        path: Path to the PDF file
        verbose: If True, print progress information

    Returns:
        List of dictionaries, each containing:
            - page_number: Page number (1-indexed)
            - text: Text content from that page
            - char_count: Number of characters on the page

    Example:
        >>> pages = extract_pdf_with_structure("report.pdf")
        >>> for page in pages:
        ...     print(f"Page {page['page_number']}: {page['char_count']} chars")
    """
    try:
        if not Path(path).exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if verbose:
            print(f"Opening PDF: {path}", file=sys.stderr)

        doc = fitz.open(path)
        pages_data = []
        total_pages = len(doc)

        if verbose:
            print(f"Processing {total_pages} pages (structured)...", file=sys.stderr)

        for page_num, page in enumerate(doc, start=1):
            try:
                text = page.get_text("text")
                if text.strip():
                    pages_data.append({
                        "page_number": page_num,
                        "text": text,
                        "char_count": len(text)
                    })
                    if verbose and page_num % 10 == 0:
                        print(f"  Processed {page_num}/{total_pages} pages", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Failed to extract page {page_num}: {e}", file=sys.stderr)
                continue

        doc.close()

        if verbose:
            print(f"✓ Extracted {len(pages_data)} pages with structure", file=sys.stderr)

        return pages_data

    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"Error processing PDF '{path}': {e}", file=sys.stderr)
        sys.exit(1)


def extract_pdf_metadata(path: str) -> Dict[str, str]:
    """
    Extract metadata from PDF file for RAG context.

    Metadata provides important context for RAG systems, such as document
    title, author, and subject. This helps with document identification
    and relevance scoring.

    Args:
        path: Path to the PDF file

    Returns:
        Dictionary containing:
            - title: Document title (empty string if not set)
            - author: Document author (empty string if not set)
            - subject: Document subject (empty string if not set)
            - page_count: Total number of pages
            - source_file: Name of the source PDF file

    Example:
        >>> metadata = extract_pdf_metadata("report.pdf")
        >>> print(f"Title: {metadata['title']}, Pages: {metadata['page_count']}")
    """
    try:
        doc = fitz.open(path)
        metadata = {
            "title": doc.metadata.get("title", "") if doc.metadata else "",
            "author": doc.metadata.get("author", "") if doc.metadata else "",
            "subject": doc.metadata.get("subject", "") if doc.metadata else "",
            "page_count": len(doc),
            "source_file": str(Path(path).name)
        }
        doc.close()
        return metadata
    except Exception as e:
        print(f"Warning: Failed to extract metadata from '{path}': {e}", file=sys.stderr)
        # Return minimal metadata on failure
        return {
            "title": "",
            "author": "",
            "subject": "",
            "page_count": 0,
            "source_file": str(Path(path).name)
        }


# ============================================================================
# TEXT CLEANING FUNCTIONS
# ============================================================================

def remove_page_numbers(text: str) -> str:
    """
    Remove common page number patterns from text.

    This function identifies and removes standalone page numbers that appear
    on their own lines. It handles several common formats:
    - "Page X" or "Page X of Y"
    - "X / Y" (slash notation)
    - Standalone numbers

    Args:
        text: Input text with page numbers

    Returns:
        Text with page numbers removed

    Note:
        This is a heuristic approach and may occasionally remove legitimate
        content that looks like page numbers. Use --keep-page-numbers flag
        to disable this if needed.

    Example:
        >>> text = "Content here\\nPage 5\\nMore content"
        >>> print(remove_page_numbers(text))
        Content here
        More content
    """
    # Define patterns for common page number formats
    patterns = [
        r'^\s*Page\s+\d+(\s+of\s+\d+)?\s*$',  # "Page 5" or "Page 5 of 10"
        r'^\s*\d+\s*/\s*\d+\s*$',              # "5 / 10"
        r'^\s*\d+\s*$'                         # Just "5"
    ]

    lines = text.splitlines()
    cleaned = []

    for line in lines:
        # Skip lines that match page number patterns
        if any(re.match(p, line.strip(), re.IGNORECASE) for p in patterns):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def whitespace_cleanup(text: str) -> str:
    """
    Clean up excessive whitespace while preserving paragraph breaks.

    This function normalizes whitespace by:
    1. Converting single newlines (within paragraphs) to spaces
    2. Preserving double newlines (paragraph breaks)
    3. Removing excessive blank lines (3+ newlines → 2 newlines)

    Args:
        text: Input text with irregular whitespace

    Returns:
        Text with normalized whitespace

    Example:
        >>> text = "Line 1\\nLine 2\\n\\n\\n\\nNew paragraph"
        >>> print(whitespace_cleanup(text))
        Line 1 Line 2

        New paragraph
    """
    # Fix broken lines: convert single newlines to spaces
    # (?<!\n)\n(?!\n) matches a newline that's NOT preceded or followed by another newline
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Collapse excessive newlines (3 or more → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def normalize_text(text: str) -> str:
    """
    Normalize text encoding and formatting for consistent processing.

    This function performs comprehensive text normalization:
    1. Unicode normalization (NFC form) for consistent character representation
    2. Remove control characters (form feeds, carriage returns)
    3. Replace special spaces (non-breaking spaces, tabs) with regular spaces
    4. Fix line breaks (preserve paragraphs, merge broken lines)
    5. Collapse excessive whitespace

    Args:
        text: Input text with various encoding and formatting issues

    Returns:
        Normalized, clean text suitable for RAG ingestion

    Note:
        Uses Unicode NFC (Canonical Decomposition, followed by Canonical
        Composition) which is the recommended form for most applications.

    Example:
        >>> text = "Text\\twith\\u00a0various\\r\\nspaces"
        >>> print(normalize_text(text))
        Text with various spaces
    """
    # Unicode normalization to NFC form (canonical composition)
    text = unicodedata.normalize("NFC", text)

    # Remove control characters
    text = text.replace("\f", "")   # Form feed
    text = text.replace("\r", "")   # Carriage return

    # Replace special spaces with regular spaces
    text = text.replace("\u00a0", " ")  # Non-breaking space
    text = text.replace("\t", " ")      # Tab

    # Fix line breaks: convert single newlines to spaces (merge broken lines)
    # but preserve paragraph breaks (double newlines)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Collapse excessive newlines (3+ → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse excessive spaces (2+ → 1)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def clean_text_pipeline(text: str, keep_page_numbers: bool = False) -> str:
    """
    Apply full text cleaning pipeline.

    This is a convenience function that applies all cleaning steps in the
    correct order. The pipeline is:
    1. Remove page numbers (optional)
    2. Clean up whitespace
    3. Normalize text encoding

    Args:
        text: Raw text extracted from PDF
        keep_page_numbers: If True, skip page number removal

    Returns:
        Fully cleaned and normalized text

    Example:
        >>> raw_text = extract_pdf_text("document.pdf")
        >>> clean_text = clean_text_pipeline(raw_text)
    """
    if not keep_page_numbers:
        text = remove_page_numbers(text)
    text = whitespace_cleanup(text)
    text = normalize_text(text)
    return text


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def write_text_output(output_path: str, text: str, verbose: bool = False) -> None:
    """
    Write cleaned text to a file.

    Args:
        output_path: Path for output text file
        text: Cleaned text content
        verbose: If True, print confirmation message
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        if verbose:
            char_count = len(text)
            word_count = len(text.split())
            print(f"✓ Written {char_count:,} characters ({word_count:,} words) to {output_path}",
                  file=sys.stderr)
    except Exception as e:
        print(f"Error writing output file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def write_json_output(output_path: str, metadata: Dict, pages_data: List[Dict],
                     verbose: bool = False) -> None:
    """
    Write structured JSON output with metadata and pages.

    Output format:
    {
        "metadata": { ... },
        "pages": [
            {"page_number": 1, "text": "...", "char_count": 123},
            ...
        ]
    }

    Args:
        output_path: Path for output JSON file
        metadata: Document metadata dictionary
        pages_data: List of page dictionaries
        verbose: If True, print confirmation message
    """
    try:
        output = {
            "metadata": metadata,
            "pages": pages_data
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        if verbose:
            total_chars = sum(p.get("char_count", len(p.get("text", ""))) for p in pages_data)
            print(f"✓ Written {len(pages_data)} pages ({total_chars:,} chars) to {output_path}",
                  file=sys.stderr)
    except Exception as e:
        print(f"Error writing JSON output '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def write_jsonl_output(output_path: str, metadata: Dict, pages_data: List[Dict],
                      verbose: bool = False) -> None:
    """
    Write JSONL output (one JSON object per line).

    JSONL format is ideal for RAG systems because:
    - Each line is a complete, independent record
    - Easy to stream and process incrementally
    - Each record includes both metadata and page content
    - Standard format for many RAG ingestion pipelines

    Output format (one record per line):
    {"title": "...", "author": "...", "page_number": 1, "text": "...", ...}
    {"title": "...", "author": "...", "page_number": 2, "text": "...", ...}

    Args:
        output_path: Path for output JSONL file
        metadata: Document metadata dictionary
        pages_data: List of page dictionaries
        verbose: If True, print confirmation message
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for page in pages_data:
                # Merge metadata and page data into single record
                record = {**metadata, **page}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        if verbose:
            total_chars = sum(p.get("char_count", len(p.get("text", ""))) for p in pages_data)
            print(f"✓ Written {len(pages_data)} JSONL records ({total_chars:,} chars) to {output_path}",
                  file=sys.stderr)
    except Exception as e:
        print(f"Error writing JSONL output '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Main entry point for PDF to text conversion.

    Parses command-line arguments and orchestrates the conversion process.
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF files to text for RAG data store ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic text output
  %(prog)s -i document.pdf -o output.txt

  # JSONL format (recommended for RAG)
  %(prog)s -i document.pdf -o output.jsonl -f jsonl

  # JSON with metadata
  %(prog)s -i document.pdf -o output.json -f json

  # Keep page numbers
  %(prog)s -i document.pdf -o output.txt --keep-page-numbers

  # Verbose output
  %(prog)s -i document.pdf -o output.txt --verbose

Output Formats:
  text  - Plain text file with all content merged
  json  - Structured JSON with metadata and pages array
  jsonl - JSONL format (one JSON record per page, best for RAG)
        """
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        metavar="FILE",
        help="PDF file to read as input"
    )

    parser.add_argument(
        "-o", "--output",
        required=True,
        metavar="FILE",
        help="Output file path"
    )

    parser.add_argument(
        "-f", "--format",
        choices=["text", "json", "jsonl"],
        default="text",
        help="Output format (default: text, recommended for RAG: jsonl)"
    )

    parser.add_argument(
        "--keep-page-numbers",
        action="store_true",
        help="Keep page numbers in text (default: remove them)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress information"
    )

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Process PDF based on output format
    try:
        if args.format in ["json", "jsonl"]:
            # Structured output - extract with page information
            if args.verbose:
                print(f"\n{'='*60}", file=sys.stderr)
                print(f"Converting PDF to {args.format.upper()} format", file=sys.stderr)
                print(f"{'='*60}\n", file=sys.stderr)

            # Extract metadata
            metadata = extract_pdf_metadata(args.input)

            # Extract text with structure
            pages_data = extract_pdf_with_structure(args.input, args.verbose)

            # Clean each page
            if args.verbose:
                print("\nCleaning extracted text...", file=sys.stderr)

            for page in pages_data:
                page["text"] = clean_text_pipeline(
                    page["text"],
                    keep_page_numbers=args.keep_page_numbers
                )
                page["char_count"] = len(page["text"])

            # Write output
            if args.format == "jsonl":
                write_jsonl_output(args.output, metadata, pages_data, args.verbose)
            else:
                write_json_output(args.output, metadata, pages_data, args.verbose)

        else:
            # Plain text output
            if args.verbose:
                print(f"\n{'='*60}", file=sys.stderr)
                print(f"Converting PDF to plain text", file=sys.stderr)
                print(f"{'='*60}\n", file=sys.stderr)

            # Extract text
            text_data = extract_pdf_text(args.input, args.verbose)

            # Clean text
            if args.verbose:
                print("\nCleaning extracted text...", file=sys.stderr)

            text_final = clean_text_pipeline(
                text_data,
                keep_page_numbers=args.keep_page_numbers
            )

            # Write output
            write_text_output(args.output, text_final, args.verbose)

        if args.verbose:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"✓ Conversion complete!", file=sys.stderr)
            print(f"  Input:  {args.input}", file=sys.stderr)
            print(f"  Output: {args.output}", file=sys.stderr)
            print(f"  Format: {args.format}", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)
        else:
            print(f"✓ Converted {args.input} → {args.output} ({args.format} format)")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

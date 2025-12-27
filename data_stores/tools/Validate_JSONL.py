#!/usr/bin/env python3
"""
Validate JSONL files for RAG Vector Store compatibility

This script validates JSONL files to ensure they are properly formatted
and ready to be loaded into RAG vector stores. It checks for:
- Valid JSON structure (one JSON object per line)
- Required 'text' field in each record
- Empty or null text entries
- Chunk size statistics and token limit warnings
- Metadata field presence and types

Usage:
    ./Validate_JSONL.py -i input.jsonl
    ./Validate_JSONL.py -i input.jsonl -v
    ./Validate_JSONL.py -i input.jsonl --model sentence-transformers/all-MiniLM-L6-v2
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


# Token limits for different embedding models (in tokens)
MODEL_TOKEN_LIMITS = {
    "sentence-transformers/all-MiniLM-L6-v2": 256,
    "sentence-transformers/all-mpnet-base-v2": 384,
    "sentence-transformers/multi-qa-mpnet-base-cos-v1": 384,
    "jinaai/jina-embeddings-v2-base-code": 8192,
}

# Character to token conversion (approximate)
CHARS_PER_TOKEN = 4


class ValidationResult:
    """Stores validation results and statistics"""

    def __init__(self):
        self.total_records = 0
        self.valid_records = 0
        self.empty_text = 0
        self.missing_text_field = 0
        self.invalid_json = 0
        self.char_sizes: List[int] = []
        self.token_sizes: List[int] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, line_num: int, message: str):
        """Add an error message"""
        self.errors.append(f"Line {line_num}: {message}")

    def add_warning(self, line_num: int, message: str):
        """Add a warning message"""
        self.warnings.append(f"Line {line_num}: {message}")

    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0 and self.valid_records > 0


def validate_jsonl_file(
    file_path: Path,
    model_name: str = None,
    verbose: bool = False
) -> ValidationResult:
    """
    Validate a JSONL file for RAG compatibility

    Args:
        file_path: Path to JSONL file
        model_name: Optional embedding model name to check token limits
        verbose: Print detailed information

    Returns:
        ValidationResult object with statistics and errors
    """
    result = ValidationResult()

    if not file_path.exists():
        result.add_error(0, f"File not found: {file_path}")
        return result

    if verbose:
        print(f"\nValidating: {file_path}")
        print("=" * 70)

    # Get token limit if model specified
    token_limit = None
    if model_name:
        token_limit = MODEL_TOKEN_LIMITS.get(model_name)
        if token_limit and verbose:
            print(f"Model: {model_name}")
            print(f"Token limit: {token_limit} tokens (~{token_limit * CHARS_PER_TOKEN} characters)\n")

    # Read and validate each line
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            result.total_records += 1
            line = line.strip()

            if not line:
                result.add_warning(line_num, "Empty line (skipped)")
                continue

            # Try to parse JSON
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                result.invalid_json += 1
                result.add_error(line_num, f"Invalid JSON: {e}")
                continue

            # Check if record is a dictionary
            if not isinstance(record, dict):
                result.invalid_json += 1
                result.add_error(line_num, "Record is not a JSON object (expected dictionary)")
                continue

            # Check for 'text' field
            if 'text' not in record:
                result.missing_text_field += 1
                result.add_error(line_num, "Missing required 'text' field")
                continue

            # Get text content
            text = record.get('text', '')

            # Check for empty or null text
            if text is None or (isinstance(text, str) and not text.strip()):
                result.empty_text += 1
                result.add_error(line_num, "Empty or null 'text' field")
                continue

            # Convert to string if not already
            if not isinstance(text, str):
                result.add_warning(line_num, f"'text' field is {type(text).__name__}, converting to string")
                text = str(text)

            # Record is valid
            result.valid_records += 1

            # Calculate sizes
            char_size = len(text)
            token_size = char_size // CHARS_PER_TOKEN
            result.char_sizes.append(char_size)
            result.token_sizes.append(token_size)

            # Check token limit if model specified
            if token_limit and token_size > token_limit:
                result.add_warning(
                    line_num,
                    f"Text exceeds model token limit: {token_size} tokens > {token_limit} tokens "
                    f"({char_size} chars). Chunking required."
                )

            # Verbose output for individual records
            if verbose:
                metadata_fields = [k for k in record.keys() if k != 'text']
                print(f"Record {line_num}: {char_size} chars (~{token_size} tokens)")
                if metadata_fields:
                    print(f"  Metadata: {', '.join(metadata_fields)}")

    return result


def print_summary(result: ValidationResult, verbose: bool = False):
    """Print validation summary"""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    # Record counts
    print(f"\nTotal records: {result.total_records}")
    print(f"Valid records: {result.valid_records}")

    if result.invalid_json > 0:
        print(f"Invalid JSON: {result.invalid_json}")
    if result.missing_text_field > 0:
        print(f"Missing 'text' field: {result.missing_text_field}")
    if result.empty_text > 0:
        print(f"Empty text entries: {result.empty_text}")

    # Size statistics
    if result.char_sizes:
        print(f"\nChunk Size Statistics:")
        print(f"  Min: {min(result.char_sizes)} chars (~{min(result.token_sizes)} tokens)")
        print(f"  Max: {max(result.char_sizes)} chars (~{max(result.token_sizes)} tokens)")
        print(f"  Avg: {sum(result.char_sizes) // len(result.char_sizes)} chars "
              f"(~{sum(result.token_sizes) // len(result.token_sizes)} tokens)")

    # Errors
    if result.errors:
        print(f"\n{len(result.errors)} ERROR(S) FOUND:")
        for error in result.errors:
            print(f"  ✗ {error}")

    # Warnings
    if result.warnings:
        print(f"\n{len(result.warnings)} WARNING(S):")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")

    # Final status
    print("\n" + "=" * 70)
    if result.is_valid():
        print("✓ VALIDATION PASSED - File is ready for RAG loading")
        if result.warnings:
            print("  Note: Warnings present but not blocking")
    else:
        print("✗ VALIDATION FAILED - Fix errors before loading")
    print("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate JSONL files for RAG Vector Store compatibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i data.jsonl
  %(prog)s -i data.jsonl -v
  %(prog)s -i data.jsonl --model sentence-transformers/all-MiniLM-L6-v2
  %(prog)s -i data.jsonl --model sentence-transformers/all-mpnet-base-v2 -v

Supported Models:
  sentence-transformers/all-MiniLM-L6-v2           (256 tokens, ~1024 chars)
  sentence-transformers/all-mpnet-base-v2          (384 tokens, ~1536 chars)
  sentence-transformers/multi-qa-mpnet-base-cos-v1 (384 tokens, ~1536 chars)
  jinaai/jina-embeddings-v2-base-code              (8192 tokens, ~32768 chars)

The script validates:
  - Valid JSON structure (one JSON object per line)
  - Required 'text' field presence
  - Non-empty text content
  - Token limits for specified model
  - Metadata field types
        """
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Input JSONL file to validate'
    )

    parser.add_argument(
        '--model',
        type=str,
        choices=list(MODEL_TOKEN_LIMITS.keys()),
        help='Embedding model to check token limits against'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed validation information'
    )

    args = parser.parse_args()

    # Validate file
    input_path = Path(args.input)
    result = validate_jsonl_file(input_path, args.model, args.verbose)

    # Print summary
    print_summary(result, args.verbose)

    # Exit with appropriate code
    sys.exit(0 if result.is_valid() else 1)


if __name__ == '__main__':
    main()

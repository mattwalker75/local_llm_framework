#!/usr/bin/env python3
"""
Create_VectorStore.py - Build FAISS vector stores from JSONL files for RAG.

This script processes JSONL files (created by Process_*.py tools) and builds
FAISS vector stores for Retrieval-Augmented Generation (RAG) applications.

Features:
- Single file or directory batch processing
- Manual embedding model selection (age-small-en-v1.5, age-code-v1, etc.)
- Configurable chunk size with overlap
- FAISS index creation and persistence
- Metadata preservation for filtering and citation
- Progress tracking and verbose output
- Automatic GPU detection for faster embedding

Usage:
    # Single JSONL file
    ./Create_VectorStore.py -i document.jsonl -o my_vectorstore --model sentence-transformers/all-MiniLM-L6-v2

    # Directory of JSONL files
    ./Create_VectorStore.py -i data_dir/ -o combined_vectorstore --model sentence-transformers/all-mpnet-base-v2

    # With chunking parameters for code
    ./Create_VectorStore.py -i document.jsonl -o vectorstore --model jinaai/jina-embeddings-v2-base-code \
        --chunk-size 512 --overlap 50

    # Verbose output
    ./Create_VectorStore.py -i data/ -o vectorstore --model sentence-transformers/all-MiniLM-L6-v2 -v

Author: Local LLM Framework
License: MIT
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Import dependencies with helpful error messages
try:
    import faiss
except ImportError:
    print("Error: faiss-cpu is required.", file=sys.stderr)
    print("Install: pip install faiss-cpu", file=sys.stderr)
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers is required.", file=sys.stderr)
    print("Install: pip install sentence-transformers", file=sys.stderr)
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm is required.", file=sys.stderr)
    print("Install: pip install tqdm", file=sys.stderr)
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_jsonl_files(input_path: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Load JSONL records from a single file or directory of files.

    Args:
        input_path: Path to a JSONL file or directory of JSONL files
        verbose: Print detailed progress information

    Returns:
        List of record dictionaries
    """
    records = []
    input_path_obj = Path(input_path)

    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    # Collect all JSONL files
    jsonl_files = []
    if input_path_obj.is_file():
        if input_path_obj.suffix.lower() == '.jsonl':
            jsonl_files.append(input_path_obj)
        else:
            raise ValueError(f"Input file must have .jsonl extension: {input_path}")
    elif input_path_obj.is_dir():
        jsonl_files = list(input_path_obj.glob('*.jsonl'))
        if not jsonl_files:
            raise ValueError(f"No .jsonl files found in directory: {input_path}")
    else:
        raise ValueError(f"Input path is neither a file nor directory: {input_path}")

    if verbose:
        logger.info(f"Found {len(jsonl_files)} JSONL file(s) to process")

    # Load all records
    for jsonl_file in tqdm(jsonl_files, desc="Loading JSONL files", disable=not verbose):
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        # Add source file to metadata
                        record['_source_jsonl'] = str(jsonl_file.name)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON in {jsonl_file.name}:{line_num}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Failed to read file {jsonl_file}: {e}")
            continue

    if verbose:
        logger.info(f"Loaded {len(records)} records total")

    return records


def extract_text_from_record(record: Dict[str, Any]) -> str:
    """
    Extract text content from a JSONL record.

    Tries multiple common field names used by Process_*.py tools.

    Args:
        record: JSONL record dictionary

    Returns:
        Extracted text string
    """
    # Try common text fields in order of preference
    text_fields = ['text', 'content', 'paragraph', 'page_text', 'body']

    for field in text_fields:
        if field in record and record[field]:
            return str(record[field]).strip()

    # If no text field found, try to concatenate heading + content
    if 'heading' in record:
        heading = str(record['heading']).strip()
        content = str(record.get('content', '')).strip()
        if heading and content:
            return f"{heading}\n\n{content}"
        elif heading:
            return heading

    # Last resort: convert entire record to string (excluding metadata)
    exclude_keys = {'_source_jsonl', 'para_number', 'page_number', 'char_count', 'line_count'}
    text_parts = []
    for key, value in record.items():
        if key not in exclude_keys and value:
            text_parts.append(str(value))

    return ' '.join(text_parts).strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    # If text is smaller than chunk_size, return as-is
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Extract chunk
        end = start + chunk_size
        chunk = text[start:end]

        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)

        # Move to next chunk with overlap
        start = end - overlap

        # Prevent infinite loop if overlap equals chunk_size
        if start >= len(text):
            break

    return chunks


def prepare_chunks(records: List[Dict[str, Any]], chunk_size: Optional[int] = None,
                   overlap: int = 0, verbose: bool = False) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Prepare text chunks and corresponding metadata from records.

    Args:
        records: List of JSONL records
        chunk_size: Maximum characters per chunk (None = no chunking)
        overlap: Number of overlapping characters between chunks
        verbose: Print detailed progress information

    Returns:
        Tuple of (text_chunks, metadata_list)
    """
    text_chunks = []
    metadata_list = []

    for record in tqdm(records, desc="Preparing chunks", disable=not verbose):
        # Extract text
        text = extract_text_from_record(record)

        if not text:
            logger.warning(f"Skipping record with no extractable text: {record.get('_source_jsonl', 'unknown')}")
            continue

        # Apply chunking if requested
        if chunk_size:
            chunks = chunk_text(text, chunk_size, overlap)
        else:
            chunks = [text]

        # Create metadata for each chunk
        for chunk_idx, chunk in enumerate(chunks):
            text_chunks.append(chunk)

            # Copy record metadata and add chunk info
            metadata = record.copy()
            metadata['_chunk_index'] = chunk_idx
            metadata['_total_chunks'] = len(chunks)
            metadata['_chunk_char_count'] = len(chunk)

            metadata_list.append(metadata)

    if verbose:
        logger.info(f"Created {len(text_chunks)} text chunks from {len(records)} records")

    return text_chunks, metadata_list


def load_embedding_model(model_name: str, cache_dir: Optional[str] = None, verbose: bool = False) -> SentenceTransformer:
    """
    Load a Sentence Transformer embedding model.

    Args:
        model_name: Model name or path (e.g., 'age-small-en-v1.5')
        cache_dir: Directory to cache downloaded models (default: local app directory)
        verbose: Print detailed progress information

    Returns:
        Loaded SentenceTransformer model
    """
    if verbose:
        logger.info(f"Loading embedding model: {model_name}")

    # Default cache directory: data_stores/embedding_models relative to this script
    if cache_dir is None:
        script_dir = Path(__file__).parent.parent  # Go up to data_stores/
        cache_dir = str(script_dir / 'embedding_models')

    # Create cache directory if it doesn't exist
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    if verbose:
        logger.info(f"Using model cache directory: {cache_dir}")

    try:
        # Determine device (GPU if available, else CPU)
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

        if verbose:
            logger.info(f"Using device: {device}")

        model = SentenceTransformer(model_name, device=device, cache_folder=cache_dir)

        if verbose:
            logger.info(f"Model loaded successfully (embedding dimension: {model.get_sentence_embedding_dimension()})")

        return model

    except Exception as e:
        logger.error(f"Failed to load model '{model_name}': {e}")
        logger.info("Available models: https://www.sbert.net/docs/pretrained_models.html")
        raise


def create_embeddings(model: SentenceTransformer, text_chunks: List[str],
                     batch_size: int = 32, verbose: bool = False) -> np.ndarray:
    """
    Create embeddings for text chunks using the model.

    Args:
        model: Loaded SentenceTransformer model
        text_chunks: List of text strings to embed
        batch_size: Number of texts to process at once
        verbose: Print detailed progress information

    Returns:
        NumPy array of embeddings (shape: [num_chunks, embedding_dim])
    """
    if verbose:
        logger.info(f"Creating embeddings for {len(text_chunks)} chunks (batch_size={batch_size})")

    try:
        # Encode with progress bar
        embeddings = model.encode(
            text_chunks,
            batch_size=batch_size,
            show_progress_bar=verbose,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )

        if verbose:
            logger.info(f"Created embeddings with shape: {embeddings.shape}")

        return embeddings

    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise


def build_faiss_index(embeddings: np.ndarray, verbose: bool = False) -> faiss.Index:
    """
    Build a FAISS index from embeddings.

    Uses IndexFlatIP for exact cosine similarity search (normalized vectors).

    Args:
        embeddings: NumPy array of embeddings
        verbose: Print detailed progress information

    Returns:
        FAISS index
    """
    if verbose:
        logger.info("Building FAISS index")

    embedding_dim = embeddings.shape[1]

    # Use IndexFlatIP for exact inner product search (cosine similarity with normalized vectors)
    index = faiss.IndexFlatIP(embedding_dim)

    # Add embeddings to index
    index.add(embeddings)

    if verbose:
        logger.info(f"FAISS index built successfully ({index.ntotal} vectors)")

    return index


def save_vector_store(index: faiss.Index, metadata: List[Dict[str, Any]],
                     output_dir: str, model_name: str, verbose: bool = False) -> None:
    """
    Save FAISS index and metadata to disk.

    Creates:
    - <output_dir>/index.faiss - FAISS index file
    - <output_dir>/metadata.jsonl - Metadata for each vector
    - <output_dir>/config.json - Vector store configuration

    Args:
        index: FAISS index
        metadata: List of metadata dictionaries (one per vector)
        output_dir: Output directory path
        model_name: Embedding model name
        verbose: Print detailed progress information
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        logger.info(f"Saving vector store to: {output_path}")

    # Save FAISS index
    index_file = output_path / 'index.faiss'
    faiss.write_index(index, str(index_file))
    if verbose:
        logger.info(f"Saved FAISS index: {index_file}")

    # Save metadata
    metadata_file = output_path / 'metadata.jsonl'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        for meta in metadata:
            f.write(json.dumps(meta, ensure_ascii=False) + '\n')
    if verbose:
        logger.info(f"Saved metadata: {metadata_file} ({len(metadata)} records)")

    # Save configuration
    config = {
        'embedding_model': model_name,
        'index_type': 'IndexFlatIP',
        'num_vectors': index.ntotal,
        'embedding_dimension': index.d,
        'metadata_records': len(metadata)
    }
    config_file = output_path / 'config.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    if verbose:
        logger.info(f"Saved configuration: {config_file}")

    logger.info(f"\n✅ Vector store created successfully!")
    logger.info(f"   Location: {output_path}")
    logger.info(f"   Vectors: {index.ntotal}")
    logger.info(f"   Model: {model_name}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Build FAISS vector stores from JSONL files for RAG.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single JSONL file
  %(prog)s -i document.jsonl -o my_vectorstore --model sentence-transformers/all-MiniLM-L6-v2

  # Directory of JSONL files
  %(prog)s -i data_dir/ -o combined_vectorstore --model sentence-transformers/all-mpnet-base-v2

  # With chunking (512 chars, 50 char overlap) for code
  %(prog)s -i document.jsonl -o vectorstore --model jinaai/jina-embeddings-v2-base-code \\
      --chunk-size 512 --overlap 50

  # Verbose output
  %(prog)s -i data/ -o vectorstore --model sentence-transformers/all-MiniLM-L6-v2 -v

Recommended Models:
  sentence-transformers/all-MiniLM-L6-v2
    - Fast, lightweight (384 dim, ~80 MB, max 256 tokens)
    - Recommended: --chunk-size 800-1000 --overlap 150-200
    - (200-250 tokens with 15-20%% overlap)

  sentence-transformers/all-mpnet-base-v2
    - High-quality general (768 dim, ~420 MB, max 384 tokens)
    - Recommended: --chunk-size 1200-1500 --overlap 200-250
    - (300-350 tokens with 15-20%% overlap)

  sentence-transformers/multi-qa-mpnet-base-cos-v1
    - Q&A optimized (768 dim, max 384 tokens)
    - Recommended: --chunk-size 1200-1500 --overlap 200-250
    - (300-350 tokens with 15-20%% overlap)

  jinaai/jina-embeddings-v2-base-code
    - Code & 30+ languages (768 dim, ~500 MB, max 8192 tokens)
    - Recommended: --chunk-size 2000-4000 --overlap 400-600
    - (500-1000 tokens with 15-20%% overlap)

NOTE: Current chunking is CHARACTER-based (not token-based).
      Approximate conversion: 1 token ≈ 4 characters

For more models: https://huggingface.co/models?library=sentence-transformers
"""
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input JSONL file or directory of JSONL files'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output directory for vector store'
    )

    parser.add_argument(
        '--model',
        required=True,
        help='Embedding model name (e.g., sentence-transformers/all-MiniLM-L6-v2, jinaai/jina-embeddings-v2-base-code)'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=None,
        help='Maximum characters per chunk (default: no chunking)'
    )

    parser.add_argument(
        '--overlap',
        type=int,
        default=0,
        help='Number of overlapping characters between chunks (default: 0)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for embedding generation (default: 32)'
    )

    parser.add_argument(
        '--cache-dir',
        default=None,
        help='Directory to cache embedding models (default: data_stores/embedding_models)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.chunk_size is not None and args.chunk_size <= 0:
        print("Error: --chunk-size must be positive", file=sys.stderr)
        sys.exit(1)

    if args.overlap < 0:
        print("Error: --overlap cannot be negative", file=sys.stderr)
        sys.exit(1)

    if args.chunk_size and args.overlap >= args.chunk_size:
        print("Error: --overlap must be less than --chunk-size", file=sys.stderr)
        sys.exit(1)

    if args.batch_size <= 0:
        print("Error: --batch-size must be positive", file=sys.stderr)
        sys.exit(1)

    try:
        # Load JSONL records
        records = load_jsonl_files(args.input, verbose=args.verbose)

        if not records:
            print("Error: No records loaded from input", file=sys.stderr)
            sys.exit(1)

        # Prepare text chunks and metadata
        text_chunks, metadata = prepare_chunks(
            records,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            verbose=args.verbose
        )

        if not text_chunks:
            print("Error: No text chunks created", file=sys.stderr)
            sys.exit(1)

        # Load embedding model
        model = load_embedding_model(args.model, cache_dir=args.cache_dir, verbose=args.verbose)

        # Create embeddings
        embeddings = create_embeddings(
            model,
            text_chunks,
            batch_size=args.batch_size,
            verbose=args.verbose
        )

        # Build FAISS index
        index = build_faiss_index(embeddings, verbose=args.verbose)

        # Save vector store
        save_vector_store(
            index,
            metadata,
            args.output,
            args.model,
            verbose=args.verbose
        )

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

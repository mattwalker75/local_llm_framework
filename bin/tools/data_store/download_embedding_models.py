#!/usr/bin/env python3
"""
Download embedding models for offline RAG vector store creation.

This script downloads recommended sentence-transformer models to the local
cache directory (data_stores/embedding_models/) for offline use.

Usage:
    # Download all recommended models
    ./download_embedding_models.py

    # Download specific models only
    ./download_embedding_models.py --models age-small-en-v1.5 age-code-v1

    # Use custom cache directory
    ./download_embedding_models.py --cache-dir /path/to/cache

Author: Local LLM Framework
License: MIT
"""

import argparse
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers is required.", file=sys.stderr)
    print("Install: pip install sentence-transformers", file=sys.stderr)
    sys.exit(1)

# Recommended models for different use cases
RECOMMENDED_MODELS = {
    'sentence-transformers/all-MiniLM-L6-v2': 'Fast, lightweight general-purpose - 80 MB',
    'sentence-transformers/all-mpnet-base-v2': 'High-quality general-purpose - 420 MB',
    'sentence-transformers/multi-qa-mpnet-base-cos-v1': 'Question-answering optimized - 420 MB',
    'jinaai/jina-embeddings-v2-base-code': 'Code & 30+ programming languages - 500 MB'
}


def download_model(model_name: str, cache_dir: Path, verbose: bool = True) -> bool:
    """
    Download a single embedding model.

    Args:
        model_name: Name of the model to download
        cache_dir: Directory to cache the model
        verbose: Print progress information

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if verbose:
            description = RECOMMENDED_MODELS.get(model_name, 'Unknown model')
            print(f"\n📥 Downloading: {model_name}")
            print(f"   Description: {description}")

        # Download model
        model = SentenceTransformer(model_name, cache_folder=str(cache_dir))

        if verbose:
            dim = model.get_sentence_embedding_dimension()
            print(f"✅ Downloaded successfully (embedding dimension: {dim})")

        return True

    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download embedding models for offline RAG vector store creation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Recommended Models:
  sentence-transformers/all-MiniLM-L6-v2          Fast, lightweight - 80 MB
  sentence-transformers/all-mpnet-base-v2         High-quality general - 420 MB
  sentence-transformers/multi-qa-mpnet-base-cos-v1  Q&A optimized - 420 MB
  jinaai/jina-embeddings-v2-base-code             Code & 30+ languages - 500 MB

Examples:
  # Download all recommended models
  %(prog)s

  # Download specific models only
  %(prog)s --models sentence-transformers/all-MiniLM-L6-v2 jinaai/jina-embeddings-v2-base-code

  # Use custom cache directory
  %(prog)s --cache-dir /path/to/cache

  # Quiet mode (minimal output)
  %(prog)s -q
"""
    )

    parser.add_argument(
        '--models',
        nargs='+',
        default=None,
        help='Specific models to download (default: all recommended models)'
    )

    parser.add_argument(
        '--cache-dir',
        default=None,
        help='Directory to cache models (default: data_stores/embedding_models)'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - minimal output'
    )

    args = parser.parse_args()

    # Determine cache directory
    if args.cache_dir:
        cache_dir = Path(args.cache_dir)
    else:
        # Default: data_stores/embedding_models (project root)
        # Script is in bin/tools/data_store/, so go up 4 levels to project root
        # download_embedding_models.py -> data_store -> tools -> bin -> project_root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        cache_dir = project_root / 'data_stores' / 'embedding_models'

    # Create cache directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print(f"{'=' * 70}")
        print("Embedding Model Downloader")
        print(f"{'=' * 70}")
        print(f"\nCache directory: {cache_dir.absolute()}")

    # Determine which models to download
    if args.models:
        models_to_download = args.models
        if not args.quiet:
            print(f"Models to download: {len(models_to_download)}")
    else:
        models_to_download = list(RECOMMENDED_MODELS.keys())
        if not args.quiet:
            print(f"Downloading all recommended models: {len(models_to_download)}")

    # Download models
    success_count = 0
    failed_models = []

    for model_name in models_to_download:
        if download_model(model_name, cache_dir, verbose=not args.quiet):
            success_count += 1
        else:
            failed_models.append(model_name)

    # Print summary
    if not args.quiet:
        print(f"\n{'=' * 70}")
        print("Download Summary")
        print(f"{'=' * 70}")
        print(f"✅ Successfully downloaded: {success_count}/{len(models_to_download)} models")

        if failed_models:
            print(f"❌ Failed downloads: {', '.join(failed_models)}")
        else:
            print("🎉 All models downloaded successfully!")

        print(f"\nCache location: {cache_dir.absolute()}")
        print("\nYou can now use these models offline with Create_VectorStore.py")

    # Exit with appropriate status
    sys.exit(0 if not failed_models else 1)


if __name__ == '__main__':
    main()

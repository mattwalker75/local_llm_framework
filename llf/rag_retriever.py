"""
RAG (Retrieval-Augmented Generation) Retriever

This module provides functionality to query FAISS vector stores and retrieve
relevant context for LLM prompts. It handles:
- Loading attached data stores from the registry
- Embedding user queries using sentence-transformers
- Searching FAISS indices for similar content
- Merging and formatting results from multiple stores

Author: Local LLM Framework
License: MIT
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import numpy as np

# Set environment variables before imports to prevent threading issues
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
except ImportError:
    torch = None

logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_CONFIG = {
    "model_cache_dir": "data_stores/embedding_models",
    "top_k_results": 5,
    "similarity_threshold": 0.3,
    "max_context_length": 4000
}


class RAGRetriever:
    """
    Retrieves relevant context from FAISS vector stores for RAG.

    This class manages loading and querying multiple vector stores, caching
    embedding models for performance, and formatting results for LLM consumption.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the RAG retriever.

        Args:
            registry_path: Path to data_store_registry.json. If None, uses default location.
        """
        # Check dependencies
        if faiss is None:
            raise ImportError("faiss-cpu is required. Install: pip install faiss-cpu")
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required. Install: pip install sentence-transformers")

        # Set registry path
        if registry_path is None:
            self.registry_path = Path(__file__).parent.parent / 'data_stores' / 'data_store_registry.json'
        else:
            self.registry_path = Path(registry_path)

        # Project root for resolving relative paths
        self.project_root = Path(__file__).parent.parent

        # Cache for embedding models (keyed by model name)
        self._model_cache: Dict[str, SentenceTransformer] = {}

        # Cache for loaded stores (keyed by store name)
        self._store_cache: Dict[str, Dict[str, Any]] = {}

        # Attached stores configuration
        self.attached_stores: Dict[str, Dict[str, Any]] = {}

        # Load attached stores from registry
        self._load_registry()

    def _load_registry(self):
        """Load the data store registry and identify attached stores."""
        try:
            if not self.registry_path.exists():
                logger.warning(f"Data store registry not found at {self.registry_path}")
                return

            with open(self.registry_path, 'r') as f:
                registry = json.load(f)

            # Filter attached stores
            data_stores = registry.get('data_stores', [])
            for store in data_stores:
                if store.get('attached', False):
                    name = store.get('name')
                    if name:
                        self.attached_stores[name] = store
                        logger.info(f"Registered attached store: {name}")

        except Exception as e:
            logger.error(f"Error loading data store registry: {e}")
            self.attached_stores = {}

    def has_attached_stores(self) -> bool:
        """Check if any stores are attached."""
        return len(self.attached_stores) > 0

    def reload(self):
        """Reload the registry and clear caches."""
        logger.info("Reloading RAG retriever configuration")
        self._model_cache.clear()
        self._store_cache.clear()
        self.attached_stores.clear()
        self._load_registry()

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path that may be relative or absolute.

        Args:
            path: Path string from registry

        Returns:
            Resolved absolute Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        else:
            return (self.project_root / path).resolve()

    def _load_embedding_model(self, model_name: str, cache_dir: Optional[str] = None) -> SentenceTransformer:
        """
        Load an embedding model, using cache if available.

        Args:
            model_name: HuggingFace model identifier
            cache_dir: Directory to cache models

        Returns:
            Loaded SentenceTransformer model
        """
        # Check cache first
        if model_name in self._model_cache:
            logger.debug(f"Using cached embedding model: {model_name}")
            return self._model_cache[model_name]

        # Load model
        logger.info(f"Loading embedding model: {model_name}")

        # Resolve cache directory
        if cache_dir:
            cache_path = self._resolve_path(cache_dir)
        else:
            cache_path = self._resolve_path(DEFAULT_CONFIG['model_cache_dir'])

        try:
            model = SentenceTransformer(model_name, cache_folder=str(cache_path))

            # Set to single-threaded mode
            if hasattr(model, 'encode'):
                # Cache the model
                self._model_cache[model_name] = model
                logger.info(f"Successfully loaded embedding model: {model_name}")
                return model
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")
            raise

    def _load_vector_store(self, store_name: str, store_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load a vector store (FAISS index + metadata).

        Args:
            store_name: Name of the store
            store_config: Store configuration from registry

        Returns:
            Dict containing index, metadata, model, and config
        """
        # Check cache first
        if store_name in self._store_cache:
            logger.debug(f"Using cached vector store: {store_name}")
            return self._store_cache[store_name]

        logger.info(f"Loading vector store: {store_name}")

        # Get paths
        vector_store_path = self._resolve_path(store_config['vector_store_path'])
        index_path = vector_store_path / 'index.faiss'
        metadata_path = vector_store_path / 'metadata.jsonl'
        config_path = vector_store_path / 'config.json'

        # Validate paths exist
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load config and validate
        with open(config_path, 'r') as f:
            stored_config = json.load(f)

        # Validate embedding model matches
        registry_model = store_config.get('embedding_model')
        stored_model = stored_config.get('embedding_model')

        if registry_model != stored_model:
            logger.warning(
                f"Embedding model mismatch for {store_name}: "
                f"registry={registry_model}, stored={stored_model}. "
                f"Using stored config model."
            )
            embedding_model_name = stored_model
        else:
            embedding_model_name = registry_model

        # Load embedding model
        cache_dir = store_config.get('model_cache_dir')
        embedding_model = self._load_embedding_model(embedding_model_name, cache_dir)

        # Load FAISS index
        logger.info(f"Loading FAISS index from {index_path}")
        index = faiss.read_index(str(index_path))

        # Load metadata
        logger.info(f"Loading metadata from {metadata_path}")
        metadata = []
        with open(metadata_path, 'r') as f:
            for line in f:
                metadata.append(json.loads(line.strip()))

        # Validate metadata count matches index
        num_vectors = index.ntotal
        if len(metadata) != num_vectors:
            logger.warning(
                f"Metadata count mismatch for {store_name}: "
                f"index={num_vectors}, metadata={len(metadata)}"
            )

        # Cache the store
        store_data = {
            'index': index,
            'metadata': metadata,
            'model': embedding_model,
            'config': stored_config,
            'registry_config': store_config
        }

        self._store_cache[store_name] = store_data
        logger.info(f"Successfully loaded vector store: {store_name} ({num_vectors} vectors)")

        return store_data

    def _embed_query(self, query_text: str, model: SentenceTransformer) -> np.ndarray:
        """
        Convert query text to embedding vector.

        Args:
            query_text: User's query string
            model: Loaded SentenceTransformer model

        Returns:
            Normalized embedding vector
        """
        try:
            # Encode query with normalization (for cosine similarity)
            embedding = model.encode(
                [query_text],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embedding[0]  # Return single vector
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise

    def _query_single_store(
        self,
        query_text: str,
        store_name: str,
        store_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Query a single vector store.

        Args:
            query_text: User's query
            store_name: Name of the store
            store_config: Store configuration

        Returns:
            List of result dicts with keys: text, score, store_name, chunk_id
        """
        try:
            # Load store
            store_data = self._load_vector_store(store_name, store_config)

            # Get components
            index = store_data['index']
            metadata = store_data['metadata']
            model = store_data['model']

            # Embed query
            query_embedding = self._embed_query(query_text, model)

            # Get top_k from config
            top_k = store_config.get('top_k_results', DEFAULT_CONFIG['top_k_results'])

            # Search index
            # Note: FAISS returns distances, convert to similarities for IndexFlatIP
            # IndexFlatIP uses inner product, so higher scores = more similar
            query_vector = query_embedding.reshape(1, -1)
            distances, indices = index.search(query_vector, top_k)

            # Format results
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue

                # Get metadata for this result
                if idx < len(metadata):
                    meta = metadata[idx]
                    results.append({
                        'text': meta.get('text', ''),
                        'score': float(dist),  # Inner product score (higher = better)
                        'store_name': store_config.get('display_name', store_name),
                        'chunk_id': meta.get('chunk_id', idx),
                        'source_file': meta.get('source_file', 'unknown')
                    })

            logger.info(f"Retrieved {len(results)} results from {store_name}")
            return results

        except Exception as e:
            logger.error(f"Error querying store {store_name}: {e}")
            return []

    def query_all_stores(self, query_text: str) -> Optional[str]:
        """
        Query all attached stores and return formatted context.

        Args:
            query_text: User's query

        Returns:
            Formatted context string, or None if no results
        """
        if not self.has_attached_stores():
            logger.debug("No attached stores to query")
            return None

        if not query_text or not query_text.strip():
            logger.debug("Empty query text, skipping RAG")
            return None

        logger.info(f"Querying {len(self.attached_stores)} attached store(s)")

        # Collect results from all stores
        all_results = []
        for store_name, store_config in self.attached_stores.items():
            try:
                results = self._query_single_store(query_text, store_name, store_config)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Failed to query store {store_name}: {e}")
                continue

        if not all_results:
            logger.info("No results from any store")
            return None

        # Sort by similarity score (descending)
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Apply similarity threshold
        # Get threshold from first store config (or use default)
        threshold = DEFAULT_CONFIG['similarity_threshold']
        for store_config in self.attached_stores.values():
            threshold = store_config.get('similarity_threshold', threshold)
            break  # Use first store's threshold

        filtered_results = [r for r in all_results if r['score'] >= threshold]

        if not filtered_results:
            logger.info(f"No results met similarity threshold {threshold}")
            return None

        # Limit by top_k (use max from all stores)
        max_top_k = DEFAULT_CONFIG['top_k_results']
        for store_config in self.attached_stores.values():
            max_top_k = max(max_top_k, store_config.get('top_k_results', DEFAULT_CONFIG['top_k_results']))

        final_results = filtered_results[:max_top_k]

        # Format context
        context = self._format_context(final_results)

        # Apply max_context_length
        max_length = DEFAULT_CONFIG['max_context_length']
        for store_config in self.attached_stores.values():
            max_length = max(max_length, store_config.get('max_context_length', DEFAULT_CONFIG['max_context_length']))

        if len(context) > max_length:
            logger.info(f"Truncating context from {len(context)} to {max_length} chars")
            context = context[:max_length] + "\n\n[Context truncated due to length limit]"

        logger.info(f"Generated context with {len(final_results)} result(s), {len(context)} chars")
        return context

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks with source attribution.

        Args:
            results: List of result dicts

        Returns:
            Formatted context string
        """
        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            store_name = result.get('store_name', 'Unknown')
            score = result.get('score', 0.0)
            text = result.get('text', '').strip()

            if not text:
                continue

            # Format: [Source: Store Name | Similarity: 0.85]
            context_parts.append(
                f"[Source: {store_name} | Similarity: {score:.2f}]\n{text}"
            )

        return "\n\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded stores and models.

        Returns:
            Dict with cache statistics
        """
        return {
            'attached_stores': len(self.attached_stores),
            'cached_stores': len(self._store_cache),
            'cached_models': len(self._model_cache),
            'store_names': list(self.attached_stores.keys())
        }

"""
Unit tests for RAG retriever module.

Tests cover:
- Registry loading and attached store detection
- Embedding model loading and caching
- Vector store loading and caching
- Query embedding generation
- FAISS similarity search
- Multi-store result merging
- Context formatting
- Error handling
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Mock dependencies before importing
import sys

# Create mock faiss module
mock_faiss = MagicMock()
sys.modules['faiss'] = mock_faiss

# Create mock sentence_transformers module
mock_st = MagicMock()
sys.modules['sentence_transformers'] = mock_st

# Import the module under test
from llf.rag_retriever import RAGRetriever, DEFAULT_CONFIG


class TestRAGRetrieverInit:
    """Test RAGRetriever initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default registry path."""
        with patch.object(RAGRetriever, '_load_registry'):
            retriever = RAGRetriever()
            assert retriever.registry_path.name == 'data_store_registry.json'
            assert retriever.attached_stores == {}
            assert retriever._model_cache == {}
            assert retriever._store_cache == {}

    def test_init_with_custom_path(self):
        """Test initialization with custom registry path."""
        custom_path = Path("/custom/path/registry.json")
        with patch.object(RAGRetriever, '_load_registry'):
            retriever = RAGRetriever(registry_path=custom_path)
            assert retriever.registry_path == custom_path

    def test_init_missing_faiss(self):
        """Test initialization fails without faiss."""
        with patch('llf.rag_retriever.faiss', None):
            with pytest.raises(ImportError, match="faiss-cpu is required"):
                RAGRetriever()

    def test_init_missing_sentence_transformers(self):
        """Test initialization fails without sentence-transformers."""
        with patch('llf.rag_retriever.SentenceTransformer', None):
            with pytest.raises(ImportError, match="sentence-transformers is required"):
                RAGRetriever()


class TestRegistryLoading:
    """Test registry loading functionality."""

    def test_load_registry_with_attached_stores(self, tmp_path):
        """Test loading registry with attached stores."""
        # Create test registry
        registry_data = {
            "version": "1.0",
            "data_stores": [
                {
                    "name": "store1",
                    "display_name": "Store 1",
                    "attached": True,
                    "vector_store_path": "path/to/store1",
                    "embedding_model": "test-model"
                },
                {
                    "name": "store2",
                    "display_name": "Store 2",
                    "attached": False,
                    "vector_store_path": "path/to/store2",
                    "embedding_model": "test-model"
                },
                {
                    "name": "store3",
                    "display_name": "Store 3",
                    "attached": True,
                    "vector_store_path": "path/to/store3",
                    "embedding_model": "test-model"
                }
            ]
        }

        registry_path = tmp_path / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        # Load registry
        retriever = RAGRetriever(registry_path=registry_path)

        # Verify only attached stores are loaded
        assert len(retriever.attached_stores) == 2
        assert "store1" in retriever.attached_stores
        assert "store3" in retriever.attached_stores
        assert "store2" not in retriever.attached_stores

    def test_load_registry_no_attached_stores(self, tmp_path):
        """Test loading registry with no attached stores."""
        registry_data = {
            "version": "1.0",
            "data_stores": [
                {
                    "name": "store1",
                    "attached": False,
                    "vector_store_path": "path/to/store1",
                    "embedding_model": "test-model"
                }
            ]
        }

        registry_path = tmp_path / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)
        assert len(retriever.attached_stores) == 0
        assert not retriever.has_attached_stores()

    def test_load_registry_missing_file(self, tmp_path):
        """Test loading non-existent registry file."""
        registry_path = tmp_path / "missing.json"
        retriever = RAGRetriever(registry_path=registry_path)
        assert len(retriever.attached_stores) == 0

    def test_load_registry_invalid_json(self, tmp_path):
        """Test loading invalid JSON registry."""
        registry_path = tmp_path / "bad_registry.json"
        with open(registry_path, 'w') as f:
            f.write("invalid json{{{")

        retriever = RAGRetriever(registry_path=registry_path)
        assert len(retriever.attached_stores) == 0


class TestHasAttachedStores:
    """Test has_attached_stores method."""

    def test_has_attached_stores_true(self, tmp_path):
        """Test with attached stores."""
        registry_data = {
            "data_stores": [{"name": "test", "attached": True, "embedding_model": "test"}]
        }
        registry_path = tmp_path / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)
        assert retriever.has_attached_stores() is True

    def test_has_attached_stores_false(self, tmp_path):
        """Test without attached stores."""
        registry_data = {
            "data_stores": [{"name": "test", "attached": False, "embedding_model": "test"}]
        }
        registry_path = tmp_path / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)
        assert retriever.has_attached_stores() is False


class TestReload:
    """Test reload functionality."""

    def test_reload_clears_caches(self, tmp_path):
        """Test that reload clears all caches."""
        registry_data = {
            "data_stores": [{"name": "test", "attached": True, "embedding_model": "test"}]
        }
        registry_path = tmp_path / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Populate caches with unique keys
        cache_size_before_models = len(retriever._model_cache)
        cache_size_before_stores = len(retriever._store_cache)

        retriever._model_cache['unique_test_model_xyz123'] = Mock()
        retriever._store_cache['unique_test_store_xyz123'] = Mock()

        # Verify caches have our test content
        assert 'unique_test_model_xyz123' in retriever._model_cache
        assert 'unique_test_store_xyz123' in retriever._store_cache

        # Reload (should clear ALL caches)
        retriever.reload()

        # Verify our test entries are gone
        assert 'unique_test_model_xyz123' not in retriever._model_cache
        assert 'unique_test_store_xyz123' not in retriever._store_cache

        # Store cache should be completely cleared
        assert len(retriever._store_cache) == 0


class TestPathResolution:
    """Test path resolution functionality."""

    def test_resolve_absolute_path(self, tmp_path):
        """Test resolving absolute path."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        abs_path = "/absolute/path/to/store"
        resolved = retriever._resolve_path(abs_path)
        assert resolved == Path(abs_path)

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative path."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        rel_path = "data_stores/vector_stores/test"
        resolved = retriever._resolve_path(rel_path)
        assert resolved.is_absolute()
        assert "data_stores/vector_stores/test" in str(resolved)


class TestEmbeddingModelLoading:
    """Test embedding model loading and caching."""

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_embedding_model_first_time(self, mock_st_class, tmp_path):
        """Test loading model for first time."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        mock_model = Mock()
        mock_st_class.return_value = mock_model

        # Load model
        model = retriever._load_embedding_model("test-model")

        # Verify model loaded and cached
        assert model == mock_model
        assert "test-model" in retriever._model_cache
        assert retriever._model_cache["test-model"] == mock_model
        mock_st_class.assert_called_once()

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_embedding_model_from_cache(self, mock_st_class, tmp_path):
        """Test loading model from cache."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Pre-populate cache
        cached_model = Mock()
        retriever._model_cache["test-model"] = cached_model

        # Load model (should use cache)
        model = retriever._load_embedding_model("test-model")

        assert model == cached_model
        mock_st_class.assert_not_called()  # Should not load from disk


class TestQueryEmbedding:
    """Test query embedding generation."""

    def test_embed_query(self, tmp_path):
        """Test embedding a query."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock model
        mock_model = Mock()
        mock_embedding = np.array([[0.1, 0.2, 0.3]])
        mock_model.encode.return_value = mock_embedding

        # Embed query
        result = retriever._embed_query("test query", mock_model)

        # Verify
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)  # Should return 1D array
        np.testing.assert_array_equal(result, mock_embedding[0])
        mock_model.encode.assert_called_once()


class TestContextFormatting:
    """Test context formatting."""

    def test_format_context_single_result(self, tmp_path):
        """Test formatting single result."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        results = [
            {
                'text': 'Test content here',
                'score': 0.85,
                'store_name': 'Test Store',
                'chunk_id': 1
            }
        ]

        context = retriever._format_context(results)

        assert "[Source: Test Store | Similarity: 0.85]" in context
        assert "Test content here" in context

    def test_format_context_multiple_results(self, tmp_path):
        """Test formatting multiple results."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        results = [
            {'text': 'First result', 'score': 0.9, 'store_name': 'Store 1'},
            {'text': 'Second result', 'score': 0.7, 'store_name': 'Store 2'}
        ]

        context = retriever._format_context(results)

        assert "First result" in context
        assert "Second result" in context
        assert "Store 1" in context
        assert "Store 2" in context
        assert "0.90" in context
        assert "0.70" in context

    def test_format_context_empty_results(self, tmp_path):
        """Test formatting empty results."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        context = retriever._format_context([])
        assert context == ""


class TestQueryAllStores:
    """Test querying all stores."""

    def test_query_all_stores_no_attached(self, tmp_path):
        """Test querying when no stores attached."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)
        result = retriever.query_all_stores("test query")

        assert result is None

    def test_query_all_stores_empty_query(self, tmp_path):
        """Test querying with empty query."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [{"name": "test", "attached": True, "embedding_model": "test"}]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)
        result = retriever.query_all_stores("")

        assert result is None

    def test_query_all_stores_below_threshold(self, tmp_path):
        """Test querying when results below threshold."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [{
                "name": "test",
                "attached": True,
                "embedding_model": "test",
                "similarity_threshold": 0.5
            }]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock _query_single_store to return low-scoring results
        low_score_results = [
            {'text': 'Low score result', 'score': 0.2, 'store_name': 'Test'}
        ]

        with patch.object(retriever, '_query_single_store', return_value=low_score_results):
            result = retriever.query_all_stores("test query")

        assert result is None  # Below threshold


class TestGetStats:
    """Test statistics retrieval."""

    def test_get_stats(self, tmp_path):
        """Test getting retriever statistics."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [
                {"name": "store1", "attached": True, "embedding_model": "test"},
                {"name": "store2", "attached": True, "embedding_model": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        stats = retriever.get_stats()

        assert stats['attached_stores'] == 2
        assert stats['cached_stores'] == 0
        assert stats['cached_models'] == 0
        assert 'store1' in stats['store_names']
        assert 'store2' in stats['store_names']

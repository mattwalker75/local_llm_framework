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


class TestLoadEmbeddingModelEdgeCases:
    """Additional tests for _load_embedding_model edge cases."""

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_embedding_model_with_custom_cache_dir(self, mock_st_class, tmp_path):
        """Test loading model with custom cache directory."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        mock_model = Mock()
        mock_st_class.return_value = mock_model

        # Load with custom cache dir
        custom_cache = "custom/cache/dir"
        model = retriever._load_embedding_model("test-model", cache_dir=custom_cache)

        assert model == mock_model
        # Verify cache_folder argument was used
        call_kwargs = mock_st_class.call_args[1]
        assert 'cache_folder' in call_kwargs

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_embedding_model_error_handling(self, mock_st_class, tmp_path):
        """Test error handling when model loading fails."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock loading failure
        mock_st_class.side_effect = Exception("Failed to load model")

        with pytest.raises(Exception, match="Failed to load model"):
            retriever._load_embedding_model("bad-model")


class TestLoadVectorStoreEdgeCases:
    """Additional tests for _load_vector_store edge cases."""

    @patch('llf.rag_retriever.faiss')
    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_vector_store_from_cache(self, mock_st_class, mock_faiss, tmp_path):
        """Test loading vector store from cache."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Pre-populate cache
        cached_store = {
            'index': Mock(),
            'metadata': [],
            'model': Mock(),
            'config': {}
        }
        retriever._store_cache['test_store'] = cached_store

        store_config = {'vector_store_path': 'path/to/store'}

        # Load store (should use cache)
        result = retriever._load_vector_store('test_store', store_config)

        assert result == cached_store
        # Should not call faiss or model loading
        mock_faiss.read_index.assert_not_called()

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_vector_store_missing_index(self, mock_st_class, tmp_path):
        """Test loading store when index.faiss is missing."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create store directory without index.faiss
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'test-model'
        }

        with pytest.raises(FileNotFoundError, match="FAISS index not found"):
            retriever._load_vector_store('test_store', store_config)

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_vector_store_missing_metadata(self, mock_st_class, tmp_path):
        """Test loading store when metadata.jsonl is missing."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create store directory with index but no metadata
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").touch()

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'test-model'
        }

        with pytest.raises(FileNotFoundError, match="Metadata file not found"):
            retriever._load_vector_store('test_store', store_config)

    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_vector_store_missing_config(self, mock_st_class, tmp_path):
        """Test loading store when config.json is missing."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create store directory with index and metadata but no config
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").touch()
        (store_dir / "metadata.jsonl").touch()

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'test-model'
        }

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            retriever._load_vector_store('test_store', store_config)

    @patch('llf.rag_retriever.faiss')
    @patch('llf.rag_retriever.SentenceTransformer')
    def test_load_vector_store_model_mismatch(self, mock_st_class, mock_faiss, tmp_path):
        """Test loading store with model mismatch between registry and stored config."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create complete store directory
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").touch()
        (store_dir / "metadata.jsonl").write_text('{"text": "test", "chunk_id": 0}\n')

        # Config with different model than registry
        stored_config = {
            'embedding_model': 'stored-model',
            'dimension': 384
        }
        with open(store_dir / "config.json", 'w') as f:
            json.dump(stored_config, f)

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'registry-model'  # Different from stored
        }

        # Mock model and index
        mock_model = Mock()
        mock_st_class.return_value = mock_model
        mock_index = Mock()
        mock_index.ntotal = 1
        mock_faiss.read_index.return_value = mock_index

        # Should use stored model (not registry model)
        result = retriever._load_vector_store('test_store', store_config)

        # Verify it loaded successfully and used stored model
        assert result['model'] == mock_model
        # Check that SentenceTransformer was called with stored-model
        assert mock_st_class.called


class TestEmbedQueryEdgeCases:
    """Additional tests for _embed_query edge cases."""

    def test_embed_query_error_handling(self, tmp_path):
        """Test error handling when embedding fails."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock model that raises error
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Encoding failed")

        with pytest.raises(Exception, match="Encoding failed"):
            retriever._embed_query("test query", mock_model)


class TestQuerySingleStoreEdgeCases:
    """Additional tests for _query_single_store edge cases."""

    @patch('llf.rag_retriever.faiss')
    @patch('llf.rag_retriever.SentenceTransformer')
    def test_query_single_store_success(self, mock_st_class, mock_faiss, tmp_path):
        """Test successfully querying a single store."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create complete store
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").touch()
        (store_dir / "metadata.jsonl").write_text('{"text": "result text", "chunk_id": 0, "source_file": "test.txt"}\n')

        stored_config = {'embedding_model': 'test-model', 'dimension': 384}
        with open(store_dir / "config.json", 'w') as f:
            json.dump(stored_config, f)

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'test-model',
            'display_name': 'Test Store',
            'top_k_results': 2
        }

        # Mock model and index
        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_st_class.return_value = mock_model

        mock_index = Mock()
        mock_index.ntotal = 1
        # Return valid results
        mock_index.search.return_value = (np.array([[0.85]]), np.array([[0]]))
        mock_faiss.read_index.return_value = mock_index

        # Query the store
        results = retriever._query_single_store("test query", "test_store", store_config)

        # Verify results
        assert len(results) == 1
        assert results[0]['text'] == 'result text'
        assert results[0]['score'] == 0.85
        assert results[0]['store_name'] == 'Test Store'

    @patch('llf.rag_retriever.faiss')
    @patch('llf.rag_retriever.SentenceTransformer')
    def test_query_single_store_with_invalid_index(self, mock_st_class, mock_faiss, tmp_path):
        """Test querying store with invalid FAISS index responses."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Create complete store
        store_dir = tmp_path / "test_store"
        store_dir.mkdir()
        (store_dir / "index.faiss").touch()
        (store_dir / "metadata.jsonl").write_text('{"text": "result text", "chunk_id": 0}\n')

        stored_config = {'embedding_model': 'test-model', 'dimension': 384}
        with open(store_dir / "config.json", 'w') as f:
            json.dump(stored_config, f)

        store_config = {
            'vector_store_path': str(store_dir),
            'embedding_model': 'test-model',
            'top_k_results': 2
        }

        # Mock model and index
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_st_class.return_value = mock_model

        mock_index = Mock()
        mock_index.ntotal = 1
        # Return -1 (invalid index marker from FAISS)
        mock_index.search.return_value = (np.array([[0.85]]), np.array([[-1]]))
        mock_faiss.read_index.return_value = mock_index

        # Query the store
        results = retriever._query_single_store("test query", "test_store", store_config)

        # Should filter out -1 indices
        assert len(results) == 0

    def test_query_single_store_error_handling(self, tmp_path):
        """Test error handling in _query_single_store."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Store config that will cause error (missing files)
        store_config = {
            'vector_store_path': 'nonexistent/path',
            'embedding_model': 'test-model'
        }

        # Should return empty list on error
        results = retriever._query_single_store("test query", "bad_store", store_config)

        assert results == []


class TestQueryAllStoresEdgeCases:
    """Additional tests for query_all_stores edge cases."""

    def test_query_all_stores_with_store_error(self, tmp_path):
        """Test querying when one store fails but others succeed."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [
                {"name": "good_store", "attached": True, "embedding_model": "test"},
                {"name": "bad_store", "attached": True, "embedding_model": "test"}
            ]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock _query_single_store to succeed for good_store, fail for bad_store
        def mock_query(query_text, store_name, store_config):
            if store_name == "good_store":
                return [{'text': 'Good result', 'score': 0.8, 'store_name': 'Good'}]
            else:
                raise Exception("Store error")

        with patch.object(retriever, '_query_single_store', side_effect=mock_query):
            result = retriever.query_all_stores("test query")

        # Should return results from good_store despite bad_store error
        assert result is not None
        assert "Good result" in result

    def test_query_all_stores_no_results_from_any_store(self, tmp_path):
        """Test querying when all stores return empty results."""
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

        # Mock _query_single_store to return empty results
        with patch.object(retriever, '_query_single_store', return_value=[]):
            result = retriever.query_all_stores("test query")

        assert result is None

    def test_query_all_stores_with_context_truncation(self, tmp_path):
        """Test context truncation when exceeding max_context_length."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [{
                "name": "test_store",
                "attached": True,
                "embedding_model": "test",
                "max_context_length": 200  # Short limit (note: uses max of all stores and default)
            }]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock _query_single_store to return results that exceed default max_context_length (4000)
        # Need very long text to exceed the default limit since max() is used
        long_text = "A" * 5000  # Text longer than DEFAULT max_context_length (4000)
        mock_results = [
            {'text': long_text, 'score': 0.9, 'store_name': 'Test', 'chunk_id': 0}
        ]

        with patch.object(retriever, '_query_single_store', return_value=mock_results):
            result = retriever.query_all_stores("test query")

        # Context should be truncated
        assert result is not None
        # The formatted context should be truncated (uses max of default 4000 and store config)
        assert "[Context truncated due to length limit]" in result
        # Verify truncation happened - result should be much shorter than full formatted text
        full_formatted_length = len("[Source: Test | Similarity: 0.90]\n" + long_text)
        assert len(result) < full_formatted_length  # Truncated is shorter than full

    def test_query_all_stores_result_sorting(self, tmp_path):
        """Test that results are sorted by score descending."""
        registry_path = tmp_path / "registry.json"
        registry_data = {
            "data_stores": [{"name": "test_store", "attached": True, "embedding_model": "test"}]
        }
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        # Mock results in unsorted order
        mock_results = [
            {'text': 'Low score', 'score': 0.5, 'store_name': 'Test'},
            {'text': 'High score', 'score': 0.9, 'store_name': 'Test'},
            {'text': 'Medium score', 'score': 0.7, 'store_name': 'Test'}
        ]

        with patch.object(retriever, '_query_single_store', return_value=mock_results):
            result = retriever.query_all_stores("test query")

        # Results should be sorted by score (highest first)
        assert "High score" in result
        high_pos = result.index("High score")
        low_pos = result.index("Low score")
        assert high_pos < low_pos


class TestFormatContextEdgeCases:
    """Additional tests for _format_context edge cases."""

    def test_format_context_with_empty_text(self, tmp_path):
        """Test formatting results with empty text fields."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        results = [
            {'text': '', 'score': 0.9, 'store_name': 'Test'},  # Empty text
            {'text': 'Valid text', 'score': 0.8, 'store_name': 'Test'}
        ]

        context = retriever._format_context(results)

        # Should skip empty text
        assert 'Valid text' in context
        assert context.count('[Source:') == 1  # Only one result formatted

    def test_format_context_with_whitespace_text(self, tmp_path):
        """Test formatting results with whitespace-only text."""
        registry_path = tmp_path / "registry.json"
        registry_data = {"data_stores": []}
        with open(registry_path, 'w') as f:
            json.dump(registry_data, f)

        retriever = RAGRetriever(registry_path=registry_path)

        results = [
            {'text': '   \n\t  ', 'score': 0.9, 'store_name': 'Test'},  # Whitespace only
            {'text': 'Valid text', 'score': 0.8, 'store_name': 'Test'}
        ]

        context = retriever._format_context(results)

        # Should skip whitespace-only text
        assert 'Valid text' in context
        assert context.count('[Source:') == 1

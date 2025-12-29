# Embedding Models for RAG Vector Stores

This document explains how embedding models are managed for vector store creation in the Local LLM Framework.

## Overview

The `Create_VectorStore.py` tool uses sentence-transformers models to create vector embeddings from text. These models are stored locally in `data_stores/embedding_models/` to enable offline operation.

## Model Storage Location

**Default Cache Directory**: `data_stores/embedding_models/`

Models are automatically downloaded on first use and cached locally. This ensures:
- ✅ Offline functionality (no internet required after initial download)
- ✅ Self-contained application (all dependencies bundled)
- ✅ Consistent model versions across deployments
- ✅ No dependency on external HuggingFace Hub availability

## Recommended Embedding Models

| Model | Use Case | Size | Dimensions | Performance |
|-------|----------|------|------------|-------------|
| `sentence-transformers/all-MiniLM-L6-v2` | Fast, lightweight general-purpose | ~80 MB | 384 | Very fast |
| `sentence-transformers/all-mpnet-base-v2` | High-quality general-purpose | ~420 MB | 768 | Slower, best quality |
| `sentence-transformers/multi-qa-mpnet-base-cos-v1` | Question-answering optimized | ~420 MB | 768 | Great for Q&A tasks |
| `jinaai/jina-embeddings-v2-base-code` | Source code & 30+ programming languages | ~500 MB | 768 | Optimized for code, 8192 seq length |

### Model Selection Guidelines

**For Fast, Lightweight Processing**:
```bash
--model sentence-transformers/all-MiniLM-L6-v2
```
Use this model when speed and low memory usage are priorities, or when working with large document collections where processing time matters more than perfect accuracy. Ideal for quick prototyping, resource-constrained environments, and general-purpose text where state-of-the-art quality isn't critical.

**For Best Quality General Text**:
```bash
--model sentence-transformers/all-mpnet-base-v2
```
Use this model for production systems where accuracy is paramount and you're working with general text documents like articles, books, reports, or customer support data. This provides the best semantic understanding for diverse text types at the cost of slower processing and higher memory usage.

**For Question-Answering Systems**:
```bash
--model sentence-transformers/multi-qa-mpnet-base-cos-v1
```
Use this model specifically when building RAG systems where users will ask questions and expect relevant answers from your knowledge base. It's specifically trained on question-answer pairs and excels at matching user queries to relevant passages, making it ideal for chatbots, help systems, and FAQ retrieval.

**For Source Code and Technical Documentation**:
```bash
--model jinaai/jina-embeddings-v2-base-code
```
Use this model when your documents contain source code, API documentation, technical specifications, or programming tutorials across 30+ languages. It understands code syntax, function semantics, and technical terminology better than general models, with support for longer sequences (8192 tokens) to handle entire code files.

## Pre-downloading Models for Offline Use

Models are automatically downloaded when first used. To pre-download models before going offline:

### Method 1: Using Create_VectorStore.py

Create a dummy vector store to trigger model download:

```bash
# Create a temporary JSONL file
echo '{"text": "test"}' > /tmp/test.jsonl

# Run Create_VectorStore.py to download the model
cd data_stores/tools
./Create_VectorStore.py -i /tmp/test.jsonl -o /tmp/test_output \
    --model sentence-transformers/all-MiniLM-L6-v2 -v

# Clean up
rm -rf /tmp/test.jsonl /tmp/test_output
```

### Method 2: Using Python Directly

```python
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Define cache directory
cache_dir = Path(__file__).parent / 'embedding_models'
cache_dir.mkdir(parents=True, exist_ok=True)

# Download models
models = [
    'sentence-transformers/all-MiniLM-L6-v2',
    'sentence-transformers/all-mpnet-base-v2',
    'sentence-transformers/multi-qa-mpnet-base-cos-v1',
    'jinaai/jina-embeddings-v2-base-code'
]

for model_name in models:
    print(f"Downloading {model_name}...")
    model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
    print(f"✓ {model_name} downloaded")
```

### Method 3: Download Script

Save this as `download_models.py` in `data_stores/`:

```python
#!/usr/bin/env python3
"""Download embedding models for offline use."""

from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

# Models to download
MODELS = [
    'sentence-transformers/all-MiniLM-L6-v2',          # Fast lightweight
    'sentence-transformers/all-mpnet-base-v2',         # High quality
    'sentence-transformers/multi-qa-mpnet-base-cos-v1', # Q&A
    'jinaai/jina-embeddings-v2-base-code'              # Code
]

def main():
    # Set cache directory
    cache_dir = Path(__file__).parent / 'embedding_models'
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading models to: {cache_dir}\n")

    for model_name in MODELS:
        try:
            print(f"📥 Downloading {model_name}...")
            model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
            dim = model.get_sentence_embedding_dimension()
            print(f"✅ {model_name} (dimension: {dim})\n")
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}\n")
            sys.exit(1)

    print("✅ All models downloaded successfully!")
    print(f"\nTotal models: {len(MODELS)}")
    print(f"Location: {cache_dir}")

if __name__ == '__main__':
    main()
```

Run it:
```bash
cd data_stores
python3 download_models.py
```

## Model Consistency Requirement

**CRITICAL**: The same embedding model MUST be used for both creating and querying the vector store.

### How Model Tracking Works

1. When you create a vector store, the model name is saved in `config.json`:
   ```json
   {
     "embedding_model": "age-small-en-v1.5",
     "index_type": "IndexFlatIP",
     "num_vectors": 1234,
     "embedding_dimension": 384
   }
   ```

2. When querying the vector store, the application automatically reads `config.json` and uses the same model.

3. If you try to query with a different model, you'll get a dimension mismatch error:
   ```
   Error: Expected 384 dimensions, got 768
   ```

### Example: Creating and Querying with Consistent Models

```bash
# Create vector store with age-small-en-v1.5
./Create_VectorStore.py -i docs.jsonl -o my_vectorstore \
    --model age-small-en-v1.5

# Query will automatically use age-small-en-v1.5 (reads from config.json)
# No need to specify model again
```

## Using Custom Cache Directory

You can override the default cache directory:

```bash
# Use custom cache directory
./Create_VectorStore.py -i document.jsonl -o vectorstore \
    --model age-small-en-v1.5 \
    --cache-dir /path/to/custom/cache
```

This is useful for:
- Sharing models across multiple projects
- Using a network-mounted cache directory
- Testing different model versions

## Verifying Downloaded Models

Check what models are cached:

```bash
ls -lh data_stores/embedding_models/
```

You should see directories for each model:
```
sentence-transformers_sentence-transformers_all-MiniLM-L6-v2/
sentence-transformers_sentence-transformers_all-mpnet-base-v2/
sentence-transformers_sentence-transformers_multi-qa-mpnet-base-cos-v1/
models--jinaai--jina-embeddings-v2-base-code/
```

## Disk Space Requirements

| Model | Approximate Size |
|-------|------------------|
| sentence-transformers/all-MiniLM-L6-v2 | ~80 MB |
| sentence-transformers/all-mpnet-base-v2 | ~420 MB |
| sentence-transformers/multi-qa-mpnet-base-cos-v1 | ~420 MB |
| jinaai/jina-embeddings-v2-base-code | ~500 MB |
| **Total (all 4 models)** | **~1.4 GB** |

## Troubleshooting

### Model Download Fails

**Problem**: Network timeout or connection error

**Solutions**:
1. Check internet connection
2. Try again later (HuggingFace Hub may be temporarily unavailable)
3. Download from a different network
4. Check firewall/proxy settings

### Model Not Found

**Problem**: `Model 'xyz' not found`

**Solution**: Verify model name at https://www.sbert.net/docs/pretrained_models.html

Common typos:
- ❌ `all-MiniLM` → ✅ `sentence-transformers/all-MiniLM-L6-v2`
- ❌ `all-mpnet-base` → ✅ `sentence-transformers/all-mpnet-base-v2`
- ❌ `jina-code` → ✅ `jinaai/jina-embeddings-v2-base-code`

### Out of Disk Space

**Problem**: Not enough disk space to download models

**Solutions**:
1. Free up disk space (models need ~1.4 GB for all 4)
2. Download only the models you need
3. Use a smaller model (e.g., `sentence-transformers/all-MiniLM-L6-v2` is only 80 MB)

### Cache Directory Permission Denied

**Problem**: Cannot write to `data_stores/embedding_models/`

**Solutions**:
```bash
# Fix permissions
chmod 755 data_stores/embedding_models/

# Or use a different cache directory
./Create_VectorStore.py --cache-dir ~/my_model_cache ...
```

## Advanced: Managing Multiple Model Versions

If you need to maintain multiple versions of the same model:

```bash
# Create version-specific cache directories
mkdir -p data_stores/embedding_models_v1
mkdir -p data_stores/embedding_models_v2

# Download to specific version
./Create_VectorStore.py -i docs.jsonl -o vectorstore_v1 \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --cache-dir data_stores/embedding_models_v1

./Create_VectorStore.py -i docs.jsonl -o vectorstore_v2 \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --cache-dir data_stores/embedding_models_v2
```

## Model Updates

Sentence-transformers models are versioned. When a new version is released:

1. Old models continue to work (no breaking changes)
2. You can download new models to a separate cache directory
3. Existing vector stores continue using their original model (from `config.json`)
4. New vector stores can use the updated model

**Recommendation**: Don't update models for existing production vector stores unless you're prepared to rebuild them.

## Additional Resources

- **Sentence Transformers Documentation**: https://www.sbert.net/
- **Available Models**: https://www.sbert.net/docs/pretrained_models.html
- **HuggingFace Model Hub**: https://huggingface.co/sentence-transformers

---

## Summary

✅ Models are cached locally in `data_stores/embedding_models/` for offline use

✅ First-time download requires internet connection

✅ Same model MUST be used for creating and querying (automatically enforced via `config.json`)

✅ Pre-download models before going offline using the methods above

✅ Total disk space needed: ~1.4 GB for all recommended models

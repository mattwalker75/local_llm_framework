# Data Store Registry Guide: data_store_registry.json

This document explains how to configure and manage RAG (Retrieval-Augmented Generation) vector stores using the `data_stores/data_store_registry.json` file.

**Last Updated:** 2025-12-28

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Structure](#configuration-structure)
3. [Parameters Reference](#parameters-reference)
4. [Attached vs Detached States](#attached-vs-detached-states)
5. [Configuration Examples](#configuration-examples)
6. [CLI Commands](#cli-commands)
7. [Creating Vector Stores](#creating-vector-stores)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Related Documentation](#related-documentation)

---

## Overview

The `data_store_registry.json` file manages RAG vector stores that provide context to the LLM. It allows you to:

- Register multiple vector stores (documentation, code, FAQs, etc.)
- Attach/detach stores to enable/disable RAG integration
- Configure embedding models and search parameters
- Track store metadata and statistics
- **Automatically integrate RAG context when stores are attached**

**Location:** `data_stores/data_store_registry.json`

**Key Concept:** When a data store is set to `"attached": true`, the framework automatically queries it with every user message and injects relevant context into the system prompt. No additional configuration needed in `config_prompt.json`.

---

## Configuration Structure

A minimal data store entry looks like this:

```json
{
  "version": "1.0",
  "last_updated": "2025-12-28",
  "data_stores": [
    {
      "name": "my_docs",
      "display_name": "My Documentation",
      "description": "Technical documentation for my project",
      "attached": false,
      "vector_store_path": "data_stores/vector_stores/my_docs",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dimension": 384,
      "index_type": "IndexFlatIP",
      "model_cache_dir": "data_stores/embedding_models",
      "top_k_results": 5,
      "similarity_threshold": 0.3,
      "max_context_length": 4000,
      "created_date": "2025-12-28",
      "num_vectors": 0,
      "metadata": {
        "source_type": "documentation",
        "content_description": "General documentation",
        "search_mode": "semantic"
      }
    }
  ],
  "metadata": {
    "description": "Registry of all available RAG vector stores for the LLM Framework",
    "schema_version": "1.0"
  }
}
```

---

## Parameters Reference

### Core Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | String | Yes | - | Unique identifier for the data store (lowercase, no spaces) |
| `display_name` | String | Yes | - | Human-readable name shown in CLI and UI |
| `description` | String | Yes | - | Brief description of the store's contents |
| `attached` | Boolean | Yes | `false` | Whether to use this store for RAG (true = active, false = inactive) |
| `vector_store_path` | String | Yes | - | Path to the FAISS vector store directory (relative or absolute) |
| `embedding_model` | String | Yes | - | HuggingFace model name for embeddings (must match creation model) |
| `embedding_dimension` | Integer | Yes | - | Vector dimension (384 for MiniLM, 768 for MPNet/Jina models) |
| `index_type` | String | Yes | `"IndexFlatIP"` | FAISS index type (currently only IndexFlatIP supported) |

### Optional Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_cache_dir` | String | No | `"data_stores/embedding_models"` | Directory for caching embedding models |
| `top_k_results` | Integer | No | `5` | Number of most similar documents to retrieve per query |
| `similarity_threshold` | Float | No | `0.3` | Minimum similarity score (0.0-1.0) to include results |
| `max_context_length` | Integer | No | `4000` | Maximum characters to send to LLM from this store |
| `created_date` | String | No | `null` | ISO date when vector store was created |
| `num_vectors` | Integer | No | `0` | Total number of vectors in the store |
| `metadata` | Object | No | `{}` | Additional metadata for the store |

### Metadata Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metadata.source_type` | String | `"general"` | Type of content: documentation, code, qa_pairs, general, etc. |
| `metadata.content_description` | String | `""` | Detailed description of store contents |
| `metadata.search_mode` | String | `"semantic"` | Search strategy: semantic, hybrid, keyword |

---

## Attached vs Detached States

### Attached (`"attached": true`)

When a data store is **attached**:
- The LLM **automatically** queries it with every user message
- Relevant context is retrieved and added to the system prompt
- RAG integration happens seamlessly without any code changes
- The store's `top_k_results`, `similarity_threshold`, and `max_context_length` are used

**Example automatic RAG context added to system prompt:**
```
---

# Knowledge Base Context

The following information has been retrieved from attached knowledge bases...

[Retrieved context from store]

# RAG Instructions

- Use the context above when it's relevant to the user's question
- Cite specific information from the context when applicable
- If the context doesn't contain relevant information, rely on your general knowledge
```

### Detached (`"attached": false`)

When a data store is **detached**:
- The vector store exists but is not queried
- No RAG context is added to prompts
- Useful for temporarily disabling a store without deleting it
- Can be re-attached at any time via CLI or by editing the JSON

**Use Cases for Detached:**
- Testing different context combinations
- Temporarily reducing token usage
- Preventing irrelevant context from specific stores
- Development and debugging

---

## Configuration Examples

### Example 1: Documentation Store

A store for product documentation with standard settings:

```json
{
  "name": "product_docs",
  "display_name": "Product Documentation",
  "description": "Official product documentation and API references",
  "attached": true,
  "vector_store_path": "data_stores/vector_stores/product_docs",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "index_type": "IndexFlatIP",
  "model_cache_dir": "data_stores/embedding_models",
  "top_k_results": 5,
  "similarity_threshold": 0.3,
  "max_context_length": 4000,
  "created_date": "2025-12-28",
  "num_vectors": 1250,
  "metadata": {
    "source_type": "documentation",
    "content_description": "Product docs, API references, tutorials",
    "search_mode": "semantic"
  }
}
```

**Use Case:** General documentation lookup for user questions about product features.

---

### Example 2: Code Repository Store

A store for code examples and repositories with higher precision:

```json
{
  "name": "code_examples",
  "display_name": "Code Examples",
  "description": "Python code examples and snippets from our repository",
  "attached": true,
  "vector_store_path": "data_stores/vector_stores/code_examples",
  "embedding_model": "jinaai/jina-embeddings-v2-base-code",
  "embedding_dimension": 768,
  "index_type": "IndexFlatIP",
  "model_cache_dir": "data_stores/embedding_models",
  "top_k_results": 3,
  "similarity_threshold": 0.5,
  "max_context_length": 6000,
  "created_date": "2025-12-28",
  "num_vectors": 850,
  "metadata": {
    "source_type": "code",
    "content_description": "Python code examples, utilities, and best practices",
    "search_mode": "semantic"
  }
}
```

**Use Case:** Code-specific RAG with specialized embeddings. Higher similarity threshold (0.5) for more precise matches. Higher max context (6000) for longer code blocks.

---

### Example 3: FAQ Store

A store for frequently asked questions with broad retrieval:

```json
{
  "name": "faq",
  "display_name": "FAQ Database",
  "description": "Frequently asked questions and answers",
  "attached": true,
  "vector_store_path": "data_stores/vector_stores/faq",
  "embedding_model": "sentence-transformers/multi-qa-mpnet-base-cos-v1",
  "embedding_dimension": 768,
  "index_type": "IndexFlatIP",
  "model_cache_dir": "data_stores/embedding_models",
  "top_k_results": 8,
  "similarity_threshold": 0.2,
  "max_context_length": 3000,
  "created_date": "2025-12-28",
  "num_vectors": 420,
  "metadata": {
    "source_type": "qa_pairs",
    "content_description": "Customer support FAQs and troubleshooting guides",
    "search_mode": "semantic"
  }
}
```

**Use Case:** FAQ lookups optimized for question-answering. Uses QA-specific embedding model. Lower similarity threshold (0.2) to catch more potential matches. Higher top_k (8) to provide multiple relevant FAQs.

---

### Example 4: Multiple Stores Working Together

You can attach multiple stores simultaneously - the LLM will query all of them:

```json
{
  "data_stores": [
    {
      "name": "python_docs",
      "display_name": "Python Documentation",
      "description": "Official Python 3.11 documentation",
      "attached": true,
      "vector_store_path": "data_stores/vector_stores/python_docs",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dimension": 384,
      "index_type": "IndexFlatIP",
      "top_k_results": 5,
      "similarity_threshold": 0.3,
      "max_context_length": 4000,
      "num_vectors": 3200
    },
    {
      "name": "project_code",
      "display_name": "Project Codebase",
      "description": "Our internal codebase",
      "attached": true,
      "vector_store_path": "data_stores/vector_stores/project_code",
      "embedding_model": "jinaai/jina-embeddings-v2-base-code",
      "embedding_dimension": 768,
      "index_type": "IndexFlatIP",
      "top_k_results": 3,
      "similarity_threshold": 0.4,
      "max_context_length": 5000,
      "num_vectors": 1850
    },
    {
      "name": "wiki",
      "display_name": "Company Wiki",
      "description": "Internal company wiki and processes",
      "attached": false,
      "vector_store_path": "data_stores/vector_stores/wiki",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dimension": 384,
      "index_type": "IndexFlatIP",
      "top_k_results": 5,
      "similarity_threshold": 0.3,
      "max_context_length": 3000,
      "num_vectors": 680
    }
  ]
}
```

**Behavior:** The LLM will retrieve context from both `python_docs` and `project_code` (attached), but not from `wiki` (detached).

---

## CLI Commands

The framework provides convenient CLI commands for managing data stores:

### List All Data Stores

```bash
# List all registered data stores
llf datastore list

# List only attached data stores
llf datastore list --attached
```

**Output:**
```
Product Documentation          attached
Code Examples                  attached
FAQ Database                   detached
```

---

### Attach a Data Store

```bash
# Attach a specific data store by name
llf datastore attach product_docs

# Attach a data store by display name
llf datastore attach "Product Documentation"

# Attach all data stores at once
llf datastore attach all
```

**Result:** Sets `"attached": true` in the registry. RAG integration activates immediately for new conversations.

---

### Detach a Data Store

```bash
# Detach a specific data store by name
llf datastore detach product_docs

# Detach by display name
llf datastore detach "Product Documentation"

# Detach all data stores at once
llf datastore detach all
```

**Result:** Sets `"attached": false` in the registry. RAG integration stops immediately for new conversations.

---

### Show Data Store Info

```bash
# Show detailed information about a data store
llf datastore info product_docs

# Or use display name
llf datastore info "Product Documentation"
```

**Output:**
```
Product Documentation (product_docs)
Description: Official product documentation and API references
Status: attached
Location: /path/to/project/data_stores/vector_stores/product_docs
Embedding Model: sentence-transformers/all-MiniLM-L6-v2
Number of Vectors: 1250
```

---

## Creating Vector Stores

The framework provides tools to create vector stores from various document types:

### Available Conversion Tools

Located in `data_stores/tools/`:

| Tool | Purpose | Input Format |
|------|---------|--------------|
| `Process_DOC.py` | Convert MS Word documents | .docx, .doc |
| `Process_PDF.py` | Convert PDF documents | .pdf |
| `Process_MD.py` | Convert Markdown files | .md |
| `Process_TXT.py` | Convert plain text files | .txt |
| `Process_WEB.py` | Convert website content | URLs |
| `Create_VectorStore.py` | Build FAISS index from JSONL | .jsonl |
| `Validate_JSONL.py` | Validate JSONL format | .jsonl |

### Workflow for Creating a Vector Store

1. **Convert documents to JSONL format:**

```bash
# Example: Convert PDF documents
python data_stores/tools/Process_PDF.py \
  --input docs/ \
  --output data_stores/processed/my_docs.jsonl

# Example: Convert Markdown files
python data_stores/tools/Process_MD.py \
  --input wiki/ \
  --output data_stores/processed/wiki.jsonl
```

2. **Validate JSONL (optional but recommended):**

```bash
python data_stores/tools/Validate_JSONL.py \
  --input data_stores/processed/my_docs.jsonl
```

3. **Create the vector store:**

```bash
python data_stores/tools/Create_VectorStore.py \
  --input data_stores/processed/my_docs.jsonl \
  --output data_stores/vector_stores/my_docs \
  --model sentence-transformers/all-MiniLM-L6-v2
```

4. **Add entry to `data_store_registry.json`:**

```json
{
  "name": "my_docs",
  "display_name": "My Documentation",
  "description": "My project documentation",
  "attached": false,
  "vector_store_path": "data_stores/vector_stores/my_docs",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "index_type": "IndexFlatIP",
  "model_cache_dir": "data_stores/embedding_models",
  "top_k_results": 5,
  "similarity_threshold": 0.3,
  "max_context_length": 4000,
  "created_date": "2025-12-28",
  "num_vectors": 0,
  "metadata": {
    "source_type": "documentation",
    "content_description": "General documentation",
    "search_mode": "semantic"
  }
}
```

5. **Attach the store to enable RAG:**

```bash
llf datastore attach my_docs
```

---

## Best Practices

### Choosing Embedding Models

**For General Documentation:**
- `sentence-transformers/all-MiniLM-L6-v2` - Fast, lightweight, good quality (384 dims)
- `sentence-transformers/all-mpnet-base-v2` - Higher quality, larger (768 dims)

**For Code:**
- `jinaai/jina-embeddings-v2-base-code` - Optimized for code understanding (768 dims)

**For Question-Answering:**
- `sentence-transformers/multi-qa-mpnet-base-cos-v1` - Optimized for QA pairs (768 dims)

**Important:** The embedding model used for creating the vector store MUST match the one specified in the registry.

### Optimizing Parameters

**`top_k_results`:**
- **3-5**: Focused, precise context (good for code)
- **5-8**: Balanced retrieval (good for general docs)
- **8-10**: Broad context (good for FAQs, exploratory queries)

**`similarity_threshold`:**
- **0.5-0.7**: Very strict, only highly relevant matches
- **0.3-0.5**: Balanced precision and recall (recommended)
- **0.1-0.3**: Broader matching, more results (good for FAQs)

**`max_context_length`:**
- **2000-4000**: Standard for most use cases
- **4000-6000**: Longer documents or code
- **1000-2000**: Minimal context to reduce token usage

### Multiple Store Strategy

1. **Attach only relevant stores** - Don't attach everything by default
2. **Use different parameters** - Tune each store for its content type
3. **Monitor token usage** - Multiple attached stores increase prompt size
4. **Test combinations** - Verify stores work well together

### Performance Tips

1. **Cache embedding models** - Set `model_cache_dir` to reuse downloads
2. **Use appropriate dimensions** - Smaller dimensions (384) are faster
3. **Limit context length** - Balance between information and speed
4. **Detach unused stores** - Reduce query overhead

---

## Troubleshooting

### Problem: "Data store not found"

**Solution:**
1. Verify the `name` in your command matches the registry
2. Check the registry file exists and is valid JSON
3. Use `llf datastore list` to see all available stores

### Problem: RAG context not appearing in responses

**Solution:**
1. Verify the store is attached: `llf datastore list --attached`
2. Check that `vector_store_path` points to a valid directory
3. Ensure the directory contains `index.faiss`, `metadata.jsonl`, and `config.json`
4. Verify `num_vectors` is greater than 0
5. Try lowering `similarity_threshold` to get more results

### Problem: "Embedding model mismatch"

**Solution:**
- The `embedding_model` in the registry MUST match the model used to create the vector store
- Check `data_stores/vector_stores/YOUR_STORE/config.json` to see the actual model used
- Recreate the vector store with the correct model if needed

### Problem: Too many/too few results

**Solution:**
1. **Too many:** Increase `similarity_threshold`, decrease `top_k_results`
2. **Too few:** Decrease `similarity_threshold`, increase `top_k_results`
3. **Wrong results:** Consider using a different `embedding_model` more suited to your content type

### Problem: High token usage / slow responses

**Solution:**
1. Reduce `max_context_length` for each store
2. Reduce `top_k_results` to retrieve fewer documents
3. Detach stores that aren't frequently used
4. Consider splitting large stores into specialized smaller stores

### Problem: "No such file or directory" error

**Solution:**
1. Check that `vector_store_path` exists
2. Ensure you've actually created the vector store (see [Creating Vector Stores](#creating-vector-stores))
3. Verify paths are correct (can be relative to project root or absolute)

---

## Related Documentation

- [Main Configuration](config_json.md) - LLM endpoint and server configuration
- [Prompt Configuration](config_prompt_json.md) - System prompts and message formatting
- [Memory Registry](memory_registry_json.md) - Long-term memory system configuration
- [Tools Registry](tools_registry_json.md) - Tool system configuration
- [Modules Registry](modules_registry_json.md) - Pluggable module configuration

---

## Additional Resources

### Example Registry

See the current registry: `data_stores/data_store_registry.json`

### Vector Store Tools

All conversion and creation tools: `data_stores/tools/`

### FAISS Index Files

Each vector store directory contains:
- `index.faiss` - FAISS index file
- `metadata.jsonl` - Document metadata and content
- `config.json` - Store configuration (embedding model, dimensions, etc.)

---

For additional help, refer to the main [README.md](../README.md) or open an issue on GitHub.

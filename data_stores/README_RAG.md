# RAG (Retrieval-Augmented Generation) Guide

This guide explains how to use RAG with the Local LLM Framework to give your LLM access to custom knowledge bases.

---

## Table of Contents

1. [What is RAG?](#what-is-rag)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Managing Data Stores](#managing-data-stores)
5. [Creating Vector Stores](#creating-vector-stores)
6. [Configuration Reference](#configuration-reference)
7. [Troubleshooting](#troubleshooting)

---

## What is RAG?

**RAG** (Retrieval-Augmented Generation) enhances your LLM with custom knowledge by:
1. Converting your documents into searchable vector embeddings
2. Finding relevant passages when you ask questions
3. Injecting those passages into the LLM's system prompt
4. Allowing the LLM to answer questions using your documents

**Example**: Instead of asking an LLM about your resume and getting generic advice, with RAG it can see your actual work history and give personalized answers.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install faiss-cpu sentence-transformers
```

### 2. Convert Your Documents

Convert your documents to JSONL format using the provided tools:

```bash
# Convert a Word document
python data_stores/tools/Process_DOC.py -i my_resume.docx -o resume.jsonl

# Convert a PDF
python data_stores/tools/Process_PDF.py -i document.pdf -o document.jsonl

# Convert markdown
python data_stores/tools/Process_MD.py -i notes.md -o notes.jsonl
```

### 3. Create a Vector Store

```bash
python data_stores/tools/Create_VectorStore.py \
  -i resume.jsonl \
  -o data_stores/vector_stores/my_resume \
  --model sentence-transformers/all-MiniLM-L6-v2
```

### 4. Register the Data Store

Edit `data_stores/data_store_registry.json` and add your store:

```json
{
  "name": "my_resume",
  "display_name": "My Resume",
  "description": "My professional resume and work history",
  "attached": true,
  "vector_store_path": "data_stores/vector_stores/my_resume",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "index_type": "IndexFlatIP"
}
```

### 5. Use in Chat

```bash
# CLI chat
llf chat

# Or GUI
llf gui
```

When you ask questions, the LLM will automatically retrieve relevant context from your attached data stores!

---

## How It Works

### Architecture Flow

```
User Question
    ↓
RAG Retriever checks for attached data stores
    ↓
Converts question to vector embedding
    ↓
Searches all attached vector stores
    ↓
Retrieves top-k most similar passages
    ↓
Filters by similarity threshold
    ↓
Formats context with source attribution
    ↓
Injects into system prompt
    ↓
LLM receives enriched prompt with your knowledge
    ↓
Generates answer using retrieved context
```

### Where Context is Injected

The retrieved context is added to the **system prompt** in this format:

```
You have access to a knowledge base with relevant information.

---

# Knowledge Base Context

[Source: My Resume | Similarity: 0.89]
Senior Software Engineer with 10+ years of experience...

[Source: My Resume | Similarity: 0.76]
Education: BS Computer Science, MIT, 2012...

# RAG Instructions

- Use the context above when it's relevant to the user's question
- Cite specific information from the context when applicable
- If the context doesn't contain relevant information, rely on your general knowledge
```

### When RAG is Active

RAG is automatically activated when:
- At least one data store has `"attached": true` in the registry
- The user sends a message in chat (CLI or GUI)
- The RAG retriever successfully loads

RAG is skipped when:
- No data stores are attached
- RAG dependencies are missing
- The query returns no results above the similarity threshold

---

## Managing Data Stores

### List All Data Stores

```bash
llf datastore list
```

Output:
```
DOCX Resume                    attached
PDF Resume                     attached
Technical Docs                 detached
```

### List Only Attached Stores

```bash
llf datastore list --attached
```

### Attach a Data Store

```bash
llf datastore attach my_resume
```

### Detach a Data Store

```bash
llf datastore detach my_resume
```

### Attach/Detach All

```bash
llf datastore attach all
llf datastore detach all
```

### Get Data Store Info

```bash
llf datastore info my_resume
```

Output:
```
My Resume (my_resume)
Description: My professional resume
Status: attached
Location: /path/to/data_stores/vector_stores/my_resume
Number of Vectors: 50

Configuration:
  • Embedding Model: sentence-transformers/all-MiniLM-L6-v2
  • Embedding Dimension: 384
  • Index Type: IndexFlatIP
  • Top K Results: 5
  • Similarity Threshold: 0.3
```

### GUI Management

```bash
llf gui
```

Navigate to the **Data Stores** tab to:
- View all available data stores
- Attach/detach stores with one click
- See real-time information about each store

---

## Creating Vector Stores

### Document Conversion Tools

#### Word Documents (.docx, .doc, .rtf)

```bash
python data_stores/tools/Process_DOC.py \
  -i resume.docx \
  -o resume.jsonl \
  --chunk-size 1000 \
  --overlap 150
```

#### PDF Files

```bash
python data_stores/tools/Process_PDF.py \
  -i document.pdf \
  -o document.jsonl \
  --chunk-size 1200 \
  --overlap 200
```

#### Markdown Files

```bash
python data_stores/tools/Process_MD.py \
  -i notes.md \
  -o notes.jsonl \
  --preserve-headings
```

#### Web Pages

```bash
python data_stores/tools/Process_WEB.py \
  -i https://example.com/article \
  -o article.jsonl
```

#### Plain Text

```bash
python data_stores/tools/Process_TXT.py \
  -i document.txt \
  -o document.jsonl \
  --chunk-size 800
```

### Vector Store Creation

#### Basic Usage

```bash
python data_stores/tools/Create_VectorStore.py \
  -i data.jsonl \
  -o data_stores/vector_stores/my_store \
  --model sentence-transformers/all-MiniLM-L6-v2
```

#### With Custom Settings

```bash
python data_stores/tools/Create_VectorStore.py \
  -i data.jsonl \
  -o data_stores/vector_stores/my_store \
  --model sentence-transformers/all-mpnet-base-v2 \
  --chunk-size 1500 \
  --overlap 250 \
  -v
```

#### Choosing the Right Model

See [EMBEDDING_MODELS.md](EMBEDDING_MODELS.md) for detailed guidance.

**Quick recommendations**:
- **General text**: `sentence-transformers/all-mpnet-base-v2`
- **Q&A systems**: `sentence-transformers/multi-qa-mpnet-base-cos-v1`
- **Code & technical docs**: `jinaai/jina-embeddings-v2-base-code`
- **Fast/lightweight**: `sentence-transformers/all-MiniLM-L6-v2`

---

## Configuration Reference

### Registry Schema

Each data store in `data_store_registry.json` has:

#### Required Fields

```json
{
  "name": "unique_store_id",
  "display_name": "Human Readable Name",
  "description": "Brief description",
  "attached": true,
  "vector_store_path": "data_stores/vector_stores/unique_store_id",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "index_type": "IndexFlatIP"
}
```

#### Optional Fields (with defaults)

```json
{
  "model_cache_dir": "data_stores/embedding_models",  // Model cache location
  "top_k_results": 5,                                  // Max results per query
  "similarity_threshold": 0.3,                         // Min similarity (0.0-1.0)
  "max_context_length": 4000,                          // Max chars in context
  "created_date": "2025-12-26",                        // Creation date
  "num_vectors": 50,                                   // Total vectors
  "metadata": {
    "source_type": "documentation",                    // Content type
    "content_description": "General documentation",    // Description
    "search_mode": "semantic"                          // Search strategy
  }
}
```

### Parameter Explanations

| Parameter | Description | Default | Notes |
|-----------|-------------|---------|-------|
| **attached** | Whether to use this store | `false` | Only attached stores are queried |
| **embedding_model** | HuggingFace model ID | Required | Must match creation model |
| **embedding_dimension** | Vector size | Required | 384 for MiniLM, 768 for MPNet |
| **index_type** | FAISS index type | `IndexFlatIP` | Use IP for cosine similarity |
| **top_k_results** | Results per store | `5` | Higher = more context |
| **similarity_threshold** | Min score to include | `0.3` | Range: 0.0-1.0 |
| **max_context_length** | Max chars total | `4000` | Prevents token overflow |

### Adjusting Retrieval Quality

**Get more results**:
```json
"top_k_results": 10,
"similarity_threshold": 0.2
```

**Get higher quality results**:
```json
"top_k_results": 3,
"similarity_threshold": 0.5
```

**Reduce context length**:
```json
"max_context_length": 2000
```

---

## Troubleshooting

### "No context retrieved"

**Possible causes**:
- No data stores attached → Check `llf datastore list --attached`
- Query doesn't match content → Lower `similarity_threshold` in registry
- Vector store empty → Check `num_vectors` in `llf datastore info`

**Solution**:
```bash
# Verify stores are attached
llf datastore attach my_store

# Lower threshold in registry
"similarity_threshold": 0.2
```

### "Embedding model mismatch"

**Error**: "registry=model-a, stored=model-b"

**Cause**: Registry has different model than used during creation

**Solution**: Update registry to match stored config:
```bash
# Check stored model
cat data_stores/vector_stores/my_store/config.json

# Update registry to match
```

### Vector Store Creation Fails

**Segmentation fault on macOS**:
- Already handled in `Create_VectorStore.py`
- Uses single-threaded mode for Python 3.13+

**Out of memory**:
- Use smaller batch size: `--batch-size 8`
- Use lighter model: `--model sentence-transformers/all-MiniLM-L6-v2`

### Context Not Appearing in Response

**Check**:
1. Verify RAG initialized: Look for "RAG retriever initialized" in logs
2. Check attached stores: `llf datastore list --attached`
3. Test retrieval directly:
   ```python
   from llf.rag_retriever import RAGRetriever
   r = RAGRetriever()
   print(r.query_all_stores("your question"))
   ```

### Slow Query Performance

**First query**: 2-3 seconds (model loading)
**Subsequent queries**: 100-300ms (models cached)

**To speed up**:
- Use lighter model (MiniLM instead of MPNet)
- Reduce `top_k_results`
- Reduce number of attached stores

---

## Advanced Usage

### Multiple Data Stores

You can attach multiple stores simultaneously:

```bash
llf datastore attach technical_docs
llf datastore attach company_policies
llf datastore attach code_examples
```

Results from all attached stores are **merged and sorted by similarity**.

### Custom System Prompts with RAG

In `configs/config_prompt.json`:

```json
{
  "system_prompt": "You are a technical documentation assistant."
}
```

RAG context will be **appended** to your system prompt automatically:

```
You are a technical documentation assistant.

---

# Knowledge Base Context
[Retrieved passages here]
...
```

### Programmatic Usage

```python
from llf.rag_retriever import RAGRetriever
from llf.prompt_config import PromptConfig

# Initialize retriever
retriever = RAGRetriever()

# Check what's attached
print(retriever.get_stats())

# Query directly
context = retriever.query_all_stores("What is my experience?")
print(context)

# Use in prompt config
pc = PromptConfig()
messages = pc.build_messages("Tell me about my work history")
# RAG context automatically included in system prompt
```

### Reloading After Registry Changes

```python
from llf.rag_retriever import RAGRetriever

retriever = RAGRetriever()

# Make changes to data_store_registry.json...

# Reload
retriever.reload()
```

---

## Best Practices

1. **Choose the right embedding model** for your content type
2. **Use appropriate chunk sizes**:
   - Small chunks (800-1000) for precise retrieval
   - Large chunks (1500-2000) for more context
3. **Tune similarity threshold** based on results:
   - Start at 0.3, lower if getting no results
   - Raise to 0.5+ for stricter matching
4. **Monitor context length** to avoid token limits
5. **Update vector stores** when source documents change
6. **Test queries** before deploying to production

---

## Next Steps

- Read [EMBEDDING_MODELS.md](EMBEDDING_MODELS.md) for model selection guide
- Explore document conversion tools in `data_stores/tools/`
- Check example registry at `data_stores/data_store_registry.json`
- Join discussions about RAG improvements

---

**Need help?** Open an issue at https://github.com/anthropics/claude-code/issues

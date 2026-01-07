# Datastore Logic Flow

This document explains the complete logic flow when a datastore is enabled in the Local LLM Framework (LLF), including detailed examples and internal processing.

## Table of Contents

1. [What is a Datastore?](#what-is-a-datastore)
2. [High-Level Flow](#high-level-flow)
3. [Detailed Logic Flow](#detailed-logic-flow)
4. [Examples](#examples)
5. [Internal Processing](#internal-processing)

## What is a Datastore?

A **datastore** in LLF is a persistent storage mechanism that allows the LLM to:
- Store and retrieve structured data
- Maintain state across conversations
- Query information using semantic search
- Build knowledge bases from documents

**Common Use Cases**:
- Document Q&A systems
- Long-term memory storage
- Semantic search over large datasets
- Persistent knowledge bases

## High-Level Flow

```
┌──────────────┐
│ User Message │
└──────┬───────┘
       │
       ↓
┌────────────────────────────────────────────────────────┐
│ 1. LLM Client Initialization                          │
│    - Load enabled datastores from config              │
│    - Initialize datastore connections                 │
│    - Verify datastore availability                    │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 2. Message Processing                                  │
│    - Analyze user message                             │
│    - Determine if datastore query is needed           │
│    - Extract query parameters                         │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│ LLM Decides: │  │ LLM Decides:     │
│ No Datastore │  │ Use Datastore    │
│ Needed       │  │                  │
└──────┬───────┘  └────────┬─────────┘
       │                   │
       │                   ↓
       │          ┌────────────────────────────┐
       │          │ 3. Datastore Query         │
       │          │    - Format query          │
       │          │    - Execute search        │
       │          │    - Retrieve results      │
       │          └────────┬───────────────────┘
       │                   │
       │                   ↓
       │          ┌────────────────────────────┐
       │          │ 4. Context Augmentation    │
       │          │    - Add results to prompt │
       │          │    - Include metadata      │
       │          │    - Format for LLM        │
       │          └────────┬───────────────────┘
       │                   │
       └───────────┬───────┘
                   │
                   ↓
         ┌─────────────────────┐
         │ 5. LLM Generation   │
         │    - Process prompt │
         │    - Generate reply │
         └─────────┬───────────┘
                   │
                   ↓
         ┌─────────────────────┐
         │ 6. Response to User │
         └─────────────────────┘
```

## Detailed Logic Flow

### Phase 1: Initialization

```
┌─────────────────────────────────────────────────────────────┐
│ LLMClient.__init__()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Load config.json       │
        │ {                      │
        │   "datastores": [      │
        │     {                  │
        │       "type": "vector",│
        │       "enabled": true, │
        │       "config": {...}  │
        │     }                  │
        │   ]                    │
        │ }                      │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ DatastoreManager()     │
        │ - Parse config         │
        │ - Validate settings    │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ For each enabled       │
        │ datastore:             │
        │                        │
        │ 1. Load driver module  │
        │ 2. Initialize conn     │
        │ 3. Verify connection   │
        │ 4. Load schema/index   │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ Datastore Ready        │
        │ - Connection pool up   │
        │ - Indexes loaded       │
        │ - Ready for queries    │
        └────────────────────────┘
```

### Phase 2: Query Decision

```
┌─────────────────────────────────────────────────────────────┐
│ User: "What did we discuss about the database schema?"      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ LLM Analyzes Message           │
        │                                │
        │ Question indicators:           │
        │ ✓ "What did we discuss..."     │
        │ ✓ Past tense (memory query)    │
        │ ✓ Reference to "we"            │
        │                                │
        │ Decision: Query datastore      │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Extract Query Parameters       │
        │                                │
        │ query: "database schema"       │
        │ type: "semantic_search"        │
        │ limit: 5                       │
        │ filters: {                     │
        │   "conversation_id": "abc123"  │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Format Datastore Query         │
        │                                │
        │ {                              │
        │   "operation": "search",       │
        │   "collection": "conversations"│
        │   "query": {                   │
        │     "text": "database schema", │
        │     "embedding_model": "...",  │
        │     "top_k": 5                 │
        │   },                           │
        │   "filters": {...}             │
        │ }                              │
        └────────────────────────────────┘
```

### Phase 3: Datastore Execution

```
┌─────────────────────────────────────────────────────────────┐
│ Datastore.execute(query)                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Step 1: Validate Query         │
        │ - Check required fields        │
        │ - Validate data types          │
        │ - Check permissions            │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 2: Generate Embedding     │
        │ (for semantic search)          │
        │                                │
        │ Input: "database schema"       │
        │ ↓                              │
        │ Embedding Model                │
        │ ↓                              │
        │ Vector: [0.123, -0.456, ...]   │
        │ (768 dimensions)               │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 3: Vector Search          │
        │                                │
        │ QUERY:                         │
        │ SELECT id, content, metadata   │
        │ FROM vectors                   │
        │ WHERE conversation_id = 'abc'  │
        │ ORDER BY similarity DESC       │
        │ LIMIT 5                        │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 4: Retrieve Results       │
        │                                │
        │ Results: [                     │
        │   {                            │
        │     "id": "msg_001",           │
        │     "content": "We discussed..."│
        │     "similarity": 0.92,        │
        │     "metadata": {              │
        │       "timestamp": "...",      │
        │       "role": "assistant"      │
        │     }                          │
        │   },                           │
        │   {...}, {...}                 │
        │ ]                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Step 5: Post-process           │
        │ - Re-rank by relevance         │
        │ - Filter by threshold          │
        │ - Format for context           │
        └────────────────────────────────┘
```

### Phase 4: Context Augmentation

```
┌─────────────────────────────────────────────────────────────┐
│ Build Augmented Prompt                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │ Original User Message              │
        │ "What did we discuss about the     │
        │  database schema?"                 │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Add Datastore Context              │
        │                                    │
        │ --- Relevant Information ---       │
        │                                    │
        │ [From previous conversation]       │
        │ User: "How should we design the    │
        │       database schema?"            │
        │                                    │
        │ Assistant: "For the database       │
        │ schema, I recommend using a        │
        │ normalized design with:            │
        │ - Users table (id, name, email)    │
        │ - Posts table (id, user_id, ...)   │
        │ - Comments table (...)"            │
        │                                    │
        │ [Similarity: 0.92]                 │
        │ [Timestamp: 2025-01-05 14:30]      │
        │                                    │
        │ --- End Context ---                │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Final Prompt to LLM                │
        │                                    │
        │ System: You are a helpful AI with  │
        │ access to conversation history.    │
        │                                    │
        │ Context: [... datastore results ...│
        │                                    │
        │ User: What did we discuss about    │
        │ the database schema?               │
        └────────────────────────────────────┘
```

### Phase 5: LLM Response

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Processes Augmented Prompt                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │ LLM Reasoning                      │
        │                                    │
        │ "The context shows a previous      │
        │ discussion about database design.  │
        │ The user asked about schema and    │
        │ I recommended a normalized design  │
        │ with Users, Posts, and Comments    │
        │ tables. I should summarize this."  │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Generated Response                 │
        │                                    │
        │ "Based on our previous discussion, │
        │ we talked about designing a        │
        │ normalized database schema with    │
        │ three main tables:                 │
        │                                    │
        │ 1. Users table - storing user info │
        │ 2. Posts table - with foreign key  │
        │    to Users                        │
        │ 3. Comments table - linking to     │
        │    Posts                           │
        │                                    │
        │ The design focused on normalization│
        │ to avoid data duplication."        │
        └────────────────────────────────────┘
```

## Examples

### Example 1: Document Q&A

**Scenario**: User has uploaded documentation and wants to query it.

```python
# 1. Setup: Load documents into datastore
from llf.datastore_manager import DatastoreManager

manager = DatastoreManager()

# Load and index documents
documents = [
    {
        "id": "doc1",
        "content": "FastAPI is a modern web framework for building APIs...",
        "metadata": {"source": "fastapi_docs.md", "section": "intro"}
    },
    {
        "id": "doc2",
        "content": "To install FastAPI: pip install fastapi uvicorn...",
        "metadata": {"source": "fastapi_docs.md", "section": "installation"}
    },
    # ... more documents
]

for doc in documents:
    manager.add_document(
        datastore_name="docs",
        document=doc
    )
```

**User Query**:
```
User: "How do I install FastAPI?"
```

**Flow**:

1. **LLM analyzes message**:
   - Detects question about FastAPI
   - Determines datastore query needed
   - Extracts: query="install FastAPI"

2. **Datastore search**:
   ```python
   results = manager.search(
       datastore_name="docs",
       query="install FastAPI",
       top_k=3
   )
   # Returns:
   # [
   #   {
   #     "content": "To install FastAPI: pip install fastapi uvicorn...",
   #     "similarity": 0.95,
   #     "metadata": {...}
   #   }
   # ]
   ```

3. **Context augmentation**:
   ```
   System: You are a helpful AI assistant with access to documentation.

   Context from documentation:
   ---
   To install FastAPI: pip install fastapi uvicorn...
   [Source: fastapi_docs.md, Section: installation]
   ---

   User: How do I install FastAPI?
   ```

4. **LLM response**:
   ```
   To install FastAPI, run:

   pip install fastapi uvicorn

   FastAPI is the main framework, and uvicorn is the ASGI server needed to run it.
   ```

### Example 2: Conversation Memory

**Scenario**: Multi-turn conversation with memory.

```
Turn 1:
User: "My name is Alice and I'm working on a Python project"
Assistant: "Nice to meet you, Alice! I'd be happy to help with your Python project..."

[System stores in datastore]:
{
  "conversation_id": "conv_123",
  "turn": 1,
  "user_message": "My name is Alice...",
  "assistant_response": "Nice to meet you...",
  "entities": ["Alice", "Python project"],
  "timestamp": "2025-01-06T10:00:00Z"
}

Turn 2:
User: "What's my name?"
```

**Flow**:

1. **LLM analyzes**: Needs to recall user's name

2. **Datastore query**:
   ```python
   results = manager.search(
       datastore_name="conversation_memory",
       query="user name",
       filters={"conversation_id": "conv_123"},
       top_k=5
   )
   # Returns conversation history mentioning "Alice"
   ```

3. **Context provided**:
   ```
   Context from conversation history:
   ---
   User said: "My name is Alice and I'm working on a Python project"
   [Turn 1, 5 minutes ago]
   ---

   User: What's my name?
   ```

4. **Response**:
   ```
   Your name is Alice!
   ```

### Example 3: Semantic Search Over Code

**Scenario**: Search codebase for specific functionality.

```python
# Setup: Index codebase
codebase = [
    {
        "file": "auth.py",
        "function": "login_user",
        "code": "def login_user(username, password):\n    # Validate credentials...",
        "description": "Authenticates user with username and password"
    },
    {
        "file": "auth.py",
        "function": "logout_user",
        "code": "def logout_user(session_id):\n    # Clear session...",
        "description": "Logs out user by clearing their session"
    },
    # ... more functions
]

for item in codebase:
    manager.add_document(
        datastore_name="codebase",
        document=item
    )
```

**User Query**:
```
User: "Where is the authentication logic?"
```

**Flow**:

1. **Query datastore**:
   ```python
   results = manager.search(
       datastore_name="codebase",
       query="authentication logic",
       top_k=3
   )
   ```

2. **Results**:
   ```python
   [
       {
           "file": "auth.py",
           "function": "login_user",
           "description": "Authenticates user with username and password",
           "similarity": 0.94
       },
       {
           "file": "auth.py",
           "function": "logout_user",
           "description": "Logs out user by clearing their session",
           "similarity": 0.87
       }
   ]
   ```

3. **Response**:
   ```
   The authentication logic is in auth.py:

   - login_user() - Authenticates user with username and password
   - logout_user() - Logs out user by clearing their session

   Would you like to see the implementation of either function?
   ```

## Internal Processing

### Datastore Configuration

```json
{
  "datastores": [
    {
      "name": "conversation_memory",
      "type": "vector",
      "enabled": true,
      "driver": "chromadb",
      "config": {
        "collection_name": "conversations",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
        "distance_metric": "cosine",
        "persist_directory": "~/.llf/datastores/conversations"
      }
    },
    {
      "name": "documents",
      "type": "vector",
      "enabled": true,
      "driver": "faiss",
      "config": {
        "index_type": "IVF",
        "nlist": 100,
        "embedding_model": "openai/text-embedding-ada-002",
        "dimension": 1536
      }
    }
  ]
}
```

### Query Processing Pipeline

```
User Query
    ↓
┌──────────────────────┐
│ 1. Query Analysis   │
│ - Intent detection  │
│ - Entity extraction │
│ - Query type        │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 2. Query Routing    │
│ - Select datastore  │
│ - Choose search type│
│ - Set parameters    │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 3. Embedding        │
│ - Tokenize query    │
│ - Generate vector   │
│ - Normalize         │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 4. Search           │
│ - Vector similarity │
│ - Apply filters     │
│ - Rank results      │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 5. Post-processing  │
│ - Re-rank           │
│ - Filter threshold  │
│ - Format context    │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 6. Context Assembly │
│ - Build prompt      │
│ - Add metadata      │
│ - Send to LLM       │
└──────────────────────┘
```

### Storage Schema

**Vector Storage**:
```
Collection: conversations
├── Vector: [0.123, -0.456, 0.789, ...]  (384-dim)
├── Metadata: {
│   "conversation_id": "conv_123",
│   "turn": 1,
│   "role": "user",
│   "timestamp": "2025-01-06T10:00:00Z",
│   "entities": ["Alice", "Python"]
│   }
└── Content: "My name is Alice and I'm working on a Python project"
```

**Index Structure** (FAISS):
```
IVF Index
├── Quantizer: 100 clusters
├── Inverted Lists: [
│   ├── Cluster 0: [vec_1, vec_5, vec_12, ...]
│   ├── Cluster 1: [vec_2, vec_8, vec_15, ...]
│   └── ...
│   ]
└── Metadata Store: {
    "vec_1": {...},
    "vec_2": {...}
    }
```

### Performance Optimizations

1. **Caching**:
   ```python
   # Cache recent queries
   cache = {
       "query_hash_123": {
           "results": [...],
           "timestamp": "2025-01-06T10:00:00Z",
           "ttl": 300  # 5 minutes
       }
   }
   ```

2. **Batch Processing**:
   ```python
   # Batch embed multiple queries
   queries = ["query1", "query2", "query3"]
   embeddings = model.encode(queries)  # Batch encode
   ```

3. **Approximate Search**:
   ```python
   # Use ANN for large datasets
   index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
   index.nprobe = 10  # Search 10 nearest clusters
   ```

## Summary

When a datastore is enabled:

1. **Initialization**: Datastore connections established at startup
2. **Query Decision**: LLM determines when to query datastore
3. **Search**: Semantic or keyword search executed
4. **Augmentation**: Results added to LLM context
5. **Generation**: LLM uses augmented context for response
6. **Storage**: New information optionally stored for future use

The datastore acts as the LLM's external memory and knowledge base, enabling it to:
- Recall past conversations
- Answer questions from documents
- Search code repositories
- Maintain persistent knowledge

---

**Last Updated**: 2025-01-06

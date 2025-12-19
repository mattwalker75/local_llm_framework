# Data Stores Directory

This directory is designated for storing data store files used in **RAG (Retrieval-Augmented Generation)** functionality.

## Purpose

Data stores provide additional context to LLM queries by storing and retrieving relevant information from external sources. This enables:
- Knowledge base integration
- Document retrieval
- Context augmentation
- Domain-specific information injection

## Current Status

**This feature is currently a placeholder.** The data store management commands are available in the CLI but not yet implemented:

```bash
llf datastore list               # List all available data stores
llf datastore list --attached    # List only attached data stores
llf datastore attach             # Attach data store to query
llf datastore detach             # Detach data store
llf datastore info DATA_STORE_NAME  # Show data store information
```

## Future Implementation

When implemented, this directory will contain:
- Vector databases for semantic search
- Document embeddings
- Knowledge base files
- RAG configuration files
- Index files for fast retrieval

## Usage

For now, this directory serves as a placeholder. Future versions of LLF will support:
1. Adding documents and data sources
2. Creating vector embeddings
3. Attaching/detaching data stores to queries
4. Querying augmented with relevant context from data stores

## Related Documentation

- See [README.md](../README.md) for general LLF information
- See [docs/USAGE.md](../docs/USAGE.md) for command usage
- See [docs/CONFIG_README.md](../docs/CONFIG_README.md) for configuration options

---

**Note:** This feature is planned for a future release. The current version (v0.1.0) focuses on core LLM interaction capabilities.

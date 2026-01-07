# Complete System Flow

This document shows the complete logic flow when **all components** (Datastore, Memory, Modules, and Tools) are enabled simultaneously in the Local LLM Framework.

## Table of Contents

1. [Overview](#overview)
2. [Complete Architecture](#complete-architecture)
3. [Detailed Flow](#detailed-flow)
4. [Complete Example](#complete-example)
5. [Component Interactions](#component-interactions)

## Overview

When all components are enabled, they work together in a coordinated pipeline:

- **Memory**: Provides conversation context and facts
- **Datastore**: Supplies knowledge from documents/data
- **Modules**: Transform input and output
- **Tools**: Execute actions when needed

Each component has its place in the processing pipeline and can interact with others.

## Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER MESSAGE                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIALIZATION (At Startup)                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Memory     │  │  Datastore   │  │   Modules    │             │
│  │   Manager    │  │   Manager    │  │   Manager    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                      │
│         │ Load history     │ Connect to DB    │ Load preprocessor   │
│         │ Load facts       │ Load indexes     │ Load postprocessor  │
│         │                  │                  │                      │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              Tools Manager                            │          │
│  │  - Load enabled tools                                │          │
│  │  - Build tool definitions for LLM                    │          │
│  │  - Configure security (whitelist, approval, etc.)    │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: INPUT PREPROCESSING                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Input: "Bonjour! What did we discuss about FastAPI?"         │
│         │                                                            │
│         ↓                                                            │
│  ┌─────────────────────────────────────────┐                       │
│  │ Preprocessor Module 1: Language Detector│                       │
│  │ Detects: French                          │                       │
│  │ Stores: metadata.original_lang = "fr"    │                       │
│  └─────────────┬───────────────────────────┘                       │
│                ↓                                                     │
│  ┌─────────────────────────────────────────┐                       │
│  │ Preprocessor Module 2: Translator        │                       │
│  │ Translates: FR → EN                      │                       │
│  │ Output: "Hello! What did we discuss      │                       │
│  │         about FastAPI?"                  │                       │
│  └─────────────┬───────────────────────────┘                       │
│                ↓                                                     │
│  ┌─────────────────────────────────────────┐                       │
│  │ Preprocessor Module 3: Content Filter    │                       │
│  │ Checks: Safe content ✓                   │                       │
│  │ Passes through unchanged                 │                       │
│  └─────────────────────────────────────────┘                       │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: CONTEXT RETRIEVAL                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Preprocessed Input: "Hello! What did we discuss about FastAPI?"   │
│         │                                                            │
│         ↓                                                            │
│  ┌─────────────────────────────────────────┐                       │
│  │ Memory System                            │                       │
│  │                                          │                       │
│  │ Short-term (recent conversation):       │                       │
│  │ [5 turns ago]                            │                       │
│  │ User: "I want to build an API"           │                       │
│  │ Assistant: "Great! Consider FastAPI..."  │                       │
│  │                                          │                       │
│  │ [3 turns ago]                            │                       │
│  │ User: "Tell me about FastAPI features"   │                       │
│  │ Assistant: "FastAPI has async support..."│                       │
│  │                                          │                       │
│  │ Long-term (facts):                       │                       │
│  │ - User prefers Python                    │                       │
│  │ - Working on API project                 │                       │
│  │ - Discussed FastAPI before               │                       │
│  └─────────────┬───────────────────────────┘                       │
│                │                                                     │
│                ↓                                                     │
│  ┌─────────────────────────────────────────┐                       │
│  │ Datastore System                         │                       │
│  │                                          │                       │
│  │ Query: "FastAPI discussion"              │                       │
│  │                                          │                       │
│  │ Vector search results:                   │                       │
│  │ 1. [Doc: FastAPI Features]               │                       │
│  │    "FastAPI is a modern framework..."    │                       │
│  │    Similarity: 0.92                      │                       │
│  │                                          │                       │
│  │ 2. [Previous conversation snippet]       │                       │
│  │    "FastAPI supports automatic docs..."  │                       │
│  │    Similarity: 0.87                      │                       │
│  │                                          │                       │
│  │ 3. [Code example]                        │                       │
│  │    "from fastapi import FastAPI..."      │                       │
│  │    Similarity: 0.81                      │                       │
│  └─────────────────────────────────────────┘                       │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: CONTEXT ASSEMBLY                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │ Build Complete Context for LLM                    │             │
│  │                                                    │             │
│  │ System Prompt:                                    │             │
│  │ "You are a helpful AI assistant."                │             │
│  │                                                    │             │
│  │ Memory Context:                                   │             │
│  │ ---                                                │             │
│  │ User Information:                                 │             │
│  │ - Name: [from long-term memory]                   │             │
│  │ - Preferences: Python, FastAPI                    │             │
│  │                                                    │             │
│  │ Recent Conversation:                              │             │
│  │ [5 turns ago] Discussed building an API          │             │
│  │ [3 turns ago] Talked about FastAPI features      │             │
│  │ ---                                                │             │
│  │                                                    │             │
│  │ Datastore Context:                                │             │
│  │ ---                                                │             │
│  │ [Relevant Documentation]                          │             │
│  │ FastAPI is a modern framework for building APIs  │             │
│  │ with Python. Key features include...             │             │
│  │                                                    │             │
│  │ [Previous Discussion]                             │             │
│  │ FastAPI supports automatic API documentation...  │             │
│  │ ---                                                │             │
│  │                                                    │             │
│  │ Tools Available:                                  │             │
│  │ - file_access: Read/write files                  │             │
│  │ - command_exec: Execute commands                 │             │
│  │ - search_internet: Search the web                │             │
│  │                                                    │             │
│  │ User Message (translated):                        │             │
│  │ "Hello! What did we discuss about FastAPI?"      │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: LLM PROCESSING                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │ LLM Analysis                                      │             │
│  │                                                    │             │
│  │ Context understanding:                            │             │
│  │ ✓ User asked about previous FastAPI discussion   │             │
│  │ ✓ Memory shows we discussed FastAPI features     │             │
│  │ ✓ Datastore has relevant documentation           │             │
│  │ ✓ User prefers Python/FastAPI                    │             │
│  │                                                    │             │
│  │ Decision: No tools needed                         │             │
│  │ Can answer from memory + datastore context       │             │
│  └─────────────┬─────────────────────────────────────┘             │
│                ↓                                                     │
│  ┌───────────────────────────────────────────────────┐             │
│  │ Generate Response (English)                       │             │
│  │                                                    │             │
│  │ "Based on our previous conversations, we         │             │
│  │ discussed several FastAPI features:               │             │
│  │                                                    │             │
│  │ 1. **Async Support**: FastAPI has built-in       │             │
│  │    async/await support for high performance      │             │
│  │                                                    │             │
│  │ 2. **Automatic Documentation**: It generates     │             │
│  │    interactive API docs automatically            │             │
│  │                                                    │             │
│  │ 3. **Type Safety**: Uses Python type hints for   │             │
│  │    validation and documentation                  │             │
│  │                                                    │             │
│  │ We also talked about it being a modern           │             │
│  │ framework for building APIs with Python, which   │             │
│  │ aligns with your preference for Python."         │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 6: OUTPUT POSTPROCESSING                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LLM Response (English)                                             │
│         │                                                            │
│         ↓                                                            │
│  ┌─────────────────────────────────────────┐                       │
│  │ Postprocessor Module 1: Markdown Format │                       │
│  │ - Detects numbered list                  │                       │
│  │ - Enhances markdown formatting           │                       │
│  │ - Adds code block formatting             │                       │
│  └─────────────┬───────────────────────────┘                       │
│                ↓                                                     │
│  ┌─────────────────────────────────────────┐                       │
│  │ Postprocessor Module 2: Content Filter   │                       │
│  │ - Checks for inappropriate content: PASS │                       │
│  │ - Validates response quality: PASS       │                       │
│  └─────────────┬───────────────────────────┘                       │
│                ↓                                                     │
│  ┌─────────────────────────────────────────┐                       │
│  │ Postprocessor Module 3: Translator Back  │                       │
│  │ - Checks metadata: original_lang = "fr"  │                       │
│  │ - Translates: EN → FR                    │                       │
│  │                                          │                       │
│  │ Output (French):                         │                       │
│  │ "D'après nos conversations précédentes,  │                       │
│  │ nous avons discuté de plusieurs          │                       │
│  │ fonctionnalités de FastAPI:              │                       │
│  │                                          │                       │
│  │ 1. **Support Async**: FastAPI a un       │                       │
│  │    support intégré pour async/await..."  │                       │
│  └─────────────────────────────────────────┘                       │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 7: MEMORY UPDATE                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │ Update Short-term Memory                          │             │
│  │                                                    │             │
│  │ Add new turn:                                     │             │
│  │ {                                                  │             │
│  │   "turn": 11,                                     │             │
│  │   "user": "What did we discuss about FastAPI?",   │             │
│  │   "assistant": "Based on our previous...",        │             │
│  │   "timestamp": "2025-01-06T10:30:00Z",           │             │
│  │   "language": "fr"                                │             │
│  │ }                                                  │             │
│  │                                                    │             │
│  │ Prune if needed (keep last 10 turns)             │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │ Update Long-term Memory                           │             │
│  │                                                    │             │
│  │ No new facts to extract (was a query)            │             │
│  │ Update access stats for existing facts           │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                      │
│  ┌───────────────────────────────────────────────────┐             │
│  │ Update Datastore (Optional)                       │             │
│  │                                                    │             │
│  │ Optionally store this Q&A for future reference:  │             │
│  │ {                                                  │             │
│  │   "question": "What did we discuss about FastAPI?"│             │
│  │   "answer": "Based on our previous...",           │             │
│  │   "context": ["async", "documentation", "types"], │             │
│  │   "timestamp": "2025-01-06T10:30:00Z"            │             │
│  │ }                                                  │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL RESPONSE TO USER                           │
│                         (in French)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Flow

### Complete Processing Steps

```
Step 1: STARTUP
├─ Load Memory (conversation history + facts)
├─ Connect to Datastore (vector database)
├─ Initialize Modules (preprocessor & postprocessor chains)
└─ Register Tools (build definitions, configure security)

Step 2: USER INPUT
├─ Receive: "Bonjour! What did we discuss about FastAPI?"
└─ Start pipeline

Step 3: PREPROCESSING
├─ Module 1: Detect language → French
├─ Module 2: Translate FR→EN → "Hello! What did we discuss about FastAPI?"
└─ Module 3: Content filter → PASS

Step 4: MEMORY RETRIEVAL
├─ Search short-term: Find FastAPI discussions (3, 5 turns ago)
├─ Search long-term: User preferences (Python, FastAPI)
└─ Context: User has discussed FastAPI before

Step 5: DATASTORE QUERY
├─ Generate embedding for "FastAPI discussion"
├─ Vector search: Find top 3 relevant documents
│  ├─ FastAPI documentation (similarity: 0.92)
│  ├─ Previous conversation (similarity: 0.87)
│  └─ Code examples (similarity: 0.81)
└─ Return context snippets

Step 6: CONTEXT ASSEMBLY
├─ Combine system prompt
├─ Add memory context (recent conversation + facts)
├─ Add datastore results (documentation + examples)
├─ Add available tools list
└─ Add user message (translated)

Step 7: LLM PROCESSING
├─ Analyze complete context
├─ Understand: Query about previous discussion
├─ Decide: No tools needed (can answer from context)
├─ Generate response using memory + datastore information
└─ Output: Detailed answer in English

Step 8: POSTPROCESSING
├─ Module 1: Format markdown (enhance lists, code blocks)
├─ Module 2: Content filter (check safety) → PASS
└─ Module 3: Translate EN→FR (back to user's language)

Step 9: MEMORY UPDATE
├─ Add turn to short-term memory
├─ Update long-term facts (if any new information)
├─ Update statistics (turn count, retrieval count)
└─ Optionally store in datastore for future queries

Step 10: DELIVER RESPONSE
└─ Return formatted, translated response to user
```

## Complete Example

Let's walk through a complex real-world scenario with all components active.

### Scenario Setup

**Enabled Components**:
- Memory: Tracking conversation and user preferences
- Datastore: Indexed documentation and code examples
- Modules: Language translation + content filtering + markdown formatting
- Tools: file_access (rw), command_exec, search_internet

**User Context** (from previous sessions):
- Name: Alice
- Preferred language: French
- Working on: Python web application project
- Discussed: FastAPI, PostgreSQL, Docker

### Example Interaction

#### Turn 1: Complex Query with Tool Use

**User Input (French)**:
```
"Recherche des tutoriels FastAPI récents et sauvegarde les meilleurs dans un fichier"
```
(Translation: "Search for recent FastAPI tutorials and save the best ones in a file")

**Complete Processing**:

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: "Recherche des tutoriels FastAPI récents..."         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ PREPROCESSING                                                │
├─────────────────────────────────────────────────────────────┤
│ Module: Language Detector                                   │
│ → Detected: French                                          │
│ → Store: metadata.original_lang = "fr"                      │
│                                                              │
│ Module: Translator                                          │
│ → Translate: FR → EN                                        │
│ → Output: "Search for recent FastAPI tutorials and save    │
│            the best ones in a file"                         │
│                                                              │
│ Module: Content Filter                                      │
│ → Check: Safe ✓                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ CONTEXT RETRIEVAL                                            │
├─────────────────────────────────────────────────────────────┤
│ Memory System                                                │
│ ├─ Short-term:                                              │
│ │  └─ [Previous turns about FastAPI project]               │
│ ├─ Long-term:                                               │
│ │  ├─ User: Alice                                           │
│ │  ├─ Language: French                                      │
│ │  ├─ Project: Python web app with FastAPI                 │
│ │  └─ Interests: FastAPI, tutorials, learning              │
│ └─ Context: User learning FastAPI for project              │
│                                                              │
│ Datastore System                                            │
│ ├─ Query: "FastAPI tutorials"                              │
│ ├─ Results:                                                 │
│ │  ├─ [Doc] "FastAPI Official Tutorial" (score: 0.94)     │
│ │  ├─ [Note] "Best FastAPI resources" (score: 0.88)       │
│ │  └─ [Code] FastAPI examples (score: 0.82)               │
│ └─ Context: Has existing knowledge about FastAPI           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM PROCESSING                                               │
├─────────────────────────────────────────────────────────────┤
│ Context Understanding:                                       │
│ ├─ Task 1: Search internet for FastAPI tutorials           │
│ ├─ Task 2: Select/filter best ones                         │
│ ├─ Task 3: Save to file                                    │
│ └─ Tools needed: search_internet, file_access              │
│                                                              │
│ TOOL CALL 1: search_internet                               │
│ ├─ Function: "search_internet"                             │
│ ├─ Arguments: {                                             │
│ │    "query": "FastAPI tutorials 2025",                    │
│ │    "max_results": 5                                      │
│ │  }                                                        │
│ └─ Execute...                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL EXECUTION 1: search_internet                           │
├─────────────────────────────────────────────────────────────┤
│ Security Checks:                                             │
│ ├─ Tool enabled: ✓                                          │
│ ├─ No whitelist needed for internet search: ✓              │
│ └─ No approval required: ✓                                  │
│                                                              │
│ Execute:                                                     │
│ └─ Search DuckDuckGo for "FastAPI tutorials 2025"          │
│                                                              │
│ Results:                                                     │
│ {                                                            │
│   "success": true,                                          │
│   "results": [                                              │
│     {                                                        │
│       "title": "Complete FastAPI Tutorial 2025",           │
│       "url": "https://example.com/tutorial1",              │
│       "snippet": "Learn FastAPI from scratch..."           │
│     },                                                       │
│     {                                                        │
│       "title": "FastAPI Best Practices 2025",              │
│       "url": "https://example.com/tutorial2",              │
│       "snippet": "Production-ready FastAPI..."             │
│     },                                                       │
│     ... 3 more results                                      │
│   ]                                                          │
│ }                                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM PROCESSING (continued)                                   │
├─────────────────────────────────────────────────────────────┤
│ Received search results (5 tutorials)                       │
│                                                              │
│ Analysis:                                                    │
│ ├─ All 5 results look relevant                             │
│ ├─ Filter/rank by quality (based on titles/snippets)       │
│ ├─ Select top 3 best tutorials                             │
│ └─ Format for file output                                   │
│                                                              │
│ Generate file content:                                      │
│ """                                                          │
│ # FastAPI Tutorials - Best Resources                       │
│                                                              │
│ ## 1. Complete FastAPI Tutorial 2025                       │
│ Learn FastAPI from scratch...                               │
│ URL: https://example.com/tutorial1                         │
│                                                              │
│ ## 2. FastAPI Best Practices 2025                          │
│ Production-ready FastAPI...                                 │
│ URL: https://example.com/tutorial2                         │
│                                                              │
│ ## 3. FastAPI Advanced Patterns                            │
│ Advanced techniques...                                      │
│ URL: https://example.com/tutorial3                         │
│ """                                                          │
│                                                              │
│ TOOL CALL 2: file_access                                   │
│ ├─ Function: "file_access"                                 │
│ ├─ Arguments: {                                             │
│ │    "operation": "write",                                 │
│ │    "path": "fastapi_tutorials.md",                       │
│ │    "content": "[formatted content above]"                │
│ │  }                                                        │
│ └─ Execute...                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL EXECUTION 2: file_access                               │
├─────────────────────────────────────────────────────────────┤
│ Security Checks:                                             │
│ ├─ Tool enabled: ✓                                          │
│ ├─ Whitelist check:                                         │
│ │  ├─ Path: "fastapi_tutorials.md"                         │
│ │  ├─ Whitelist: ["**/*.md", "**/*.txt", "**/*.json"]     │
│ │  └─ Match: ✓ (matches **/*.md)                          │
│ ├─ Dangerous path check:                                    │
│ │  ├─ Not in /etc/, /sys/, ~/.ssh/                         │
│ │  └─ Safe: ✓                                              │
│ ├─ Mode check:                                              │
│ │  ├─ Operation: write                                     │
│ │  ├─ Mode: rw (read-write)                                │
│ │  └─ Allowed: ✓                                           │
│ └─ Approval required: false (not dangerous) ✓              │
│                                                              │
│ Execute:                                                     │
│ └─ Write content to fastapi_tutorials.md                   │
│                                                              │
│ Result:                                                      │
│ {                                                            │
│   "success": true,                                          │
│   "path": "fastapi_tutorials.md",                          │
│   "bytes_written": 1024,                                    │
│   "operation": "write"                                      │
│ }                                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ LLM PROCESSING (final)                                       │
├─────────────────────────────────────────────────────────────┤
│ Both tools executed successfully:                           │
│ ├─ ✓ Searched internet (found 5 tutorials)                 │
│ ├─ ✓ Selected best 3                                       │
│ └─ ✓ Saved to fastapi_tutorials.md                         │
│                                                              │
│ Generate response (English):                                │
│ "I've searched for recent FastAPI tutorials and saved      │
│ the top 3 best ones to fastapi_tutorials.md:               │
│                                                              │
│ 1. Complete FastAPI Tutorial 2025 - Comprehensive guide   │
│ 2. FastAPI Best Practices 2025 - Production tips          │
│ 3. FastAPI Advanced Patterns - Advanced techniques        │
│                                                              │
│ The file is 1KB and ready for you to review!"              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ POSTPROCESSING                                               │
├─────────────────────────────────────────────────────────────┤
│ Module: Markdown Formatter                                  │
│ → Enhance formatting (already good markdown)                │
│                                                              │
│ Module: Content Filter                                      │
│ → Check safety: ✓ PASS                                      │
│                                                              │
│ Module: Translator Back                                     │
│ → Check: original_lang = "fr"                               │
│ → Translate: EN → FR                                        │
│ → Output (French):                                          │
│   "J'ai recherché des tutoriels FastAPI récents et         │
│   sauvegardé les 3 meilleurs dans fastapi_tutorials.md:    │
│                                                              │
│   1. Tutoriel Complet FastAPI 2025 - Guide complet        │
│   2. Meilleures Pratiques FastAPI 2025 - Conseils prod    │
│   3. Patterns Avancés FastAPI - Techniques avancées        │
│                                                              │
│   Le fichier fait 1Ko et est prêt à consulter!"            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ MEMORY & DATASTORE UPDATE                                    │
├─────────────────────────────────────────────────────────────┤
│ Memory Update:                                               │
│ ├─ Add turn to short-term:                                  │
│ │  {                                                         │
│ │    "user": "Search FastAPI tutorials and save...",        │
│ │    "assistant": "I've searched...",                       │
│ │    "tools_used": ["search_internet", "file_access"],     │
│ │    "files_created": ["fastapi_tutorials.md"]             │
│ │  }                                                         │
│ ├─ Update long-term facts:                                  │
│ │  └─ Add: "Saved FastAPI tutorials to file"               │
│ └─ Update statistics                                        │
│                                                              │
│ Datastore Update:                                           │
│ ├─ Store conversation for future reference                  │
│ ├─ Index file content for search:                          │
│ │  └─ fastapi_tutorials.md content → vector embedding      │
│ └─ Link to user's project context                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ FINAL OUTPUT TO USER (French)                               │
│ "J'ai recherché des tutoriels FastAPI récents et           │
│ sauvegardé les 3 meilleurs dans fastapi_tutorials.md..."   │
└─────────────────────────────────────────────────────────────┘
```

#### Turn 2: Follow-up with Context

**User Input (French)**:
```
"Montre-moi le premier tutoriel"
```
(Translation: "Show me the first tutorial")

**Complete Processing**:

```
INPUT → PREPROCESS (translate) → MEMORY (recall file) →
DATASTORE (find tutorial details) → LLM (decide to read file) →
TOOL (file_access: read) → LLM (format response) →
POSTPROCESS (translate back) → UPDATE MEMORY → OUTPUT
```

**Detailed Flow**:

```
1. Preprocessing:
   - Translate: "Show me the first tutorial" (EN)

2. Memory Retrieval:
   - Short-term: Previous turn saved FastAPI tutorials to file
   - Context: "first tutorial" refers to fastapi_tutorials.md
   - File: fastapi_tutorials.md was just created

3. Datastore Query:
   - Query: "first tutorial FastAPI"
   - Result: Find reference to "Complete FastAPI Tutorial 2025"

4. LLM Processing:
   - Understands: User wants content from first tutorial in file
   - Decision: Need to read fastapi_tutorials.md
   - Tool call: file_access(operation="read", path="fastapi_tutorials.md")

5. Tool Execution:
   - Security: ✓ (file whitelisted, read operation in ro/rw mode)
   - Execute: Read file
   - Return: File content

6. LLM Processing (continued):
   - Extract first tutorial section
   - Format response

7. Postprocessing:
   - Format markdown
   - Filter content: ✓
   - Translate to French

8. Memory Update:
   - Add turn: "User viewed first tutorial"
   - Update: User engaged with saved content

9. Output:
   "Voici le premier tutoriel:

   ## 1. Tutoriel Complet FastAPI 2025
   Learn FastAPI from scratch...
   URL: https://example.com/tutorial1"
```

## Component Interactions

### How Components Work Together

```
┌─────────────┐
│   MEMORY    │──────┐
└─────┬───────┘      │
      │              │ Provides context
      │ Stores facts │ for better queries
      ↓              ↓
┌─────────────┐  ┌──────────────┐
│  DATASTORE  │  │   MODULES    │
└─────┬───────┘  └──────┬───────┘
      │                 │
      │ Semantic search │ Transforms
      │ results         │ input/output
      ↓                 ↓
┌──────────────────────────────┐
│           LLM                │
│   (with tool definitions)    │
└──────────────┬───────────────┘
               │
               │ Decides to use tools
               ↓
       ┌───────────────┐
       │     TOOLS     │
       │  (execute)    │
       └───────┬───────┘
               │
               │ Results feed back
               ↓
       Update Memory & Datastore
```

### Interaction Patterns

#### Pattern 1: Memory → Datastore
```
User: "What did we discuss about databases?"

Memory → Recalls: "Discussed PostgreSQL 3 days ago"
      ↓
Datastore → Query: "PostgreSQL discussion"
         → Returns: Detailed notes from that conversation
      ↓
LLM → Combines both sources for comprehensive answer
```

#### Pattern 2: Module → Tool
```
User: (French) "Crée un fichier avec le code"

Module → Translate: "Create a file with the code"
      ↓
LLM → Decides: Need file_access tool
   ↓
Tool → Execute: Create file
    ↓
Module → Translate response back to French
```

#### Pattern 3: Tool → Datastore
```
User: "Search for Python tutorials and remember them"

Tool → search_internet: Get tutorials
    ↓
LLM → Process results
   ↓
Datastore → Store: Index tutorials for future reference
         ↓
Memory → Update: "User interested in Python tutorials"
```

#### Pattern 4: All Components Together
```
User: (French) "Based on what we discussed, find examples and save to project"

Module (Preprocessor) → Translate to English
                     ↓
Memory → Recall: "We discussed FastAPI async patterns"
      ↓
Datastore → Query: "FastAPI async examples"
         ↓
LLM → Understand full context
   → Decide: search_internet + file_access tools needed
   ↓
Tool 1 → Search internet for examples
      ↓
Tool 2 → Save to file
      ↓
Module (Postprocessor) → Format markdown
                      → Translate back to French
                      ↓
Memory → Update: "Saved FastAPI examples to project"
      ↓
Datastore → Index: New file content for future search
```

## Summary

When all components are enabled together:

1. **Modules** transform input/output (translate, format, filter)
2. **Memory** provides conversation context and user preferences
3. **Datastore** supplies semantic search over knowledge/documents
4. **Tools** execute actions based on LLM decisions
5. **LLM** orchestrates everything, deciding what to use when

### Key Benefits of Full Integration

- **Context-Aware**: Memory + Datastore provide rich context
- **Multilingual**: Modules handle translation seamlessly
- **Action-Capable**: Tools execute real operations
- **Learning**: System improves by storing interactions
- **Safe**: Multiple security layers protect the system
- **Flexible**: Components can be enabled/disabled independently

### Processing Time Breakdown

For a typical request with all components:

```
Component          Time    Percentage
─────────────────────────────────────
Preprocessing      100ms   5%
Memory Retrieval   200ms   10%
Datastore Query    300ms   15%
LLM Processing     1000ms  50%
Tool Execution     300ms   15%
Postprocessing     100ms   5%
─────────────────────────────────────
TOTAL             ~2000ms  100%
```

The LLM processing is typically the bottleneck, while other components add minimal overhead for significant functionality gains.

---

**Last Updated**: 2025-01-06

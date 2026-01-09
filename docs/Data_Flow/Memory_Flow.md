# Memory Logic Flow

This document explains the complete logic flow when memory is enabled in the Local LLM Framework (LLF), including detailed examples and internal processing.

## Table of Contents

1. [What is Memory?](#what-is-memory)
2. [Memory vs Datastore](#memory-vs-datastore)
3. [High-Level Flow](#high-level-flow)
4. [Detailed Logic Flow](#detailed-logic-flow)
5. [Examples](#examples)
6. [Internal Processing](#internal-processing)

## What is Memory?

**Memory** in LLF is a structured system for storing and retrieving conversation context, facts, and learned information. Unlike datastores (which are general-purpose storage), memory is specifically designed for conversational AI.

**Key Features**:
- Short-term memory (recent conversation)
- Long-term memory (facts, preferences, context)
- Automatic memory management
- Semantic recall
- Memory prioritization

**Memory Types**:
1. **Short-term**: Recent conversation turns (sliding window)
2. **Long-term**: Persistent facts and context
3. **Working**: Currently active information
4. **Episodic**: Specific conversation episodes

## Memory vs Datastore

| Feature | Memory | Datastore |
|---------|--------|-----------|
| **Purpose** | Conversation context | General data storage |
| **Structure** | Conversation-optimized | Flexible schema |
| **Lifecycle** | Managed automatically | Manual control |
| **Retrieval** | Context-aware | Query-based |
| **Updates** | Automatic on each turn | Explicit operations |
| **Size** | Limited by relevance | Unlimited |

## High-Level Flow

```
┌──────────────┐
│ User Message │
└──────┬───────┘
       │
       ↓
┌────────────────────────────────────────────────────────┐
│ 1. Memory System Initialization                       │
│    - Load short-term memory (recent turns)            │
│    - Load long-term memory (facts/context)            │
│    - Initialize working memory                        │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 2. Memory Retrieval                                    │
│    - Extract relevant memories based on query         │
│    - Rank by recency and relevance                    │
│    - Apply memory limits                              │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 3. Context Construction                                │
│    - Build conversation history from short-term       │
│    - Add relevant long-term memories                  │
│    - Format for LLM consumption                       │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 4. LLM Processing                                      │
│    - Process message with memory context              │
│    - Generate response                                │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 5. Memory Update                                       │
│    - Add new turn to short-term memory                │
│    - Extract new facts for long-term memory           │
│    - Update memory statistics                         │
│    - Prune old memories if needed                     │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌──────────────────┐
│ Response to User │
└──────────────────┘
```

## Detailed Logic Flow

### Phase 1: Memory Initialization

```
┌─────────────────────────────────────────────────────────────┐
│ LLMClient.__init__()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ MemoryManager()        │
        │ - Load config          │
        │ - Initialize stores    │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Load Short-term Memory         │
        │                                │
        │ Recent conversation turns:     │
        │ [                              │
        │   {                            │
        │     "role": "user",            │
        │     "content": "Hello",        │
        │     "timestamp": "10:00:00",   │
        │     "turn": 1                  │
        │   },                           │
        │   {                            │
        │     "role": "assistant",       │
        │     "content": "Hi! How...",   │
        │     "timestamp": "10:00:01",   │
        │     "turn": 1                  │
        │   }                            │
        │ ]                              │
        │                                │
        │ Limit: 10 most recent turns    │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Load Long-term Memory          │
        │                                │
        │ Persistent facts:              │
        │ {                              │
        │   "user_name": "Alice",        │
        │   "user_preferences": {        │
        │     "language": "Python",      │
        │     "framework": "FastAPI"     │
        │   },                           │
        │   "project_context": {         │
        │     "name": "web_app",         │
        │     "status": "development"    │
        │   }                            │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Initialize Working Memory      │
        │                                │
        │ Currently active:              │
        │ - Current topic: None          │
        │ - Active entities: []          │
        │ - Context window: []           │
        └────────────────────────────────┘
```

### Phase 2: Memory Retrieval

```
┌─────────────────────────────────────────────────────────────┐
│ User Message: "What was my project name again?"             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Analyze Query                  │
        │                                │
        │ Intent: Recall information     │
        │ Keywords: ["project", "name"]  │
        │ Type: Fact retrieval           │
        │ Tense: Past (memory query)     │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Search Short-term Memory       │
        │                                │
        │ Query: "project name"          │
        │ Recent turns: 10               │
        │                                │
        │ Matches: [                     │
        │   {                            │
        │     "turn": 5,                 │
        │     "content": "working on     │
        │                 web_app...",   │
        │     "relevance": 0.75          │
        │   }                            │
        │ ]                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Search Long-term Memory        │
        │                                │
        │ Query: "project name"          │
        │                                │
        │ Matches: {                     │
        │   "project_context": {         │
        │     "name": "web_app",         │
        │     "relevance": 0.95          │
        │   }                            │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Rank and Combine               │
        │                                │
        │ Results sorted by:             │
        │ 1. Relevance score (0.95)      │
        │ 2. Recency (timestamp)         │
        │ 3. Importance (metadata)       │
        │                                │
        │ Top result:                    │
        │ project_context.name = "web_app│
        └────────────────────────────────┘
```

### Phase 3: Context Construction

```
┌─────────────────────────────────────────────────────────────┐
│ Build Context for LLM                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌──────────────────────────────────────┐
        │ Short-term Memory (Conversation)     │
        │                                      │
        │ [3 turns ago]                        │
        │ User: "I'm starting a new project"   │
        │ Assistant: "Great! What kind?"       │
        │                                      │
        │ [2 turns ago]                        │
        │ User: "A web application called      │
        │        web_app"                      │
        │ Assistant: "Excellent choice! What   │
        │            stack?"                   │
        │                                      │
        │ [1 turn ago]                         │
        │ User: "Python with FastAPI"          │
        │ Assistant: "Perfect! FastAPI is..."  │
        └────────┬─────────────────────────────┘
                 │
                 ↓
        ┌──────────────────────────────────────┐
        │ Long-term Memory (Facts)             │
        │                                      │
        │ User Information:                    │
        │ - Name: Alice                        │
        │ - Preferred language: Python         │
        │ - Preferred framework: FastAPI       │
        │                                      │
        │ Project Information:                 │
        │ - Name: web_app                      │
        │ - Status: development                │
        │ - Stack: Python, FastAPI             │
        └────────┬─────────────────────────────┘
                 │
                 ↓
        ┌──────────────────────────────────────┐
        │ Assemble Final Context               │
        │                                      │
        │ System: You are assisting Alice with │
        │ their web development project.       │
        │                                      │
        │ Project Context:                     │
        │ - Project name: web_app              │
        │ - Stack: Python, FastAPI             │
        │ - Status: development                │
        │                                      │
        │ Recent conversation:                 │
        │ [... conversation history ...]       │
        │                                      │
        │ User: What was my project name again?│
        └──────────────────────────────────────┘
```

### Phase 4: LLM Processing

```
┌─────────────────────────────────────────────────────────────┐
│ LLM receives context and processes                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │ LLM Analysis                       │
        │                                    │
        │ Input understanding:               │
        │ ✓ User asking for project name     │
        │ ✓ Information in long-term memory  │
        │ ✓ Also mentioned in conversation   │
        │                                    │
        │ Confidence: HIGH                   │
        │ Answer: "web_app"                  │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Generate Response                  │
        │                                    │
        │ "Your project is called web_app!"  │
        └────────────────────────────────────┘
```

### Phase 5: Memory Update

```
┌─────────────────────────────────────────────────────────────┐
│ After Response Generation                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │ Update Short-term Memory           │
        │                                    │
        │ Add new turn:                      │
        │ {                                  │
        │   "turn": 11,                      │
        │   "user": "What was my project     │
        │            name again?",           │
        │   "assistant": "Your project is    │
        │                 called web_app!",  │
        │   "timestamp": "10:15:30"          │
        │ }                                  │
        │                                    │
        │ If > 10 turns: Remove oldest       │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Extract New Facts                  │
        │                                    │
        │ Analyze conversation for:          │
        │ - New user preferences             │
        │ - New facts to remember            │
        │ - Updates to existing facts        │
        │                                    │
        │ This turn: No new facts            │
        │ (query, not statement)             │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Update Statistics                  │
        │                                    │
        │ memory_stats = {                   │
        │   "total_turns": 11,               │
        │   "facts_stored": 5,               │
        │   "last_query": "10:15:30",        │
        │   "memory_hits": 147               │
        │ }                                  │
        └────────┬───────────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────────┐
        │ Memory Maintenance                 │
        │                                    │
        │ Tasks:                             │
        │ ✓ Prune very old short-term        │
        │ ✓ Consolidate similar facts        │
        │ ✓ Update relevance scores          │
        │ ✓ Persist to disk                  │
        └────────────────────────────────────┘
```

## Examples

### Example 1: Basic Conversation Memory

**Conversation**:

```python
# Turn 1
User: "Hi, I'm Bob"
Assistant: "Hello Bob! Nice to meet you."

# Memory Update:
short_term.append({
    "turn": 1,
    "user": "Hi, I'm Bob",
    "assistant": "Hello Bob! Nice to meet you."
})
long_term["user_name"] = "Bob"

# Turn 2
User: "I like working with TypeScript"
Assistant: "Great! TypeScript adds type safety to JavaScript."

# Memory Update:
short_term.append({
    "turn": 2,
    "user": "I like working with TypeScript",
    "assistant": "Great! TypeScript adds..."
})
long_term["preferences"] = {"language": "TypeScript"}

# Turn 3
User: "What's my name?"
Assistant: "Your name is Bob!"

# Memory Retrieval:
# 1. Search long_term: user_name = "Bob"
# 2. Search short_term: Turn 1 mentions "Bob"
# 3. High confidence answer
```

**Memory State After Turn 3**:

```python
{
    "short_term": [
        {"turn": 1, "user": "Hi, I'm Bob", ...},
        {"turn": 2, "user": "I like working with TypeScript", ...},
        {"turn": 3, "user": "What's my name?", ...}
    ],
    "long_term": {
        "user_name": "Bob",
        "preferences": {
            "language": "TypeScript"
        }
    }
}
```

### Example 2: Context-Aware Memory

**Scenario**: Multi-topic conversation with context switching.

```python
# Topic 1: Project Setup
User: "I'm building an e-commerce site"
Assistant: "Exciting! What platform are you using?"

# Memory:
working_memory["current_topic"] = "e-commerce project"
working_memory["entities"] = ["e-commerce site"]

User: "I'll use Next.js and Stripe"
Assistant: "Great combination! Next.js for frontend, Stripe for payments."

# Memory Update:
long_term["projects"]["ecommerce"] = {
    "framework": "Next.js",
    "payment": "Stripe"
}

# Topic 2: Unrelated question
User: "What's the weather like?"
Assistant: "I don't have access to weather information."

# Memory: Topic switch detected, save context
working_memory["previous_topic"] = "e-commerce project"
working_memory["current_topic"] = "weather"

# Topic 3: Return to project
User: "Back to my project - what payment system was I using?"
Assistant: "You're using Stripe for payment processing in your Next.js e-commerce site."

# Memory Retrieval:
# 1. Detect "my project" reference
# 2. Load previous_topic context
# 3. Retrieve: projects["ecommerce"]["payment"] = "Stripe"
# 4. Also recall: projects["ecommerce"]["framework"] = "Next.js"
```

**Flow Diagram**:

```
Topic 1 (e-commerce)
    ↓
[Store context]
    ↓
Topic 2 (weather)
    ↓
[Save Topic 1 context]
[Load Topic 2]
    ↓
Back to Topic 1
    ↓
[Retrieve saved Topic 1 context]
[Resume with full context]
```

### Example 3: Fact Extraction and Storage

**Conversation**:

```python
User: "I work at TechCorp as a senior developer. I've been there for 3 years."
```

**Memory Processing**:

```python
# 1. Extract Facts
extracted_facts = {
    "company": "TechCorp",
    "position": "senior developer",
    "tenure": "3 years",
    "employment_status": "currently employed"
}

# 2. Categorize
categories = {
    "professional": {
        "company": "TechCorp",
        "position": "senior developer",
        "tenure": "3 years"
    }
}

# 3. Store in Long-term Memory
long_term["professional_info"] = {
    "current_employer": "TechCorp",
    "current_position": "senior developer",
    "current_tenure": "3 years",
    "stored_at": "2025-01-06T10:30:00Z"
}

# 4. Add to Short-term
short_term.append({
    "turn": 15,
    "content": "I work at TechCorp...",
    "entities": ["TechCorp", "senior developer"],
    "fact_extraction": True
})
```

**Later Retrieval**:

```python
User: "Where do I work?"

# Memory Search:
relevant_memories = memory.search("work employer")

# Results:
{
    "long_term_match": {
        "field": "professional_info.current_employer",
        "value": "TechCorp",
        "confidence": 0.98
    },
    "short_term_match": {
        "turn": 15,
        "excerpt": "...work at TechCorp...",
        "confidence": 0.85
    }
}

# Response:
"You work at TechCorp as a senior developer."
```

### Example 4: Memory-Based Personalization

**Initial Setup**:

```python
User: "I prefer concise explanations with code examples"

# Memory:
long_term["communication_preferences"] = {
    "style": "concise",
    "include_code": True,
    "format": "examples"
}
```

**Later Usage**:

```python
User: "How do I sort a list in Python?"

# Memory Retrieved:
preferences = long_term["communication_preferences"]
# style: concise, include_code: True

# Response (tailored):
"""
Use sorted() or .sort():

# sorted() - returns new list
sorted_list = sorted([3, 1, 2])  # [1, 2, 3]

# .sort() - modifies in place
my_list = [3, 1, 2]
my_list.sort()  # my_list is now [1, 2, 3]
"""

# Without memory, response might be verbose with
# full explanations, edge cases, etc.
```

## Internal Processing

### Memory Storage Structure

```python
{
    "conversation_id": "conv_abc123",

    "short_term": {
        "max_turns": 10,
        "turns": [
            {
                "turn_id": 1,
                "timestamp": "2025-01-06T10:00:00Z",
                "user_message": "Hello",
                "assistant_message": "Hi there!",
                "entities": [],
                "topics": ["greeting"]
            },
            # ... more turns
        ]
    },

    "long_term": {
        "facts": {
            "user_name": {
                "value": "Alice",
                "confidence": 1.0,
                "source": "turn_1",
                "last_updated": "2025-01-06T10:00:00Z"
            },
            "user_preferences": {
                "language": {
                    "value": "Python",
                    "confidence": 0.95,
                    "source": "turn_5"
                }
            }
        },

        "entities": {
            "people": ["Alice", "Bob"],
            "projects": ["web_app"],
            "technologies": ["Python", "FastAPI"]
        },

        "context": {
            "current_project": "web_app",
            "project_status": "development",
            "last_topic": "database design"
        }
    },

    "working": {
        "current_topic": "authentication",
        "active_entities": ["FastAPI", "JWT"],
        "context_window": [8, 9, 10],  # Active turn IDs
        "pending_questions": []
    },

    "statistics": {
        "total_turns": 10,
        "facts_count": 12,
        "memory_retrievals": 47,
        "last_update": "2025-01-06T10:30:00Z"
    }
}
```

### Memory Search Algorithm

```python
def search_memory(query: str, memory_state: dict) -> list:
    """Search both short-term and long-term memory."""

    results = []

    # 1. Search Short-term (Recent Conversation)
    for turn in memory_state["short_term"]["turns"]:
        similarity = compute_similarity(
            query,
            turn["user_message"] + " " + turn["assistant_message"]
        )

        if similarity > 0.7:
            results.append({
                "source": "short_term",
                "turn": turn["turn_id"],
                "content": turn,
                "score": similarity * 1.2,  # Boost recent
                "age_penalty": calculate_age_penalty(turn["timestamp"])
            })

    # 2. Search Long-term (Facts)
    for fact_key, fact_data in memory_state["long_term"]["facts"].items():
        similarity = compute_similarity(query, str(fact_data["value"]))

        if similarity > 0.6:
            results.append({
                "source": "long_term",
                "key": fact_key,
                "content": fact_data,
                "score": similarity * fact_data["confidence"],
                "age_penalty": 0  # Facts don't age
            })

    # 3. Rank Results
    for result in results:
        result["final_score"] = (
            result["score"] - result["age_penalty"]
        )

    results.sort(key=lambda x: x["final_score"], reverse=True)

    return results[:5]  # Top 5 results
```

### Memory Update Pipeline

```
New Turn
    ↓
┌──────────────────────┐
│ 1. Add to Short-term│
│ - Append turn       │
│ - Check limit       │
│ - Prune if needed   │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 2. Entity Extraction│
│ - NER (people, etc.)│
│ - Keyword extraction│
│ - Topic detection   │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 3. Fact Extraction  │
│ - Identify facts    │
│ - Extract key-value │
│ - Assign confidence │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 4. Update Long-term │
│ - Add new facts     │
│ - Update existing   │
│ - Resolve conflicts │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 5. Update Working   │
│ - Current topic     │
│ - Active entities   │
│ - Context window    │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ 6. Persist          │
│ - Save to disk      │
│ - Update stats      │
└──────────────────────┘
```

### Memory Pruning Strategy

```python
def prune_short_term(short_term: dict, max_turns: int = 10):
    """Remove old turns when limit exceeded."""

    turns = short_term["turns"]

    if len(turns) <= max_turns:
        return  # No pruning needed

    # Strategy 1: Simple FIFO
    # Remove oldest turns
    turns_to_remove = len(turns) - max_turns
    turns = turns[turns_to_remove:]

    # Strategy 2: Importance-based
    # Keep important turns even if old
    important_turns = [
        t for t in turns if t.get("importance", 0) > 0.8
    ]
    regular_turns = [
        t for t in turns if t.get("importance", 0) <= 0.8
    ]

    # Keep important + most recent regular
    keep_count = max_turns - len(important_turns)
    final_turns = important_turns + regular_turns[-keep_count:]

    short_term["turns"] = sorted(final_turns, key=lambda t: t["turn_id"])
```

## Summary

When memory is enabled:

1. **Initialization**: Memory state loaded from previous session
2. **Retrieval**: Relevant memories retrieved for each message
3. **Context**: Memory added to LLM prompt
4. **Processing**: LLM uses memory to inform response
5. **Update**: New information stored, old information pruned
6. **Persistence**: Memory saved for future sessions

Memory provides the LLM with:
- **Continuity**: Remembers previous conversations
- **Personalization**: Adapts to user preferences
- **Context**: Maintains project and topic awareness
- **Learning**: Accumulates knowledge over time

The memory system acts as the LLM's "brain," enabling natural, context-aware conversations that feel continuous rather than isolated exchanges.

---

**Last Updated**: 2025-01-06

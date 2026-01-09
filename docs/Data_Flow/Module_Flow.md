# Module Logic Flow

This document explains the complete logic flow when a module is enabled in the Local LLM Framework (LLF), including detailed examples and internal processing.

## Table of Contents

1. [What is a Module?](#what-is-a-module)
2. [Module Types](#module-types)
3. [High-Level Flow](#high-level-flow)
4. [Detailed Logic Flow](#detailed-logic-flow)
5. [Examples](#examples)
6. [Internal Processing](#internal-processing)

## What is a Module?

A **module** in LLF is a pluggable component that extends or modifies the LLM's behavior. Modules can:
- Preprocess user input
- Postprocess LLM output
- Add custom functionality
- Integrate external services
- Modify conversation flow

**Key Characteristics**:
- Self-contained functionality
- Configurable and reusable
- Chainable (multiple modules can work together)
- Hook-based (respond to specific events)

**Common Use Cases**:
- Content moderation
- Language translation
- Response formatting
- Custom business logic
- External API integration

## Module Types

### 1. Preprocessor Modules

Execute **before** the LLM processes the message.

```
User Input → [Preprocessor Module] → Modified Input → LLM
```

**Examples**:
- Language detection and translation
- Content filtering
- Context enrichment
- Input validation

### 2. Postprocessor Modules

Execute **after** the LLM generates a response.

```
LLM → Response → [Postprocessor Module] → Modified Response → User
```

**Examples**:
- Response formatting (Markdown, HTML)
- Content moderation
- Translation back to user's language
- Adding citations or references

### 3. Middleware Modules

Execute at **multiple points** in the pipeline.

```
User → [Pre] → LLM → [Post] → User
         ↓             ↓
    [Middleware]  [Middleware]
```

**Examples**:
- Logging and analytics
- Performance monitoring
- Error handling
- Caching

## High-Level Flow

```
┌──────────────┐
│ User Message │
└──────┬───────┘
       │
       ↓
┌────────────────────────────────────────────────────────┐
│ 1. Module Initialization                              │
│    - Load enabled modules from config                 │
│    - Initialize module instances                      │
│    - Set up module chain                              │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 2. Preprocessing Phase                                 │
│    - Execute preprocessor modules in order            │
│    - Each module can modify the input                 │
│    - Pass modified input to next module               │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 3. LLM Processing                                      │
│    - Process (potentially modified) input             │
│    - Generate response                                │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│ 4. Postprocessing Phase                                │
│    - Execute postprocessor modules in order           │
│    - Each module can modify the response              │
│    - Pass modified response to next module            │
└────────────────┬───────────────────────────────────────┘
                 │
                 ↓
┌──────────────────┐
│ Response to User │
└──────────────────┘
```

## Detailed Logic Flow

### Phase 1: Module Loading

```
┌─────────────────────────────────────────────────────────────┐
│ LLMClient.__init__()                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Load modules config    │
        │ {                      │
        │   "modules": [         │
        │     {                  │
        │       "name": "trans", │
        │       "type": "pre",   │
        │       "enabled": true, │
        │       "config": {...}  │
        │     },                 │
        │     {                  │
        │       "name": "format",│
        │       "type": "post",  │
        │       "enabled": true  │
        │     }                  │
        │   ]                    │
        │ }                      │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ ModuleManager()        │
        │ - Parse config         │
        │ - Validate modules     │
        │ - Check dependencies   │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ For each enabled       │
        │ module:                │
        │                        │
        │ 1. Import module code  │
        │ 2. Initialize instance │
        │ 3. Verify interface    │
        │ 4. Add to chain        │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ Build Execution Chains │
        │                        │
        │ Preprocessors: [       │
        │   translator,          │
        │   validator            │
        │ ]                      │
        │                        │
        │ Postprocessors: [      │
        │   formatter,           │
        │   moderator            │
        │ ]                      │
        └────────────────────────┘
```

### Phase 2: Preprocessing Execution

```
┌─────────────────────────────────────────────────────────────┐
│ User Input: "Bonjour! Comment créer une API?"              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Module Chain: Preprocessors    │
        │ [translator, validator]        │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Module 1: Translator           │
        │ (preprocessor)                 │
        │                                │
        │ Input:                         │
        │ "Bonjour! Comment créer une    │
        │  API?"                         │
        │                                │
        │ Processing:                    │
        │ - Detect language: French      │
        │ - Translate to English         │
        │                                │
        │ Output:                        │
        │ "Hello! How to create an API?" │
        │                                │
        │ Metadata:                      │
        │ {                              │
        │   "original_lang": "fr",       │
        │   "translated": true           │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Module 2: Validator            │
        │ (preprocessor)                 │
        │                                │
        │ Input:                         │
        │ "Hello! How to create an API?" │
        │                                │
        │ Processing:                    │
        │ - Check for inappropriate      │
        │   content: PASS                │
        │ - Validate question format:    │
        │   PASS                         │
        │ - Check length: OK             │
        │                                │
        │ Output:                        │
        │ "Hello! How to create an API?" │
        │ (unchanged)                    │
        │                                │
        │ Metadata:                      │
        │ {                              │
        │   "validated": true,           │
        │   "safe": true                 │
        │ }                              │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Final Preprocessed Input       │
        │                                │
        │ Text:                          │
        │ "Hello! How to create an API?" │
        │                                │
        │ Metadata:                      │
        │ {                              │
        │   "original_lang": "fr",       │
        │   "translated": true,          │
        │   "validated": true,           │
        │   "safe": true                 │
        │ }                              │
        └────────────────────────────────┘
```

### Phase 3: LLM Processing

```
┌─────────────────────────────────────────────────────────────┐
│ LLM receives preprocessed input                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Input to LLM:                  │
        │ "Hello! How to create an API?" │
        │                                │
        │ (Note: User's original French  │
        │  was already translated)       │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ LLM Processing                 │
        │ - Generate response in English │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ LLM Output:                    │
        │                                │
        │ "To create an API, you can use │
        │ frameworks like FastAPI or     │
        │ Flask in Python. Here's a      │
        │ simple example with FastAPI:   │
        │                                │
        │ ```python                      │
        │ from fastapi import FastAPI    │
        │ app = FastAPI()                │
        │                                │
        │ @app.get('/')                  │
        │ def read_root():               │
        │     return {'Hello': 'World'}  │
        │ ```"                           │
        └────────────────────────────────┘
```

### Phase 4: Postprocessing Execution

```
┌─────────────────────────────────────────────────────────────┐
│ LLM Response (English)                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────┐
        │ Module Chain: Postprocessors   │
        │ [formatter, translator_back]   │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Module 1: Formatter            │
        │ (postprocessor)                │
        │                                │
        │ Input: Raw LLM text            │
        │                                │
        │ Processing:                    │
        │ - Detect code blocks           │
        │ - Add syntax highlighting      │
        │ - Format markdown              │
        │                                │
        │ Output: Formatted markdown     │
        │ with proper code blocks        │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Module 2: Translator Back      │
        │ (postprocessor)                │
        │                                │
        │ Check metadata:                │
        │ - original_lang: "fr"          │
        │ - translated: true             │
        │                                │
        │ Action: Translate back to      │
        │         French                 │
        │                                │
        │ Input: (English response)      │
        │ Output: (French response)      │
        │                                │
        │ "Pour créer une API, vous      │
        │ pouvez utiliser des frameworks │
        │ comme FastAPI ou Flask en      │
        │ Python. Voici un exemple       │
        │ simple avec FastAPI:           │
        │                                │
        │ ```python                      │
        │ from fastapi import FastAPI    │
        │ ...                            │
        │ ```"                           │
        └────────┬───────────────────────┘
                 │
                 ↓
        ┌────────────────────────────────┐
        │ Final Response to User         │
        │ (French, formatted)            │
        └────────────────────────────────┘
```

## Examples

### Example 1: Language Translation Module

**Module Configuration**:

```json
{
  "name": "auto_translator",
  "type": "preprocessor",
  "enabled": true,
  "config": {
    "target_language": "en",
    "provider": "google_translate"
  }
}
```

**Module Code**:

```python
# modules/auto_translator.py

class AutoTranslator:
    """Automatically translate non-English input to English."""

    def __init__(self, config: dict):
        self.target_lang = config.get('target_language', 'en')
        self.provider = config.get('provider', 'google_translate')

    def preprocess(self, input_data: dict) -> dict:
        """
        Preprocess user input by translating to target language.

        Args:
            input_data: {
                'text': str,
                'metadata': dict
            }

        Returns:
            Modified input_data with translation
        """
        text = input_data['text']
        metadata = input_data.get('metadata', {})

        # Detect language
        detected_lang = self._detect_language(text)

        # If not target language, translate
        if detected_lang != self.target_lang:
            translated_text = self._translate(
                text,
                source=detected_lang,
                target=self.target_lang
            )

            # Store original language in metadata
            metadata['original_language'] = detected_lang
            metadata['translated'] = True

            return {
                'text': translated_text,
                'metadata': metadata
            }

        # No translation needed
        return input_data

    def _detect_language(self, text: str) -> str:
        """Detect language of text."""
        # Implementation using language detection library
        from langdetect import detect
        return detect(text)

    def _translate(self, text: str, source: str, target: str) -> str:
        """Translate text from source to target language."""
        # Implementation using translation API
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src=source, dest=target)
        return result.text
```

**Usage Flow**:

```
User (French): "Comment faire une boucle en Python?"
    ↓
[Preprocessor: AutoTranslator]
    ↓
Translated: "How to make a loop in Python?"
    ↓
[LLM Processing]
    ↓
Response: "To create a loop in Python, use 'for' or 'while'..."
    ↓
[Postprocessor: TranslateBack]
    ↓
Final: "Pour créer une boucle en Python, utilisez 'for' ou 'while'..."
    ↓
User (French) receives response
```

### Example 2: Content Moderation Module

**Module Configuration**:

```json
{
  "name": "content_moderator",
  "type": "postprocessor",
  "enabled": true,
  "config": {
    "check_harmful": true,
    "check_bias": true,
    "action": "flag"
  }
}
```

**Module Code**:

```python
# modules/content_moderator.py

class ContentModerator:
    """Moderate LLM responses for harmful or biased content."""

    def __init__(self, config: dict):
        self.check_harmful = config.get('check_harmful', True)
        self.check_bias = config.get('check_bias', True)
        self.action = config.get('action', 'flag')  # flag, redact, reject

    def postprocess(self, output_data: dict) -> dict:
        """
        Postprocess LLM output for content moderation.

        Args:
            output_data: {
                'text': str,
                'metadata': dict
            }

        Returns:
            Modified output with moderation applied
        """
        text = output_data['text']
        metadata = output_data.get('metadata', {})

        issues = []

        # Check for harmful content
        if self.check_harmful:
            harmful_score = self._check_harmful_content(text)
            if harmful_score > 0.7:
                issues.append({
                    'type': 'harmful',
                    'score': harmful_score
                })

        # Check for bias
        if self.check_bias:
            bias_score = self._check_bias(text)
            if bias_score > 0.6:
                issues.append({
                    'type': 'bias',
                    'score': bias_score
                })

        # Take action if issues found
        if issues:
            metadata['moderation'] = {
                'issues': issues,
                'action': self.action
            }

            if self.action == 'reject':
                return {
                    'text': "I apologize, but I cannot provide that response.",
                    'metadata': metadata
                }
            elif self.action == 'redact':
                text = self._redact_problematic_parts(text, issues)

        return {
            'text': text,
            'metadata': metadata
        }

    def _check_harmful_content(self, text: str) -> float:
        """Check for harmful content, return score 0-1."""
        # Implementation using ML model or API
        harmful_keywords = ['violence', 'harm', 'illegal']
        score = sum(1 for word in harmful_keywords if word in text.lower())
        return min(score / 3, 1.0)

    def _check_bias(self, text: str) -> float:
        """Check for biased content, return score 0-1."""
        # Implementation using bias detection model
        return 0.3  # Placeholder

    def _redact_problematic_parts(self, text: str, issues: list) -> str:
        """Redact problematic parts of text."""
        # Implementation to redact specific parts
        return text  # Simplified
```

**Usage Flow**:

```
User: "How do I hack into a system?"
    ↓
[LLM Processing]
    ↓
Response: "I cannot help with hacking as it's illegal..."
    ↓
[Postprocessor: ContentModerator]
    ↓
Check: harmful_score = 0.2 (low, because LLM refused)
    ↓
Action: PASS (no moderation needed)
    ↓
User receives: "I cannot help with hacking as it's illegal..."
```

### Example 3: Response Formatting Module

**Module Code**:

```python
# modules/markdown_formatter.py

class MarkdownFormatter:
    """Format LLM responses with proper markdown."""

    def postprocess(self, output_data: dict) -> dict:
        """Format response with markdown."""
        text = output_data['text']

        # Add code block formatting
        text = self._format_code_blocks(text)

        # Add headers
        text = self._format_headers(text)

        # Add lists
        text = self._format_lists(text)

        return {
            'text': text,
            'metadata': output_data.get('metadata', {})
        }

    def _format_code_blocks(self, text: str) -> str:
        """Detect and format code blocks."""
        import re

        # Find code-like patterns
        # (simplified - real implementation more complex)
        pattern = r'(def |class |import |from )[^\n]+'

        def add_code_block(match):
            code = match.group(0)
            return f"\n```python\n{code}\n```\n"

        return re.sub(pattern, add_code_block, text)

    def _format_headers(self, text: str) -> str:
        """Add markdown headers."""
        # Implementation
        return text

    def _format_lists(self, text: str) -> str:
        """Format lists with markdown."""
        # Implementation
        return text
```

**Usage**:

```
LLM Output (plain):
"To create a function in Python use def keyword. Example: def hello(): return 'hi'"

    ↓
[Postprocessor: MarkdownFormatter]
    ↓

Formatted Output:
"To create a function in Python use `def` keyword. Example:

```python
def hello():
    return 'hi'
```"
```

### Example 4: Module Chaining

**Configuration**:

```json
{
  "modules": [
    {
      "name": "translator",
      "type": "preprocessor",
      "order": 1
    },
    {
      "name": "validator",
      "type": "preprocessor",
      "order": 2
    },
    {
      "name": "formatter",
      "type": "postprocessor",
      "order": 1
    },
    {
      "name": "moderator",
      "type": "postprocessor",
      "order": 2
    }
  ]
}
```

**Execution Flow**:

```
User Input (French)
    ↓
┌─────────────────────┐
│ Preprocessor 1      │
│ (Translator)        │
│ FR → EN             │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Preprocessor 2      │
│ (Validator)         │
│ Check safety        │
└─────────┬───────────┘
          ↓
     [LLM Processing]
          ↓
┌─────────────────────┐
│ Postprocessor 1     │
│ (Formatter)         │
│ Add markdown        │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Postprocessor 2     │
│ (Moderator)         │
│ Check content       │
└─────────┬───────────┘
          ↓
    Final Output
```

## Internal Processing

### Module Interface

All modules must implement this interface:

```python
from typing import Protocol, dict

class Module(Protocol):
    """Module interface."""

    def __init__(self, config: dict):
        """Initialize module with config."""
        ...

    def preprocess(self, input_data: dict) -> dict:
        """
        Preprocess input (for preprocessor modules).

        Args:
            input_data: {
                'text': str,
                'metadata': dict,
                'context': dict  # Optional
            }

        Returns:
            Modified input_data
        """
        ...

    def postprocess(self, output_data: dict) -> dict:
        """
        Postprocess output (for postprocessor modules).

        Args:
            output_data: {
                'text': str,
                'metadata': dict,
                'context': dict  # Optional
            }

        Returns:
            Modified output_data
        """
        ...
```

### Module Manager

```python
class ModuleManager:
    """Manages module loading and execution."""

    def __init__(self, config: dict):
        self.config = config
        self.preprocessors = []
        self.postprocessors = []
        self._load_modules()

    def _load_modules(self):
        """Load all enabled modules."""
        for module_config in self.config.get('modules', []):
            if not module_config.get('enabled', False):
                continue

            module = self._import_module(module_config)

            if module_config['type'] == 'preprocessor':
                self.preprocessors.append(module)
            elif module_config['type'] == 'postprocessor':
                self.postprocessors.append(module)

        # Sort by order
        self.preprocessors.sort(key=lambda m: m.config.get('order', 0))
        self.postprocessors.sort(key=lambda m: m.config.get('order', 0))

    def run_preprocessors(self, input_data: dict) -> dict:
        """Run all preprocessors in order."""
        data = input_data

        for module in self.preprocessors:
            try:
                data = module.preprocess(data)
            except Exception as e:
                logger.error(f"Preprocessor error: {e}")
                # Continue with original data

        return data

    def run_postprocessors(self, output_data: dict) -> dict:
        """Run all postprocessors in order."""
        data = output_data

        for module in self.postprocessors:
            try:
                data = module.postprocess(data)
            except Exception as e:
                logger.error(f"Postprocessor error: {e}")
                # Continue with original data

        return data
```

### Complete Processing Pipeline

```
User Message
    ↓
┌──────────────────────────────┐
│ 1. Input Preparation         │
│ data = {                     │
│   'text': user_message,      │
│   'metadata': {},            │
│   'context': conversation    │
│ }                            │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ 2. Run Preprocessors         │
│ for module in preprocessors: │
│   data = module.preprocess(  │
│       data)                  │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ 3. LLM Processing            │
│ response = llm.generate(     │
│     data['text'])            │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ 4. Prepare Output            │
│ output = {                   │
│   'text': response,          │
│   'metadata': data.metadata, │
│   'context': data.context    │
│ }                            │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ 5. Run Postprocessors        │
│ for module in postprocessors:│
│   output = module.postprocess│
│       (output)               │
└──────────┬───────────────────┘
           ↓
    Final Response
```

## Summary

When a module is enabled:

1. **Load**: Module loaded and initialized at startup
2. **Chain**: Added to preprocessing or postprocessing chain
3. **Execute**: Run in order when processing messages
4. **Transform**: Can modify input/output at each stage
5. **Metadata**: Can add context and metadata for other modules

Modules provide:
- **Extensibility**: Add features without changing core code
- **Modularity**: Self-contained, reusable components
- **Flexibility**: Chain multiple modules for complex behavior
- **Integration**: Connect external services and APIs
- **Control**: Modify LLM behavior at multiple points

The module system enables LLF to be highly customizable and adaptable to specific use cases and requirements.

---

**Last Updated**: 2025-01-06

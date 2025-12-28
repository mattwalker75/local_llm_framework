# RAG Data Store Tools

Utilities for preparing and processing data for ingestion into RAG (Retrieval-Augmented Generation) data stores.

## Tools

### Process_PDF.py

Convert PDF files to clean text suitable for RAG ingestion.

### Process_DOC.py

Convert Microsoft Word documents (.docx, .rtf) to clean text suitable for RAG ingestion.

### Process_TXT.py

Convert plain text files (.txt, .log, etc.) to clean, structured text suitable for RAG ingestion.

### Process_MD.py

Advanced Markdown file processing with structure parsing, code block extraction, and hierarchical sections for RAG ingestion.

### Process_WEB.py

Extract clean text from web pages (URLs) for RAG ingestion.

---

## Process_PDF.py

### Quick Start

```bash
# Install dependencies
pip install pymupdf

# Basic text conversion
./Process_PDF.py -i document.pdf -o output.txt

# JSONL format (recommended for RAG)
./Process_PDF.py -i document.pdf -o output.jsonl -f jsonl
```

#### Features

- **Multiple Output Formats**: Text, JSON, JSONL (line-delimited JSON)
- **Metadata Extraction**: Captures title, author, subject, page count
- **Text Normalization**: Unicode normalization, whitespace cleanup
- **Page Number Removal**: Automatically removes common page number patterns
- **Structure Preservation**: Maintains page numbers for citation (JSON/JSONL formats)
- **Error Handling**: Robust error handling with helpful messages
- **Progress Tracking**: Verbose mode for debugging

#### Usage Examples

**Basic text output:**
```bash
./Process_PDF.py -i report.pdf -o report.txt
```

**JSONL format (best for RAG ingestion):**
```bash
./Process_PDF.py -i report.pdf -o report.jsonl -f jsonl
```

Output format (one JSON record per line):
```json
{"title": "Report", "author": "John Doe", "page_number": 1, "text": "...", "char_count": 1234}
{"title": "Report", "author": "John Doe", "page_number": 2, "text": "...", "char_count": 1567}
```

**JSON format with metadata:**
```bash
./Process_PDF.py -i report.pdf -o report.json -f json
```

Output format:
```json
{
  "metadata": {
    "title": "Report",
    "author": "John Doe",
    "subject": "Analysis",
    "page_count": 10,
    "source_file": "report.pdf"
  },
  "pages": [
    {"page_number": 1, "text": "...", "char_count": 1234},
    {"page_number": 2, "text": "...", "char_count": 1567}
  ]
}
```

**Keep page numbers in text:**
```bash
./Process_PDF.py -i report.pdf -o report.txt --keep-page-numbers
```

**Verbose output for debugging:**
```bash
./Process_PDF.py -i report.pdf -o report.txt --verbose
```

#### Command-Line Options

```
Required Arguments:
  -i, --input FILE       PDF file to read as input
  -o, --output FILE      Output file path

Optional Arguments:
  -f, --format FORMAT    Output format: text, json, jsonl (default: text)
  --keep-page-numbers    Keep page numbers in text (default: remove them)
  -v, --verbose          Print detailed progress information
  -h, --help            Show help message
```

#### Text Cleaning Pipeline

The script applies the following cleaning steps:

1. **Page Number Removal** (optional)
   - Removes "Page X", "X / Y", and standalone numbers
   - Can be disabled with `--keep-page-numbers`

2. **Whitespace Cleanup**
   - Merges broken lines within paragraphs
   - Preserves paragraph breaks (double newlines)
   - Removes excessive blank lines

3. **Text Normalization**
   - Unicode NFC normalization
   - Removes control characters (form feeds, carriage returns)
   - Replaces special spaces (non-breaking spaces, tabs)
   - Collapses excessive whitespace

#### Why JSONL for RAG?

JSONL (JSON Lines) format is recommended for RAG systems because:

- **Stream Processing**: Each line is independent, easy to process incrementally
- **Page Citations**: Preserves page numbers for source attribution
- **Metadata Rich**: Each record includes document metadata
- **Standard Format**: Widely supported by RAG ingestion pipelines
- **Efficient**: No need to parse entire file into memory

#### Example RAG Workflow

```bash
# 1. Convert multiple PDFs to JSONL
for pdf in documents/*.pdf; do
    ./Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
done

# 2. Concatenate all JSONL files
cat processed/*.jsonl > all_documents.jsonl

# 3. Ingest into RAG system (example with custom script)
python ingest_to_rag.py --input all_documents.jsonl --index my_index

# 4. Query the RAG system
python query_rag.py --query "What is the main finding?" --index my_index
```

#### Error Handling

The script handles common errors gracefully:

- **File not found**: Clear error message with file path
- **PDF parsing errors**: Warns about specific pages, continues processing
- **No text extracted**: Warning message, creates empty output
- **Output write errors**: Clear error message with path

Exit codes:
- `0`: Success
- `1`: Error (file not found, parsing error, write error)
- `130`: User interrupted (Ctrl+C)

#### Dependencies

- **PyMuPDF (fitz)**: PDF text extraction
  ```bash
  pip install pymupdf
  ```

#### Performance

- **Speed**: ~100-200 pages/second (depends on PDF complexity)
- **Memory**: Minimal - processes pages incrementally
- **File Size**: No hard limit, but very large PDFs may be slow

#### Limitations

- **Text-based PDFs**: Requires actual text (not scanned images)
- **OCR**: Does not perform OCR on scanned documents
- **Tables**: Basic table text extraction (may need post-processing)
- **Images**: Skips images (text-only extraction)
- **Formatting**: Does not preserve complex formatting

#### Troubleshooting

**Problem**: "ModuleNotFoundError: No module named 'fitz'"

**Solution**: Install PyMuPDF
```bash
pip install pymupdf
```

**Problem**: "No text extracted from PDF"

**Solution**: PDF may be scanned images. Use OCR tool first:
```bash
# Example with ocrmypdf
ocrmypdf input.pdf output_ocr.pdf
./Process_PDF.py -i output_ocr.pdf -o output.txt
```

**Problem**: Important numbers being removed as page numbers

**Solution**: Use `--keep-page-numbers` flag
```bash
./Process_PDF.py -i document.pdf -o output.txt --keep-page-numbers
```

#### Contributing

Contributions welcome! Please ensure:
- Type hints for all functions
- Docstrings in Google style
- Error handling with helpful messages
- Unit tests for new features

#### License

MIT License - see LICENSE file for details

---

## Process_DOC.py

### Quick Start

```bash
# Install dependencies
pip install python-docx striprtf

# Basic text conversion
./Process_DOC.py -i document.docx -o output.txt

# JSONL format (recommended for RAG)
./Process_DOC.py -i document.docx -o output.jsonl -f jsonl
```

### Features

- **Multiple Input Formats**: .docx (modern Word), .rtf (Rich Text Format)
- **Multiple Output Formats**: Text, JSON, JSONL (line-delimited JSON)
- **Metadata Extraction**: Captures title, author, subject, dates, paragraph count
- **Structure Preservation**: Maintains headings and paragraph styles
- **Text Normalization**: Unicode normalization, whitespace cleanup
- **Error Handling**: Robust error handling with helpful messages
- **Progress Tracking**: Verbose mode for debugging

### Usage Examples

**Basic text output:**
```bash
./Process_DOC.py -i report.docx -o report.txt
```

**JSONL format (best for RAG ingestion):**
```bash
./Process_DOC.py -i report.docx -o report.jsonl -f jsonl
```

Output format (one JSON record per paragraph):
```json
{"title": "Report", "author": "John", "para_number": 1, "text": "Introduction...", "is_heading": false, "style": "Normal", "char_count": 234}
{"title": "Report", "author": "John", "para_number": 2, "text": "Background", "is_heading": true, "style": "Heading 1", "char_count": 10}
{"title": "Report", "author": "John", "para_number": 3, "text": "The project began...", "is_heading": false, "style": "Normal", "char_count": 156}
```

**JSON format with metadata:**
```bash
./Process_DOC.py -i report.docx -o report.json -f json
```

Output format:
```json
{
  "metadata": {
    "title": "Annual Report",
    "author": "John Doe",
    "subject": "Financial Analysis",
    "created": "2024-01-15",
    "modified": "2024-03-20",
    "para_count": 45,
    "source_file": "report.docx"
  },
  "paragraphs": [
    {"para_number": 1, "text": "...", "is_heading": false, "style": "Normal", "char_count": 234},
    {"para_number": 2, "text": "...", "is_heading": true, "style": "Heading 1", "char_count": 10}
  ]
}
```

**Preserve document structure:**
```bash
./Process_DOC.py -i report.docx -o report.txt --preserve-structure
```

**Verbose output for debugging:**
```bash
./Process_DOC.py -i report.docx -o report.txt --verbose
```

**Convert RTF files:**
```bash
./Process_DOC.py -i document.rtf -o output.txt
```

### Command-Line Options

```
Required Arguments:
  -i, --input FILE       Word document to read (.docx, .rtf)
  -o, --output FILE      Output file path

Optional Arguments:
  -f, --format FORMAT    Output format: text, json, jsonl (default: text)
  --preserve-structure   Preserve document structure (headings, paragraphs)
  -v, --verbose          Print detailed progress information
  -h, --help            Show help message
```

### Text Cleaning Pipeline

The script applies the following cleaning steps:

1. **Structure Preservation** (JSON/JSONL formats)
   - Identifies headings vs normal paragraphs
   - Preserves paragraph styles (Heading 1, Heading 2, Normal, etc.)
   - Maintains paragraph order

2. **Text Normalization**
   - Unicode NFC normalization
   - Removes control characters (form feeds, carriage returns)
   - Replaces special spaces (non-breaking spaces, tabs, zero-width spaces)
   - Collapses excessive whitespace

### Why JSONL for RAG?

JSONL (JSON Lines) format is recommended for RAG systems because:

- **Structure Aware**: Identifies headings for better document understanding
- **Paragraph Citations**: Preserves paragraph numbers for source attribution
- **Metadata Rich**: Each record includes document metadata and paragraph style
- **Stream Processing**: Each line is independent, easy to process incrementally
- **Standard Format**: Widely supported by RAG ingestion pipelines

### Supported Formats

| Format | Extension | Support | Notes |
|--------|-----------|---------|-------|
| Modern Word | .docx | ✅ Full | Recommended, preserves structure |
| Rich Text | .rtf | ✅ Basic | Structure preservation limited |
| Legacy Word | .doc | ❌ Convert first | Use Word or LibreOffice to convert to .docx |

### Converting Legacy .doc Files

If you have old .doc files, convert them first:

**Using Microsoft Word:**
1. Open the .doc file
2. File → Save As → Choose "Word Document (.docx)"

**Using LibreOffice (free, cross-platform):**
```bash
libreoffice --headless --convert-to docx file.doc
```

**Using unoconv (command-line):**
```bash
unoconv -f docx file.doc
```

### Example RAG Workflow

```bash
# 1. Convert multiple Word documents to JSONL
for doc in documents/*.docx; do
    ./Process_DOC.py -i "$doc" -o "processed/$(basename "$doc" .docx).jsonl" -f jsonl
done

# 2. Also convert RTF files
for rtf in documents/*.rtf; do
    ./Process_DOC.py -i "$rtf" -o "processed/$(basename "$rtf" .rtf).jsonl" -f jsonl
done

# 3. Concatenate all JSONL files
cat processed/*.jsonl > all_documents.jsonl

# 4. Ingest into RAG system (example)
python ingest_to_rag.py --input all_documents.jsonl --index my_index

# 5. Query the RAG system
python query_rag.py --query "What are the key findings?" --index my_index
```

### Error Handling

The script handles common errors gracefully:

- **File not found**: Clear error message with file path
- **Unsupported format**: Helpful message with conversion instructions
- **Parsing errors**: Warns about specific paragraphs, continues processing
- **No text extracted**: Warning message, creates empty output
- **Output write errors**: Clear error message with path

Exit codes:
- `0`: Success
- `1`: Error (file not found, parsing error, write error)
- `130`: User interrupted (Ctrl+C)

### Dependencies

- **python-docx**: For .docx file extraction
  ```bash
  pip install python-docx
  ```

- **striprtf**: For .rtf file extraction
  ```bash
  pip install striprtf
  ```

Install all dependencies:
```bash
pip install python-docx striprtf
```

### Performance

- **Speed**: ~1000-2000 paragraphs/second (depends on document complexity)
- **Memory**: Minimal - processes paragraphs incrementally
- **File Size**: No hard limit, but very large documents may be slow

### Limitations

- **Legacy .doc format**: Requires conversion to .docx first
- **Tables**: Basic table text extraction (cells extracted as paragraphs)
- **Images**: Skips images (text-only extraction)
- **Complex Formatting**: Does not preserve fonts, colors, or complex layouts
- **Embedded Objects**: Skips embedded objects (charts, diagrams)
- **Track Changes**: Extracts final text only (ignores tracked changes)

### Troubleshooting

**Problem**: "ModuleNotFoundError: No module named 'docx'"

**Solution**: Install python-docx
```bash
pip install python-docx
```

**Problem**: "ModuleNotFoundError: No module named 'striprtf'"

**Solution**: Install striprtf (only needed for .rtf files)
```bash
pip install striprtf
```

**Problem**: "Error: .doc format is not directly supported"

**Solution**: Convert to .docx first using Word, LibreOffice, or unoconv:
```bash
libreoffice --headless --convert-to docx file.doc
./Process_DOC.py -i file.docx -o output.txt
```

**Problem**: "No text extracted from document"

**Solution**: Document may be empty or contain only images. Check the original file.

**Problem**: Table content appears jumbled

**Solution**: Word tables are extracted as sequential paragraphs. For better table handling, consider using specialized table extraction tools or export to CSV from Word first.

### Structure Preservation

When using JSON/JSONL output, the script preserves:

- **Heading Levels**: Identified by paragraph style (Heading 1, Heading 2, etc.)
- **Paragraph Styles**: Normal, List, Quote, etc.
- **Document Hierarchy**: Paragraphs in original order
- **Metadata**: Title, author, dates from document properties

This is especially useful for RAG systems that need to:
- Weight headings higher in search results
- Understand document structure for better chunking
- Provide hierarchical context in responses

### Contributing

Contributions welcome! Please ensure:
- Type hints for all functions
- Docstrings in Google style
- Error handling with helpful messages
- Unit tests for new features

### License

MIT License - see LICENSE file for details

---

## Process_TXT.py

### Quick Start

```bash
# Basic text normalization
./Process_TXT.py -i document.txt -o output.txt

# JSONL format (recommended for RAG)
./Process_TXT.py -i document.txt -o output.jsonl -f jsonl

# Process markdown files with heading detection
./Process_TXT.py -i README.md -o output.jsonl -f jsonl --detect-headings
```

### Features

- **Multiple Input Formats**: .txt, .md, .log, or any plain text file
- **Multiple Output Formats**: Text, JSON, JSONL (line-delimited JSON)
- **Smart Encoding Detection**: Automatically detects UTF-8, Latin-1, Windows-1252, etc.
- **Paragraph Detection**: Intelligently splits text into paragraphs
- **Markdown Heading Detection**: Identifies and marks heading levels (# through ######)
- **Text Normalization**: Unicode normalization, whitespace cleanup
- **Metadata Extraction**: Character counts, line counts, paragraph numbers
- **Error Handling**: Robust error handling with helpful messages
- **Progress Tracking**: Verbose mode for debugging

### Usage Examples

**Basic text normalization:**
```bash
./Process_TXT.py -i document.txt -o clean.txt
```

**JSONL format (best for RAG ingestion):**
```bash
./Process_TXT.py -i document.txt -o output.jsonl -f jsonl
```

Output format (one JSON record per paragraph):
```json
{"source_file": "document.txt", "encoding": "utf-8", "para_number": 1, "text": "Introduction paragraph...", "is_heading": false, "heading_level": 0, "char_count": 234, "line_count": 3}
{"source_file": "document.txt", "encoding": "utf-8", "para_number": 2, "text": "Second paragraph...", "is_heading": false, "heading_level": 0, "char_count": 156, "line_count": 2}
```

**JSON format with metadata:**
```bash
./Process_TXT.py -i document.txt -o output.json -f json
```

Output format:
```json
{
  "metadata": {
    "source_file": "document.txt",
    "source_path": "/full/path/to/document.txt",
    "encoding": "utf-8",
    "para_count": 25,
    "total_chars": 5432,
    "total_lines": 120
  },
  "paragraphs": [
    {"para_number": 1, "text": "...", "is_heading": false, "heading_level": 0, "char_count": 234, "line_count": 3},
    {"para_number": 2, "text": "...", "is_heading": false, "heading_level": 0, "char_count": 156, "line_count": 2}
  ]
}
```

**Process markdown files with heading detection:**
```bash
./Process_TXT.py -i README.md -o readme.jsonl -f jsonl --detect-headings
```

Output includes heading detection:
```json
{"source_file": "README.md", "encoding": "utf-8", "para_number": 1, "text": "Introduction", "is_heading": true, "heading_level": 1, "char_count": 12, "line_count": 1}
{"source_file": "README.md", "encoding": "utf-8", "para_number": 2, "text": "This is the intro paragraph...", "is_heading": false, "heading_level": 0, "char_count": 156, "line_count": 2}
{"source_file": "README.md", "encoding": "utf-8", "para_number": 3, "text": "Installation", "is_heading": true, "heading_level": 2, "char_count": 12, "line_count": 1}
```

**Verbose output for debugging:**
```bash
./Process_TXT.py -i document.txt -o output.txt --verbose
```

### Command-Line Options

```
Required Arguments:
  -i, --input FILE       Text file to read (.txt, .md, .log, etc.)
  -o, --output FILE      Output file path

Optional Arguments:
  -f, --format FORMAT    Output format: text, json, jsonl (default: text)
  --detect-headings      Detect and mark markdown-style headings
  -v, --verbose          Print detailed progress information
  -h, --help            Show help message
```

### Text Processing Pipeline

The script applies the following processing steps:

1. **Encoding Detection**
   - Automatically detects file encoding
   - Tries UTF-8, Latin-1, Windows-1252, ISO-8859-1, ASCII
   - Falls back to UTF-8 with error replacement

2. **Text Normalization**
   - Unicode NFC normalization
   - Removes control characters (except newline/tab)
   - Replaces special spaces (non-breaking spaces, zero-width spaces)
   - Normalizes line endings to \n
   - Collapses excessive blank lines (max 2 consecutive)
   - Preserves indentation while collapsing internal whitespace

3. **Paragraph Detection**
   - Splits on blank lines
   - Preserves paragraph structure
   - Counts lines and characters per paragraph

4. **Heading Detection** (optional with --detect-headings)
   - Detects markdown ATX-style headings (# through ######)
   - Identifies heading level (1-6)
   - Cleans heading text (removes # markers)

### Why JSONL for RAG?

JSONL (JSON Lines) format is recommended for RAG systems because:

- **Paragraph-Level Chunking**: Each paragraph is a separate record
- **Heading Awareness**: Identifies headings for better document understanding
- **Metadata Rich**: Each record includes source file, encoding, character counts
- **Stream Processing**: Each line is independent, easy to process incrementally
- **Standard Format**: Widely supported by RAG ingestion pipelines
- **Flexible**: Can be concatenated, filtered, or transformed line-by-line

### Supported File Types

| Type | Extensions | Support | Notes |
|------|-----------|---------|-------|
| Plain Text | .txt | ✅ Full | Any encoding |
| Markdown | .md | ✅ Full | Use --detect-headings for structure |
| Log Files | .log | ✅ Full | Automatic encoding detection |
| Code | .py, .js, .java, etc. | ✅ Full | Preserves structure |
| Config | .conf, .cfg, .ini | ✅ Full | Any text-based format |

### Example RAG Workflow

```bash
# 1. Convert multiple text files to JSONL
for txt in documents/*.txt; do
    ./Process_TXT.py -i "$txt" -o "processed/$(basename "$txt" .txt).jsonl" -f jsonl
done

# 2. Convert markdown files with heading detection
for md in documents/*.md; do
    ./Process_TXT.py -i "$md" -o "processed/$(basename "$md" .md).jsonl" -f jsonl --detect-headings
done

# 3. Convert log files
for log in logs/*.log; do
    ./Process_TXT.py -i "$log" -o "processed/$(basename "$log" .log).jsonl" -f jsonl
done

# 4. Concatenate all JSONL files
cat processed/*.jsonl > all_documents.jsonl

# 5. Ingest into RAG system (example)
python ingest_to_rag.py --input all_documents.jsonl --index my_index

# 6. Query the RAG system
python query_rag.py --query "What is the main topic?" --index my_index
```

### Error Handling

The script handles common errors gracefully:

- **File not found**: Clear error message with file path
- **Encoding errors**: Automatic encoding detection with fallback
- **Empty files**: Warning message, creates empty output
- **Output write errors**: Clear error message with path

Exit codes:
- `0`: Success
- `1`: Error (file not found, parsing error, write error)
- `130`: User interrupted (Ctrl+C)

### Dependencies

Process_TXT.py uses only Python standard library modules:
- `argparse` - Command-line argument parsing
- `json` - JSON encoding/decoding
- `re` - Regular expressions
- `unicodedata` - Unicode normalization
- `pathlib` - Path manipulation

**No external dependencies required!**

### Performance

- **Speed**: ~10,000-50,000 lines/second (depends on file size and format)
- **Memory**: Minimal - loads full file but processes incrementally
- **File Size**: No hard limit, tested with files up to 100MB+

### Limitations

- **Binary Files**: Only processes text files (not binary)
- **Encoding Detection**: May not detect all rare encodings correctly
- **Heading Detection**: Only supports markdown ATX-style (# headings), not Setext-style (underlined)
- **Code Structure**: Doesn't parse language-specific structure (functions, classes)
- **Table Detection**: Doesn't detect or parse ASCII tables

### Troubleshooting

**Problem**: "UnicodeDecodeError" when reading file

**Solution**: The script auto-detects encoding, but you can manually convert files:
```bash
# Convert to UTF-8 using iconv
iconv -f WINDOWS-1252 -t UTF-8 input.txt > input_utf8.txt
./Process_TXT.py -i input_utf8.txt -o output.jsonl -f jsonl
```

**Problem**: "No text content extracted from file"

**Solution**: File may be empty or contain only whitespace. Check the original file:
```bash
wc -l input.txt  # Check line count
cat input.txt    # View contents
```

**Problem**: Headings not detected in markdown file

**Solution**: Use the `--detect-headings` flag:
```bash
./Process_TXT.py -i README.md -o output.jsonl -f jsonl --detect-headings
```

**Problem**: Paragraphs split incorrectly

**Solution**: The script splits on blank lines. Ensure your text has proper paragraph breaks (double newlines).

### Use Cases

**1. Documentation Processing**
```bash
# Convert all markdown docs with heading structure
for md in docs/**/*.md; do
    ./Process_TXT.py -i "$md" -o "processed/$(basename "$md" .md).jsonl" -f jsonl --detect-headings
done
```

**2. Log File Analysis**
```bash
# Process application logs for RAG
./Process_TXT.py -i app.log -o app_processed.jsonl -f jsonl
```

**3. Code Documentation**
```bash
# Extract code comments and docstrings (as plain text)
./Process_TXT.py -i source_code.py -o code_docs.jsonl -f jsonl
```

**4. Plain Text Books/Articles**
```bash
# Process text books for Q&A system
./Process_TXT.py -i textbook.txt -o textbook.jsonl -f jsonl
```

### Advanced Features

**Encoding Detection**
The script automatically detects file encoding using the following priority:
1. UTF-8
2. Latin-1 (ISO-8859-1)
3. Windows-1252
4. ISO-8859-1
5. ASCII

**Text Normalization**
- Unicode NFC composition (é instead of e + ´)
- Removes zero-width spaces and non-breaking spaces
- Normalizes all line endings to \n
- Preserves intentional indentation
- Collapses excessive whitespace

**Paragraph Detection**
- Blank lines mark paragraph boundaries
- Preserves multi-line paragraphs
- Counts characters and lines per paragraph

**Markdown Heading Support**
- Detects ATX-style headings (# through ######)
- Extracts heading level (1-6)
- Removes # markers from heading text
- Marks headings in output metadata

### Contributing

Contributions welcome! Please ensure:
- Type hints for all functions
- Docstrings in Google style
- Error handling with helpful messages
- Unit tests for new features

### License

MIT License - see LICENSE file for details

---

## Process_WEB.py

### Quick Start

```bash
# Install dependencies
pip install requests beautifulsoup4

# Basic text extraction
./Process_WEB.py -i https://example.com -o output.txt

# JSONL format (recommended for RAG)
./Process_WEB.py -i https://example.com -o output.jsonl -f jsonl
```

### Features

- **Web Page Fetching**: Downloads and parses HTML from URLs
- **Multiple Output Formats**: Text, JSON, JSONL (line-delimited JSON)
- **Smart Content Extraction**: Focuses on main content, removes scripts/nav/footer
- **Metadata Extraction**: Captures title, description, author, URL, domain
- **Heading Detection**: Identifies H1-H6 HTML heading elements
- **Paragraph-Level Chunking**: Extracts paragraphs, lists, blockquotes
- **Text Normalization**: Unicode normalization, whitespace cleanup
- **User-Agent Support**: Configurable User-Agent to avoid blocking
- **Error Handling**: Robust error handling with helpful messages
- **Progress Tracking**: Verbose mode for debugging

### Usage Examples

**Basic text extraction:**
```bash
./Process_WEB.py -i https://example.com/article -o article.txt
```

**JSONL format (best for RAG ingestion):**
```bash
./Process_WEB.py -i https://example.com/article -o article.jsonl -f jsonl
```

Output format (one JSON record per paragraph):
```json
{"url": "https://example.com/article", "domain": "example.com", "title": "Article Title", "para_number": 1, "text": "Introduction paragraph...", "is_heading": false, "heading_level": 0, "element_type": "p", "char_count": 234}
{"url": "https://example.com/article", "domain": "example.com", "title": "Article Title", "para_number": 2, "text": "Main Heading", "is_heading": true, "heading_level": 1, "element_type": "h1", "char_count": 12}
```

**JSON format with metadata:**
```bash
./Process_WEB.py -i https://example.com/article -o article.json -f json
```

**With heading detection:**
```bash
./Process_WEB.py -i https://example.com/article -o article.jsonl -f jsonl --detect-headings
```

**Verbose output for debugging:**
```bash
./Process_WEB.py -i https://example.com -o output.txt --verbose
```

### Command-Line Options

```
Required Arguments:
  -i, --input URL        URL to fetch (e.g., https://example.com)
  -o, --output FILE      Output file path

Optional Arguments:
  -f, --format FORMAT    Output format: text, json, jsonl (default: text)
  --detect-headings      Detect and mark HTML heading elements (h1-h6)
  --user-agent STRING    User-Agent header (default: RAGBot/1.0)
  --timeout SECONDS      Request timeout in seconds (default: 30)
  -v, --verbose          Print detailed progress information
  -h, --help            Show help message
```

### Why JSONL for RAG?

JSONL (JSON Lines) format is recommended for RAG systems because:

- **URL Attribution**: Each record includes source URL for citations
- **Paragraph-Level Chunking**: Each paragraph is a separate record
- **Heading Awareness**: Identifies headings for better document understanding
- **Metadata Rich**: Each record includes title, domain, element type
- **Stream Processing**: Each line is independent, easy to process incrementally

### Example RAG Workflow

```bash
# 1. Create a list of URLs to process
cat > urls.txt <<EOF
https://example.com/article1
https://example.com/article2
https://example.com/docs/guide
EOF

# 2. Convert all URLs to JSONL
while read url; do
    filename=$(echo "$url" | sed 's|https://||; s|http://||; s|/|_|g')
    ./Process_WEB.py -i "$url" -o "processed/${filename}.jsonl" -f jsonl --detect-headings
    sleep 2  # Be polite - wait between requests
done < urls.txt

# 3. Concatenate all JSONL files
cat processed/*.jsonl > all_web_content.jsonl

# 4. Ingest into RAG system
python ingest_to_rag.py --input all_web_content.jsonl --index my_index
```

### Dependencies

- **requests**: HTTP library (already in base requirements.txt)
- **beautifulsoup4**: HTML parsing and content extraction
  ```bash
  pip install beautifulsoup4
  ```

### Limitations

- **JavaScript-Heavy Sites**: Does not execute JavaScript (static HTML only)
- **Dynamic Content**: Cannot access content loaded via AJAX/fetch
- **Authentication**: Does not handle login/authentication
- **Rate Limiting**: Does not implement rate limiting (add delays manually)
- **Robots.txt**: Does not check robots.txt (respect site policies manually)

### Troubleshooting

**Problem**: "Invalid URL" error

**Solution**: Ensure URL includes scheme (http:// or https://):
```bash
# Correct
./Process_WEB.py -i https://example.com -o output.txt
```

**Problem**: HTTP 403 Forbidden error

**Solution**: Use a custom User-Agent:
```bash
./Process_WEB.py -i https://example.com -o output.txt --user-agent "Mozilla/5.0"
```

**Problem**: HTTP 429 Too Many Requests

**Solution**: Add delays between requests:
```bash
while read url; do
    ./Process_WEB.py -i "$url" -o "output.txt"
    sleep 5  # Wait 5 seconds
done < urls.txt
```

### Respecting Site Policies

**Important**: Always respect website terms of service:

1. **Check robots.txt** before scraping
2. **Add delays** between requests (2-5 seconds)
3. **Use descriptive User-Agent** with contact info
4. **Respect rate limits** and server load

### License

MIT License - see LICENSE file for details

---

## Process_MD.py

### Quick Start

```bash
# Basic Markdown processing
./Process_MD.py -i README.md -o output.txt

# JSONL format (recommended for RAG)
./Process_MD.py -i README.md -o output.jsonl -f jsonl

# Extract code blocks separately
./Process_MD.py -i README.md -o output.jsonl -f jsonl --extract-code
```

### Features

- **Advanced Markdown Parsing**: Full syntax support (headings, lists, code blocks, quotes)
- **Hierarchical Structure**: Parent-child heading relationships preserved
- **YAML Front Matter**: Extracts metadata from document headers
- **Code Block Extraction**: Separate extraction with language detection
- **Section-Based Chunking**: Intelligent section splitting for RAG
- **Heading Hierarchy**: Tracks parent headings for context
- **Multiple Output Formats**: Text, JSON, JSONL (line-delimited JSON)
- **Text Normalization**: Unicode normalization, whitespace cleanup
- **No External Dependencies**: Uses only Python standard library

### Usage Examples

**Basic Markdown to text:**
```bash
./Process_MD.py -i README.md -o readme.txt
```

**JSONL format (best for RAG ingestion):**
```bash
./Process_MD.py -i documentation.md -o docs.jsonl -f jsonl
```

Output format (one JSON record per section):
```json
{"source_file": "README.md", "section_number": 1, "type": "heading", "level": 1, "heading": "Introduction", "parent_path": "", "content": "This is the intro text...", "char_count": 234, "line_count": 3}
{"source_file": "README.md", "section_number": 2, "type": "heading", "level": 2, "heading": "Installation", "parent_path": "Introduction", "content": "To install, run...", "char_count": 156, "line_count": 2}
{"source_file": "README.md", "section_number": 3, "type": "code_block", "level": 0, "heading": "[Code: bash]", "parent_path": "", "content": "npm install", "language": "bash", "char_count": 11, "line_count": 1}
```

**JSON format with metadata:**
```bash
./Process_MD.py -i README.md -o readme.json -f json
```

Output format:
```json
{
  "metadata": {
    "source_file": "README.md",
    "title": "My Project",
    "author": "John Doe",
    "section_count": 15,
    "total_chars": 5432
  },
  "sections": [
    {"section_number": 1, "type": "heading", "level": 1, "heading": "Introduction", "parent_path": "", "content": "...", "char_count": 234},
    {"section_number": 2, "type": "heading", "level": 2, "heading": "Features", "parent_path": "Introduction", "content": "...", "char_count": 156}
  ]
}
```

**Extract code blocks separately:**
```bash
./Process_MD.py -i tutorial.md -o tutorial.jsonl -f jsonl --extract-code
```

With `--extract-code`, code blocks are nested within their parent sections:
```json
{"section_number": 1, "heading": "Installation", "content": "To install:", "code_blocks": [{"type": "code_block", "language": "bash", "code": "npm install", "line_count": 1}]}
```

**Verbose output for debugging:**
```bash
./Process_MD.py -i README.md -o output.txt --verbose
```

### Command-Line Options

```
Required Arguments:
  -i, --input FILE       Markdown file to process
  -o, --output FILE      Output file path

Optional Arguments:
  -f, --format FORMAT    Output format: text, json, jsonl (default: text)
  --extract-code         Extract code blocks separately (nested in sections)
  -v, --verbose          Print detailed progress information
  -h, --help            Show help message
```

### Advanced Features

#### 1. Hierarchical Heading Structure

Process_MD.py tracks the full heading hierarchy, creating parent-child relationships:

```markdown
# Main Topic
## Subtopic
### Detail
```

Produces sections with `parent_path`:
```json
{"heading": "Main Topic", "parent_path": ""}
{"heading": "Subtopic", "parent_path": "Main Topic"}
{"heading": "Detail", "parent_path": "Main Topic > Subtopic"}
```

This helps RAG systems understand document structure and provide contextual answers.

#### 2. YAML Front Matter Extraction

Automatically extracts metadata from YAML front matter:

```markdown
---
title: API Documentation
author: Engineering Team
version: 2.0
date: 2024-01-15
---

# Content starts here...
```

Extracted metadata is included in all output formats.

#### 3. Code Block Detection

Detects fenced code blocks with language specification:

````markdown
```python
def hello():
    print("Hello, world!")
```
````

Extracted as:
```json
{
  "type": "code_block",
  "language": "python",
  "code": "def hello():\n    print(\"Hello, world!\")",
  "line_count": 2,
  "char_count": 39
}
```

#### 4. Section-Based Chunking

Unlike simple paragraph splitting, Process_MD.py chunks by logical sections (headings), which produces more meaningful chunks for RAG retrieval.

### Why Process_MD.py vs Process_TXT.py?

| Feature | Process_TXT.py | Process_MD.py |
|---------|---------------|--------------|
| Basic heading detection | ✅ ATX-style (#) | ✅ ATX-style (#) |
| Heading hierarchy | ❌ | ✅ Parent paths |
| Code block extraction | ❌ | ✅ With language |
| YAML front matter | ❌ | ✅ Full parsing |
| Section-based chunking | ❌ Paragraph-based | ✅ Heading-based |
| List detection | ❌ | ✅ Ordered/unordered |
| Best for | Plain text, logs | Markdown docs |

**Use Process_MD.py when:**
- Processing technical documentation with code examples
- Need hierarchical structure (API docs, user guides)
- Want to extract code blocks for separate indexing
- Have YAML metadata in front matter

**Use Process_TXT.py when:**
- Processing plain text or simple markdown
- No code blocks or complex structure
- Want fastest processing (no parsing overhead)

### Why JSONL for RAG?

JSONL format is recommended for RAG because:

- **Section-Level Chunking**: Each section is a logical unit
- **Hierarchical Context**: Parent paths show document structure
- **Code Awareness**: Code blocks marked with language
- **Metadata Rich**: YAML front matter included in each record
- **Stream Processing**: Each line is independent
- **Easy to Combine**: Concatenate multiple files: `cat *.jsonl > all.jsonl`

### Example RAG Workflow

```bash
# 1. Process all Markdown documentation files
for md in docs/**/*.md; do
    ./Process_MD.py -i "$md" -o "processed/$(basename "$md" .md).jsonl" -f jsonl --extract-code
done

# 2. Process GitHub README files
for readme in repos/*/README.md; do
    repo_name=$(basename $(dirname "$readme"))
    ./Process_MD.py -i "$readme" -o "processed/readme_${repo_name}.jsonl" -f jsonl
done

# 3. Combine all processed files
cat processed/*.jsonl > all_markdown_docs.jsonl

# 4. Ingest into RAG system
python ingest_to_rag.py --input all_markdown_docs.jsonl --index documentation

# 5. Query with context-aware retrieval
python query_rag.py --query "How do I install the package?" --index documentation
```

### Dependencies

**No external dependencies required!**

Process_MD.py uses only Python standard library:
- `argparse` - Command-line argument parsing
- `json` - JSON encoding/decoding
- `re` - Regular expressions for parsing
- `unicodedata` - Unicode normalization
- `pathlib` - Path manipulation

### Performance

- **Speed**: ~20,000-50,000 lines/second (depends on complexity)
- **Memory**: Minimal - loads full file but processes incrementally
- **File Size**: No hard limit, tested with files up to 50MB+

### Supported Markdown Syntax

| Feature | Support | Notes |
|---------|---------|-------|
| ATX Headings (# through ######) | ✅ Full | With hierarchy tracking |
| Fenced Code Blocks (``` or ~~~) | ✅ Full | Language detection |
| YAML Front Matter (---) | ✅ Full | Key-value pairs |
| Lists (ordered & unordered) | ✅ Basic | Detected and extracted |
| Blockquotes (>) | ✅ Basic | Treated as content |
| Links [text](url) | ✅ Preserved | In text content |
| Bold/Italic | ✅ Preserved | In text content |
| Tables | ⚠️ Basic | Extracted as text |
| Images | ✅ Preserved | As markdown syntax |
| Setext Headings (underlined) | ❌ Not supported | Use ATX-style instead |

### Troubleshooting

**Problem**: "No content extracted from file"

**Solution**: Check if file is empty or only has YAML front matter:
```bash
cat file.md  # View contents
./Process_MD.py -i file.md -o output.txt --verbose
```

**Problem**: Headings not detected properly

**Solution**: Ensure headings use ATX-style (# through ######) with space after #:
```markdown
# Correct Heading
#Incorrect - needs space after #
```

**Problem**: Code blocks not extracted

**Solution**: Use `--extract-code` flag:
```bash
./Process_MD.py -i file.md -o output.jsonl -f jsonl --extract-code
```

**Problem**: YAML front matter not parsed

**Solution**: Ensure front matter is at the very start of file:
```markdown
---
title: My Doc
---

Content starts here...
```

### Use Cases

**1. API Documentation**
```bash
# Process API docs with code examples
./Process_MD.py -i api-reference.md -o api.jsonl -f jsonl --extract-code
```

**2. Technical Tutorials**
```bash
# Extract tutorials with hierarchical sections
./Process_MD.py -i tutorial.md -o tutorial.jsonl -f jsonl
```

**3. Project README Files**
```bash
# Batch process all README files in repositories
for readme in projects/*/README.md; do
    project=$(basename $(dirname "$readme"))
    ./Process_MD.py -i "$readme" -o "processed/${project}_readme.jsonl" -f jsonl
done
```

**4. Documentation Websites**
```bash
# Process static site documentation
for doc in docs/**/*.md; do
    ./Process_MD.py -i "$doc" -o "processed/$(basename "$doc" .md).jsonl" -f jsonl --extract-code
done
```

### Advanced Example: Code Search

Extract all code blocks for a code search index:

```bash
# 1. Process with code extraction
./Process_MD.py -i docs.md -o docs.jsonl -f jsonl --extract-code

# 2. Extract just code blocks using jq
cat docs.jsonl | jq -r 'select(.code_blocks != null) | .code_blocks[] | {language, code, section: .heading}' > code_index.jsonl
```

### Comparison with Other Tools

**vs Markdown Parsers (mistune, markdown-it):**
- Process_MD.py is optimized for RAG, not HTML rendering
- Preserves structure for chunking
- No external dependencies

**vs Process_TXT.py:**
- More Markdown-aware (hierarchy, code blocks)
- Better for technical documentation
- Slightly slower due to parsing

**vs pandoc:**
- Simpler, focused on RAG use case
- No external binaries required
- Faster for bulk processing

### Contributing

Contributions welcome! Please ensure:
- Type hints for all functions
- Docstrings in Google style
- Error handling with helpful messages
- Unit tests for new features

### License

MIT License - see LICENSE file for details

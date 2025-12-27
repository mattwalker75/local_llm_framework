# RAG Data Processing Tools - Quick Reference

Quick reference guide for processing different file types for RAG ingestion.

## Overview

Five specialized tools for converting different content types to JSONL format (recommended for RAG):

| Tool | Input Types | Best For |
|------|-------------|----------|
| **Process_PDF.py** | .pdf | Academic papers, reports, books |
| **Process_DOC.py** | .docx, .rtf | Business documents, formatted reports |
| **Process_TXT.py** | .txt, .log | Plain text, logs, simple files |
| **Process_MD.py** | .md | Markdown docs with code blocks, hierarchical structure |
| **Process_WEB.py** | URLs (http/https) | Web pages, articles, documentation |

## Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install pymupdf python-docx striprtf beautifulsoup4
```

## Quick Commands

### PDF Files
```bash
# Single file
./Process_PDF.py -i document.pdf -o output.jsonl -f jsonl

# Batch processing
for pdf in documents/*.pdf; do
    ./Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
done
```

### Word Documents
```bash
# Single file
./Process_DOC.py -i document.docx -o output.jsonl -f jsonl

# Batch processing
for doc in documents/*.docx; do
    ./Process_DOC.py -i "$doc" -o "processed/$(basename "$doc" .docx).jsonl" -f jsonl
done
```

### Text Files
```bash
# Single file
./Process_TXT.py -i document.txt -o output.jsonl -f jsonl

# Batch processing
for txt in documents/*.txt; do
    ./Process_TXT.py -i "$txt" -o "processed/$(basename "$txt" .txt).jsonl" -f jsonl
done
```

### Markdown Files
```bash
# Single file (with full structure parsing and code extraction)
./Process_MD.py -i README.md -o output.jsonl -f jsonl --extract-code

# Batch processing
for md in documents/*.md; do
    ./Process_MD.py -i "$md" -o "processed/$(basename "$md" .md).jsonl" -f jsonl --extract-code
done
```

### Web Pages
```bash
# Single URL
./Process_WEB.py -i https://example.com/article -o output.jsonl -f jsonl --detect-headings

# Batch processing from URL list
while read url; do
    filename=$(echo "$url" | sed 's|https://||; s|http://||; s|[^a-zA-Z0-9]|_|g')
    ./Process_WEB.py -i "$url" -o "processed/${filename}.jsonl" -f jsonl --detect-headings
    sleep 2  # Be polite to servers
done < urls.txt
```

## Complete RAG Workflow

```bash
# 1. Create output directory
mkdir -p processed

# 2. Process all document types
for pdf in documents/*.pdf; do
    ./Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
done

for doc in documents/*.docx; do
    ./Process_DOC.py -i "$doc" -o "processed/$(basename "$doc" .docx).jsonl" -f jsonl
done

for txt in documents/*.txt; do
    ./Process_TXT.py -i "$txt" -o "processed/$(basename "$txt" .txt).jsonl" -f jsonl
done

for md in documents/*.md; do
    ./Process_MD.py -i "$md" -o "processed/$(basename "$md" .md).jsonl" -f jsonl --extract-code
done

# If you have URLs
while read url; do
    filename=$(echo "$url" | sed 's|https://||; s|http://||; s|[^a-zA-Z0-9]|_|g')
    ./Process_WEB.py -i "$url" -o "processed/${filename}.jsonl" -f jsonl --detect-headings
    sleep 2
done < urls.txt

# 3. Combine all JSONL files
cat processed/*.jsonl > all_documents.jsonl

# 4. Ingest into your RAG system
# (Replace with your actual ingestion command)
python your_rag_ingest.py --input all_documents.jsonl --index my_knowledge_base
```

## Output Format

All tools produce consistent JSONL output (one JSON record per line):

### PDF Output
```json
{"title": "Report", "author": "John", "page_number": 1, "text": "...", "char_count": 1234}
```

### Word Document Output
```json
{"title": "Report", "author": "John", "para_number": 1, "text": "...", "is_heading": false, "style": "Normal", "char_count": 234}
```

### Text Output
```json
{"source_file": "doc.txt", "encoding": "utf-8", "para_number": 1, "text": "...", "is_heading": false, "heading_level": 0, "char_count": 234, "line_count": 3}
```

### Markdown Output
```json
{"source_file": "README.md", "section_number": 1, "type": "heading", "level": 1, "heading": "Introduction", "parent_path": "", "content": "...", "char_count": 234, "line_count": 3}
```

### Web Page Output
```json
{"url": "https://example.com", "domain": "example.com", "title": "Title", "para_number": 1, "text": "...", "is_heading": false, "heading_level": 0, "element_type": "p", "char_count": 234}
```

## Common Options

All tools support these common flags:

- `-i, --input` - Input file/URL (required)
- `-o, --output` - Output file (required)
- `-f, --format` - Output format: `text`, `json`, or `jsonl` (default: `text`)
- `-v, --verbose` - Show detailed progress
- `-h, --help` - Show help message

## Special Options

### Process_PDF.py
- `--keep-page-numbers` - Keep page numbers in extracted text

### Process_DOC.py
- `--preserve-structure` - Preserve document structure in text output

### Process_TXT.py
- `--detect-headings` - Detect markdown-style headings (# through ######)

### Process_MD.py
- `--extract-code` - Extract code blocks separately (nested in sections)

### Process_WEB.py
- `--detect-headings` - Detect HTML headings (h1-h6)
- `--user-agent STRING` - Custom User-Agent header
- `--timeout SECONDS` - Request timeout (default: 30)

## Why JSONL Format?

JSONL (JSON Lines) is recommended for RAG because:

1. **Stream Processing** - Read one line at a time (low memory)
2. **Parallel Processing** - Each line is independent
3. **Source Attribution** - Each chunk includes metadata for citations
4. **Structure Awareness** - Headings marked for better chunking
5. **Easy to Combine** - Just concatenate files: `cat *.jsonl > all.jsonl`

## Dependencies Summary

| Tool | Required Packages | Standard Library Only? |
|------|------------------|----------------------|
| Process_PDF.py | `pymupdf` | ❌ |
| Process_DOC.py | `python-docx`, `striprtf` | ❌ |
| Process_TXT.py | None | ✅ |
| Process_MD.py | None | ✅ |
| Process_WEB.py | `beautifulsoup4`, `requests` | ❌ |

## Performance Tips

1. **Batch Processing** - Process multiple files in parallel using `xargs` or `parallel`
2. **Large Files** - All tools stream/process incrementally (low memory)
3. **Web Scraping** - Always add delays (`sleep 2-5`) between requests
4. **Encoding** - Process_TXT.py auto-detects encoding (UTF-8, Latin-1, etc.)

## Troubleshooting

### All Tools
- Run with `--verbose` flag to see detailed progress
- Check output file permissions if write fails
- Ensure input file/URL exists and is accessible

### Process_PDF.py
- **No text extracted**: PDF may be scanned images (needs OCR first)
- Install: `pip install pymupdf`

### Process_DOC.py
- **.doc files not supported**: Convert to .docx first using LibreOffice
- Install: `pip install python-docx striprtf`

### Process_TXT.py
- **Encoding errors**: Auto-detection usually works, or manually convert with `iconv`
- No external dependencies needed!

### Process_MD.py
- **Code blocks not extracted**: Use `--extract-code` flag
- **Headings not detected**: Ensure ATX-style (# ) with space after #
- No external dependencies needed!

### Process_WEB.py
- **403 Forbidden**: Use `--user-agent` to set a browser User-Agent
- **429 Rate Limited**: Add delays between requests (`sleep 5`)
- **JavaScript sites**: Won't work (static HTML only)
- Install: `pip install beautifulsoup4` (requests already in requirements)

## Full Documentation

See [README.md](README.md) for complete documentation, examples, and advanced usage.

## License

MIT License - All tools are open source and free to use.

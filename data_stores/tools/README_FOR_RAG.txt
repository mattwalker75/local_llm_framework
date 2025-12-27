
Best to use for RAG:

PDF:
./data_stores/tools/Process_PDF.py -i document.pdf -o output.jsonl -f jsonl

WORD:
./data_stores/tools/Process_DOC.py -i document.docx -o output.jsonl -f jsonl

TEXT:
./data_stores/tools/Process_TXT.py -i document.txt -o output.jsonl -f jsonl

WEB:
./data_stores/tools/Process_WEB.py -i https://example.com/article -o article.jsonl -f jsonl --detect-headings


EXAMPLE BATCH:

for pdf in documents/*.pdf; do
    ./data_stores/tools/Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
done

----------------------------------------------

Eyeball text after it is converted to JSONL and make sure it looks good and there is no empty text slots.

Pick an embedding model to use:
   age-small-en-v1.5 for general text
   age-code-v1 for code

Generate local vector store using the embedding model and .jsonl data



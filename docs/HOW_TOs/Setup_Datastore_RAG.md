
# Setup a Data Store

This document explains how to get text data, such as a large PDF file, and load it into a LLM Data Store, also known as a RAG Vector Store, for the LLM to access.  This enables you to ask the LLM questions directly about the document, and it will return the requested information.  You can have multiple Data Stores connected to the LLM at one time.

---

## Initial Setup

### Download embedding models from https://huggingface.co
- Run the following script to download the embedding models to `data_stores/embedding_models`
```bash
cd bin/tools/data_store
./download_embedding_models.py
```

---

## Convert files to JSONL format

### Find the documentats that you want to use with the LLM
- Select and review the documents 
- The following document types are currently supported
   - PDF
   - Microsoft Word (DOC/DOCX)
   - TXT
   - MD
   - Web Site URL text content

### Convert files to JSONL so they can be loaded into a Data Store
- Convert PDF files ( .pdf )
```bash
cd bin/tools/data_store
./Process_PDF.py -i document.pdf -o output.jsonl -f jsonl
```
- Convert Microsoft Word Docs and Docx ( .doc / .docx )
```bash
cd bin/tools/data_store
./Process_DOC.py -i document.docx -o output.jsonl -f jsonl
```
- Convert Text files ( .txt )
```bash
cd bin/tools/data_store
./Process_TXT.py -i document.txt -o output.jsonl -f jsonl
```
- Convert Markdown files ( .md )
```bash
cd bin/tools/data_store
./Process_MD.py -i README.md -o output.jsonl -f jsonl
```
- Convert the text content of a Web Site
```bash
cd bin/tools/data_store
./Process_WEB.py -i https://example.com/article -o article.jsonl -f jsonl --detect-headings
```
- Example of how to batch process multiple files of the same type
```bash
cd bin/tools/data_store
for pdf in documents/*.pdf; do
   ./Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
done
```
### Review the generated JSONL files
- Review the data in the newly generated JSONL files and make sure it looks good and there are no "oddities".  
- Run the following data verification script against the JSONL file
```bash
cd bin/tools/data_store
./Validate_JSONL.py -i output.jsonl
```

---

## Pick and Embedding Model to encode the JSONL data

Now it is time to preparer for the use of those embedding models that you downloaded earlier.

### Pick an Embedding Model
- Pick an embedding model to load the JSONL data based on the type of data you have
   - `sentence-transformers/all-MiniLM-L6-v2`
      - Fast, lightweight ( Good for computers with minimal resources )
      - Make note of the following parameters
         - Select a chunk size:  800 - 1000
         - Select a overlap:  150 - 200
   - `sentence-transformers/all-mpnet-base-v2`
      - High-quality general use ( Preferred for most data )
      - Make note of the following parameters
         - Select a chunk size:  1200 - 1500
         - Select a overlap:  200 - 250
   - `sentence-transformers/multi-qa-mpnet-base-cos-v1`
      - Q&A optimized ( Good for Question/Answer type of data )
      - Make note of the following parameters
         - Select a chunk size:  1200 - 1500
         - Select a overlap:  200 - 250
   - `jinaai/jina-embeddings-v2-base-code`
      - Programming and Coding ( Good for programming languages )
      - Make note of the following parameters
         - Select a chunk size:  2000 - 4000
         - Select a overlap:  400 - 600

### Record what you selected above
- Pick the model to use along with the associated `chunk size` and `overlap`
   - It is fine to pick a low value for those items as long as they are in the proper range

---

## Generate Data Store and update Configs

### Generate the Data Store ( Vector Store ) from the JSONL files 
<U>IMPORTANT</U>:  Due to how the terminal environment may process the command, you will want to put the command in a standalone temp script to execute, such as the followoing:
```bash
bin/tools/data_store/CREATE_VECTOR_STORE.sh
```
- Get the name of the `embedding model` that you used along with the `chunk size` and `overlap` that you selected
- Run the following command to convert a single JSON file into a Data Store
```bash
cd bin/tools/data_store
./Create_VectorStore.py -i document.jsonl -o MY_DATA_STORE --model MODEL_NAME --chunk-size CHUNK_SIZE --overlap OVERLAP
```
- Here is an example command
```bash
./Create_VectorStore.py -i document.jsonl -o my_doc_store --model sentence-transformers/all-mpnet-base-v2 --chunk-size 1200 --overlap 200
```
- Run the following to convert a directory of JSONL files into a single Data Store
```bash
cd bin/tools/data_store
./Create_VectorStore.py -i data_dir -o my_vectorstore --model sentence-transformers/all-mpnet-base-v2 --chunk-size 1200 --overlap 200
```
- Remember to update the CREATE_VECTOR_STORE.sh script to run the above commands

NOTE:  The Data Store ( Also called a RAG Vector Store ) is a created directory with generated files in it.  That directory can be moved wherever you want.  The default location to put them is in `data_stores/vector_stores`

### Make note of Embedding Dimensions
- Get the notes you made of the Embedding Model that you used up above.  You will want to make note of this extra value and call it the `embedding dimension`
   - sentence-transformers/all-MiniLM-L6-v2:  384
   - sentence-transformers/all-mpnet-base-v2:  768
   - sentence-transformers/multi-qa-mpnet-base-cos-v1:  768
   - jinaai/jina-embeddings-v2-base-code:  768

### Select an Index type to use
- A large majority of the time, you will use `IndexFlatIP`
- Below are the options to choose from:
   - NOTE:  The number of Vectors is the same as the number of text chunks
   - IndexFlatIP
      - Exact cosine similarity search (inner product with normalized vectors). 
      - Best for <100K vectors. 100% accurate, slower.
   - IndexFlatL2
      - Exact L2 (Euclidean) distance search. 
      - Best for <100K vectors. 100% accurate, slower.
   - IndexIVFFlat
      - Approximate search with inverted file index. 
      - Best for >100K vectors. Faster, slightly less accurate.
   - IndexHNSWFlat
      - Hierarchical graph-based approximate search. 
      - Best for large datasets needing speed. High memory, very fast.
   - IndexIVFPQ
      - Compressed approximate search with product quantization. 
      - Best for millions of vectors. Low memory, approximate.


### Update the Data Store Registry file
Updating the Data Store Registry is how we make the LLF tool aware of the Data Stores that it can use.
- The file you will need to edit:  `data_stores/data_store_registry.json`     
- The following is the list of required entries to create/edit in the file
   - "name": "A_NAME_THAT_MAKES_SENSE",
   - "display_name": "A Name That Makes Sense",
   - "description": "Something that explains the data in this",
   - "attached": true/false,
   - "vector_store_path": "data_stores/vector_stores/A_NAME_THAT_MAKES_SENSE",
   - "embedding_model": "Name of the Embedding Model that you used",
   - "embedding_dimension": Embedding Diminsion of Embedding Model in this Doc,
   - "index_type":  Must likely it will be "IndexFlatIP",

- The follwowing is an example of a configuration only using the required parameters
```JSON
{
  "version": "1.0",
  "last_updated": "2025-12-26",
  "data_stores": [
    {
      "name": "app_support_docx",
      "display_name": "App Support",
      "description": "Application support reference material",
      "attached": false,
      "vector_store_path": "data_stores/vector_stores/app_support_docx",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dimension": 768,
      "index_type": "IndexFlatIP"
    }
  ]
}
```
- The following is the list of optional entries to create/edit in the file
   - "model_cache_dir": "data_stores/embedding_models",
   - "top_k_results": 5,
      - 5: text / 8: code and tech content / 10: massive overviews
   - "similarity_threshold": 0.3,
      - Adjust between 0.25 and 0.35 if you are not getting expected data
   - "max_context_length": 4000,
      - 4000-5000: most cases / 6000-8000: for code and tech content
               - 4000 - 5000 for most use cases
               - 6000 - 8000 for code and technical content
   - "created_date": "2025-12-26",
   - "num_vectors": Read following content,
      - Total number of text chunks created
         - Go to the RAG Vector Store directory
         - Look at the `config.json` file and look for `num_vectors`
   - "metadata": {
      - "source_type": "documentation",
      - "content_description": "General documentation and user guides",
      - "search_mode": "semantic"
         - Typically keep set to semantic
            - semantic - for embedding-based similarity
            - keyword - text matching only
            - hybrid - for semantic and keyword

- The follwowing is an example of a configuration using all of the parameters
```JSON
{
  "version": "1.0",
  "last_updated": "2025-12-26",
  "data_stores": [
    {
      "name": "app_support_docx",
      "display_name": "App Support",
      "description": "Application support reference material",
      "attached": false,
      "vector_store_path": "data_stores/vector_stores/app_support_docx",
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "embedding_dimension": 768,
      "index_type": "IndexFlatIP",
      "model_cache_dir": "data_stores/embedding_models",
      "top_k_results": 5,
      "similarity_threshold": 0.3,
      "max_context_length": 4000,
      "created_date": "2025-12-26",
      "num_vectors": 50,
      "metadata": {
        "source_type": "documentation",
        "content_description": "General documentation",
        "search_mode": "semantic"
      }
    }
  ]
}
```

---

## Start Using the Data Store

### Test that the LLF environment sees the Data Store
- Run the following list command and verify that you see your new Data Store
```bash
cd bin
./llf datastore list
```
NOTE:  If you don't see your Data Store, then go back and review your `data_store_registry.json` updates.

### Enable your Data Store
- Run the following command to enable your Data Store 
```bash
cd bin
./llf datastore attach DATA_STORE_NAME
```

### Test out that the LLM can use it
- Run the following command to start an interactive chat with the LLM
```bash
cd bin
./llf chat
```
- If you are asked to start up the server, then type `y`
- Ask the LLM a few specific questions that would only be in the Data Store
   - For example, if this document was part of the data, you could ask the following test questions
      - What is the command to convert PDF files to JSONL?
      - What are the required entries for the data_store_registry.json file?

### Disable your Data Store
- You can optionally run the following command to disable your Data Store if you want
```bash
cd bin
./llf datastore detach DATA_STORE_NAME
```





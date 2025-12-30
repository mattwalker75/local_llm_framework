
This is the steps to get data and store it in RAG to be used by the LLM

-------------------------------------------------------------------


Optionally download embedding models before starting:
   - Run the following script
      - ./download_embedding_models.py


Find documents that you want to load into the LLM:
   - Select and review documents that you want to laod into the LLM
   - The following document types are support
      - PDF
      - Microsoft Word
      - TXT
      - Web Site URL's


Convert files to a data format that can be loaded into RAG:
   - PDF:
      - ./tools/Process_PDF.py -i document.pdf -o output.jsonl -f jsonl
   - WORD:
      - ./tools/Process_DOC.py -i document.docx -o output.jsonl -f jsonl
   - TEXT:
      - ./tools/Process_TXT.py -i document.txt -o output.jsonl -f jsonl
   - WEB:
      - ./tools/Process_WEB.py -i https://example.com/article -o article.jsonl -f jsonl --detect-headings
   - EXAMPLE BATCH:
      - for pdf in documents/*.pdf; do
         ./Process_PDF.py -i "$pdf" -o "processed/$(basename "$pdf" .pdf).jsonl" -f jsonl
        done


Review generated output files with the .jsonl extention:
   - Look at the .jsonl files and ensure the data looks good and there are no 
     empty text slots in the file
   - Use the Validat_JSONL.py script to help validate
      - ./Validate_JSONL.py -i output.jsonl


Pick an embedding model to load the .jsonl data into a new RAG datastore
   - sentence-transformers/all-MiniLM-L6-v2
      - Fast, lightweight ( Good for computers with minimal resources )
      - Make note of the following parms
         - Select a chunk size:  800 - 1000
         - Select a overlap:  150 - 200
   - sentence-transformers/all-mpnet-base-v2
      - High-quality general ( Preferred to use with most data )
      - Make note of the following parms
         - Select a chunk size:  1200 - 1500
         - Select a overlap:  200 - 250 
   - sentence-transformers/multi-qa-mpnet-base-cos-v1
      - Q&A optimized ( Good for Question / Answer type of data )
      - Make note of the following parms
         - Select a chunk size:  1200 - 1500
         - Select a overlap:  200 - 250 
   - jinaai/jina-embeddings-v2-base-code
      - Code & 30+ languages ( Good for programming languages )
      - Make note of the following parms
         - Select a chunk size:  2000 - 4000
         - Select a overlap:  400 - 600


Make note of which embedding model to use and associated values
   - Make note of the following from the above section
      - Model you are going to use
         - We will pick:  sentence-transformers/all-mpnet-base-v2
            - We just picked this for our following examples
      - Chunk size based on model recommondation
         - We will pick:  1200
            - We just picked this for our following examples
      - Overlap which is based on the chunk size
         - We will pick:  200 
            - We just picked this for our following examples


Generate local vector store using the embedding model and .jsonl data
   - IMPORTANT:  Due to how the terminal environment may process the command, you will want to
                 put the command in a stand along temp script to execute
                   - Update and use the following script:  CREATE_VECTOR_STORE.sh
   - The Vector Store will consist of a directory of data.  You can move the generated
     directory to any location you want but do not modify any of the contents
   - Convert a single small file not worried about chunk size
      - ./Create_VectorStore.py -i document.jsonl -o my_vectorstore --model sentence-transformers/all-mpnet-base-v2
   - Convert a single massive file 
      - ./Create_VectorStore.py -i document.jsonl -o my_vectorstore --model sentence-transformers/all-mpnet-base-v2 --chunk-size 1200 --overlap 200
   - Convert a directory of .jonsl files 
      - ./Create_VectorStore.py -i data_dir -o my_vectorstore --model sentence-transformers/all-mpnet-base-v2 --chunk-size 1200 --overlap 200
   - Update the CREATE_VECTOR_STORE.sh script with the long command that you will want to run
   - Execute the CREATE_VECTOR_STORE.sh script
 

Update the data_store_registry.json file
   - Make note of the following data
      - Embedding Dimension values based on model you used for encoding
         - sentence-transformers/all-MiniLM-L6-v2:  384
         - sentence-transformers/all-mpnet-base-v2:  768
         - sentence-transformers/multi-qa-mpnet-base-cos-v1:  768
         - jinaai/jina-embeddings-v2-base-code:  768
      - Select an Index Type
         - A large majority of the time:  IndexFlatIP
         - Below are the options to choose from:
            - NOTE:  The number of Vectors is the same as the number of text chunks
            - IndexFlatIP
               - Exact cosine similarity search (inner product with normalized vectors). 
                 Best for <100K vectors. 100% accurate, slower.
            - IndexFlatL2
               - Exact L2 (Euclidean) distance search. Best for <100K vectors. 
                 100% accurate, slower.
            - IndexIVFFlat
               - Approximate search with inverted file index. Best for >100K vectors. 
                 Faster, slightly less accurate.
            - IndexHNSWFlat
               - Hierarchical graph-based approximate search. Best for large datasets 
                 needing speed. High memory, very fast.
            - IndexIVFPQ
               - Compressed approximate search with product quantization. Best for millions 
                 of vectors. Low memory, approximate.
   - Follow the data structure of the data_store_registry.json and add your new data store
      - The following are the required parameters
         "name": "example_docs",
            - A name that makes sense
         "display_name": "Example Documentation Store",
            - A clean name that will be displayed
         "description": "Sample RAG vector store for documentation and guides",
            - A description of the data
         "enabled": false,
            - This is used to enable or disable the use of the RAG data store
         "vector_store_path": "data_stores/vector_stores/example_docs",
            - Physical directory location of the generated RAG data store
         "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            - The model used for encoding
         "embedding_dimension": 384,
            - The embedding dimensions that is based on the model you used
         "index_type": "IndexFlatIP",
            - Just keep this set to IndexFlatIP
      - The following are optional parameters
         "model_cache_dir": "data_stores/embedding_models",
            - Location where the downloaded embedding models are located
         "top_k_results": 5,
            - Number of most similar chunks to retrieve from the vector store
               - 5 for most text 
               - 8 for queries about programming or code
               - 10 for large summarizations and overviews
         "similarity_threshold": 0.3,
            - Helps detemine which data gets filtered out of searches
               - Keep betwen 0.25 - 0.35
         "max_context_length": 4000,
            - Maximum amount of characters from retrieved chunks to send to LLM
               - 4000 - 5000 for most use cases
               - 6000 - 8000 for code and technical content
         "created_date": "2025-12-26",
            - When the vector store was created
         "num_vectors": 0,
            - Total number of text chunks created
               - Go to the RAG Vector Store directory
                  - Look at the config.json file
                     - Look at the num_vectors value and use it 
         "metadata": {
           "source_type": "documentation",
              - Type of data ( used for organization purposes )
           "content_description": "General documentation and user guides",
              - Quick description of what is in this Vector Store
           "search_mode": "semantic"
              - Typically keep set to semantic
              - Type of search to perform
                 semantic - for embedding-based similarity
                 keyword - text matching only
                 hybrid - for semantic and keyword
         }





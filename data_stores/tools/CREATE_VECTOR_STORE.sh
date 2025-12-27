#
#  Run the Create_VectorStore.py in a script to prevent the shell
#  from jacking up the file pathing
#
./Create_VectorStore.py -i "/MY_DIRECTORY/local_llm_framework/data_stores/TEST_DATA/test_PDF.jsonl" -o "/MY_DIRECTORY/local_llm_framework/data_stores/RAG/test_pdf" --model "sentence-transformers/all-mpnet-base-v2" --chunk-size 1200 --overlap 200 -v

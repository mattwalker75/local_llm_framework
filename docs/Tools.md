
## Tools in the `bin/tools` Directory

This document will review the other commands and programs that you can use and how to use them besides the `llf` command.  All the commands that we are going to discuss are in the `bin/tools` directory or one of its sub-directories.

- convert_huggingface_llm_2_gguf.sh
   - This script is used to take an LLM model that is downloaded from https://huggingface.co via the `llf model download --huggingface-model MODEL/NAME` and convert it to a GGUF formatted LLM model.  The `ollama.ccp` backend OpenAI server that you downloaded as part of the install process that has the models mapped to it only supports models that are in the GGUF format.
   - After you download a model, take a look at it in the `models` directory
   ```bash
   # cd models
   # ls
   Qwen--Qwen3-Coder-30B-A3B-Instruct	README.md
   ```
   - You will want to convert that model to a GGUF format like this
   ```bash
   ./convert_huggingface_llm_2_gguf.sh -f -s Qwen--Qwen3-Coder-30B-A3B-Instruct -d Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF
   ```
   - The above command will take a while to run.  After it is done, you can delete the original `Qwen--Qwen3-Coder-30B-A3B-Instruct` because you will be using the newly created `Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF` model with your local server.
   - All the document you need is here:  `./convert_huggingface_llm_2_gguf.sh -h`

- create_memory.py
   - Creates new memory modules in the `memory` directory
   - NOTE:  This has been replaced with "llf memory create" command
   - Run the following command to create a new memory module
   ```bash
   ./create_memory.py my_test_memory
   ```
   - A new memory module is now created in the `memory` directory and the `memory/memory_registry.json` registry file is fully updated.
   - You can run the `llf memory` commands to test out the new memory module

- test_speech2text.py
   - Test if your computer supports the Speech-To-Text `module`, which is located in `modules/speech2text`.
   - Run the following command to perform the test
   ```bash
   ./test_speech2text.py
   ```
   - View the optional advance parameters you can use
   ```bash
   ./test_speech2text.py -h
   ```

- test_text2speech.py
   - Test if your computer supports the Text-To-Speech `module`, which is located in `modules/text2speech`.
   - Run the following command to perform the test
   ```bash
   ./test_text2speech.py "this is a test"
   ```
   - View the optional advance parameters you can use
   ```bash
   ./test_text2speech.py -h
   ```

---

### Tools in the `tools/data_store` directory
All of these tools are covered in detailed in the `Use LLM as your personal documentation reference tool` How To documentation.

- CREATE_VECTOR_STORE.sh
   - A temp script you can use to build your `Create_VectorStore.py` command in to execute

- Create_VectorStore.py
   - Takes the content of JSONL documents and builds a Data Store module ( RAG Vector Store )
   - Run the following for help documentation
   ```bash
   ./Create_VectorStore.py
   ```
   - Here is an example running the tool
   ```bash
   ./Create_VectorStore.py -i "/MY_DIRECTORY/local_llm_framework/data_stores/TEST_DATA/test_PDF.jsonl" -o "/MY_DIRECTORY/local_llm_framework/data_stores/vector_stores/test_pdf" --model "sentence-transformers/all-mpnet-base-v2" --chunk-size 1200 --overlap 200 -v
   ```
   - The new Data Store will to built in `data_stores/vector_stores`.

- download_embedding_models.py
   - This download the Embedding Models needed by the Data Stores ( RAG Vector Stores )
   - They are downloaded to `data_stores/embedding_models`.

- Process_DOC.py
   - Converts Microsoft .doc and .docx files to JSONL data files that are used to build out the Data Stores for LLM usage
   - Run the following for help:  `./Process_DOC.py -h`

- Process_MD.py
   - Converts Mark Down files to JSONL data files that are used to build out the Data Stores for LLM usage 
   - Run the following for help:  `./Process_MD.py -h`

- Process_PDF.py
   - Converts PDF files to JSONL data files that are used to build out the Data Stores for LLM usage
   - Run the following for help:  `./Process_PDF.py -h`

- Process_TXT.py
   - Converts TXT files to JSONL data files that are used to build out the Data Stores for LLM usage
   - Run the following for help:  `./Process_TXT.py -h`

- Process_WEB.py
   - Converts the text from websites to JSONL data files that are used to build out the Data Stores for LLM usage
   - Run the following for help:  `./Process_WEB.py -h`
   - Example extracting data from a web site
   ```bash
   ./Process_WEB.py -i https://en.wikipedia.org/wiki/Superman -o matt.jsonl -f jsonl
   ```

- Validate_JSONL.py
   - Validates the data in the JSONL format to ensure the data structure is proper and nothing is missing.
   - Run the following for help:  `./Validate_JSONL.py -h`


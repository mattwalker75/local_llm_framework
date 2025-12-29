
# Install and Setup

## INSTALL AND SETUP llama.cpp  

NOTE:  THIS IS NEEDED IF YOU ARE GOING TO RUN LLM MODELS LOCALLY

- Downlaod the llama.cpp code repo
   ```bash
   git clone https://github.com/ggml-org/llama.cpp.git
   ```

- Build the llama server
   ```bash
   cd llama.cpp
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```

- Verify the newly compiled llama server works
   ```bash
   ./bin/llama-server --version
   ```

- Your newly compiled Llama Server is located in the following location
   ```bash
   llama.cpp/build/bin/llama-server
   ```

- You will want to verify that the following tools exist because they will be needed to convert downloaded LLM models to GGUF format so they can run on the Llama Server
   ```bash
   llama.cpp/convert_hf_to_gguf.py
   llama.cpp/build/bin/llama-quantize
   ```

## DOWNLOAD AND SETUP THE LOCAL LLM FRAMEWORK (llf) ENVIRONMENT

- Download the Local LLM Framework (llf) code repo
   ```bash
   git clone https://github.com/mattwalker75/local_llm_framework.git
   ```

- Change to directory
   ```bash
   cd local_llm_framework
   ```

- Create Python virtual environment
   ```bash
   python -m venv llf_venv
   ```

- Change over to the virtual environment
   ```bash
   source llf_venv/bin/activate
   ```
   NOTE:  Remember to always be in the virtual environment

- Verify you are in the virtual environment
   ```bash
   echo $VIRTUAL_ENV
   ```

- Install all the required Python packages
   ```bash
   pip install -e .
   ```

- Test the CLI environment
   ```bash
   cd bin
   ./llf --version
   ./llf -h
   ```
 
- Test the GUI environment
   ```bash
   cd bin
   ./llf gui
   ```
    - Click on "Shutdown GUI"   


## CONNECT THE LOCAL LLM FRAMEWORK (llf) ENVIRONMENT TO THE LLAMA.CPP 

NOTE:  This is only needed if you are using llama.cpp to run local LLM models

- Modify the following file:  `local_llm_framework/configs/config.json`<br>
  Ensure `llama_server_path` is pointing to the llama-server binary.<br>
  EXAMPLE:<br>
      ```bash
      {
        "local_llm_server": {
          "llama_server_path": "../llama.cpp/build/bin/llama-server",
          "server_host": "127.0.0.1",
          "server_port": 8000,
      ```

- Modify the following file:  `local_llm_framework/bin/tools/convert_huggingface_llm_2_gguf.sh`
  Modify the following parameters:<br>
   - Update the below parameter to point to `llama.cpp/convert_hf_to_gguf.py`
      ```bash
         #  Convert HuggingFace LLM to GGUF format for Llama
         CONVERT_TOOL="../../../llama.cpp/convert_hf_to_gguf.py"
      ```

   - Update the below parameter to point to `llama.cpp/build/bin/llama-quantize`
      ```bash
         #  Convert HuggingFace LLM to GGUF format for Llama
         #  Quantizing the GGUF converted LLM
         QUANTIZER="../../../llama.cpp/build/bin/llama-quantize"
      ```


## DOWNLOAD YOUR FIRST LLM MODEL AND CONVERT TO GGUF FORMAT FOR THE LLAMA SERVER
NOTE:  This is only needed if you are using llama.cpp to run local LLM models

- LLM Model download information
   - We will be downloading LLM Models from the following website
      - https://huggingface.co

   - We will go through the process to download and convert the following Model
      - https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct

Change to the main bin directory:
   cd local_llm_framework/bin

Run the following command to download the above mentioned LLM Model:
   ./llf model download --huggingface-model Qwen/Qwen3-Coder-30B-A3B-Instruct

Run the following command to very the image downloaded successfully:
   NOTE:  The models are downloaded here:  local_llm_framework/models
      ./llf model list
      ./llf model info --model Qwen/Qwen3-Coder-30B-A3B-Instruct

Get the directory name of the newly downloaded LLM model
   cd local_llm_framework/models
   ls
   < MAKE NOTE OF THE DIRECTORY:  Qwen--Qwen3-Coder-30B-A3B-Instruct >

Run the following commands to convert  the downloaded image to a GGUF format:
   cd local_llm_framework/bin/tools
   ./convert_huggingface_llm_2_gguf.sh -s Qwen--Qwen3-Coder-30B-A3B-Instruct -d Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF
      NOTE:  If you want to replace an existing Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF, then
             you can use the -f parameter

Collect converted LLM Model information:
   cd local_llm_framework/bin
   ./llf model list
      NOTE:  You should see your new model named Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF
   ./llf model info --model Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF
      NOTE:  Look at the "Path" and make note of the directory name in the "models" directory.
             EXAMPLE NAME: Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF
      NOTE:  Look at the "Path" and look at the content of that directory.  Make note of the .guff file name.
             EXAMPLE NAME:  Qwen--Qwen3-Coder-30B-A3B-Instruct_f16_q5_K_M.gguf

Update the config.json file with the collected LLM Model information
   Modify the following file:  local_llm_framework/configs/config.json
   Ensure the "model_dir" is set to the directory the model is located in in the "models" directory.
   Ensure the "gguf_file" is set to the .gguf model file name in the above mentioned directory.
   EXAMPLE:
      {
        "local_llm_server": {
          "llama_server_path": "../llama.cpp/build/bin/llama-server",
          "server_host": "127.0.0.1",
          "server_port": 8000,
          "healthcheck_interval": 2.0,
          "model_dir": "Qwen--Qwen3-Coder-30B-A3B-Instruct-GGUF",
          "gguf_file": "Qwen--Qwen3-Coder-30B-A3B-Instruct_f16_q5_K_M.gguf"
        },

Run the following commands to start the local Llama server:
   cd local_llm_framework/bin
   ./llf server start --daemon

--------------------------------------------------

UPDATE THE LLM ENDPOINT CLIENT CONFIGURATION IF USING LOCAL LLAMA SERVER:

Update the config.json file with the LLM endpoint client configuration:
   Modify the following file:  local_llm_framework/configs/config.json
        "llm_endpoint": {
          "api_base_url": "http://127.0.0.1:8000/v1",
          "api_key": "EMPTY",

Run the following commands to get a list of models:
   cd local_llm_framework/bin
   ./llf model list
      EXAMPLE:  Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF

Get the model that you want to use from the above command and update the config.json:
   Modify the following file:  local_llm_framework/configs/config.json
   You will want to update the "model_name" with the model you want to use from the
   "./llf server list_models" command:
     "llm_endpoint": {
       "api_base_url": "http://127.0.0.1:8000/v1",
       "api_key": "EMPTY",
       "model_name": "Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF"
     },

--------------------------------------------------

UPDATE THE LLM ENDPOINT CLIENT CONFIGURATION IF USING A REMOTE SERVER:

Update the config.json file with the LLM endpoint client configuration:
   Modify the following file:  local_llm_framework/configs/config.json
      For OpenAI ( ChatGPT ):
        "llm_endpoint": {
          "api_base_url": "https://api.openai.com/v1",
          "api_key": "YOUR-OPENAI-API-KEY",
      For Anthropic ( Claude ):
        "llm_endpoint": {
          "api_base_url": "https://api.anthropic.com/v1",
          "api_key": "YOUR-ANTHROPIC-API-KEY",

Run the following commands to get a list of models:
   cd local_llm_framework/bin
   ./llf server list_models
      EXAMPLE:  chatgpt-2

Get the model name that you want to use from the above command and update the config.json:
   Modify the following file:  local_llm_framework/configs/config.json
   You will want to update the "model_name" with the model you want to use from the
   "./llf server list_models" command:
     "llm_endpoint": {
       "api_base_url": "https://api.openai.com/v1",
       "api_key": "YOUR-OPENAI-API-KEY",
       "model_name": "chatgpt-2"
     },

--------------------------------------------------

VERIFY THE CLIENT IS WORKING:

Run the following commands to test that the LLM Model is working:
   cd local_llm_framework/bin
   ./llf chat --cli "this is a test"

If you get errors about unsupported parameters, then you will want to do the following:
   Make note of the unsupported parameters.
   Modify the following file:  local_llm_framework/configs/config.json
   Remove the unsupported parameters from the following section:
     "inference_params": {
       "temperature": 0.7,
       "max_tokens": 2048,
       "top_p": 0.9,
       "top_k": 50,
       "repetition_penalty": 1.1
     }

Re-run the "./llf chat --cli" test

--------------------------------------------------

SOME HELPFUL FILE LOCATIONS ( cd local_llm_framework )

 bin                 Main program location
   tools             Specialized tools
 configs             Configuration files
   config_examples   Example config files
 llf_venv            Virtual Environment
 models              Locally downloaded LLM models

--------------------------------------------------

SOME HELPFUL COMMANDS YOU CAN RUN ( cd local_llm_framework/bin )

ALWAYS Ensure you are in the virtual environment:
  source ../llf_venv/bin/activate
   NOTE:  Remember to always be in the virtual environment

General online help:
   ./llf -h

Online help about the server command:
   ./llf server -h

Start local LLM server:
   ./llf server start --daemon

Stop local LLM server:
   ./llf server stop

Send non-interactive chat request to LLM:
   ./llf chat --cli "what is the origin of Christmas?"

Start interactive chat in the terminal:
   ./llf chat

   Helpful commands in the interactive chat:
      
      View help menu:  help
      Exit interactive chat:  exit
      View the model you are using:  info

List the downloaded models:
   ./llf model list

Download a specific model from https://huggingface.co:
   ./llf model download --huggingface-model <MODEL NAME>
   EXAMPLE:  ./llf model download --huggingface-model deepseek-ai/DeepSeek-V3.2

   NOTE:  You will need to run the conversion process earlier in this document.
          to convert the downloaded LLM to a GGUF format so it will be 
          compatible with the local Llama server.  If the conversion process
          does NOT work, then you can not use the model

Convert a newly downloaded Model to GGUF format to run locally:
   cd tools
   ./convert_huggingface_llm_2_gguf.sh -s <MODEL_NAME> -d <MODEL_NAME>-GGUF
      NOTE:  If you want to replace an existing <MODEL_NAME>-GGUF, then
             you can use the -f parameter

   NOTE:  If the conversion process is not successful, then the model can not
          be used by the local Llama LLM Server.

Remove old Models:
   cd ../models
   ls -l 
   rm -Rf <DIRECTORY NAME WITH MODEL IN IT TO DELETE>




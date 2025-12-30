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


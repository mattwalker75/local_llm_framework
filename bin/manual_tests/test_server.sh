#
#  had to download and compile llama-server for the 
#  backend and go to hugging face and download a
#  model with a -GGUF extension, such as the following
#  through huggingface:
#
#  Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
#
#  This is how we had to get it running instead of using
#  vllm due to the fact that I am running on a Mac and
#  not on Linux along with the limited hardware on a Mac
#
#    git clone https://github.com/ggml-org/llama.cpp
#    cd llama.cpp
#    mkdir build
#    cd build
#    cmake ..
#    cmake --build . --config Release
#

#
#  Using Llama as a backend server running locally so we
#  can use OpenAI libraries for LLM work
#
LLM_SERVER="../llama.cpp/build/bin/llama-server"
MODEL_GGUF_FILE="models/Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
PORT=8000

${LLM_SERVER} --model ${MODEL_GGUF_FILE} --host 0.0.0.0 --port ${PORT}

